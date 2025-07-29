# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\hub.py'],
    pathex=[],
    binaries=[],
    datas=[('config', 'config'), ('scripts', 'scripts')],
    hiddenimports=['nats', 'pynput', 'GitPython', 'pyautogui', 'pywin32', 'flask'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='hub',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['scripts\\W_Logo1.ico'],
)
