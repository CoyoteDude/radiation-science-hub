"""
patch_app_export.py
───────────────────
Run from your project directory:
    cd ~/Downloads/pycharm_project
    python patch_app_export.py

Adds the PDF Export tab to app.py:
  1. Imports render_export_tab
  2. Adds sidebar button
  3. Adds routing branch
"""

from pathlib import Path

TARGET = Path("app.py")
if not TARGET.exists():
    print("ERROR: app.py not found. Run from your project directory.")
    exit(1)

src = TARGET.read_text()
original = src

# ── Import ────────────────────────────────────────────────────────────────────
if "render_export_tab" not in src:
    anchor = "from spectrum_db import load_db"
    if anchor in src:
        src = src.replace(anchor, anchor + "\nfrom report_export import render_export_tab", 1)
        print("FIX 1: added render_export_tab import")
    else:
        print("FIX 1: anchor not found — add manually: from report_export import render_export_tab")
else:
    print("FIX 1: import already present")

# ── Sidebar button ─────────────────────────────────────────────────────────────
if 'nav_export' not in src:
    anchor = '    st.markdown("---")'
    insert = ('    if st.button("📄  Export PDF", key="nav_export", use_container_width=True):\n'
              '        st.session_state["section"] = "export"\n\n')
    if anchor in src:
        src = src.replace(anchor, insert + anchor, 1)
        print("FIX 2: added Export PDF sidebar button")
    else:
        print("FIX 2: sidebar anchor not found")
else:
    print("FIX 2: sidebar button already present")

# ── Route ──────────────────────────────────────────────────────────────────────
if '"export"' not in src:
    anchor = 'elif section == "library_match": render_library_match_tab(db)'
    if anchor not in src:
        anchor = 'elif section == "dose":         render_dose_tab()'
    insert = '\nelif section == "export":        render_export_tab(db)'
    if anchor in src:
        src = src.replace(anchor, anchor + insert, 1)
        print("FIX 3: added export routing branch")
    else:
        print("FIX 3: routing anchor not found — add manually")
else:
    print("FIX 3: route already present")

if src != original:
    TARGET.write_text(src)
    print(f"\n✓ app.py patched successfully.")
else:
    print("\n⚠  No changes written.")
