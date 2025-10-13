# -*- mode: python ; coding: utf-8 -*-

import certifi
import os

block_cipher = None

# Get certifi certificate bundle path
certifi_path = os.path.dirname(certifi.__file__)

a = Analysis(
    ['nat.py'],
    pathex=[],
    binaries=[],
    datas=[
        (certifi_path, 'certifi'),  # Include SSL certificates
    ],
    hiddenimports=[
        'requests',
        'urllib3',
        'charset_normalizer',
        'certifi',
        'idna',
        're',
        'time',
        'datetime',
        'requests.adapters',
        'requests.packages.urllib3',
        'urllib3.contrib.pyopenssl',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'PyQt5',
        'scipy',
        'pkg_resources',  # Deprecated module, not needed
        'setuptools',     # Not needed for runtime
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AuroraNATUpdater',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='OCC.ico',
)