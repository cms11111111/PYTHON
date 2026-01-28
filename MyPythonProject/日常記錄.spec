# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['日常記錄.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pandas._libs.tslibs.timedeltas', 'pandas._libs.tslibs.timestamps', 'pandas._libs.interval', 'tkcalendar'],
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
    name='日常記錄',
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
)
