# MRN Downloads Organizer

**Version 1.3 — UI/UX Polish & Usability Improvements**

A lightweight Windows desktop utility that automatically organizes messy folders by sorting files into categorized directories based on their extensions.

Built with Python's standard library and Tkinter, this application provides a polished dark-themed desktop interface for managing files without manually sorting them.

## ✨ Features

- **Premium Dark Interface** — A clean, modern desktop experience with a dark navy palette and blue accents.
- **Five Navigation Pages** — Dashboard, Organizer, Categories, Settings and About.
- **Dashboard** — View scanned and ready-to-organize file totals, detected categories, the selected folder and recent activity.
- **Organizer Workspace** — Select a folder, use the Downloads shortcut, scan files and review organization results.
- **Quick Rescan** — Rescan the currently selected folder without selecting it again.
- **Automatic File Categorization** — Sort files into supported categories based on their extensions.
- **Downloads Shortcut** — Quickly access the Windows Downloads directory.
- **Category Overview** — See supported categories and the detected file count for each.
- **Organization Preview** — Review the files and destinations before confirming any moves.
- **Live Search and Sorting** — Filter preview and operation results by filename as you type; search is case-insensitive. Sort by filename, extension, file size or category in ascending or descending order.
- **Organization Confirmation Summary** — Before moving files, review the number of files, categories involved and the destination folder.
- **Background Work** — Scanning and organizing run in the background to keep the interface responsive.
- **Progress Indicator** — Follow scan and organization progress.
- **Per-file Results** — Review successfully moved, skipped and failed files.
- **Open Organized Folder** — Open the selected folder after organizing, if enabled in Settings.
- **Persistent Preferences** — Save the last-folder and open-after-organizing options, plus window size and position, in a JSON settings file in the Windows user application-data directory.
- **Clear Session** — Clear scan statistics, preview data and operation results after confirmation, without changing files or saved preferences.
- **Clear Feedback** — Get scan summaries, empty-folder and unsupported-file notices, organization completion status and partial-failure counts.
- **Refined User Interface** — Consistent typography, spacing, alignment, buttons and hover states across the application.
- **Improved Dashboard** — Clearer metric-card hierarchy and a more readable recent-activity summary.
- **Polished Organizer Workspace** — Refined folder and action controls, with consistent preview and results presentation.
- **Category Clarity** — Balanced cards for all 11 categories, including supported-extension descriptions and detected file counts.
- **Improved Search and Empty States** — Clearer filter and sort controls, live match counts, and readable messages when no files match.
- **Refined Settings and About Pages** — Improved spacing, alignment and typography consistent with the rest of the application.
- **Duplicate Protection** — Prevent accidental overwriting by generating unique filenames.
- **Safe File Handling** — Never delete files or recursively process subdirectories.

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

- Python 3
- Tkinter / ttk

The application uses Python's standard library only. No external dependencies are required.

## 🚀 Getting Started

### Requirements

- Windows 10 or Windows 11
- Python 3 installed

### Run Locally

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

## 🔒 Safety

MRN Downloads Organizer operates only on a folder explicitly selected by the user. It does not automatically select or organize a drive or drive root.

- No automatic drive-wide organization or drive-root processing.
- Scanning is limited to the immediate contents of the selected folder; subfolders are not processed or moved.
- No file deletion.
- No overwriting existing files.
- When a destination filename already exists, a unique filename is generated instead.
- The application source file and temporary files are excluded from scanning and organization.

Always review the preview before confirming file operations.

## 🗺️ Roadmap

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
- [ ] **V2.0 — Final stable release with a standalone Windows executable (.exe).**

## 📌 Project Status

**Current Version:** 1.3

**Status:** Functional — V1.3 UI/UX and usability improvements implemented.

A standalone Windows executable is planned for the V2.0 final stable release and is not included in this version.

---

Developed by **MRN** 👑
