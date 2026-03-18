"""
patch_app_library.py
─────────────────────
Run from your project directory:

    cd ~/Downloads/pycharm_project
    python patch_app_library.py

Wires the new spectral library matching tab into app.py:
  1. Adds the import for render_library_match_tab
  2. Adds the sidebar nav button
  3. Adds the routing elif branch
"""

import re
from pathlib import Path

TARGET = Path("app.py")
if not TARGET.exists():
    print("ERROR: app.py not found. Run from your project directory.")
    exit(1)

src = TARGET.read_text()
original = src

# ── FIX 1: Add import ────────────────────────────────────────────────────────
OLD_IMPORT = "from spectrum_db import load_db"
NEW_IMPORT = "from spectrum_db import load_db\nfrom library_match_tab import render_library_match_tab"

if "render_library_match_tab" in src:
    print("FIX 1: import already present — skipping.")
elif OLD_IMPORT not in src:
    print("FIX 1: could not find import anchor — skipping.")
else:
    src = src.replace(OLD_IMPORT, NEW_IMPORT, 1)
    print("FIX 1 applied: added render_library_match_tab import.")

# ── FIX 2: Add sidebar button ────────────────────────────────────────────────
# Insert before the closing of the sidebar (before the "---" divider + curve display)
SIDEBAR_ANCHOR = '    st.markdown("---")'
SIDEBAR_INSERT = (
    '    if st.button("📚  Library Match", key="nav_lib", use_container_width=True):\n'
    '        st.session_state["section"] = "library_match"\n'
    '\n'
)

if 'nav_lib' in src:
    print("FIX 2: sidebar button already present — skipping.")
elif SIDEBAR_ANCHOR not in src:
    print("FIX 2: sidebar anchor not found — skipping.")
else:
    src = src.replace(SIDEBAR_ANCHOR, SIDEBAR_INSERT + SIDEBAR_ANCHOR, 1)
    print("FIX 2 applied: added Library Match sidebar button.")

# ── FIX 3: Add routing branch ────────────────────────────────────────────────
ROUTE_ANCHOR = 'elif section == "dose":         render_dose_tab()'
ROUTE_INSERT = '\nelif section == "library_match": render_library_match_tab(db)'

if 'library_match' in src:
    print("FIX 3: route already present — skipping.")
elif ROUTE_ANCHOR not in src:
    print("FIX 3: route anchor not found — check app.py routing block.")
else:
    src = src.replace(ROUTE_ANCHOR, ROUTE_ANCHOR + ROUTE_INSERT, 1)
    print("FIX 3 applied: added library_match routing branch.")

# ── Write back ────────────────────────────────────────────────────────────────
if src != original:
    TARGET.write_text(src)
    print(f"\n✓ app.py patched successfully.")
else:
    print("\n⚠  No changes written — check messages above.")
