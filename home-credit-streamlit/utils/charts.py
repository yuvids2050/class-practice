"""
Reusable Plotly chart builders covering every chart type called for in the
spec's chart-recommendation table: bar, horizontal bar, histogram, box,
scatter, line, stacked bar, donut, treemap, heatmap, grouped bar, gauge.

A shared vivid color palette + clean white template is applied globally via
px.defaults so every chart across all 20 pages shares one colorful,
professional visual identity without needing per-call color arguments.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .styling import CHART_PALETTE

px.defaults.color_discrete_sequence = CHART_PALETTE
px.defaults.color_continuous_scale = "Viridis"
px.defaults.template = "plotly_white"

_SINGLE_SERIES_COLOR = CHART_PALETTE[0]
_SEQUENTIAL_SCALE = "Plasma"
_TITLE_FONT = dict(size=17, color="#312E81", family="sans-serif")


def _polish(fig, showlegend=None):
    layout = dict(title_font=_TITLE_FONT, margin=dict(t=60, l=10, r=10, b=10), height=380)
    if showlegend is not None:
        layout["showlegend"] = showlegend
    fig.update_layout(**layout)
    return fig


def bar_chart(df: pd.DataFrame, group_col: str, value_col: str | None, title: str, top_n: int = None, aggfunc: str = "sum"):
    if value_col is None:
        data = df.groupby(group_col, observed=True).size().reset_index(name="value")
        y_col = "value"
    else:
        if aggfunc == "count":
            data = df.groupby(group_col, observed=True)[value_col].count().reset_index(name=value_col)
        elif aggfunc == "mean":
            data = df.groupby(group_col, observed=True)[value_col].mean().round(4).reset_index(name=value_col)
        else:
            data = df.groupby(group_col, observed=True)[value_col].sum().reset_index(name=value_col)
        y_col = value_col
    data = data.sort_values(y_col, ascending=False)
    if top_n:
        data = data.head(top_n)
    fig = px.bar(data, x=group_col, y=y_col, title=title, text_auto=".2s", color=group_col)
    return _polish(fig, showlegend=False)


def horizontal_bar_chart(df: pd.DataFrame, group_col: str, value_col: str, title: str, top_n: int = None, ascending: bool = True, aggfunc: str = "sum"):
    if aggfunc == "mean":
        data = df.groupby(group_col, observed=True)[value_col].mean().reset_index(name=value_col)
    elif aggfunc == "count":
        data = df.groupby(group_col, observed=True)[value_col].count().reset_index(name=value_col)
    else:
        data = df.groupby(group_col, observed=True)[value_col].sum().reset_index(name=value_col)
    data = data.sort_values(value_col, ascending=ascending)
    if top_n:
        data = data.tail(top_n) if ascending else data.head(top_n)
    fig = px.bar(data, y=group_col, x=value_col, title=title, orientation="h", color=value_col, color_continuous_scale=_SEQUENTIAL_SCALE)
    return _polish(fig, showlegend=False)


def grouped_bar_chart(df: pd.DataFrame, group_col: str, value_col: str, split_col: str, title: str, aggfunc: str = "mean"):
    if aggfunc == "mean":
        data = df.groupby([group_col, split_col], observed=True)[value_col].mean().reset_index()
    elif aggfunc == "count":
        data = df.groupby([group_col, split_col], observed=True)[value_col].count().reset_index()
    else:
        data = df.groupby([group_col, split_col], observed=True)[value_col].sum().reset_index()
    fig = px.bar(data, x=group_col, y=value_col, color=split_col, title=title, barmode="group")
    return _polish(fig)


def stacked_bar_chart(df: pd.DataFrame, group_col: str, split_col: str, title: str):
    data = df.groupby([group_col, split_col], observed=True).size().reset_index(name="Count")
    fig = px.bar(data, x=group_col, y="Count", color=split_col, title=title, barmode="stack")
    return _polish(fig)


def histogram(df: pd.DataFrame, column: str, title: str, color_col: str | None = None, nbins: int = 40):
    if color_col:
        fig = px.histogram(df, x=column, nbins=nbins, title=title, color=color_col, barmode="overlay", opacity=0.75)
    else:
        fig = px.histogram(df, x=column, nbins=nbins, title=title, color_discrete_sequence=[_SINGLE_SERIES_COLOR])
    return _polish(fig)


def donut_chart(df: pd.DataFrame, names_col: str, title: str, values_col: str | None = None, aggfunc: str = "count"):
    if values_col is None:
        data = df.groupby(names_col, observed=True).size().reset_index(name="Count")
        values_col = "Count"
    elif aggfunc == "count":
        data = df.groupby(names_col, observed=True).size().reset_index(name=values_col)
    else:
        data = df.groupby(names_col, observed=True)[values_col].sum().reset_index()
    fig = px.pie(data, names=names_col, values=values_col, title=title, hole=0.5)
    fig.update_traces(textinfo="percent+label", marker=dict(line=dict(color="#FFFFFF", width=2)))
    return _polish(fig)


def treemap_chart(df: pd.DataFrame, path_cols: list, value_col: str, title: str, aggfunc: str = "sum"):
    if aggfunc == "mean":
        data = df.groupby(path_cols, observed=True)[value_col].mean().reset_index()
    else:
        data = df.groupby(path_cols, observed=True)[value_col].sum().reset_index()
    fig = px.treemap(data, path=path_cols, values=value_col, title=title, color=value_col, color_continuous_scale=_SEQUENTIAL_SCALE)
    return _polish(fig)


def scatter_chart(df: pd.DataFrame, x_col: str, y_col: str, color_col: str | None, title: str):
    fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=title, opacity=0.65)
    fig.update_traces(marker=dict(size=7, line=dict(width=0.5, color="white")))
    return _polish(fig)


def box_plot(df: pd.DataFrame, y_col: str, x_col: str | None, title: str):
    if x_col:
        fig = px.box(df, y=y_col, x=x_col, title=title, color=x_col)
        return _polish(fig, showlegend=False)
    fig = px.box(df, y=y_col, title=title, color_discrete_sequence=[_SINGLE_SERIES_COLOR])
    return _polish(fig)


def line_chart(df: pd.DataFrame, x_col: str, y_col: str, title: str, aggfunc: str = "mean"):
    if aggfunc == "mean":
        data = df.groupby(x_col, observed=True)[y_col].mean().reset_index()
    elif aggfunc == "count":
        data = df.groupby(x_col, observed=True)[y_col].count().reset_index()
    else:
        data = df.groupby(x_col, observed=True)[y_col].sum().reset_index()
    data = data.sort_values(x_col)
    fig = px.line(data, x=x_col, y=y_col, title=title, markers=True, color_discrete_sequence=[_SINGLE_SERIES_COLOR])
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    return _polish(fig)


def correlation_heatmap(corr_matrix: pd.DataFrame, title: str):
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values, x=corr_matrix.columns, y=corr_matrix.index,
        colorscale="RdBu", zmid=0, text=corr_matrix.round(2).values, texttemplate="%{text}",
    ))
    fig.update_layout(title=dict(text=title, font=_TITLE_FONT), height=450, margin=dict(t=60, l=10, r=10, b=10))
    return fig


def category_heatmap(df: pd.DataFrame, row_col: str, col_col: str, title: str):
    """Heatmap of counts across two categorical columns (e.g. status x month)."""
    pivot = pd.crosstab(df[row_col], df[col_col])
    fig = go.Figure(data=go.Heatmap(z=pivot.values, x=pivot.columns.astype(str), y=pivot.index.astype(str), colorscale="Turbo"))
    fig.update_layout(title=dict(text=title, font=_TITLE_FONT), height=420, margin=dict(t=60, l=10, r=10, b=10))
    return fig


def gauge_chart(value: float, title: str, max_value: float = 100, suffix: str = "%"):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": suffix, "font": {"color": "#312E81", "size": 36}},
        title={"text": title, "font": _TITLE_FONT},
        gauge={
            "axis": {"range": [0, max_value]},
            "bar": {"color": "#6366F1"},
            "bgcolor": "white",
            "borderwidth": 1,
            "bordercolor": "#E0E7FF",
            "steps": [
                {"range": [0, max_value * 0.5], "color": "#FEE2E2"},
                {"range": [max_value * 0.5, max_value * 0.8], "color": "#FEF3C7"},
                {"range": [max_value * 0.8, max_value], "color": "#D1FAE5"},
            ],
        },
    ))
    fig.update_layout(height=280, margin=dict(t=50, l=20, r=20, b=10))
    return fig
