"""Display a small terminal with tkinter widgets."""

import tkinter as tk
from tkinter.scrolledtext import ScrolledText

from .constants import TERMINAL_FONT, WIDGET_PADDING, WINDOW_GEOMETRY
from .shell import Shell


class ShellWindow:
    """Connect the command entry and transcript to a shell instance."""

    def __init__(self, root: tk.Tk, shell: Shell) -> None:
        """Configure the window and create its input and output widgets."""
        self.root = root
        self.shell = shell
        root.title(f"UNIX shell - {shell.name}")
        root.geometry(WINDOW_GEOMETRY)
        self.output = ScrolledText(
            root,
            state=tk.DISABLED,
            wrap=tk.WORD,
            font=TERMINAL_FONT,
        )
        self.output.pack(
            fill=tk.BOTH,
            expand=True,
            padx=WIDGET_PADDING,
            pady=WIDGET_PADDING,
        )
        self.entry = tk.Entry(root, font=TERMINAL_FONT)
        self.entry.pack(
            fill=tk.X,
            padx=WIDGET_PADDING,
            pady=WIDGET_PADDING,
        )
        self.entry.bind("<Return>", self.submit)
        self.entry.focus_set()
        self.append("Stage 1: ls, cd, exit. Type a command and press Enter.\n")

    def append(self, text: str) -> None:
        """Append output while keeping the transcript read only."""
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, text)
        self.output.configure(state=tk.DISABLED)
        self.output.see(tk.END)

    def submit(self, event=None) -> str:
        """Echo input, show its result, and handle a valid exit."""
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        self.append(f"{self.shell.prompt}{line}\n")
        result = self.shell.execute(line)
        if result.text:
            self.append(f"{result.text}\n")
        if result.should_exit:
            self.root.destroy()
        return "break"


def launch() -> None:
    """Run the tkinter event loop."""
    root = tk.Tk()
    ShellWindow(root, Shell())
    root.mainloop()
