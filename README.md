# MRN Downloads Organizer

A lightweight Windows desktop utility that automatically organizes messy folders by sorting files into categorized directories based on their extensions.

Built with Python and Tkinter, this application provides a simple graphical interface for managing downloaded files without manually sorting them.

## ✨ Features

- **Automatic File Categorization** — Sort files based on their extensions.
- **Folder Selection** — Organize Downloads or any explicitly selected folder.
- **Downloads Shortcut** — Quickly access the Windows Downloads directory.
- **File Scanning** — Scan folders and display category-wise file counts.
- **Organization Preview** — Review files before moving them.
- **Duplicate Protection** — Prevent accidental overwriting by generating unique filenames.
- **Safe File Handling** — Never delete files or recursively process subdirectories.
- **Operation Summary** — View successfully moved, skipped and failed files.

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
| Others | Unsupported extensions |

## 🛠️ Technology Stack

- Python 3
- Tkinter / ttk
- Python Standard Library

No external dependencies are required for the current version.

## 🚀 Getting Started

### Requirements

- Windows 10 or Windows 11
- Python 3 installed

### Run Locally

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/MRN-Downloads-Organizer.git
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

MRN Downloads Organizer is designed with basic file safety in mind.

- No automatic drive-wide organization.
- No recursive directory processing.
- No file deletion.
- No overwriting existing files.
- Existing subdirectories are excluded from scanning.
- The application source file is excluded from organization.

Always review the preview before confirming file operations.

## 🗺️ Roadmap

- [x] Initial file organizer implementation.
- [x] Automatic file categorization.
- [x] Folder scanning and preview.
- [x] Duplicate filename protection.
- [ ] Premium desktop interface.
- [ ] Persistent application settings.
- [ ] Progress indicators.
- [ ] Standalone Windows executable (.exe).

## 📌 Project Status

**Current Version:** 1.0

**Status:** Functional — Initial testing completed.

Further UI improvements and Windows application packaging are planned.

---

Developed by **MRN** 👑
