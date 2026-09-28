"""Enlace serie: hilo lector + cola de comandos (uno a uno hasta OK/ERROR)."""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from typing import Optional

from protocol import Parsed, parse_line

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover
    serial = None
    list_ports = None


BAUD = 9600
CMD_TIMEOUT_S = 2.0


@dataclass
class RxEvent:
    """Línea recibida. kind: line | cmd_ok | cmd_err | timeout | link."""

    kind: str
    parsed: Optional[Parsed] = None
    raw: str = ""
    cmd: str = ""
    error_code: Optional[int] = None
    message: str = ""


def list_serial_ports() -> list[str]:
    if list_ports is None:
        return []
    return [p.device for p in list_ports.comports()]


class SerialLink:
    def __init__(self, rx_queue: queue.Queue):
        self._q = rx_queue
        self._ser: Optional[object] = None
        self._reader: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._cmd_lock = threading.Lock()
        self._pending: Optional[str] = None
        self._pending_ev = threading.Event()
        self._pending_result: Optional[Parsed] = None
        self._buf = bytearray()

    @property
    def connected(self) -> bool:
        return self._ser is not None and getattr(self._ser, "is_open", False)

    def open(self, port: str) -> None:
        if serial is None:
            raise RuntimeError("pyserial no instalado (pip install pyserial)")
        self.close()
        self._ser = serial.Serial(port, BAUD, timeout=0.05)
        self._stop.clear()
        self._buf.clear()
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        self._q.put(RxEvent(kind="link", message=f"conectado {port}"))

    def close(self) -> None:
        self._stop.set()
        if self._reader and self._reader.is_alive():
            self._reader.join(timeout=1.0)
        self._reader = None
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None
            self._q.put(RxEvent(kind="link", message="desconectado"))
        if self._pending is not None:
            self._pending_result = None
            self._pending_ev.set()
            self._pending = None

    def send(self, cmd: str, timeout: float = CMD_TIMEOUT_S) -> Parsed:
        """Envía un comando y espera OK o ERROR. Lanza TimeoutError."""
        if not self.connected:
            raise RuntimeError("sin conexión")
        with self._cmd_lock:
            self._pending = cmd
            self._pending_result = None
            self._pending_ev.clear()
            line = (cmd + "\r\n").encode("ascii", errors="ignore")
            self._ser.write(line)
            self._ser.flush()
            ok = self._pending_ev.wait(timeout)
            result = self._pending_result
            self._pending = None
            if not ok or result is None:
                self._q.put(
                    RxEvent(kind="timeout", cmd=cmd, message="timeout")
                )
                raise TimeoutError(f"timeout esperando respuesta a {cmd}")
            return result

    def _read_loop(self) -> None:
        while not self._stop.is_set():
            ser = self._ser
            if ser is None:
                break
            try:
                chunk = ser.read(256)
            except Exception as exc:
                self._q.put(RxEvent(kind="link", message=f"error RX: {exc}"))
                break
            if not chunk:
                continue
            self._buf.extend(chunk)
            while True:
                i_cr = self._buf.find(b"\r")
                i_lf = self._buf.find(b"\n")
                if i_cr < 0 and i_lf < 0:
                    break
                if i_cr < 0:
                    cut = i_lf
                elif i_lf < 0:
                    cut = i_cr
                else:
                    cut = min(i_cr, i_lf)
                raw_b = bytes(self._buf[:cut])
                del self._buf[: cut + 1]
                if self._buf[:1] in (b"\r", b"\n"):
                    del self._buf[:1]
                try:
                    text = raw_b.decode("ascii", errors="ignore").strip()
                except Exception:
                    continue
                if not text:
                    continue
                self._on_line(text)

    def _on_line(self, text: str) -> None:
        parsed = parse_line(text)
        if self._pending is not None and parsed.kind in ("OK", "ERROR"):
            self._pending_result = parsed
            self._pending_ev.set()
            if parsed.kind == "OK":
                self._q.put(RxEvent(kind="cmd_ok", parsed=parsed, raw=text, cmd=self._pending or ""))
            else:
                self._q.put(
                    RxEvent(
                        kind="cmd_err",
                        parsed=parsed,
                        raw=text,
                        cmd=self._pending or "",
                        error_code=parsed.fields.get("code"),
                    )
                )
            return
        self._q.put(RxEvent(kind="line", parsed=parsed, raw=text))
