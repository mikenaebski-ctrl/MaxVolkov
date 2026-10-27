"""Display a small terminal with tkinter widgets."""

import tkinter as tk
from tkinter.scrolledtext import ScrolledText

from .config import Config, describe
from .constants import TERMINAL_FONT, WIDGET_PADDING, WINDOW_GEOMETRY
from .script import ScriptError, load_script, run_script
from .session import Session
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
        self.append("Stage 3: ls, cd, vfs-info, exit. Press Enter to run.\n")

    def append(self, text: str) -> None:
        """Append output while keeping the transcript read only."""
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, text)
        self.output.configure(state=tk.DISABLED)
        self.output.see(tk.END)

    def print_line(self, text: str) -> None:
        """Append one line of output."""
        self.append(f"{text}\n")

    def show_config(self, config: Config) -> None:
        """Print the startup parameters for debugging."""
        for line in describe(config):
            self.print_line(line)

    def start_script(self, path: str) -> None:
        """Replay the startup script and report unreadable files."""
        try:
            lines = load_script(path)
        except ScriptError as error:
            self.print_line(f"error: {error}")
            return
        report = run_script(self.shell, lines, self.print_line)
        if report.exited:
            self.root.destroy()

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


def launch(config: Config, session: Session) -> None:
    """Run the tkinter event loop, replaying the script once it starts."""
    root = tk.Tk()
    window = ShellWindow(root, session.shell)
    window.show_config(config)
    for message in session.messages:
        window.print_line(message)
    if config.script_path:
        root.after(0, window.start_script, config.script_path)
    root.mainloop()
