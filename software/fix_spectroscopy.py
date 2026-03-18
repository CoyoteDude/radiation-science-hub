"""
fix_spectroscopy.py  —  Precise fix for spectroscopy_module.py
───────────────────────────────────────────────────────────────
Run from your project directory:
    cd ~/Downloads/pycharm_project
    python fix_spectroscopy.py
"""
import re
from pathlib import Path

PROJECT = Path(".")

# ══════════════════════════════════════════════════════════════════════════════
#  spectroscopy_module.py
# ══════════════════════════════════════════════════════════════════════════════
sm = PROJECT / "spectroscopy_module.py"
if not sm.exists():
    print("ERROR: spectroscopy_module.py not found")
    raise SystemExit(1)

src = sm.read_text(encoding="utf-8")
print(f"Loaded: {src.count(chr(10))} lines")

# ── 1. Remove ALL existing bad MINERAL_TYPES injections ───────────────────────
while "MINERAL_TYPES" in src:
    new_src = re.sub(
        r'\n\n?# ?[─\-]+ Sample.*?\n?MINERAL_TYPES\s*=\s*\[.*?\]\n\n?',
        '\n',
        src, flags=re.DOTALL, count=1
    )
    if new_src == src:
        # Try simpler pattern
        new_src = re.sub(
            r'\nMINERAL_TYPES\s*=\s*\[.*?\]\n',
            '\n',
            src, flags=re.DOTALL, count=1
        )
    if new_src == src:
        print("⚠ Could not remove existing MINERAL_TYPES — trying line-by-line")
        lines = src.splitlines(keepends=True)
        # Find the MINERAL_TYPES = [ line and the closing ]
        start_i = end_i = None
        for i, line in enumerate(lines):
            if re.match(r'\s*MINERAL_TYPES\s*=\s*\[', line):
                start_i = i
            if start_i is not None and i > start_i and re.match(r'\s*\]\s*$', line):
                end_i = i
                break
        if start_i is not None and end_i is not None:
            del lines[start_i:end_i+1]
            # Also remove any comment line immediately before
            if start_i > 0 and '──' in lines[start_i-1]:
                del lines[start_i-1]
            src = "".join(lines)
            print(f"  Removed lines {start_i+1}–{end_i+1}")
        else:
            print("  Cannot find boundaries — aborting MINERAL_TYPES removal")
        break
    src = new_src
    print("✓ Removed an existing MINERAL_TYPES block")

# ── 2. Also fix any IndentationError from injected block inside a function ─────
# The error was at line 413: spec_css() with unexpected indent.
# This means our injection inserted blank lines + text INSIDE a function.
# We already removed it above, but let's verify there are no orphaned lines.
if "MINERAL_TYPES" in src:
    print("⚠ MINERAL_TYPES still present after removal attempt — manual cleanup needed")
else:
    print("✓ MINERAL_TYPES removed from file")

# ── 3. Build the MINERAL_TYPES constant ───────────────────────────────────────
ITEMS = [
    "Unknown / unclassified", "Custom (see notes)",
    # Igneous rocks
    "Granite", "Granodiorite", "Diorite", "Gabbro", "Basalt", "Andesite",
    "Rhyolite", "Obsidian", "Pumice", "Tuff", "Pegmatite", "Syenite",
    "Nepheline syenite", "Peridotite", "Dunite", "Phonolite",
    # Metamorphic rocks
    "Gneiss", "Schist", "Phyllite", "Slate", "Quartzite", "Marble",
    "Hornfels", "Amphibolite", "Eclogite", "Migmatite", "Greenstone",
    # Sedimentary rocks
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
    # NORM / radioactive minerals
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
    # Industrial / sealed sources
    "Sealed radioactive source", "Smoke detector (Am-241)",
    "Luminous paint / dial", "Radium legacy source",
    "Industrial gauge source", "Well logging source",
    "Radiography source (Ir-192/Se-75)",
    # Calibration sources
    "Calibration source -- Cs-137", "Calibration source -- Co-60",
    "Calibration source -- Eu-152", "Calibration source -- Ba-133",
    "Calibration source -- Am-241", "Calibration source -- Na-22",
    "Calibration source -- Mn-54", "Calibration source -- Zn-65",
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

item_lines = ",\n".join(f'    {repr(item)}' for item in ITEMS)
MINERAL_BLOCK = f"MINERAL_TYPES = [\n{item_lines},\n]\n"

# ── 4. Inject MINERAL_TYPES at EXACTLY the right spot ─────────────────────────
# From the file we know the structure ends with:
#   SPEC_DIR.mkdir(parents=True, exist_ok=True)
# followed immediately by:
#   def load_db():
# We insert between them.

ANCHOR = "SPEC_DIR.mkdir(parents=True, exist_ok=True)"
if ANCHOR in src:
    src = src.replace(
        ANCHOR,
        ANCHOR + "\n\n" + MINERAL_BLOCK,
        1
    )
    print(f"✓ Injected MINERAL_TYPES after '{ANCHOR}'")
else:
    # Fallback: inject before the first def
    first_def = src.find("\ndef ")
    if first_def == -1:
        first_def = src.find("\nclass ")
    if first_def != -1:
        src = src[:first_def] + "\n\n" + MINERAL_BLOCK + src[first_def:]
        print("✓ Injected MINERAL_TYPES before first def (fallback)")
    else:
        print("ERROR: could not find injection point")
        raise SystemExit(1)

# ── 5. Wire into the selectbox ────────────────────────────────────────────────
replaced = False
for pat in [
    # mineral_type = st.selectbox("...", [...shortlist...], key=...)
    r'(mineral_type\s*=\s*st\.selectbox\s*\([^,]+,\s*)\[[^\]]{1,3000}?\]',
    # st.selectbox("Mineral type", [...], ...)
    r'(st\.selectbox\s*\(\s*["\'][Mm]ineral[^"\']*["\'],\s*)\[[^\]]{1,3000}?\]',
    # st.selectbox("Sample type", [...], ...)  -- in case it's labelled differently
    r'(st\.selectbox\s*\(\s*["\'][Ss]ample\s+type[^"\']*["\'],\s*)\[[^\]]{1,3000}?\]',
]:
    new_src = re.sub(pat, r'\1MINERAL_TYPES', src, count=1, flags=re.DOTALL)
    if new_src != src:
        src = new_src
        replaced = True
        print("✓ Wired MINERAL_TYPES into selectbox")
        break

if not replaced:
    print("⚠ Could not auto-wire selectbox.")
    print("  Search your file for 'mineral_type' and change its options to MINERAL_TYPES")

# ── 6. Fix sel_id issues ──────────────────────────────────────────────────────
print("\n── sel_id fixes ────────────────────────────────────────────────────────")

if 'st.session_state["sel_id"] = entry["id"]' in src:
    src = src.replace(
        'st.session_state["sel_id"] = entry["id"]',
        'st.session_state["_pending_sel_id"] = entry["id"]'
    )
    print('✓ Analyze button: sel_id → _pending_sel_id')

if 'st.session_state["sel_id"] = st.session_state.pop("_pending_sel_id")' in src:
    src = src.replace(
        'st.session_state["sel_id"] = st.session_state.pop("_pending_sel_id")',
        'st.session_state["_active_sel_id"] = st.session_state.pop("_pending_sel_id")'
    )
    print('✓ Consumer block: sel_id → _active_sel_id')

if 'key="sel_id"' in src:
    src = src.replace('key="sel_id"', 'key="sel_id_identify"')
    print("✓ Renamed key='sel_id' widget")

# ── 7. Save spectroscopy_module.py ────────────────────────────────────────────
sm.write_text(src, encoding="utf-8")
print(f"\n✓ spectroscopy_module.py saved ({src.count(chr(10))} lines)")

# Quick syntax check
import py_compile, tempfile, shutil
tmp = Path(tempfile.mktemp(suffix=".py"))
shutil.copy(sm, tmp)
try:
    py_compile.compile(str(tmp), doraise=True)
    print("✓ Syntax check PASSED")
except py_compile.PyCompileError as e:
    print(f"✗ Syntax check FAILED: {e}")
    print("  Check the file manually around the injection point")
finally:
    tmp.unlink(missing_ok=True)

# ══════════════════════════════════════════════════════════════════════════════
#  analysis_tabs.py — fix sel_id read
# ══════════════════════════════════════════════════════════════════════════════
print("\n── analysis_tabs.py ────────────────────────────────────────────────────")
at = PROJECT / "analysis_tabs.py"
if at.exists():
    src2 = at.read_text(encoding="utf-8")
    changed = False
    for old, new in [
        (
            '    default = 0\n'
            '    if "sel_id" in st.session_state and st.session_state["sel_id"] in db:\n'
            '        default = list(db.keys()).index(st.session_state["sel_id"])\n',
            '    default = 0\n'
            '    _pend = st.session_state.pop("_pending_sel_id", None) or st.session_state.get("_active_sel_id")\n'
            '    if _pend and _pend in db:\n'
            '        default = list(db.keys()).index(_pend)\n'
        ),
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
        (
            '    default = 0\n'
            '    _pend = st.session_state.pop("_pending_sel_id", None) or st.session_state.get("_active_sel_id")\n'
            '    if _pend and _pend in db:\n'
            '        default = list(db.keys()).index(_pend)\n',
            '    default = 0\n'
            '    _pend = st.session_state.pop("_pending_sel_id", None) or st.session_state.get("_active_sel_id")\n'
            '    if _pend and _pend in db:\n'
            '        default = list(db.keys()).index(_pend)\n'
        ),
    ]:
        if old in src2:
            src2 = src2.replace(old, new, 1)
            changed = True
            print("✓ Fixed _get_entry_and_peaks default logic")
            break
    if not changed:
        if '"sel_id"' not in src2:
            print("✓ Already fixed (no sel_id references)")
        else:
            print("⚠ Pattern not matched. Current sel_id lines:")
            for i, line in enumerate(src2.splitlines(), 1):
                if "sel_id" in line:
                    print(f"  {i:4d}: {line}")
    else:
        at.write_text(src2, encoding="utf-8")
        print("✓ analysis_tabs.py saved")
else:
    print("⚠ analysis_tabs.py not found")

# ══════════════════════════════════════════════════════════════════════════════
#  app.py — wire export + library match
# ══════════════════════════════════════════════════════════════════════════════
print("\n── app.py ──────────────────────────────────────────────────────────────")
app = PROJECT / "app.py"
if app.exists():
    src3 = app.read_text(encoding="utf-8")
    orig3 = src3

    if "render_export_tab" not in src3:
        src3 = src3.replace(
            "from spectrum_db import load_db",
            "from spectrum_db import load_db\nfrom report_export import render_export_tab"
        )
        print("✓ Added render_export_tab import")

    if "render_library_match_tab" not in src3 and (PROJECT / "library_match_tab.py").exists():
        src3 = src3.replace(
            "from spectrum_db import load_db",
            "from spectrum_db import load_db\nfrom library_match_tab import render_library_match_tab"
        )
        print("✓ Added render_library_match_tab import")

    SIDEBAR_ANCHOR = '    st.markdown("---")'
    if "nav_export" not in src3 and SIDEBAR_ANCHOR in src3:
        src3 = src3.replace(
            SIDEBAR_ANCHOR,
            '    if st.button("📄  Export PDF", key="nav_export", use_container_width=True):\n'
            '        st.session_state["section"] = "export"\n\n'
            + SIDEBAR_ANCHOR,
            1
        )
        print("✓ Added Export PDF sidebar button")

    ROUTE = 'elif section == "dose":         render_dose_tab()'
    if '"export"' not in src3 and ROUTE in src3:
        src3 = src3.replace(
            ROUTE,
            ROUTE + '\nelif section == "export":        render_export_tab(db)'
        )
        print("✓ Added export route")

    if src3 != orig3:
        app.write_text(src3, encoding="utf-8")
        print("✓ app.py saved")
    else:
        print("  (no changes needed)")

print("\n═══════════════════════════════════════════════════════════════════")
print("Done.  streamlit run app.py")
print("═══════════════════════════════════════════════════════════════════")
