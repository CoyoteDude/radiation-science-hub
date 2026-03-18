"""
fix_everything.py
─────────────────
Direct fixes — no pattern matching, operates on exact strings.

Run from your project directory:
    cd ~/Downloads/pycharm_project
    python fix_everything.py
"""

from pathlib import Path
import sys

PROJECT = Path(".")

# ══════════════════════════════════════════════════════════════════════════════
#  HELPER
# ══════════════════════════════════════════════════════════════════════════════

def fix_file(name: str, replacements: list[tuple[str, str]]) -> bool:
    """Apply a list of (old, new) replacements to a file. Returns True if changed."""
    p = PROJECT / name
    if not p.exists():
        print(f"  ✗ {name} not found — skipping")
        return False
    src = p.read_text(encoding="utf-8")
    original = src
    for old, new in replacements:
        if old in src:
            src = src.replace(old, new, 1)
            print(f"  ✓ applied replacement in {name}")
        else:
            # Try to give a helpful message
            short = old.strip()[:60].replace('\n', '↵')
            print(f"  ⚠ pattern not found in {name}: {repr(short)}")
    if src != original:
        p.write_text(src, encoding="utf-8")
        return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
#  FIX A — spectroscopy_module.py
#  The "Analyze" button writes st.session_state["sel_id"] = entry["id"]
#  This triggers the Streamlit conflict because Identify tab's selectbox
#  reads the same key in the same render cycle.
#  Fix: write to "_pending_sel_id" instead, and change patch_spectroscopy's
#  consumer block to use a compatible approach.
# ══════════════════════════════════════════════════════════════════════════════
print("\n── spectroscopy_module.py ──────────────────────────────────────────────")

fix_file("spectroscopy_module.py", [
    # 1a. Analyze button: change target key
    (
        'st.session_state["sel_id"] = entry["id"]',
        'st.session_state["_pending_sel_id"] = entry["id"]'
    ),
    # 1b. Also catch single-quote variant
    (
        "st.session_state['sel_id'] = entry['id']",
        "st.session_state['_pending_sel_id'] = entry['id']"
    ),
    # 2. The patch_spectroscopy.py consumer block (if present):
    #    replaces direct "sel_id" assignment with a safe pre-widget consume
    (
        '    # Consume any pending spectrum selection BEFORE widgets instantiate\n'
        '    if "_pending_sel_id" in st.session_state:\n'
        '        st.session_state["sel_id"] = st.session_state.pop("_pending_sel_id")\n',
        '    # Consume any pending spectrum selection BEFORE widgets instantiate\n'
        '    _pending_spec = st.session_state.pop("_pending_sel_id", None)\n'
        '    if _pending_spec and _pending_spec in load_db():\n'
        '        st.session_state["_active_sel_id"] = _pending_spec\n'
    ),
])

# ══════════════════════════════════════════════════════════════════════════════
#  FIX B — spectroscopy_module.py Identify tab selectbox
#  Change the selectbox that uses key="sel_id" to a different key,
#  OR change the default logic to not read from session_state["sel_id"].
#
#  The identify tab selectbox most likely looks like:
#    eid = st.selectbox("Spectrum", ..., index=default, key="sel_id")
#  OR uses a helper that reads sel_id. We need to rename the widget key.
# ══════════════════════════════════════════════════════════════════════════════

sm = PROJECT / "spectroscopy_module.py"
if sm.exists():
    src = sm.read_text(encoding="utf-8")

    # Find any selectbox with key="sel_id" and rename it
    import re
    # Match selectbox(..., key="sel_id") or key='sel_id'
    new_src = re.sub(
        r'(st\.selectbox\([^)]*key\s*=\s*)["\']sel_id["\']',
        r'\1"sel_id_identify"',
        src
    )
    # Also fix the reading logic that references sel_id for the default
    new_src = new_src.replace(
        'if "sel_id" in st.session_state and st.session_state["sel_id"] in db:\n'
        '        default = list(db.keys()).index(st.session_state["sel_id"])',
        'if "_active_sel_id" in st.session_state and st.session_state["_active_sel_id"] in db:\n'
        '        default = list(db.keys()).index(st.session_state["_active_sel_id"])'
    )

    if new_src != src:
        sm.write_text(new_src, encoding="utf-8")
        print("  ✓ renamed sel_id widget key and updated default logic in spectroscopy_module.py")
    else:
        print("  ⚠ sel_id selectbox key pattern not found — may already be fixed or named differently")


# ══════════════════════════════════════════════════════════════════════════════
#  FIX C — analysis_tabs.py
#  _get_entry_and_peaks reads st.session_state["sel_id"] for default.
#  Update to read from "_active_sel_id" (or "_pending_sel_id" if no consumer).
# ══════════════════════════════════════════════════════════════════════════════
print("\n── analysis_tabs.py ────────────────────────────────────────────────────")

fix_file("analysis_tabs.py", [
    # Remove reading sel_id from session state entirely — use _pending_sel_id pop
    (
        '    default = 0\n'
        '    if "sel_id" in st.session_state and st.session_state["sel_id"] in db:\n'
        '        default = list(db.keys()).index(st.session_state["sel_id"])\n',
        '    default = 0\n'
        '    _pend = st.session_state.pop("_pending_sel_id", None) or st.session_state.get("_active_sel_id")\n'
        '    if _pend and _pend in db:\n'
        '        default = list(db.keys()).index(_pend)\n'
    ),
    # Also catch if patch_all.py already partially applied
    (
        '    default = 0\n'
        '    _pending = st.session_state.pop("_pending_sel_id", None)\n'
        '    if _pending and _pending in db:\n'
        '        default = list(db.keys()).index(_pending)\n',
        '    default = 0\n'
        '    _pend = st.session_state.pop("_pending_sel_id", None) or st.session_state.get("_active_sel_id")\n'
        '    if _pend and _pend in db:\n'
        '        default = list(db.keys()).index(_pend)\n'
    ),
])


# ══════════════════════════════════════════════════════════════════════════════
#  FIX D — spectroscopy_module.py mineral_type
#  Inject a comprehensive MINERAL_TYPES list and wire it to the selectbox.
#  This works by finding the mineral_type selectbox line and replacing it.
# ══════════════════════════════════════════════════════════════════════════════
print("\n── mineral_type expansion ──────────────────────────────────────────────")

MINERAL_TYPES_LIST = [
    # Unknown
    "Unknown / unclassified", "Custom (see notes)",
    # Igneous rocks
    "Granite", "Granodiorite", "Diorite", "Gabbro", "Basalt", "Andesite",
    "Rhyolite", "Obsidian", "Pumice", "Tuff", "Pegmatite", "Syenite",
    "Nepheline syenite", "Peridotite", "Dunite", "Phonolite",
    # Metamorphic
    "Gneiss", "Schist", "Phyllite", "Slate", "Quartzite", "Marble",
    "Hornfels", "Amphibolite", "Eclogite", "Migmatite", "Greenstone",
    # Sedimentary
    "Sandstone", "Shale", "Mudstone", "Siltstone", "Limestone", "Chalk",
    "Dolomite rock", "Conglomerate", "Breccia", "Chert / Flint", "Ironstone",
    "Coal", "Lignite", "Oil shale", "Evaporite", "Rock salt (halite)",
    "Gypsum rock", "Travertine",
    # Minerals
    "Quartz", "Feldspar", "Mica (muscovite/biotite)", "Amphibole",
    "Pyroxene", "Olivine", "Calcite", "Dolomite mineral", "Apatite",
    "Zircon", "Tourmaline", "Garnet", "Epidote", "Chlorite", "Serpentine",
    "Talc", "Kaolin / Kaolinite", "Montmorillonite / Smectite",
    "Illite", "Barite", "Fluorite", "Gypsum mineral", "Anhydrite",
    "Halite", "Sylvite", "Pyrite", "Pyrrhotite", "Chalcopyrite",
    "Galena", "Sphalerite", "Magnetite", "Hematite", "Ilmenite",
    "Rutile", "Chromite", "Spinel", "Corundum", "Graphite", "Sulfur",
    # NORM minerals
    "Monazite", "Xenotime", "Uraninite (pitchblende)", "Uranophane",
    "Autunite", "Carnotite", "Coffinite", "Thorianite", "Thorite",
    "Allanite", "Euxenite", "Samarskite", "Columbite-tantalite",
    "Pyrochlore", "Betafite", "Davidite", "Brannerite",
    # Phosphates / fertilizers
    "Phosphate rock (apatite ore)", "Phosphorite",
    "Triple superphosphate", "Single superphosphate",
    "Ammonium phosphate", "Potassium fertilizer (KCl/K2SO4)",
    "NPK fertilizer blend",
    # Soils & sediments
    "Topsoil", "Sandy soil", "Clay soil", "Loam", "Peat",
    "Alluvial sediment", "Marine sediment", "Lake sediment",
    "River sand", "Beach sand", "Mineral sand (heavy mineral)",
    "Black sand (ilmenite/magnetite)", "Volcanic ash",
    "Laterite", "Bauxite", "Red mud (bauxite residue)",
    # Water
    "Water sample (tap/river/lake)", "Groundwater", "Seawater",
    "Mineral water", "Brine", "Sediment slurry",
    # Building / industrial
    "Cement", "Concrete", "Mortar", "Brick (fired clay)",
    "Ceramic tile", "Gypsum board / plasterboard", "Plaster (gypsum)",
    "Fly ash (coal combustion)", "Bottom ash", "Slag (blast furnace)",
    "Phosphogypsum (by-product)", "TENORM pipe scale", "TENORM sludge",
    "Asphalt / bitumen", "Coal ash", "Zircon sand (industrial)",
    # Metals
    "Steel / iron", "Stainless steel", "Aluminium", "Copper", "Lead",
    "Tungsten", "Uranium metal / alloy", "Thorium metal", "Depleted uranium",
    # Industrial sources
    "Sealed radioactive source", "Smoke detector (Am-241)",
    "Luminous paint / dial", "Radium legacy source",
    "Industrial gauge source", "Well logging source",
    "Radiography source (Ir-192/Se-75)",
    # Calibration
    "Calibration source — Cs-137", "Calibration source — Co-60",
    "Calibration source — Eu-152", "Calibration source — Ba-133",
    "Calibration source — Am-241", "Calibration source — Na-22",
    "Calibration source — Mn-54", "Calibration source — Zn-65",
    "Mixed calibration source", "Marinelli beaker standard",
    # Medical
    "Medical waste", "Nuclear medicine patient sample", "Radiopharmaceutical",
    # Environmental
    "Air filter", "Air particulate", "Vegetation / plant matter",
    "Food sample", "Milk / dairy", "Meat / fish", "Grain / cereal",
    "Bone / tissue", "Urine / biological fluid", "Swipe / wipe sample",
    # Reference
    "Background measurement", "Blank / empty container",
    "Reference material (certified)",
]

sm = PROJECT / "spectroscopy_module.py"
if sm.exists():
    src = sm.read_text(encoding="utf-8")
    import re

    # Inject MINERAL_TYPES constant if not already present
    if "MINERAL_TYPES" not in src:
        # Find first import line and insert after it
        import_end = 0
        for m in re.finditer(r'^import |^from ', src, re.MULTILINE):
            import_end = m.end()
        # Find end of last import block line
        last_import_line_end = src.rfind('\n', 0, src.find('\n\n', import_end)) + 1
        if last_import_line_end <= 0:
            last_import_line_end = 500  # fallback

        mt_str = repr(MINERAL_TYPES_LIST)
        injection = f"\n\nMINERAL_TYPES = {mt_str}\n\n"
        src = src[:last_import_line_end] + injection + src[last_import_line_end:]
        print("  ✓ MINERAL_TYPES constant injected")
    else:
        print("  ⚠ MINERAL_TYPES already present — skipping injection")

    # Find the mineral_type selectbox and replace its options
    # Common patterns:
    patterns = [
        # selectbox("Mineral type", [...], key=...)
        r'(st\.selectbox\s*\(\s*["\'][Mm]ineral[^"\']*["\'],\s*)\[[^\]]*\]',
        # selectbox("Sample type", [...], key=...)
        r'(st\.selectbox\s*\(\s*["\'][Ss]ample[^"\']*["\'],\s*)\[[^\]]*\]',
        # selectbox("Type", [...], key=...) with mineral context
        r'(mineral_type\s*=\s*st\.selectbox\s*\([^,]+,\s*)\[[^\]]*\]',
    ]
    replaced = False
    for pat in patterns:
        new_src = re.sub(pat, r'\1MINERAL_TYPES', src, count=1, flags=re.DOTALL)
        if new_src != src:
            src = new_src
            replaced = True
            print(f"  ✓ mineral_type selectbox options replaced with MINERAL_TYPES")
            break

    if not replaced:
        print("  ⚠ mineral_type selectbox pattern not found")
        print("    Manual fix: find your mineral_type selectbox and change its")
        print('    options list to: MINERAL_TYPES')

    sm.write_text(src, encoding="utf-8")


# ══════════════════════════════════════════════════════════════════════════════
#  FIX E — app.py  (PDF export + library match wiring)
# ══════════════════════════════════════════════════════════════════════════════
print("\n── app.py ──────────────────────────────────────────────────────────────")

app = PROJECT / "app.py"
if app.exists():
    src = app.read_text(encoding="utf-8")
    original = src
    changed = False

    # Import render_export_tab
    if "render_export_tab" not in src:
        src = src.replace(
            "from spectrum_db import load_db",
            "from spectrum_db import load_db\n"
            "from report_export import render_export_tab"
        )
        print("  ✓ added render_export_tab import")
        changed = True

    # Import render_library_match_tab
    if "render_library_match_tab" not in src:
        src = src.replace(
            "from spectrum_db import load_db",
            "from spectrum_db import load_db\n"
            "from library_match_tab import render_library_match_tab"
        )
        print("  ✓ added render_library_match_tab import")
        changed = True

    # Sidebar buttons — insert before st.markdown("---")
    SIDEBAR_ANCHOR = '    st.markdown("---")'
    if 'nav_export' not in src and SIDEBAR_ANCHOR in src:
        insert = (
            '    if st.button("📚  Library Match",  key="nav_lib",    use_container_width=True):\n'
            '        st.session_state["section"] = "library_match"\n'
            '    if st.button("📄  Export PDF",     key="nav_export", use_container_width=True):\n'
            '        st.session_state["section"] = "export"\n\n'
        )
        src = src.replace(SIDEBAR_ANCHOR, insert + SIDEBAR_ANCHOR, 1)
        print("  ✓ added Library Match + Export PDF sidebar buttons")
        changed = True
    elif 'nav_export' in src:
        print("  ⚠ sidebar buttons already present")

    # Routing branches
    ROUTE_ANCHOR = 'elif section == "dose":         render_dose_tab()'
    if '"library_match"' not in src and ROUTE_ANCHOR in src:
        src = src.replace(
            ROUTE_ANCHOR,
            ROUTE_ANCHOR
            + '\nelif section == "library_match": render_library_match_tab(db)'
            + '\nelif section == "export":        render_export_tab(db)'
        )
        print("  ✓ added library_match + export routing branches")
        changed = True
    elif '"library_match"' in src and '"export"' not in src:
        # library_match exists, just add export
        src = src.replace(
            'render_library_match_tab(db)',
            'render_library_match_tab(db)'
            '\nelif section == "export":        render_export_tab(db)'
        )
        print("  ✓ added export routing branch")
        changed = True
    else:
        print("  ⚠ routing branches already present or anchor not found")

    if changed:
        app.write_text(src, encoding="utf-8")
        print("  ✓ app.py saved")


print("\n═══════════════════════════════════════════════════════════════════")
print("Done. Now run:  streamlit run app.py")
print("═══════════════════════════════════════════════════════════════════")
