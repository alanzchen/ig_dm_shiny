# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import copy_metadata

datas = [('payload', '.')]
datas += collect_data_files('torch')
datas += collect_data_files('sentence_transformers')
datas += collect_data_files('spacy_fastlang')
datas += copy_metadata('torch')
datas += copy_metadata('tqdm')
datas += copy_metadata('regex')
datas += copy_metadata('requests')
datas += copy_metadata('filelock')
datas += copy_metadata('numpy')
datas += copy_metadata('tokenizers')
datas += copy_metadata('importlib_metadata')
datas += copy_metadata('safetensors')
datas += copy_metadata('pyyaml')
datas += copy_metadata('packaging', recursive=True)
datas += copy_metadata('tqdm', recursive=True)
datas += copy_metadata('transformers', recursive=True)


a = Analysis(
    ['wx_app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['pytorch', 'sklearn.utils._cython_blas', 'sklearn.neighbors.typedefs', 'sklearn.neighbors.quad_tree', 'sklearn.tree', 'sklearn.tree._utils', 'safetensors', 'pyarrow.vendored.version', 'scipy.special._cdflib', 'pyarrow', 'spacy_fastlang'],
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
    [],
    exclude_binaries=True,
    name='wx_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file='entitlements.plist',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='wx_app',
)
app = BUNDLE(
    coll,
    name='wx_app.app',
    icon=None,
    bundle_identifier=None,
)
