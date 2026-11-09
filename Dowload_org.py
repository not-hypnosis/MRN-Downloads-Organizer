import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


APP_TITLE = "MRN Downloads Organizer"
APP_FILE = Path(__file__).resolve()
COLORS = {
    "background": "#101722",
    "panel": "#182333",
    "panel_light": "#202e40",
    "text": "#e8eef7",
    "muted": "#9aa9bc",
    "accent": "#4388f5",
    "accent_hover": "#3477e3",
}

CATEGORIES = {
    "Images": {"jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "ico", "tif", "tiff"},
    "PDFs": {"pdf"},
    "Documents": {"doc", "docx", "txt", "rtf", "odt"},
    "Presentations": {"ppt", "pptx", "odp"},
    "Spreadsheets": {"xls", "xlsx", "csv", "ods"},
    "Archives": {"zip", "rar", "7z", "tar", "gz"},
    "Videos": {"mp4", "mkv", "avi", "mov", "wmv", "webm"},
    "Audio": {"mp3", "wav", "flac", "aac", "ogg", "m4a"},
    "Installers": {"exe", "msi"},
    "Code": {"c", "cpp", "h", "py", "js", "ts", "html", "css", "java", "json"},
    "Others": set(),
}

TEMPORARY_SUFFIXES = {
    ".tmp", ".temp", ".part", ".crdownload", ".download", ".partial",
    ".swp", ".swo", ".lock", ".bak",
}
def categorize_file(file_path):
    extension = file_path.suffix.lower().lstrip(".")
    for category, extensions in CATEGORIES.items():
        if extension in extensions:
            return category
    return "Others"


def is_temporary_file(file_path):
    name = file_path.name.lower()
    return name.startswith("~$") or file_path.suffix.lower() in TEMPORARY_SUFFIXES


def is_drive_root(folder):
    return folder == Path(folder.anchor)


def scan_folder(folder):
    folder = Path(folder)
    if not folder.is_dir():
        raise OSError("The selected folder is no longer available.")
    if is_drive_root(folder):
        raise ValueError("For safety, a drive root cannot be scanned.")

    files_by_category = {category: [] for category in CATEGORIES}
    with os.scandir(folder) as entries:
        for entry in entries:
            if not entry.is_file(follow_symlinks=False):
                continue
            file_path = Path(entry.path)
            if file_path.resolve() == APP_FILE or is_temporary_file(file_path):
                continue
            files_by_category[categorize_file(file_path)].append(file_path)
    return files_by_category


def unique_destination(destination):
    if not os.path.lexists(destination):
        return destination

    counter = 1
    while True:
        candidate = destination.with_name(
            "{}_{}{}".format(destination.stem, counter, destination.suffix)
        )
        if not os.path.lexists(candidate):
            return candidate
        counter += 1


def move_files(folder, planned_files):
    moved = []
    skipped = []
    failed = []
    folder = Path(folder)

    for category, source in planned_files:
        try:
            source = Path(source)
            if (source.parent.resolve() != folder.resolve()
                    or not source.is_file()
                    or source.is_symlink()
                    or source.resolve() == APP_FILE
                    or is_temporary_file(source)):
                skipped.append(source.name)
                continue

            destination_folder = folder / category
            destination_folder.mkdir(exist_ok=True)
            destination = unique_destination(destination_folder / source.name)
            # Rename is atomic on the same volume and won't overwrite an existing file.
            while True:
                try:
                    os.rename(source, destination)
                    moved.append((destination.name, category))
                    break
                except FileExistsError:
                    destination = unique_destination(destination_folder / source.name)
        except OSError as error:
            failed.append((Path(source).name, str(error)))

    return moved, skipped, failed


class DownloadsOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("940x700")
        self.root.minsize(760, 570)
        self.root.configure(bg=COLORS["background"])

        self.folder_var = tk.StringVar()
        self.total_var = tk.StringVar(value="No scan yet")
        self.status_var = tk.StringVar(value="Choose a folder to get started.")
        self.files_by_category = None

        self._configure_styles()
        self._build_interface()

    def _configure_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            ".", background=COLORS["background"], foreground=COLORS["text"],
            font=("Segoe UI", 10),
        )
        style.configure("TFrame", background=COLORS["background"])
        style.configure("Panel.TFrame", background=COLORS["panel"])
        style.configure(
            "TLabel", background=COLORS["background"], foreground=COLORS["text"],
        )
        style.configure(
            "Panel.TLabel", background=COLORS["panel"], foreground=COLORS["text"],
        )
        style.configure(
            "Muted.TLabel", background=COLORS["panel"], foreground=COLORS["muted"],
        )
        style.configure(
            "Title.TLabel", font=("Segoe UI Semibold", 21),
            background=COLORS["background"], foreground=COLORS["text"],
        )
        style.configure(
            "Subtitle.TLabel", font=("Segoe UI", 10),
            background=COLORS["background"], foreground=COLORS["muted"],
        )
        style.configure(
            "TButton", padding=(13, 9), background=COLORS["panel_light"],
            foreground=COLORS["text"], borderwidth=0, focusthickness=0,
        )
        style.map(
            "TButton",
            background=[("active", "#2b3b50"), ("disabled", COLORS["panel_light"])],
            foreground=[("disabled", "#748196")],
        )
        style.configure(
            "Accent.TButton", padding=(15, 9), background=COLORS["accent"],
            foreground="#ffffff", font=("Segoe UI Semibold", 10), borderwidth=0,
        )
        style.map("Accent.TButton", background=[("active", COLORS["accent_hover"])])
        style.configure(
            "Treeview", background=COLORS["panel"], fieldbackground=COLORS["panel"],
            foreground=COLORS["text"], rowheight=31, borderwidth=0,
        )
        style.configure(
            "Treeview.Heading", background=COLORS["panel_light"],
            foreground=COLORS["muted"], font=("Segoe UI Semibold", 9),
            padding=(8, 8), borderwidth=0,
        )
        style.map(
            "Treeview",
            background=[("selected", COLORS["accent"])],
            foreground=[("selected", "#ffffff")],
        )
        style.configure(
            "TEntry", padding=(10, 9), fieldbackground=COLORS["panel_light"],
            foreground=COLORS["text"], insertcolor=COLORS["text"], borderwidth=0,
        )

    def _build_interface(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        header = ttk.Frame(self.root, padding=(28, 24, 28, 16))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text=APP_TITLE, style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Sort files into clear categories. Nothing moves until you review and confirm.",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(5, 0))

        folder_panel = ttk.Frame(self.root, style="Panel.TFrame", padding=18)
        folder_panel.grid(row=1, column=0, sticky="ew", padx=28, pady=(0, 16))
        folder_panel.columnconfigure(0, weight=1)
        ttk.Label(folder_panel, text="FOLDER TO ORGANIZE", style="Muted.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 9)
        )
        self.folder_entry = ttk.Entry(
            folder_panel, textvariable=self.folder_var, state="readonly"
        )
        self.folder_entry.grid(row=1, column=0, sticky="ew", padx=(0, 9))
        ttk.Button(folder_panel, text="Browse Folder", command=self._browse).grid(
            row=1, column=1, padx=(0, 8)
        )
        ttk.Button(folder_panel, text="Downloads", command=self._select_downloads).grid(
            row=1, column=2
        )
        self.folder_var.trace_add("write", self._folder_changed)

        content = ttk.Frame(self.root, padding=(28, 0, 28, 12))
        content.grid(row=2, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)

        summary = ttk.Frame(content, style="Panel.TFrame", padding=(18, 14))
        summary.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        summary.columnconfigure(0, weight=1)
        ttk.Label(summary, text="Scan summary", style="Panel.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            summary, textvariable=self.total_var, style="Panel.TLabel",
            font=("Segoe UI Semibold", 11),
        ).grid(row=0, column=1, sticky="e")

        table_panel = ttk.Frame(content, style="Panel.TFrame", padding=12)
        table_panel.grid(row=1, column=0, sticky="nsew")
        table_panel.columnconfigure(0, weight=1)
        table_panel.rowconfigure(0, weight=1)
        self.category_tree = ttk.Treeview(
            table_panel, columns=("category", "count"), show="headings",
            selectmode="none",
        )
        self.category_tree.heading("category", text="CATEGORY")
        self.category_tree.heading("count", text="FILES FOUND", anchor="e")
        self.category_tree.column("category", anchor="w", width=250)
        self.category_tree.column("count", anchor="e", width=130, stretch=False)
        self.category_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(
            table_panel, orient="vertical", command=self.category_tree.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.category_tree.configure(yscrollcommand=scrollbar.set)
        self._show_empty_counts()

        footer = ttk.Frame(self.root, padding=(28, 4, 28, 20))
        footer.grid(row=3, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status_var, style="Subtitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.preview_button = ttk.Button(
            footer, text="Preview & Organize", style="Accent.TButton",
            command=self._show_preview, state="disabled",
        )
        self.preview_button.grid(row=0, column=2, padx=(8, 0))
        self.scan_button = ttk.Button(
            footer, text="Scan Files", command=self._scan, state="disabled"
        )
        self.scan_button.grid(row=0, column=1)

    def _show_empty_counts(self):
        for item in self.category_tree.get_children():
            self.category_tree.delete(item)
        for category in CATEGORIES:
            self.category_tree.insert("", "end", values=(category, "—"))

    def _folder_changed(self, *_):
        self.files_by_category = None
        self.total_var.set("No scan yet")
        self.status_var.set("Folder selected. Scan to see its files.")
        self.preview_button.configure(state="disabled")
        self.scan_button.configure(state="normal" if self.folder_var.get() else "disabled")
        self._show_empty_counts()

    def _set_folder(self, folder):
        folder = Path(folder)
        if not folder.is_dir():
            messagebox.showerror(APP_TITLE, "That folder could not be found.", parent=self.root)
            return
        if is_drive_root(folder):
            messagebox.showwarning(
                APP_TITLE, "For safety, a drive root cannot be selected.", parent=self.root
            )
            return
        self.folder_var.set(str(folder.resolve()))

    def _browse(self):
        selected = filedialog.askdirectory(
            title="Choose a folder to organize", mustexist=True, parent=self.root
        )
        if selected:
            self._set_folder(selected)

    def _select_downloads(self):
        downloads = Path.home() / "Downloads"
        if not downloads.is_dir():
            messagebox.showerror(
                APP_TITLE, "The Windows Downloads folder could not be found.",
                parent=self.root,
            )
            return
        self._set_folder(downloads)

    def _scan(self):
        folder = Path(self.folder_var.get())
        try:
            self.files_by_category = scan_folder(folder)
        except (OSError, ValueError) as error:
            messagebox.showerror(APP_TITLE, str(error), parent=self.root)
            return

        for item in self.category_tree.get_children():
            self.category_tree.delete(item)
        for category, files in self.files_by_category.items():
            self.category_tree.insert("", "end", values=(category, len(files)))

        total = sum(len(files) for files in self.files_by_category.values())
        self.total_var.set("{} file{}".format(total, "" if total == 1 else "s"))
        self.status_var.set("Scan complete. Review the preview before moving files.")
        self.preview_button.configure(state="normal" if total else "disabled")

    def _show_preview(self):
        if self.files_by_category is None:
            return

        planned_files = [
            (category, file_path)
            for category, files in self.files_by_category.items()
            for file_path in files
        ]
        if not planned_files:
            messagebox.showinfo(APP_TITLE, "No files are available to organize.", parent=self.root)
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Review organization")
        dialog.geometry("760x540")
        dialog.minsize(600, 400)
        dialog.configure(bg=COLORS["background"])
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(2, weight=1)

        counts = {}
        for category, _ in planned_files:
            counts[category] = counts.get(category, 0) + 1
        count_summary = "   ".join(
            "{}: {}".format(category, count)
            for category, count in counts.items()
        )
        ttk.Label(
            dialog, text="Review files to be moved", style="Title.TLabel"
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(20, 4))
        ttk.Label(
            dialog, text=count_summary, style="Subtitle.TLabel", wraplength=700
        ).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 14))

        table = ttk.Frame(dialog, style="Panel.TFrame", padding=10)
        table.grid(row=2, column=0, sticky="nsew", padx=22, pady=(0, 16))
        table.columnconfigure(0, weight=1)
        table.rowconfigure(0, weight=1)
        preview_tree = ttk.Treeview(
            table, columns=("file", "destination"), show="headings",
            selectmode="none",
        )
        preview_tree.heading("file", text="FILE")
        preview_tree.heading("destination", text="CATEGORY FOLDER")
        preview_tree.column("file", width=440)
        preview_tree.column("destination", width=200, stretch=False)
        preview_tree.grid(row=0, column=0, sticky="nsew")
        preview_scroll = ttk.Scrollbar(
            table, orient="vertical", command=preview_tree.yview
        )
        preview_scroll.grid(row=0, column=1, sticky="ns")
        preview_tree.configure(yscrollcommand=preview_scroll.set)
        for category, file_path in planned_files:
            preview_tree.insert("", "end", values=(file_path.name, category))

        actions = ttk.Frame(dialog, padding=(22, 0, 22, 20))
        actions.grid(row=3, column=0, sticky="ew")
        actions.columnconfigure(0, weight=1)
        ttk.Button(actions, text="Cancel", command=dialog.destroy).grid(
            row=0, column=1, padx=(0, 8)
        )
        ttk.Button(
            actions, text="Confirm & Move", style="Accent.TButton",
            command=lambda: self._confirm_organization(dialog, planned_files),
        ).grid(row=0, column=2)

    def _confirm_organization(self, dialog, planned_files):
        confirmed = messagebox.askyesno(
            APP_TITLE,
            "Move {} file{} into category folders in:\n\n{}\n\n"
            "Existing files will not be overwritten.".format(
                len(planned_files), "" if len(planned_files) == 1 else "s",
                self.folder_var.get(),
            ),
            parent=dialog,
        )
        if not confirmed:
            return

        dialog.destroy()
        moved, skipped, failed = move_files(
            Path(self.folder_var.get()), planned_files
        )
        self._show_results(moved, skipped, failed)
        self._scan()

    def _show_results(self, moved, skipped, failed):
        result = tk.Toplevel(self.root)
        result.title("Organization results")
        result.geometry("740x560")
        result.minsize(580, 400)
        result.configure(bg=COLORS["background"])
        result.transient(self.root)
        result.columnconfigure(0, weight=1)
        result.rowconfigure(2, weight=1)

        total = len(moved) + len(skipped) + len(failed)
        ttk.Label(
            result, text="Organization complete", style="Title.TLabel"
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(20, 3))
        ttk.Label(
            result,
            text="{} moved  ·  {} skipped  ·  {} failed  ·  {} processed".format(
                len(moved), len(skipped), len(failed), total
            ),
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 14))

        table_frame = ttk.Frame(result, style="Panel.TFrame", padding=10)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=22, pady=(0, 16))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        results_tree = ttk.Treeview(
            table_frame, columns=("status", "file", "details"),
            show="headings", selectmode="none",
        )
        results_tree.heading("status", text="STATUS")
        results_tree.heading("file", text="FILE")
        results_tree.heading("details", text="DETAILS")
        results_tree.column("status", width=95, stretch=False)
        results_tree.column("file", width=250)
        results_tree.column("details", width=230)
        results_tree.grid(row=0, column=0, sticky="nsew")
        results_scroll = ttk.Scrollbar(
            table_frame, orient="vertical", command=results_tree.yview
        )
        results_scroll.grid(row=0, column=1, sticky="ns")
        results_tree.configure(yscrollcommand=results_scroll.set)
        for name, category in moved:
            results_tree.insert("", "end", values=("Moved", name, category))
        for name in skipped:
            results_tree.insert("", "end", values=("Skipped", name, "No longer eligible"))
        for name, error in failed:
            results_tree.insert("", "end", values=("Failed", name, error))

        actions = ttk.Frame(result, padding=(22, 0, 22, 20))
        actions.grid(row=3, column=0, sticky="ew")
        actions.columnconfigure(0, weight=1)
        ttk.Button(
            actions, text="Scan Folder Again", style="Accent.TButton",
            command=lambda: self._close_results_and_scan(result),
        ).grid(row=0, column=1)

    def _close_results_and_scan(self, result):
        result.destroy()
        self._scan()


def main():
    root = tk.Tk()
    DownloadsOrganizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()