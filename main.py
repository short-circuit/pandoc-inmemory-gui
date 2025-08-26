import subprocess
import sys
import threading
import tkinter as tk
import tkhtmlview
from tkinter import ttk, messagebox, scrolledtext

try:
    from tkhtmlview import HTMLLabel
    HTML_AVAILABLE = True
except Exception:
    HTML_AVAILABLE = False

FORMATS = [
    "markdown",
    "markdown_strict",
    "commonmark",
    "html",
    "latex",
    "rst",
    "org",
    "plain",
    "asciidoc",
    "mediawiki",
]

def pandoc_convert(text: str, from_fmt: str, to_fmt: str) -> str:
    try:
        proc = subprocess.run(
            ["pandoc", "-f", from_fmt, "-t", to_fmt],
            input=text.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return proc.stdout.decode("utf-8")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(e.stderr.decode("utf-8") or "Pandoc conversion failed")

class PandocGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pandoc In‑Memory Converter with HTML Preview")
        self.geometry("950x700")
        self.create_widgets()

    def create_widgets(self):
        top_frame = ttk.Frame(self, padding="5")
        top_frame.pack(fill=tk.X)

        ttk.Label(top_frame, text="From:").pack(side=tk.LEFT, padx=(0, 5))
        self.from_var = tk.StringVar(value=FORMATS[0])
        ttk.OptionMenu(top_frame, self.from_var, FORMATS[0], *FORMATS).pack(side=tk.LEFT)

        ttk.Label(top_frame, text="To:").pack(side=tk.LEFT, padx=(15, 5))
        self.to_var = tk.StringVar(value=FORMATS[1])
        ttk.OptionMenu(top_frame, self.to_var, FORMATS[1], *FORMATS).pack(side=tk.LEFT)

        ttk.Button(top_frame, text="Convert ▶", command=self.start_conversion).pack(
            side=tk.RIGHT, padx=5
        )
        ttk.Button(top_frame, text="Copy Output", command=self.copy_output).pack(
            side=tk.RIGHT, padx=5
        )

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Input tab
        input_frame = ttk.Frame(self.notebook)
        self.notebook.add(input_frame, text="Input")
        self.input_text = scrolledtext.ScrolledText(
            input_frame, wrap=tk.WORD, height=12, font=("Consolas", 10)
        )
        self.input_text.pack(fill=tk.BOTH, expand=True)

        # Output tab
        output_frame = ttk.Frame(self.notebook)
        self.notebook.add(output_frame, text="Output")
        self.output_text = scrolledtext.ScrolledText(
            output_frame, wrap=tk.WORD, height=12, font=("Consolas", 10)
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Preview tab
        preview_frame = ttk.Frame(self.notebook)
        self.notebook.add(preview_frame, text="HTML Preview")
        if HTML_AVAILABLE:
            self.preview_label = HTMLLabel(preview_frame, html="", background="white")
            self.preview_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        else:
            self.preview_label = None
            ttk.Label(preview_frame, text="HTML preview unavailable.\nInstall tkhtmlview package.", foreground="red").pack(pady=20)

        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

    def start_conversion(self):
        thread = threading.Thread(target=self.convert)
        thread.daemon = True
        thread.start()

    def convert(self):
        self.set_status("Converting...")
        src = self.input_text.get("1.0", tk.END).rstrip("\n")
        if not src.strip():
            self.show_error("Input is empty.")
            self.set_status("Ready")
            return

        from_fmt = self.from_var.get()
        to_fmt = self.to_var.get()
        try:
            result = pandoc_convert(src, from_fmt, to_fmt)
            self.output_text.delete("1.0", tk.END)
            self.output_text.insert(tk.END, result)
            self.update_preview(result, to_fmt)
            self.set_status("Conversion successful.")
        except Exception as exc:
            self.show_error(str(exc))
            self.set_status("Error")

    def update_preview(self, content: str, fmt: str):
        if fmt != "html":
            if self.preview_label:
                self.preview_label.set_html("<p>Preview only available for HTML output.</p>")
            return
        if not self.preview_label:
            return
        self.preview_label.set_html(content)

    def set_status(self, message: str):
        self.status_var.set(message)

    def show_error(self, message: str):
        messagebox.showerror("Conversion Error", message)

    def copy_output(self):
        output = self.output_text.get("1.0", tk.END).rstrip("\n")
        if not output:
            self.show_error("There is no output to copy.")
            return
        self.clipboard_clear()
        self.clipboard_append(output)
        self.set_status("Output copied to clipboard.")

if __name__ == "__main__":
    try:
        subprocess.run(
            ["pandoc", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        messagebox.showerror(
            "Pandoc Not Found",
            "Pandoc executable was not found on your system.\n"
            "Please install Pandoc and ensure it is available in your PATH.",
        )
        sys.exit(1)

    app = PandocGUI()
    app.mainloop()
