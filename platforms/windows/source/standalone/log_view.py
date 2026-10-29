"""Bounded, read-only diagnostics displayed inside the main application."""

from pathlib import Path
import tkinter as tk
from tkinter import ttk

from standalone.environment_check import _read_recent_log


LOG_FILES = {"按键与语音": "bridge.log", "音频": "audio.log", "程序运行": "host.log"}
ERROR_MARKERS = ("error", "failed", "failure", "traceback", "exception", "invalid", "unavailable", "waiting")


def display_log(directory: Path, category: str, errors_only: bool = False) -> str:
    filename = LOG_FILES[category]
    path = directory / filename
    if not path.is_file():
        return "暂无日志，运行相应功能后会在这里显示。"
    content = _read_recent_log(path).replace("\r\n", "\n")
    if errors_only:
        content = "\n".join(line for line in content.splitlines()
                            if any(marker in line.casefold() for marker in ERROR_MARKERS))
        return content or "最近日志中没有错误或警告记录。"
    return content or "日志暂时为空。"


class LogPanel(tk.Frame):
    def __init__(self, parent, directory: Path):
        super().__init__(parent, bg="#f3f6fb", padx=24, pady=20)
        self.directory = directory
        self.category = tk.StringVar(value="按键与语音")
        self.errors_only = tk.BooleanVar(value=False)
        self.follow = tk.BooleanVar(value=True)
        self.notice = tk.StringVar(value="显示最近日志，每秒更新；复制内容仅保留在剪贴板。")
        self._last_content = None
        self._timer = None
        tk.Label(self, text="日志与诊断", bg="#f3f6fb", fg="#17263d",
                 font=("Microsoft YaHei UI", 18, "bold")).pack(anchor="w")
        tk.Label(self, text="查看连接、按键和录音记录，快速找到没有响应的环节。", bg="#f3f6fb", fg="#65758c",
                 font=("Microsoft YaHei UI", 9)).pack(anchor="w", pady=(6, 0))
        self.summary = tk.StringVar(value="等待更新")
        tk.Label(self, textvariable=self.summary, bg="#e8efff", fg="#234b88", anchor="w",
                 padx=14, pady=10, font=("Microsoft YaHei UI", 10)).pack(fill="x", pady=(16, 0))
        bar = tk.Frame(self, bg="#f3f6fb")
        bar.pack(fill="x", pady=14)
        selector = ttk.Combobox(bar, textvariable=self.category, values=tuple(LOG_FILES), state="readonly", width=18)
        selector.pack(side="left", padx=(0, 12))
        selector.bind("<<ComboboxSelected>>", lambda _: self.refresh(reset=True))
        ttk.Checkbutton(bar, text="仅错误 / 警告", variable=self.errors_only,
                        command=lambda: self.refresh(reset=True)).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(bar, text="跟随最新", variable=self.follow).pack(side="left", padx=(0, 12))
        ttk.Button(bar, text="刷新", command=self.refresh).pack(side="left", padx=(0, 8))
        ttk.Button(bar, text="复制当前内容", command=self.copy).pack(side="left")
        body = tk.Frame(self, bg="white")
        body.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(body)
        scrollbar.pack(side="right", fill="y")
        self.text = tk.Text(body, wrap="word", state="disabled", bg="white", fg="#26364b",
                            font=("Consolas", 10), padx=12, pady=12, yscrollcommand=scrollbar.set)
        self.text.pack(fill="both", expand=True)
        scrollbar.configure(command=self.text.yview)
        self.text.tag_configure("error", foreground="#b42318", background="#fff0ee")
        self.text.tag_configure("success", foreground="#16714a")
        self.text.tag_configure("section", foreground="#245ac0", spacing1=8, spacing3=4)
        tk.Label(self, textvariable=self.notice, bg="#f3f6fb", fg="#65758c", anchor="w").pack(fill="x", pady=(10, 0))

    def refresh(self, reset=False):
        content = display_log(self.directory, self.category.get(), self.errors_only.get())
        if content != self._last_content or reset:
            position = self.text.yview()[0]
            self.text.configure(state="normal")
            self.text.delete("1.0", "end")
            self.text.insert("1.0", content)
            errors = 0
            for number, line in enumerate(content.splitlines(), 1):
                if any(marker in line.casefold() for marker in ERROR_MARKERS):
                    tag = "error"
                    errors += 1
                elif line.startswith("---"):
                    tag = "section"
                elif any(marker in line for marker in ("READY", "MIC ON", "result=signal")):
                    tag = "success"
                else:
                    continue
                self.text.tag_add(tag, f"{number}.0", f"{number}.end")
            self.summary.set(f"{self.category.get()}  ·  最近 {len(content.splitlines())} 行  ·  {errors} 条错误 / 警告")
            self.text.configure(state="disabled")
            if self.follow.get():
                self.text.see("end")
            else:
                self.text.yview_moveto(0 if reset else position)
            self._last_content = content

    def copy(self):
        self.clipboard_clear()
        self.clipboard_append(self.text.get("1.0", "end-1c"))
        self.notice.set("已复制当前显示内容，可以粘贴给协助排查的人。")

    def start(self):
        self.stop()
        self.refresh()
        self._timer = self.after(1000, self.start)

    def stop(self):
        if self._timer is not None:
            self.after_cancel(self._timer)
            self._timer = None
