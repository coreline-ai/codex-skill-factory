#!/usr/bin/env python3
from __future__ import annotations

import os
import sys

COMMAND = ["codex-skill-factory", "hook-turn-stop", "--project"]


def main() -> int:
    try:
        os.execvp(COMMAND[0], COMMAND)
    except FileNotFoundError:
        sys.stderr.write(
            "codex-skill-factory is not available on PATH. "
            "Install the CLI or run `codex-skill-factory init --repo . --yes` again.\n"
        )
        return 127
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
