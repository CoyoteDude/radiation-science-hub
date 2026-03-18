"""
download_ensdf.py — Downloads ENSDF files at runtime if not present
"""
import urllib.request
import zipfile
import os
from pathlib import Path

ENSDF_DIR = Path(__file__).parent / "ensdf_260301"
ENSDF_URL = "https://www.nndc.bnl.gov/ensdf/ensdf/download/ensdf.zip"

def ensure_ensdf():
    ens_files = list(ENSDF_DIR.glob("ensdf.*"))
    if ens_files:
        return  # Already have files
    
    ENSDF_DIR.mkdir(exist_ok=True)
    zip_path = ENSDF_DIR / "ensdf.zip"
    
    print("Downloading ENSDF database (~265MB), please wait...")
    urllib.request.urlretrieve(ENSDF_URL, zip_path)
    
    print("Extracting...")
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(ENSDF_DIR)
    
    zip_path.unlink()
    print("ENSDF database ready.")

if __name__ == "__main__":
    ensure_ensdf()
