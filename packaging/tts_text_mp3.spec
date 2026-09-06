# PyInstaller spec for YomiPalette.
# Provider SDKs are imported lazily by the application, so the base bundle can
# stay small while still allowing all providers to be selected at runtime.

import os
import sys

from PyInstaller.utils.hooks import collect_submodules


hiddenimports = []
hiddenimports += [
    "core",
    "core.config",
    "core.file_reader",
    "core.tts_engine",
    "core.mobi_reader",
    "core.providers",
    "core.providers.base",
    "core.providers.edge",
    "core.providers.azure",
    "core.providers.google",
    "core.providers.openai",
]
for package in (
    "edge_tts",
    "ebooklib",
    "bs4",
    "lxml",
    "mobi",
    "azure.cognitiveservices.speech",
    "google.cloud.texttospeech",
    "openai",
):
    hiddenimports += collect_submodules(package)

project_root = os.path.abspath(os.path.join(SPECPATH, os.pardir))
icon_path = os.path.join(project_root, "assets", "app-icon.ico")

a = Analysis(
    [os.path.join(project_root, "main.py")],
    pathex=[project_root],
    binaries=[],
    datas=[(os.path.join(project_root, "locales"), "locales")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="YomiPalette",
    icon=icon_path if sys.platform == "win32" else None,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="YomiPalette",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="YomiPalette.app",
        icon=None,
        bundle_identifier="com.ttstextmp3.app",
    )
