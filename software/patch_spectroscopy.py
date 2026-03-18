"""
patch_spectroscopy.py
─────────────────────
Run this once from your project directory:

    cd ~/Downloads/pycharm_project
    python patch_spectroscopy.py

It applies two targeted fixes to spectroscopy_module.py:

  FIX 1 — The "Analyze" button in My Spectra no longer writes to
           st.session_state["sel_id"] after the widget is instantiated.
           It writes to a staging key "_pending_sel_id" instead.

  FIX 2 — At the top of render_spectroscopy(), any pending sel_id is
           consumed and committed BEFORE any widget with key="sel_id"
           is created, avoiding the StreamlitAPIException.
"""

import re
from pathlib import Path

TARGET = Path("spectroscopy_module.py")

if not TARGET.exists():
    print(f"ERROR: {TARGET} not found. Run this script from your project directory.")
    exit(1)

src = TARGET.read_text()
original = src  # keep for diff

# ── FIX 1 ──────────────────────────────────────────────────────────────────
# Old: st.session_state["sel_id"] = entry["id"]
# New: st.session_state["_pending_sel_id"] = entry["id"]
old1 = 'st.session_state["sel_id"] = entry["id"]'
new1 = 'st.session_state["_pending_sel_id"] = entry["id"]'

if old1 not in src:
    print("FIX 1: pattern not found — already patched or file differs.")
else:
    src = src.replace(old1, new1)
    print("FIX 1 applied: Analyze button now uses _pending_sel_id staging key.")

# ── FIX 2 ──────────────────────────────────────────────────────────────────
# Insert pending-sel_id consumer at the very start of render_spectroscopy().
# We look for the function def line followed by its docstring or first statement.
consumer_block = '''\
    # Consume any pending spectrum selection BEFORE widgets instantiate
    if "_pending_sel_id" in st.session_state:
        st.session_state["sel_id"] = st.session_state.pop("_pending_sel_id")
'''

# Find `def render_spectroscopy():` and insert after it
pattern = r'(def render_spectroscopy\(\):[ \t]*\n)([ \t]+""".*?"""[ \t]*\n)?'

def inserter(m):
    defline = m.group(1)
    docstring = m.group(2) or ""
    return defline + docstring + consumer_block

new_src, n = re.subn(pattern, inserter, src, count=1, flags=re.DOTALL)

if n == 0:
    print("FIX 2: render_spectroscopy() not found — check function name.")
elif consumer_block in src:
    print("FIX 2: consumer block already present — skipping.")
else:
    src = new_src
    print("FIX 2 applied: _pending_sel_id consumed before widget instantiation.")

# ── Write back ─────────────────────────────────────────────────────────────
if src != original:
    TARGET.write_text(src)
    print(f"\n✓ {TARGET} patched successfully.")
else:
    print("\n⚠  No changes written — check messages above.")
