from cx_Freeze import setup, Executable

# Dependencies
build_exe_options = {
    "packages": ["requests", "re", "os", "sys", "time", "datetime"],
    "includes": [],
    "excludes": [],
}

setup(
    name="Aurora NAT Updater",
    version="3.0",
    author="IVAO - OCC; VID 609402, VID 598172, VID 200696",
    description="Aurora NATs injector",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "./nat.py",
            icon="./OCC.ico",
            base=None,  # Use "Win32GUI" to hide console, None to show it
        )
    ]
)