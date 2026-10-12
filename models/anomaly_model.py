"""
TerraWatch AI - NDVI anomaly screening
Input: a CSV containing latitude, longitude, date, ndvi
Output: data/results.csv

This is a screening baseline, not a validated crop-damage classifier.
"""

from pathlib import Path
import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
OUTPUT_CSV = DATA_DIR / "results.csv"

REQUIRED_COLUMNS = {"latitude", "longitude", "date", "ndvi"}


def process_ndvi(input_csv: str | Path, output_csv: str | Path = OUTPUT_CSV) -> pd.DataFrame:
    """Load NDVI observations, calculate a location-specific baseline, and save flags."""
    input_csv = Path(input_csv)
    output_csv = Path(output_csv)

    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    df = pd.read_csv(input_csv)
    df.columns = [str(c).strip().lower() for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            "Input CSV is missing columns: "
            + ", ".join(sorted(missing))
            + ". Required: latitude, longitude, date, ndvi"
        )

    for col in ("latitude", "longitude", "ndvi"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True).dt.tz_localize(None)
    df = df.dropna(subset=["latitude", "longitude", "date", "ndvi"]).copy()

    if df.empty:
        raise ValueError("No valid observations remain after cleaning the input CSV.")

    # NDVI is generally within [-1, 1]; out-of-range values are invalid for this workflow.
    df = df[df["ndvi"].between(-1.0, 1.0)].copy()
    if df.empty:
        raise ValueError("No NDVI values in the valid range [-1, 1].")

    # Stable per-pixel key using coordinates rounded to 4 decimals (~11 m latitude).
    # For gridded products, use the native pixel/grid ID where available.
    df["location_key"] = (
        df["latitude"].round(4).astype(str)
        + "_"
        + df["longitude"].round(4).astype(str)
    )

    df = df.sort_values(["location_key", "date"]).reset_index(drop=True)

    # Use prior observations only for the baseline to reduce leakage from the current value.
    grouped = df.groupby("location_key", sort=False)["ndvi"]
    df["baseline_ndvi"] = grouped.transform(
        lambda s: s.shift(1).expanding(min_periods=3).median()
    )
    df["baseline_std"] = grouped.transform(
        lambda s: s.shift(1).expanding(min_periods=3).std()
    )

    # For early observations with insufficient history, use the location's overall median
    # as a fallback and clearly mark the reason as limited historical context.
    overall_median = df.groupby("location_key")["ndvi"].transform("median")
    has_history = df["baseline_ndvi"].notna()
    df["baseline_ndvi"] = df["baseline_ndvi"].fillna(overall_median)

    df["ndvi_change"] = df["ndvi"] - df["baseline_ndvi"]
    df["ndvi_change_pct"] = np.where(
        df["baseline_ndvi"].abs() > 1e-6,
        100.0 * df["ndvi_change"] / df["baseline_ndvi"].abs(),
        np.nan,
    )

    # Conservative rule-based screening threshold; tune only after validation.
    # A drop of at least 0.15 NDVI is flagged for review.
    df["review_flag"] = df["ndvi_change"] <= -0.15

    df["review_reason"] = np.select(
        [
            ~has_history,
            df["review_flag"],
            df["ndvi_change"] >= 0.15,
        ],
        [
            "Limited prior history; interpret baseline cautiously",
            "NDVI is at least 0.15 below the estimated baseline; review required",
            "NDVI is at least 0.15 above the estimated baseline",
        ],
        default="No large NDVI deviation detected by this screening rule",
    )

    df["data_quality"] = "valid_numeric_ndvi"
    if "qa" in df.columns:
        df["data_quality"] = np.where(
            df["qa"].astype(str).str.strip().ne(""),
            "QA field supplied; product-specific QA filtering still required",
            "QA missing; quality screening incomplete",
        )
    else:
        df["data_quality"] = "QA field absent; quality screening incomplete"

    df["screening_method"] = "historical_median_rule_v1"
    df["review_flag"] = df["review_flag"].astype(bool)

    output_columns = [
        "latitude",
        "longitude",
        "date",
        "ndvi",
        "baseline_ndvi",
        "ndvi_change",
        "ndvi_change_pct",
        "review_flag",
        "review_reason",
        "data_quality",
        "screening_method",
    ]
    result = df[output_columns].copy()

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_csv, index=False, date_format="%Y-%m-%d")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run TerraWatch NDVI anomaly screening.")
    parser.add_argument(
        "--input",
        default=str(DATA_DIR / "ndvi_input.csv"),
        help="Input CSV with latitude,longitude,date,ndvi columns",
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_CSV),
        help="Output results CSV path",
    )
    args = parser.parse_args()

    output = process_ndvi(args.input, args.output)
    print(f"Saved {len(output)} rows to: {args.output}")
    print(f"Rows flagged for review: {int(output['review_flag'].sum())}")
