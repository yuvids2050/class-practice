"""
KPI aggregation, number formatting, and statistical-summary helpers shared
across pages.
"""
import pandas as pd


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def fmt_currency(x) -> str:
    if pd.isna(x):
        return "N/A"
    return f"${x:,.0f}"


def fmt_pct(x, decimals: int = 2) -> str:
    if pd.isna(x):
        return "N/A"
    return f"{x:.{decimals}f}%"


def fmt_number(x) -> str:
    if pd.isna(x):
        return "N/A"
    return f"{x:,.0f}"


# ---------------------------------------------------------------------------
# Portfolio-level KPIs
# ---------------------------------------------------------------------------

def portfolio_kpis(df: pd.DataFrame) -> dict:
    total = len(df)
    defaults = int(df["TARGET"].sum()) if "TARGET" in df.columns else None
    default_rate = (defaults / total * 100) if (total and defaults is not None) else None
    return {
        "total_customers": df["SK_ID_CURR"].nunique() if "SK_ID_CURR" in df.columns else total,
        "total_applications": total,
        "default_customers": defaults,
        "non_default_customers": (total - defaults) if defaults is not None else None,
        "default_rate": default_rate,
        "total_credit": df["AMT_CREDIT"].sum() if "AMT_CREDIT" in df.columns else None,
        "avg_credit": df["AMT_CREDIT"].mean() if "AMT_CREDIT" in df.columns else None,
        "median_credit": df["AMT_CREDIT"].median() if "AMT_CREDIT" in df.columns else None,
        "avg_income": df["AMT_INCOME_TOTAL"].mean() if "AMT_INCOME_TOTAL" in df.columns else None,
        "median_income": df["AMT_INCOME_TOTAL"].median() if "AMT_INCOME_TOTAL" in df.columns else None,
        "avg_annuity": df["AMT_ANNUITY"].mean() if "AMT_ANNUITY" in df.columns else None,
        "avg_goods_price": df["AMT_GOODS_PRICE"].mean() if "AMT_GOODS_PRICE" in df.columns else None,
    }


def default_rate_by(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Count + default rate breakdown by any category — keeps the count vs
    rate distinction explicit (Page 11 requirement)."""
    g = df.dropna(subset=[group_col]).groupby(group_col, observed=True).agg(
        Customers=("TARGET", "size"),
        Defaults=("TARGET", "sum"),
    ).reset_index()
    g["Default Rate %"] = (g["Defaults"] / g["Customers"] * 100).round(2)
    return g.sort_values("Customers", ascending=False)


def top_bottom_by_default_rate(df: pd.DataFrame, group_col: str, min_count: int = 5):
    g = df.dropna(subset=[group_col]).groupby(group_col, observed=True)["TARGET"].agg(["mean", "count"])
    g = g[g["count"] >= min_count]
    if g.empty:
        return None, None
    return g["mean"].idxmax(), g["mean"].idxmin()


def correlation_with_target(df: pd.DataFrame, columns: list) -> pd.Series:
    cols = [c for c in columns if c in df.columns]
    corr = df[cols].corr(numeric_only=True)
    if "TARGET" not in corr.columns:
        return pd.Series(dtype=float)
    return corr["TARGET"].drop("TARGET", errors="ignore").sort_values(ascending=False)


# ---------------------------------------------------------------------------
# Descriptive statistics (Section 31: mean/median/mode/std/min/max/percentiles/IQR)
# ---------------------------------------------------------------------------

def descriptive_stats(series: pd.Series) -> dict:
    s = series.dropna()
    if s.empty:
        return {}
    return {
        "Mean": round(s.mean(), 2),
        "Median": round(s.median(), 2),
        "Mode": round(s.mode().iloc[0], 2) if not s.mode().empty else None,
        "Std Dev": round(s.std(), 2),
        "Minimum": round(s.min(), 2),
        "Maximum": round(s.max(), 2),
        "25th Percentile": round(s.quantile(0.25), 2),
        "75th Percentile": round(s.quantile(0.75), 2),
        "IQR": round(s.quantile(0.75) - s.quantile(0.25), 2),
    }
