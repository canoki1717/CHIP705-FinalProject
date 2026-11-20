"""Download Allen Cell Types metadata and computed electrophysiology features.

Run from this directory:
    python 01_download_data.py

This script uses the public Allen Brain Atlas API. It saves the source tables
before creating a restricted mouse spiny/aspiny analysis cohort.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
API_URL = "https://api.brain-map.org/api/v2/data/query.json"


def fetch_allen_table(criteria: str, table_name: str) -> pd.DataFrame:
    """Fetch all rows for one Allen API query and return the msg table."""
    response = requests.get(
        API_URL,
        params={"criteria": criteria},
        headers={"User-Agent": "CHIP705-student-project/1.0"},
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()

    if payload.get("success") is False:
        raise RuntimeError(f"Allen API returned an error for {table_name}: {payload}")

    rows = payload.get("msg")
    if not isinstance(rows, list):
        raise RuntimeError(
            f"Unexpected Allen API response for {table_name}: expected a list in 'msg'."
        )
    return pd.DataFrame(rows)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    metadata_criteria = (
        "model::ApiCellTypesSpecimenDetail"
        ",rma::criteria,[donor__species$il'mus musculus']"
        ",rma::options[num_rows$eqall]"
    )
    ephys_criteria = (
        "model::EphysFeature"
        ",rma::criteria,specimen(ephys_result[failed$eqfalse])"
        ",rma::options[num_rows$eqall]"
    )

    print("Downloading Allen cell metadata...")
    metadata = fetch_allen_table(metadata_criteria, "mouse metadata")
    print(f"  Retrieved {len(metadata):,} metadata rows")

    print("Downloading computed electrophysiology features...")
    ephys = fetch_allen_table(ephys_criteria, "electrophysiology features")
    print(f"  Retrieved {len(ephys):,} feature rows")

    metadata_path = RAW_DIR / "allen_mouse_cell_metadata.csv"
    ephys_path = RAW_DIR / "allen_ephys_features_all_species.csv"
    metadata.to_csv(metadata_path, index=False)
    ephys.to_csv(ephys_path, index=False)

    if "specimen__id" not in metadata.columns:
        raise KeyError(
            "Expected specimen identifier 'specimen__id'; found: "
            f"{metadata.columns.tolist()}"
        )
    if "specimen_id" not in ephys.columns:
        raise KeyError(
            f"Expected specimen identifier 'specimen_id'; found: {ephys.columns.tolist()}"
        )
    if "tag__dendrite_type" not in metadata.columns:
        raise KeyError(
            "Expected dendrite label 'tag__dendrite_type'; found: "
            f"{metadata.columns.tolist()}"
        )

    metadata = metadata.rename(columns={"specimen__id": "specimen_id"})
    cohort = metadata.merge(ephys, on="specimen_id", how="inner", validate="one_to_one")
    cohort = cohort.loc[
        cohort["tag__dendrite_type"].astype(str).str.lower().isin(["spiny", "aspiny"])
    ].copy()
    cohort = cohort.rename(columns={"tag__dendrite_type": "dendrite_type"})

    analysis_path = DATA_DIR / "allen_mouse_spiny_aspiny_analysis.csv"
    cohort.to_csv(analysis_path, index=False)

    retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    counts = cohort["dendrite_type"].value_counts().to_dict()
    provenance = f"""# Data provenance

**Retrieved:** {retrieved_at}

**Source:** Allen Institute for Brain Science, Allen Cell Types Database.

**API endpoints:**

- Metadata: `{API_URL}?criteria={metadata_criteria}`
- Electrophysiology: `{API_URL}?criteria={ephys_criteria}`

**Rows retrieved:** {len(metadata):,} mouse metadata rows; {len(ephys):,} electrophysiology feature rows.

**Primary analysis cohort:** {len(cohort):,} mouse cells with a matching electrophysiology record and a `spiny` or `aspiny` dendrite label.

**Class counts:** {counts}

**Files:**

- `raw/allen_mouse_cell_metadata.csv`: source metadata table.
- `raw/allen_ephys_features_all_species.csv`: source electrophysiology feature table; filter to mouse during the metadata merge.
- `allen_mouse_spiny_aspiny_analysis.csv`: merged primary cohort before feature selection and missing-value handling.

**Documentation:** https://brain-map.org/support/documentation/cell-types-database-api
"""
    (DATA_DIR / "README.md").write_text(provenance, encoding="utf-8")

    print(f"Saved analysis cohort to: {analysis_path}")
    print(f"Class counts: {counts}")


if __name__ == "__main__":
    main()
