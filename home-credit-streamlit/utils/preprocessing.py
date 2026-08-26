"""
Preprocessing utilities: data-quality summaries, missing-value analysis,
duplicate checks, invalid-value cleanup, and outlier detection (IQR-based).

No modeling logic lives here — only the cleaning / explanation utilities
used by the "Data Quality", "Missing Value", and "Outlier" pages, plus the
one-time cleanup applied before feature engineering.
"""
import numpy as np
import pandas as pd

# DAYS_EMPLOYED uses 365243 as a placeholder for "not currently employed"
# (mostly pensioners / unemployed). Left uncleaned, converting it to years
# would produce a customer "employed" for ~1000 years.
DAYS_EMPLOYED_ANOMALY = 365243


def clean_application_data(df: pd.DataFrame) -> pd.DataFrame:
    """Fix known invalid values in application_train.csv before feature engineering."""
    df = df.copy()

    if "DAYS_EMPLOYED" in df.columns:
        df["DAYS_EMPLOYED"] = df["DAYS_EMPLOYED"].replace(DAYS_EMPLOYED_ANOMALY, np.nan)

    # CODE_GENDER occasionally contains 'XNA' in the full dataset — treat as missing
    if "CODE_GENDER" in df.columns:
        df["CODE_GENDER"] = df["CODE_GENDER"].replace("XNA", np.nan)

    # AMT_INCOME_TOTAL / AMT_CREDIT / AMT_ANNUITY should never be negative or zero
    for col in ["AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY", "AMT_GOODS_PRICE"]:
        if col in df.columns:
            df.loc[df[col] <= 0, col] = np.nan

    return df


# ---------------------------------------------------------------------------
# Data quality / dataset-level summaries (Page 2)
# ---------------------------------------------------------------------------

def dataset_overview(df: pd.DataFrame) -> dict:
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns
    return {
        "rows": len(df),
        "columns": df.shape[1],
        "numeric_columns": len(numeric_cols),
        "categorical_columns": len(categorical_cols),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024 ** 2),
        "unique_customers": df["SK_ID_CURR"].nunique() if "SK_ID_CURR" in df.columns else None,
    }


def column_profile(df: pd.DataFrame) -> pd.DataFrame:
    """One row per column: dtype, missing count/%, unique values, and
    min/max/mean/median for numeric columns."""
    rows = []
    n = len(df)
    for col in df.columns:
        s = df[col]
        missing = int(s.isna().sum())
        row = {
            "Column Name": col,
            "Data Type": str(s.dtype),
            "Missing Count": missing,
            "Missing %": round(missing / n * 100, 2) if n else 0,
            "Unique Values": int(s.nunique()),
        }
        if pd.api.types.is_numeric_dtype(s):
            row["Minimum"] = s.min()
            row["Maximum"] = s.max()
            row["Mean"] = round(s.mean(), 2) if s.notna().any() else None
            row["Median"] = round(s.median(), 2) if s.notna().any() else None
        else:
            row["Minimum"] = None
            row["Maximum"] = None
            row["Mean"] = None
            row["Median"] = None
        rows.append(row)
    return pd.DataFrame(rows)


def duplicate_summary(df: pd.DataFrame, id_col: str = "SK_ID_CURR") -> dict:
    return {
        "full_row_duplicates": int(df.duplicated().sum()),
        "duplicate_ids": int(df[id_col].duplicated().sum()) if id_col in df.columns else None,
        "id_is_unique": bool(df[id_col].is_unique) if id_col in df.columns else None,
    }


# ---------------------------------------------------------------------------
# Missing-value analysis (Page 3)
# ---------------------------------------------------------------------------

def missing_value_summary(df: pd.DataFrame) -> pd.DataFrame:
    missing_count = df.isna().sum()
    missing_pct = (missing_count / len(df) * 100).round(2)
    dtypes = df.dtypes.astype(str)
    summary = pd.DataFrame({
        "Column": df.columns,
        "Missing Count": missing_count.values,
        "Missing %": missing_pct.values,
        "Data Type": dtypes.values,
    })
    summary = summary[summary["Missing Count"] > 0].sort_values("Missing Count", ascending=False)
    return summary.reset_index(drop=True)


def missing_bucket(pct: float) -> str:
    if pct <= 5:
        return "0-5% Missing"
    if pct <= 20:
        return "5-20% Missing"
    if pct <= 40:
        return "20-40% Missing"
    if pct <= 60:
        return "40-60% Missing"
    return "60%+ Missing"


def suggest_treatment(missing_pct: float, dtype: str) -> str:
    """Rule-of-thumb missing-value treatment with a stated reason."""
    if missing_pct > 60:
        return "Drop column — too sparse to reliably impute"
    if missing_pct > 40:
        return "Retain + missing indicator — high missingness may itself be informative"
    if "float" in dtype or "int" in dtype:
        return "Fill with median — robust to skew/outliers"
    return "Fill with mode / 'Unknown' — low-cardinality categorical"


# ---------------------------------------------------------------------------
# Outlier analysis (Page 4) — IQR method
# ---------------------------------------------------------------------------

def iqr_bounds(series: pd.Series, k: float = 1.5) -> tuple:
    s = series.dropna()
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    return q1 - k * iqr, q3 + k * iqr


def outlier_summary(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    rows = []
    for col in columns:
        if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
            continue
        s = df[col].dropna()
        if s.empty:
            continue
        lower, upper = iqr_bounds(s)
        outliers = s[(s < lower) | (s > upper)]
        rows.append({
            "Column": col,
            "Q1": round(s.quantile(0.25), 2),
            "Q3": round(s.quantile(0.75), 2),
            "IQR": round(s.quantile(0.75) - s.quantile(0.25), 2),
            "Lower Bound": round(lower, 2),
            "Upper Bound": round(upper, 2),
            "Outlier Count": len(outliers),
            "Outlier %": round(len(outliers) / len(s) * 100, 2),
        })
    return pd.DataFrame(rows)
