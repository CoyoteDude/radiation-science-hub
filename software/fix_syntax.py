"""
fix_syntax.py  —  Emergency syntax fix
───────────────────────────────────────
The previous script injected MINERAL_TYPES at the wrong line.
This script removes it from the wrong place and puts it correctly.

Run from your project directory:
    cd ~/Downloads/pycharm_project
    python fix_syntax.py
"""
import re
from pathlib import Path

PROJECT = Path(".")
TARGET  = PROJECT / "spectroscopy_module.py"

if not TARGET.exists():
    print("ERROR: spectroscopy_module.py not found")
    raise SystemExit(1)

src = TARGET.read_text(encoding="utf-8")
print(f"File loaded: {len(src)} chars, {src.count(chr(10))} lines")

# ── Step 1: Remove any existing bad MINERAL_TYPES injection ──────────────────
if "MINERAL_TYPES" in src:
    # Remove the whole MINERAL_TYPES = [...] assignment wherever it is
    new_src = re.sub(
        r'\n+MINERAL_TYPES\s*=\s*\[.*?\]\n+',
        '\n',
        src,
        flags=re.DOTALL,
        count=1
    )
    if new_src != src:
        src = new_src
        print("✓ Removed misplaced MINERAL_TYPES injection")
    else:
        print("⚠ MINERAL_TYPES found but couldn't auto-remove — check manually")

# ── Step 2: Find a safe injection point ──────────────────────────────────────
# We want to inject MINERAL_TYPES after all imports (import/from lines)
# and after any module-level constants that are already there,
# but BEFORE any def or class.

lines = src.splitlines(keepends=True)

# Find the last import line index
last_import_idx = -1
for i, line in enumerate(lines):
    stripped = line.lstrip()
    if stripped.startswith("import ") or stripped.startswith("from "):
        last_import_idx = i

# Find the first def/class line index
first_def_idx = len(lines)
for i, line in enumerate(lines):
    stripped = line.lstrip()
    if stripped.startswith("def ") or stripped.startswith("class "):
        first_def_idx = i
        break

# Insert after last import but before first def, at a blank line
inject_after = last_import_idx
if inject_after == -1:
    inject_after = 0

# Find a blank line right after inject_after to make it clean
for i in range(inject_after, min(inject_after + 20, first_def_idx)):
    if lines[i].strip() == "":
        inject_after = i
        break

print(f"Injecting MINERAL_TYPES after line {inject_after + 1}  "
      f"(first def at line {first_def_idx + 1})")

# ── Step 3: Build the MINERAL_TYPES constant ─────────────────────────────────
ITEMS = [
    # Unknown / generic
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
    # Mineral specimens
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
    # Building / industrial materials
    "Cement", "Concrete", "Mortar", "Brick (fired clay)",
    "Ceramic tile", "Gypsum board / plasterboard", "Plaster (gypsum)",
    "Fly ash (coal combustion)", "Bottom ash", "Slag (blast furnace)",
    "Phosphogypsum (by-product)", "TENORM pipe scale", "TENORM sludge",
    "Asphalt / bitumen", "Coal ash", "Zircon sand (industrial)",
    # Metals & alloys
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

# Build a clean multi-line assignment
item_lines = []
for item in ITEMS:
    item_lines.append(f'    {repr(item)},')

mineral_block = (
    "\n\n# ── Sample / mineral type options ──────────────────────────────────────────\n"
    "MINERAL_TYPES = [\n"
    + "\n".join(item_lines)
    + "\n]\n\n"
)

# ── Step 4: Inject ────────────────────────────────────────────────────────────
lines.insert(inject_after + 1, mineral_block)
new_src = "".join(lines)

# ── Step 5: Wire MINERAL_TYPES into the selectbox ─────────────────────────────
# Replace any short inline list in a mineral_type selectbox
patterns = [
    # mineral_type = st.selectbox("Mineral type", [...], ...)
    (r'(mineral_type\s*=\s*st\.selectbox\s*\([^,]+,\s*)\[[^\]]{0,2000}?\]',
     r'\1MINERAL_TYPES'),
    # mineral_type = st.selectbox("Sample type", [...], ...)
    (r'(mineral_type\s*=\s*st\.selectbox\s*\([^,]+,\s*)\[[^\]]{0,2000}?\]',
     r'\1MINERAL_TYPES'),
]
replaced = False
for pat, repl in patterns:
    result = re.sub(pat, repl, new_src, count=1, flags=re.DOTALL)
    if result != new_src:
        new_src = result
        replaced = True
        print("✓ Wired MINERAL_TYPES into the mineral_type selectbox")
        break

if not replaced:
    print("⚠ Could not auto-wire selectbox — printing search context:")
    # Show lines around any selectbox that could be the mineral_type one
    for i, line in enumerate(new_src.splitlines()):
        if "mineral" in line.lower() and "selectbox" in line.lower():
            start = max(0, i - 1)
            end   = min(len(new_src.splitlines()), i + 3)
            for j, l in enumerate(new_src.splitlines()[start:end], start + 1):
                print(f"  {j:4d}: {l}")
    print("\n  Manual fix: change the options list in that selectbox to: MINERAL_TYPES")

# ── Step 6: Also fix sel_id issues ───────────────────────────────────────────
print("\n── sel_id fixes ────────────────────────────────────────────────────────")

# Fix 1: Analyze button in My Spectra — write to _pending_sel_id not sel_id
if 'st.session_state["sel_id"] = entry["id"]' in new_src:
    new_src = new_src.replace(
        'st.session_state["sel_id"] = entry["id"]',
        'st.session_state["_pending_sel_id"] = entry["id"]'
    )
    print("✓ Analyze button: changed sel_id → _pending_sel_id")
elif 'st.session_state["_pending_sel_id"] = entry["id"]' in new_src:
    print("✓ Analyze button already uses _pending_sel_id")
else:
    print("⚠ Analyze button pattern not found")

# Fix 2: Any consumer block that incorrectly sets sel_id from _pending_sel_id
bad_consumer = (
    '    if "_pending_sel_id" in st.session_state:\n'
    '        st.session_state["sel_id"] = st.session_state.pop("_pending_sel_id")\n'
)
if bad_consumer in new_src:
    new_src = new_src.replace(
        bad_consumer,
        '    if "_pending_sel_id" in st.session_state:\n'
        '        st.session_state["_active_sel_id"] = st.session_state.pop("_pending_sel_id")\n'
    )
    print("✓ Fixed consumer block: sel_id → _active_sel_id")

# Fix 3: Any selectbox using key="sel_id" — rename to avoid conflict
if 'key="sel_id"' in new_src:
    new_src = new_src.replace('key="sel_id"', 'key="sel_id_identify"')
    print("✓ Renamed key='sel_id' widget to 'sel_id_identify'")
elif "key='sel_id'" in new_src:
    new_src = new_src.replace("key='sel_id'", "key='sel_id_identify'")
    print("✓ Renamed key='sel_id' widget to 'sel_id_identify'")
else:
    print("  (no key='sel_id' widget found in this file)")

# ── Step 7: Save ──────────────────────────────────────────────────────────────
TARGET.write_text(new_src, encoding="utf-8")
print(f"\n✓ spectroscopy_module.py saved ({new_src.count(chr(10))} lines)")

# ── Step 8: Fix analysis_tabs.py sel_id read ─────────────────────────────────
print("\n── analysis_tabs.py ────────────────────────────────────────────────────")

at = PROJECT / "analysis_tabs.py"
if at.exists():
    src2 = at.read_text(encoding="utf-8")
    changed = False

    # Remove any existing partial fix
    for old, new in [
        # Previous partial patch
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
        # Previous partial patch v2
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
        # Original unfixed version
        (
            '    default = 0\n'
            '    if "sel_id" in st.session_state and st.session_state["sel_id"] in db:\n'
            '        default = list(db.keys()).index(st.session_state["sel_id"])\n',
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
        if '"sel_id"' not in src2 and '_pend' in src2:
            print("✓ analysis_tabs.py already fixed")
        else:
            print("⚠ Pattern not matched — current state of default logic:")
            for i, line in enumerate(src2.splitlines()):
                if 'default' in line or 'sel_id' in line:
                    print(f"  {i+1:4d}: {line}")

    if changed:
        at.write_text(src2, encoding="utf-8")
        print("✓ analysis_tabs.py saved")
else:
    print("⚠ analysis_tabs.py not found")

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n═══════════════════════════════════════════════════════════════════")
print("Done.  Now run:  streamlit run app.py")
print("═══════════════════════════════════════════════════════════════════")
