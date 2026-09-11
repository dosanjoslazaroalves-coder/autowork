# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('modules/dados/*.json', 'modules/dados'),
    ],
    hiddenimports=[
        'pyaudio',
        'speech_recognition',
        'sounddevice',
        'numpy',
        'scipy',
        'scipy.io',
        'scipy.io.wavfile',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas,
          name='AUTOWORK', console=True, icon=None)
