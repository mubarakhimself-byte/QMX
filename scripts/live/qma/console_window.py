"""Drive `qma.console` in a real Windows console window, the way the operator types into it.

`ConsoleWindow` starts the console under its own `conhost.exe` window with a fixed title, types
keystrokes into that window's input buffer, sends Ctrl+C as the keyboard does, reads the screen
buffer back as text, and captures the window with `ffmpeg -f gdigrab`. Windows only; standard
library and psutil only.
"""

from __future__ import annotations

import contextlib
import ctypes
import os
import shutil
import subprocess
import time
from ctypes import wintypes
from pathlib import Path
from typing import Final

import psutil

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)

KEY_EVENT: Final = 0x0001
VK_RETURN: Final = 0x0D
CTRL_C_EVENT: Final = 0
GENERIC_RW: Final = 0xC0000000
SHARE_RW: Final = 0x3
OPEN_EXISTING: Final = 3
COLUMNS: Final = 118
ROWS: Final = 42
SCROLLBACK: Final = 3000
CONHOST: Final = str(Path(os.environ.get("SYSTEMROOT", "C:/Windows")) / "System32" / "conhost.exe")
FFMPEG: Final = shutil.which("ffmpeg") or "ffmpeg"


class CharUnion(ctypes.Union):
    _fields_ = (("UnicodeChar", wintypes.WCHAR), ("AsciiChar", ctypes.c_char))


class KeyEventRecord(ctypes.Structure):
    _fields_ = (
        ("bKeyDown", wintypes.BOOL),
        ("wRepeatCount", wintypes.WORD),
        ("wVirtualKeyCode", wintypes.WORD),
        ("wVirtualScanCode", wintypes.WORD),
        ("uChar", CharUnion),
        ("dwControlKeyState", wintypes.DWORD),
    )


class EventUnion(ctypes.Union):
    _fields_ = (("KeyEvent", KeyEventRecord), ("padding", ctypes.c_byte * 16))


class InputRecord(ctypes.Structure):
    _fields_ = (("EventType", wintypes.WORD), ("Event", EventUnion))


class Coord(ctypes.Structure):
    _fields_ = (("X", wintypes.SHORT), ("Y", wintypes.SHORT))


class SmallRect(ctypes.Structure):
    _fields_ = (
        ("Left", wintypes.SHORT),
        ("Top", wintypes.SHORT),
        ("Right", wintypes.SHORT),
        ("Bottom", wintypes.SHORT),
    )


class BufferInfo(ctypes.Structure):
    _fields_ = (
        ("dwSize", Coord),
        ("dwCursorPosition", Coord),
        ("wAttributes", wintypes.WORD),
        ("srWindow", SmallRect),
        ("dwMaximumWindowSize", Coord),
    )


kernel32.CreateFileW.restype = wintypes.HANDLE
kernel32.GetConsoleWindow.restype = wintypes.HWND
kernel32.SetConsoleScreenBufferSize.argtypes = (wintypes.HANDLE, Coord)
kernel32.ReadConsoleOutputCharacterW.argtypes = (
    wintypes.HANDLE,
    wintypes.LPWSTR,
    wintypes.DWORD,
    Coord,
    ctypes.POINTER(wintypes.DWORD),
)
kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
kernel32.WriteConsoleInputW.argtypes = (
    wintypes.HANDLE,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
)
kernel32.SetConsoleWindowInfo.argtypes = (wintypes.HANDLE, wintypes.BOOL, ctypes.c_void_p)
kernel32.GetConsoleScreenBufferInfo.argtypes = (wintypes.HANDLE, ctypes.c_void_p)
user32.SetWindowPos.argtypes = (
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
)
user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
user32.SetForegroundWindow.argtypes = (wintypes.HWND,)


def _check(ok: object, what: str) -> None:
    if not ok:
        raise OSError(ctypes.get_last_error(), what)


class ConsoleWindow:
    def __init__(self, title: str, argv: list[str], *, cwd: Path, env: dict[str, str]) -> None:
        self.title = title
        self.host = subprocess.Popen([CONHOST, *argv], cwd=cwd, env=env)
        try:
            self._setup(argv[0])
        except BaseException:
            self.kill()
            raise

    def _setup(self, exe: str) -> None:
        self.pid = self._console_pid(exe)
        kernel32.SetConsoleCtrlHandler(None, True)
        self._attach()
        title = self.title
        _check(kernel32.SetConsoleTitleW(title), "SetConsoleTitleW")
        out = self._out()
        rect = SmallRect(0, 0, COLUMNS - 1, ROWS - 1)
        kernel32.SetConsoleWindowInfo(out, True, ctypes.byref(SmallRect(0, 0, 40, 10)))
        _check(kernel32.SetConsoleScreenBufferSize(out, Coord(COLUMNS, SCROLLBACK)), "buffer")
        _check(kernel32.SetConsoleWindowInfo(out, True, ctypes.byref(rect)), "window size")
        kernel32.CloseHandle(out)
        self.hwnd = kernel32.GetConsoleWindow()
        self._detach()
        self.front()

    def _console_pid(self, exe: str) -> int:
        name = Path(exe).name.casefold()
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            with contextlib.suppress(psutil.Error):
                for child in psutil.Process(self.host.pid).children(recursive=True):
                    if child.name().casefold() == name:
                        return child.pid
            time.sleep(0.1)
        raise RuntimeError(f"{exe} never started under conhost")

    def _attach(self) -> None:
        kernel32.FreeConsole()
        _check(kernel32.AttachConsole(self.pid), "AttachConsole")

    def _detach(self) -> None:
        kernel32.FreeConsole()

    def _open(self, name: str) -> int:
        handle = kernel32.CreateFileW(name, GENERIC_RW, SHARE_RW, None, OPEN_EXISTING, 0, None)
        _check(handle not in (0, -1, None), f"open {name}")
        return int(handle)

    def _out(self) -> int:
        return self._open("CONOUT$")

    def front(self) -> None:
        if self.hwnd:
            user32.ShowWindow(self.hwnd, 9)
            user32.SetWindowPos(self.hwnd, -1, 40, 40, 0, 0, 0x0001)
            user32.SetForegroundWindow(self.hwnd)

    def type(self, text: str, *, enter: bool = True, delay: float = 0.02) -> None:
        self._attach()
        try:
            handle = self._open("CONIN$")
            for char in text + ("\r" if enter else ""):
                vk = VK_RETURN if char == "\r" else 0
                records = (InputRecord * 2)()
                for index, down in enumerate((True, False)):
                    records[index].EventType = KEY_EVENT
                    key = records[index].Event.KeyEvent
                    key.bKeyDown, key.wRepeatCount, key.wVirtualKeyCode = down, 1, vk
                    key.uChar.UnicodeChar = char
                written = wintypes.DWORD()
                _check(
                    kernel32.WriteConsoleInputW(handle, records, 2, ctypes.byref(written)),
                    "WriteConsoleInputW",
                )
                time.sleep(delay)
            kernel32.CloseHandle(handle)
        finally:
            self._detach()

    def ctrl_c(self) -> None:
        self._attach()
        try:
            _check(kernel32.GenerateConsoleCtrlEvent(CTRL_C_EVENT, 0), "GenerateConsoleCtrlEvent")
            time.sleep(0.2)
        finally:
            self._detach()

    def screen(self) -> tuple[list[str], int]:
        """Every buffer row up to the cursor, right-trimmed, and the cursor row's index."""
        self._attach()
        try:
            out = self._out()
            info = BufferInfo()
            _check(kernel32.GetConsoleScreenBufferInfo(out, ctypes.byref(info)), "buffer info")
            width, last = info.dwSize.X, info.dwCursorPosition.Y
            cells = width * (last + 1)
            chars = ctypes.create_unicode_buffer(cells)
            read = wintypes.DWORD()
            kernel32.ReadConsoleOutputCharacterW(out, chars, cells, Coord(0, 0), ctypes.byref(read))
            kernel32.CloseHandle(out)
        finally:
            self._detach()
        text = ctypes.wstring_at(chars, read.value)
        rows = [text[i : i + width].rstrip() for i in range(0, len(text), width)]
        return rows, last

    def text(self) -> str:
        return "\n".join(self.screen()[0])

    def cursor_line(self) -> str:
        rows, last = self.screen()
        return rows[last] if last < len(rows) else ""

    def wait(self, predicate: str | None = None, *, seconds: float = 300) -> str:
        """Wait until the cursor rests on the console's main prompt (`> `), or on a line that
        holds `predicate`. Returns the cursor line."""
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            line = self.cursor_line()
            if (predicate is None and line.strip() == ">") or (predicate and predicate in line):
                return line
            if self.host.poll() is not None:
                raise RuntimeError("the console window closed")
            time.sleep(0.2)
        raise TimeoutError(f"no {predicate or 'prompt'} after {seconds:.0f} s: {line!r}")

    def send(self, text: str, answers: list[str] | None = None, *, seconds: float = 300) -> None:
        """Type one line, answer each ask in order (the last answer repeats), and wait for the
        main prompt."""
        queue = list(answers or ["n"])
        self.type(text)
        time.sleep(0.5)
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            line = self.cursor_line()
            if line.strip() == ">":
                return
            if line.rstrip().endswith(">") and line.strip() != ">":
                reply = queue.pop(0) if len(queue) > 1 else queue[0]
                self.type(reply)
                time.sleep(0.5)
                continue
            if self.host.poll() is not None:
                raise RuntimeError("the console window closed")
            time.sleep(0.2)
        raise TimeoutError(f"{text!r} did not finish in {seconds:.0f} s")

    def retitle(self) -> None:
        """A full-screen program such as the CLI sets its own title; put ours back."""
        self._attach()
        try:
            kernel32.SetConsoleTitleW(self.title)
        finally:
            self._detach()

    def shot(self, path: Path) -> Path:
        self.retitle()
        self.front()
        time.sleep(0.4)
        path.parent.mkdir(parents=True, exist_ok=True)
        grab = [FFMPEG, "-y", "-loglevel", "error", "-f", "gdigrab", "-i", f"title={self.title}"]
        subprocess.run([*grab, "-frames:v", "1", str(path)], check=True, timeout=60)
        return path

    def record(self, path: Path, seconds: int) -> subprocess.Popen[bytes]:
        """Stop it early by writing `q` to its stdin."""
        path.parent.mkdir(parents=True, exist_ok=True)
        grab = [FFMPEG, "-y", "-loglevel", "error", "-f", "gdigrab", "-framerate", "8"]
        grab += ["-i", f"title={self.title}", "-t", str(seconds), "-pix_fmt", "yuv420p"]
        grab += ["-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", str(path)]
        return subprocess.Popen(grab, stdin=subprocess.PIPE)

    def close(self) -> None:
        """`/exit`, which also stops a host the console started; a kill if it hangs."""
        with contextlib.suppress(Exception):
            if self.host.poll() is None:
                self.type("/exit")
                self.host.wait(60)
        self.kill()

    def kill(self) -> None:
        with contextlib.suppress(psutil.Error):
            tree = psutil.Process(self.host.pid)
            for member in [*tree.children(recursive=True), tree]:
                with contextlib.suppress(psutil.Error):
                    member.kill()
