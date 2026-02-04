"""Resolve merge conflict in errors.log: keep HEAD, drop incoming block.
Run from repo root when errors.log contains <<<<<<< HEAD / ======= / >>>>>>> markers.
"""
import re
import sys

path = "errors.log"
try:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
except FileNotFoundError:
    print("errors.log not found.")
    sys.exit(1)

# Match conflict markers (allow \n or \r\n; ======= and >>>>>>> can appear in tracebacks, so be strict)
start = re.search(r"^<<<<<<< HEAD\r?\n", content, re.MULTILINE)
if not start:
    print("Conflict markers not found. File may already be resolved.")
    sys.exit(0)

# Find first ======= and >>>>>>> after start (these are the conflict separators)
rest = content[start.end() :]
mid = re.search(r"\r?\n=======\r?\n", rest)
if not mid:
    print("Could not find ======= marker.")
    sys.exit(1)
end = re.search(r"\r?\n>>>>>>> [^\r\n]+\r?\n", rest[mid.end() :])
if not end:
    print("Could not find >>>>>>> marker.")
    sys.exit(1)

# Keep: everything before <<<<<<<, then HEAD block (until =======)
before = content[: start.start()]
head_block = rest[: mid.start()]
after_incoming = rest[mid.end() + end.end() :]
resolved = before + head_block + after_incoming

# Normalize: no trailing conflict junk
resolved = resolved.rstrip()
if not resolved.endswith("\n"):
    resolved += "\n"

with open(path, "w", encoding="utf-8", newline="") as out:
    out.write(resolved)

print("Resolved errors.log: kept HEAD, removed incoming block.")
