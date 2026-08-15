from pathlib import Path

import pandas as pd
import requests


API_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

OUTPUT_FILE = Path("data/catalogs/targets.csv")


QUERY = """
SELECT
    rowid,
    kepid,
    tce_plnt_num,
    tce_period,
    tce_time0bk,
    tce_duration,
    av_training_set
FROM q1_q17_dr24_tce
WHERE av_training_set IN ('PC', 'AFP', 'NTP')
"""


def download_catalog():

    print("Downloading Kepler Q1-Q17 DR24 TCE catalog...")

    response = requests.get(
        API_URL,
        params={
            "query": QUERY,
            "format": "csv",
        },
        timeout=120,
    )

    response.raise_for_status()

    from io import StringIO

    df = pd.read_csv(
        StringIO(response.text)
    )

    print(
        f"Downloaded {len(df)} labeled TCEs."
    )

    return df


def build_targets(df):

    print("\nBuilding ExoVision target catalog...")

    # --------------------------------------------------
    # Clean labels
    # --------------------------------------------------

    df["av_training_set"] = (
        df["av_training_set"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # PC = planet
    # AFP/NTP = non-planet
    df["label"] = (
        df["av_training_set"] == "PC"
    ).astype(int)

    # --------------------------------------------------
    # Create target identifier
    # --------------------------------------------------

    df["target"] = (
        "KIC_" +
        df["kepid"].astype(int).astype(str)
    )

    # --------------------------------------------------
    # Rename useful TCE information
    # --------------------------------------------------

    targets = df[
        [
            "target",
            "kepid",
            "tce_plnt_num",
            "label",
            "tce_period",
            "tce_time0bk",
            "tce_duration",
            "av_training_set",
        ]
    ].copy()

    targets = targets.rename(
        columns={
            "tce_period": "period",
            "tce_time0bk": "epoch",
            "tce_duration": "duration_hours",
            "av_training_set": "original_label",
        }
    )

    # --------------------------------------------------
    # Validate
    # --------------------------------------------------

    targets = targets.dropna(
        subset=[
            "target",
            "period",
            "epoch",
            "duration_hours",
        ]
    )

    targets = targets[
        targets["period"] > 0
    ]

    targets = targets[
        targets["duration_hours"] > 0
    ]

    targets = targets.drop_duplicates(
        subset=["target", "tce_plnt_num"]
    )

    return targets


def main():

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    raw = download_catalog()

    targets = build_targets(raw)

    print("\n================================")
    print("EXOVISION CATALOG")
    print("================================")

    print(
        f"\nTotal targets: {len(targets)}"
    )

    print("\nOriginal labels:")
    print(
        targets["original_label"]
        .value_counts()
        .sort_index()
    )

    print("\nBinary labels:")
    print(
        targets["label"]
        .value_counts()
        .sort_index()
    )

    print("\nExample rows:")
    print(
        targets.head()
    )

    targets.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"\nSaved to:\n{OUTPUT_FILE}"
    )

    print("\nCatalog generation successful!")


if __name__ == "__main__":
    main()