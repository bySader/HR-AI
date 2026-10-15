# =============================================================================
# modules/export_excel.py
# Exportación de reportes a Excel con estilos corporativos
# =============================================================================

import io
import pandas as pd
import xlsxwriter
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import EXPORT_CONFIG, COLORS
from modules.types import KpiMetric


def export_to_excel(df: pd.DataFrame, kpis: dict[str, KpiMetric]) -> bytes:
    """
    Genera un archivo Excel con múltiples hojas:
    - Resumen de KPIs
    - Headcount por departamento
    - Ausentismo
    - Detalle de empleados

    Returns:
        bytes del archivo Excel listo para descarga
    """
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})

    # ── Formatos ─────────────────────────────────────────────────────────────
    fmt_title = workbook.add_format({
        "bold": True, "font_size": 18, "font_color": "#3B82F6",
        "font_name": "Calibri", "border": 0,
    })
    fmt_subtitle = workbook.add_format({
        "bold": False, "font_size": 10, "font_color": "#6B7280",
        "font_name": "Calibri",
    })
    fmt_header = workbook.add_format({
        "bold": True, "font_size": 11, "font_color": "#FFFFFF",
        "bg_color": "#1D4ED8", "border": 1, "border_color": "#1E40AF",
        "font_name": "Calibri", "align": "center", "valign": "vcenter",
    })
    fmt_kpi_label = workbook.add_format({
        "bold": True, "font_size": 12, "font_color": "#9CA3AF",
        "font_name": "Calibri",
    })
    fmt_kpi_value = workbook.add_format({
        "bold": True, "font_size": 22, "font_color": "#3B82F6",
        "font_name": "Calibri",
    })
    fmt_cell = workbook.add_format({
        "font_size": 10, "font_name": "Calibri", "border": 1,
        "border_color": "#E5E7EB",
    })
    fmt_cell_alt = workbook.add_format({
        "font_size": 10, "font_name": "Calibri", "border": 1,
        "border_color": "#E5E7EB", "bg_color": "#F9FAFB",
    })
    fmt_number = workbook.add_format({
        "font_size": 10, "font_name": "Calibri", "border": 1,
        "border_color": "#E5E7EB", "num_format": "#,##0",
    })
    fmt_currency = workbook.add_format({
        "font_size": 10, "font_name": "Calibri", "border": 1,
        "border_color": "#E5E7EB", "num_format": '"$"#,##0.00',
    })
    fmt_pct = workbook.add_format({
        "font_size": 10, "font_name": "Calibri", "border": 1,
        "border_color": "#E5E7EB", "num_format": "0.00%",
    })
    fmt_date = workbook.add_format({
        "font_size": 10, "font_name": "Calibri", "border": 1,
        "border_color": "#E5E7EB", "num_format": "dd/mm/yyyy",
    })

    fecha_reporte = datetime.now().strftime("%d/%m/%Y %H:%M")

    # ════════════════════════════════════════════════════════════════════════
    # HOJA 1: KPIs
    # ════════════════════════════════════════════════════════════════════════
    ws_kpi = workbook.add_worksheet(EXPORT_CONFIG["excel_sheet_kpis"])
    ws_kpi.hide_gridlines(2)
    ws_kpi.set_column("A:A", 25)
    ws_kpi.set_column("B:B", 20)
    ws_kpi.set_column("C:C", 35)
    ws_kpi.set_row(0, 35)

    ws_kpi.write("A1", EXPORT_CONFIG["report_title"], fmt_title)
    ws_kpi.write("A2", f"{EXPORT_CONFIG['company_name']} · Generado: {fecha_reporte}", fmt_subtitle)

    ws_kpi.write("A4", "Indicador", fmt_header)
    ws_kpi.write("B4", "Valor", fmt_header)
    ws_kpi.write("C4", "Descripción", fmt_header)

    kpi_row = 4
    kpi_labels = {
        "headcount": "Headcount Activos",
        "rotacion_pct": "Tasa de Rotación (%)",
        "ausentismo_pct": "Tasa de Ausentismo (%)",
        "nomina_total": "Nómina Mensual ($)",
        "altas": "Altas (últimos 30 días)",
        "bajas_periodo": "Bajas del Período",
        "antiguedad_promedio": "Antigüedad Promedio (años)",
    }

    for i, (key, label) in enumerate(kpi_labels.items()):
        if key in kpis:
            kpi = kpis[key]
            row = kpi_row + i
            fmt_row = fmt_cell if i % 2 == 0 else fmt_cell_alt
            ws_kpi.write(row, 0, label, fmt_row)
            ws_kpi.write(row, 1, kpi["valor"], fmt_row)
            ws_kpi.write(row, 2, kpi.get("descripcion", ""), fmt_row)

    # ════════════════════════════════════════════════════════════════════════
    # HOJA 2: Headcount
    # ════════════════════════════════════════════════════════════════════════
    ws_hc = workbook.add_worksheet(EXPORT_CONFIG["excel_sheet_headcount"])
    ws_hc.hide_gridlines(2)

    activos = df[df["Estatus"] == "Activo"]
    if "Departamento" in activos.columns:
        hc_depto = (
            activos.groupby("Departamento").size().reset_index(name="Headcount").sort_values("Headcount", ascending=False)
        )
        headers = ["Departamento", "Headcount"]
        ws_hc.set_column("A:A", 30)
        ws_hc.set_column("B:B", 15)
        for col_idx, header in enumerate(headers):
            ws_hc.write(0, col_idx, header, fmt_header)
        for row_idx, row in hc_depto.iterrows():
            fmt_r = fmt_cell if row_idx % 2 == 0 else fmt_cell_alt
            ws_hc.write(row_idx + 1, 0, row["Departamento"], fmt_r)
            ws_hc.write(row_idx + 1, 1, row["Headcount"], fmt_number)

    # ════════════════════════════════════════════════════════════════════════
    # HOJA 3: Ausentismo
    # ════════════════════════════════════════════════════════════════════════
    ws_aus = workbook.add_worksheet(EXPORT_CONFIG["excel_sheet_ausentismo"])
    ws_aus.hide_gridlines(2)

    if "Dias_Ausentismo" in df.columns and "Departamento" in df.columns:
        aus_depto = (
            df.groupby("Departamento")["Dias_Ausentismo"]
            .agg(["sum", "mean", "count"])
            .reset_index()
            .rename(columns={"sum": "Días Totales", "mean": "Días Promedio", "count": "Empleados"})
            .sort_values("Días Totales", ascending=False)
        )
        ws_aus.set_column("A:A", 30)
        ws_aus.set_column("B:D", 18)
        for col_idx, col in enumerate(aus_depto.columns):
            ws_aus.write(0, col_idx, col, fmt_header)
        for row_idx, row in aus_depto.iterrows():
            fmt_r = fmt_cell if row_idx % 2 == 0 else fmt_cell_alt
            ws_aus.write(row_idx + 1, 0, row["Departamento"], fmt_r)
            ws_aus.write(row_idx + 1, 1, row["Días Totales"], fmt_number)
            ws_aus.write(row_idx + 1, 2, round(row["Días Promedio"], 1), fmt_cell)
            ws_aus.write(row_idx + 1, 3, row["Empleados"], fmt_number)

    # ════════════════════════════════════════════════════════════════════════
    # HOJA 4: Detalle de Empleados (sin datos ultra-sensibles)
    # ════════════════════════════════════════════════════════════════════════
    ws_det = workbook.add_worksheet(EXPORT_CONFIG["excel_sheet_detalle"])
    ws_det.hide_gridlines(2)

    # Columnas a exportar (excluimos Salario por privacidad en el detalle)
    export_cols = [
        c for c in [
            "ID_Empleado", "Nombre_Completo", "Departamento", "Puesto",
            "Tipo_Contrato", "Estatus", "Ubicacion", "Fecha_Ingreso",
            "Antiguedad_Anos", "Dias_Ausentismo", "Genero", "Nivel_Jerarquico",
        ] if c in df.columns
    ]

    for col_idx, col in enumerate(export_cols):
        ws_det.set_column(col_idx, col_idx, 20)
        ws_det.write(0, col_idx, col.replace("_", " "), fmt_header)

    for row_idx, row in df[export_cols].iterrows():
        fmt_r = fmt_cell if row_idx % 2 == 0 else fmt_cell_alt
        for col_idx, col in enumerate(export_cols):
            val = row[col]
            if pd.isna(val):
                ws_det.write(row_idx + 1, col_idx, "", fmt_r)
            elif "Fecha" in col and hasattr(val, "strftime"):
                ws_det.write(row_idx + 1, col_idx, val.strftime("%d/%m/%Y"), fmt_r)
            elif isinstance(val, (int, float)):
                ws_det.write(row_idx + 1, col_idx, val, fmt_number)
            else:
                ws_det.write(row_idx + 1, col_idx, str(val), fmt_r)

    workbook.close()
    output.seek(0)
    return output.read()
