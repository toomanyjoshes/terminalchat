#!/usr/bin/env python3
from setuptools import setup, find_packages

setup(
    name="terminalchat",
    version="0.1.0",
    description="A simple terminal-based chat application",
    author="Shortcut Studios",
    author_email="info@shortcutstudios.com",
    packages=find_packages(),
    install_requires=[
        "rich>=10.0.0",
    ],
    entry_points={
        "console_scripts": [
            "terminalchat=terminalchat:main",
        ],
    },
    py_modules=["terminalchat"],
    python_requires=">=3.6",
)
