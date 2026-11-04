#!/usr/bin/env python3
"""
Pre-commit hook setup script.
Configures Git to run the local secret scanner before every commit.
"""
import os
import subprocess
import sys

def setup():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print(f"Setting up Git hooks in repository: {repo_root}")
    try:
        subprocess.run(
            ["git", "config", "core.hooksPath", ".githooks"],
            cwd=repo_root,
            check=True
        )
        print("[SUCCESS] Local Git hooks activated! Commits will now automatically scan for secrets via .githooks/pre-commit.")
    except Exception as e:
        print(f"[ERROR] Failed to configure Git hooks path: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup()
