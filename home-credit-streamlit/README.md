# Home Credit Default Risk — 20-Page EDA & Preprocessing Dashboard

## Project Objective

A 20-page Streamlit application covering **data understanding, preprocessing,
missing-value & outlier analysis, feature engineering, and exploratory data
analysis (EDA)** across the full Home Credit Default Risk dataset — with
business insights and recommendations on every page.

**This is an EDA and business-insights project. No machine-learning models,
predictions, feature-importance scores, ROC curves, or confusion matrices are
built anywhere in this application.** The project scope ends at:

```
DATA → PREPROCESSING → FEATURE ENGINEERING → EDA → SEGMENT ANALYSIS
     → OBSERVED RISK PATTERNS → BUSINESS INSIGHTS → BUSINESS RECOMMENDATIONS
```

## Business Problem

Home Credit extends loans to customers who often have limited or no formal
credit history. Understanding *who* the customer base is, *how* they behave
across income, employment, affordability, bureau, and repayment dimensions,
and *where* observed risk concentrates, supports better underwriting policy,
manual-review prioritization, and portfolio monitoring — without requiring a
predictive model.

## Home Credit Dataset Description

| File | Description | Key |
|---|---|---|
| `application_train.csv` | One row per loan application, includes `TARGET` (0 = repaid, 1 = default) | `SK_ID_CURR` |
| `bureau.csv` | Client's credit history at other financial institutions | `SK_ID_CURR`, `SK_ID_BUREAU` |
| `bureau_balance.csv` | Monthly status of each bureau credit | `SK_ID_BUREAU` |
| `previous_application.csv` | Client's previous Home Credit applications | `SK_ID_CURR`, `SK_ID_PREV` |
| `POS_CASH_balance.csv` | Monthly point-of-sale / cash loan balances | `SK_ID_PREV` |
| `installments_payments.csv` | Actual repayment history (scheduled vs paid) | `SK_ID_PREV` |
| `credit_card_balance.csv` | Monthly credit-card balances | `SK_ID_PREV` |

## Dataset Relationships

```
application_train (SK_ID_CURR)
    │
    ├── bureau (SK_ID_CURR → SK_ID_BUREAU)
    │        └── bureau_balance (SK_ID_BUREAU)
    │
    └── previous_application (SK_ID_CURR → SK_ID_PREV)
             ├── POS_CASH_balance (SK_ID_PREV)
             ├── installments_payments (SK_ID_PREV)
             └── credit_card_balance (SK_ID_PREV)
```

## Technology Stack

Python · Pandas · NumPy · Streamlit · Plotly Express · Plotly Graph Objects ·
Jupyter Notebook

## Preprocessing Steps

1. **Data understanding** — shape, dtypes, head/tail/sample, describe (see `notebooks/01_data_understanding.ipynb`)
2. **Missing values** — count + percentage per column, bucketed (0-5%, 5-20%, 20-40%, 40-60%, 60%+), with a stated treatment reason per bucket
3. **Duplicate analysis** — full-row duplicates and `SK_ID_CURR` uniqueness
4. **Data type correction** — numeric vs categorical vs ID columns kept distinct
5. **Invalid value cleanup** — `DAYS_EMPLOYED` anomaly (365243 placeholder) → missing; non-positive income/credit/annuity → missing; `CODE_GENDER` "XNA" → missing
6. **Outlier analysis** — IQR method with bounds, counts, and % per numeric column; outliers are flagged, not blindly removed (see Page 4 for the reasoning)

Full detail: `notebooks/02_preprocessing.ipynb`, `utils/preprocessing.py`.

## Feature Engineering

**Application-level** (`utils/feature_engineering.py::add_application_features`):
`AGE_YEARS`, `AGE_GROUP`, `EMPLOYMENT_YEARS`, `EMPLOYMENT_GROUP`, `INCOME_GROUP`
(quantile-based), `INCOME_PERCENTILE`, `INCOME_PER_FAMILY_MEMBER`,
`INCOME_PER_CHILD`, `CREDIT_TO_INCOME`, `ANNUITY_TO_INCOME`, `GOODS_TO_INCOME`,
`CREDIT_TO_GOODS`, plus banded versions of credit, credit-to-income, and
annuity-to-income for EDA.

**Customer-level aggregates from related tables**, one row per `SK_ID_CURR`:
- Bureau → `BUREAU_ACCOUNT_COUNT`, `ACTIVE_BUREAU_COUNT`, `TOTAL_BUREAU_DEBT`, `TOTAL_BUREAU_OVERDUE`, ...
- Bureau balance → `MONTHS_WITH_DELINQUENCY`, `MAX_DELINQUENCY_LEVEL`, ...
- Previous applications → `PREVIOUS_APPLICATION_COUNT`, `PREVIOUS_APPROVAL_RATE`, ...
- POS/CASH → `AVG_DPD`, `MAX_DPD`, `TOTAL_DPD_EVENTS`, ...
- Installments → `LATE_PAYMENT_COUNT`, `LATE_PAYMENT_PERCENTAGE`, `AVG_PAYMENT_DELAY`, ...
- Credit card → `AVG_CC_UTILIZATION`, `MAX_CC_UTILIZATION`, `MAX_CC_DPD`, ...

These feed `build_master_customer_table()` and the rule-based
`assign_risk_segment()` used on Pages 19-20.

Full detail: `notebooks/03_feature_engineering.ipynb`.

## 20 Dashboard Pages

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
19. Customer Risk Segmentation (rule-based EDA — explicitly not ML)
20. Executive Insights & Business Recommendations

Every page follows the same structure: **Business Objective → Sidebar
Filters → KPI Cards → 4-8 Visualizations → Detailed Data Table (with
download) → Key Observations → Business Insights → Recommendations.**

## EDA Methodology

- **Univariate**: income, credit, age, education, occupation distributions
- **Bivariate**: income vs credit, employment vs default, income group vs default, credit-to-income vs default
- **Multivariate**: age + income + default, employment + income + default, education + income + default (see `notebooks/04_eda.ipynb`)
- Descriptive statistics (mean, median, mode, std dev, min/max, percentiles, IQR) are computed wherever relevant, not just charted
- **Count vs rate** is always reported together (Page 11) — a large group can contain many defaults simply because it's large; rate, not count, measures relative risk
- Correlation is reported as an **observed relationship**, never as causation (Page 12)

## Major Insights & Business Recommendations

See **Page 20 (Executive Insights & Business Recommendations)** for the full
10-insight / 15-recommendation synthesis across affordability, repayment,
bureau, credit cards, employment, data quality, and portfolio monitoring.

## Project Structure

```
home-credit-streamlit/
├── app.py                          # Landing page
├── requirements.txt
├── README.md
├── .streamlit/config.toml          # Color theme
├── data/                           # 7 Home Credit CSVs (sample data included)
├── notebooks/                      # 4 supporting notebooks (data understanding,
│                                    #  preprocessing, feature engineering, EDA)
├── pages/                          # 20 numbered Streamlit pages
└── utils/
    ├── data_loader.py              # Cached CSV loaders + prepared/master table builders
    ├── preprocessing.py            # Data quality, missing values, duplicates, outliers
    ├── feature_engineering.py      # Application features + all customer-level aggregates
    ├── filters.py                  # Shared sidebar filters
    ├── charts.py                   # Reusable, colorful Plotly chart library
    ├── metrics.py                  # KPI, formatting, and statistical-summary helpers
    └── styling.py                  # Shared CSS for the colorful dashboard theme
```

## Installation

```bash
pip install -r requirements.txt
```

## How to Run

```bash
streamlit run app.py
```

### Using your full dataset

This folder ships with a small sample (1,000 rows per table) so the app runs
immediately. To use your full-size files, replace each file in `data/` with
your real one, **keeping the same filenames**:

```
data/application_train.csv
data/bureau.csv
data/bureau_balance.csv
data/previous_application.csv
data/POS_CASH_balance.csv
data/installments_payments.csv
data/credit_card_balance.csv
```

All loaders are wrapped in `@st.cache_data`, so each file is read from disk
only once per session regardless of file size.

## Screenshots

_Add screenshots of the running app here before submission._

## Streamlit Deployment URL

_Add your deployed Streamlit Community Cloud (or equivalent) URL here after deployment._

## Author

_Add your name here._
