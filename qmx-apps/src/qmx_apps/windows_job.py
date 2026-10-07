"""Windows kernel limits; pywin32 exposes memory limits, ctypes supplies CPU rate control."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from typing import Any

from qmx_apps.errors import Document
from qmx_apps.manifest import Budget


class CpuRate(ctypes.Structure):
    _fields_ = [("ControlFlags", wintypes.DWORD), ("CpuRate", wintypes.DWORD)]


class WindowsJob:
    def __init__(self, name: str, budget: Budget) -> None:
        if sys.platform != "win32":
            raise RuntimeError("Windows Job Objects are only available on Windows.")
        import win32job

        # Upstream stubs incorrectly declare CreateJobObject's result as None.
        self.api: Any = win32job
        self.handle: Any = self.api.CreateJobObject(None, name)
        self.closed = False
        try:
            info = self.api.QueryInformationJobObject(
                self.handle, self.api.JobObjectExtendedLimitInformation
            )
            info["BasicLimitInformation"]["LimitFlags"] = (
                self.api.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | self.api.JOB_OBJECT_LIMIT_JOB_MEMORY
            )
            info["JobMemoryLimit"] = budget.memory_mb * 1024 * 1024
            self.api.SetInformationJobObject(
                self.handle, self.api.JobObjectExtendedLimitInformation, info
            )
            kernel: Any = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.SetInformationJobObject.argtypes = [
                wintypes.HANDLE,
                ctypes.c_int,
                ctypes.c_void_p,
                wintypes.DWORD,
            ]
            kernel.SetInformationJobObject.restype = wintypes.BOOL
            kernel.QueryInformationJobObject.argtypes = [
                wintypes.HANDLE,
                ctypes.c_int,
                ctypes.c_void_p,
                wintypes.DWORD,
                ctypes.c_void_p,
            ]
            kernel.QueryInformationJobObject.restype = wintypes.BOOL
            self.kernel = kernel
            rate = CpuRate(
                5, budget.cpu_percent * 100
            )  # ENABLE | HARD_CAP, hundredths of a percent.
            if not kernel.SetInformationJobObject(
                int(self.handle), 15, ctypes.byref(rate), ctypes.sizeof(rate)
            ):
                raise ctypes.WinError(ctypes.get_last_error())
        except BaseException:
            self.handle.Close()
            raise

    def limits(self) -> Document:
        info = self.api.QueryInformationJobObject(
            self.handle, self.api.JobObjectExtendedLimitInformation
        )
        rate = CpuRate()
        if not self.kernel.QueryInformationJobObject(
            int(self.handle), 15, ctypes.byref(rate), ctypes.sizeof(rate), None
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        return {
            "memory_mb": info["JobMemoryLimit"] // (1024 * 1024),
            "cpu_percent": rate.CpuRate // 100,
            "kill_on_close": bool(
                info["BasicLimitInformation"]["LimitFlags"]
                & self.api.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            ),
        }

    def terminate(self) -> None:
        if not self.closed:
            self.api.TerminateJobObject(self.handle, 1)

    def close(self) -> None:
        if not self.closed:
            self.handle.Close()
            self.closed = True
