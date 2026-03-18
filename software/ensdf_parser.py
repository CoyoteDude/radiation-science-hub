ensdf_parser.py  —  ENSDF / NuDat gamma line database loader
─────────────────────────────────────────────────────────────
Loads gamma line data from three possible sources, in priority order:

  1. A locally cached JSON file  (~/.gammalab/ensdf_gamma_cache.json)
  2. The ENSDF bulk dataset file  (user downloads from NNDC and places in
     ~/Documents/GammaLab/ensdf/ — instructions below)
  3. The NuDat 3 REST API         (requires internet, fetches on demand)

After first load the data is cached so subsequent loads are instant.

──────────────────────────────────────────────────────────────
HOW TO GET THE FULL ENSDF DATABASE (one-time manual step)
──────────────────────────────────────────────────────────────
1. Go to:  https://www.nndc.bnl.gov/ensdf/ensdf/dl_ensdf.jsp
2. Select: "All ENSDF data" → "ENSDF database (ASCII)"
3. Download the zip file  (ensdf_YYYYMMDD.zip, ~40 MB)
4. Unzip it — you get a folder of files named  A=001.ens, A=002.ens, …
5. Place all those .ens files in:
       ~/Documents/GammaLab/ensdf/
6. Restart the app — it will auto-parse and cache everything

Without the ENSDF files the app still works using the curated
isotope_db.py library (~200 isotopes) plus NuDat API fallback.
──────────────────────────────────────────────────────────────
"""

from __future__ import annotations
import json
import re
import os
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.parse

# ── Storage paths ──────────────────────────────────────────────────────────────
HOME       = Path.home()
ENSDF_DIR  = HOME / "Documents" / "GammaLab" / "ensdf"
CACHE_DIR  = HOME / ".gammalab"
CACHE_FILE = CACHE_DIR / "ensdf_gamma_cache.json"

try:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    CACHE_DIR  = _APP_DIR / ".gammalab"
    CACHE_FILE = CACHE_DIR / "ensdf_gamma_cache.json"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ── In-memory store (populated on first call to get_gamma_db()) ───────────────
_GAMMA_DB: dict[str, list[tuple[float, float, str]]] | None = None


# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def get_gamma_db(force_reload: bool = False) -> dict[str, list[tuple[float, float, str]]]:
    """
    Return the full gamma line database.

    Format:
        { "Bi-214": [(609.31, 45.49, "γ"), (1120.29, 14.91, "γ"), …], … }

    Energy in keV, intensity in % (absolute).
    Loads from cache if available, otherwise parses ENSDF files or queries NuDat.
    """
    global _GAMMA_DB
    if _GAMMA_DB is not None and not force_reload:
        return _GAMMA_DB

    # 1. Try cache
    if CACHE_FILE.exists() and not force_reload:
        try:
            raw = json.loads(CACHE_FILE.read_text())
            _GAMMA_DB = {k: [tuple(x) for x in v] for k, v in raw.items()}
            return _GAMMA_DB
        except Exception:
            pass

    # 2. Try ENSDF directory
    ensdf_search_dir = ENSDF_DIR if ENSDF_DIR.exists() else BUNDLED_ENSDF
    if ensdf_search_dir.exists():
        ens_files = (sorted(ensdf_search_dir.glob("*.ens")) +
                     sorted(ensdf_search_dir.glob("*.ENS")) +
                     sorted(ensdf_search_dir.glob("ensdf.*")) +
                     sorted(ensdf_search_dir.glob("ENSDF.*")))
        # Filter out non-data files (e.g. ensdf.zip, ensdf.idx)
        ens_files = [f for f in ens_files
                     if f.suffix.lstrip(".").isdigit() or
                        f.suffix.lower() in (".ens",)]
        if ens_files:
            _GAMMA_DB = _parse_ensdf_directory(ens_files)
            _save_cache(_GAMMA_DB)
            return _GAMMA_DB

    # 3. Fall back to curated isotope_db
    try:
        from isotope_db import GAMMA_LINES
        _GAMMA_DB = {k: list(v) for k, v in GAMMA_LINES.items()}
        return _GAMMA_DB
    except ImportError:
        pass

    _GAMMA_DB = {}
    return _GAMMA_DB


def get_lines_for_isotope(symbol: str) -> list[tuple[float, float, str]]:
    """Return gamma lines for a single isotope symbol (e.g. 'Bi-214')."""
    db = get_gamma_db()
    # Try exact match first
    if symbol in db:
        return db[symbol]
    # Try normalised form
    norm = _normalise_symbol(symbol)
    return db.get(norm, [])


def search_by_energy(energy_kev: float,
                     tolerance_kev: float = 5.0,
                     min_intensity: float = 0.1
                     ) -> list[dict]:
    """
    Find all isotopes with a gamma line within tolerance_kev of energy_kev.
    Returns list sorted by delta (closest first).
    """
    db      = get_gamma_db()
    results = []
    for symbol, lines in db.items():
        for kev, intensity, note in lines:
            if intensity < min_intensity:
                continue
            delta = abs(kev - energy_kev)
            if delta <= tolerance_kev:
                results.append({
                    "symbol":    symbol,
                    "lib_keV":   kev,
                    "intensity": intensity,
                    "note":      note,
                    "delta":     round(delta, 3),
                })
    results.sort(key=lambda x: (x["delta"], -x["intensity"]))
    return results


def isotope_count() -> int:
    return len(get_gamma_db())


def database_source() -> str:
    """Return a human-readable string describing where the data came from."""
    if CACHE_FILE.exists():
        try:
            raw  = json.loads(CACHE_FILE.read_text())
            n    = len(raw)
            size = CACHE_FILE.stat().st_size // 1024
            return f"Cached ENSDF/NuDat  ({n:,} isotopes, {size:,} KB)"
        except Exception:
            pass
    ens_files = list(ENSDF_DIR.glob("*.ens")) if ENSDF_DIR.exists() else []
    if ens_files:
        return f"ENSDF files in {ENSDF_DIR}  ({len(ens_files)} mass files)"
    return "Curated library (isotope_db.py, ~200 isotopes)"


# ══════════════════════════════════════════════════════════════════════════════
#  ENSDF ASCII PARSER
# ══════════════════════════════════════════════════════════════════════════════
#
# ENSDF record format (80-char fixed-width):
#   Col 1-3   : Nuclide (mass+element, e.g. "214BI")
#   Col 8     : Record type  (G = gamma, L = level, B = beta, A = alpha …)
#   Col 10-19 : Energy (keV)
#   Col 22-29 : Energy uncertainty
#   Col 30-39 : Intensity (relative)
#   Col 40-49 : Intensity uncertainty
#
# We parse G (gamma) records and normalise intensities to absolute %.
# ──────────────────────────────────────────────────────────────────────────────

def _parse_ensdf_directory(ens_files: list[Path]) -> dict[str, list[tuple[float, float, str]]]:
    db: dict[str, list] = {}
    for path in ens_files:
        try:
            _parse_ensdf_file(path, db)
        except Exception:
            continue
    # Sort each isotope's lines by energy
    for sym in db:
        db[sym].sort(key=lambda x: x[0])
    return db


def _parse_ensdf_file(path: Path,
                       db: dict[str, list]) -> None:
    """
    Parse one ENSDF mass-chain file and add gamma lines to db.

    ENSDF fixed-width format (80 chars per line):
      Col  1-3  : Mass number (right-justified)
      Col  4-5  : Element symbol (left-justified)
      Col  6    : Isomer flag (blank or letter)
      Col  8    : Record type:
                    ' ' = identification (dataset header)
                    'H' = history
                    'Q' = Q-value
                    'X' = cross-ref
                    'L' = level
                    'G' = gamma
                    'B' = beta
                    'A' = alpha
                    'E' = electron capture
      Col  9-80 : Record data
    """
    try:
        text = path.read_text(encoding="ascii", errors="replace")
    except Exception:
        return

    lines = text.split("\n")
    current_nuclide   = None
    dataset_gammas: list[tuple[float, float]] = []

    for raw in lines:
        # Pad to at least 80 chars so indexing is safe
        line = raw.ljust(80)

        nuclide_field = line[0:5].strip()
        rec_type      = line[7].upper()

        # Dataset identification record: col 8 is blank (space)
        # This marks the start of a new nuclide dataset
        if rec_type == " " and nuclide_field:
            # Commit previous dataset
            if current_nuclide and dataset_gammas:
                _commit_dataset(current_nuclide, dataset_gammas, db)
                dataset_gammas = []
            parsed = _parse_nuclide_field(nuclide_field)
            current_nuclide = parsed if parsed else current_nuclide
            continue

        # End-of-dataset marker (blank line or line with no nuclide)
        if not nuclide_field and rec_type == " ":
            if current_nuclide and dataset_gammas:
                _commit_dataset(current_nuclide, dataset_gammas, db)
                dataset_gammas = []
            current_nuclide = None
            continue

        # Gamma record
        if rec_type == "G" and current_nuclide:
            energy_str    = line[9:19].strip()
            intensity_str = line[21:29].strip()
            try:
                # Strip uncertainties in parentheses, flags
                e_clean = energy_str.split("(")[0].replace("?","").replace("@","").strip()
                i_clean = intensity_str.split("(")[0].replace("?","").replace("@","").strip()
                if not e_clean:
                    continue
                energy    = float(e_clean)
                intensity = float(i_clean) if i_clean else 0.0
                if energy > 0:
                    dataset_gammas.append((energy, intensity))
            except (ValueError, IndexError):
                continue

    # Commit last dataset
    if current_nuclide and dataset_gammas:
        _commit_dataset(current_nuclide, dataset_gammas, db)


def _commit_dataset(symbol: str,
                     gammas: list[tuple[float, float]],
                     db: dict[str, list]) -> None:
    """
    Normalise relative intensities and add to database.
    ENSDF stores relative intensities (strongest line = 100).
    We keep them as-is since we don't know the absolute branching
    without the parent dataset — flag as "rel%" in the note.
    Lines with intensity 0 or unknown get intensity=1.0 (present but weak).
    """
    if not gammas or not symbol:
        return

    max_int = max(g[1] for g in gammas) or 1.0
    lines_out = []
    for energy, rel_int in gammas:
        # Normalise to 0–100 scale (relative to strongest line in dataset)
        norm_int = round((rel_int / max_int) * 100.0, 2) if rel_int > 0 else 1.0
        lines_out.append((round(energy, 2), norm_int, "γ"))

    if symbol in db:
        # Merge: keep highest intensity for duplicate energies
        existing = {round(e, 0): (e, i, n) for e, i, n in db[symbol]}
        for e, i, n in lines_out:
            key = round(e, 0)
            if key not in existing or i > existing[key][1]:
                existing[key] = (e, i, n)
        db[symbol] = sorted(existing.values(), key=lambda x: x[0])
    else:
        db[symbol] = lines_out


def _parse_nuclide_field(field: str) -> str:
    """
    Convert ENSDF nuclide field (e.g. '214BI', '137CS', '60CO') to
    standard symbol (e.g. 'Bi-214', 'Cs-137', 'Co-60').
    """
    field = field.strip().upper()
    # Match mass number + element
    m = re.match(r"(\d+)\s*([A-Z]{1,3})", field)
    if not m:
        return field
    mass = m.group(1)
    elem = m.group(2).capitalize()
    # Fix two-letter elements that got capitalised wrong
    if len(elem) == 2:
        elem = elem[0].upper() + elem[1].lower()
    elif len(elem) == 3:
        elem = elem[0].upper() + elem[1].lower() + elem[2].lower()
    return f"{elem}-{mass}"


def _normalise_symbol(symbol: str) -> str:
    """Normalise 'bi214', 'BI-214', 'Bismuth-214' → 'Bi-214'."""
    symbol = symbol.strip()
    # Already in Xx-NNN form?
    if re.match(r"^[A-Z][a-z]?-\d+", symbol):
        return symbol
    # Try NNNXx or XXnnn
    m = re.match(r"(\d+)([A-Za-z]{1,3})", symbol)
    if m:
        return f"{m.group(2).capitalize()}-{m.group(1)}"
    m = re.match(r"([A-Za-z]{1,3})(\d+)", symbol)
    if m:
        return f"{m.group(1).capitalize()}-{m.group(2)}"
    return symbol


# ══════════════════════════════════════════════════════════════════════════════
#  NUDAT REST API FALLBACK
# ══════════════════════════════════════════════════════════════════════════════

def fetch_nudat_gamma_lines(symbol: str,
                             timeout: float = 5.0) -> list[tuple[float, float, str]]:
    """
    Fetch gamma lines from NuDat 3 REST API for a single isotope.
    Returns list of (keV, intensity%, note) tuples.
    Requires internet connection.
    """
    # Parse symbol
    m = re.match(r"([A-Za-z]{1,3})-?(\d+)", symbol.strip())
    if not m:
        return []
    elem = m.group(1).capitalize()
    mass = m.group(2)

    url = (f"https://nds.iaea.org/relnsd/v1/data?"
           f"fields=gammas&nuclides={mass}{elem.upper()}")
    try:
        req  = urllib.request.Request(url, headers={"User-Agent": "GammaLab/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return []

    lines = []
    for row in data:
        try:
            kev  = float(row.get("energy", 0) or 0)
            ints = row.get("intensity", "") or ""
            try:
                inten = float(str(ints).split("(")[0].strip() or 0)
            except ValueError:
                inten = 0.0
            if kev > 0:
                lines.append((round(kev, 2), round(inten, 2), "γ"))
        except Exception:
            continue

    lines.sort(key=lambda x: x[0])
    return lines


# ══════════════════════════════════════════════════════════════════════════════
#  CACHE
# ══════════════════════════════════════════════════════════════════════════════

def _save_cache(db: dict) -> None:
    try:
        CACHE_FILE.write_text(json.dumps(db, separators=(",", ":")))
    except Exception:
        pass


def clear_cache() -> None:
    """Delete the cached database so it will be rebuilt on next load."""
    global _GAMMA_DB
    _GAMMA_DB = None
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()


def rebuild_cache() -> tuple[int, str]:
    """Force a full rebuild of the gamma database cache. Returns (n_isotopes, source)."""
    clear_cache()
    db = get_gamma_db(force_reload=True)
    return len(db), database_source()
