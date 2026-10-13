#!/usr/bin/env bash
set -euo pipefail
python scripts/download_model.py
exec streamlit run app.py
