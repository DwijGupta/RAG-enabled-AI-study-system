#!/usr/bin/env python3
"""
Local Secret & Credential Pre-Commit Scanner
=============================================
Scans staged Git changes to prevent accidental commits of API keys, environment
variables (.env), secrets, and sensitive tokens before they reach source control.
"""

import sys
import re
import subprocess
from pathlib import Path

# Sensitive filenames that must NEVER be staged or committed
FORBIDDEN_FILE_PATTERNS = [
    r"(^|/)\.env(\..+)?$",
    r"(^|/)config\.json$",
    r"(^|/)secrets\.json$",
    r"(^|/)credentials\.json$",
    r".*\.pem$",
    r".*\.key$",
    r".*\.pfx$",
    r".*\.p12$",
    r".*\.cert$",
    r".*\.crt$",
    r"service-account.*\.json$",
]

# Whitelist allowed templates
ALLOWED_FILES = {
    ".env.example",
    "backend/.env.example",
    "frontend/.env.example",
}

# Regex patterns for high-risk secrets in code/diffs
SECRET_PATTERNS = [
    (
        "Google Gemini / Cloud API Key",
        re.compile(r"(AIza[0-9A-Za-z_\-]{35}|AQ\.[A-Za-z0-9_\-]{40,})")
    ),
    (
        "Generic Private Key",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")
    ),
    (
        "Hardcoded API Key Assignment",
        re.compile(r"""(?i)(?:api_key|secret_key|app_secret|gemini_key)\s*[:=]\s*["']([A-Za-z0-9_\-]{24,})["']""")
    ),
    (
        "OpenAI / Anthropic API Key",
        re.compile(r"(sk-[A-Za-z0-9_\-]{32,}|sk-ant-[A-Za-z0-9_\-]{32,})")
    ),
    (
        "AWS Access Key ID",
        re.compile(r"(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}")
    )
]

# Patterns explicitly permitted (dummy placeholders)
SAFE_PATTERNS = [
    "your_gemini_api_key_here",
    "your_google_gemini_api_key_here",
    "mock_ci_key",
    "your_api_key_here",
    "AIzaSyDemoPlaceHolderKey"
]


def run_cmd(args):
    try:
        res = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        return res.stdout.strip(), res.returncode
    except Exception as e:
        print(f"Error running {' '.join(args)}: {e}")
        return "", 1


def get_staged_files():
    stdout, code = run_cmd(["git", "diff", "--cached", "--name-only"])
    if code != 0 or not stdout:
        return []
    return [line.strip().replace("\\", "/") for line in stdout.splitlines() if line.strip()]


def check_forbidden_filenames(staged_files):
    violations = []
    for file_path in staged_files:
        if file_path in ALLOWED_FILES:
            continue
        for pattern in FORBIDDEN_FILE_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                violations.append((file_path, f"Matches forbidden secret file pattern '{pattern}'"))
                break
    return violations


def check_staged_diff():
    diff_output, code = run_cmd(["git", "diff", "--cached", "-U0"])
    if code != 0 or not diff_output:
        return []

    violations = []
    current_file = None

    for line in diff_output.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:].strip().replace("\\", "/")
            continue

        # Only inspect added lines
        if not line.startswith("+") or line.startswith("+++"):
            continue

        added_content = line[1:].strip()

        # Skip harmless placeholders
        if any(safe in added_content for safe in SAFE_PATTERNS):
            continue

        # Skip lines in allowed example files or test fixtures
        if current_file in ALLOWED_FILES or (current_file and ('/tests/' in current_file or current_file.startswith('tests/'))):
            continue

        for label, regex in SECRET_PATTERNS:
            match = regex.search(added_content)
            if match:
                secret_preview = match.group(0)
                masked = secret_preview[:4] + "*" * (len(secret_preview) - 8) + secret_preview[-4:] if len(secret_preview) > 8 else "***"
                violations.append((
                    current_file or "unknown",
                    f"Possible {label} detected: '{masked}'"
                ))
                break

    return violations


def main():
    scan_all = "--all" in sys.argv or "--check-all" in sys.argv
    print("=" * 70)
    print(" [AI Study Buddy] Secret & Credential Pre-Commit Scanner")
    print("=" * 70)

    if scan_all:
        print("Mode: Scanning all tracked repository files...")
        stdout, _ = run_cmd(["git", "ls-files"])
        files_to_check = [f.strip().replace("\\", "/") for f in stdout.splitlines() if f.strip()]
        name_violations = check_forbidden_filenames(files_to_check)
        if name_violations:
            print("\n[SECURITY ALERT] Tracked forbidden secret files found:")
            for path, reason in name_violations:
                print(f"  - {path}: {reason}")
            print("\nRun: git rm --cached <file> and ensure it is in .gitignore.")
            sys.exit(1)
        print("[OK] All tracked files comply with filename security policy.")
        sys.exit(0)

    staged_files = get_staged_files()
    if not staged_files:
        print("[INFO] No staged changes found to scan. Ready.")
        sys.exit(0)

    print(f"Scanning {len(staged_files)} staged file(s)...")

    # 1. Filename checks
    filename_violations = check_forbidden_filenames(staged_files)
    if filename_violations:
        print("\n[CRITICAL] BLOCKED COMMIT: You are attempting to commit secret/environment file(s):")
        for path, reason in filename_violations:
            print(f"  - {path} ({reason})")
        print("\nRemediation:")
        print("  1. Unstage the file: git reset HEAD <filename>")
        print("  2. Ensure it is listed in .gitignore")
        print("  3. Never commit live secrets to git.\n")
        sys.exit(1)

    # 2. Diff content checks
    diff_violations = check_staged_diff()
    if diff_violations:
        print("\n[CRITICAL] BLOCKED COMMIT: Potential API key or credential detected in diff:")
        for path, reason in diff_violations:
            print(f"  - In file '{path}': {reason}")
        print("\nRemediation:")
        print("  1. Remove hardcoded keys from code.")
        print("  2. Load credentials dynamically via environment variables (e.g., .env).")
        print("  3. Commit again once secrets are sanitized.\n")
        sys.exit(1)

    print("[OK] Clean! No credentials, API keys, or forbidden environment files detected.")
    sys.exit(0)


if __name__ == "__main__":
    main()
