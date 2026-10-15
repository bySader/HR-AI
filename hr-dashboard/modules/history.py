# =============================================================================
# modules/history.py
# Gestión del historial de reportes generados
# NOTA DE PRIVACIDAD: Solo se guardan KPIs agregados, nunca datos personales
# =============================================================================

import json
import os
from datetime import datetime
from typing import cast
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import HISTORY_FILE, MAX_HISTORY_RECORDS
from modules.types import DashboardFilters, KpiMetric, KpiSnapshot, ReportRecord


def _load_history() -> list[ReportRecord]:
    """Carga el historial desde el archivo JSON."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return cast(list[ReportRecord], json.load(f))
    except (json.JSONDecodeError, IOError):
        return []


def _save_history(records: list[ReportRecord]) -> None:
    """Guarda el historial en el archivo JSON."""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2, default=str)


def save_report(
    kpis: dict[str, KpiMetric],
    filters: DashboardFilters,
    filename: str = "",
) -> ReportRecord:
    """
    Guarda un snapshot del reporte actual en el historial.

    PRIVACIDAD: Solo se guardan valores numéricos agregados (KPIs),
    nunca nombres, IDs ni datos personales de empleados.

    Returns:
        dict con el registro guardado
    """
    records = _load_history()

    # Extraer solo los valores numéricos de los KPIs
    kpi_snapshot: dict[str, KpiSnapshot] = {
        key: {
            "valor": kpi.get("valor", 0),
            "estado": kpi.get("estado", "neutral"),
            "label": kpi.get("label", key),
        }
        for key, kpi in kpis.items()
    }

    # Limpiar filtros para serialización (quitar objetos Timestamp)
    filters_clean: dict[str, str | list[str] | None] = {}
    for k, v in filters.items():
        if hasattr(v, "isoformat"):
            filters_clean[k] = v.isoformat()
        elif isinstance(v, list):
            filters_clean[k] = v
        else:
            filters_clean[k] = str(v) if v is not None else None

    record = {
        "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "fecha": datetime.now().isoformat(),
        "fecha_display": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "archivo": filename,
        "kpis": kpi_snapshot,
        "filtros_aplicados": filters_clean,
    }

    records.insert(0, record)  # más reciente primero

    # Limitar número de registros
    records = records[:MAX_HISTORY_RECORDS]
    _save_history(records)

    return record


def get_history() -> list[ReportRecord]:
    """Retorna el historial completo de reportes."""
    return _load_history()


def delete_record(record_id: str) -> bool:
    """Elimina un registro del historial por ID."""
    records = _load_history()
    original_len = len(records)
    records = [r for r in records if r.get("id") != record_id]
    if len(records) < original_len:
        _save_history(records)
        return True
    return False


def clear_history() -> None:
    """Elimina todo el historial."""
    _save_history([])
