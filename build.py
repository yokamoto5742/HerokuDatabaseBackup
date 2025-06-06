import subprocess


def build_executable():
    subprocess.run([
        "pyinstaller",
        "--name=HerokuDatabaseBackup",
        "--windowed",
        "--add-data", "config.ini;.",
        "main.py"
    ])

    print(f"Executable built successfully.")


if __name__ == "__main__":
    build_executable()
