"""Activate the installed Codex desktop application using Windows APIs."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os

import psutil

CODEX_APP_ID = "OpenAI.Codex_2p2nqsd0c76g0!App"


def activate_codex() -> str:
    """Focus a matching visible window, or ask Windows to open the app.

    Foreground activation is subject to Windows focus rules. Shell activation is
    used as a fallback if there is no suitable window or focus is rejected.
    """
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows.argtypes = [callback_type, wintypes.LPARAM]
    user32.EnumWindows.restype = wintypes.BOOL
    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL
    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.IsIconic.restype = wintypes.BOOL
    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    handles: list[int] = []

    @callback_type
    def collect(hwnd, _parameter):
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        try:
            path = psutil.Process(pid.value).exe().replace("/", "\\").lower()
            if "\\windowsapps\\openai.codex_" in path and path.endswith("\\chatgpt.exe"):
                handles.append(hwnd)
        except (psutil.Error, OSError):
            pass
        return True

    user32.EnumWindows(collect, 0)
    for hwnd in handles:
        if user32.IsIconic(hwnd):
            user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        if user32.SetForegroundWindow(hwnd):
            return "focused"
    os.startfile("shell:AppsFolder\\" + CODEX_APP_ID)
    return "requested-launch"
