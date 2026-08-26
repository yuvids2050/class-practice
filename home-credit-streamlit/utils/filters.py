"""
Shared sidebar filters (Section 27 of the spec): Gender, Age Group, Income
Group, Education, Occupation, Family Status, Housing Type, Contract Type,
Employment Group, Default Status, and (where available) Risk Segment.

Every filter is optional/graceful — a page that hasn't computed
EMPLOYMENT_GROUP or RISK_SEGMENT yet simply won't show that control.
"""
import pandas as pd
import streamlit as st


def _multiselect(df: pd.DataFrame, col: str, label: str):
    if col not in df.columns:
        return None
    options = sorted([o for o in df[col].dropna().unique().tolist()])
    if not options:
        return None
    return st.sidebar.multiselect(label, options=options, default=options)


def sidebar_filters(df: pd.DataFrame) -> dict:
    st.sidebar.header("Filters")

    filters = {
        "CODE_GENDER": _multiselect(df, "CODE_GENDER", "Gender"),
        "AGE_GROUP": _multiselect(df, "AGE_GROUP", "Age Group"),
        "INCOME_GROUP": _multiselect(df, "INCOME_GROUP", "Income Group"),
        "NAME_EDUCATION_TYPE": _multiselect(df, "NAME_EDUCATION_TYPE", "Education"),
        "OCCUPATION_TYPE": _multiselect(df, "OCCUPATION_TYPE", "Occupation"),
        "NAME_FAMILY_STATUS": _multiselect(df, "NAME_FAMILY_STATUS", "Family Status"),
        "NAME_HOUSING_TYPE": _multiselect(df, "NAME_HOUSING_TYPE", "Housing Type"),
        "NAME_CONTRACT_TYPE": _multiselect(df, "NAME_CONTRACT_TYPE", "Contract Type"),
        "EMPLOYMENT_GROUP": _multiselect(df, "EMPLOYMENT_GROUP", "Employment Group"),
        "RISK_SEGMENT": _multiselect(df, "RISK_SEGMENT", "Risk Segment"),
    }

    if "TARGET" in df.columns:
        target_labels = {0: "Repaid (0)", 1: "Defaulted (1)"}
        options = sorted(df["TARGET"].dropna().unique().tolist())
        filters["TARGET"] = st.sidebar.multiselect(
            "Default Status", options=options, default=options,
            format_func=lambda x: target_labels.get(x, str(x)),
        )
    else:
        filters["TARGET"] = None

    return filters


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    d = df.copy()
    for col, selected in filters.items():
        if selected is None:
            continue
        if col not in d.columns:
            continue
        d = d[d[col].isin(selected)]
    return d
