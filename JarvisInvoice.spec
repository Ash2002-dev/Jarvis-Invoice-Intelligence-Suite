# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

from PyInstaller.utils.hooks import collect_all

# --- Collect required packages safely ---
# collect_all is aggressive and ensures all metadata/DLLs are included
torch_datas, torch_bins, torch_hidden = collect_all("torch")
tv_datas, tv_bins, tv_hidden = collect_all("torchvision")
ocr_datas, ocr_bins, ocr_hidden = collect_all("easyocr")

a = Analysis(
    ['src/app.py'],
    pathex=['.'],
    binaries=torch_bins + tv_bins + ocr_bins,
    datas=[('logo.png', '.')] + torch_datas + tv_datas + ocr_datas,
    hiddenimports=[
        # TorchDynamo core
        "torch._dynamo",
        "torch._dynamo.utils",
        "torch._dynamo.config",

        # TorchDynamo polyfills (ALL required for runtime stability)
        "torch._dynamo.polyfills",
        "torch._dynamo.polyfills.loader",
        "torch._dynamo.polyfills.fx",
        "torch._dynamo.polyfills.tensor",
        "torch._dynamo.polyfills.os",
        "torch._dynamo.polyfills.builtins",
        "torch._dynamo.polyfills.collections",
        "torch._dynamo.polyfills.inspect",

        # Torch FX (used by torchvision and dynamo)
        "torch.fx",
    ] + torch_hidden + tv_hidden + ocr_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "torch.distributed",
        "torch.multiprocessing",
        "torch.cuda",
        "torch.backends.cuda",
        "torch.testing", # Extra cleanup
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
    name='Jarvis Invoice Intelligence',
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
    icon=['logo.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Jarvis Invoice Intelligence',
)
