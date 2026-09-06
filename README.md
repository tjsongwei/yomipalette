[English](README.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)

# YomiPalette

Turn your digital books into audio, with your choice of voice.

The Android/iOS Flutter client is maintained as a separate project in [`mobile/`](mobile/README.md). Mobile provider support differs where client-side credential security or SDK availability requires it.

A desktop application that converts text from TXT, EPUB or PDF files into MP3 audio. It supports Windows and macOS.

## Features

- Extract text from TXT, EPUB, PDF, MOBI, AZW, and AZW3 files
- Generate MP3 files by EPUB chapter
- Generate MP3 files by a specified character count
- Select language and voice
- Generate an audio preview from the selected output unit
- Adjust speaking speed, volume, and pitch
- Automatically split long text
- Generate audio in the background with cancellation support
- Switch the UI between Japanese, English, and Simplified Chinese

## Supported Providers

| Provider | Credentials |
| --- | --- |
| Edge TTS | Not required |
| Microsoft Azure Speech | API key and region |
| Google Cloud Text-to-Speech | API key or service account JSON |
| OpenAI TTS | API key |

## Download

Download the appropriate file for your operating system from the [latest GitHub Release](https://github.com/tjsongwei/yomipalette/releases/latest).

Existing releases through v0.1.7 still use the `TTS-Text-MP3` filenames and app name. The `YomiPalette` filenames below apply to future releases.

### Windows

| File | Purpose |
| --- | --- |
| `YomiPalette_Setup_<version>.exe` | Standard installer with Start menu registration and uninstall support |
| `YomiPalette_Windows_Portable_<version>.zip` | Portable version; extract the ZIP and run `YomiPalette.exe` |

The Setup version is recommended. For the Portable version, extract the entire ZIP to a folder before launching the application.

### macOS

Choose the DMG or ZIP that matches your Mac.

| Filename contains | Target Mac |
| --- | --- |
| `arm64` | Apple Silicon Mac (M1, M2, M3, M4, or later) |
| `x86_64` | Intel Mac |

- DMG: Open the disk image to use the application
- ZIP: Extract the archive and use the `.app`

The current macOS build is not code-signed or notarized by Apple. If macOS displays a warning on first launch, Control-click the application in Finder and select **Open**.

## Basic Usage

1. Select a TTS provider.
2. If required, enter credentials under **Settings...**.
3. Select a TXT, EPUB or PDF file.
4. Configure the output folder, language, voice, speed, and other options.
5. Use **Preview Audio** if needed.
6. Click **Generate MP3**.

### MP3 Splitting

- **By chapter** uses the top-level EPUB table of contents on desktop and mobile. Separate chapter title and body files are joined, and nested sections stay in their parent chapter.
- Front matter and identifiable end matter (such as notes or a colophon) remain separate selectable items. All items start checked; uncheck any you do not want to read. Unidentified continuation text stays in its chapter. Broken links do not invalidate other chapter boundaries. A missing anchor uses the start of its file only when that file has no valid chapter start. If no navigation targets are usable, text is retained by internal file.
- **By character count** joins the TXT, EPUB or PDF body and splits it into sequential MP3 files named from `Part 001`. The default maximum is 5,000 characters.
- Character counts are based on the processed text; spaces and line breaks each count as one character. The last sentence ending or line break within the limit is preferred. Text without a suitable boundary is split at the limit.
- The selected splitting method and character count are restored the next time the application starts.

**Preview Audio** creates an approximately 15-second sample from the selected output unit. If no unit is selected, the first one is used. The actual duration varies by language, voice, and speaking speed.

Edge TTS can be used immediately without credentials.

### Display Language

Use **Display language** at the top of the window to switch between Japanese, English, and Simplified Chinese. On first launch, the application uses the operating system language and falls back to English for unsupported languages. Your selection is saved for future launches.

## Credentials and Configuration

Enter Azure, Google, and OpenAI credentials under **Settings...**. They are stored as plain text in the following location:

- Windows: `%USERPROFILE%\.tts-text-mp3\config.json`
- macOS: `~/.tts-text-mp3/config.json`

Do not commit or share API keys, `config.json`, or Google service account JSON files. Credentials are not included in distributed packages or GitHub Releases.

## Run from Source

Use Python 3.10 or later.

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

### macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

## Build Distribution Packages Locally

### Windows

PowerShell, PyInstaller, and Inno Setup 6 are required.

```powershell
python -m pip install -r requirements.txt pyinstaller
.\scripts\build_windows.ps1 -Version "dev"
```

The Setup executable and Portable ZIP are created under `release/`.

### macOS

Run this on macOS.

```bash
python -m pip install -r requirements.txt pyinstaller
bash scripts/build_macos.sh dev
```

The `.app` ZIP and DMG for the current Mac architecture are created under `release/`.

## Create a GitHub Release

Pushing a tag that begins with `v` makes GitHub Actions build and attach the following files to a Release:

- Windows Setup
- Windows Portable
- macOS Apple Silicon (DMG / ZIP)
- macOS Intel (DMG / ZIP)

```bash
git tag v0.2.0
git push origin v0.2.0
```

The workflow is located at `.github/workflows/release.yml`. It does not store provider credentials and uses only the standard GitHub Actions `GITHUB_TOKEN` with `contents: write` permission to create the Release.

## Current Limitations

- The macOS build is not signed or notarized.
- The Windows build is not code-signed, so SmartScreen may display a warning.
- Provider pricing, character limits, and regional restrictions are governed by each service.
- The macOS application icon is not currently configured.

## License

This project is released under the [MIT License](LICENSE).

Copyright (c) 2026 YuluEthan

## Support YomiPalette

If YomiPalette is useful to you, consider supporting its continued development. Your support helps improve features, fix bugs, and test Windows and Android compatibility. Support is optional and does not change which app features you can use.

- [Support via GitHub Sponsors](https://github.com/sponsors/tjsongwei)
- [Support via Buy Me a Coffee](https://buymeacoffee.com/tjsongweic)

## PDF input

PDFs with embedded text are supported. **By chapter / page** creates units such as `Page 001` in physical page order; **By character count** joins all extracted page text before splitting. PDF bookmarks are not used as chapter boundaries. Pages without text (blank or image-only) are skipped, preserving original page numbers in titles.

OCR is not supported. Image-only/scanned PDFs cannot be read; mixed documents contribute only their text pages. PDFs requiring a password are not supported. Vertical text, columns, tables, and unusual fonts may produce incorrect reading order or extraction. PDF text is extracted on the device; speech generation follows the normal behavior of the selected TTS provider.

## Kindle input (MOBI / AZW / AZW3)

Kindle files in MOBI, AZW, and AZW3 formats are supported. **AZW3 with embedded KF8 (EPUB)** is split into the same chapter boundaries the file declares, matching desktop EPUB behavior. **Older MOBI / AZW** files are returned as a single chapter because the legacy format does not expose a reliable table of contents; splitting still works through **By character count**.

DRM-protected Kindle files (e.g. from the Kindle Store) cannot be read. Import a DRM-free copy (such as one created with Calibre after stripping the protection from a file you own). Other limitations: print-replica Kindle files (with a fixed PDF layout) are not supported; audio, video, fixed-layout, and dictionary entries are ignored. Text is extracted on the device; speech generation follows the normal behavior of the selected TTS provider.
