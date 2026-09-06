# AGENTS.md

Notes for OpenCode and similar agents working in this repository.

## Project shape

- Desktop Python app **YomiPalette** (formerly `TTS-Text-MP3`). Entry point: `main.py` -> `gui/app.py:run_app`.
- Source layout: `core/` (TXT/EPUB/PDF/MOBI readers, TTS engine, config, providers), `gui/` (UI), `i18n.py`, `locales/{en,ja,zh-CN}.json`, `assets/` (icons), `packaging/` (PyInstaller spec + Inno Setup script), `scripts/`, `tests/`.
- Providers live in `core/providers/` and are loaded lazily by dotted path in `core/providers/__init__.py`; they share the `TTSProvider` base in `core/providers/base.py`.
- `mobile/` is a separate Flutter app. Mobile provider support can differ; its own `README.md` is authoritative. CI for it lives in `.github/workflows/mobile.yml` and the Android build is also part of the tag-driven release flow.
- Mobile supports **TXT, EPUB, PDF only**. MOBI / AZW / AZW3 are desktop-only because the KF8 / HUFF-CDIC parser in pure Dart would be a large maintenance burden. If you need to read Kindle files on a phone, use the desktop build or pre-convert to EPUB with Calibre. The mobile `file_picker` extension allowlist in `lib/main.dart` reflects this and must stay `['txt','epub','pdf']` until a mobile reader is added.
- Python **>= 3.10** is required (CI uses 3.12).

## Install and run from source

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
source .venv/bin/activate    # macOS / Linux
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

## Tests

- Framework: `unittest` only. No `pytest`, no `tox`, no Makefile. Run with `python -m unittest discover -s tests` from the repo root.
- Each test file runs as a standalone script too (`if __name__ == "__main__": unittest.main()`), so a single test file can be executed with `python tests/test_tts_engine.py`.
- The PDF fixtures in `tests/fixtures/pdf/` are synthetic. Regenerate them with `python tests/fixtures/pdf/generate.py` (requires `pypdf`).
- The MOBI/AZW3 fixtures in `tests/fixtures/mobi/` are generated from a tiny synthetic EPUB. Regenerate them with `python tests/fixtures/mobi/generate.py` (requires Calibre's `ebook-convert` on PATH).
- `tests/test_i18n.py` enforces that all three locale catalogs share the same keys. If you add or remove a `t(...)` key, update `locales/en.json`, `locales/ja.json`, and `locales/zh-CN.json` together or the test will fail.
- `tests/test_support_links.py` exists; check it before changing README/FUNDING content.

## Lint / typecheck

- No lint, formatter, or typechecker is configured in-repo. Do not invent one without being asked.

## Configuration and credentials

- User config and provider credentials are stored as plain text at `~/.tts-text-mp3/config.json` (see `core/config.py`). The path, file, and any `credentials*.json` / `client_secret*.json` / `*service-account*.json` are gitignored. Never commit them.
- Edge TTS works without credentials; Azure / Google / OpenAI need entries under `providers.<name>` in `config.json`.

## Internationalization

- Supported languages are hard-coded in `i18n.py`: `("ja", "en", "zh-CN")`. The module reads `locales/<lang>.json` on demand and falls back to English. The UI is started from `i18n.detect_system_language()` when no `ui_language` is saved.
- Any new user-visible string must be added to all three locale files; the i18n test will catch drift.

## Build / release

- Tag-driven release: `git tag v0.2.0 && git push origin v0.2.0` triggers `.github/workflows/release.yml`, which builds Windows, macOS (arm64 + x86_64), and Android, then publishes a GitHub Release. Only `GITHUB_TOKEN` with `contents: write` is used; no provider secrets.
- Windows packaging requires PowerShell, PyInstaller, and **Inno Setup 6** (ISCC.exe). `scripts/build_windows.ps1 -Version <tag>` builds the PyInstaller bundle, the portable ZIP, and the Setup installer. Install with `winget install --id JRSoftware.InnoSetup --exact` if missing.
- macOS packaging: `bash scripts/build_macos.sh <tag>` (must be run on macOS). Output goes to `release/`.
- PyInstaller spec: `packaging/tts_text_mp3.spec`. It bundles the whole `locales/` directory and uses `assets/app-icon.ico` on Windows. macOS app icon is intentionally not set (see README "Current Limitations"). Bundle id is `com.ttstextmp3.app`.
- `dist/`, `build/`, and `release/` are gitignored. Don't commit build artifacts.

## Code conventions

- Source files mix English and Japanese in module/docstring strings; do not "fix" the Japanese comments.
- Follow the existing pattern of lazy imports for provider SDKs so the base bundle stays small (see `packaging/tts_text_mp3.spec` comment).
- New providers: implement `core/providers/base.TTSProvider`, add an entry in `_PROVIDER_CLASSES` in `core/providers/__init__.py`, and add the module to `hiddenimports` in `packaging/tts_text_mp3.spec` plus `collect_submodules(...)` if it has third-party deps.

## Things to watch out for

- `core/providers/__init__.py` calls `get_provider(name)` for every entry when listing providers. Don't add heavy SDK imports at module top level in `core/providers/<name>.py`; defer them inside methods so unused providers stay cheap.
- `tts_engine.extract_preview_text` prefers sentence boundaries (`.` `。` `!` `?` line break) that land at >= 60% of the requested length; tests pin this behavior.
- PDF support is text-only: image-only / scanned PDFs raise a `ValueError` mentioning "OCR". Password-protected PDFs surface the localized `error.pdf_password` message.
- MOBI/AZW/AZW3 are extracted via the `mobi` package (`mobi.extract()`). AZW3 with embedded KF8 reuses `core/epub_reader.read_epub_sections` for chapter splitting; older MOBI/AZW return a single chapter because the legacy format has no reliable TOC. DRM-protected files surface the localized `error.mobi_drm` message; detection relies on `MobiHeader.isEncrypted()`.
- macOS and Windows binaries are **unsigned**; README documents the user-side workarounds (Control-click, SmartScreen).
