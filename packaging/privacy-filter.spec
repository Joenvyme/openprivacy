# -*- mode: python ; coding: utf-8 -*-
# PyInstaller — application de bureau « Filtre de confidentialité »
# Usage : pyinstaller packaging/privacy-filter.spec (depuis la racine du projet)

import sys
from pathlib import Path

block_cipher = None
project_root = Path(SPECPATH).parent

a = Analysis(
    [str(project_root / "desktop" / "app_gui.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        "opf",
        "opf._api",
        "opf._core",
        "opf._core.runtime",
        "opf._core.decoding",
        "opf._core.spans",
        "opf._core.sequence_labeling",
        "opf._model",
        "opf._model.model",
        "opf._model.weights",
        "opf._common",
        "opf._common.checkpoint_download",
        "opf._common.label_space",
        "opf._common.constants",
        "tiktoken",
        "tiktoken_ext",
        "tiktoken_ext.openai_public",
        "safetensors",
        "safetensors.torch",
        "huggingface_hub",
        "huggingface_hub.utils",
        "tqdm",
        "regex",
        "numpy",
        "torch",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "pandas",
        "scipy",
        "IPython",
        "jupyter",
        "notebook",
        "pytest",
        "setuptools",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FiltreConfidentialite",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="FiltreConfidentialite",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="FiltreConfidentialite.app",
        icon=None,
        bundle_identifier="fr.joenvyme.privacyfilter",
        info_plist={
            "CFBundleName": "Filtre de confidentialité",
            "CFBundleDisplayName": "Filtre de confidentialité",
            "CFBundleVersion": "1.0.0",
            "CFBundleShortVersionString": "1.0.0",
            "NSHighResolutionCapable": True,
            "NSHumanReadableCopyright": "OpenAI Privacy Filter (Apache 2.0)",
        },
    )
