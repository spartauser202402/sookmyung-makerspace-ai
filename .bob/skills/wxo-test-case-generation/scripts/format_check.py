#!/usr/bin/env python3
"""CLI shim — validates a test case JSON file against the TestCase schema.

Usage::

    python skills/wxo-test-case-generation/scripts/format_check.py --path test-001.json

Exits 0 and prints "Valid: <TestCase …>" when the test case is correctly formatted.
Exits 1 and prints validation errors when the test case is invalid.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure the scripts directory is on sys.path so test_case_format_check can be
# imported regardless of how (or from where) this script is invoked.
sys.path.insert(0, str(Path(__file__).parent))

from test_case_format_check import is_correct_format  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path",
        required=True,
        help="Path to the test case JSON file to validate.",
    )
    args = parser.parse_args()

    with open(args.path) as fh:
        test_case = json.load(fh)

    try:
        result = is_correct_format(test_case)
        print("Valid:", result)
        return 0
    except Exception as exc:  # noqa: BLE001
        print("Invalid:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
