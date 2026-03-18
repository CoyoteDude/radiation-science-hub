"""
patch_all.py — three fixes in one pass
Run from ~/Downloads/pycharm_project:
    python patch_all.py
"""
import re
from pathlib import Path

PROJECT = Path(".")

# ═══════════════════════════════════════════════════════════
#  FIX 1 — sel_id conflict in analysis_tabs.py
# ═══════════════════════════════════════════════════════════
p = PROJECT / "analysis_tabs.py"
if p.exists():
    src = p.read_text()
    OLD = ('    default = 0\n'
           '    if "sel_id" in st.session_state and st.session_state["sel_id"] in db:\n'
           '        default = list(db.keys()).index(st.session_state["sel_id"])\n')
    NEW = ('    default = 0\n'
           '    # Use _pending_sel_id (non-widget staging key) to avoid conflicting\n'
           '    # with any widget that has key="sel_id" in spectroscopy_module.py\n'
           '    _pending = st.session_state.pop("_pending_sel_id", None)\n'
           '    if _pending and _pending in db:\n'
           '        default = list(db.keys()).index(_pending)\n')
    if OLD in src:
        p.write_text(src.replace(OLD, NEW, 1))
        print("FIX 1 applied: sel_id conflict resolved in analysis_tabs.py")
    elif "_pending_sel_id" in src:
        print("FIX 1: already applied")
    else:
        print("FIX 1: pattern not found — check analysis_tabs.py manually")
else:
    print("FIX 1: analysis_tabs.py not found")

# ═══════════════════════════════════════════════════════════
#  FIX 2 — expand mineral_type in spectroscopy_module.py
# ═══════════════════════════════════════════════════════════
p = PROJECT / "spectroscopy_module.py"
if p.exists():
    src = p.read_text()

    # Big comprehensive mineral/sample type list
    MINERAL_TYPES = '''[
        # ── Unknown / generic ────────────────────────────────────────
        "Unknown / unclassified",
        "Custom (see notes)",

        # ── Igneous rocks ────────────────────────────────────────────
        "Granite",
        "Granodiorite",
        "Diorite",
        "Gabbro",
        "Basalt",
        "Andesite",
        "Rhyolite",
        "Obsidian",
        "Pumice",
        "Tuff",
        "Pegmatite",
        "Syenite",
        "Nepheline syenite",
        "Peridotite",
        "Dunite",
        "Komatiite",
        "Phonolite",

        # ── Metamorphic rocks ─────────────────────────────────────────
        "Gneiss",
        "Schist",
        "Phyllite",
        "Slate",
        "Quartzite",
        "Marble",
        "Hornfels",
        "Amphibolite",
        "Eclogite",
        "Migmatite",
        "Greenstone",

        # ── Sedimentary rocks ─────────────────────────────────────────
        "Sandstone",
        "Shale",
        "Mudstone",
        "Siltstone",
        "Limestone",
        "Chalk",
        "Dolomite",
        "Conglomerate",
        "Breccia",
        "Chert / Flint",
        "Ironstone",
        "Coal",
        "Lignite",
        "Oil shale",
        "Evaporite",
        "Rock salt (halite)",
        "Gypsum rock",
        "Travertine",

        # ── Mineral specimens ─────────────────────────────────────────
        "Quartz",
        "Feldspar",
        "Mica (muscovite/biotite)",
        "Amphibole",
        "Pyroxene",
        "Olivine",
        "Calcite",
        "Dolomite (mineral)",
        "Apatite",
        "Zircon",
        "Tourmaline",
        "Garnet",
        "Epidote",
        "Chlorite",
        "Serpentine",
        "Talc",
        "Kaolin / Kaolinite",
        "Montmorillonite / Smectite",
        "Illite",
        "Chlorite (clay)",
        "Barite",
        "Fluorite",
        "Gypsum (mineral)",
        "Anhydrite",
        "Halite",
        "Sylvite",
        "Pyrite",
        "Pyrrhotite",
        "Marcasite",
        "Chalcopyrite",
        "Galena",
        "Sphalerite",
        "Magnetite",
        "Hematite",
        "Ilmenite",
        "Rutile",
        "Chromite",
        "Spinel",
        "Corundum",
        "Diamond",
        "Graphite",
        "Sulfur",

        # ── NORM / radioactive minerals ───────────────────────────────
        "Monazite",
        "Xenotime",
        "Uraninite (pitchblende)",
        "Uranophane",
        "Autunite",
        "Carnotite",
        "Coffinite",
        "Thorianite",
        "Thorite",
        "Allanite",
        "Euxenite",
        "Samarskite",
        "Fergusonite",
        "Columbite-tantalite",
        "Pyrochlore",
        "Betafite",
        "Davidite",
        "Brannerite",

        # ── Phosphate minerals & fertilizers ──────────────────────────
        "Phosphate rock (apatite ore)",
        "Phosphorite",
        "Triple superphosphate",
        "Single superphosphate",
        "Ammonium phosphate",
        "Potassium fertilizer (KCl/K2SO4)",
        "NPK fertilizer blend",

        # ── Soils & sediments ─────────────────────────────────────────
        "Topsoil",
        "Sandy soil",
        "Clay soil",
        "Loam",
        "Peat",
        "Alluvial sediment",
        "Marine sediment",
        "Lake sediment",
        "River sand",
        "Beach sand",
        "Mineral sand (heavy mineral)",
        "Black sand (ilmenite/magnetite)",
        "Volcanic ash",
        "Laterite",
        "Bauxite",
        "Red mud (bauxite residue)",

        # ── Water & liquids ───────────────────────────────────────────
        "Water sample (tap/river/lake)",
        "Groundwater",
        "Seawater",
        "Mineral water",
        "Brine",
        "Sediment slurry",

        # ── Building / industrial materials ───────────────────────────
        "Cement",
        "Concrete",
        "Mortar",
        "Brick (fired clay)",
        "Ceramic tile",
        "Gypsum board / plasterboard",
        "Plaster (gypsum)",
        "Fly ash (coal combustion)",
        "Bottom ash",
        "Slag (blast furnace)",
        "Phosphogypsum (by-product)",
        "TENORM pipe scale",
        "TENORM sludge",
        "Asphalt / bitumen",
        "Coal ash",
        "Zircon sand (industrial)",

        # ── Metals & alloys ───────────────────────────────────────────
        "Steel / iron",
        "Stainless steel",
        "Aluminium",
        "Copper",
        "Lead",
        "Tungsten",
        "Uranium metal / alloy",
        "Thorium metal",
        "Depleted uranium",

        # ── Industrial / sealed sources ────────────────────────────────
        "Sealed radioactive source",
        "Smoke detector (Am-241)",
        "Luminous paint / dial",
        "Radium legacy source",
        "Industrial gauge source",
        "Well logging source",
        "Radiography source (Ir-192/Se-75)",

        # ── Calibration sources ────────────────────────────────────────
        "Calibration source — Cs-137",
        "Calibration source — Co-60",
        "Calibration source — Eu-152",
        "Calibration source — Ba-133",
        "Calibration source — Am-241",
        "Calibration source — Na-22",
        "Calibration source — Mn-54",
        "Calibration source — Zn-65",
        "Mixed calibration source",
        "Marinelli beaker standard",

        # ── Medical / pharmaceutical ───────────────────────────────────
        "Medical waste",
        "Nuclear medicine patient sample",
        "Radiopharmaceutical",

        # ── Environmental / field samples ──────────────────────────────
        "Air filter",
        "Air particulate",
        "Vegetation / plant matter",
        "Food sample",
        "Milk / dairy",
        "Meat / fish",
        "Grain / cereal",
        "Bone / tissue",
        "Urine / biological fluid",
        "Swipe / wipe sample",

        # ── Background & reference ─────────────────────────────────────
        "Background measurement",
        "Blank / empty container",
        "Reference material (certified)",
    ]'''

    # Find the existing mineral_type selectbox by looking for MINERAL_TYPES list or short list
    # Try common patterns for the selectbox in import tab
    patterns_to_try = [
        # Pattern A: already a MINERAL_TYPES variable
        (r'MINERAL_TYPES\s*=\s*\[.*?\]', 'MINERAL_TYPES = ' + MINERAL_TYPES),
        # Pattern B: inline short list in selectbox (the most likely case)
        (r'mineral_type\s*=\s*st\.selectbox\s*\(\s*["\']Mineral[^)]+\)',
         None),  # handled separately below
    ]

    # Check if MINERAL_TYPES already exists as a variable
    if 'MINERAL_TYPES' in src:
        # Replace the existing list
        new_src = re.sub(r'MINERAL_TYPES\s*=\s*\[.*?\]',
                         'MINERAL_TYPES = ' + MINERAL_TYPES,
                         src, flags=re.DOTALL, count=1)
        if new_src != src:
            p.write_text(new_src)
            print("FIX 2 applied: MINERAL_TYPES variable expanded")
        else:
            print("FIX 2: MINERAL_TYPES pattern replacement failed")
    else:
        # Find the mineral_type selectbox and inject a MINERAL_TYPES constant before it,
        # then replace the inline list with the variable reference
        mineral_selectbox_re = re.search(
            r'(mineral_type\s*=\s*st\.selectbox\s*\(\s*["\'][Mm]ineral[^"\']*["\'],\s*\[)(.*?)(\],)',
            src, re.DOTALL
        )
        if mineral_selectbox_re:
            # Replace inline list with variable reference
            old_call = mineral_selectbox_re.group(0)
            # Build replacement: mineral_type = st.selectbox("...", MINERAL_TYPES, ...)
            # Keep everything after the closing bracket
            prefix = mineral_selectbox_re.group(1)  # "mineral_type = st.selectbox("...", ["
            # Find where the selectbox call ends (closing parenthesis)
            start = mineral_selectbox_re.start()
            # Find matching )
            depth = 0
            end = start
            for i, ch in enumerate(src[start:]):
                if ch == '(': depth += 1
                elif ch == ')':
                    depth -= 1
                    if depth == 0:
                        end = start + i + 1
                        break
            old_full = src[start:end]
            # Extract the selectbox arguments beyond the list to preserve key= etc.
            # Find the key= argument
            key_match = re.search(r'key\s*=\s*["\'][^"\']+["\']', old_full)
            key_arg = key_match.group(0) if key_match else 'key="imp_mineral"'
            # Find label
            label_match = re.search(r'st\.selectbox\s*\(\s*(["\'][^"\']+["\'])', old_full)
            label = label_match.group(1) if label_match else '"Sample / mineral type"'

            new_call = f'mineral_type = st.selectbox({label}, MINERAL_TYPES, {key_arg})'

            # Inject MINERAL_TYPES constant before the line containing the selectbox
            line_start = src.rfind('\n', 0, start) + 1
            injection = f'MINERAL_TYPES = {MINERAL_TYPES}\n\n'
            new_src = src[:line_start] + injection + src[line_start:start] + new_call + src[end:]
            p.write_text(new_src)
            print("FIX 2 applied: mineral_type selectbox expanded with 100+ options")
        else:
            # Fallback: just inject MINERAL_TYPES at module level and note it
            # Find "def render_spectroscopy" and inject before it
            insert_point = src.find('\ndef render_spectroscopy(')
            if insert_point == -1:
                insert_point = src.find('\ndef save_db(')
            if insert_point == -1:
                insert_point = 0
            injection = f'\nMINERAL_TYPES = {MINERAL_TYPES}\n'
            new_src = src[:insert_point] + injection + src[insert_point:]
            p.write_text(new_src)
            print("FIX 2 partial: MINERAL_TYPES injected — find your mineral_type selectbox")
            print("  and change its options list to: MINERAL_TYPES")

print("FIX 3: PDF export — see report_export.py (separate file)")
print("\nDone.")
