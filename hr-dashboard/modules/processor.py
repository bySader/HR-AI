# =============================================================================
# modules/processor.py
# Cálculo de KPIs y métricas de RRHH
# =============================================================================

import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import ALERT_THRESHOLDS, WORKING_DAYS_PER_MONTH
from modules.types import DashboardFilters, KpiMetric


def apply_filters(df: pd.DataFrame, filters: DashboardFilters) -> pd.DataFrame:
    """
    Aplica filtros dinámicos al DataFrame.

    Args:
        df: DataFrame completo
        filters: dict con claves opcionales:
            - departamentos: list[str]
            - ubicaciones: list[str]
            - estatus: list[str]
            - tipos_contrato: list[str]
            - generos: list[str]
            - niveles: list[str]
            - fecha_ingreso_desde: pd.Timestamp
            - fecha_ingreso_hasta: pd.Timestamp
    """
    filtered = df.copy()

    if filters.get("departamentos"):
        filtered = filtered[filtered["Departamento"].isin(filters["departamentos"])]

    if filters.get("ubicaciones"):
        filtered = filtered[filtered["Ubicacion"].isin(filters["ubicaciones"])]

    if filters.get("estatus"):
        filtered = filtered[filtered["Estatus"].isin(filters["estatus"])]

    if filters.get("tipos_contrato") and "Tipo_Contrato" in filtered.columns:
        filtered = filtered[filtered["Tipo_Contrato"].isin(filters["tipos_contrato"])]

    if filters.get("generos") and "Genero" in filtered.columns:
        filtered = filtered[filtered["Genero"].isin(filters["generos"])]

    if filters.get("niveles") and "Nivel_Jerarquico" in filtered.columns:
        filtered = filtered[filtered["Nivel_Jerarquico"].isin(filters["niveles"])]

    if filters.get("fecha_ingreso_desde") and "Fecha_Ingreso" in filtered.columns:
        filtered = filtered[filtered["Fecha_Ingreso"] >= filters["fecha_ingreso_desde"]]

    if filters.get("fecha_ingreso_hasta") and "Fecha_Ingreso" in filtered.columns:
        filtered = filtered[filtered["Fecha_Ingreso"] <= filters["fecha_ingreso_hasta"]]

    return filtered


def calculate_kpis(df: pd.DataFrame) -> dict[str, KpiMetric]:
    """
    Calcula los KPIs principales de RRHH.

    Returns:
        dict con métricas y sus metadatos (valor, estado, delta, descripción)
    """
    total_filas = len(df)
    activos = df[df["Estatus"] == "Activo"]
    bajas = df[df["Estatus"] == "Baja"]
    suspendidos = df[df["Estatus"] == "Suspendido"]

    # ── Headcount ────────────────────────────────────────────────────────────
    headcount = len(activos)

    # ── Altas del período (empleados ingresados en el último mes) ────────────
    hoy = pd.Timestamp.today()
    hace_30_dias = hoy - pd.Timedelta(days=30)
    altas = 0
    if "Fecha_Ingreso" in df.columns and pd.api.types.is_datetime64_any_dtype(df["Fecha_Ingreso"]):
        altas = len(activos[activos["Fecha_Ingreso"] >= hace_30_dias])

    # ── Bajas del período (último mes) ───────────────────────────────────────
    bajas_periodo = 0
    if "Fecha_Baja" in df.columns and pd.api.types.is_datetime64_any_dtype(df["Fecha_Baja"]):
        bajas_periodo = len(df[df["Fecha_Baja"] >= hace_30_dias])
    else:
        bajas_periodo = len(bajas)

    # ── Tasa de rotación ─────────────────────────────────────────────────────
    headcount_promedio = max(total_filas, 1)
    rotacion_pct = round((len(bajas) / headcount_promedio) * 100, 2)
    rotacion_estado = (
        "danger" if rotacion_pct >= ALERT_THRESHOLDS["rotacion_pct"]
        else "warning" if rotacion_pct >= ALERT_THRESHOLDS["rotacion_pct"] * 0.7
        else "success"
    )

    # ── Tasa de ausentismo ───────────────────────────────────────────────────
    dias_ausentes_total = df["Dias_Ausentismo"].sum() if "Dias_Ausentismo" in df.columns else 0
    dias_laborables_total = headcount * WORKING_DAYS_PER_MONTH
    ausentismo_pct = round(
        (dias_ausentes_total / max(dias_laborables_total, 1)) * 100, 2
    )
    ausentismo_estado = (
        "danger" if ausentismo_pct >= ALERT_THRESHOLDS["ausentismo_pct"] * 1.5
        else "warning" if ausentismo_pct >= ALERT_THRESHOLDS["ausentismo_pct"]
        else "success"
    )

    # ── Costo de nómina ──────────────────────────────────────────────────────
    nomina_total = activos["Salario"].sum() if "Salario" in activos.columns else 0

    # ── Promedio de antigüedad ───────────────────────────────────────────────
    antiguedad_promedio = 0
    if "Antiguedad_Anos" in activos.columns:
        antiguedad_promedio = round(activos["Antiguedad_Anos"].mean(), 1)
    elif "Fecha_Ingreso" in activos.columns and pd.api.types.is_datetime64_any_dtype(activos["Fecha_Ingreso"]):
        hoy = pd.Timestamp.today()
        antiguedad_promedio = round(
            ((hoy - activos["Fecha_Ingreso"]).dt.days / 365.25).mean(), 1
        )

    # ── Salario promedio ─────────────────────────────────────────────────────
    salario_promedio = round(activos["Salario"].mean(), 0) if "Salario" in activos.columns else 0

    return {
        "headcount": {
            "valor": headcount,
            "label": "Headcount Activos",
            "icono": "👥",
            "estado": "neutral",
            "formato": "entero",
            "descripcion": f"{len(suspendidos)} suspendidos · {len(bajas)} bajas totales",
        },
        "rotacion_pct": {
            "valor": rotacion_pct,
            "label": "Tasa de Rotación",
            "icono": "🔄",
            "estado": rotacion_estado,
            "formato": "porcentaje",
            "descripcion": f"Umbral alerta: {ALERT_THRESHOLDS['rotacion_pct']}%",
            "umbral": ALERT_THRESHOLDS["rotacion_pct"],
        },
        "ausentismo_pct": {
            "valor": ausentismo_pct,
            "label": "Tasa de Ausentismo",
            "icono": "📅",
            "estado": ausentismo_estado,
            "formato": "porcentaje",
            "descripcion": f"{int(dias_ausentes_total)} días ausentes en total",
            "umbral": ALERT_THRESHOLDS["ausentismo_pct"],
        },
        "nomina_total": {
            "valor": nomina_total,
            "label": "Nómina Mensual",
            "icono": "💰",
            "estado": "neutral",
            "formato": "moneda",
            "descripcion": f"Salario promedio: ${salario_promedio:,.0f}",
        },
        "altas": {
            "valor": altas,
            "label": "Altas (30 días)",
            "icono": "📈",
            "estado": "success" if altas > 0 else "neutral",
            "formato": "entero",
            "descripcion": "Nuevos ingresos en los últimos 30 días",
        },
        "bajas_periodo": {
            "valor": bajas_periodo,
            "label": "Bajas (período)",
            "icono": "📉",
            "estado": "warning" if bajas_periodo > 0 else "success",
            "formato": "entero",
            "descripcion": "Total de bajas registradas",
        },
        "antiguedad_promedio": {
            "valor": antiguedad_promedio,
            "label": "Antigüedad Promedio",
            "icono": "⏳",
            "estado": "neutral",
            "formato": "años",
            "descripcion": "Años promedio de permanencia (activos)",
        },
    }


def get_headcount_por_depto(df: pd.DataFrame) -> pd.DataFrame:
    """Headcount activo agrupado por departamento."""
    activos = df[df["Estatus"] == "Activo"]
    result = (
        activos.groupby("Departamento")
        .size()
        .reset_index(name="Headcount")
        .sort_values("Headcount", ascending=False)
    )
    return result


def get_headcount_por_ubicacion(df: pd.DataFrame) -> pd.DataFrame:
    """Headcount activo agrupado por ubicación."""
    activos = df[df["Estatus"] == "Activo"]
    result = (
        activos.groupby("Ubicacion")
        .size()
        .reset_index(name="Headcount")
        .sort_values("Headcount", ascending=False)
    )
    return result


def get_distribucion_contrato(df: pd.DataFrame) -> pd.DataFrame:
    """Distribución por tipo de contrato (activos)."""
    if "Tipo_Contrato" not in df.columns:
        return pd.DataFrame()
    activos = df[df["Estatus"] == "Activo"]
    result = (
        activos.groupby("Tipo_Contrato")
        .size()
        .reset_index(name="Cantidad")
        .sort_values("Cantidad", ascending=False)
    )
    result["Porcentaje"] = (result["Cantidad"] / result["Cantidad"].sum() * 100).round(1)
    return result


def get_distribucion_genero(df: pd.DataFrame) -> pd.DataFrame:
    """Distribución por género (activos)."""
    if "Genero" not in df.columns:
        return pd.DataFrame()
    activos = df[df["Estatus"] == "Activo"]
    result = (
        activos.groupby("Genero")
        .size()
        .reset_index(name="Cantidad")
        .sort_values("Cantidad", ascending=False)
    )
    result["Porcentaje"] = (result["Cantidad"] / result["Cantidad"].sum() * 100).round(1)
    return result


def get_tendencia_ingreso(df: pd.DataFrame) -> pd.DataFrame:
    """Ingresos por mes (últimos 12 meses)."""
    if "Fecha_Ingreso" not in df.columns or not pd.api.types.is_datetime64_any_dtype(df["Fecha_Ingreso"]):
        return pd.DataFrame()

    hoy = pd.Timestamp.today()
    hace_12_meses = hoy - pd.DateOffset(months=12)
    recientes = df[df["Fecha_Ingreso"] >= hace_12_meses].copy()
    recientes["Mes"] = recientes["Fecha_Ingreso"].dt.to_period("M").astype(str)

    result = (
        recientes.groupby("Mes")
        .size()
        .reset_index(name="Ingresos")
        .sort_values("Mes")
    )
    return result


def get_ausentismo_por_depto(df: pd.DataFrame) -> pd.DataFrame:
    """Días de ausentismo por departamento."""
    if "Dias_Ausentismo" not in df.columns:
        return pd.DataFrame()
    result = (
        df.groupby("Departamento")["Dias_Ausentismo"]
        .agg(["sum", "mean", "count"])
        .reset_index()
        .rename(columns={"sum": "Dias_Total", "mean": "Dias_Promedio", "count": "Empleados"})
        .sort_values("Dias_Total", ascending=False)
    )
    result["Dias_Promedio"] = result["Dias_Promedio"].round(1)
    return result


def get_motivos_ausentismo(df: pd.DataFrame) -> pd.DataFrame:
    """Top motivos de ausentismo."""
    if "Motivo_Ausentismo" not in df.columns:
        return pd.DataFrame()
    result = (
        df[df["Dias_Ausentismo"] > 0]
        .groupby("Motivo_Ausentismo")["Dias_Ausentismo"]
        .sum()
        .reset_index()
        .sort_values("Dias_Ausentismo", ascending=True)
        .tail(10)
    )
    return result


def get_motivos_baja(df: pd.DataFrame) -> pd.DataFrame:
    """Top motivos de baja."""
    if "Motivo_Baja" not in df.columns:
        return pd.DataFrame()
    bajas = df[df["Estatus"] == "Baja"]
    result = (
        bajas.groupby("Motivo_Baja")
        .size()
        .reset_index(name="Cantidad")
        .sort_values("Cantidad", ascending=False)
    )
    return result


def get_distribucion_nivel(df: pd.DataFrame) -> pd.DataFrame:
    """Distribución por nivel jerárquico."""
    if "Nivel_Jerarquico" not in df.columns:
        return pd.DataFrame()
    activos = df[df["Estatus"] == "Activo"]
    result = (
        activos.groupby("Nivel_Jerarquico")
        .size()
        .reset_index(name="Cantidad")
        .sort_values("Cantidad", ascending=False)
    )
    return result


def get_nomina_por_depto(df: pd.DataFrame) -> pd.DataFrame:
    """Costo de nómina por departamento (activos)."""
    if "Salario" not in df.columns:
        return pd.DataFrame()
    activos = df[df["Estatus"] == "Activo"]
    result = (
        activos.groupby("Departamento")["Salario"]
        .agg(["sum", "mean", "count"])
        .reset_index()
        .rename(columns={"sum": "Nomina_Total", "mean": "Salario_Promedio", "count": "Empleados"})
        .sort_values("Nomina_Total", ascending=False)
    )
    result["Salario_Promedio"] = result["Salario_Promedio"].round(0)
    return result


def get_antiguedad_buckets(df: pd.DataFrame) -> pd.DataFrame:
    """Distribución de empleados por rango de antigüedad."""
    if "Antiguedad_Anos" not in df.columns:
        return pd.DataFrame()
    activos = df[df["Estatus"] == "Activo"].copy()

    bins = [0, 1, 2, 5, 10, 20, 100]
    labels = ["< 1 año", "1-2 años", "2-5 años", "5-10 años", "10-20 años", "> 20 años"]
    activos["Rango_Antiguedad"] = pd.cut(
        activos["Antiguedad_Anos"], bins=bins, labels=labels, right=False
    )
    result = (
        activos.groupby("Rango_Antiguedad", observed=True)
        .size()
        .reset_index(name="Empleados")
    )
    return result
