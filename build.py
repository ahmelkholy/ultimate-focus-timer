import PyInstaller.__main__


def build():
    """Build the application using PyInstaller."""
    # Clean up previous builds - temporarily disabled
    # if os.path.exists("dist"):
    #     shutil.rmtree("dist")
    # if os.path.exists("build"):
    #     shutil.rmtree("build")

    # Build using direct PyInstaller arguments
    PyInstaller.__main__.run(
        [
            "main.py",
            "--name=focus",
            "--onefile",
            "--noconsole",
            "--icon=files/icon.png",
            "--add-data=files;files",
            "--add-data=src;src",
            "--add-data=config.yml;.",
            "--add-data=data;data",
            "--hidden-import=tkinter",
            "--hidden-import=tkinter.ttk",
            "--hidden-import=tkinter.filedialog",
            "--hidden-import=yaml",
            "--hidden-import=psutil",
            "--hidden-import=matplotlib.backends.backend_tkagg",
            "--hidden-import=pandas",
            "--hidden-import=PIL",
            "--hidden-import=plyer.platforms.win.notification",
            "--hidden-import=rich",
            "--hidden-import=colorama",
            "--clean",
            "--noconfirm",
        ]
    )


if __name__ == "__main__":
    build()
if __name__ == "__main__":
    build()
