"""
KBC Pillar 3 Data Hub – Streamlit Dashboard

Run with:  uv run streamlit run dashboard.py
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
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
ZANDERS_BLUE = "#003366"
ZANDERS_LIGHT = "#0066aa"
KBC_GREEN = "#00A651"
ACCENT_TEAL = "#17a2b8"
ACCENT_RED = "#cc3333"
ACCENT_ORANGE = "#e67e22"

CHART_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Segoe UI, sans-serif", size=12),
    margin=dict(l=10, r=20, t=45, b=30),
    plot_bgcolor="white",
)


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

# ══════════════════════════════════════════════════════════════════════════════
# 2. RWA OVERVIEW (EU OV1, k_60.00.a)
# ══════════════════════════════════════════════════════════════════════════════
_ov1 = DF[
    (DF.file == "k_60.00.a")
    & (DF.col_label.str.contains("TREA|a\\.", na=False, regex=True))
].copy()
_ov1["rc"] = _clean(_ov1["row_label"])
_main_risks = _ov1[_ov1.rc.str.match(r"^\d+\.\s")].copy()
_main_risks["label"] = _main_risks.rc.str.replace(r"^\d+\.\s+", "", regex=True)

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
# CHART BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def fig_capital_stack() -> go.Figure:
    if CAP_AMOUNTS.empty:
        return go.Figure()
    d = CAP_AMOUNTS.sort_values("value_bn")
    fig = go.Figure(go.Bar(
        x=d.value_bn, y=d.label, orientation="h",
        text=d.value_bn.apply(lambda v: f"€{v:,.1f}bn"),
        textposition="outside", textfont=dict(size=11),
        marker_color=[KBC_GREEN, ZANDERS_LIGHT, ZANDERS_BLUE],
    ))
    fig.update_layout(
        title=dict(text="Own Funds (EU KM1)", font=dict(size=14)),
        xaxis_title="EUR billions", yaxis_title="",
        showlegend=False, height=280, **CHART_LAYOUT,
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
            textfont=dict(size=12, color=colors[i]),
            marker_color=colors[i], name=row.label, showlegend=False,
        ))
    fig.add_hline(y=4.5, line_dash="dot", line_color=ACCENT_RED, line_width=1.5,
                  annotation=dict(text="CET1 min 4.5%", font=dict(size=10, color=ACCENT_RED)))
    fig.add_hline(y=8.0, line_dash="dot", line_color=ACCENT_ORANGE, line_width=1.5,
                  annotation=dict(text="Total min 8%", font=dict(size=10, color=ACCENT_ORANGE)))
    fig.update_layout(
        title=dict(text="Capital Ratios vs Regulatory Minimums", font=dict(size=14)),
        yaxis=dict(title="%", range=[0, max(d.value_pct) * 1.25]),
        showlegend=False, height=340, **CHART_LAYOUT,
    )
    return fig


def fig_rwa_breakdown() -> go.Figure:
    data = _main_risks[_main_risks.factNumeric.notna() & (_main_risks.factNumeric > 0)].copy()
    if data.empty:
        return go.Figure()
    data["value_bn"] = data.factNumeric / 1e9
    data = data.sort_values("value_bn", ascending=True)
    n = len(data)
    colors = px.colors.sequential.Teal_r[:n] if n <= len(px.colors.sequential.Teal_r) else None
    fig = go.Figure(go.Bar(
        x=data.value_bn, y=data.label, orientation="h",
        text=data.value_bn.apply(lambda v: f"€{v:,.1f}bn"),
        textposition="outside", textfont=dict(size=11),
        marker_color=colors,
    ))
    fig.update_layout(
        title=dict(text="TREA by Risk Type (EU OV1)", font=dict(size=14)),
        xaxis_title="EUR billions", yaxis_title="",
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
        textposition="outside", textfont=dict(size=10),
        increasing_marker_color=KBC_GREEN,
        decreasing_marker_color=ACCENT_RED,
        totals_marker_color=ZANDERS_BLUE,
        connector_line_color="#ccc",
    ))
    fig.update_layout(
        title=dict(text="Credit Risk RWEA Flows (EU CR8)", font=dict(size=14)),
        yaxis_title="EUR billions", height=380,
        template="plotly_white", font=dict(family="Segoe UI, sans-serif", size=12),
        plot_bgcolor="white", margin=dict(l=10, r=20, t=45, b=70),
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
        textposition="outside", textfont=dict(size=10),
        increasing_marker_color=KBC_GREEN,
        decreasing_marker_color=ACCENT_RED,
        totals_marker_color=ZANDERS_BLUE,
    ))
    fig.update_layout(
        title=dict(text="Market Risk RWEA Flows (EU MR2-B)", font=dict(size=14)),
        yaxis_title="EUR billions", height=380,
        template="plotly_white", font=dict(family="Segoe UI, sans-serif", size=12),
        plot_bgcolor="white", margin=dict(l=10, r=20, t=45, b=70),
    )
    return fig


def fig_irrbb() -> go.Figure:
    fig = go.Figure()
    if not IRR_EVE.empty:
        fig.add_trace(go.Bar(
            x=IRR_EVE.rc, y=IRR_EVE.factNumeric / 1e6,
            name="ΔEVE", marker_color=ZANDERS_BLUE,
            text=IRR_EVE.factNumeric.apply(lambda v: f"€{v/1e6:,.0f}m"),
            textposition="outside", textfont=dict(size=10),
        ))
    if not IRR_NII.empty:
        fig.add_trace(go.Bar(
            x=IRR_NII.rc, y=IRR_NII.factNumeric / 1e6,
            name="ΔNII", marker_color=KBC_GREEN,
            text=IRR_NII.factNumeric.apply(lambda v: f"€{v/1e6:,.0f}m"),
            textposition="outside", textfont=dict(size=10),
        ))
    fig.update_layout(
        title=dict(text="IRRBB Sensitivities – EVE vs NII (EU IRRBB1)", font=dict(size=14)),
        yaxis_title="EUR millions", barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=380, **CHART_LAYOUT,
    )
    return fig


def fig_liquidity_gauges() -> go.Figure:
    fig = go.Figure()
    for val, title, col, dom_x in [
        (LCR_PCT, "LCR", KBC_GREEN, [0, 0.3]),
        (NSFR_PCT, "NSFR", ZANDERS_BLUE, [0.35, 0.65]),
        (LEV_PCT, "Leverage", ACCENT_TEAL, [0.7, 1]),
    ]:
        mx = 250 if "LCR" in title else 200 if "NSFR" in title else 10
        thresh = 100 if title != "Leverage" else 3
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=val,
            number={"suffix": "%", "font": {"size": 22}},
            title={"text": title, "font": {"size": 14}},
            gauge={
                "axis": {"range": [0, mx], "tickfont": {"size": 10}},
                "bar": {"color": col},
                "steps": [
                    {"range": [0, thresh], "color": "#ffe0e0"},
                    {"range": [thresh, mx], "color": "#e0ffe0"},
                ],
                "threshold": {"line": {"color": ACCENT_RED, "width": 2}, "value": thresh},
            },
            domain={"x": dom_x, "y": [0, 1]},
        ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=10))
    return fig


# ── NMD Charts ─────────────────────────────────────────────────────────────────

def fig_nmd_unweighted_vs_weighted() -> go.Figure:
    uw = NMD_UW[NMD_UW.factNumeric.notna()].copy()
    w = NMD_W[NMD_W.factNumeric.notna()].copy()
    if uw.empty and w.empty:
        return go.Figure().update_layout(title="No NMD data available")
    fig = go.Figure()
    if not uw.empty:
        fig.add_trace(go.Bar(
            x=uw.short, y=uw.factNumeric / 1e9,
            name="Unweighted (gross)", marker_color=ZANDERS_LIGHT,
            text=uw.factNumeric.apply(lambda v: f"€{v/1e9:,.1f}bn"),
            textposition="outside", textfont=dict(size=10),
        ))
    if not w.empty:
        fig.add_trace(go.Bar(
            x=w.short, y=w.factNumeric / 1e9,
            name="Weighted (net outflow)", marker_color=KBC_GREEN,
            text=w.factNumeric.apply(lambda v: f"€{v/1e9:,.1f}bn"),
            textposition="outside", textfont=dict(size=10),
        ))
    fig.update_layout(
        title=dict(text="LCR Deposit Outflows – Unweighted vs Weighted (Period T)",
                   font=dict(size=14)),
        yaxis_title="EUR billions", barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=420, **CHART_LAYOUT,
    )
    return fig


def fig_nmd_outflow_rates() -> go.Figure:
    uw = NMD_UW[NMD_UW.factNumeric.notna() & (NMD_UW.factNumeric > 0)].set_index("rc")
    w = NMD_W[NMD_W.factNumeric.notna()].set_index("rc")
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
        textposition="outside", textfont=dict(size=11),
        marker_color=[KBC_GREEN if r < 10 else ACCENT_ORANGE if r < 30 else ACCENT_RED
                      for r in rates.rate],
    ))
    fig.update_layout(
        title=dict(text="LCR Outflow Rates by Deposit Type (Period T)", font=dict(size=14)),
        xaxis=dict(title="Outflow Rate (%)", range=[0, max(rates.rate) * 1.3]),
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
            marker_color=colors[label],
            text=sub.value_bn.apply(lambda v: f"€{v:,.1f}bn"),
            textposition="inside", textfont=dict(size=10, color="white"),
        ))

    # Add total annotation on top of each stacked bar
    totals = d.groupby("period", observed=True)["value_bn"].sum()
    for p in period_order:
        if p in totals.index:
            fig.add_annotation(
                x=p, y=totals[p], text=f"€{totals[p]:,.1f}bn",
                showarrow=False, font=dict(size=11, color=ZANDERS_BLUE),
                yshift=12,
            )

    lbl = "Weighted" if weighted else "Unweighted"
    fig.update_layout(
        title=dict(
            text=f"NMD {'Outflow' if weighted else 'Volume'} Trend – {lbl} (EU LIQ1)",
            font=dict(size=14)),
        xaxis_title="Period", yaxis_title="EUR billions",
        barmode="stack",
        legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=400, **CHART_LAYOUT,
    )
    return fig


def fig_deposit_composition() -> go.Figure:
    d = NMD_UW[NMD_UW.factNumeric.notna() & NMD_UW.rc.isin(_DEPOSIT_ROWS)].copy()
    if d.empty:
        return go.Figure().update_layout(title="No data")
    fig = go.Figure(go.Pie(
        labels=d.short, values=d.factNumeric / 1e9,
        textinfo="label+percent", textfont=dict(size=11),
        marker=dict(colors=[KBC_GREEN, ZANDERS_BLUE, ACCENT_TEAL,
                            ZANDERS_LIGHT, ACCENT_ORANGE, "#8ecae6", "#219ebc"]),
        hole=0.35,
    ))
    fig.update_layout(
        title=dict(text="Deposit Composition – Unweighted (Period T)", font=dict(size=14)),
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5,
                    font=dict(size=10)),
        height=420, margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(
    f"""
    <div style="background: linear-gradient(135deg, {ZANDERS_BLUE}, {ZANDERS_LIGHT});
                border-radius: 0 0 8px 8px; padding: 1.2rem 1.5rem; margin-bottom: 1.5rem;">
        <h2 style="color: white; margin: 0; font-weight: 700;">
            KBC Group – Pillar 3 Disclosure Dashboard
        </h2>
        <p style="color: rgba(255,255,255,0.75); margin: 0; font-size: 0.85rem;">
            EBA Pillar 3 Data Hub (P3DH) – Mapped &amp; Visualised
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_overview, tab_nmd, tab_explorer = st.tabs(["📊 Overview", "🏦 NMD & Deposits", "🔍 Data Explorer"])

# ── TAB 1: Overview ───────────────────────────────────────────────────────────
with tab_overview:
    # KPI row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("CET1 Ratio", f"{CET1_PCT:.2f}%")
    c2.metric("Tier 1 Ratio", f"{T1_PCT:.2f}%")
    c3.metric("Total Capital", f"{TC_PCT:.2f}%")
    c4.metric("Total RWA", f"€{RWA_BN:,.1f}bn")
    c5.metric("Leverage", f"{LEV_PCT:.2f}%")
    c6.metric("LCR / NSFR", f"{LCR_PCT:.0f}% / {NSFR_PCT:.0f}%")

    st.divider()

    # Capital Adequacy
    st.subheader("Capital Adequacy")
    st.caption("EU KM1 – Key Metrics")
    left, right = st.columns([5, 7])
    left.plotly_chart(fig_capital_stack(), use_container_width=True)
    right.plotly_chart(fig_capital_ratios(), use_container_width=True)

    # RWA
    st.subheader("Risk-Weighted Exposure Amounts")
    left, right = st.columns(2)
    left.plotly_chart(fig_rwa_breakdown(), use_container_width=True)
    right.plotly_chart(fig_cr8_waterfall(), use_container_width=True)

    # Market Risk + IRRBB
    st.subheader("Market Risk & IRRBB")
    left, right = st.columns(2)
    left.plotly_chart(fig_mr2_total(), use_container_width=True)
    right.plotly_chart(fig_irrbb(), use_container_width=True)

    # Liquidity
    st.subheader("Liquidity Overview")
    st.plotly_chart(fig_liquidity_gauges(), use_container_width=True)

# ── TAB 2: NMD & Deposits ────────────────────────────────────────────────────
with tab_nmd:
    # NMD KPIs
    stable_uw = NMD_UW[NMD_UW.rc.str.contains("Stable deposits", na=False)]
    less_stable_uw = NMD_UW[NMD_UW.rc.str.contains("Less stable", na=False)]
    retail_uw = NMD_UW[NMD_UW.rc.str.contains("Retail", na=False)]
    stable_w = NMD_W[NMD_W.rc.str.contains("Stable deposits", na=False)]
    less_stable_w = NMD_W[NMD_W.rc.str.contains("Less stable", na=False)]

    s_val = stable_uw.factNumeric.values[0] / 1e9 if len(stable_uw) else 0
    ls_val = less_stable_uw.factNumeric.values[0] / 1e9 if len(less_stable_uw) else 0
    ret_val = retail_uw.factNumeric.values[0] / 1e9 if len(retail_uw) else 0
    s_w = stable_w.factNumeric.values[0] / 1e9 if len(stable_w) else 0
    ls_w = less_stable_w.factNumeric.values[0] / 1e9 if len(less_stable_w) else 0

    s_rate = (s_w / s_val * 100) if s_val else 0
    ls_rate = (ls_w / ls_val * 100) if ls_val else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Retail & SME (UW)", f"€{ret_val:,.1f}bn")
    c2.metric("Stable NMD (UW)", f"€{s_val:,.1f}bn")
    c3.metric("Less Stable (UW)", f"€{ls_val:,.1f}bn")
    c4.metric("Stable Outflow Rate", f"{s_rate:.1f}%")
    c5.metric("Less Stable Rate", f"{ls_rate:.1f}%")
    c6.metric("NMD Total (UW)", f"€{s_val + ls_val:,.1f}bn")

    st.divider()

    # Charts row 1
    st.subheader("Deposit Breakdown")
    st.caption("EU LIQ1 (K_73.00.c) – LCR outflow detail")
    left, right = st.columns([7, 5])
    left.plotly_chart(fig_nmd_unweighted_vs_weighted(), use_container_width=True)
    right.plotly_chart(fig_deposit_composition(), use_container_width=True)

    # Explanation box
    st.info(
        "**Unweighted vs Weighted – what does it mean?**\n\n"
        "In the LCR framework, **unweighted** values are the gross (nominal) deposit amounts "
        "reported by KBC. **Weighted** values are the *regulatory outflow amounts* after applying "
        "EBA-prescribed run-off rates that reflect the likelihood of depositors withdrawing "
        "funds during a 30-day stress scenario.\n\n"
        "• **Stable NMD** (e.g. insured retail deposits in long-standing relationships) receive "
        "a low outflow rate (typically 5%), meaning regulators assume most funds stay.\n"
        "• **Less Stable NMD** (e.g. high-value or internet-only deposits) get a higher rate "
        "(typically 10-15%), implying more expected outflows under stress.\n\n"
        "The *outflow rate* = Weighted ÷ Unweighted. A lower rate means the deposits are "
        "considered stickier and more favourable for the bank's LCR.",
        icon="💡",
    )

    # Charts row 2: outflow rates
    st.subheader("Outflow Rates")
    st.plotly_chart(fig_nmd_outflow_rates(), use_container_width=True)

    # Charts row 3: stacked bar trends (UW and W side by side)
    st.subheader("NMD Trends across Periods")
    st.caption("Stable + Less Stable NMD stacked per quarter (Retail & SME total shown above bars)")
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

# ── TAB 3: Data Explorer ─────────────────────────────────────────────────────
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
st.divider()
st.caption(
    "Source: EBA Pillar 3 Data Hub – KBC Group  ·  "
    "Mapping: EBA Annotated Table Layouts v4.1  ·  "
    "Dashboard: Zanders"
)
