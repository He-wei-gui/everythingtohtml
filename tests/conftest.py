"""Shared pytest fixtures and helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def write_file(tmp_path: Path):
    """Return a helper that writes bytes/text to a temp file and returns its path."""

    def _write(name: str, content: str | bytes) -> Path:
        path = tmp_path / name
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    return _write


@pytest.fixture
def sample_notebook() -> str:
    notebook = {
        "cells": [
            {"cell_type": "markdown", "source": ["# My Notebook\n", "\n", "Intro text."]},
            {
                "cell_type": "code",
                "source": ["print('hello')"],
                "outputs": [{"output_type": "stream", "text": ["hello\n"]}],
            },
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    return json.dumps(notebook)
