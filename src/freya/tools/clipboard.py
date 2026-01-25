import subprocess

def copy_to_clipboard_windows(text: str) -> None:
    # Set-Clipboard lit la valeur depuis stdin via ReadToEnd
    # Source: https://learn.microsoft.com/powershell/module/microsoft.powershell.management/set-clipboard
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Set-Clipboard -Value ([Console]::In.ReadToEnd())",
        ],
        input=text,
        text=True,
        check=True,
    )
