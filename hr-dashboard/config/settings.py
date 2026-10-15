# =============================================================================
# config/settings.py
# Configuración central de la aplicación HR Analytics Dashboard
# =============================================================================

# ── Metadatos de la app ───────────────────────────────────────────────────────
APP_NAME = "HR Analytics Dashboard"
APP_VERSION = "1.0.0"
APP_ICON = "👥"

# ── Columnas requeridas en el Excel ───────────────────────────────────────────
REQUIRED_COLUMNS = [
    "ID_Empleado",
    "Nombre_Completo",
    "Departamento",
    "Puesto",
    "Tipo_Contrato",
    "Fecha_Ingreso",
    "Estatus",
    "Salario",
    "Dias_Ausentismo",
    "Ubicacion",
]

# Columnas opcionales (se añaden funcionalidades si existen)
OPTIONAL_COLUMNS = [
    "Motivo_Ausentismo",
    "Fecha_Baja",
    "Motivo_Baja",
    "Fecha_Nacimiento",
    "Genero",
    "Nivel_Jerarquico",
    "Banda_Salarial",
]

# Valores válidos para columnas categóricas
VALID_ESTATUS = ["Activo", "Baja", "Suspendido"]
VALID_TIPO_CONTRATO = ["Indefinido", "Temporal", "Por Obra", "Honorarios", "Prácticas"]
VALID_GENERO = ["Masculino", "Femenino", "No binario", "Prefiero no decir"]

# ── Umbrales de alerta (configurables) ────────────────────────────────────────
ALERT_THRESHOLDS = {
    "rotacion_pct": 5.0,       # % de rotación que activa alerta roja
    "ausentismo_pct": 3.0,     # % de ausentismo que activa alerta amarilla
    "headcount_caida_pct": 10.0,  # % de caída en headcount que activa alerta roja
}

# ── Paleta de colores — Dark Mode premium ─────────────────────────────────────
COLORS = {
    # Fondos
    "bg_primary": "#0E1117",
    "bg_secondary": "#1C2333",
    "bg_card": "#1E2A3A",
    "bg_card_hover": "#243347",

    # Acento principal (azul eléctrico)
    "accent": "#3B82F6",
    "accent_light": "#60A5FA",
    "accent_dark": "#1D4ED8",

    # Semáforo de alertas
    "success": "#10B981",    # verde
    "warning": "#F59E0B",    # amarillo
    "danger": "#EF4444",     # rojo
    "neutral": "#6B7280",    # gris

    # Texto
    "text_primary": "#F9FAFB",
    "text_secondary": "#9CA3AF",
    "text_muted": "#6B7280",

    # Gradientes de gráficos
    "chart_palette": [
        "#3B82F6",  # azul
        "#10B981",  # verde
        "#F59E0B",  # amarillo
        "#EF4444",  # rojo
        "#8B5CF6",  # violeta
        "#EC4899",  # rosa
        "#06B6D4",  # cian
        "#F97316",  # naranja
        "#84CC16",  # lima
        "#A78BFA",  # lavanda
    ],
}

# ── Configuración de exportación ─────────────────────────────────────────────
EXPORT_CONFIG = {
    "company_name": "Mi Empresa S.A. de C.V.",
    "report_title": "Reporte de Recursos Humanos",
    "excel_sheet_kpis": "KPIs",
    "excel_sheet_headcount": "Headcount",
    "excel_sheet_ausentismo": "Ausentismo",
    "excel_sheet_rotacion": "Rotación",
    "excel_sheet_detalle": "Detalle Empleados",
}

# ── Configuración de historial ────────────────────────────────────────────────
HISTORY_FILE = "reports/history.json"
MAX_HISTORY_RECORDS = 50  # máximo de reportes guardados

# ── Días laborables por mes (estimado) ───────────────────────────────────────
WORKING_DAYS_PER_MONTH = 22
