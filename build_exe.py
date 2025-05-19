import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["tkinter", "os", "aiohttp", "json", "pandas"],
    "includes": ["tkinter", "tkinter.ttk"],
    "include_files": ["README.md", "requirements.txt"]
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"  # для оконного приложения

setup(
    name="VAK_Filter",
    version="1.0",
    description="Фильтр журналов ВАК 2.3.4",
    options={"build_exe": build_exe_options},
    executables=[Executable("main.py", base=base, target_name="VAK_Filter.exe")]
)