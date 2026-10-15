from __future__ import annotations

from datetime import date
from typing import NotRequired, TypedDict

import pandas as pd


class KpiMetric(TypedDict):
    valor: int | float
    label: str
    icono: str
    estado: str
    formato: str
    descripcion: str
    umbral: NotRequired[int | float]


class KpiSnapshot(TypedDict):
    valor: int | float
    estado: str
    label: str


class ValidationResult(TypedDict):
    valid: bool
    errors: list[str]
    warnings: list[str]
    df: pd.DataFrame | None


class FilterOptions(TypedDict, total=False):
    departamentos: list[str]
    ubicaciones: list[str]
    estatus: list[str]
    tipos_contrato: list[str]
    generos: list[str]
    niveles: list[str]
    fecha_min: pd.Timestamp
    fecha_max: pd.Timestamp


FilterValue = list[str] | pd.Timestamp | date | None


class DashboardFilters(TypedDict, total=False):
    departamentos: list[str] | None
    ubicaciones: list[str] | None
    estatus: list[str] | None
    tipos_contrato: list[str] | None
    generos: list[str] | None
    niveles: list[str] | None
    fecha_ingreso_desde: pd.Timestamp | None
    fecha_ingreso_hasta: pd.Timestamp | None


class ReportRecord(TypedDict):
    id: str
    fecha: str
    fecha_display: str
    archivo: str
    kpis: dict[str, KpiSnapshot]
    filtros_aplicados: dict[str, str | list[str] | None]
