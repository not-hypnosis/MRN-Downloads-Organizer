# 📁 MRN Downloads Organizer

**Version 2.1 — Premium UI Redesign 🚀**

A lightweight Windows desktop utility that automatically organizes messy folders by sorting files into categorized directories based on their extensions.

Built with Python's standard library and Tkinter, MRN Downloads Organizer provides a polished desktop interface for managing files without manually sorting them.

Now featuring a **standalone Windows executable (.exe)**, so you can use the application without installing Python!

## ✨ Features

- **🎨 Premium Dark Interface** — A refined, modern desktop experience with improved contrast, typography, spacing, borders and visual consistency.
- **🧭 Five Navigation Pages** — Dashboard, Organizer, Categories, Settings and About.
- **📊 Interactive Dashboard** — View scanned and ready-to-organize file totals, detected categories, the selected folder and recent activity.
- **📂 Organizer Workspace** — Select a folder, use the Downloads shortcut, scan files and review organization results.
- **⚡ Quick Rescan** — Rescan the currently selected folder without selecting it again.
- **🗂️ Automatic File Categorization** — Sort files into supported categories based on their extensions.
- **📥 Downloads Shortcut** — Quickly access the Windows Downloads directory.
- **📋 Category Overview** — See supported categories and the detected file count for each.
- **👀 Organization Preview** — Review files and their destinations before confirming any moves.
- **🔎 Live Search and Sorting** — Filter preview and operation results by filename as you type. Sort by filename, extension, file size or category in ascending or descending order.
- **✅ Organization Confirmation Summary** — Review the number of files, categories involved and destination folder before moving files.
- **⚙️ Background Processing** — Scanning and organizing run in the background to keep the interface responsive.
- **📈 Progress Indicator** — Follow scan and organization progress.
- **📝 Per-file Results** — Review successfully moved, skipped and failed files.
- **📁 Open Organized Folder** — Open the selected folder after organizing, if enabled in Settings.
- **💾 Persistent Preferences** — Save the last-folder and open-after-organizing options, plus window size and position, in a JSON settings file in the Windows user application-data directory.
- **🧹 Clear Session** — Clear scan statistics, preview data and operation results after confirmation, without changing files or saved preferences.
- **🔔 Clear Feedback** — Get scan summaries, empty-folder and unsupported-file notices, organization completion status and partial-failure counts.
- **🛡️ Duplicate Protection** — Prevent accidental overwriting by generating unique filenames.
- **🔒 Safe File Handling** — Never delete files or recursively process subdirectories.
- **🖥️ Improved DPI Awareness** — Better display scaling and layout behavior across different Windows display settings.
- **🎯 Refined Visual Elements** — Custom Canvas-drawn category icons, improved navigation states, buttons, tables and scrollbars.

## 📂 Supported Categories

| Category | Examples |
|---|---|
| Images | JPG, PNG, GIF, WEBP, SVG |
| PDFs | PDF |
| Documents | DOC, DOCX, TXT, RTF |
| Presentations | PPT, PPTX, ODP |
| Spreadsheets | XLS, XLSX, CSV |
| Archives | ZIP, RAR, 7Z, TAR |
| Videos | MP4, MKV, AVI, MOV |
| Audio | MP3, WAV, FLAC, AAC |
| Installers | EXE, MSI |
| Code | C, CPP, PY, JS, TS, HTML, CSS |
| Others | Unsupported or missing extensions |

## 🛠️ Technology Stack

- **Language:** Python 3
- **GUI Framework:** Tkinter / ttk
- **Packaging:** PyInstaller
- **Icon:** Custom MRN application icon

The application itself uses Python's standard library only. No third-party runtime dependencies are required.

## 🚀 Getting Started

MRN Downloads Organizer V2.1 supports two ways to run the application.

### 🖥️ Option 1 — Standalone Windows Executable

The standalone executable is the easiest way to use the application.

1. Download `MRN Downloads Organizer.exe` from the [GitHub Releases](https://github.com/not-hypnosis/MRN-Downloads-Organizer/releases) page.
2. Run the executable.
3. Select a folder and start organizing!

**Requirements:**
- Windows 10 or Windows 11.
- No Python installation required.

### 💻 Option 2 — Run from Source

**Requirements:**
- Windows 10 or Windows 11.
- Python 3 installed.

Clone the repository:

```bash
git clone https://github.com/not-hypnosis/MRN-Downloads-Organizer.git
```

Navigate into the project directory:

```bash
cd MRN-Downloads-Organizer
```

Run the application:

```bash
python Dowload_org.py
```

## 📦 Building the Standalone EXE

To build your own standalone Windows executable from the source code:

Install PyInstaller:

```bash
python -m pip install pyinstaller
```

Build the application:

```bash
python -m PyInstaller --noconfirm --clean --onefile --windowed --icon=MRN.ico --name "MRN Downloads Organizer" Dowload_org.py
```

After a successful build, the executable will be available inside:

```text
dist/
└── MRN Downloads Organizer.exe
```

**Note:** PyInstaller is a build-time dependency only. It is not required to run the packaged application. Pillow was used as a development utility to generate the icon and is not required at runtime or for rebuilding when the provided `.ico` file is used.

## 🔒 Safety

MRN Downloads Organizer operates only on a folder explicitly selected by the user. It does not automatically select or organize a drive or drive root.

- 🚫 No automatic drive-wide organization or drive-root processing.
- 📁 Scanning is limited to the immediate contents of the selected folder; subfolders are not processed or moved.
- 🗑️ No file deletion.
- ♻️ No overwriting existing files.
- 🛡️ When a destination filename already exists, a unique filename is generated instead.
- ⚙️ The application's own source file or running executable and temporary files are excluded from scanning and organization.

**Always review the organization preview before confirming file operations.**

## 🗺️ Development Roadmap

- [x] Initial file organizer implementation.
- [x] Automatic file categorization.
- [x] Folder scanning and preview.
- [x] Duplicate filename protection.
- [x] Premium desktop interface and five-page navigation.
- [x] Persistent application settings and progress indicators.
- [x] Background scanning and organizing with per-file results.
- [x] Window geometry persistence, quick rescan, live search and sorting.
- [x] Clear Session and improved scan and organization feedback.
- [x] V1.3 visual refinement, category clarity and improved search and empty states.
- [x] V2.0 final stable release.
- [x] Standalone Windows executable with custom application icon.
- [x] V2.1 premium UI redesign and visual refinement.
- [x] Improved DPI awareness and display scaling.
- [x] Refined category icons, navigation, tables and scrollbars.

## 📌 Project Status

**Current Version:** 2.1

**Status:** Stable Release ✅

MRN Downloads Organizer V2.1 is a polished, fully packaged Windows desktop application with a standalone executable.

The project is maintained as a personal utility for the developer and friends.

---

Developed with ❤️ by **MRN** 👑

*Simple. Safe. Organized.*
