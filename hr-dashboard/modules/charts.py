# =============================================================================
# modules/charts.py
# Generación de gráficos Plotly con tema dark mode premium
# =============================================================================

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import COLORS

# ── Tema base para todos los gráficos ────────────────────────────────────────
PLOTLY_THEME = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"family": "Inter, sans-serif", "color": COLORS["text_primary"], "size": 12},
    "colorway": COLORS["chart_palette"],
    "margin": {"l": 20, "r": 20, "t": 50, "b": 20},
    "legend": {
        "bgcolor": "rgba(0,0,0,0)",
        "font": {"color": COLORS["text_secondary"]},
    },
    "xaxis": {
        "gridcolor": "rgba(255,255,255,0.05)",
        "linecolor": "rgba(255,255,255,0.1)",
        "tickfont": {"color": COLORS["text_secondary"]},
        "title": {"font": {"color": COLORS["text_secondary"]}},
    },
    "yaxis": {
        "gridcolor": "rgba(255,255,255,0.05)",
        "linecolor": "rgba(255,255,255,0.1)",
        "tickfont": {"color": COLORS["text_secondary"]},
        "title": {"font": {"color": COLORS["text_secondary"]}},
    },
}


def _apply_theme(fig: go.Figure, title: str = "") -> go.Figure:
    """Aplica el tema dark mode a cualquier figura Plotly."""
    fig.update_layout(
        title={
            "text": title,
            "font": {"size": 15, "color": COLORS["text_primary"], "family": "Inter, sans-serif"},
            "x": 0,
            "xanchor": "left",
            "pad": {"l": 5},
        },
        **PLOTLY_THEME,
    )
    return fig


def chart_headcount_por_depto(df_depto: pd.DataFrame) -> go.Figure:
    """Barras horizontales — Headcount por departamento."""
    if df_depto.empty:
        return _empty_chart("Sin datos de departamento")

    fig = px.bar(
        df_depto,
        x="Headcount",
        y="Departamento",
        orientation="h",
        color="Headcount",
        color_continuous_scale=[[0, COLORS["accent_dark"]], [1, COLORS["accent_light"]]],
        text="Headcount",
    )
    fig.update_traces(
        textposition="outside",
        textfont={"color": COLORS["text_primary"]},
        marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>Headcount: %{x}<extra></extra>",
    )
    fig.update_coloraxes(showscale=False)
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return _apply_theme(fig, "👥 Headcount por Departamento")


def chart_distribucion_donut(df: pd.DataFrame, col_nombre: str, col_valor: str, titulo: str) -> go.Figure:
    """Gráfico donut genérico para distribuciones."""
    if df.empty:
        return _empty_chart(f"Sin datos de {titulo}")

    fig = go.Figure(
        go.Pie(
            labels=df[col_nombre],
            values=df[col_valor],
            hole=0.55,
            textinfo="label+percent",
            textfont={"size": 11, "color": COLORS["text_primary"]},
            marker={"colors": COLORS["chart_palette"], "line": {"color": COLORS["bg_primary"], "width": 2}},
            hovertemplate="<b>%{label}</b><br>Cantidad: %{value}<br>%{percent}<extra></extra>",
        )
    )
    return _apply_theme(fig, titulo)


def chart_tendencia_ingresos(df_tendencia: pd.DataFrame) -> go.Figure:
    """Línea de tendencia — Ingresos por mes."""
    if df_tendencia.empty:
        return _empty_chart("Sin datos de tendencia temporal")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_tendencia["Mes"],
            y=df_tendencia["Ingresos"],
            mode="lines+markers+text",
            name="Ingresos",
            line={"color": COLORS["accent"], "width": 3},
            marker={"size": 8, "color": COLORS["accent_light"], "line": {"color": COLORS["accent"], "width": 2}},
            text=df_tendencia["Ingresos"],
            textposition="top center",
            textfont={"color": COLORS["text_primary"], "size": 11},
            fill="tozeroy",
            fillcolor=f"rgba(59,130,246,0.1)",
            hovertemplate="<b>%{x}</b><br>Ingresos: %{y}<extra></extra>",
        )
    )
    return _apply_theme(fig, "📈 Tendencia de Ingresos (últimos 12 meses)")


def chart_ausentismo_por_depto(df_aus: pd.DataFrame) -> go.Figure:
    """Barras — Días de ausentismo por departamento."""
    if df_aus.empty:
        return _empty_chart("Sin datos de ausentismo")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_aus["Departamento"],
            y=df_aus["Dias_Total"],
            name="Días totales",
            marker_color=COLORS["warning"],
            marker_line_width=0,
            text=df_aus["Dias_Total"],
            textposition="outside",
            textfont={"color": COLORS["text_primary"]},
            hovertemplate="<b>%{x}</b><br>Días ausentes: %{y}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_aus["Departamento"],
            y=df_aus["Dias_Promedio"],
            mode="markers",
            name="Promedio por empleado",
            marker={"symbol": "diamond", "size": 10, "color": COLORS["danger"]},
            yaxis="y2",
            hovertemplate="<b>%{x}</b><br>Promedio: %{y:.1f} días<extra></extra>",
        )
    )
    fig.update_layout(
        yaxis2={
            "overlaying": "y",
            "side": "right",
            "showgrid": False,
            "tickfont": {"color": COLORS["text_secondary"]},
            "title": {"text": "Promedio/empleado", "font": {"color": COLORS["text_secondary"]}},
        },
        barmode="group",
        legend={"orientation": "h", "y": -0.2},
    )
    return _apply_theme(fig, "📅 Ausentismo por Departamento")


def chart_motivos_ausentismo(df_motivos: pd.DataFrame) -> go.Figure:
    """Barras horizontales — Top motivos de ausentismo."""
    if df_motivos.empty:
        return _empty_chart("Sin datos de motivos de ausentismo")

    fig = px.bar(
        df_motivos,
        x="Dias_Ausentismo",
        y="Motivo_Ausentismo",
        orientation="h",
        color="Dias_Ausentismo",
        color_continuous_scale=[[0, COLORS["success"]], [0.5, COLORS["warning"]], [1, COLORS["danger"]]],
        text="Dias_Ausentismo",
    )
    fig.update_traces(
        textposition="outside",
        textfont={"color": COLORS["text_primary"]},
        marker_line_width=0,
        hovertemplate="<b>%{y}</b><br>Días: %{x}<extra></extra>",
    )
    fig.update_coloraxes(showscale=False)
    return _apply_theme(fig, "🏷️ Top Motivos de Ausentismo (días)")


def chart_motivos_baja(df_bajas: pd.DataFrame) -> go.Figure:
    """Barras — Motivos de baja."""
    if df_bajas.empty:
        return _empty_chart("Sin datos de motivos de baja")

    fig = px.bar(
        df_bajas.head(10),
        x="Cantidad",
        y="Motivo_Baja",
        orientation="h",
        color="Cantidad",
        color_continuous_scale=[[0, COLORS["accent_dark"]], [1, COLORS["danger"]]],
        text="Cantidad",
    )
    fig.update_traces(
        textposition="outside",
        textfont={"color": COLORS["text_primary"]},
        marker_line_width=0,
    )
    fig.update_coloraxes(showscale=False)
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    return _apply_theme(fig, "🚪 Motivos de Baja")


def chart_antiguedad_buckets(df_ant: pd.DataFrame) -> go.Figure:
    """Barras — Distribución por rango de antigüedad."""
    if df_ant.empty:
        return _empty_chart("Sin datos de antigüedad")

    fig = px.bar(
        df_ant,
        x="Rango_Antiguedad",
        y="Empleados",
        color="Empleados",
        color_continuous_scale=[[0, COLORS["accent_dark"]], [1, COLORS["success"]]],
        text="Empleados",
    )
    fig.update_traces(
        textposition="outside",
        textfont={"color": COLORS["text_primary"]},
        marker_line_width=0,
        hovertemplate="<b>%{x}</b><br>Empleados: %{y}<extra></extra>",
    )
    fig.update_coloraxes(showscale=False)
    return _apply_theme(fig, "⏳ Distribución por Antigüedad")


def chart_nomina_por_depto(df_nomina: pd.DataFrame) -> go.Figure:
    """Barras — Nómina mensual por departamento."""
    if df_nomina.empty:
        return _empty_chart("Sin datos de nómina")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_nomina["Departamento"],
            y=df_nomina["Nomina_Total"],
            name="Nómina Total",
            marker_color=COLORS["success"],
            marker_line_width=0,
            text=[f"${v:,.0f}" for v in df_nomina["Nomina_Total"]],
            textposition="outside",
            textfont={"color": COLORS["text_primary"], "size": 10},
            hovertemplate="<b>%{x}</b><br>Nómina: $%{y:,.0f}<extra></extra>",
        )
    )
    return _apply_theme(fig, "💰 Nómina Mensual por Departamento")


def chart_headcount_ubicacion(df_ubic: pd.DataFrame) -> go.Figure:
    """Donut — Headcount por ubicación."""
    if df_ubic.empty:
        return _empty_chart("Sin datos de ubicación")
    return chart_distribucion_donut(df_ubic, "Ubicacion", "Headcount", "📍 Headcount por Ubicación")


def _empty_chart(mensaje: str) -> go.Figure:
    """Gráfico vacío con mensaje informativo."""
    fig = go.Figure()
    fig.add_annotation(
        text=f"ℹ️ {mensaje}",
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font={"size": 14, "color": COLORS["text_muted"]},
    )
    return _apply_theme(fig)
