import streamlit as st
from utils.styling import apply_custom_css

from utils.data_loader import load_prepared_application_data, data_file_status
from utils.filters import sidebar_filters, apply_filters
from utils.metrics import portfolio_kpis, fmt_currency, fmt_pct, fmt_number
from utils.charts import donut_chart, bar_chart, histogram

st.set_page_config(page_title="Home Credit Analytics", page_icon="🏦", layout="wide")
apply_custom_css()

st.title("🏦 HOME CREDIT DEFAULT RISK — EDA & PREPROCESSING DASHBOARD")
st.markdown(
    """
    A 20-page Streamlit application covering **data understanding, preprocessing, missing-value and
    outlier analysis, feature engineering, and exploratory data analysis** across the full Home Credit
    dataset (application, bureau, bureau balance, previous applications, POS/CASH, installments, and
    credit card tables).

    **This is an EDA & business-insights project — no machine-learning models, predictions, or
    feature-importance scores are built anywhere in this application.**
    """
)

status = data_file_status()
missing_files = [name for name, present in status.items() if not present]
if missing_files:
    st.warning(f"Missing data files: {', '.join(missing_files)}. Some pages will be unavailable until these are added to `data/`.")

with st.expander("📋 Dashboard Navigation (20 Pages)"):
    st.markdown(
        """
        **Foundation**
        1. Executive Portfolio Overview
        2. Data Quality Dashboard
        3. Missing Value Analysis
        4. Outlier & Distribution Analysis

        **Customer & Application EDA**
        5. Customer Demographic Analysis
        6. Income Analysis
        7. Employment Analysis
        8. Family & Housing Analysis
        9. Current Loan Application Analysis
        10. Credit Affordability Analysis
        11. Default Risk EDA
        12. Risk Factor Exploration

        **Related Tables & Synthesis**
        13. Bureau Credit History Analysis
        14. Bureau Balance Analysis
        15. Previous Application Analysis
        16. POS/CASH Loan Analysis
        17. Installment Payment Analysis
        18. Credit Card Balance Analysis
        19. Customer Risk Segmentation (rule-based EDA, not ML)
        20. Executive Insights & Business Recommendations
        """
    )

st.divider()

try:
    df = load_prepared_application_data()
    filters = sidebar_filters(df)
    d = apply_filters(df, filters)

    if d.empty:
        st.warning("No applicants match the selected filters.")
    else:
        metrics = portfolio_kpis(d)

        st.subheader("Portfolio KPIs")
        cols = st.columns(4)
        cols[0].metric("Total Customers", fmt_number(metrics["total_customers"]))
        cols[1].metric("Default Customers", fmt_number(metrics["default_customers"]))
        cols[2].metric("Default Rate", fmt_pct(metrics["default_rate"]))
        cols[3].metric("Total Credit Exposure", fmt_currency(metrics["total_credit"]))

        cols = st.columns(4)
        cols[0].metric("Average Credit", fmt_currency(metrics["avg_credit"]))
        cols[1].metric("Average Income", fmt_currency(metrics["avg_income"]))
        cols[2].metric("Average Annuity", fmt_currency(metrics["avg_annuity"]))
        cols[3].metric("Median Income", fmt_currency(metrics["median_income"]))

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(donut_chart(d, "REPAYMENT_STATUS", "Default vs Non-Default"), use_container_width=True)
        with col2:
            st.plotly_chart(bar_chart(d, "NAME_EDUCATION_TYPE", "TARGET", "Default Rate by Education", aggfunc="mean"), use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(histogram(d, "AMT_CREDIT", "Credit Amount Distribution"), use_container_width=True)
        with col2:
            st.plotly_chart(histogram(d, "AMT_INCOME_TOTAL", "Income Distribution"), use_container_width=True)

except FileNotFoundError:
    st.error("❌ `data/application_train.csv` not found. Please add your dataset files and refresh.")
