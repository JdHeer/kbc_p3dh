"""
KBC Pillar 3 Data Hub – Streamlit Dashboard

Run with:  uv run streamlit run dashboard.py
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from kbc_p3dh.loader import get_template_group, load_mapped_data

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="KBC P3DH Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Colour palette ─────────────────────────────────────────────────────────────
ZANDERS_BLUE = "#1B2A4A"
ZANDERS_LIGHT = "#3A7BD5"
KBC_GREEN = "#00C853"
ACCENT_TEAL = "#26C6DA"
ACCENT_RED = "#EF5350"
ACCENT_ORANGE = "#FFA726"
ACCENT_PURPLE = "#AB47BC"
SUBTLE_GRAY = "#90A4AE"
CARD_BG = "rgba(255,255,255,0.04)"

CHART_LAYOUT = dict(
    template="plotly_dark",
    font=dict(family="Inter, Segoe UI, sans-serif", size=12, color="#E0E0E0"),
    margin=dict(l=10, r=20, t=50, b=30),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Import Inter font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Global font */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(58,123,213,0.10), rgba(0,200,83,0.06));
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 16px 20px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    border-color: rgba(58,123,213,0.3);
}
[data-testid="stMetric"] [data-testid="stMetricLabel"] {
    font-size: 0.78rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    opacity: 0.7;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -0.02em;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(255,255,255,0.03);
    border-radius: 12px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 10px 24px;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #3A7BD5, #1B2A4A) !important;
}

/* Dividers */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(58,123,213,0.3), transparent);
    margin: 1.5rem 0;
}

/* Subheaders */
.stMarkdown h3 {
    font-weight: 600;
    letter-spacing: -0.01em;
    margin-bottom: 0.25rem;
}

/* Expander styling */
.streamlit-expanderHeader {
    font-weight: 500;
    font-size: 0.9rem;
}

/* Info box */
[data-testid="stAlert"] {
    border-radius: 10px;
    border-left-width: 4px;
}

/* Plotly chart containers */
[data-testid="stPlotlyChart"] {
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.06);
    background: rgba(255,255,255,0.02);
    padding: 4px;
    transition: border-color 0.2s ease;
}
[data-testid="stPlotlyChart"]:hover {
    border-color: rgba(58,123,213,0.2);
}

/* Dataframe styling */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
}

/* Caption styling */
.stCaption {
    opacity: 0.6;
}
</style>
""", unsafe_allow_html=True)


# ── Data loading (cached) ─────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading EBA data…")
def _load():
    df = load_mapped_data()
    df["group"] = df["file"].apply(get_template_group)
    return df


DF = _load()


def _clean(s: pd.Series) -> pd.Series:
    return s.str.replace("\xa0", " ", regex=False)


# ══════════════════════════════════════════════════════════════════════════════
# 1. KEY METRICS (EU KM1, k_61.00)
# ══════════════════════════════════════════════════════════════════════════════
_km = DF[(DF.file == "k_61.00") & (DF.col_label == "a. T")].copy()
_km["rc"] = _clean(_km["row_label"])

_cap_labels = {
    "1. Common Equity Tier 1 (CET1) capital": "CET1 Capital",
    "2. Tier 1 capital": "Tier 1 Capital",
    "3. Total capital": "Total Capital",
}
CAP_AMOUNTS = _km[_km.rc.isin(_cap_labels)].copy()
CAP_AMOUNTS["label"] = CAP_AMOUNTS.rc.map(_cap_labels)
CAP_AMOUNTS["value_bn"] = CAP_AMOUNTS.factNumeric / 1e9

_ratio_labels = {
    "5. Common Equity Tier 1 ratio (%)": "CET1 Ratio",
    "6. Tier 1 ratio (%)": "Tier 1 Ratio",
    "7. Total capital ratio (%)": "Total Capital Ratio",
}
CAP_RATIOS = _km[_km.rc.isin(_ratio_labels)].copy()
CAP_RATIOS["label"] = CAP_RATIOS.rc.map(_ratio_labels)
CAP_RATIOS["value_pct"] = CAP_RATIOS.factNumeric * 100


def _kpi(mask_str: str) -> float:
    row = _km[_km.rc.str.contains(mask_str, na=False)]
    return row.factNumeric.values[0] if len(row) else 0


RWA_BN = _kpi("4. Total risk-weighted exposure amount") / 1e9
LEV_PCT = _kpi("14. Leverage ratio") * 100
LCR_PCT = _kpi("Liquidity coverage ratio") * 100
NSFR_PCT = _kpi("NSFR ratio") * 100
CET1_PCT = _kpi("5. Common Equity Tier 1 ratio") * 100
T1_PCT = _kpi("6. Tier 1 ratio") * 100
TC_PCT = _kpi("7. Total capital ratio") * 100
T1_ABS = _kpi("2. Tier 1 capital")  # absolute Tier 1 for SOT denominators

# ══════════════════════════════════════════════════════════════════════════════
# 2. RWA OVERVIEW (EU OV1, k_60.00.a)
# ══════════════════════════════════════════════════════════════════════════════
_ov1 = DF[
    (DF.file == "k_60.00.a")
    & (DF.col_label.str.contains("TREA|a\\.", na=False, regex=True))
].copy()
_ov1["rc"] = _clean(_ov1["row_label"])
_all_risks = _ov1[_ov1.rc.str.match(r"^\d+\.\s")].copy()
_all_risks["label"] = _all_risks.rc.str.replace(r"^\d+\.\s+", "", regex=True)
_all_risks["is_of_which"] = _all_risks["label"].str.lower().str.startswith("of which")
_all_risks["is_total"] = _all_risks["label"].str.lower().str.startswith("total")
# Parent risk types: exclude "of which" sub-items and the Total row
_main_risks = _all_risks[~_all_risks.is_of_which & ~_all_risks.is_total].copy()
# Sub-items ("of which" rows) for the detail chart
_sub_risks = _all_risks[_all_risks.is_of_which].copy()
_sub_risks["label"] = _sub_risks["label"].str.replace(r"^[Oo]f which\s+", "", regex=True)

# Build parent-child mapping for hover context
_RWA_PARENT_MAP: dict[str, str] = {}
for idx, row in _all_risks.iterrows():
    if not row.is_of_which and not row.is_total:
        current_parent = row.label
    elif row.is_of_which:
        _RWA_PARENT_MAP[row.label] = current_parent if current_parent else ""

# ══════════════════════════════════════════════════════════════════════════════
# 3. CREDIT RISK RWEA FLOWS (EU CR8, k_28.00)
# ══════════════════════════════════════════════════════════════════════════════
_cr8 = DF[DF.file == "k_28.00"].copy()
_cr8["rc"] = _clean(_cr8["row_label"])

# ══════════════════════════════════════════════════════════════════════════════
# 4. MARKET RISK RWEA FLOWS (EU MR2-B, k_12.00)
# ══════════════════════════════════════════════════════════════════════════════
_mr2 = DF[DF.file == "k_12.00"].copy()
_mr2["rc"] = _clean(_mr2["row_label"])

# ══════════════════════════════════════════════════════════════════════════════
# 5. IRRBB (EU IRRBB1, k_68.00)
# ══════════════════════════════════════════════════════════════════════════════
_irr = DF[DF.file == "k_68.00"].copy()
_irr["rc"] = _clean(_irr["row_label"])
IRR_EVE = _irr[
    _irr.col_label.str.contains("economic value", case=False, na=False)
    & _irr.col_code.str.contains("Current", case=False, na=False)
].copy()
IRR_NII = _irr[
    _irr.col_label.str.contains("net interest", case=False, na=False)
    & _irr.col_code.str.contains("Current", case=False, na=False)
].copy()

# ══════════════════════════════════════════════════════════════════════════════
# 6. NMD / DEPOSIT DATA (EU LIQ1, k_73.00.c)
# ══════════════════════════════════════════════════════════════════════════════
_lcr = DF[DF.file == "k_73.00.c"].copy()
_lcr["rc"] = _clean(_lcr["row_label"])


def _period(col_code: str) -> str:
    m = {"a. T": "T", "b. T-1": "T-1", "c. T-2": "T-2", "d. T-3": "T-3",
         "e. T": "T", "f. T-1": "T-1", "g. T-2": "T-2", "h. T-3": "T-3"}
    return m.get(str(col_code).strip(), "")


def _weight_type(col_code: str, col_label: str) -> str:
    code = str(col_code).strip()
    if code in ("a. T", "b. T-1", "c. T-2", "d. T-3"):
        return "Unweighted"
    if code in ("e. T", "f. T-1", "g. T-2", "h. T-3"):
        return "Weighted"
    if "unweighted" in str(col_label).lower():
        return "Unweighted"
    if "weighted" in str(col_label).lower():
        return "Weighted"
    return ""


_lcr["period"] = _lcr.col_code.apply(_period)
_lcr["weight"] = _lcr.apply(lambda r: _weight_type(r.col_code, r.col_label), axis=1)

_NMD_ROWS = [
    "2. Retail deposits and deposits from small business customers, of which:",
    "3. Stable deposits",
    "4. Less stable deposits",
]
_WHOLESALE_ROWS = [
    "5. Unsecured wholesale funding",
    "6. Operational deposits all counterparties and deposits in networks of cooperative banks",
    "7. Non-operational deposits all counterparties",
    "8. Unsecured debt",
]
_DEPOSIT_ROWS = _NMD_ROWS + _WHOLESALE_ROWS

_SHORT: dict[str, str] = {
    "2. Retail deposits and deposits from small business customers, of which:": "Retail & SME",
    "3. Stable deposits": "Stable NMD",
    "4. Less stable deposits": "Less Stable NMD",
    "5. Unsecured wholesale funding": "Unsecured Wholesale",
    "6. Operational deposits all counterparties and deposits in networks of cooperative banks": "Operational Deposits",
    "7. Non-operational deposits all counterparties": "Non-Operational Deposits",
    "8. Unsecured debt": "Unsecured Debt",
}

_nmd_t = _lcr[(_lcr.period == "T") & _lcr.rc.isin(_DEPOSIT_ROWS)].copy()
_nmd_t["short"] = _nmd_t.rc.map(_SHORT)
NMD_UW = _nmd_t[_nmd_t.weight == "Unweighted"].copy()
NMD_W = _nmd_t[_nmd_t.weight == "Weighted"].copy()

_nmd_ts = _lcr[_lcr.rc.isin(_NMD_ROWS) & (_lcr.weight != "")].copy()
_nmd_ts["short"] = _nmd_ts.rc.map(_SHORT)


# ══════════════════════════════════════════════════════════════════════════════
# 7. ANNUAL REPORT DEPOSIT INSIGHTS (IFRS TABLES)
# Source: KBC Annual Report 2024 (Note 2.3 / Note 4.1 / Liquidity section)
# ══════════════════════════════════════════════════════════════════════════════
_AR_TOTAL_DEPOSITS_2024_MN = 271_087  # Deposits from customers + debt securities (excl. repos)
_AR_TOTAL_DEPOSITS_2023_MN = 259_491
_AR_CUSTOMER_DEPOSITS_2024_MN = 228_747
_AR_CUSTOMER_DEPOSITS_2023_MN = 216_501
_AR_REPORT_URL = "https://www.kbc.com/content/dam/kbccom/doc/investor-relations/Results/jvs-2024/jvs-2024-grp-en.pdf"

_AR_GEO = pd.DataFrame(
    [
        {"label": "Belgium BU", "group": "Business Unit", "parent": "Total", "v2024": 164_483, "v2023": 154_238},
        {"label": "Czech BU", "group": "Business Unit", "parent": "Total", "v2024": 52_709, "v2023": 52_642},
        {"label": "International Markets BU", "group": "Business Unit", "parent": "Total", "v2024": 32_832, "v2023": 31_687},
        {"label": "Hungary", "group": "IM Country", "parent": "International Markets BU", "v2024": 9_607, "v2023": 9_610},
        {"label": "Slovakia", "group": "IM Country", "parent": "International Markets BU", "v2024": 9_360, "v2023": 8_836},
        {"label": "Bulgaria", "group": "IM Country", "parent": "International Markets BU", "v2024": 13_865, "v2023": 13_241},
    ]
)
_AR_GEO_TOTAL_EX_GC_2024_MN = int(_AR_GEO[_AR_GEO["group"] == "Business Unit"]["v2024"].sum())
_AR_GEO_TOTAL_EX_GC_2023_MN = int(_AR_GEO[_AR_GEO["group"] == "Business Unit"]["v2023"].sum())
_AR_GEO["yoy_pct"] = (_AR_GEO["v2024"] / _AR_GEO["v2023"] - 1) * 100
_AR_GEO["share_pct"] = _AR_GEO["v2024"] / _AR_GEO_TOTAL_EX_GC_2024_MN * 100

_AR_PRODUCTS = pd.DataFrame(
    [
        {"label": "Demand deposits", "v2024": 110_090, "v2023": 107_568},
        {"label": "Savings accounts", "v2024": 74_440, "v2023": 70_810},
        {"label": "Time deposits", "v2024": 42_966, "v2023": 38_044},
        {"label": "Debt securities\n(incl. savings certificates)", "v2024": 43_590, "v2023": 43_068},
    ]
)
_AR_PRODUCTS["yoy_pct"] = (_AR_PRODUCTS["v2024"] / _AR_PRODUCTS["v2023"] - 1) * 100
_AR_PRODUCTS["share_pct"] = _AR_PRODUCTS["v2024"] / _AR_TOTAL_DEPOSITS_2024_MN * 100

_AR_DGS_COVERAGE_PCT = 56.0
_AR_STABLE_RETAIL_SME_PCT = 86.0
_AR_CUSTOMER_FUNDING_ON_DEMAND_BN = 154.0
_AR_CUSTOMER_FUNDING_TOTAL_BN = 229.0


# ══════════════════════════════════════════════════════════════════════════════
# CHART BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def fig_capital_stack() -> go.Figure:
    if CAP_AMOUNTS.empty:
        return go.Figure()
    d = CAP_AMOUNTS.sort_values("value_bn")
    colors = [KBC_GREEN, ZANDERS_LIGHT, ZANDERS_BLUE]
    fig = go.Figure(go.Bar(
        x=d.value_bn, y=d.label, orientation="h",
        text=d.value_bn.apply(lambda v: f"€{v:,.1f}bn"),
        textposition="outside", textfont=dict(size=12, color="#E0E0E0"),
        marker=dict(
            color=colors,
            line=dict(width=0),
            cornerradius=4,
        ),
        hovertemplate="<b>%{y}</b><br>€%{x:,.2f}bn<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Own Funds (EU KM1)", font=dict(size=15, color="#ffffff")),
        xaxis=dict(title="EUR billions", gridcolor="rgba(255,255,255,0.06)"),
        yaxis_title="",
        showlegend=False, height=300, **CHART_LAYOUT,
    )
    return fig


def fig_capital_ratios() -> go.Figure:
    if CAP_RATIOS.empty:
        return go.Figure()
    d = CAP_RATIOS.sort_values("value_pct", ascending=False)
    colors = [KBC_GREEN, ZANDERS_LIGHT, ZANDERS_BLUE]
    fig = go.Figure()
    for i, (_, row) in enumerate(d.iterrows()):
        fig.add_trace(go.Bar(
            x=[row.label], y=[row.value_pct],
            text=[f"{row.value_pct:.1f}%"], textposition="outside",
            textfont=dict(size=13, color=colors[i], weight="bold"),
            marker=dict(color=colors[i], cornerradius=6, line=dict(width=0)),
            name=row.label, showlegend=False,
            hovertemplate="<b>%{x}</b><br>%{y:.2f}%<extra></extra>",
            width=0.5,
        ))
    fig.add_hline(y=4.5, line_dash="dash", line_color=ACCENT_RED, line_width=2,
                  annotation=dict(text="CET1 min 4.5%", font=dict(size=10, color=ACCENT_RED),
                                  bgcolor="rgba(239,83,80,0.15)", borderpad=3))
    fig.add_hline(y=8.0, line_dash="dash", line_color=ACCENT_ORANGE, line_width=2,
                  annotation=dict(text="Total min 8%", font=dict(size=10, color=ACCENT_ORANGE),
                                  bgcolor="rgba(255,167,38,0.15)", borderpad=3))
    fig.update_layout(
        title=dict(text="Capital Ratios vs Regulatory Minimums", font=dict(size=15, color="#ffffff")),
        yaxis=dict(title="%", range=[0, max(d.value_pct) * 1.25], gridcolor="rgba(255,255,255,0.06)"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        showlegend=False, height=340, **CHART_LAYOUT,
    )
    return fig


def fig_rwa_breakdown() -> go.Figure:
    """Main risk-type bars (excluding 'of which' sub-items and Total)."""
    data = _main_risks[_main_risks.factNumeric.notna() & (_main_risks.factNumeric > 0)].copy()
    if data.empty:
        return go.Figure()
    data["value_bn"] = data.factNumeric / 1e9
    data = data.sort_values("value_bn", ascending=True)
    n = len(data)
    palette = [ACCENT_TEAL, ZANDERS_LIGHT, KBC_GREEN, ZANDERS_BLUE, ACCENT_PURPLE, ACCENT_ORANGE]
    colors = (palette * ((n // len(palette)) + 1))[:n]
    fig = go.Figure(go.Bar(
        x=data.value_bn, y=data.label, orientation="h",
        text=data.value_bn.apply(lambda v: f"€{v:,.1f}bn"),
        textposition="outside", textfont=dict(size=11, color="#E0E0E0"),
        marker=dict(color=colors, cornerradius=4, line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>€%{x:,.2f}bn<extra></extra>",
    ))
    # Add total line
    total = _all_risks[_all_risks.is_total]
    if not total.empty:
        tot_bn = total.factNumeric.values[0] / 1e9
        fig.add_vline(x=tot_bn, line_dash="dash", line_color=SUBTLE_GRAY, line_width=1.5,
                      annotation=dict(text=f"Total: €{tot_bn:,.1f}bn", font=dict(size=10, color=SUBTLE_GRAY),
                                      bgcolor="rgba(144,164,174,0.15)", borderpad=3))
    fig.update_layout(
        title=dict(text="TREA by Risk Type (EU OV1)", font=dict(size=15, color="#ffffff")),
        xaxis=dict(title="EUR billions", gridcolor="rgba(255,255,255,0.06)"),
        yaxis_title="",
        showlegend=False, height=380, **CHART_LAYOUT,
    )
    return fig


def fig_rwa_of_which() -> go.Figure:
    """'Of which' sub-breakdowns, shown with parent context."""
    data = _sub_risks[_sub_risks.factNumeric.notna() & (_sub_risks.factNumeric > 0)].copy()
    if data.empty:
        return go.Figure().update_layout(
            title="No 'of which' sub-items", **CHART_LAYOUT)
    data["value_bn"] = data.factNumeric / 1e9
    data["parent"] = data.label.map(_RWA_PARENT_MAP).fillna("")
    data["display"] = data.apply(
        lambda r: f"{r.parent[:25]}:<br>  {r.label[:35]}" if r.parent else r.label[:35], axis=1)
    data = data.sort_values("value_bn", ascending=True)

    # Color by parent category
    parents = data.parent.unique()
    parent_colors = {p: c for p, c in zip(parents, [ZANDERS_LIGHT, ACCENT_TEAL, KBC_GREEN,
                                                     ACCENT_PURPLE, ACCENT_ORANGE, ZANDERS_BLUE])}
    colors = [parent_colors.get(p, SUBTLE_GRAY) for p in data.parent]

    fig = go.Figure(go.Bar(
        x=data.value_bn, y=data.display, orientation="h",
        text=data.value_bn.apply(lambda v: f"€{v:,.1f}bn"),
        textposition="outside", textfont=dict(size=11, color="#E0E0E0"),
        marker=dict(
            color=colors, cornerradius=4,
            line=dict(width=1, color="rgba(255,255,255,0.15)"),
            pattern=dict(shape="/", solidity=0.15),
        ),
        hovertemplate="<b>%{y}</b><br>€%{x:,.2f}bn<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="TREA Sub-Breakdowns ('of which')", font=dict(size=15, color="#ffffff")),
        xaxis=dict(title="EUR billions", gridcolor="rgba(255,255,255,0.06)"),
        yaxis_title="",
        showlegend=False, height=380, **CHART_LAYOUT,
    )
    return fig


def fig_cr8_waterfall() -> go.Figure:
    data = _cr8.copy()
    data["short"] = data.rc.str.replace(r"^\d+\.\s+", "", regex=True)
    opening = data[data.short.str.contains("end of the previous", na=False)]
    closing = data[data.short.str.contains("end of the reporting", na=False)]
    flows = data[~data.short.str.contains("end of the", na=False)]

    labels, values, measures = [], [], []
    if not opening.empty:
        labels.append("Opening RWA")
        values.append(opening.factNumeric.values[0] / 1e9)
        measures.append("absolute")
    for _, r in flows.iterrows():
        labels.append(r.short[:25])
        values.append(r.factNumeric / 1e9)
        measures.append("relative")
    if not closing.empty:
        labels.append("Closing RWA")
        values.append(closing.factNumeric.values[0] / 1e9)
        measures.append("total")

    fig = go.Figure(go.Waterfall(
        x=labels, y=values, measure=measures,
        text=[f"€{v:+,.1f}bn" if m == "relative" else f"€{v:,.1f}bn"
              for v, m in zip(values, measures)],
        textposition="outside", textfont=dict(size=10, color="#E0E0E0"),
        increasing_marker_color=KBC_GREEN,
        decreasing_marker_color=ACCENT_RED,
        totals_marker_color=ZANDERS_BLUE,
        connector_line_color="rgba(255,255,255,0.15)",
    ))
    fig.update_layout(
        title=dict(text="Credit Risk RWEA Flows (EU CR8)", font=dict(size=15, color="#ffffff")),
        yaxis=dict(title="EUR billions", gridcolor="rgba(255,255,255,0.06)"),
        height=380,
        template="plotly_dark",
        font=dict(family="Inter, Segoe UI, sans-serif", size=12, color="#E0E0E0"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=20, t=50, b=70),
    )
    return fig


def fig_mr2_total() -> go.Figure:
    data = _mr2[_mr2.col_label.str.contains("Total RWEA|f\\.", na=False, regex=True)].copy()
    data["short"] = data.rc.str.replace(r"^\d+[ab]?\.\s+", "", regex=True)
    op = data[data.rc.str.contains("1\\. RWEA|1\\. RWEAs at previous", na=False, regex=True)]
    cl = data[data.rc.str.contains(
        r"8\.\s+RWEAs at the end of the disclosure period$", na=False, regex=True)]
    flows = data[~data.short.str.contains(
        "RWEA|Regulatory adjust|previous|end of the day|end of the disc",
        case=False, na=False)]

    labels, values, measures = [], [], []
    if not op.empty:
        labels.append("Opening MR RWA")
        values.append(op.factNumeric.values[0] / 1e9)
        measures.append("absolute")
    for _, r in flows.iterrows():
        labels.append(r.short[:25])
        values.append(r.factNumeric / 1e9)
        measures.append("relative")
    if not cl.empty:
        labels.append("Closing MR RWA")
        values.append(cl.factNumeric.values[0] / 1e9)
        measures.append("total")
    if not labels:
        return go.Figure()

    fig = go.Figure(go.Waterfall(
        x=labels, y=values, measure=measures,
        text=[f"€{v:+,.2f}bn" if m == "relative" else f"€{v:,.2f}bn"
              for v, m in zip(values, measures)],
        textposition="outside", textfont=dict(size=10, color="#E0E0E0"),
        increasing_marker_color=KBC_GREEN,
        decreasing_marker_color=ACCENT_RED,
        totals_marker_color=ZANDERS_BLUE,
        connector_line_color="rgba(255,255,255,0.15)",
    ))
    fig.update_layout(
        title=dict(text="Market Risk RWEA Flows (EU MR2-B)", font=dict(size=15, color="#ffffff")),
        yaxis=dict(title="EUR billions", gridcolor="rgba(255,255,255,0.06)"),
        height=380,
        template="plotly_dark",
        font=dict(family="Inter, Segoe UI, sans-serif", size=12, color="#E0E0E0"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=20, t=50, b=70),
    )
    return fig


def fig_irrbb() -> go.Figure:
    """IRRBB sensitivities as % of Tier 1 capital, with SOT threshold lines."""
    fig = go.Figure()
    if not IRR_EVE.empty and T1_ABS > 0:
        eve_pct = IRR_EVE.factNumeric / T1_ABS * 100
        fig.add_trace(go.Bar(
            x=IRR_EVE.rc, y=eve_pct,
            name="ΔEVE / T1", marker=dict(color=ZANDERS_LIGHT, cornerradius=4),
            text=eve_pct.apply(lambda v: f"{v:+.1f}%"),
            textposition="outside", textfont=dict(size=10, color="#E0E0E0"),
            hovertemplate="<b>%{x}</b><br>ΔEVE: %{y:+.2f}% of Tier 1<extra></extra>",
        ))
    if not IRR_NII.empty and T1_ABS > 0:
        nii_pct = IRR_NII.factNumeric / T1_ABS * 100
        fig.add_trace(go.Bar(
            x=IRR_NII.rc, y=nii_pct,
            name="ΔNII / T1", marker=dict(color=KBC_GREEN, cornerradius=4),
            text=nii_pct.apply(lambda v: f"{v:+.1f}%"),
            textposition="outside", textfont=dict(size=10, color="#E0E0E0"),
            hovertemplate="<b>%{x}</b><br>ΔNII: %{y:+.2f}% of Tier 1<extra></extra>",
        ))
    # SOT threshold lines (manual shape+annotation to avoid Plotly xref bug)
    for y_val, dash, color, label, x_pos, anchor, bg in [
        (-15, "dash", ACCENT_RED, "EVE SOT (−15% T1)", 1, "right", "rgba(239,83,80,0.15)"),
        (-5, "dot", ACCENT_ORANGE, "NII SOT (−5% T1)", 0, "left", "rgba(255,167,38,0.15)"),
    ]:
        fig.add_shape(type="line", xref="paper", yref="y",
                      x0=0, x1=1, y0=y_val, y1=y_val,
                      line=dict(color=color, width=2 if dash == "dash" else 1.5, dash=dash))
        fig.add_annotation(text=label, xref="paper", yref="y",
                           x=x_pos, y=y_val, xanchor=anchor, yanchor="bottom",
                           font=dict(size=10, color=color),
                           bgcolor=bg, borderpad=3, showarrow=False)
    # Determine y-axis range to show threshold lines
    all_vals = []
    if not IRR_EVE.empty and T1_ABS > 0:
        all_vals.extend((IRR_EVE.factNumeric / T1_ABS * 100).tolist())
    if not IRR_NII.empty and T1_ABS > 0:
        all_vals.extend((IRR_NII.factNumeric / T1_ABS * 100).tolist())
    y_min = min(min(all_vals, default=-15), -18)
    y_max = max(max(all_vals, default=5), 8)
    fig.update_layout(
        title=dict(text="IRRBB – Supervisory Outlier Test (% of Tier 1)", font=dict(size=15, color="#ffffff")),
        yaxis=dict(title="% of Tier 1 Capital", gridcolor="rgba(255,255,255,0.06)",
                   range=[y_min * 1.3, y_max * 1.3]),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=11)),
        height=420, **CHART_LAYOUT,
    )
    return fig


def fig_liquidity_gauges() -> go.Figure:
    fig = go.Figure()
    for val, title, col, dom_x in [
        (LCR_PCT, "LCR", KBC_GREEN, [0, 0.3]),
        (NSFR_PCT, "NSFR", ZANDERS_LIGHT, [0.35, 0.65]),
        (LEV_PCT, "Leverage", ACCENT_TEAL, [0.7, 1]),
    ]:
        mx = 250 if "LCR" in title else 200 if "NSFR" in title else 10
        thresh = 100 if title != "Leverage" else 3
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=val,
            number={"suffix": "%", "font": {"size": 26, "color": "#ffffff"}},
            title={"text": title, "font": {"size": 15, "color": "#B0BEC5"}},
            gauge={
                "axis": {"range": [0, mx], "tickfont": {"size": 10, "color": "#78909C"},
                         "tickcolor": "rgba(255,255,255,0.1)"},
                "bar": {"color": col, "thickness": 0.75},
                "bgcolor": "rgba(255,255,255,0.03)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, thresh], "color": "rgba(239,83,80,0.12)"},
                    {"range": [thresh, mx], "color": "rgba(0,200,83,0.08)"},
                ],
                "threshold": {"line": {"color": ACCENT_RED, "width": 2}, "value": thresh},
            },
            domain={"x": dom_x, "y": [0, 1]},
        ))
    fig.update_layout(
        height=270,
        margin=dict(l=20, r=20, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ── NMD Charts ─────────────────────────────────────────────────────────────────

# ── Leaf-level rows (non-overlapping sub-categories) ──────────────────────────
_RETAIL_CHILDREN = [
    "3. Stable deposits",
    "4. Less stable deposits",
]
_WHOLESALE_CHILDREN = [
    "6. Operational deposits all counterparties and deposits in networks of cooperative banks",
    "7. Non-operational deposits all counterparties",
    "8. Unsecured debt",
]
_LEAF_ROWS = _RETAIL_CHILDREN + _WHOLESALE_CHILDREN


def fig_deposit_sunburst() -> go.Figure:
    """Sunburst: Total Deposits → Retail / Wholesale → sub-categories."""
    uw = NMD_UW[NMD_UW.factNumeric.notna()].set_index("rc")
    if uw.empty:
        return go.Figure().update_layout(title="No deposit data")

    # Extract values
    ret = uw.loc["2. Retail deposits and deposits from small business customers, of which:", "factNumeric"] / 1e9
    ws = uw.loc["5. Unsecured wholesale funding", "factNumeric"] / 1e9
    stable = uw.loc["3. Stable deposits", "factNumeric"] / 1e9 if "3. Stable deposits" in uw.index else 0
    less_st = uw.loc["4. Less stable deposits", "factNumeric"] / 1e9 if "4. Less stable deposits" in uw.index else 0
    other_ret = ret - stable - less_st
    oper = uw.loc["6. Operational deposits all counterparties and deposits in networks of cooperative banks", "factNumeric"] / 1e9 if "6. Operational deposits all counterparties and deposits in networks of cooperative banks" in uw.index else 0
    non_oper = uw.loc["7. Non-operational deposits all counterparties", "factNumeric"] / 1e9 if "7. Non-operational deposits all counterparties" in uw.index else 0
    unsec_debt = uw.loc["8. Unsecured debt", "factNumeric"] / 1e9 if "8. Unsecured debt" in uw.index else 0
    total = ret + ws

    ids =     ["Total",    "Retail",  "Wholesale",  "Stable NMD", "Less Stable NMD", "Other Retail", "Operational",  "Non-Operational", "Unsecured Debt"]
    labels =  [f"Total<br>€{total:,.0f}bn", f"Retail & SME<br>€{ret:,.0f}bn", f"Wholesale<br>€{ws:,.0f}bn",
               f"Stable NMD<br>€{stable:,.0f}bn", f"Less Stable<br>€{less_st:,.0f}bn", f"Other Retail<br>€{other_ret:,.0f}bn",
               f"Operational<br>€{oper:,.0f}bn", f"Non-Operational<br>€{non_oper:,.0f}bn", f"Unsecured Debt<br>€{unsec_debt:,.0f}bn"]
    parents = ["",          "Total",   "Total",      "Retail",     "Retail",          "Retail",       "Wholesale",    "Wholesale",       "Wholesale"]
    values =  [total,       ret,        ws,           stable,       less_st,           other_ret,      oper,           non_oper,          unsec_debt]
    colors =  ["rgba(0,0,0,0)", ZANDERS_LIGHT, ZANDERS_BLUE,
               KBC_GREEN, ACCENT_ORANGE, ACCENT_TEAL,
               ACCENT_PURPLE, "#26A69A", SUBTLE_GRAY]

    fig = go.Figure(go.Sunburst(
        ids=ids, labels=labels, parents=parents, values=values,
        branchvalues="total",
        marker=dict(colors=colors, line=dict(color="rgba(0,0,0,0.4)", width=1.5)),
        textfont=dict(size=11, color="white"),
        hovertemplate="<b>%{label}</b><br>%{percentRoot:.1%} of total<extra></extra>",
        insidetextorientation="radial",
    ))
    fig.update_layout(
        title=dict(text="Deposit Hierarchy – Unweighted (Period T)",
                   font=dict(size=15, color="#ffffff")),
        height=480, margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def fig_nmd_unweighted_vs_weighted() -> go.Figure:
    """UW vs W comparison using only leaf-level (non-overlapping) categories."""
    # Use leaf rows + compute Other Retail as implied
    uw_leaf = NMD_UW[NMD_UW.rc.isin(_LEAF_ROWS) & NMD_UW.factNumeric.notna()].copy()
    w_leaf = NMD_W[NMD_W.rc.isin(_LEAF_ROWS) & NMD_W.factNumeric.notna()].copy()

    # Add implied "Other Retail" row
    ret_uw = NMD_UW[NMD_UW.rc.str.contains("Retail", na=False)]
    stable_uw = NMD_UW[NMD_UW.rc == "3. Stable deposits"]
    ls_uw = NMD_UW[NMD_UW.rc == "4. Less stable deposits"]
    if len(ret_uw) and len(stable_uw) and len(ls_uw):
        other_val = ret_uw.factNumeric.values[0] - stable_uw.factNumeric.values[0] - ls_uw.factNumeric.values[0]
        if other_val > 0:
            other_row = stable_uw.iloc[[0]].copy()
            other_row["rc"] = "Other Retail"
            other_row["short"] = "Other Retail"
            other_row["factNumeric"] = other_val
            uw_leaf = pd.concat([uw_leaf, other_row], ignore_index=True)

    # Weighted "Other Retail"
    ret_w = NMD_W[NMD_W.rc.str.contains("Retail", na=False)]
    stable_w = NMD_W[NMD_W.rc == "3. Stable deposits"]
    ls_w = NMD_W[NMD_W.rc == "4. Less stable deposits"]
    if len(ret_w) and len(stable_w) and len(ls_w):
        other_w_val = ret_w.factNumeric.values[0] - stable_w.factNumeric.values[0] - ls_w.factNumeric.values[0]
        if other_w_val > 0:
            other_w_row = stable_w.iloc[[0]].copy()
            other_w_row["rc"] = "Other Retail"
            other_w_row["short"] = "Other Retail"
            other_w_row["factNumeric"] = other_w_val
            w_leaf = pd.concat([w_leaf, other_w_row], ignore_index=True)

    if uw_leaf.empty and w_leaf.empty:
        return go.Figure().update_layout(title="No deposit data")

    # Ensure short names
    uw_leaf["short"] = uw_leaf["short"].fillna(uw_leaf.rc.map(_SHORT))
    w_leaf["short"] = w_leaf["short"].fillna(w_leaf.rc.map(_SHORT))

    # Order: retail children first, then wholesale children
    order = ["Stable NMD", "Less Stable NMD", "Other Retail",
             "Operational Deposits", "Non-Operational Deposits", "Unsecured Debt"]
    uw_leaf["sort"] = uw_leaf.short.apply(lambda s: order.index(s) if s in order else 99)
    w_leaf["sort"] = w_leaf.short.apply(lambda s: order.index(s) if s in order else 99)
    uw_leaf = uw_leaf.sort_values("sort")
    w_leaf = w_leaf.sort_values("sort")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=uw_leaf.short, y=uw_leaf.factNumeric / 1e9,
        name="Unweighted (gross)", marker=dict(color=ZANDERS_LIGHT, cornerradius=4),
        text=uw_leaf.factNumeric.apply(lambda v: f"€{v/1e9:,.1f}bn"),
        textposition="outside", textfont=dict(size=10, color="#E0E0E0"),
        hovertemplate="<b>%{x}</b><br>Unweighted: €%{y:,.2f}bn<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=w_leaf.short, y=w_leaf.factNumeric / 1e9,
        name="Weighted (outflow)", marker=dict(color=KBC_GREEN, cornerradius=4),
        text=w_leaf.factNumeric.apply(lambda v: f"€{v/1e9:,.1f}bn"),
        textposition="outside", textfont=dict(size=10, color="#E0E0E0"),
        hovertemplate="<b>%{x}</b><br>Weighted: €%{y:,.2f}bn<extra></extra>",
    ))

    # Add parent group annotations
    fig.add_vrect(x0=-0.5, x1=2.5, fillcolor=ZANDERS_LIGHT, opacity=0.04, line_width=0,
                  annotation=dict(text="← Retail & SME →", font=dict(size=10, color="#78909C"),
                                  yref="paper", y=0.98, showarrow=False))
    fig.add_vrect(x0=2.5, x1=5.5, fillcolor=ZANDERS_BLUE, opacity=0.04, line_width=0,
                  annotation=dict(text="← Wholesale →", font=dict(size=10, color="#78909C"),
                                  yref="paper", y=0.98, showarrow=False))
    fig.update_layout(
        title=dict(text="LCR Outflows – Sub-Category Detail (Period T)",
                   font=dict(size=15, color="#ffffff")),
        yaxis=dict(title="EUR billions", gridcolor="rgba(255,255,255,0.06)"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=11)),
        height=480, **CHART_LAYOUT,
    )
    return fig


def fig_nmd_outflow_rates() -> go.Figure:
    # Use only leaf rows (no parent totals) to avoid misleading rates
    leaf_plus_parent = _LEAF_ROWS + [
        "2. Retail deposits and deposits from small business customers, of which:",
        "5. Unsecured wholesale funding",
    ]
    uw = NMD_UW[NMD_UW.factNumeric.notna() & (NMD_UW.factNumeric > 0) & NMD_UW.rc.isin(leaf_plus_parent)].set_index("rc")
    w = NMD_W[NMD_W.factNumeric.notna() & NMD_W.rc.isin(leaf_plus_parent)].set_index("rc")
    common = uw.index.intersection(w.index)
    if common.empty:
        return go.Figure().update_layout(title="No outflow rate data")
    rates = (w.loc[common, "factNumeric"] / uw.loc[common, "factNumeric"] * 100).reset_index()
    rates.columns = ["rc", "rate"]
    rates["short"] = rates.rc.map(_SHORT)
    rates = rates.sort_values("rate")
    fig = go.Figure(go.Bar(
        x=rates.rate, y=rates.short, orientation="h",
        text=rates.rate.apply(lambda v: f"{v:.1f}%"),
        textposition="outside", textfont=dict(size=11, color="#E0E0E0"),
        marker=dict(
            color=[KBC_GREEN if r < 10 else ACCENT_ORANGE if r < 30 else ACCENT_RED
                   for r in rates.rate],
            cornerradius=4,
        ),
        hovertemplate="<b>%{y}</b><br>Outflow rate: %{x:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="LCR Outflow Rates by Deposit Type (Period T)", font=dict(size=15, color="#ffffff")),
        xaxis=dict(title="Outflow Rate (%)", range=[0, max(rates.rate) * 1.3],
                   gridcolor="rgba(255,255,255,0.06)"),
        yaxis_title="", showlegend=False, height=380, **CHART_LAYOUT,
    )
    return fig


def fig_nmd_trend(weighted: bool = False) -> go.Figure:
    """Stacked bar chart: Stable + Less Stable NMD across periods.

    Retail & SME is the sum of the two, shown as a total annotation.
    """
    wt = "Weighted" if weighted else "Unweighted"
    # Only use the sub-components (Stable & Less Stable), not the Retail total
    _sub_rows = ["3. Stable deposits", "4. Less stable deposits"]
    d = _nmd_ts[
        (_nmd_ts.weight == wt)
        & _nmd_ts.period.isin(["T-3", "T-2", "T-1", "T"])
        & _nmd_ts.rc.isin(_sub_rows)
    ]
    if d.empty:
        return go.Figure().update_layout(title="No trend data")
    d = d.copy()
    d["value_bn"] = d.factNumeric / 1e9
    period_order = ["T-3", "T-2", "T-1", "T"]
    d["period"] = pd.Categorical(d.period, categories=period_order, ordered=True)
    d = d.sort_values("period")

    colors = {"Stable NMD": KBC_GREEN, "Less Stable NMD": ACCENT_ORANGE}
    fig = go.Figure()
    for label in ["Stable NMD", "Less Stable NMD"]:
        sub = d[d.short == label]
        fig.add_trace(go.Bar(
            x=sub.period.astype(str), y=sub.value_bn, name=label,
            marker=dict(color=colors[label], cornerradius=3),
            text=sub.value_bn.apply(lambda v: f"€{v:,.1f}bn"),
            textposition="inside", textfont=dict(size=10, color="white"),
            hovertemplate="<b>%{x}</b><br>" + label + ": €%{y:,.2f}bn<extra></extra>",
        ))

    # Add total annotation on top of each stacked bar
    totals = d.groupby("period", observed=True)["value_bn"].sum()
    for p in period_order:
        if p in totals.index:
            fig.add_annotation(
                x=p, y=totals[p], text=f"€{totals[p]:,.1f}bn",
                showarrow=False, font=dict(size=11, color="#B0BEC5"),
                yshift=14,
            )

    lbl = "Weighted" if weighted else "Unweighted"
    fig.update_layout(
        title=dict(
            text=f"NMD {'Outflow' if weighted else 'Volume'} Trend – {lbl} (EU LIQ1)",
            font=dict(size=15, color="#ffffff")),
        xaxis=dict(title="Period", gridcolor="rgba(255,255,255,0.06)"),
        yaxis=dict(title="EUR billions", gridcolor="rgba(255,255,255,0.06)"),
        barmode="stack",
        legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=11)),
        height=400, **CHART_LAYOUT,
    )
    return fig


# ── Annual report deposit insight charts ──────────────────────────────────────

def fig_ar_geo_treemap() -> go.Figure:
    d = _AR_GEO.copy()
    total_yoy = (_AR_GEO_TOTAL_EX_GC_2024_MN / _AR_GEO_TOTAL_EX_GC_2023_MN - 1) * 100

    ids = ["Total"] + d["label"].tolist()
    labels = [f"Total (excl. Group Centre)<br>€{_AR_GEO_TOTAL_EX_GC_2024_MN/1e3:,.1f}bn"] + [
        f"{r.label}<br>€{r.v2024/1e3:,.1f}bn" for _, r in d.iterrows()
    ]
    parents = [""] + d["parent"].tolist()
    values = [_AR_GEO_TOTAL_EX_GC_2024_MN] + d["v2024"].tolist()
    shares = [100.0] + d["share_pct"].tolist()
    yoy = [total_yoy] + d["yoy_pct"].tolist()

    color_map = {"Business Unit": ZANDERS_LIGHT, "IM Country": KBC_GREEN}
    colors = ["rgba(0,0,0,0)"] + [color_map.get(g, SUBTLE_GRAY) for g in d["group"]]

    fig = go.Figure(go.Treemap(
        ids=ids,
        labels=labels,
        parents=parents,
        values=values,
        customdata=list(zip(shares, yoy)),
        branchvalues="total",
        marker=dict(colors=colors, line=dict(color="rgba(0,0,0,0.35)", width=1)),
        textfont=dict(size=11, color="white"),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Value: €%{value:,.0f}m<br>"
            "Share of total: %{customdata[0]:.1f}%<br>"
            "YoY: %{customdata[1]:+.1f}%<extra></extra>"
        ),
    ))
    fig.update_layout(
        title=dict(text="Deposit Geography (IFRS, 2024, excl. Group Centre)", font=dict(size=15, color="#ffffff")),
        height=470,
        margin=dict(l=10, r=10, t=55, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def fig_ar_geo_growth() -> go.Figure:
    d = _AR_GEO.copy()
    d["display"] = d.apply(
        lambda r: f"{r['label']} (IM)" if r["group"] == "IM Country" else r["label"], axis=1
    )
    d = d.sort_values("yoy_pct")
    fig = go.Figure(go.Bar(
        x=d["yoy_pct"],
        y=d["display"],
        orientation="h",
        marker=dict(
            color=[KBC_GREEN if v >= 0 else ACCENT_RED for v in d["yoy_pct"]],
            cornerradius=4,
        ),
        text=d["yoy_pct"].apply(lambda v: f"{v:+.1f}%"),
        textposition="outside",
        textfont=dict(size=11, color="#E0E0E0"),
        hovertemplate="<b>%{y}</b><br>YoY growth: %{x:+.2f}%<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="YoY Growth by Geography (2024 vs 2023)", font=dict(size=15, color="#ffffff")),
        xaxis=dict(title="Growth (%)", gridcolor="rgba(255,255,255,0.06)"),
        yaxis_title="",
        showlegend=False,
        height=470,
        **CHART_LAYOUT,
    )
    return fig


def fig_ar_product_mix_donut() -> go.Figure:
    d = _AR_PRODUCTS.copy()
    color_map = {
        "Demand deposits": ZANDERS_LIGHT,
        "Savings accounts": KBC_GREEN,
        "Time deposits": ACCENT_ORANGE,
        "Debt securities\n(incl. savings certificates)": ZANDERS_BLUE,
    }
    fig = go.Figure(go.Pie(
        labels=d["label"],
        values=d["v2024"],
        hole=0.48,
        marker=dict(colors=[color_map.get(lbl, SUBTLE_GRAY) for lbl in d["label"]],
                    line=dict(color="rgba(0,0,0,0.35)", width=1)),
        customdata=d["share_pct"],
        texttemplate="%{percent}",
        textfont=dict(size=12, color="white"),
        hovertemplate="<b>%{label}</b><br>€%{value:,.0f}m<br>Share: %{customdata:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Deposit Product Mix (2024)", font=dict(size=15, color="#ffffff")),
        height=430,
        legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5, font=dict(size=10)),
        margin=dict(l=10, r=10, t=55, b=35),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def fig_ar_product_yoy() -> go.Figure:
    d = _AR_PRODUCTS.copy()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=d["label"],
        y=d["v2023"] / 1e3,
        name="2023",
        marker=dict(color=SUBTLE_GRAY, cornerradius=4),
        text=d["v2023"].apply(lambda v: f"€{v/1e3:,.1f}bn"),
        textposition="outside",
        textfont=dict(size=10, color="#B0BEC5"),
        hovertemplate="<b>%{x}</b><br>2023: €%{y:,.2f}bn<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=d["label"],
        y=d["v2024"] / 1e3,
        name="2024",
        marker=dict(color=ZANDERS_LIGHT, cornerradius=4),
        text=d["yoy_pct"].apply(lambda v: f"{v:+.1f}% YoY"),
        textposition="outside",
        textfont=dict(size=10, color="#E0E0E0"),
        hovertemplate="<b>%{x}</b><br>2024: €%{y:,.2f}bn<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Product Volumes: 2024 vs 2023", font=dict(size=15, color="#ffffff")),
        yaxis=dict(title="EUR billions", gridcolor="rgba(255,255,255,0.06)"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
        height=430,
        **CHART_LAYOUT,
    )
    return fig


def fig_ar_stability_profile() -> go.Figure:
    on_demand_pct = _AR_CUSTOMER_FUNDING_ON_DEMAND_BN / _AR_CUSTOMER_FUNDING_TOTAL_BN * 100
    d = pd.DataFrame(
        [
            {"metric": "Deposit guarantee coverage", "strong_pct": _AR_DGS_COVERAGE_PCT},
            {"metric": "Stable retail/SME share", "strong_pct": _AR_STABLE_RETAIL_SME_PCT},
            {"metric": "On-demand customer funding", "strong_pct": on_demand_pct},
        ]
    )
    d["rest_pct"] = 100 - d["strong_pct"]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=d["strong_pct"],
        y=d["metric"],
        orientation="h",
        name="Primary share",
        marker=dict(color=KBC_GREEN, cornerradius=4),
        text=d["strong_pct"].apply(lambda v: f"{v:.1f}%"),
        textposition="inside",
        textfont=dict(size=11, color="white"),
        hovertemplate="<b>%{y}</b><br>%{x:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=d["rest_pct"],
        y=d["metric"],
        orientation="h",
        name="Remainder",
        marker=dict(color="rgba(144,164,174,0.35)", cornerradius=4),
        hovertemplate="<b>%{y}</b><br>Remainder: %{x:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Deposit Stability Profile (2024)", font=dict(size=15, color="#ffffff")),
        xaxis=dict(title="Share of customer deposits / funding (%)", range=[0, 100],
                   gridcolor="rgba(255,255,255,0.06)"),
        yaxis_title="",
        barmode="stack",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
        height=360,
        **CHART_LAYOUT,
    )
    return fig


# fig_deposit_composition removed – replaced by fig_deposit_sunburst above


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    f"""
    <div style="background: linear-gradient(135deg, {ZANDERS_BLUE} 0%, {ZANDERS_LIGHT} 60%, {KBC_GREEN} 100%);
                border-radius: 0 0 14px 14px; padding: 1.8rem 2rem; margin: -1rem -1rem 1.5rem -1rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.4);">
        <h2 style="color: white; margin: 0; font-weight: 700; font-size: 1.6rem;
                   letter-spacing: -0.02em; font-family: 'Inter', sans-serif;">
            🏦 KBC Group – Pillar 3 Disclosure Dashboard
        </h2>
        <p style="color: rgba(255,255,255,0.7); margin: 0.3rem 0 0 0; font-size: 0.85rem;
                  font-weight: 400; letter-spacing: 0.02em;">
            EBA Pillar 3 Data Hub (P3DH) · Mapped &amp; Visualised by Zanders
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(
    f"References: [KBC Annual Report 2024 (PDF)]({_AR_REPORT_URL})"
)

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_overview, tab_nmd, tab_deposit_insights, tab_explorer = st.tabs([
    "📊  Overview",
    "🏦  NMD & Deposits",
    "🧭  Deposit Insights",
    "🔍  Data Explorer",
])

# ── TAB 1: Overview ─────────────────────────────────────────────────────────
with tab_overview:
    # KPI row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("CET1 Ratio", f"{CET1_PCT:.2f}%")
    c2.metric("Tier 1 Ratio", f"{T1_PCT:.2f}%")
    c3.metric("Total Capital", f"{TC_PCT:.2f}%")
    c4.metric("Total RWA", f"€{RWA_BN:,.1f}bn")
    c5.metric("Leverage", f"{LEV_PCT:.2f}%")
    c6.metric("LCR / NSFR", f"{LCR_PCT:.0f}% / {NSFR_PCT:.0f}%")

    st.markdown("")
    st.divider()

    # Capital Adequacy
    st.subheader("Capital Adequacy")
    st.caption(
        "EU KM1 – Key Metrics  ·  "
        "Left: absolute own-funds amounts (CET1 ⊂ Tier 1 ⊂ Total Capital).  "
        "Right: regulatory ratio = own funds ÷ RWA; dashed lines show minimum requirements."
    )
    left, right = st.columns([5, 7])
    left.plotly_chart(fig_capital_stack(), use_container_width=True)
    right.plotly_chart(fig_capital_ratios(), use_container_width=True)

    # RWA
    st.subheader("Risk-Weighted Exposure Amounts")
    st.caption(
        "EU OV1 – Left chart shows the **additive** risk categories that sum to Total TREA (dashed line). "
        "Right chart shows 'of which' sub-breakdowns (hatched bars) — these are **included in** their parent, not additional. "
        "Read them as: 'Of the €104.6bn Credit Risk, €49.2bn comes from A-IRB, €34.9bn from Standardised, etc.'"
    )
    left, right = st.columns(2)
    left.plotly_chart(fig_rwa_breakdown(), use_container_width=True)
    right.plotly_chart(fig_rwa_of_which(), use_container_width=True)

    # RWA flows
    st.subheader("RWEA Flow Analysis")
    st.caption(
        "Waterfall charts show how RWA moved from the previous reporting period to the current one. "
        "Green bars = increases, red bars = decreases. The first bar is the opening balance, the last is the closing balance."
    )
    left, right = st.columns(2)
    left.plotly_chart(fig_cr8_waterfall(), use_container_width=True)
    right.plotly_chart(fig_mr2_total(), use_container_width=True)

    # IRRBB
    st.subheader("Interest Rate Risk in the Banking Book")
    st.caption(
        "EU IRRBB1 – Sensitivities expressed as **% of Tier 1 capital** (€{t1:.1f}bn) to match the EBA Supervisory Outlier Test (SOT) format.  ·  "
        "EVE SOT threshold: −15% of Tier 1 (red dashed). NII SOT threshold: −5% of Tier 1 (orange dotted).  ·  "
        "Bars below a threshold line would trigger enhanced supervisory scrutiny.".format(t1=T1_ABS/1e9)
    )
    st.plotly_chart(fig_irrbb(), use_container_width=True)

    # Liquidity
    st.subheader("Liquidity Overview")
    st.caption(
        "LCR (Liquidity Coverage Ratio): high-quality liquid assets ÷ net 30-day stress outflows — must exceed 100%.  ·  "
        "NSFR (Net Stable Funding Ratio): available stable funding ÷ required stable funding — must exceed 100%.  ·  "
        "Leverage Ratio: Tier 1 capital ÷ total exposure — must exceed 3%. Red zone = below minimum."
    )
    st.plotly_chart(fig_liquidity_gauges(), use_container_width=True)

# ── TAB 2: NMD & Deposits ────────────────────────────────────────────────────
with tab_nmd:
    # NMD KPIs
    stable_uw = NMD_UW[NMD_UW.rc.str.contains("Stable deposits", na=False)]
    less_stable_uw = NMD_UW[NMD_UW.rc.str.contains("Less stable", na=False)]
    retail_uw = NMD_UW[NMD_UW.rc.str.contains("Retail", na=False)]
    wholesale_uw = NMD_UW[NMD_UW.rc.str.contains("Unsecured wholesale funding", na=False)]
    stable_w = NMD_W[NMD_W.rc.str.contains("Stable deposits", na=False)]
    less_stable_w = NMD_W[NMD_W.rc.str.contains("Less stable", na=False)]

    s_val = stable_uw.factNumeric.values[0] / 1e9 if len(stable_uw) else 0
    ls_val = less_stable_uw.factNumeric.values[0] / 1e9 if len(less_stable_uw) else 0
    ret_val = retail_uw.factNumeric.values[0] / 1e9 if len(retail_uw) else 0
    ws_val = wholesale_uw.factNumeric.values[0] / 1e9 if len(wholesale_uw) else 0
    total_deposits = ret_val + ws_val
    other_retail = ret_val - s_val - ls_val  # retail deposits not classified as Stable/Less Stable
    s_w = stable_w.factNumeric.values[0] / 1e9 if len(stable_w) else 0
    ls_w = less_stable_w.factNumeric.values[0] / 1e9 if len(less_stable_w) else 0

    s_rate = (s_w / s_val * 100) if s_val else 0
    ls_rate = (ls_w / ls_val * 100) if ls_val else 0

    # Row 1: deposit totals
    st.caption("All values are 12-month LCR rolling averages (unweighted), not point-in-time balances")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Deposits (UW)", f"€{total_deposits:,.1f}bn",
              help="Retail & SME + Unsecured Wholesale. LCR 12-month avg ≈ annual report YE balance.")
    c2.metric("Retail & SME", f"€{ret_val:,.1f}bn",
              help="Row 2 in EU LIQ1 — includes Stable, Less Stable, and other retail deposits.")
    c3.metric("Unsecured Wholesale", f"€{ws_val:,.1f}bn",
              help="Row 5 in EU LIQ1 — operational + non-operational + unsecured debt.")
    c4.metric("Retail / Wholesale Split", f"{ret_val/total_deposits*100:.0f}% / {ws_val/total_deposits*100:.0f}%")

    # Row 2: NMD detail
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Stable NMD", f"€{s_val:,.1f}bn",
              help="Portion of retail deposits with low run-off risk; can be modelled with longer behavioral maturity.")
    c2.metric("Less Stable NMD", f"€{ls_val:,.1f}bn",
              help="Retail deposits with higher run-off risk (e.g. high-value, internet-only).")
    c3.metric("Other Retail", f"€{other_retail:,.1f}bn",
              help=f"Retail & SME (€{ret_val:,.1f}bn) minus Stable (€{s_val:,.1f}bn) minus Less Stable (€{ls_val:,.1f}bn). Likely term deposits or other categories.")
    c4.metric("Stable Outflow Rate", f"{s_rate:.1f}%")
    c5.metric("Less Stable Outflow Rate", f"{ls_rate:.1f}%")

    st.divider()

    # Charts row 1
    st.subheader("Deposit Breakdown")
    st.caption(
        "EU LIQ1 (K_73.00.c) – **Left**: sunburst showing the deposit hierarchy: Total €241bn → Retail & SME / Wholesale → leaf sub-categories. "
        "Click a segment to zoom in.  ·  "
        "**Right**: gross volumes (blue) vs regulatory stressed outflow (green) for each **non-overlapping** sub-category."
    )
    left, right = st.columns([5, 7])
    left.plotly_chart(fig_deposit_sunburst(), use_container_width=True)
    right.plotly_chart(fig_nmd_unweighted_vs_weighted(), use_container_width=True)

    # Explanation box
    col_left, col_right = st.columns(2)
    with col_left:
        st.info(
            "**Unweighted vs Weighted – what does it mean?**\n\n"
            "In the LCR framework, **unweighted** values are the gross (nominal) deposit amounts "
            "reported by KBC. **Weighted** values are the *regulatory outflow amounts* after applying "
            "EBA-prescribed run-off rates that reflect the likelihood of depositors withdrawing "
            "funds during a 30-day stress scenario.\n\n"
            "• **Stable NMD** — low outflow rate (typically 5%): regulators assume most funds stay.\n"
            "• **Less Stable NMD** — higher rate (typically 10–15%): more expected outflows under stress.\n\n"
            "The *outflow rate* = Weighted ÷ Unweighted. A lower rate means the deposits are "
            "considered stickier and more favourable for the bank's LCR.",
            icon="💡",
        )
    with col_right:
        st.info(
            "**Stable NMDs & Behavioral Maturity**\n\n"
            "Non-Maturing Deposits have no contractual maturity — in theory they could be withdrawn "
            "overnight. However, **stable NMDs** are the portion to which banks may assign a "
            "*behavioral repricing maturity longer than overnight* under EBA IRRBB guidelines.\n\n"
            "Banks model the 'core' component of stable deposits with maturities up to **5 years**, "
            "reflecting observed depositor behavior. This is critical for IRRBB because it determines "
            "how much duration risk the bank carries on the liability side.\n\n"
            "• **Stable** → long behavioral maturity → lower IRRBB sensitivity\n"
            "• **Less stable** → shorter maturity assumed → higher repricing risk\n\n"
            "The split directly impacts both the EVE and NII sensitivity metrics shown in the "
            "Overview tab.",
            icon="📐",
        )

    # Charts row 2: outflow rates
    st.subheader("Outflow Rates")
    st.caption(
        "Outflow rate = Weighted ÷ Unweighted. A lower rate means the deposit type is considered more 'sticky'. "
        "Green = low runoff risk (<10%), orange = moderate (10–30%), red = high (>30%). "
        "Stable NMD at ~5% is extremely favourable; unsecured debt at 100% must be fully covered."
    )
    st.plotly_chart(fig_nmd_outflow_rates(), use_container_width=True)

    # Charts row 3: stacked bar trends (UW and W side by side)
    st.subheader("NMD Trends across Periods")
    st.caption(
        "Stacked bars show the Stable (green) and Less Stable (orange) NMD split over time. "
        "Total shown above each bar. Left = gross volumes; Right = net outflow after applying run-off rates. "
        "A growing green share means more deposits are classified as stable — good for both LCR and IRRBB."
    )
    left, right = st.columns(2)
    left.plotly_chart(fig_nmd_trend(weighted=False), use_container_width=True)
    right.plotly_chart(fig_nmd_trend(weighted=True), use_container_width=True)

    # Raw data – collapsed
    with st.expander("📋 NMD Raw Data", expanded=False):
        d = _lcr[_lcr.rc.isin(_DEPOSIT_ROWS)].copy()
        d["Category"] = d.rc.map(_SHORT)
        d["Period"] = d.period
        d["Type"] = d.weight
        d["Value (€bn)"] = d.factNumeric.apply(lambda v: f"{v/1e9:,.2f}" if pd.notna(v) else "")
        st.dataframe(
            d[["Category", "Period", "Type", "Value (€bn)"]].sort_values(
                ["Category", "Type", "Period"]),
            use_container_width=True, hide_index=True, height=500,
        )

# ── TAB 3: Deposit Insights ──────────────────────────────────────────────────
with tab_deposit_insights:
    st.subheader("Annual Report Deposit Insights (IFRS)")
    st.caption(
        "Source: KBC Annual Report 2024  ·  Note 2.3 (Balance-sheet info by segment), "
        "Note 4.1 (financial liabilities), and Liquidity section.  "
        "Values are year-end IFRS balances (not LCR rolling averages)."
    )
    st.markdown(
        f"Verify source document: [KBC Annual Report 2024 (PDF)]({_AR_REPORT_URL})"
    )

    with st.expander("🔎 Source references (click to verify)", expanded=False):
        st.markdown(
            f"- Geographic split and segment deposit products: [Note 2.3 (PDF p.280, printed p.278)]({_AR_REPORT_URL}#page=280) "
            "(Group Centre excluded in this dashboard view, because it mainly reflects debt securities)\n"
            f"- Deposit liabilities and customer deposit subtotal: [Note 4.1 (PDF p.298, printed p.296)]({_AR_REPORT_URL}#page=298)\n"
            f"- Funding mix and customer-funding maturity buckets: [Liquidity section (PDF p.87, printed p.85)]({_AR_REPORT_URL}#page=87)\n"
            f"- Deposit Guarantee coverage (56%) and stable retail/SME share (86%): [PDF p.306, printed p.304]({_AR_REPORT_URL}#page=306)"
        )

    geo_scope_delta_bn = (_AR_GEO_TOTAL_EX_GC_2024_MN - _AR_GEO_TOTAL_EX_GC_2023_MN) / 1e3
    cust_delta_bn = (_AR_CUSTOMER_DEPOSITS_2024_MN - _AR_CUSTOMER_DEPOSITS_2023_MN) / 1e3
    savings_cert_2024_bn = 1_250 / 1e3
    savings_cert_delta_bn = (1_250 - 79) / 1e3

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Geo Scope (excl. Group Centre)",
        f"€{_AR_GEO_TOTAL_EX_GC_2024_MN/1e3:,.1f}bn",
        delta=f"+€{geo_scope_delta_bn:,.1f}bn vs 2023",
        help="Belgium BU + Czech BU + International Markets BU only.",
    )
    c2.metric(
        "Customer Deposits",
        f"€{_AR_CUSTOMER_DEPOSITS_2024_MN/1e3:,.1f}bn",
        delta=f"+€{cust_delta_bn:,.1f}bn vs 2023",
    )
    c3.metric(
        "Deposit Product Core",
        "Demand / Savings / Time",
        help="Demand: €110.1bn, Savings: €74.4bn, Time: €43.0bn (2024).",
    )
    c4.metric(
        "Savings Certificates",
        f"€{savings_cert_2024_bn:,.2f}bn",
        delta=f"+€{savings_cert_delta_bn:,.2f}bn vs 2023",
    )

    st.divider()

    st.subheader("1) Geographic Deposit Split")
    st.caption(
        "2024 IFRS deposit balances across business units with drill-down into "
        "International Markets (Hungary, Slovakia, Bulgaria). "
        "Group Centre is excluded because it is mainly debt securities."
    )
    st.caption(
        f"Reference: [Annual Report Note 2.3 – Balance-sheet info by segment (PDF p.280, printed p.278)]({_AR_REPORT_URL}#page=280)"
    )
    left, right = st.columns([7, 5])
    left.plotly_chart(fig_ar_geo_treemap(), use_container_width=True)
    right.plotly_chart(fig_ar_geo_growth(), use_container_width=True)

    st.subheader("2) Deposit Product Mix")
    st.caption(
        "Composition of deposits by product in 2024 and comparison to 2023 "
        "(demand deposits, savings accounts, time deposits, and debt securities)."
    )
    st.caption(
        f"References: [Note 2.3 (PDF p.280, printed p.278)]({_AR_REPORT_URL}#page=280)  ·  "
        f"[Note 4.1 – liabilities breakdown (PDF p.298, printed p.296)]({_AR_REPORT_URL}#page=298)"
    )
    left, right = st.columns([5, 7])
    left.plotly_chart(fig_ar_product_mix_donut(), use_container_width=True)
    right.plotly_chart(fig_ar_product_yoy(), use_container_width=True)

    st.subheader("3) Deposit Stability Indicators")
    st.caption(
        "Annual report indicators linked to stability of the funding base."
    )
    st.caption(
        f"References: [Liquidity funding mix table (PDF p.87, printed p.85)]({_AR_REPORT_URL}#page=87)  ·  "
        f"[Deposit Guarantee coverage + stable retail/SME share (PDF p.306, printed p.304)]({_AR_REPORT_URL}#page=306)"
    )
    on_demand_pct = _AR_CUSTOMER_FUNDING_ON_DEMAND_BN / _AR_CUSTOMER_FUNDING_TOTAL_BN * 100
    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Deposit Guarantee Coverage",
        f"{_AR_DGS_COVERAGE_PCT:.1f}%",
        help=f"Approx. €{_AR_CUSTOMER_DEPOSITS_2024_MN*_AR_DGS_COVERAGE_PCT/100/1e3:,.1f}bn of customer deposits.",
    )
    c2.metric(
        "Stable Retail/SME Share",
        f"{_AR_STABLE_RETAIL_SME_PCT:.1f}%",
        help=f"Approx. €{_AR_CUSTOMER_DEPOSITS_2024_MN*_AR_STABLE_RETAIL_SME_PCT/100/1e3:,.1f}bn of customer deposits.",
    )
    c3.metric(
        "On-demand Customer Funding",
        f"{on_demand_pct:.1f}%",
        help="€154bn on-demand out of €229bn customer funding in liquidity maturity table (2024).",
    )
    st.plotly_chart(fig_ar_stability_profile(), use_container_width=True)

    with st.expander("📋 Annual Report Deposit Data (2024 vs 2023)", expanded=False):
        geo = _AR_GEO[["label", "group", "v2024", "v2023", "share_pct", "yoy_pct"]].copy()
        geo.columns = ["Geography", "Type", "2024 (€m)", "2023 (€m)", "Share 2024 (%)", "YoY (%)"]
        geo["2024 (€bn)"] = geo["2024 (€m)"] / 1e3
        geo["2023 (€bn)"] = geo["2023 (€m)"] / 1e3
        geo["Share 2024 (%)"] = geo["Share 2024 (%)"].map(lambda v: f"{v:,.1f}")
        geo["YoY (%)"] = geo["YoY (%)"].map(lambda v: f"{v:+.1f}")

        prod = _AR_PRODUCTS.copy()
        prod.columns = ["Product", "2024 (€m)", "2023 (€m)", "YoY (%)", "Share 2024 (%)"]
        prod["2024 (€bn)"] = prod["2024 (€m)"] / 1e3
        prod["2023 (€bn)"] = prod["2023 (€m)"] / 1e3
        prod["YoY (%)"] = prod["YoY (%)"].map(lambda v: f"{v:+.1f}")
        prod["Share 2024 (%)"] = prod["Share 2024 (%)"].map(lambda v: f"{v:,.1f}")

        left, right = st.columns(2)
        left.dataframe(
            geo[["Geography", "Type", "2024 (€bn)", "2023 (€bn)", "Share 2024 (%)", "YoY (%)"]],
            use_container_width=True,
            hide_index=True,
        )
        right.dataframe(
            prod[["Product", "2024 (€bn)", "2023 (€bn)", "Share 2024 (%)", "YoY (%)"]],
            use_container_width=True,
            hide_index=True,
        )

# ── TAB 4: Data Explorer ─────────────────────────────────────────────────────
with tab_explorer:
    st.subheader("Data Explorer")
    st.caption("Browse all mapped EBA datapoints")

    groups = sorted(DF["group"].unique())
    c_sel, c_filt = st.columns([1, 2])
    group = c_sel.selectbox("Template Group", groups, index=0)
    text_filter = c_filt.text_input("Filter rows", placeholder="Search row labels…")

    subset = DF[DF["group"] == group].copy()
    if text_filter:
        subset = subset[subset["row_label"].str.contains(text_filter, case=False, na=False)]

    display = subset[["datapoint", "row_label", "col_label", "factValue", "unit"]].copy()
    display.columns = ["Datapoint", "Row", "Column", "Value", "Unit"]
    display["Value"] = display["Value"].apply(
        lambda v: f"{float(v):,.2f}" if pd.notna(pd.to_numeric(v, errors="coerce")) else v
    )
    with st.expander(f"📋 {group} – {len(display)} rows", expanded=True):
        st.dataframe(display, use_container_width=True, hide_index=True, height=600)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("")
st.divider()
st.markdown(
    f"""
    <div style="text-align: center; padding: 0.5rem 0; opacity: 0.5; font-size: 0.78rem;">
        Source: EBA Pillar 3 Data Hub – KBC Group &nbsp;·&nbsp;
        Annual report: <a href="{_AR_REPORT_URL}" target="_blank">KBC Annual Report 2024</a> &nbsp;·&nbsp;
        Mapping: EBA Annotated Table Layouts v4.1 &nbsp;·&nbsp;
        Dashboard: <span style="color: {ZANDERS_LIGHT}; font-weight: 600;">Zanders</span>
    </div>
    """,
    unsafe_allow_html=True,
)
