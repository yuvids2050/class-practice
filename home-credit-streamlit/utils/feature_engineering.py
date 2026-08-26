"""
Feature engineering for the Home Credit dashboard.

Two kinds of features are built here:

1. Application-level features (add_application_features) — derived directly
   from application_train.csv: ages, ratios, bands.

2. Customer-level aggregates (aggregate_* functions) — one row per
   SK_ID_CURR, summarizing each related table (bureau, bureau_balance,
   previous_application, POS_CASH_balance, installments_payments,
   credit_card_balance) so they can be joined back onto the application
   table for segmentation / executive pages.
"""
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 1. Application-level features
# ---------------------------------------------------------------------------

def add_application_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # AGE_YEARS
    if "DAYS_BIRTH" in df.columns:
        df["AGE_YEARS"] = (df["DAYS_BIRTH"].abs() / 365).round(1)
        df["AGE_GROUP"] = pd.cut(
            df["AGE_YEARS"], bins=[20, 30, 40, 50, 60, 100],
            labels=["20-30", "31-40", "41-50", "51-60", "60+"],
        )

    # EMPLOYMENT_YEARS (DAYS_EMPLOYED anomaly must already be cleaned to NaN)
    if "DAYS_EMPLOYED" in df.columns:
        df["EMPLOYMENT_YEARS"] = (df["DAYS_EMPLOYED"].abs() / 365).round(1)
        df["EMPLOYMENT_GROUP"] = employment_group(df["EMPLOYMENT_YEARS"])

    # INCOME_GROUP — quantile based (Very Low..Very High)
    if "AMT_INCOME_TOTAL" in df.columns:
        df["INCOME_GROUP"] = quantile_group(df["AMT_INCOME_TOTAL"])
        df["INCOME_PERCENTILE"] = (df["AMT_INCOME_TOTAL"].rank(pct=True) * 100).round(1)

    # INCOME_PER_FAMILY_MEMBER / INCOME_PER_CHILD
    if {"AMT_INCOME_TOTAL", "CNT_FAM_MEMBERS"}.issubset(df.columns):
        df["INCOME_PER_FAMILY_MEMBER"] = (df["AMT_INCOME_TOTAL"] / df["CNT_FAM_MEMBERS"].replace(0, np.nan)).round(2)
    if {"AMT_INCOME_TOTAL", "CNT_CHILDREN"}.issubset(df.columns):
        df["INCOME_PER_CHILD"] = (df["AMT_INCOME_TOTAL"] / df["CNT_CHILDREN"].replace(0, np.nan)).round(2)

    # Affordability ratios
    if {"AMT_CREDIT", "AMT_INCOME_TOTAL"}.issubset(df.columns):
        df["CREDIT_TO_INCOME"] = (df["AMT_CREDIT"] / df["AMT_INCOME_TOTAL"]).round(2)
    if {"AMT_ANNUITY", "AMT_INCOME_TOTAL"}.issubset(df.columns):
        df["ANNUITY_TO_INCOME"] = (df["AMT_ANNUITY"] / df["AMT_INCOME_TOTAL"]).round(3)
    if {"AMT_GOODS_PRICE", "AMT_INCOME_TOTAL"}.issubset(df.columns):
        df["GOODS_TO_INCOME"] = (df["AMT_GOODS_PRICE"] / df["AMT_INCOME_TOTAL"]).round(2)
    if {"AMT_CREDIT", "AMT_GOODS_PRICE"}.issubset(df.columns):
        df["CREDIT_TO_GOODS"] = (df["AMT_CREDIT"] / df["AMT_GOODS_PRICE"]).round(2)

    # Bands for affordability / EDA
    if "AMT_CREDIT" in df.columns:
        df["CREDIT_BAND"] = pd.cut(
            df["AMT_CREDIT"], bins=[-1, 100_000, 300_000, 500_000, 700_000, 1_000_000, np.inf],
            labels=["Below 100K", "100K-300K", "300K-500K", "500K-700K", "700K-1M", "Above 1M"],
        )
    if "CREDIT_TO_INCOME" in df.columns:
        df["CREDIT_TO_INCOME_BAND"] = pd.cut(
            df["CREDIT_TO_INCOME"], bins=[-np.inf, 2, 4, 6, np.inf],
            labels=["Low (<2)", "Moderate (2-4)", "High (4-6)", "Very High (>6)"],
        )
    if "ANNUITY_TO_INCOME" in df.columns:
        df["ANNUITY_TO_INCOME_BAND"] = pd.cut(
            df["ANNUITY_TO_INCOME"], bins=[-np.inf, 0.10, 0.20, 0.30, np.inf],
            labels=["Low", "Medium", "High", "Very High"],
        )

    if "TARGET" in df.columns:
        df["REPAYMENT_STATUS"] = df["TARGET"].map({0: "Repaid", 1: "Defaulted"})

    return df.copy()


def employment_group(years: pd.Series) -> pd.Series:
    bins = [-0.01, 1, 3, 5, 10, 20, 1000]
    labels = ["<1 Year", "1-3 Years", "3-5 Years", "5-10 Years", "10-20 Years", "20+ Years"]
    return pd.cut(years, bins=bins, labels=labels)


def quantile_group(series: pd.Series, labels=("Very Low", "Low", "Middle", "High", "Very High")) -> pd.Series:
    try:
        return pd.qcut(series.rank(method="first"), q=5, labels=list(labels))
    except ValueError:
        return pd.Series([np.nan] * len(series), index=series.index)


# ---------------------------------------------------------------------------
# 2. Bureau credit history aggregates (Page 13)
# ---------------------------------------------------------------------------

def aggregate_bureau_features(bureau: pd.DataFrame) -> pd.DataFrame:
    g = bureau.groupby("SK_ID_CURR")
    agg = g.agg(
        BUREAU_ACCOUNT_COUNT=("SK_ID_BUREAU", "count"),
        TOTAL_BUREAU_CREDIT=("AMT_CREDIT_SUM", "sum"),
        AVG_BUREAU_CREDIT=("AMT_CREDIT_SUM", "mean"),
        TOTAL_BUREAU_DEBT=("AMT_CREDIT_SUM_DEBT", "sum"),
        TOTAL_BUREAU_OVERDUE=("AMT_CREDIT_SUM_OVERDUE", "sum"),
        MAX_BUREAU_OVERDUE=("AMT_CREDIT_MAX_OVERDUE", "max"),
    ).reset_index()

    active_counts = bureau[bureau["CREDIT_ACTIVE"] == "Active"].groupby("SK_ID_CURR").size()
    closed_counts = bureau[bureau["CREDIT_ACTIVE"] == "Closed"].groupby("SK_ID_CURR").size()
    agg["ACTIVE_BUREAU_COUNT"] = agg["SK_ID_CURR"].map(active_counts).fillna(0).astype(int)
    agg["CLOSED_BUREAU_COUNT"] = agg["SK_ID_CURR"].map(closed_counts).fillna(0).astype(int)

    return agg


# ---------------------------------------------------------------------------
# 3. Bureau balance aggregates (Page 14) — joins through bureau to get SK_ID_CURR
# ---------------------------------------------------------------------------

DELINQUENCY_STATUSES = {"1", "2", "3", "4", "5"}  # DPD buckets; 'C'=closed, 'X'=unknown, '0'=no DPD


def aggregate_bureau_balance_features(bureau_balance: pd.DataFrame, bureau: pd.DataFrame) -> pd.DataFrame:
    id_map = bureau[["SK_ID_BUREAU", "SK_ID_CURR"]].drop_duplicates()
    bb = bureau_balance.merge(id_map, on="SK_ID_BUREAU", how="inner")

    bb["IS_DELINQUENT"] = bb["STATUS"].isin(DELINQUENCY_STATUSES)
    bb["IS_CLOSED"] = bb["STATUS"] == "C"
    bb["DELINQUENCY_LEVEL"] = bb["STATUS"].apply(lambda s: int(s) if s in DELINQUENCY_STATUSES else 0)

    g = bb.groupby("SK_ID_CURR")
    agg = g.agg(
        BUREAU_BALANCE_MONTHS=("MONTHS_BALANCE", "count"),
        MONTHS_WITH_DELINQUENCY=("IS_DELINQUENT", "sum"),
        MAX_DELINQUENCY_LEVEL=("DELINQUENCY_LEVEL", "max"),
        CLOSED_MONTHS_COUNT=("IS_CLOSED", "sum"),
    ).reset_index()
    agg["ACTIVE_MONTHS_COUNT"] = agg["BUREAU_BALANCE_MONTHS"] - agg["CLOSED_MONTHS_COUNT"]
    return agg


# ---------------------------------------------------------------------------
# 4. Previous application aggregates (Page 15)
# ---------------------------------------------------------------------------

def aggregate_previous_application_features(prev: pd.DataFrame) -> pd.DataFrame:
    g = prev.groupby("SK_ID_CURR")
    agg = g.agg(
        PREVIOUS_APPLICATION_COUNT=("SK_ID_PREV", "count"),
        AVG_PREVIOUS_CREDIT=("AMT_CREDIT", "mean"),
        MAX_PREVIOUS_CREDIT=("AMT_CREDIT", "max"),
    ).reset_index()

    approved = prev[prev["NAME_CONTRACT_STATUS"] == "Approved"].groupby("SK_ID_CURR").size()
    refused = prev[prev["NAME_CONTRACT_STATUS"] == "Refused"].groupby("SK_ID_CURR").size()
    agg["PREVIOUS_APPROVED_COUNT"] = agg["SK_ID_CURR"].map(approved).fillna(0).astype(int)
    agg["PREVIOUS_REFUSED_COUNT"] = agg["SK_ID_CURR"].map(refused).fillna(0).astype(int)
    agg["PREVIOUS_APPROVAL_RATE"] = (agg["PREVIOUS_APPROVED_COUNT"] / agg["PREVIOUS_APPLICATION_COUNT"] * 100).round(2)
    return agg


# ---------------------------------------------------------------------------
# 5. POS/CASH balance aggregates (Page 16)
# ---------------------------------------------------------------------------

def aggregate_pos_cash_features(pos: pd.DataFrame) -> pd.DataFrame:
    g = pos.groupby("SK_ID_CURR")
    agg = g.agg(
        AVG_DPD=("SK_DPD", "mean"),
        MAX_DPD=("SK_DPD", "max"),
        AVG_INSTALMENTS_REMAINING=("CNT_INSTALMENT_FUTURE", "mean"),
    ).reset_index()
    agg["TOTAL_DPD_EVENTS"] = agg["SK_ID_CURR"].map(pos[pos["SK_DPD"] > 0].groupby("SK_ID_CURR").size()).fillna(0).astype(int)
    agg["COMPLETED_CONTRACT_COUNT"] = agg["SK_ID_CURR"].map(
        pos[pos["NAME_CONTRACT_STATUS"] == "Completed"].groupby("SK_ID_CURR")["SK_ID_PREV"].nunique()
    ).fillna(0).astype(int)
    return agg


# ---------------------------------------------------------------------------
# 6. Installment payment aggregates (Page 17) — repayment behaviour
# ---------------------------------------------------------------------------

def add_installment_features(installments: pd.DataFrame) -> pd.DataFrame:
    df = installments.copy()
    df["PAYMENT_DELAY"] = df["DAYS_ENTRY_PAYMENT"] - df["DAYS_INSTALMENT"]
    df["PAYMENT_DIFFERENCE"] = df["AMT_PAYMENT"] - df["AMT_INSTALMENT"]
    df["PAYMENT_RATIO"] = (df["AMT_PAYMENT"] / df["AMT_INSTALMENT"].replace(0, np.nan)).round(3)
    df["PAYMENT_CLASS"] = df["PAYMENT_DELAY"].apply(classify_payment_timing)
    return df


def classify_payment_timing(delay_days) -> str:
    if pd.isna(delay_days):
        return "Unknown"
    if delay_days < 0:
        return "Early Payment"
    if delay_days == 0:
        return "On-Time Payment"
    return "Late Payment"


def classify_payment_amount(ratio) -> str:
    if pd.isna(ratio):
        return "Unknown"
    if ratio < 0.99:
        return "Underpayment"
    if ratio > 1.01:
        return "Overpayment"
    return "Full Payment"


def aggregate_installment_features(installments_with_features: pd.DataFrame) -> pd.DataFrame:
    df = installments_with_features
    g = df.groupby("SK_ID_CURR")
    agg = g.agg(
        TOTAL_INSTALLMENTS=("AMT_INSTALMENT", "count"),
        AVG_PAYMENT_DELAY=("PAYMENT_DELAY", "mean"),
        MAX_PAYMENT_DELAY=("PAYMENT_DELAY", "max"),
        AVG_PAYMENT_RATIO=("PAYMENT_RATIO", "mean"),
    ).reset_index()

    late = df[df["PAYMENT_CLASS"] == "Late Payment"].groupby("SK_ID_CURR").size()
    agg["LATE_PAYMENT_COUNT"] = agg["SK_ID_CURR"].map(late).fillna(0).astype(int)
    agg["LATE_PAYMENT_PERCENTAGE"] = (agg["LATE_PAYMENT_COUNT"] / agg["TOTAL_INSTALLMENTS"] * 100).round(2)

    underpay = df[df["PAYMENT_RATIO"] < 0.99].groupby("SK_ID_CURR").size()
    agg["UNDERPAYMENT_COUNT"] = agg["SK_ID_CURR"].map(underpay).fillna(0).astype(int)
    return agg


# ---------------------------------------------------------------------------
# 7. Credit card balance aggregates (Page 18)
# ---------------------------------------------------------------------------

def add_credit_card_features(cc: pd.DataFrame) -> pd.DataFrame:
    df = cc.copy()
    df["CREDIT_UTILIZATION"] = (df["AMT_BALANCE"] / df["AMT_CREDIT_LIMIT_ACTUAL"].replace(0, np.nan)).round(3)
    return df


def aggregate_credit_card_features(cc_with_features: pd.DataFrame) -> pd.DataFrame:
    df = cc_with_features
    g = df.groupby("SK_ID_CURR")
    agg = g.agg(
        AVG_CC_BALANCE=("AMT_BALANCE", "mean"),
        MAX_CC_BALANCE=("AMT_BALANCE", "max"),
        AVG_CC_LIMIT=("AMT_CREDIT_LIMIT_ACTUAL", "mean"),
        AVG_CC_UTILIZATION=("CREDIT_UTILIZATION", "mean"),
        MAX_CC_UTILIZATION=("CREDIT_UTILIZATION", "max"),
        TOTAL_CC_DRAWINGS=("AMT_DRAWINGS_CURRENT", "sum"),
        AVG_CC_PAYMENT=("AMT_PAYMENT_CURRENT", "mean"),
        MAX_CC_DPD=("SK_DPD", "max"),
    ).reset_index()
    return agg


# ---------------------------------------------------------------------------
# 8. Master customer table + rule-based risk segmentation (Pages 19-20)
# ---------------------------------------------------------------------------

def build_master_customer_table(app_df: pd.DataFrame, bureau_agg=None, prev_agg=None,
                                 pos_agg=None, inst_agg=None, cc_agg=None) -> pd.DataFrame:
    """Left-join every customer-level aggregate onto the application table."""
    master = app_df.copy()
    for agg in [bureau_agg, prev_agg, pos_agg, inst_agg, cc_agg]:
        if agg is not None and not agg.empty:
            master = master.merge(agg, on="SK_ID_CURR", how="left")
    return master


def assign_risk_segment(df: pd.DataFrame) -> pd.Series:
    """
    Descriptive, rule-based EDA segmentation — NOT a predictive model.

    A point is added to a customer's "risk score" for each elevated-risk
    signal present (high leverage, high burden, weak bureau/repayment/card
    history). The resulting score (0-5) is mapped to a segment label.
    """
    score = pd.Series(0, index=df.index)

    if "CREDIT_TO_INCOME" in df.columns:
        score += (df["CREDIT_TO_INCOME"] > 5).fillna(False).astype(int)
    if "ANNUITY_TO_INCOME" in df.columns:
        score += (df["ANNUITY_TO_INCOME"] > 0.30).fillna(False).astype(int)
    if "LATE_PAYMENT_PERCENTAGE" in df.columns:
        score += (df["LATE_PAYMENT_PERCENTAGE"] > 20).fillna(False).astype(int)
    if "TOTAL_BUREAU_OVERDUE" in df.columns:
        score += (df["TOTAL_BUREAU_OVERDUE"] > 0).fillna(False).astype(int)
    if "AVG_CC_UTILIZATION" in df.columns:
        score += (df["AVG_CC_UTILIZATION"] > 0.75).fillna(False).astype(int)

    segment = pd.cut(
        score, bins=[-1, 0, 1, 2, 100],
        labels=["Low Observed Risk", "Moderate Observed Risk", "Elevated Observed Risk", "High Observed Risk"],
    )
    return segment
