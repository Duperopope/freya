from __future__ import annotations

from rich.console import Console
from rich.theme import Theme

THEME = Theme(
    {
        "freya.title": "bold magenta",
        "freya.ok": "bold green",
        "freya.warn": "bold yellow",
        "freya.err": "bold red",
        "freya.dim": "dim",
        "freya.user": "italic cyan",
        "freya.step": "bold italic white",
        "freya.code": "cyan",
    }
)

console = Console(theme=THEME, highlight=False)


def hr(label: str = "") -> None:
    if label:
        console.rule(f"[freya.title]{label}[/freya.title]")
    else:
        console.rule()


def say(msg: str) -> None:
    console.print(f"[freya.user]{msg}[/freya.user]")


def step(msg: str) -> None:
    console.print(f"[freya.step]{msg}[/freya.step]")


def ok(msg: str) -> None:
    console.print(f"[freya.ok]{msg}[/freya.ok]")


def warn(msg: str) -> None:
    console.print(f"[freya.warn]{msg}[/freya.warn]")


def err(msg: str) -> None:
    console.print(f"[freya.err]{msg}[/freya.err]")
