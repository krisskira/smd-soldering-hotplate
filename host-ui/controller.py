"""Orquestación: serie, comandos AT, dispatch RX → estado/vistas."""

from __future__ import annotations

import csv
import queue
import threading
import time
from typing import TYPE_CHECKING, Callable, Optional

from tkinter import filedialog, messagebox

import protocol as proto
import ramps_store
import tune_store
from constants import POLL_MS
from serial_link import SerialLink
from state import SessionState

if TYPE_CHECKING:
    import tkinter as tk

    from views.connection_view import ConnectionView
    from views.heat_view import HeatView
    from views.settings_view import SettingsView
    from views.status_bar import StatusBar
    from views.tune_view import TuneView


class AppController:
    def __init__(self, root: "tk.Tk", state: SessionState) -> None:
        self.root = root
        self.state = state
        self._rx: queue.Queue = queue.Queue()
        self.link = SerialLink(self._rx)
        self._stat_job: Optional[str] = None

        # Vistas (inyectadas tras construir el notebook)
        self.conn: ConnectionView
        self.heat: HeatView
        self.settings: SettingsView
        self.tune: TuneView
        self.status_bar: StatusBar

    def bind_views(
        self,
        conn: "ConnectionView",
        heat: "HeatView",
        settings: "SettingsView",
        tune: "TuneView",
        status_bar: "StatusBar",
    ) -> None:
        self.conn = conn
        self.heat = heat
        self.settings = settings
        self.tune = tune
        self.status_bar = status_bar
        ramps_store.load_ramps(
            lambda i, v: self.heat.ramp_active[i].set(v),
            lambda i, v: self.heat.ramp_temp[i].set(v),
            lambda i, v: self.heat.ramp_hold[i].set(v),
        )
        self.heat.refresh_objetivo()
        self.refresh_chrome()
        self.root.after(POLL_MS, self._poll_rx)

    # ---- chrome / sesión ----

    def refresh_chrome(self) -> None:
        st = self.state
        connected = self.link.connected
        self.status_bar.update(
            connected, st.device_online, st.conn_port, st.usb_mode
        )
        self.conn.refresh_session_ui(connected, st.device_online, st.usb_mode)

    def toggle_conn(self) -> None:
        if self.link.connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self) -> None:
        port = self.conn.selected_port()
        if not port:
            messagebox.showerror("Puerto", "Elige un puerto serie")
            return
        try:
            self.link.open(port)
        except Exception as exc:
            messagebox.showerror("Conexión", str(exc))
            return
        self.state.conn_port = port
        self.state.device_online = False
        self.state.usb_mode = False
        self._cancel_stat()
        self.refresh_chrome()
        self.conn.log_line("--", "puerto abierto — esperando arranque HP…")

    def disconnect(self) -> None:
        self._cancel_stat()
        self.link.close()
        self.state.reset_link()
        self.refresh_chrome()

    def on_device_online(self) -> None:
        if self.state.device_online:
            return
        self.state.device_online = True
        self.conn.log_line("--", "equipo en línea")
        self.refresh_chrome()
        self.toggle_stat_poll()

    def toggle_mode(self) -> None:
        if self.state.usb_mode:
            self.send(proto.cmd_mode(0), after_ok=self._on_manual_ok)
        else:
            self.send(proto.cmd_mode(1), after_ok=self._on_usb_enter)

    def _on_manual_ok(self) -> None:
        self.state.usb_mode = False
        self.refresh_chrome()

    def _on_usb_enter(self) -> None:
        self.state.usb_mode = True
        self.refresh_chrome()
        self.read_ramps()
        self.read_cfg()

    def on_close(self) -> None:
        self._cancel_stat()
        self.link.close()
        self.root.destroy()

    # ---- comandos ----

    def send(self, cmd: str, after_ok: Optional[Callable] = None) -> None:
        if not self.link.connected:
            messagebox.showwarning("Serie", "Conecta primero")
            return
        if not self.state.device_online:
            messagebox.showwarning(
                "Equipo",
                "Espera el arranque (línea HP) antes de enviar comandos",
            )
            return
        self.conn.log_line("TX", cmd)

        def work() -> None:
            try:
                result = self.link.send(cmd)
            except Exception as exc:
                self.root.after(0, lambda: self.conn.log_line("!!", str(exc)))
                return
            if after_ok and result.kind == "OK":
                self.root.after(0, after_ok)

        threading.Thread(target=work, daemon=True).start()

    def ping(self) -> None:
        self.send(proto.cmd_at())

    def query_stat(self) -> None:
        self.send(proto.cmd_stat())

    def stop(self) -> None:
        self.state.recording_heat = False
        self.tune.stop_recording()
        self.send(proto.cmd_stop())

    def start_heat(self) -> None:
        if not self.heat.has_active_ramps():
            messagebox.showwarning(
                "HEAT",
                "No hay escalones activos. Configura y guarda al menos la rampa 1.",
            )
            return
        self.tune.stop_recording()
        self.state.clear_samples()
        self.heat.chart.clear()
        self.heat.sync_chart_ylim()
        self.state.recording_heat = True
        self.send(proto.cmd_run_heat())

    def read_ramps(self) -> None:
        self.send(proto.cmd_cfg_ramps_query())

    def read_cfg(self) -> None:
        self.send(proto.cmd_cfg_query())

    def write_ramp(self, idx: int) -> None:
        try:
            temp = int(self.heat.ramp_temp[idx].get())
            hold = int(self.heat.ramp_hold[idx].get())
        except ValueError:
            messagebox.showerror("Rampas", "Temperatura y tiempo deben ser numéricos")
            return
        err = proto.validate_ramp(idx, temp, hold, self.state.tmin, self.state.tmax)
        if err:
            messagebox.showerror("Rampas", err)
            return
        self.send(proto.cmd_cfg_ramp(idx, temp, hold), after_ok=self._save_ramps)

    def write_all_ramps(self) -> None:
        for i in range(4):
            if self.heat.ramp_active[i].get():
                self.write_ramp(i)

    def _save_ramps(self) -> None:
        active, temps, holds = self.heat.ramp_snapshot()
        ramps_store.save_ramps(active, temps, holds)

    def write_safety(self) -> None:
        try:
            mn, mx = int(self.settings.var_mn.get()), int(self.settings.var_mx.get())
        except ValueError:
            messagebox.showerror("Límites", "valores numéricos")
            return
        err = proto.validate_safety(mn, mx)
        if err:
            messagebox.showerror("Límites", err)
            return

        def _ok() -> None:
            self.state.tmin = mn
            self.state.tmax = mx

        self.send(proto.cmd_cfg_safety(mn, mx), after_ok=_ok)

    def write_heat(self) -> None:
        """Persiste AT+CFG=H (precalentado + arranque/fin juntos)."""
        try:
            vals = [
                1 if self.settings.var_ph.get() else 0,
                int(self.settings.var_pct.get()),
                int(self.settings.var_sb.get()),
                int(self.settings.var_dly.get()),
                1 if self.settings.var_air.get() else 0,
                1 if self.settings.var_snd.get() else 0,
            ]
        except ValueError:
            messagebox.showerror("Flujo HEAT", "valores numéricos")
            return
        err = proto.validate_heat(*vals)
        if err:
            messagebox.showerror("Flujo HEAT", err)
            return
        self.send(proto.cmd_cfg_heat(*vals))

    def write_pid(self) -> None:
        try:
            kp = int(self.settings.var_kp.get())
            ki = int(self.settings.var_ki.get())
            kd = int(self.settings.var_kd.get())
        except ValueError:
            messagebox.showerror("PID", "valores numéricos")
            return
        err = proto.validate_pid(kp, ki, kd)
        if err:
            messagebox.showerror("PID", err)
            return
        self.send(proto.cmd_cfg_pid(kp, ki, kd))

    def save_tune_params(self) -> None:
        """Valida, envía AT+CFG=T al equipo y guarda caché local."""
        try:
            temp = int(self.tune.var_ttemp.get())
            cycles = int(self.tune.var_tcyc.get())
            hyst = int(self.tune.var_thyst.get())
            max_s = int(self.tune.var_tmax_s.get())
        except ValueError:
            messagebox.showerror("Autoajuste", "valores numéricos")
            return
        err = proto.validate_tune(
            temp, cycles, hyst, self.state.tmin, self.state.tmax, max_s
        )
        if err:
            messagebox.showerror("Autoajuste", err)
            return
        err_t = proto.validate_tune_cfg(cycles, hyst, max_s)
        if err_t:
            messagebox.showerror("Autoajuste", err_t)
            return
        tune_store.save_tune(temp, cycles, hyst, max_s)
        self.tune.sync_chart_ylim()

        def _ok() -> None:
            messagebox.showinfo(
                "Autoajuste",
                "Parámetros guardados en el equipo (AT+CFG=T → EEPROM)\n"
                f"y en el host (timeout {max_s} s).",
            )

        self.send(proto.cmd_cfg_tune(cycles, hyst, max_s), after_ok=_ok)

    def run_tune(self) -> None:
        try:
            temp = int(self.tune.var_ttemp.get())
            cycles = int(self.tune.var_tcyc.get())
            hyst = int(self.tune.var_thyst.get())
            max_s = int(self.tune.var_tmax_s.get())
        except ValueError:
            messagebox.showerror("Autoajuste", "valores numéricos")
            return
        err = proto.validate_tune(
            temp, cycles, hyst, self.state.tmin, self.state.tmax, max_s
        )
        if err:
            messagebox.showerror("Autoajuste", err)
            return
        tune_store.save_tune(temp, cycles, hyst, max_s)
        self.state.recording_heat = False
        self.tune.begin_run()
        self.send(proto.cmd_run_tune(temp, cycles, hyst, max_s))

    def apply_atune(self) -> None:
        self.send(proto.cmd_cfg_apply_atune())

    # ---- sondeo STAT ----

    def toggle_stat_poll(self) -> None:
        self._cancel_stat()
        if (
            self.conn.poll_stat.get()
            and self.link.connected
            and self.state.device_online
        ):
            self._stat_tick()

    def _cancel_stat(self) -> None:
        if self._stat_job is not None:
            self.root.after_cancel(self._stat_job)
            self._stat_job = None

    def _stat_tick(self) -> None:
        if (
            self.link.connected
            and self.state.device_online
            and self.conn.poll_stat.get()
        ):
            self.send(proto.cmd_stat())
            self._stat_job = self.root.after(
                self.conn.stat_interval_ms(), self._stat_tick
            )

    # ---- RX ----

    def _poll_rx(self) -> None:
        try:
            while True:
                self._handle_ev(self._rx.get_nowait())
        except queue.Empty:
            pass
        self.root.after(POLL_MS, self._poll_rx)

    def _handle_ev(self, ev) -> None:
        if ev.kind == "link":
            self.conn.log_line("--", ev.message)
            if "desconectado" in ev.message.lower() and not self.link.connected:
                self.state.reset_link()
                self._cancel_stat()
                self.refresh_chrome()
            return
        if ev.kind == "timeout":
            self.conn.log_line("!!", f"timeout {ev.cmd}")
            return
        if ev.kind in ("cmd_ok", "cmd_err", "line"):
            self.conn.log_line("RX", ev.raw)
        if ev.parsed is None:
            return
        p = ev.parsed
        if p.kind == "HP":
            self._apply_hp(p.fields)
        elif p.kind == "CF":
            self.state.last_cf = p.fields
            self.settings.apply_cf(p.fields, self.state)
            if "AMS" in p.fields:
                self.tune.var_tmax_s.set(str(p.fields["AMS"]))
            self.heat.refresh_objetivo()
        elif p.kind == "R":
            self.heat.apply_ramps_frame(
                int(p.fields.get("n", 0)), p.fields.get("steps") or []
            )
            self._save_ramps()
        elif p.kind == "ALARM":
            self.heat.set_banner(
                f"Alarma: {p.fields.get('name')} (código {p.fields.get('code')})",
                "#c90",
            )
        elif p.kind == "ERROR":
            self.heat.set_banner(
                f"Error: {p.fields.get('name')} (código {p.fields.get('code')})",
                "#c0392b",
            )
        elif p.kind == "BOOT":
            self.conn.log_line("--", "arranque del equipo (HP)")
            self.on_device_online()

    def _apply_hp(self, fields: dict) -> None:
        self.state.last_hp = fields
        self.heat.apply_hp(
            fields,
            delay_cfg=self.settings.var_dly.get(),
            preheat_en=self.settings.preheat_en_str(),
            preheat_pct=self.settings.var_pct.get(),
        )
        self.tune.apply_atune_fields(fields)

        t = fields.get("T")
        a = int(fields.get("A", 0))
        p = int(fields.get("P", 0))
        # HEAT activo: fases 1…7; muestra final en Terminado/Falla y corta
        heat_running = p == 1 and a in (1, 2, 3, 4, 5, 6, 7)
        heat_ending = p == 1 and a in (8, 9)
        if self.state.recording_heat and (heat_running or heat_ending):
            now = time.time()
            if self.state.t0 is None:
                self.state.t0 = now
            plot_set = float("nan")
            if a in (2, 3, 4, 5):
                try:
                    plot_set = float(fields.get("SET", float("nan")))
                except (TypeError, ValueError):
                    plot_set = float("nan")
            self.state.append_sample(
                now - self.state.t0,
                float(t) if t is not None else float("nan"),
                plot_set,
                float(fields.get("DU", float("nan"))),
            )
            self.heat.chart.redraw(
                self.state.samples, None, y_max=self.heat.ramp_ymax()
            )
            if heat_ending:
                self.state.recording_heat = False
        elif self.state.recording_heat and not heat_running:
            self.state.recording_heat = False

    def clear_plot(self) -> None:
        self.state.clear_samples()
        self.heat.chart.clear()
        self.heat.sync_chart_ylim()

    def _export_trace_csv(
        self, rows: list, *, initialfile: str, empty_msg: str
    ) -> None:
        if not rows:
            messagebox.showinfo("CSV", empty_msg)
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=initialfile,
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["t_s", "T_C", "SET_C", "DU_pct"])
            for row in rows:
                w.writerow(row)
        messagebox.showinfo(
            "CSV", f"Guardado {path}\n{len(rows)} muestras (histórico completo)"
        )

    def export_csv(self) -> None:
        self._export_trace_csv(
            self.state.trace,
            initialfile="hotplate_heat_trace.csv",
            empty_msg="Sin muestras de HEAT",
        )

    def export_tune_csv(self) -> None:
        self._export_trace_csv(
            self.tune.history,
            initialfile="hotplate_tune_trace.csv",
            empty_msg="Sin muestras de autoajuste",
        )
