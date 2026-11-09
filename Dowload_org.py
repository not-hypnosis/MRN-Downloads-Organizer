import json
import os
import queue
import threading
import tkinter as tk
import webbrowser
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
    "accent_soft": "#1c3556",
    "green": "#54c49a",
    "orange": "#e9ad64",
    "red": "#e47e85",
    "line": "#29384c",
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

CATEGORY_ICONS = {
    "Images": "▧",
    "PDFs": "▤",
    "Documents": "▤",
    "Presentations": "▥",
    "Spreadsheets": "▦",
    "Archives": "▱",
    "Videos": "▷",
    "Audio": "♫",
    "Installers": "⬇",
    "Code": "</>",
    "Others": "···",
}


def get_config_path():
    app_data = os.environ.get("APPDATA")
    if app_data:
        base = Path(app_data)
    else:
        base = Path.home() / "AppData" / "Roaming"
    return base / "MRN Downloads Organizer" / "settings.json"


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


def scan_folder(folder, progress_callback=None):
    folder = Path(folder)
    if not folder.is_dir():
        raise OSError("The selected folder is no longer available.")
    if is_drive_root(folder):
        raise ValueError("For safety, a drive root cannot be scanned.")

    files_by_category = {category: [] for category in CATEGORIES}
    with os.scandir(folder) as entries:
        for index, entry in enumerate(entries, start=1):
            if progress_callback:
                progress_callback(index)
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


def move_files(folder, planned_files, progress_callback=None):
    moved = []
    skipped = []
    failed = []
    folder = Path(folder)

    for index, (category, source) in enumerate(planned_files, start=1):
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
        finally:
            if progress_callback:
                progress_callback(index)

    return moved, skipped, failed


class DownloadsOrganizer:
    NAV_ITEMS = (
        ("Dashboard", "⌂"),
        ("Organizer", "↗"),
        ("Categories", "▦"),
        ("Settings", "⚙"),
        ("About", "i"),
    )

    def __init__(self, root):
        self.root = root
        self.root.title("{}  |  Version 1.1".format(APP_TITLE))
        self.root.geometry("1160x780")
        self.root.minsize(900, 640)
        self.root.configure(bg=COLORS["background"])
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.settings = {
            "remember_last_folder": False,
            "open_after_organizing": False,
        }
        self.config_error = self._load_settings()
        self.folder_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Select a folder to begin.")
        self.progress_text_var = tk.StringVar(value="Ready")
        self.files_by_category = None
        self.total_files = 0
        self.ready_files = 0
        self.last_results = None
        self.current_page = "Dashboard"
        self.busy = False
        self.worker_messages = queue.Queue()
        self.nav_buttons = {}
        self.category_count_labels = {}
        self._configure_styles()
        self._build_interface()

        remembered = self.settings.get("last_folder", "")
        if self.settings["remember_last_folder"] and remembered:
            remembered_path = Path(remembered)
            if remembered_path.is_dir() and not is_drive_root(remembered_path):
                self.folder_var.set(str(remembered_path.resolve()))
        self.folder_var.trace_add("write", self._folder_changed)
        self._refresh_metrics()
        if self.config_error:
            self.status_var.set(self.config_error)
        self.root.after(100, self._process_worker_messages)

    def _load_settings(self):
        try:
            with get_config_path().open("r", encoding="utf-8") as settings_file:
                stored = json.load(settings_file)
            if not isinstance(stored, dict):
                raise ValueError("Settings data must be a JSON object.")
            for key in ("remember_last_folder", "open_after_organizing"):
                if isinstance(stored.get(key), bool):
                    self.settings[key] = stored[key]
            if isinstance(stored.get("last_folder"), str):
                self.settings["last_folder"] = stored["last_folder"]
            return ""
        except FileNotFoundError:
            return ""
        except (OSError, json.JSONDecodeError, ValueError) as error:
            return "Could not read settings: {}".format(error)

    def _save_settings(self):
        path = get_config_path()
        payload = {
            "remember_last_folder": self.remember_folder_var.get(),
            "open_after_organizing": self.open_after_var.get(),
        }
        if payload["remember_last_folder"] and self.folder_var.get():
            payload["last_folder"] = self.folder_var.get()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as settings_file:
                json.dump(payload, settings_file, indent=2)
            self.settings.update(payload)
            self.settings_message_var.set("Preferences saved on this computer.")
            if not self.busy:
                self.status_var.set("Preferences saved.")
        except OSError as error:
            self.settings_message_var.set("Could not save preferences: {}".format(error))
            self.status_var.set("Could not save preferences: {}".format(error))

    def _on_close(self):
        if self.busy:
            messagebox.showinfo(
                APP_TITLE,
                "Please wait for the current operation to finish before closing.",
                parent=self.root,
            )
            return
        if hasattr(self, "remember_folder_var"):
            self._save_settings()
        self.root.destroy()

    def _configure_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            ".", background=COLORS["background"], foreground=COLORS["text"],
            font=("Segoe UI", 10),
        )
        style.configure("TFrame", background=COLORS["background"])
        style.configure("Panel.TFrame", background=COLORS["panel"])
        style.configure("Panel2.TFrame", background=COLORS["panel_light"])
        style.configure(
            "TLabel", background=COLORS["background"], foreground=COLORS["text"],
        )
        style.configure(
            "Panel.TLabel", background=COLORS["panel"], foreground=COLORS["text"],
        )
        style.configure(
            "Panel2.TLabel", background=COLORS["panel_light"],
            foreground=COLORS["text"],
        )
        style.configure(
            "Muted.TLabel", background=COLORS["panel"], foreground=COLORS["muted"],
        )
        style.configure(
            "Title.TLabel", font=("Segoe UI Semibold", 24),
            background=COLORS["background"], foreground=COLORS["text"],
        )
        style.configure(
            "Section.TLabel", font=("Segoe UI Semibold", 13),
            background=COLORS["panel"], foreground=COLORS["text"],
        )
        style.configure(
            "Subtitle.TLabel", font=("Segoe UI", 10),
            background=COLORS["background"], foreground=COLORS["muted"],
        )
        style.configure(
            "Metric.TLabel", font=("Segoe UI Semibold", 24),
            background=COLORS["panel"], foreground=COLORS["text"],
        )
        style.configure(
            "TButton", padding=(12, 9), background=COLORS["panel_light"],
            foreground=COLORS["text"], borderwidth=0, focusthickness=0,
        )
        style.map(
            "TButton",
            background=[("active", "#2b3b50"), ("disabled", COLORS["panel_light"])],
            foreground=[("disabled", "#748196")],
        )
        style.configure(
            "Accent.TButton", padding=(15, 10), background=COLORS["accent"],
            foreground="#ffffff", font=("Segoe UI Semibold", 10), borderwidth=0,
        )
        style.map("Accent.TButton", background=[("active", COLORS["accent_hover"])])
        style.configure(
            "Treeview", background=COLORS["panel"], fieldbackground=COLORS["panel"],
            foreground=COLORS["text"], rowheight=34, borderwidth=0,
        )
        style.configure(
            "Treeview.Heading", background=COLORS["panel_light"],
            foreground=COLORS["muted"], font=("Segoe UI Semibold", 9),
            padding=(8, 9), borderwidth=0,
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
        style.configure(
            "TProgressbar", troughcolor=COLORS["panel_light"],
            background=COLORS["accent"], borderwidth=0, thickness=8,
        )
        style.configure(
            "TCheckbutton", background=COLORS["panel"], foreground=COLORS["text"],
            font=("Segoe UI", 10),
        )
        style.map(
            "TCheckbutton",
            background=[("active", COLORS["panel"])],
            foreground=[("active", COLORS["text"])],
        )

    def _build_interface(self):
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        sidebar = tk.Frame(self.root, bg="#131d2b", width=218)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)
        sidebar.rowconfigure(7, weight=1)
        brand = tk.Frame(sidebar, bg="#131d2b")
        brand.pack(fill="x", padx=22, pady=(26, 34))
        tk.Label(
            brand, text="MRN", bg="#131d2b", fg=COLORS["accent"],
            font=("Segoe UI Semibold", 12),
        ).pack(anchor="w")
        tk.Label(
            brand, text="Downloads\nOrganizer", bg="#131d2b", fg=COLORS["text"],
            justify="left", font=("Segoe UI Semibold", 16),
        ).pack(anchor="w", pady=(5, 0))

        tk.Label(
            sidebar, text="WORKSPACE", bg="#131d2b", fg="#74849a",
            font=("Segoe UI Semibold", 8),
        ).pack(anchor="w", padx=22, pady=(0, 10))
        for label, icon in self.NAV_ITEMS:
            button = tk.Button(
                sidebar, text="  {}   {}".format(icon, label),
                command=lambda page=label: self._show_page(page),
                anchor="w", relief="flat", borderwidth=0, cursor="hand2",
                padx=13, pady=11, bg="#131d2b", fg=COLORS["muted"],
                activebackground=COLORS["accent_soft"],
                activeforeground=COLORS["text"],
                font=("Segoe UI Semibold", 10),
            )
            button.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[label] = button

        sidebar_footer = tk.Frame(sidebar, bg="#131d2b")
        sidebar_footer.pack(side="bottom", fill="x", padx=22, pady=20)
        ttk.Separator(sidebar_footer).pack(fill="x", pady=(0, 12))
        tk.Label(
            sidebar_footer, text="VERSION 1.1", bg="#131d2b", fg="#74849a",
            font=("Segoe UI Semibold", 8),
        ).pack(anchor="w")

        workspace = ttk.Frame(self.root, padding=(32, 24, 32, 20))
        workspace.grid(row=0, column=1, sticky="nsew")
        workspace.columnconfigure(0, weight=1)
        workspace.rowconfigure(1, weight=1)

        header = ttk.Frame(workspace)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header.columnconfigure(0, weight=1)
        self.page_title_var = tk.StringVar()
        self.page_subtitle_var = tk.StringVar()
        ttk.Label(header, textvariable=self.page_title_var, style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            header, textvariable=self.page_subtitle_var, style="Subtitle.TLabel"
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.header_status = ttk.Label(
            header, textvariable=self.status_var, style="Subtitle.TLabel",
            wraplength=230, justify="right",
        )
        self.header_status.grid(row=0, column=1, rowspan=2, sticky="e", padx=(20, 0))

        self.page_host = ttk.Frame(workspace)
        self.page_host.grid(row=1, column=0, sticky="nsew")
        self.page_host.columnconfigure(0, weight=1)
        self.page_host.rowconfigure(0, weight=1)
        self.pages = {}
        self._build_dashboard()
        self._build_organizer()
        self._build_categories()
        self._build_settings()
        self._build_about()
        self._show_page("Dashboard")

    def _new_page(self, name):
        frame = ttk.Frame(self.page_host)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        self.pages[name] = frame
        return frame

    def _build_metric_card(self, parent, title, variable, note, column):
        card = ttk.Frame(parent, style="Panel.TFrame", padding=(18, 16))
        card.grid(row=0, column=column, sticky="nsew", padx=(0, 12 if column < 2 else 0))
        ttk.Label(card, text=title.upper(), style="Muted.TLabel").pack(anchor="w")
        ttk.Label(card, textvariable=variable, style="Metric.TLabel").pack(
            anchor="w", pady=(11, 3)
        )
        ttk.Label(card, text=note, style="Muted.TLabel").pack(anchor="w")
        return card

    def _build_dashboard(self):
        page = self._new_page("Dashboard")
        page.rowconfigure(2, weight=1)
        metrics = ttk.Frame(page)
        metrics.grid(row=0, column=0, sticky="ew")
        for column in range(3):
            metrics.columnconfigure(column, weight=1, uniform="metrics")
        self.dashboard_total_var = tk.StringVar(value="0")
        self.dashboard_ready_var = tk.StringVar(value="0")
        self.dashboard_categories_var = tk.StringVar(value="0")
        self._build_metric_card(
            metrics, "Files scanned", self.dashboard_total_var,
            "In the selected folder", 0
        )
        self._build_metric_card(
            metrics, "Ready to organize", self.dashboard_ready_var,
            "Awaiting your confirmation", 1
        )
        self._build_metric_card(
            metrics, "Categories", self.dashboard_categories_var,
            "With detected files", 2
        )

        folder_card = ttk.Frame(page, style="Panel.TFrame", padding=(20, 16))
        folder_card.grid(row=1, column=0, sticky="ew", pady=14)
        ttk.Label(folder_card, text="CURRENT FOLDER", style="Muted.TLabel").pack(anchor="w")
        self.dashboard_folder_var = tk.StringVar(value="No folder selected")
        ttk.Label(
            folder_card, textvariable=self.dashboard_folder_var, style="Panel.TLabel",
            font=("Segoe UI Semibold", 11), wraplength=760,
        ).pack(anchor="w", pady=(8, 0))

        bottom = ttk.Frame(page)
        bottom.grid(row=2, column=0, sticky="nsew")
        bottom.columnconfigure(0, weight=1)
        bottom.rowconfigure(0, weight=1)
        activity = ttk.Frame(bottom, style="Panel.TFrame", padding=(20, 18))
        activity.grid(row=0, column=0, sticky="nsew")
        activity.columnconfigure(0, weight=1)
        ttk.Label(activity, text="Recent activity", style="Section.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.activity_var = tk.StringVar(
            value="Your scan and organization summaries will appear here."
        )
        ttk.Label(
            activity, textvariable=self.activity_var, style="Muted.TLabel",
            wraplength=700, justify="left",
        ).grid(row=1, column=0, sticky="nw", pady=(13, 4))
        ttk.Button(
            activity, text="Go to Organizer", style="Accent.TButton",
            command=lambda: self._show_page("Organizer"),
        ).grid(row=2, column=0, sticky="w", pady=(15, 0))

    def _build_organizer(self):
        page = self._new_page("Organizer")
        page.columnconfigure(0, weight=1)
        page.rowconfigure(3, weight=1)

        folder_card = ttk.Frame(page, style="Panel.TFrame", padding=(18, 16))
        folder_card.grid(row=0, column=0, sticky="ew")
        folder_card.columnconfigure(0, weight=1)
        ttk.Label(folder_card, text="FOLDER TO ORGANIZE", style="Muted.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 9)
        )
        self.folder_entry = ttk.Entry(
            folder_card, textvariable=self.folder_var, state="readonly"
        )
        self.folder_entry.grid(row=1, column=0, sticky="ew", padx=(0, 9))
        self.folder_buttons = []
        browse = ttk.Button(folder_card, text="Browse", command=self._browse)
        browse.grid(row=1, column=1, padx=(0, 8))
        downloads = ttk.Button(
            folder_card, text="Downloads", command=self._select_downloads
        )
        downloads.grid(row=1, column=2)
        self.folder_buttons.extend((browse, downloads))

        actions = ttk.Frame(page)
        actions.grid(row=1, column=0, sticky="ew", pady=(14, 11))
        self.scan_button = ttk.Button(
            actions, text="Scan folder", command=self._scan, state="disabled"
        )
        self.scan_button.pack(side="left")
        self.preview_button = ttk.Button(
            actions, text="Preview & organize", style="Accent.TButton",
            command=self._show_preview, state="disabled",
        )
        self.preview_button.pack(side="left", padx=(9, 0))
        self.results_button = ttk.Button(
            actions, text="View results", command=self._show_results,
            state="disabled",
        )
        self.results_button.pack(side="left", padx=(9, 0))
        self.open_folder_button = ttk.Button(
            actions, text="Open folder", command=self._open_folder,
            state="disabled",
        )
        self.open_folder_button.pack(side="right")

        progress_card = ttk.Frame(page, style="Panel.TFrame", padding=(16, 12))
        progress_card.grid(row=2, column=0, sticky="ew", pady=(0, 13))
        progress_card.columnconfigure(0, weight=1)
        self.progress_bar = ttk.Progressbar(
            progress_card, mode="determinate", maximum=100, value=0
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        ttk.Label(
            progress_card, textvariable=self.progress_text_var, style="Muted.TLabel"
        ).grid(row=1, column=0, sticky="w", pady=(7, 0))

        results_card = ttk.Frame(page, style="Panel.TFrame", padding=12)
        results_card.grid(row=3, column=0, sticky="nsew")
        results_card.columnconfigure(0, weight=1)
        results_card.rowconfigure(1, weight=1)
        heading = ttk.Frame(results_card, style="Panel.TFrame")
        heading.grid(row=0, column=0, sticky="ew", padx=6, pady=(3, 10))
        heading.columnconfigure(0, weight=1)
        ttk.Label(heading, text="Scan & organization results", style="Section.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.organizer_summary_var = tk.StringVar(value="No scan yet")
        ttk.Label(
            heading, textvariable=self.organizer_summary_var, style="Muted.TLabel"
        ).grid(row=0, column=1, sticky="e")
        self.organizer_tree = ttk.Treeview(
            results_card,
            columns=("category", "count", "result"),
            show="headings", selectmode="none",
        )
        self.organizer_tree.heading("category", text="CATEGORY")
        self.organizer_tree.heading("count", text="FILES", anchor="e")
        self.organizer_tree.heading("result", text="LATEST RESULT")
        self.organizer_tree.column("category", width=230)
        self.organizer_tree.column("count", width=90, anchor="e", stretch=False)
        self.organizer_tree.column("result", width=300)
        self.organizer_tree.grid(row=1, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(
            results_card, orient="vertical", command=self.organizer_tree.yview
        )
        scroll.grid(row=1, column=1, sticky="ns")
        self.organizer_tree.configure(yscrollcommand=scroll.set)
        self._fill_organizer_tree()

    def _build_categories(self):
        page = self._new_page("Categories")
        page.columnconfigure((0, 1, 2), weight=1, uniform="category")
        page.rowconfigure((1, 2, 3, 4), weight=1, uniform="category")
        ttk.Label(
            page, text="Files are grouped by their extension. Unsupported types go to Others.",
            style="Subtitle.TLabel", wraplength=800,
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))
        for index, category in enumerate(CATEGORIES):
            row = index // 3 + 1
            column = index % 3
            card = ttk.Frame(page, style="Panel.TFrame", padding=(15, 13))
            card.grid(
                row=row, column=column, sticky="nsew",
                padx=(0, 10 if column < 2 else 0), pady=(0, 10),
            )
            card.columnconfigure(1, weight=1)
            ttk.Label(
                card, text=CATEGORY_ICONS[category], style="Panel.TLabel",
                font=("Segoe UI Semibold", 17), foreground=COLORS["accent"],
            ).grid(row=0, column=0, rowspan=2, sticky="w", padx=(0, 12))
            ttk.Label(card, text=category, style="Section.TLabel").grid(
                row=0, column=1, sticky="w"
            )
            count_var = tk.StringVar(value="0 files detected")
            self.category_count_labels[category] = count_var
            ttk.Label(card, textvariable=count_var, style="Muted.TLabel").grid(
                row=1, column=1, sticky="w", pady=(4, 0)
            )

    def _build_settings(self):
        page = self._new_page("Settings")
        page.rowconfigure(1, weight=1)
        card = ttk.Frame(page, style="Panel.TFrame", padding=(22, 22))
        card.grid(row=0, column=0, sticky="new")
        card.columnconfigure(0, weight=1)
        ttk.Label(card, text="Preferences", style="Section.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            card,
            text="Choose what the organizer remembers and does after a successful run.",
            style="Muted.TLabel", wraplength=650,
        ).grid(row=1, column=0, sticky="w", pady=(7, 20))
        self.remember_folder_var = tk.BooleanVar(
            value=self.settings["remember_last_folder"]
        )
        self.open_after_var = tk.BooleanVar(
            value=self.settings["open_after_organizing"]
        )
        ttk.Checkbutton(
            card, text="Remember the last selected folder",
            variable=self.remember_folder_var, command=self._save_settings,
        ).grid(row=2, column=0, sticky="w", pady=(0, 14))
        ttk.Checkbutton(
            card, text="Open the folder after organizing",
            variable=self.open_after_var, command=self._save_settings,
        ).grid(row=3, column=0, sticky="w")
        ttk.Separator(card).grid(row=4, column=0, sticky="ew", pady=20)
        self.settings_message_var = tk.StringVar(
            value="Preferences are stored in your Windows user profile."
        )
        ttk.Label(
            card, textvariable=self.settings_message_var, style="Muted.TLabel",
            wraplength=700,
        ).grid(row=5, column=0, sticky="w")

    def _build_about(self):
        page = self._new_page("About")
        page.rowconfigure(0, weight=1)
        card = ttk.Frame(page, style="Panel.TFrame", padding=(30, 30))
        card.grid(row=0, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        ttk.Label(
            card, text="MRN", style="Panel.TLabel",
            font=("Segoe UI Semibold", 12), foreground=COLORS["accent"],
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            card, text="Downloads Organizer", style="Panel.TLabel",
            font=("Segoe UI Semibold", 25),
        ).grid(row=1, column=0, sticky="w", pady=(8, 3))
        ttk.Label(
            card, text="Version 1.1  ·  Built with Python and Tkinter",
            style="Muted.TLabel",
        ).grid(row=2, column=0, sticky="w", pady=(3, 22))
        ttk.Separator(card).grid(row=3, column=0, sticky="ew", pady=(0, 20))
        ttk.Label(
            card,
            text=(
                "A focused desktop utility for organizing files in a folder you "
                "choose. Review every proposed move before anything changes. "
                "Files are never deleted or overwritten, and subfolders are not "
                "scanned."
            ),
            style="Panel.TLabel", wraplength=700, justify="left",
        ).grid(row=4, column=0, sticky="nw")

    def _show_page(self, page_name):
        self.current_page = page_name
        self.page_title_var.set(page_name)
        subtitles = {
            "Dashboard": "A clear overview of your file organization.",
            "Organizer": "Scan a chosen folder, review the plan, then organize.",
            "Categories": "See supported file types and the current scan counts.",
            "Settings": "Control local preferences for this application.",
            "About": "A safer, simpler way to keep folders organized.",
        }
        self.page_subtitle_var.set(subtitles[page_name])
        self.pages[page_name].tkraise()
        for name, button in self.nav_buttons.items():
            active = name == page_name
            button.configure(
                bg=COLORS["accent_soft"] if active else "#131d2b",
                fg=COLORS["text"] if active else COLORS["muted"],
            )
        self._refresh_header_status()

    def _refresh_header_status(self):
        if self.busy:
            return
        if self.folder_var.get():
            self.status_var.set("Folder selected")
        else:
            self.status_var.set("Select a folder to begin.")

    def _refresh_metrics(self):
        if hasattr(self, "dashboard_total_var"):
            self.dashboard_total_var.set(str(self.total_files))
            self.dashboard_ready_var.set(str(self.ready_files))
            detected = sum(1 for count in self._category_counts().values() if count)
            self.dashboard_categories_var.set(str(detected))
            self.dashboard_folder_var.set(
                self.folder_var.get() or "No folder selected"
            )
        if hasattr(self, "category_count_labels"):
            counts = self._category_counts()
            for category, variable in self.category_count_labels.items():
                count = counts.get(category, 0)
                variable.set("{} file{}".format(count, "" if count == 1 else "s"))

    def _category_counts(self):
        if self.files_by_category is None:
            return {}
        return {
            category: len(files)
            for category, files in self.files_by_category.items()
        }

    def _fill_organizer_tree(self, results=None):
        for item in self.organizer_tree.get_children():
            self.organizer_tree.delete(item)
        counts = self._category_counts()
        result_counts = {}
        if results:
            moved, skipped, failed = results
            for _, category in moved:
                result_counts[category] = result_counts.get(category, 0) + 1
            for _ in skipped:
                result_counts["Skipped"] = result_counts.get("Skipped", 0) + 1
            for _ in failed:
                result_counts["Failed"] = result_counts.get("Failed", 0) + 1
        for category in CATEGORIES:
            count = counts.get(category, 0)
            result = "{} moved".format(result_counts.get(category, 0))
            self.organizer_tree.insert(
                "", "end", values=(category, count if self.files_by_category is not None else "—", result)
            )
        if results:
            moved, skipped, failed = results
            if skipped:
                self.organizer_tree.insert("", "end", values=("Skipped", len(skipped), "Review source files"))
            if failed:
                self.organizer_tree.insert("", "end", values=("Failed", len(failed), "See status and retry"))

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
            title="Choose a folder to organize",
            initialdir=self.folder_var.get() or str(Path.home()),
            mustexist=True, parent=self.root,
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

    def _folder_changed(self, *_):
        self.files_by_category = None
        self.total_files = 0
        self.ready_files = 0
        self.last_results = None
        self.organizer_summary_var.set("No scan yet")
        self.progress_text_var.set("Ready")
        self.progress_bar.configure(mode="determinate", maximum=100, value=0)
        self.preview_button.configure(state="disabled")
        self.scan_button.configure(
            state="normal" if self.folder_var.get() and not self.busy else "disabled"
        )
        self.results_button.configure(state="disabled")
        self.open_folder_button.configure(
            state="normal" if self.folder_var.get() else "disabled"
        )
        self._fill_organizer_tree()
        self._refresh_metrics()
        self._refresh_header_status()
        if self.remember_folder_var.get():
            self._save_settings()

    def _set_busy(self, busy, operation=""):
        self.busy = busy
        state = "disabled" if busy else "normal"
        for button in self.folder_buttons:
            button.configure(state=state)
        self.scan_button.configure(state=state if self.folder_var.get() else "disabled")
        self.preview_button.configure(
            state="disabled" if busy or self.ready_files == 0 else "normal"
        )
        self.results_button.configure(
            state="disabled" if busy or self.last_results is None else "normal"
        )
        self.open_folder_button.configure(
            state="disabled" if busy or not self.folder_var.get() else "normal"
        )
        if busy:
            self.status_var.set(operation)
        else:
            self._refresh_header_status()

    def _scan(self):
        if self.busy or not self.folder_var.get():
            return
        folder = Path(self.folder_var.get())
        self._set_busy(True, "Scanning selected folder…")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start(10)
        self.progress_text_var.set("Scanning immediate folder contents…")

        def worker():
            try:
                def report_progress(count):
                    if count == 1 or count % 100 == 0:
                        self.worker_messages.put(("scan_progress", count))

                result = scan_folder(
                    folder,
                    progress_callback=report_progress,
                )
                self.worker_messages.put(("scan_done", result))
            except (OSError, ValueError) as error:
                self.worker_messages.put(("scan_error", str(error)))
            except Exception as error:
                self.worker_messages.put(("scan_error", "Unexpected scan error: {}".format(error)))

        threading.Thread(target=worker, daemon=True).start()

    def _show_preview(self):
        if self.busy or self.files_by_category is None:
            return
        planned_files = [
            (category, file_path)
            for category, files in self.files_by_category.items()
            for file_path in files
        ]
        if not planned_files:
            messagebox.showinfo(
                APP_TITLE, "No files are available to organize.", parent=self.root
            )
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
        summary = "   ·   ".join(
            "{} {}".format(category, count) for category, count in counts.items()
        )
        ttk.Label(
            dialog, text="Review files to be moved", style="Title.TLabel"
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(20, 4))
        ttk.Label(
            dialog, text=summary, style="Subtitle.TLabel", wraplength=700
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
            actions, text="Confirm & move", style="Accent.TButton",
            command=lambda: self._confirm_organization(dialog, planned_files),
        ).grid(row=0, column=2)

    def _confirm_organization(self, dialog, planned_files):
        folder = Path(self.folder_var.get())
        if not folder.is_dir() or is_drive_root(folder):
            messagebox.showerror(
                APP_TITLE, "The selected folder is no longer available.",
                parent=dialog,
            )
            return
        if not messagebox.askyesno(
            APP_TITLE,
            "Move {} file{} into category folders in:\n\n{}\n\n"
            "Files will not be deleted or overwritten.".format(
                len(planned_files), "" if len(planned_files) == 1 else "s", folder
            ),
            parent=dialog,
        ):
            return
        dialog.destroy()
        self._organize(folder, planned_files)

    def _organize(self, folder, planned_files):
        if self.busy:
            return
        self.last_results = None
        self._set_busy(True, "Organizing files…")
        self.progress_bar.stop()
        self.progress_bar.configure(
            mode="determinate", maximum=max(len(planned_files), 1), value=0
        )
        self.progress_text_var.set("Preparing to move {} files…".format(len(planned_files)))

        def worker():
            try:
                progress_step = max(1, len(planned_files) // 100)

                def report_progress(count):
                    if count % progress_step == 0 or count == len(planned_files):
                        self.worker_messages.put(
                            ("move_progress", (count, len(planned_files)))
                        )

                results = move_files(
                    folder, planned_files,
                    progress_callback=report_progress,
                )
                self.worker_messages.put(("move_done", results))
            except Exception as error:
                self.worker_messages.put(
                    ("move_error", "Unexpected organization error: {}".format(error))
                )

        threading.Thread(target=worker, daemon=True).start()

    def _process_worker_messages(self):
        try:
            while True:
                message, payload = self.worker_messages.get_nowait()
                if message == "scan_progress":
                    self.progress_text_var.set(
                        "Checking {} folder entr{}".format(
                            payload, "y" if payload == 1 else "ies"
                        )
                    )
                elif message == "scan_done":
                    self.progress_bar.stop()
                    self.progress_bar.configure(mode="determinate", maximum=100, value=100)
                    self.files_by_category = payload
                    self.total_files = sum(len(files) for files in payload.values())
                    self.ready_files = self.total_files
                    self.last_results = None
                    self.organizer_summary_var.set(
                        "{} file{} scanned".format(
                            self.total_files, "" if self.total_files == 1 else "s"
                        )
                    )
                    self.progress_text_var.set("Scan complete")
                    self.activity_var.set(
                        "Last scan found {} file{} ready to organize.".format(
                            self.total_files, "" if self.total_files == 1 else "s"
                        )
                    )
                    self._fill_organizer_tree()
                    self._refresh_metrics()
                    self._set_busy(False)
                    self.preview_button.configure(
                        state="normal" if self.total_files else "disabled"
                    )
                elif message == "scan_error":
                    self.progress_bar.stop()
                    self.progress_bar.configure(mode="determinate", value=0)
                    self.progress_text_var.set("Scan did not complete")
                    self._set_busy(False)
                    messagebox.showerror(APP_TITLE, payload, parent=self.root)
                elif message == "refresh_done":
                    self.files_by_category = payload
                    self.total_files = sum(len(files) for files in payload.values())
                    self.ready_files = self.total_files
                    moved, skipped, failed = self.last_results
                    self.organizer_summary_var.set(
                        "{} moved  ·  {} skipped  ·  {} failed  ·  {} remaining".format(
                            len(moved), len(skipped), len(failed), self.total_files
                        )
                    )
                    self.progress_text_var.set("Folder summary refreshed")
                    self._fill_organizer_tree(self.last_results)
                    self._refresh_metrics()
                    self._set_busy(False)
                    self.preview_button.configure(
                        state="normal" if self.ready_files else "disabled"
                    )
                elif message == "refresh_error":
                    self._set_busy(False)
                    self.status_var.set(
                        "Organization finished, but refresh failed: {}".format(payload)
                    )
                    messagebox.showerror(
                        APP_TITLE,
                        "Organization finished, but the folder summary could not be refreshed:\n{}".format(
                            payload
                        ),
                        parent=self.root,
                    )
                elif message == "move_progress":
                    count, total = payload
                    self.progress_bar.configure(value=count)
                    self.progress_text_var.set("Organizing {} of {} files…".format(count, total))
                elif message == "move_done":
                    moved, skipped, failed = payload
                    self.last_results = payload
                    self.ready_files = 0
                    self.results_button.configure(state="normal")
                    self.progress_bar.configure(value=self.progress_bar["maximum"])
                    self.progress_text_var.set("Organization complete")
                    self.organizer_summary_var.set(
                        "{} moved  ·  {} skipped  ·  {} failed".format(
                            len(moved), len(skipped), len(failed)
                        )
                    )
                    self.activity_var.set(
                        "Organization finished: {} moved, {} skipped, {} failed.".format(
                            len(moved), len(skipped), len(failed)
                        )
                    )
                    self._fill_organizer_tree(payload)
                    self._refresh_metrics()
                    self._set_busy(False)
                    self._refresh_after_organize()
                    if moved and self.open_after_var.get():
                        self._open_folder()
                elif message == "move_error":
                    self.progress_text_var.set("Organization stopped")
                    self._set_busy(False)
                    messagebox.showerror(APP_TITLE, payload, parent=self.root)
        except queue.Empty:
            pass
        self.root.after(100, self._process_worker_messages)

    def _refresh_after_organize(self):
        folder = Path(self.folder_var.get())
        self._set_busy(True, "Refreshing folder summary…")

        def worker():
            try:
                result = scan_folder(folder)
                self.worker_messages.put(("refresh_done", result))
            except (OSError, ValueError) as error:
                self.worker_messages.put(("refresh_error", str(error)))

        threading.Thread(target=worker, daemon=True).start()

    def _show_results(self):
        if self.last_results is None:
            return
        moved, skipped, failed = self.last_results
        result = tk.Toplevel(self.root)
        result.title("Organization results")
        result.geometry("760x560")
        result.minsize(600, 400)
        result.configure(bg=COLORS["background"])
        result.transient(self.root)
        result.columnconfigure(0, weight=1)
        result.rowconfigure(2, weight=1)
        processed = len(moved) + len(skipped) + len(failed)

        ttk.Label(
            result, text="Organization results", style="Title.TLabel"
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(20, 4))
        ttk.Label(
            result,
            text="{} moved  ·  {} skipped  ·  {} failed  ·  {} processed".format(
                len(moved), len(skipped), len(failed), processed
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
        results_tree.column("details", width=250)
        results_tree.grid(row=0, column=0, sticky="nsew")
        results_scroll = ttk.Scrollbar(
            table_frame, orient="vertical", command=results_tree.yview
        )
        results_scroll.grid(row=0, column=1, sticky="ns")
        results_tree.configure(yscrollcommand=results_scroll.set)
        for name, category in moved:
            results_tree.insert("", "end", values=("Moved", name, category))
        for name in skipped:
            results_tree.insert(
                "", "end", values=("Skipped", name, "No longer eligible")
            )
        for name, error in failed:
            results_tree.insert("", "end", values=("Failed", name, error))

        ttk.Button(
            result, text="Close", command=result.destroy,
        ).grid(row=3, column=0, sticky="e", padx=22, pady=(0, 20))

    def _open_folder(self):
        if not self.folder_var.get():
            return
        folder = Path(self.folder_var.get())
        if not folder.is_dir():
            messagebox.showerror(
                APP_TITLE, "The selected folder could not be found.", parent=self.root
            )
            return
        try:
            if hasattr(os, "startfile"):
                os.startfile(str(folder))
            else:
                webbrowser.open(folder.as_uri())
        except OSError as error:
            messagebox.showerror(
                APP_TITLE, "Could not open the selected folder:\n{}".format(error),
                parent=self.root,
            )

    def _close_results_and_scan(self, result):
        result.destroy()
        self._scan()


def main():
    root = tk.Tk()
    DownloadsOrganizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()