import streamlit as st
from utils.styling import apply_custom_css

from utils.data_loader import load_prepared_application_data
from utils.filters import sidebar_filters, apply_filters
from utils.metrics import fmt_number, fmt_pct, top_bottom_by_default_rate
from utils.charts import bar_chart, donut_chart, horizontal_bar_chart, grouped_bar_chart

st.set_page_config(page_title="Default Risk EDA", layout="wide")
apply_custom_css()
st.title("Page 11 — Default Risk EDA")
st.caption("**Business Objective:** exploratory analysis of the TARGET variable. This is EDA only — no predictive model is built.")

df = load_prepared_application_data()
filters = sidebar_filters(df)
d = apply_filters(df, filters)

if d.empty:
    st.warning("No applicants match the selected filters.")
else:
    total = len(d)
    defaults = int(d["TARGET"].sum())
    default_rate = defaults / total * 100 if total else 0

    highest_risk_age, _ = top_bottom_by_default_rate(d, "AGE_GROUP", min_count=5)
    highest_risk_income, _ = top_bottom_by_default_rate(d, "INCOME_GROUP", min_count=5)
    highest_risk_employment, _ = top_bottom_by_default_rate(d, "EMPLOYMENT_GROUP", min_count=5)

    st.subheader("KPI Cards")
    cols = st.columns(3)
    cols[0].metric("Default Customers", fmt_number(defaults))
    cols[1].metric("Non-Default Customers", fmt_number(total - defaults))
    cols[2].metric("Default Rate", fmt_pct(default_rate))
    cols = st.columns(3)
    cols[0].metric("Highest Risk Age Group", str(highest_risk_age))
    cols[1].metric("Highest Risk Income Group", str(highest_risk_income))
    cols[2].metric("Highest Risk Employment Group", str(highest_risk_employment))

    st.subheader("Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(d, "REPAYMENT_STATUS", "TARGET", "TARGET Distribution", aggfunc="count"), use_container_width=True)
    with col2:
        st.plotly_chart(donut_chart(d, "REPAYMENT_STATUS", "Default Percentage"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(d, "AGE_GROUP", "TARGET", "Default Rate by Age Group", aggfunc="mean"), use_container_width=True)
    with col2:
        st.plotly_chart(bar_chart(d, "INCOME_GROUP", "TARGET", "Default Rate by Income Group", aggfunc="mean"), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(bar_chart(d, "EMPLOYMENT_GROUP", "TARGET", "Default Rate by Employment Group", aggfunc="mean"), use_container_width=True)
    with col2:
        st.plotly_chart(horizontal_bar_chart(d, "NAME_EDUCATION_TYPE", "TARGET", "Default Rate by Education", aggfunc="mean", ascending=False), use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(
            horizontal_bar_chart(d.dropna(subset=["OCCUPATION_TYPE"]), "OCCUPATION_TYPE", "TARGET", "Default Rate by Occupation (Top 12)", top_n=12, aggfunc="mean", ascending=False),
            use_container_width=True,
        )
    with col2:
        st.plotly_chart(grouped_bar_chart(d, "NAME_CONTRACT_TYPE", "TARGET", "CODE_GENDER", "Default by Contract Type x Gender", aggfunc="mean"), use_container_width=True)

    st.subheader("Detailed Data Table")
    age_summary = d.dropna(subset=["AGE_GROUP"]).groupby("AGE_GROUP", observed=True).agg(
        Customers=("TARGET", "size"), Defaults=("TARGET", "sum")
    ).reset_index()
    age_summary["Default Rate %"] = (age_summary["Defaults"] / age_summary["Customers"] * 100).round(2)
    st.dataframe(age_summary, use_container_width=True, hide_index=True)
    st.download_button("Download Age Group Default Summary", age_summary.to_csv(index=False), "default_by_age_group.csv", "text/csv")

    st.subheader("Required Insight — Count vs Rate")
    biggest_default_count_group = d.dropna(subset=["AGE_GROUP"]).groupby("AGE_GROUP", observed=True)["TARGET"].sum().idxmax()
    st.markdown(
        f"""
        The age group with the **most defaults in absolute count** is **{biggest_default_count_group}**,
        but the age group with the **highest default rate** is **{highest_risk_age}** — these are not
        necessarily the same group. A large group can contain many defaults simply because it
        contains many customers; rate, not count, is the correct measure of relative risk.
        """
    )

    st.subheader("Key Observations")
    st.markdown(
        f"""
        - Overall default rate in the filtered portfolio is **{fmt_pct(default_rate)}**.
        - The **{highest_risk_age}** age group, **{highest_risk_income}** income group, and
          **{highest_risk_employment}** employment tenure group each show the highest observed
          default rate within their respective dimension.
        """
    )

    st.subheader("Business Insights")
    st.markdown(
        """
        - Default risk is not evenly distributed — it concentrates in specific, identifiable
          segments rather than spreading uniformly across the portfolio.
        - Reporting default counts without rates (or vice versa) can mislead decision-makers; both
          numbers are needed together for correct portfolio risk reads.
        """
    )

    st.subheader("Recommendations")
    st.markdown(
        f"""
        1. Always pair default **counts** with default **rates** in risk reporting — never one
           without the other.
        2. Apply enhanced review for the **{highest_risk_age}** / **{highest_risk_income}** /
           **{highest_risk_employment}** segments identified above.
        3. Investigate *why* these segments show elevated rates (income volatility? shorter credit
           history?) on the Risk Factor Exploration and Bureau pages before changing policy.
        """
    )
