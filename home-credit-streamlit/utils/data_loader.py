"""
Cached CSV loaders for every Home Credit table used across the dashboard.

Each raw loader is wrapped with @st.cache_data so a (potentially large)
file is only read from disk once per session, no matter how many pages
or filter interactions request it.
"""
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

APPLICATION_PATH = DATA_DIR / "application_train.csv"
BUREAU_PATH = DATA_DIR / "bureau.csv"
BUREAU_BALANCE_PATH = DATA_DIR / "bureau_balance.csv"
PREVIOUS_APPLICATION_PATH = DATA_DIR / "previous_application.csv"
POS_CASH_PATH = DATA_DIR / "POS_CASH_balance.csv"
INSTALLMENTS_PATH = DATA_DIR / "installments_payments.csv"
CREDIT_CARD_PATH = DATA_DIR / "credit_card_balance.csv"


def _read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    return df


@st.cache_data
def load_application_raw() -> pd.DataFrame:
    return _read_csv(APPLICATION_PATH)


@st.cache_data
def load_bureau_raw() -> pd.DataFrame:
    return _read_csv(BUREAU_PATH)


@st.cache_data
def load_bureau_balance_raw() -> pd.DataFrame:
    return _read_csv(BUREAU_BALANCE_PATH)


@st.cache_data
def load_previous_application_raw() -> pd.DataFrame:
    return _read_csv(PREVIOUS_APPLICATION_PATH)


@st.cache_data
def load_pos_cash_raw() -> pd.DataFrame:
    return _read_csv(POS_CASH_PATH)


@st.cache_data
def load_installments_raw() -> pd.DataFrame:
    return _read_csv(INSTALLMENTS_PATH)


@st.cache_data
def load_credit_card_raw() -> pd.DataFrame:
    return _read_csv(CREDIT_CARD_PATH)


@st.cache_data
def load_prepared_application_data() -> pd.DataFrame:
    """application_train.csv, cleaned + with all application-level derived
    features attached. This is the dataframe almost every page works from."""
    from .preprocessing import clean_application_data
    from .feature_engineering import add_application_features

    df = load_application_raw()
    df = clean_application_data(df)
    df = add_application_features(df)
    return df


@st.cache_data
def load_master_customer_table() -> pd.DataFrame:
    """One row per customer: application features + aggregated features from
    every related table, plus the rule-based RISK_SEGMENT. Used by the
    Risk Segmentation (19) and Executive Insights (20) pages."""
    from .feature_engineering import (
        aggregate_bureau_features, aggregate_bureau_balance_features,
        aggregate_previous_application_features, aggregate_pos_cash_features,
        add_installment_features, aggregate_installment_features,
        add_credit_card_features, aggregate_credit_card_features,
        build_master_customer_table, assign_risk_segment,
    )

    app_df = load_prepared_application_data()
    bureau = load_bureau_raw()
    bureau_balance = load_bureau_balance_raw()
    prev = load_previous_application_raw()
    pos = load_pos_cash_raw()
    inst = load_installments_raw()
    cc = load_credit_card_raw()

    bureau_agg = aggregate_bureau_features(bureau)
    bb_agg = aggregate_bureau_balance_features(bureau_balance, bureau)
    prev_agg = aggregate_previous_application_features(prev)
    pos_agg = aggregate_pos_cash_features(pos)
    inst_agg = aggregate_installment_features(add_installment_features(inst))
    cc_agg = aggregate_credit_card_features(add_credit_card_features(cc))

    master = build_master_customer_table(app_df, bureau_agg, prev_agg, pos_agg, inst_agg, cc_agg)
    if bb_agg is not None and not bb_agg.empty:
        master = master.merge(bb_agg, on="SK_ID_CURR", how="left")

    master["RISK_SEGMENT"] = assign_risk_segment(master)
    return master


def data_file_status() -> dict:
    """Which of the 7 recommended files are actually present in data/."""
    paths = {
        "application_train.csv": APPLICATION_PATH,
        "bureau.csv": BUREAU_PATH,
        "bureau_balance.csv": BUREAU_BALANCE_PATH,
        "previous_application.csv": PREVIOUS_APPLICATION_PATH,
        "POS_CASH_balance.csv": POS_CASH_PATH,
        "installments_payments.csv": INSTALLMENTS_PATH,
        "credit_card_balance.csv": CREDIT_CARD_PATH,
    }
    return {name: path.exists() for name, path in paths.items()}
