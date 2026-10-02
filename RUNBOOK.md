# CompostMitra Runbook: Offline Operations & M1 Gate Protocol

This runbook provides complete operational procedures for deploying, validating, and exporting **CompostMitra** in zero-network offline environments across Windows, Linux, and Docker.

---

## 1. Offline Setup & Execution Instructions

CompostMitra is architected to operate with zero runtime network access. All dependencies and datasets are vendored or cached locally.

### 1.1 Linux Setup (Ubuntu / Debian / RHEL / Fedora)

```bash
# Ensure Python 3.11 is installed
python3.11 --version

# Create local virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install from frozen requirements (or local wheel cache if fully offline)
pip install --no-index --find-links=wheels/ -r requirements.txt || pip install -r requirements.txt

# Launch application
streamlit run app.py --server.headless true --server.port 8501
```

### 1.2 Windows Setup (PowerShell / Command Prompt)

```powershell
# Ensure Python 3.11 is available via the Python launcher
py -3.11 --version

# Create virtual environment
py -3.11 -m venv .venv
.venv\Scripts\activate

# Install dependencies offline
pip install --no-index --find-links=wheels\ -r requirements.txt || pip install -r requirements.txt

# Launch application
streamlit run app.py
```

### 1.3 Docker Offline Deployment

CompostMitra can be packaged into an isolated OCI image with an image budget under 800MB:

```bash
# Build the production container image
docker build -t compostmitra:s1 .

# Run container with strict zero-network isolation (--network none)
docker run -d \
  --name compostmitra-offline \
  --network none \
  -p 8501:8501 \
  compostmitra:s1

# Verify container health check
curl -sf http://localhost:8501/_stcore/health
```

---

## 2. Two-Green-Runs M1 Gate Checklist

Before signing off on the M1 Foundation Milestone or submitting changes to the repository, execute the full validation protocol twice consecutively. Both runs must pass with zero failures.

| Check Item | Validation Command | Expected Outcome | Run 1 | Run 2 |
| :--- | :--- | :--- | :---: | :---: |
| **1. Cornell 30:1 Blend** | `python scripts/blender.py --cornell-check` | `CN=30.x PASS (28-32)` | [ ] PASS | [ ] PASS |
| **2. Clean Data Contract** | `python scripts/datacheck.py --strict data/clean/*.csv data/ingredients.csv data/plants.csv` | Exit code 0, 0 violations | [ ] PASS | [ ] PASS |
| **3. Negative Fixtures** | `python scripts/datacheck.py --strict tests/fixtures/bad/` | Exit code != 0, exactly 6 bad files rejected | [ ] PASS | [ ] PASS |
| **4. Unit Tests** | `python -m pytest tests/ -q` | 20+ unit tests passing | [ ] PASS | [ ] PASS |
| **5. Wording Guard** | `! grep -rEw "proves|causes" --include="*.py" .` | Exit code 0 (zero hits) | [ ] PASS | [ ] PASS |
| **6. Footnote Check** | `python scripts/check_tier_footnotes.py docs/` | Exit code 0, all figures footnoted | [ ] PASS | [ ] PASS |
| **7. Holdout Label Check** | `python scripts/check_holdout_labels.py docs/` | Exit code 0, all metrics labeled | [ ] PASS | [ ] PASS |
| **8. Shell Cold Load** | `bash scripts/serve_and_check.sh` | Health endpoint OK, cold load < 3.0s | [ ] PASS | [ ] PASS |

---

## 3. USB FAT32 Export Protocol

For live viva evaluation or disaster recovery where local workstations fail, an offline backup bundle can be synchronized directly to a FAT32-formatted USB flash drive.

### 3.1 Filename Compatibility Rules for FAT32
- Maximum filename length: 255 characters (no deep path nesting).
- Reserved characters forbidden: `*`, `?`, `<`, `>`, `:`, `"`, `/`, `\`, `|`.
- File size limit: Maximum 4.0 GB per individual file.

### 3.2 Export Command

Run the following command to generate the standardized USB backup bundle:

```bash
# 1. Create target backup directory
mkdir -p usb_backup/docs usb_backup/data usb_backup/reports

# 2. Synchronize essential documentation and schemas
cp README.md RUNBOOK.md docs/ARCH_LOCKED.md docs/DATA_CONTRACT_v3.1.md docs/ADRS.md usb_backup/docs/

# 3. Synchronize clean datasets and reference tables
cp data/ingredients.csv data/plants.csv data/schema_map.csv usb_backup/data/
cp data/clean/*.csv usb_backup/data/

# 4. Generate CycloneDX Software Bill of Materials (SBOM) if tool is available
if command -v cyclonedx-py &> /dev/null; then
  cyclonedx-py requirements -i requirements.txt -o usb_backup/reports/sbom.cyclonedx.json
fi

# 5. Export USB bundle to FAT32 drive (e.g. mounted at /media/usb or D:\)
# Linux:
# rsync -av --modify-window=1 --delete usb_backup/ /media/$USER/COMPOST_USB/
# Windows:
# robocopy usb_backup D:\COMPOST_USB /MIR /FFT /Z
```

---

## 4. Emergency Troubleshooting & Fallback Procedures

1. **Port 8501 Already in Use:**
   ```bash
   # Terminate existing Streamlit processes
   pkill -f "streamlit run" || kill $(lsof -t -i:8501)
   ```
2. **Key-Casing Assertion Failure:**
   Run `python scripts/check_keys.py mock/recipe_response.json mock/predict_response.json` to pinpoint uppercase or camelCase keys.
3. **Out-of-Range Datacheck Error:**
   Examine quarantined rows in `data/quarantine/` and verify unit conversion factors against `REAL_RANGES.md`.

---

> **Tier Footnote:** `T1 REAL | LIT calc | D1 proxy`  
> **Model Disclaimer:** Supplement, builds soil — not fertilizer replacement. Model estimates reflect statistical associations on historical proxy data (sanity check, not proof).
