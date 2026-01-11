import sys
from pathlib import Path

# Simulate the fix logic
print(f"__file__: {__file__}")
# ORIGINAL FAILED LOGIC
# candidates = [
#     Path(__file__).parent / "docs",
#     Path(__file__).parent.parent / "docs",
#     Path("/app/docs")
# ]

# NEW FIXED LOGIC
candidates = [
    Path(__file__).resolve().parent / "docs",
    Path(__file__).resolve().parent.parent / "docs",
    Path("/app/docs")
]

print(f"Candidates: {[str(c) for c in candidates]}")

# Verify logic
found = False
for c in candidates:
    if c.exists() and (c / "project_vision.md").exists():
        print(f"FOUND DOCS AT: {c}")
        found = True
        break

if not found:
    print("DOCS NOT FOUND")
    sys.exit(1)
