from __future__ import annotations

import tkinter as tk
from collections.abc import Iterable


def configure_tree_columns(tree, columns: Iterable[tuple[str, str]]) -> None:
    for key, text in columns:
        tree.heading(key, text=text, anchor=tk.CENTER)
        tree.column(key, anchor=tk.CENTER)
