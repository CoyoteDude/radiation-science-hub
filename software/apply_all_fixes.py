"""
apply_all_fixes.py
──────────────────
Run from your project directory:
    cd ~/Downloads/pycharm_project
    python apply_all_fixes.py

Fixes:
  1. mineral_type selectbox — 100+ options
  2. sel_id widget conflict
  3. app.py — add Library Match + Export PDF sidebar buttons + routing
  4. Prints a diagnostic of what it found so nothing is silent
"""
import re, sys
from pathlib import Path

P = Path(".")

def load(name):
    f = P / name
    if not f.exists():
        print(f"  ✗ {name} NOT FOUND"); return None
    return f.read_text(encoding="utf-8")

def save(name, src):
    (P / name).write_text(src, encoding="utf-8")
    print(f"  ✓ saved {name}")

def syntax_ok(name):
    import py_compile, tempfile, shutil
    tmp = Path(tempfile.mktemp(suffix=".py"))
    shutil.copy(P / name, tmp)
    try:
        py_compile.compile(str(tmp), doraise=True)
        print(f"  ✓ syntax OK: {name}")
        return True
    except py_compile.PyCompileError as e:
        print(f"  ✗ syntax FAIL: {name}: {e}")
        return False
    finally:
        tmp.unlink(missing_ok=True)

MINERAL_TYPES = [
    "Unknown / unclassified", "Custom (see notes)",
    # Igneous
    "Granite","Granodiorite","Diorite","Gabbro","Basalt","Andesite",
    "Rhyolite","Obsidian","Pumice","Tuff","Pegmatite","Syenite",
    "Nepheline syenite","Peridotite","Dunite","Phonolite",
    # Metamorphic
    "Gneiss","Schist","Phyllite","Slate","Quartzite","Marble",
    "Hornfels","Amphibolite","Eclogite","Migmatite","Greenstone",
    # Sedimentary
    "Sandstone","Shale","Mudstone","Siltstone","Limestone","Chalk",
    "Dolomite rock","Conglomerate","Breccia","Chert / Flint","Ironstone",
    "Coal","Lignite","Oil shale","Evaporite","Rock salt (halite)",
    "Gypsum rock","Travertine",
    # Minerals
    "Quartz","Feldspar","Mica (muscovite/biotite)","Amphibole",
    "Pyroxene","Olivine","Calcite","Dolomite mineral","Apatite",
    "Zircon","Tourmaline","Garnet","Epidote","Chlorite","Serpentine",
    "Talc","Kaolin / Kaolinite","Montmorillonite / Smectite",
    "Illite","Barite","Fluorite","Gypsum mineral","Anhydrite",
    "Halite","Sylvite","Pyrite","Pyrrhotite","Chalcopyrite",
    "Galena","Sphalerite","Magnetite","Hematite","Ilmenite",
    "Rutile","Chromite","Spinel","Corundum","Graphite","Sulfur",
    # NORM / radioactive
    "Monazite","Xenotime","Uraninite (pitchblende)","Uranophane",
    "Autunite","Carnotite","Coffinite","Thorianite","Thorite",
    "Allanite","Euxenite","Samarskite","Columbite-tantalite",
    "Pyrochlore","Betafite","Davidite","Brannerite",
    # Phosphates / fertilizers
    "Phosphate rock (apatite ore)","Phosphorite",
    "Triple superphosphate","Single superphosphate",
    "Ammonium phosphate","Potassium fertilizer (KCl/K2SO4)",
    "NPK fertilizer blend",
    # Soils & sediments
    "Topsoil","Sandy soil","Clay soil","Loam","Peat",
    "Alluvial sediment","Marine sediment","Lake sediment",
    "River sand","Beach sand","Mineral sand (heavy mineral)",
    "Black sand (ilmenite/magnetite)","Volcanic ash",
    "Laterite","Bauxite","Red mud (bauxite residue)",
    # Water
    "Water sample (tap/river/lake)","Groundwater","Seawater",
    "Mineral water","Brine","Sediment slurry",
    # Building / industrial
    "Cement","Concrete","Mortar","Brick (fired clay)",
    "Ceramic tile","Gypsum board / plasterboard","Plaster (gypsum)",
    "Fly ash (coal combustion)","Bottom ash","Slag (blast furnace)",
    "Phosphogypsum (by-product)","TENORM pipe scale","TENORM sludge",
    "Asphalt / bitumen","Coal ash","Zircon sand (industrial)",
    # Metals
    "Steel / iron","Stainless steel","Aluminium","Copper","Lead",
    "Tungsten","Uranium metal / alloy","Thorium metal","Depleted uranium",
    # Sources
    "Sealed radioactive source","Smoke detector (Am-241)",
    "Luminous paint / dial","Radium legacy source",
    "Industrial gauge source","Well logging source",
    "Radiography source (Ir-192/Se-75)",
    # Calibration
    "Calibration source -- Cs-137","Calibration source -- Co-60",
    "Calibration source -- Eu-152","Calibration source -- Ba-133",
    "Calibration source -- Am-241","Calibration source -- Na-22",
    "Calibration source -- Mn-54","Calibration source -- Zn-65",
    "Mixed calibration source","Marinelli beaker standard",
    # Medical
    "Medical waste","Nuclear medicine patient sample","Radiopharmaceutical",
    # Environmental
    "Air filter","Air particulate","Vegetation / plant matter",
    "Food sample","Milk / dairy","Meat / fish","Grain / cereal",
    "Bone / tissue","Urine / biological fluid","Swipe / wipe sample",
    # Reference
    "Background measurement","Blank / empty container",
    "Reference material (certified)",
]

MT_LINES = ",\n".join(f'    {repr(x)}' for x in MINERAL_TYPES)
MT_BLOCK = f"MINERAL_TYPES = [\n{MT_LINES},\n]\n"

# ══════════════════════════════════════════════════════════════════════════════
print("\n━━━━ spectroscopy_module.py ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
src = load("spectroscopy_module.py")
if src:
    orig = src

    # ── Remove any previous bad MINERAL_TYPES injection ────────────────────
    while "MINERAL_TYPES" in src:
        new = re.sub(r'\nMINERAL_TYPES\s*=\s*\[.*?\]\n', '\n', src, count=1, flags=re.DOTALL)
        if new == src:
            # line-by-line removal
            lines = src.splitlines(keepends=True)
            si = ei = None
            for i,l in enumerate(lines):
                if re.match(r'\s*MINERAL_TYPES\s*=\s*\[', l): si = i
                if si and i > si and re.match(r'\s*\]\s*\n?$', l): ei = i; break
            if si is not None and ei is not None:
                # also remove comment line before if it's a divider
                if si > 0 and re.match(r'\s*#\s*[─\-═]+', lines[si-1]):
                    si -= 1
                del lines[si:ei+1]
                src = "".join(lines)
                print(f"  removed MINERAL_TYPES block (lines {si+1}–{ei+1})")
            else:
                print("  ⚠ could not remove MINERAL_TYPES — manual cleanup needed")
                break
        else:
            src = new
            print("  removed old MINERAL_TYPES block")

    # ── Find injection point: after SPEC_DIR.mkdir line ────────────────────
    # We know from the file: SPEC_DIR.mkdir(parents=True, exist_ok=True)
    # is the last module-level statement before def load_db()
    ANCHOR = "SPEC_DIR.mkdir(parents=True, exist_ok=True)"
    if ANCHOR in src:
        src = src.replace(ANCHOR, ANCHOR + "\n\n" + MT_BLOCK, 1)
        print(f"  ✓ injected MINERAL_TYPES after '{ANCHOR}'")
    else:
        # Fallback: before first def at column 0
        m = re.search(r'\ndef [a-z]', src)
        if m:
            src = src[:m.start()+1] + "\n" + MT_BLOCK + src[m.start()+1:]
            print("  ✓ injected MINERAL_TYPES before first def (fallback)")
        else:
            print("  ✗ could not find injection point")

    # ── Wire into selectbox ─────────────────────────────────────────────────
    # Show all selectbox lines that contain 'mineral' or 'sample' to diagnose
    found_box = False
    for i,line in enumerate(src.splitlines(), 1):
        if 'selectbox' in line and ('mineral' in line.lower() or 'sample' in line.lower()):
            print(f"  found selectbox at line {i}: {line.strip()[:80]}")
            found_box = True

    # Try replacing the options list in any mineral_type selectbox
    for pat in [
        r'(mineral_type\s*=\s*st\.selectbox\s*\([^,\n]+,\s*)\[[^\]]{2,3000}?\]',
        r'(st\.selectbox\s*\(\s*"[Mm]ineral[^"]*",\s*)\[[^\]]{2,3000}?\]',
        r'(st\.selectbox\s*\(\s*"[Ss]ample[^"]*type[^"]*",\s*)\[[^\]]{2,3000}?\]',
    ]:
        new = re.sub(pat, r'\1MINERAL_TYPES', src, count=1, flags=re.DOTALL)
        if new != src:
            src = new
            print("  ✓ wired MINERAL_TYPES into selectbox")
            found_box = True
            break

    if not found_box:
        print("  ⚠ no mineral_type selectbox found by pattern")
        print("  → search your file for 'mineral_type' and replace its list with: MINERAL_TYPES")

    # ── Fix sel_id ─────────────────────────────────────────────────────────
    replacements = [
        ('st.session_state["sel_id"] = entry["id"]',
         'st.session_state["_pending_sel_id"] = entry["id"]'),
        ("st.session_state['sel_id'] = entry['id']",
         "st.session_state['_pending_sel_id'] = entry['id']"),
        ('st.session_state["sel_id"] = st.session_state.pop("_pending_sel_id")',
         'st.session_state["_active_sel_id"] = st.session_state.pop("_pending_sel_id")'),
        ('key="sel_id"', 'key="sel_id_identify"'),
        ("key='sel_id'", "key='sel_id_identify'"),
    ]
    for old, new in replacements:
        if old in src:
            src = src.replace(old, new)
            print(f"  ✓ replaced: {old[:50]!r}")

    if src != orig:
        save("spectroscopy_module.py", src)
        syntax_ok("spectroscopy_module.py")
    else:
        print("  (no changes)")

# ══════════════════════════════════════════════════════════════════════════════
print("\n━━━━ analysis_tabs.py ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
src = load("analysis_tabs.py")
if src:
    orig = src
    # Show current default/sel_id lines for diagnosis
    for i,line in enumerate(src.splitlines(), 1):
        if 'sel_id' in line or ('default' in line and 'sel' in line.lower()):
            print(f"  line {i}: {line.rstrip()}")

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
    ]:
        if old in src:
            src = src.replace(old, new, 1)
            print("  ✓ fixed _get_entry_and_peaks default logic")
            break
    else:
        if '"sel_id"' not in src:
            print("  ✓ already fixed (no sel_id references)")
        else:
            print("  ⚠ pattern not matched — sel_id still present")

    if src != orig:
        save("analysis_tabs.py", src)
        syntax_ok("analysis_tabs.py")

# ══════════════════════════════════════════════════════════════════════════════
print("\n━━━━ app.py ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
src = load("app.py")
if src:
    orig = src
    print("  current imports:")
    for i,l in enumerate(src.splitlines(),1):
        if l.startswith("from ") or l.startswith("import "):
            print(f"    {i}: {l}")
    print("  current routes:")
    for i,l in enumerate(src.splitlines(),1):
        if 'elif section ==' in l or 'if section ==' in l:
            print(f"    {i}: {l.strip()}")

    # ── Imports ─────────────────────────────────────────────────────────────
    if "render_export_tab" not in src:
        src = src.replace(
            "from spectrum_db import load_db",
            "from spectrum_db import load_db\nfrom report_export import render_export_tab",
            1)
        print("  ✓ added render_export_tab import")

    if "render_library_match_tab" not in src and (P/"library_match_tab.py").exists():
        src = src.replace(
            "from spectrum_db import load_db",
            "from spectrum_db import load_db\nfrom library_match_tab import render_library_match_tab",
            1)
        print("  ✓ added render_library_match_tab import")

    # ── Sidebar buttons ──────────────────────────────────────────────────────
    # Find the st.markdown("---") in the sidebar and insert before it
    SDIV = '    st.markdown("---")'
    if "nav_export" not in src:
        new_btns = ""
        if "render_library_match_tab" in src and "nav_lib" not in src:
            new_btns += (
                '    if st.button("📚  Library Match", key="nav_lib", use_container_width=True):\n'
                '        st.session_state["section"] = "library_match"\n'
            )
        new_btns += (
            '    if st.button("📄  Export PDF",    key="nav_export", use_container_width=True):\n'
            '        st.session_state["section"] = "export"\n\n'
        )
        if SDIV in src:
            src = src.replace(SDIV, new_btns + SDIV, 1)
            print("  ✓ added sidebar buttons")
        else:
            # Append before the last button block
            print(f"  ⚠ sidebar anchor '{SDIV}' not found — buttons not added")
            print("    Add manually to sidebar:")
            print('    if st.button("📄  Export PDF", key="nav_export", use_container_width=True):')
            print('        st.session_state["section"] = "export"')
    else:
        print("  (sidebar buttons already present)")

    # ── Routes ───────────────────────────────────────────────────────────────
    DOSE_ROUTE = 'elif section == "dose":         render_dose_tab()'
    if DOSE_ROUTE not in src:
        # Try a looser match
        DOSE_ROUTE = next((l.strip() for l in src.splitlines() if 'render_dose_tab' in l and 'elif' in l), None)
        if DOSE_ROUTE:
            DOSE_ROUTE = next(l for l in src.splitlines() if 'render_dose_tab' in l and 'elif' in l)

    if DOSE_ROUTE and '"export"' not in src:
        extra = ""
        if "render_library_match_tab" in src and '"library_match"' not in src:
            extra += '\nelif section == "library_match": render_library_match_tab(db)'
        extra += '\nelif section == "export":        render_export_tab(db)'
        src = src.replace(DOSE_ROUTE, DOSE_ROUTE + extra, 1)
        print("  ✓ added routes")
    elif '"export"' in src:
        print("  (routes already present)")
    else:
        print("  ⚠ dose route anchor not found — add manually at end of routing block:")
        print('  elif section == "export":        render_export_tab(db)')

    if src != orig:
        save("app.py", src)
        syntax_ok("app.py")

# ══════════════════════════════════════════════════════════════════════════════
print("\n━━━━ Summary ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
for f in ["spectroscopy_module.py","analysis_tabs.py","app.py","report_export.py","library_match_tab.py"]:
    exists = (P/f).exists()
    print(f"  {'✓' if exists else '✗'} {f}")
print("\nDone — run: streamlit run app.py")
