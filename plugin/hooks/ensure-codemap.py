#!/usr/bin/env python3
"""
Pre-hook to ensure codemap CLI is installed before use.
Only installs when a codemap command is detected.
"""
import json
import subprocess
import sys
import re

def main():
    # Read hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Not JSON, let it pass

    tool_name = input_data.get('tool_name', '')
    tool_input = input_data.get('tool_input', {})
    command = tool_input.get('command', '')

    # Only check for codemap commands
    if tool_name != 'Bash' or not re.search(r'\bcodemap\b', command):
        sys.exit(0)  # Not a codemap command, exit success

    # Check if codemap is installed
    try:
        subprocess.run(['codemap', '--help'], capture_output=True, timeout=5, check=True)
        sys.exit(0)  # Already installed
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass  # Not installed, continue to install

    # Install codemap
    print("Installing codemap CLI...", file=sys.stderr)
    try:
        result = subprocess.run(
            ['pip', 'install', 'git+https://github.com/AZidan/codemap.git'],
            capture_output=True,
            timeout=120
        )
        if result.returncode != 0:
            print(f"Failed to install codemap: {result.stderr.decode()}", file=sys.stderr)
            sys.exit(2)  # Blocking error
        print("✓ codemap installed successfully", file=sys.stderr)
    except Exception as e:
        print(f"Error installing codemap: {e}", file=sys.stderr)
        sys.exit(2)  # Blocking error

    sys.exit(0)

if __name__ == '__main__':
    main()
