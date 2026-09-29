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
import theme as ui_theme
import tune_store
from constants import POLL_MS
from serial_link import SerialLink
from state import SessionState

if TYPE_CHECKING:
    import tkinter as tk

    from views.appearance_view import AppearanceView
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
        self.appearance: AppearanceView

    def bind_views(
        self,
        conn: "ConnectionView",
        heat: "HeatView",
        settings: "SettingsView",
        tune: "TuneView",
        status_bar: "StatusBar",
        appearance: "AppearanceView",
    ) -> None:
        self.conn = conn
        self.heat = heat
        self.settings = settings
        self.tune = tune
        self.status_bar = status_bar
        self.appearance = appearance
        ramps_store.load_ramps(
            lambda i, v: self.heat.ramp_active[i].set(v),
            lambda i, v: self.heat.ramp_temp[i].set(v),
            lambda i, v: self.heat.ramp_hold[i].set(v),
        )
        self.heat.ramp_active[0].set(True)
        self.heat.refresh_objetivo()
        self.refresh_chrome()
        self.root.after(POLL_MS, self._poll_rx)

    def apply_theme(self) -> None:
        ui_theme.apply_ttk(self.root)
        self.conn.apply_theme()
        self.heat.apply_theme()
        self.tune.apply_theme()
        self.settings.apply_theme()
        self.appearance.apply_theme()
        self.status_bar.apply_theme()

    def save_theme(self) -> None:
        partial = self.appearance.collect_theme()
        ui_theme.save(partial)
        self.apply_theme()
        messagebox.showinfo(
            "Tema",
            "Apariencia aplicada y guardada (ui_theme.json).",
        )

    def reset_theme(self) -> None:
        ui_theme.reset_defaults()
        self.appearance.reload_theme_vars()
        self.apply_theme()
        messagebox.showinfo("Tema", "Tema restaurado a los valores por defecto.")

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
        self.conn.log_line(
            "--",
            "puerto abierto — el saludo HP solo sale al encender; preguntando con AT…",
        )
        self._probe_boot()

    def disconnect(self) -> None:
        self._cancel_stat()
        self.link.close()
        self.state.reset_link()
        self.refresh_chrome()

    def _probe_boot(self) -> None:
        """El equipo ya encendido no repite HP. AT → OK lo da por en línea."""

        def work() -> None:
            try:
                result = self.link.send(proto.cmd_at())
            except Exception as exc:
                msg = str(exc)
                self.root.after(0, lambda m=msg: self._probe_boot_fail(m))
                return
            if result.kind == "OK":
                self.root.after(0, self._probe_boot_ok)

        self.conn.log_line("TX", proto.cmd_at())
        threading.Thread(target=work, daemon=True).start()

    def _probe_boot_ok(self) -> None:
        if not self.link.connected or self.state.device_online:
            return
        self.conn.log_line("RX", "OK")
        self.conn.log_line("--", "equipo en marcha (AT → OK)")
        self.on_device_online()

    def _probe_boot_fail(self, msg: str) -> None:
        if not self.link.connected or self.state.device_online:
            return
        self.conn.log_line(
            "!!",
            f"{msg}. Sin respuesta: el firmware grabado y Studio tienen que ir los dos a 19200.",
        )

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
        self._set_usb_mode(False)

    def _on_usb_enter(self) -> None:
        self._set_usb_mode(True)
        self.read_ramps()
        self.read_cfg()

    def _set_usb_mode(self, on: bool) -> None:
        """En USB el equipo empuja $HP a 1 Hz; en Manual vuelve el sondeo."""
        self.state.usb_mode = on
        self.refresh_chrome()
        self.toggle_stat_poll()

    def on_close(self) -> None:
        self._cancel_stat()
        self.link.close()
        self.root.destroy()

    # ---- comandos ----

    def send(
        self,
        cmd: str,
        after_ok: Optional[Callable] = None,
        after_err: Optional[Callable] = None,
        *,
        ok_msg: Optional[str] = None,
        err_title: str = "Error",
    ) -> None:
        if not self.link.connected:
            messagebox.showwarning("Serie", "Conecta primero")
            return
        if not self.state.device_online:
            messagebox.showwarning(
                "Equipo",
                "El equipo aún no respondió. Espera el saludo HP o el OK del ping AT.",
            )
            return
        self.conn.log_line("TX", cmd)

        def work() -> None:
            try:
                result = self.link.send(cmd)
            except Exception as exc:
                msg = str(exc)
                self.root.after(0, lambda m=msg: self.conn.log_line("!!", m))
                if ok_msg is not None or after_err is not None:
                    self.root.after(
                        0,
                        lambda m=msg: messagebox.showerror(err_title, m),
                    )
                if after_err:
                    self.root.after(0, lambda: after_err(None))
                return
            if result.kind == "OK":
                def _ok() -> None:
                    if after_ok:
                        after_ok()
                    if ok_msg:
                        messagebox.showinfo("Guardado", ok_msg)

                self.root.after(0, _ok)
            else:
                detail = getattr(result, "raw", None) or str(result.kind)
                if getattr(result, "fields", None):
                    detail = (
                        f"{result.fields.get('name', detail)} "
                        f"(código {result.fields.get('code', '?')})"
                    )

                def _err() -> None:
                    if after_err:
                        after_err(result)
                    elif ok_msg is not None:
                        messagebox.showerror(
                            err_title, f"El equipo respondió ERROR:\n{detail}"
                        )

                self.root.after(0, _err)

        threading.Thread(target=work, daemon=True).start()

    def ping(self) -> None:
        self.send(proto.cmd_at(), err_title="Ping")

    def query_stat(self) -> None:
        self.send(proto.cmd_stat(), err_title="Estado")

    def _unlock_heat_poll(self) -> None:
        self.conn.set_poll_locked(False)
        self.heat.set_heat_running(False)

    def _lock_heat_poll(self) -> None:
        self.conn.set_poll_locked(True)
        self.toggle_stat_poll()
        self.heat.set_heat_running(True)

    def stop(self) -> None:
        was_heat = self.state.recording_heat or self.heat.is_heat_running()
        self.state.recording_heat = False
        self.state.heat_seen_active = False
        self.tune.stop_recording()
        if was_heat:
            self._unlock_heat_poll()
        self.send(proto.cmd_stop(), err_title="Detener")

    def toggle_heat(self) -> None:
        if self.heat.is_heat_running() or self.state.recording_heat:
            self.stop()
        else:
            self.start_heat()

    def toggle_tune(self) -> None:
        if self.tune.is_tune_running() or self.tune.recording:
            self.stop()
        else:
            self.run_tune()

    def start_heat(self) -> None:
        if not self.heat.has_active_ramps():
            messagebox.showwarning(
                "HEAT",
                "No hay escalones activos. Configura y guarda al menos la rampa 1.",
            )
            return
        active, temps, _holds = self.heat.ramp_snapshot()
        try:
            int_temps = [int(temps[i]) if active[i] else 0 for i in range(4)]
        except ValueError:
            messagebox.showerror("HEAT", "Temperaturas de rampa inválidas")
            return
        err = proto.validate_ramp_profile(int_temps, list(active))
        if err:
            messagebox.showerror("HEAT", err)
            return
        self.tune.stop_recording()
        self.state.clear_samples()
        self.heat.chart.clear()
        self.heat.sync_chart_ylim()
        self.state.recording_heat = True
        self.state.heat_seen_active = False
        self._lock_heat_poll()

        def _fail(_r=None) -> None:
            self.state.recording_heat = False
            self.state.heat_seen_active = False
            self._unlock_heat_poll()
            messagebox.showerror(
                "HEAT",
                "No se pudo iniciar HEAT. Revisa modo USB y rampas en el equipo.",
            )

        self.send(
            proto.cmd_run_heat(),
            after_err=_fail,
            err_title="HEAT",
        )

    def read_ramps(self) -> None:
        self.send(proto.cmd_cfg_ramps_query(), err_title="Rampas")

    def read_cfg(self) -> None:
        self.send(proto.cmd_cfg_query(), err_title="Ajustes")

    def write_ramp(self, idx: int) -> None:
        """Guarda el perfil activo completo (un solo escalón no debe achicar N)."""
        self.write_all_ramps()

    def write_all_ramps(self) -> None:
        """Escribe escalones activos 0..n-1; el último fija N en el equipo."""
        self.heat.ramp_active[0].set(True)
        self.heat._on_ramp_active_toggle()
        active, temps, holds = self.heat.ramp_snapshot()
        n = 0
        for i in range(4):
            if active[i]:
                n = i + 1
            elif any(active[j] for j in range(i + 1, 4)):
                messagebox.showerror(
                    "Rampas",
                    "Los escalones activos deben ser contiguos desde la rampa 1.",
                )
                return
        if n < 1:
            messagebox.showerror("Rampas", "Se requiere al menos la rampa 1")
            return
        int_temps: list[int] = []
        for i in range(4):
            try:
                int_temps.append(int(temps[i]) if active[i] else 0)
            except ValueError:
                int_temps.append(0)
        err = proto.validate_ramp_profile(int_temps, list(active))
        if err:
            messagebox.showerror("Rampas", err)
            return
        cmds: list[tuple[int, int, int]] = []
        prev: int | None = None
        for i in range(n):
            try:
                temp = int(temps[i])
                hold = int(holds[i])
            except ValueError:
                messagebox.showerror("Rampas", f"Rampa {i + 1}: valores numéricos")
                return
            err = proto.validate_ramp(
                i, temp, hold, self.state.tmin, self.state.tmax, prev_temp=prev
            )
            if err:
                messagebox.showerror("Rampas", f"Rampa {i + 1}: {err}")
                return
            cmds.append((i, temp, hold))
            prev = temp

        def step(i: int) -> None:
            if i >= len(cmds):
                self._save_ramps()
                messagebox.showinfo(
                    "Guardado",
                    f"Soldering Profile guardado en HotPlate (N={n}).\n"
                    "Leyendo de vuelta para confirmar…",
                )
                self.read_ramps()
                return
            idx, temp, hold = cmds[i]

            def _fail(_r=None) -> None:
                messagebox.showerror(
                    "Rampas",
                    f"Error al guardar el escalón {idx + 1}. Soldering Profile incompleto.",
                )

            self.send(
                proto.cmd_cfg_ramp(idx, temp, hold),
                after_ok=lambda: step(i + 1),
                after_err=_fail,
                err_title="Rampas",
            )

        step(0)

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

        self.send(
            proto.cmd_cfg_safety(mn, mx),
            after_ok=_ok,
            ok_msg="Límites de temperatura guardados.",
            err_title="Límites",
        )

    def write_heat(self) -> None:
        """Persiste AT+CFG=H y bandas AT+CFG=B."""
        try:
            vals = [
                self.settings.delay_seconds(),
                1 if self.settings.var_air.get() else 0,
            ]
            bn = int(self.settings.var_bn.get())
            bx = int(self.settings.var_bx.get())
        except ValueError:
            messagebox.showerror("Flujo HEAT", "valores numéricos")
            return
        err = proto.validate_heat(*vals)
        if err:
            messagebox.showerror("Flujo HEAT", err)
            return
        err = proto.validate_band(bn, bx)
        if err:
            messagebox.showerror("Flujo HEAT", err)
            return

        def _after_h_ok() -> None:
            self.send(
                proto.cmd_cfg_band(bn, bx),
                ok_msg="Flujo HEAT y bandas guardados (AT+CFG=H/B).",
                err_title="Bandas",
            )

        self.send(
            proto.cmd_cfg_heat(*vals),
            after_ok=_after_h_ok,
            err_title="Flujo HEAT",
        )

    def write_pid(self) -> None:
        try:
            kp = int(self.settings.var_kp.get())
            ki = int(self.settings.var_ki.get())
        except ValueError:
            messagebox.showerror("PID", "valores numéricos")
            return
        err = proto.validate_pid(kp, ki)
        if err:
            messagebox.showerror("PID", err)
            return

        def _ok() -> None:
            self.tune.apply_working_pid({"KP": kp, "KI": ki})

        self.send(
            proto.cmd_cfg_pid(kp, ki),
            after_ok=_ok,
            ok_msg="Ganancias PID guardadas en el equipo.",
            err_title="PID",
        )

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
        self.send(
            proto.cmd_cfg_tune(cycles, hyst, max_s),
            ok_msg=(
                "Parámetros de autoajuste guardados (AT+CFG=T → EEPROM)\n"
                f"y caché local (timeout {max_s} s)."
            ),
            err_title="Autoajuste",
        )

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

        def _fail(_r=None) -> None:
            self.tune.stop_recording()
            messagebox.showerror(
                "Autoajuste",
                "No se pudo iniciar el autoajuste. Revisa modo USB y parámetros.",
            )

        self.send(
            proto.cmd_run_tune(temp, cycles, hyst, max_s),
            after_err=_fail,
            err_title="Autoajuste",
        )

    def apply_atune(self) -> None:
        """Kp/Ki ya están en EEPROM al terminar el autoajuste. Solo refresca $CF."""
        self.tune._atune_result_ready = False
        self.read_cfg()

    # ---- sondeo STAT ----

    def toggle_stat_poll(self) -> None:
        if self.conn._poll_locked:
            self.conn.poll_stat.set(True)
            self.conn.stat_interval.set("1 s")
        self._cancel_stat()
        if self.state.usb_mode:
            return
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
            and not self.state.usb_mode
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
            self.tune.apply_working_pid(p.fields)
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
            # ERROR:8 = EXIT en HotPanel: el equipo ya está en Manual.
            if p.fields.get("code") == 8 and self.state.usb_mode:
                self._set_usb_mode(False)
        elif p.kind == "BOOT":
            self.conn.log_line("--", "arranque del equipo (HP)")
            if self.state.usb_mode:
                self._set_usb_mode(False)
            self.on_device_online()

    def _apply_hp(self, fields: dict) -> None:
        self.state.last_hp = fields
        delay_cfg = self.settings.delay_clock()
        self.heat.apply_hp(fields, delay_cfg=delay_cfg)
        self.tune.apply_status(fields, delay_cfg)
        self.tune.apply_atune_fields(fields)

        t = fields.get("T")
        a = int(fields.get("A", 0))
        p = int(fields.get("P", 0))
        # HEAT activo: fases 1…7; muestra final en Terminado/Falla y corta
        heat_running = p == 1 and a in (1, 2, 3, 4, 5, 6, 7)
        heat_ending = p == 1 and a in (8, 9)
        if self.state.recording_heat and (heat_running or heat_ending):
            self.state.heat_seen_active = True
            now = time.time()
            if self.state.t0 is None:
                self.state.t0 = now
            plot_set = float("nan")
            if a in (4, 5):
                try:
                    plot_set = float(fields.get("SET", float("nan")))
                except (TypeError, ValueError):
                    plot_set = float("nan")
            self.state.append_sample(
                now - self.state.t0,
                float(t) if t is not None else float("nan"),
                plot_set,
                float(fields.get("DU", float("nan"))),
                proto.chart_phase_label(a, fields.get("RI")),
            )
            # Usar trace completo (no la ventana samples) para no “cortar” ni
            # desplazar el origen del eje X al llenarse el deque.
            self.heat.chart.redraw(
                self.state.trace, None, y_max=self.heat.ramp_ymax()
            )
            if heat_ending:
                self.state.recording_heat = False
                self.state.heat_seen_active = False
                self._unlock_heat_poll()
        elif self.state.recording_heat and self.state.heat_seen_active:
            self.state.recording_heat = False
            self.state.heat_seen_active = False
            self._unlock_heat_poll()

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
            w.writerow(
                [
                    "Tiempo (s)",
                    "Temperatura medida (°C)",
                    "Temperatura consignada / SET (°C)",
                    "Potencia calentador (%)",
                    "Fase del proceso",
                ]
            )
            for row in rows:
                cells = list(row)
                if len(cells) < 5:
                    cells.extend([""] * (5 - len(cells)))
                w.writerow(cells)
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

    def _export_event_csv(self, chart, *, initialfile: str, empty_msg: str) -> None:
        rows = chart.event_rows()
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
            w.writerow(["Tiempo", "Duración", "Temperatura (°C)", "Evento"])
            w.writerows(rows)
        messagebox.showinfo("CSV", f"Guardado {path}\n{len(rows)} eventos")

    def export_heat_events(self) -> None:
        self._export_event_csv(
            self.heat.chart,
            initialfile="hotplate_heat_eventos.csv",
            empty_msg="Sin eventos de HEAT",
        )

    def export_tune_events(self) -> None:
        self._export_event_csv(
            self.tune.chart,
            initialfile="hotplate_tune_eventos.csv",
            empty_msg="Sin eventos de autoajuste",
        )
