"""Native Tk About window for the standalone Windows application."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk


BACKGROUND = "#f3f7fc"
NAVY = "#102342"
WHITE = "#ffffff"


def about_window_size(screen_width: int, screen_height: int) -> tuple[int, int]:
    """Fit the preferred 680x700 window on small or scaled displays."""

    if screen_width <= 0 or screen_height <= 0:
        raise ValueError("screen dimensions must be positive")
    width = min(680, max(320, screen_width - 48), screen_width)
    height = min(700, max(360, screen_height - 96), screen_height)
    return width, height


class AboutWindow:
    """Own a single, non-modal About ``Toplevel`` and its application information."""

    def __init__(
        self,
        owner: tk.Misc,
        app_name: str,
        app_version: str,
        check_updates: Callable[[], None],
        logger: Callable[[str], None],
    ) -> None:
        self.owner = owner
        self.app_name = app_name
        self.app_version = app_version
        self.check_updates = check_updates
        self.logger = logger
        self.window: tk.Toplevel | None = None

    def show(self) -> None:
        """Create the window once, or activate the existing instance."""

        if self._window_exists():
            assert self.window is not None
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
            return
        self._build()

    def close(self) -> None:
        window = self.window
        self.window = None
        if window is not None:
            try:
                window.destroy()
            except tk.TclError:
                pass

    def _window_exists(self) -> bool:
        if self.window is None:
            return False
        try:
            return bool(self.window.winfo_exists())
        except tk.TclError:
            self.window = None
            return False

    def _build(self) -> None:
        window = tk.Toplevel(self.owner)
        self.window = window
        window.title(f"关于 {self.app_name}")
        window.configure(background=BACKGROUND)
        window.resizable(True, True)
        window.protocol("WM_DELETE_WINDOW", self.close)
        window.bind("<Escape>", lambda _event: self.close())
        window.bind("<Control-w>", lambda _event: self.close())
        window.bind("<Destroy>", self._on_destroy, add="+")

        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        width, height = about_window_size(screen_width, screen_height)
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.minsize(min(520, width), min(480, height))

        shell = tk.Frame(window, background=BACKGROUND)
        shell.pack(fill="both", expand=True)
        canvas = tk.Canvas(
            shell,
            background=BACKGROUND,
            borderwidth=0,
            highlightthickness=0,
        )
        scrollbar = ttk.Scrollbar(shell, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(canvas, background=BACKGROUND)
        content_id = canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(content_id, width=event.width),
        )
        window.bind("<MouseWheel>", lambda event: self._scroll(canvas, event))
        window.bind("<Prior>", lambda _event: canvas.yview_scroll(-1, "pages"))
        window.bind("<Next>", lambda _event: canvas.yview_scroll(1, "pages"))
        window.bind("<Home>", lambda _event: canvas.yview_moveto(0.0))
        window.bind("<End>", lambda _event: canvas.yview_moveto(1.0))

        self._build_header(content)
        self._build_footer(content)

        window.after_idle(window.focus_force)

    def _build_header(self, parent: tk.Misc) -> None:
        header = tk.Frame(parent, background=NAVY, padx=28, pady=24)
        header.pack(fill="x")
        tk.Label(
            header,
            text=self.app_name,
            background=NAVY,
            foreground=WHITE,
            font=("Microsoft YaHei UI", 21, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text=f"Windows · v{self.app_version}",
            background=NAVY,
            foreground="#a9c8f5",
            font=("Microsoft YaHei UI", 10),
        ).pack(anchor="w", pady=(5, 0))

    def _build_footer(self, parent: tk.Misc) -> None:
        footer = tk.Frame(parent, background=BACKGROUND)
        footer.pack(fill="x", padx=24, pady=(0, 24))
        update_button = ttk.Button(
            footer,
            text="检查更新",
            command=self.check_updates,
        )
        update_button.pack(side="left")
        close_button = ttk.Button(footer, text="关闭", command=self.close)
        close_button.pack(side="right")
        update_button.bind("<Return>", lambda _event: update_button.invoke())
        close_button.bind("<Return>", lambda _event: close_button.invoke())

    @staticmethod
    def _scroll(canvas: tk.Canvas, event: tk.Event) -> str:
        if event.delta:
            canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"

    def _on_destroy(self, event: tk.Event) -> None:
        if event.widget is not self.window:
            return
        self.window = None
