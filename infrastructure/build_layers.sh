#!/usr/bin/env bash
# =============================================================================
# build_layers.sh — Docker-free Lambda layer builder for macOS/Linux
#
# Builds four Lambda-compatible layer ZIPs using pip's cross-compilation
# flags (manylinux2014_x86_64 wheels → runs on Amazon Linux 2 Lambda runtime).
#
# Usage:
#   chmod +x infrastructure/build_layers.sh
#   ./infrastructure/build_layers.sh
#
# After running, set lambda_layers_built = true in terraform.tfvars and run:
#   cd infrastructure/terraform && terraform apply -var="lambda_layers_built=true"
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAYERS_DIR="$SCRIPT_DIR/layers"          # Layer ZIPs go HERE (matches Terraform)
ZIPS_DIR="$LAYERS_DIR/zips"             # Handler ZIPs go here (Terraform archive_file output)
WORK_DIR="$LAYERS_DIR/work"

# Python version that matches Lambda runtime (python3.12)
PY_VERSION="3.12"

# pip flags for cross-compilation (Linux x86_64, no source builds)
PIP_FLAGS="--platform manylinux2014_x86_64 --python-version $PY_VERSION --only-binary=:all: --upgrade"

echo "======================================================"
echo "  Trading Lambda Layer Builder (Docker-free)"
echo "  Target: python$PY_VERSION / manylinux2014_x86_64"
echo "======================================================"
echo ""

# Ensure output directories exist
mkdir -p "$LAYERS_DIR" "$ZIPS_DIR" "$WORK_DIR"

# ── Layer 1: NLP layer (~5 MB) ─────────────────────────────────────────────────
# Used by: trading-news-sentiment, trading-bedrock-sentiment-tool
#
# Two-pass approach because feedparser 6.x depends on sgmllib3k which only
# has a pure-Python source distribution (no manylinux wheel).
# - Pass 1: lxml (compiled, needs manylinux binary)
# - Pass 2: pure-Python packages (no platform restriction, all are py3-none-any)
echo ">>> Building trading-nlp-layer ..."
NLP_DIR="$WORK_DIR/trading-nlp-layer/python"
rm -rf "$WORK_DIR/trading-nlp-layer"
mkdir -p "$NLP_DIR"

# Compiled: lxml (needs manylinux wheel for Linux runtime)
pip install $PIP_FLAGS --target "$NLP_DIR" lxml

# Pure-Python: no platform restriction needed — wheels are universal
pip install --upgrade --target "$NLP_DIR" \
    "feedparser>=6.0" \
    sgmllib3k \
    vaderSentiment \
    requests \
    pytz \
    beautifulsoup4

NLP_ZIP="$LAYERS_DIR/trading-nlp-layer.zip"
rm -f "$NLP_ZIP"   # always start fresh — zip -r updates existing ZIPs otherwise
(cd "$WORK_DIR/trading-nlp-layer" && zip -r9q "$NLP_ZIP" python/)
echo "    → $NLP_ZIP  ($(du -sh "$NLP_ZIP" | cut -f1))"
echo ""

# ── Layer 2: Export layer (~3 MB) ─────────────────────────────────────────────
# Used by: trading-excel-export
# openpyxl + pytz are pure Python — no platform restriction needed.
echo ">>> Building trading-export-layer ..."
EXPORT_DIR="$WORK_DIR/trading-export-layer/python"
rm -rf "$WORK_DIR/trading-export-layer"
mkdir -p "$EXPORT_DIR"

pip install --upgrade --target "$EXPORT_DIR" openpyxl pytz

EXPORT_ZIP="$LAYERS_DIR/trading-export-layer.zip"
rm -f "$EXPORT_ZIP"
(cd "$WORK_DIR/trading-export-layer" && zip -r9q "$EXPORT_ZIP" python/)
echo "    → $EXPORT_ZIP  ($(du -sh "$EXPORT_ZIP" | cut -f1))"
echo ""

# ── Layer 3: Heavy layer (~160 MB unzipped, ~60 MB zipped) ───────────────────
# Used by: trading-stocks-signal, trading-options-analysis, trading-options-refresh,
#          trading-bedrock-technical-tool, trading-bedrock-options-tool
# NOTE: This approaches Lambda's 250 MB limit — deploy as a layer, not inline.
echo ">>> Building trading-heavy-layer (this may take 2-4 minutes)..."
HEAVY_DIR="$WORK_DIR/trading-heavy-layer/python"
rm -rf "$WORK_DIR/trading-heavy-layer"
mkdir -p "$HEAVY_DIR"

# Compiled packages — require manylinux binary wheels
# NOTE: scipy omitted intentionally — backend/utils/greeks.py has a try/except
# ImportError fallback to math.erfc (scipy-free Black-Scholes CDF).
pip install $PIP_FLAGS --target "$HEAVY_DIR" \
    numpy \
    pandas \
    yfinance \
    pytz \
    requests \
    urllib3

# Pure-Python packages — no platform restriction (no C extensions, no binary wheel needed)
# --no-deps: numpy + pandas are already installed above (manylinux); without --no-deps pip
# would "upgrade" them using the HOST machine's platform wheel (macOS ARM64), doubling the
# layer size with duplicate .so files that have different filenames.
pip install --no-deps --upgrade --target "$HEAVY_DIR" ta

# curl_cffi — has manylinux wheels on PyPI
pip install $PIP_FLAGS --target "$HEAVY_DIR" curl_cffi || {
    echo "    ⚠ curl_cffi wheel not found for manylinux2014, trying manylinux_2_28..."
    pip install --platform manylinux_2_28_x86_64 \
        --python-version "$PY_VERSION" \
        --only-binary=:all: --upgrade \
        --target "$HEAVY_DIR" curl_cffi || echo "    ⚠ curl_cffi skipped — options will use standard requests"
}

HEAVY_ZIP="$LAYERS_DIR/trading-heavy-layer.zip"
rm -f "$HEAVY_ZIP"
(cd "$WORK_DIR/trading-heavy-layer" && zip -r9q "$HEAVY_ZIP" python/)
HEAVY_SIZE=$(du -sh "$HEAVY_ZIP" | cut -f1)
echo "    → $HEAVY_ZIP  ($HEAVY_SIZE)"
echo ""

# ── Layer 4: Backend Python source layer (~200 KB) ────────────────────────────
# Packages the project's backend/ Python code + shared/dynamo_cache.py into a
# Lambda Layer so all 12 handlers can do:
#   from backend.data.options_fetcher import OptionsFetcher
#   import dynamo_cache
# without any sys.path manipulation.
# Lambda automatically adds /opt/python to sys.path, so the layer contents
# are importable as top-level packages.
echo ">>> Building trading-backend-layer (backend/ source + shared/) ..."
BACKEND_LAYER_DIR="$WORK_DIR/trading-backend-layer/python"
rm -rf "$WORK_DIR/trading-backend-layer"
mkdir -p "$BACKEND_LAYER_DIR"

# Copy the entire backend/ package
cp -r "$SCRIPT_DIR/../backend" "$BACKEND_LAYER_DIR/backend"

# Copy shared helper (dynamo_cache.py) as top-level module
cp "$SCRIPT_DIR/../lambdas/shared/dynamo_cache.py" "$BACKEND_LAYER_DIR/dynamo_cache.py"

# Remove local-dev cache dirs / pyc files to keep zip small
find "$BACKEND_LAYER_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$BACKEND_LAYER_DIR" -name "*.pyc" -delete 2>/dev/null || true
find "$BACKEND_LAYER_DIR" -name ".DS_Store" -delete 2>/dev/null || true

BACKEND_ZIP="$LAYERS_DIR/trading-backend-layer.zip"
rm -f "$BACKEND_ZIP"
(cd "$WORK_DIR/trading-backend-layer" && zip -r9q "$BACKEND_ZIP" python/)
BACKEND_SIZE=$(du -sh "$BACKEND_ZIP" | cut -f1)
echo "    → $BACKEND_ZIP  ($BACKEND_SIZE)"
echo ""

# ── Lambda handler ZIPs ────────────────────────────────────────────────────────
# Terraform's archive_file data sources auto-generate these, but this section
# pre-builds them for reference / local testing (not used by Terraform deploy).
echo ">>> Building Lambda handler ZIPs (for reference) ..."
LAMBDA_DIR="$SCRIPT_DIR/../lambdas"

for func_dir in "$LAMBDA_DIR"/trading_*/; do
    func_name=$(basename "$func_dir")
    zip_path="$ZIPS_DIR/${func_name}.zip"
    (cd "$LAMBDA_DIR" && zip -r9q "$zip_path" "$func_name/" shared/)
    echo "    → $zip_path"
done
echo ""

# ── Summary ───────────────────────────────────────────────────────────────────
echo "======================================================"
echo "  Build complete!"
echo ""
echo "  Layer ZIPs (used by Terraform):"
ls -lh "$LAYERS_DIR"/*.zip 2>/dev/null || echo "  (none found)"
echo ""
echo "  Handler ZIPs (pre-built reference):"
ls -lh "$ZIPS_DIR"/trading_*.zip 2>/dev/null || echo "  (none found)"
echo ""
echo "  Next steps:"
echo "  1. Verify heavy-layer size < 60 MB zipped"
echo "  2. Edit infrastructure/terraform/terraform.tfvars:"
echo "       lambda_layers_built = true"
echo "  3. cd infrastructure/terraform && terraform init && terraform apply"
echo "======================================================"

# Clean up work directory (keep ZIPs)
rm -rf "$WORK_DIR"
