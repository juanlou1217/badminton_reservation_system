from __future__ import annotations

import tkinter as tk

from app.ui.treeview_helpers import configure_tree_columns


class FakeTree:
    def __init__(self):
        self.heading_calls = []
        self.column_calls = []

    def heading(self, key, **kwargs):
        self.heading_calls.append((key, kwargs))

    def column(self, key, **kwargs):
        self.column_calls.append((key, kwargs))


def test_configure_tree_columns_centers_headings_and_cells():
    tree = FakeTree()

    configure_tree_columns(tree, (("username", "用户名"), ("status", "状态")))

    assert tree.heading_calls == [
        ("username", {"text": "用户名", "anchor": tk.CENTER}),
        ("status", {"text": "状态", "anchor": tk.CENTER}),
    ]
    assert tree.column_calls == [
        ("username", {"anchor": tk.CENTER}),
        ("status", {"anchor": tk.CENTER}),
    ]
