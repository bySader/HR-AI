# =============================================================================
# app.py — Punto de entrada del HR Analytics Dashboard
# Ejecutar con: streamlit run app.py
# =============================================================================

import streamlit as st
import pandas as pd
import io
import os
import sys
from datetime import date, datetime
from streamlit.runtime.uploaded_file_manager import UploadedFile

# ── Configuración de paths ────────────────────────────────────────────────────
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

# ── Configuración de página (DEBE ir antes de cualquier st.call) ──────────────
st.set_page_config(
    page_title="HR Analytics Dashboard",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "HR Analytics Dashboard v1.0 — Powered by Streamlit + Plotly",
    },
)

# ── Imports internos ──────────────────────────────────────────────────────────
from config.settings import APP_NAME, APP_ICON, REQUIRED_COLUMNS
from modules.types import DashboardFilters, KpiMetric
from modules.validator import get_filter_options, validate_excel
from modules.processor import (
    apply_filters,
    calculate_kpis,
    get_headcount_por_depto,
    get_headcount_por_ubicacion,
    get_distribucion_contrato,
    get_distribucion_genero,
    get_tendencia_ingreso,
    get_ausentismo_por_depto,
    get_motivos_ausentismo,
    get_motivos_baja,
    get_antiguedad_buckets,
    get_nomina_por_depto,
)
from modules.charts import (
    chart_headcount_por_depto,
    chart_distribucion_donut,
    chart_tendencia_ingresos,
    chart_ausentismo_por_depto,
    chart_motivos_ausentismo,
    chart_motivos_baja,
    chart_antiguedad_buckets,
    chart_nomina_por_depto,
    chart_headcount_ubicacion,
)
from modules.export_excel import export_to_excel
from modules.history import save_report, get_history


# ── Cargar CSS personalizado ──────────────────────────────────────────────────
def load_css():
    css_path = os.path.join(ROOT_DIR, "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()


# ── Helpers de UI ─────────────────────────────────────────────────────────────
def render_kpi_card(kpi: KpiMetric) -> str:
    """Genera HTML de tarjeta KPI."""
    estado = kpi.get("estado", "neutral")
    valor = kpi["valor"]
    formato = kpi.get("formato", "entero")

    # Formatear valor
    if formato == "porcentaje":
        valor_display = f"{valor:.2f}%"
    elif formato == "moneda":
        valor_display = f"${valor:,.0f}"
    elif formato == "años":
        valor_display = f"{valor:.1f} años"
    else:
        valor_display = f"{int(valor):,}"

    # Badge de alerta
    umbral = kpi.get("umbral")
    alert_html = ""
    if estado == "danger" and umbral:
        alert_html = f'<div class="kpi-alert-badge danger">⚠ Sobre umbral ({umbral}%)</div>'
    elif estado == "warning" and umbral:
        alert_html = f'<div class="kpi-alert-badge warning">▲ Cerca del umbral</div>'

    return f"""
    <div class="kpi-card {estado}">
        <span class="kpi-icon">{kpi.get('icono', '📊')}</span>
        <div class="kpi-label">{kpi['label']}</div>
        <div class="kpi-value {estado}">{valor_display}</div>
        <div class="kpi-desc">{kpi.get('descripcion', '')}</div>
        {alert_html}
    </div>
    """


def render_section_header(titulo: str, subtitulo: str = ""):
    """Encabezado de sección con separador."""
    st.markdown(f"""
    <div style="margin: 1.5rem 0 0.75rem 0;">
        <h3 style="font-size:1rem; font-weight:700; color:#F9FAFB; 
                   text-transform:uppercase; letter-spacing:0.05em; margin:0;">
            {titulo}
        </h3>
        {"<p style='font-size:0.8rem; color:#9CA3AF; margin:0.2rem 0 0 0;'>" + subtitulo + "</p>" if subtitulo else ""}
    </div>
    <hr>
    """, unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <h2>👥 HR Analytics</h2>
        <span>Dashboard Corporativo</span>
    </div>
    """, unsafe_allow_html=True)

    # Carga de archivo
    st.markdown("### 📂 Cargar Datos")
    uploaded_file = st.file_uploader(
        "Arrastra tu archivo Excel aquí",
        type=["xlsx", "xls"],
        help=(
            f"El archivo debe contener las columnas: "
            f"{', '.join(REQUIRED_COLUMNS[:5])}... y más."
        ),
    )

    # Opción de demo
    st.markdown("---")
    use_demo = st.button("🎮 Usar datos de demo", use_container_width=True)

    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.7rem; color:#6B7280; text-align:center;'>"
        "Los datos se procesan en memoria.<br>Ningún archivo se almacena.</p>",
        unsafe_allow_html=True,
    )


# ── Funciones de carga ────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_demo_data() -> pd.DataFrame:
    """Carga el archivo de demo incluido en la app."""
    demo_path = os.path.join(ROOT_DIR, "data", "ejemplo_hr.xlsx")
    if os.path.exists(demo_path):
        df = pd.read_excel(demo_path, engine="openpyxl")  # type: ignore[reportUnknownMemberType]
        return df
    return pd.DataFrame()


def load_uploaded_file(file: UploadedFile) -> tuple[pd.DataFrame | None, str]:
    """Carga y valida el archivo subido por el usuario."""
    try:
        # Detectar engine según la extensión real
        file_bytes = file.read()
        file.seek(0)

        # Intentar openpyxl primero (xlsx), luego xlrd (xls)
        try:
            df = pd.read_excel(
                io.BytesIO(file_bytes), engine="openpyxl"
            )  # type: ignore[reportUnknownMemberType]
        except Exception:
            df = pd.read_excel(
                io.BytesIO(file_bytes), engine="xlrd"
            )  # type: ignore[reportUnknownMemberType]

        return df, file.name
    except Exception as e:
        return None, str(e)


# ── Estado de sesión ──────────────────────────────────────────────────────────
if "df_raw" not in st.session_state:
    st.session_state.df_raw = None
if "df_validated" not in st.session_state:
    st.session_state.df_validated = None
if "filename" not in st.session_state:
    st.session_state.filename = ""
if "filters" not in st.session_state:
    st.session_state.filters = {}
if "report_saved" not in st.session_state:
    st.session_state.report_saved = False


# ── Manejo de carga de datos ──────────────────────────────────────────────────
if use_demo:
    with st.spinner("Cargando datos de demostración..."):
        df_raw = load_demo_data()
        if df_raw.empty:
            st.error("❌ No se encontró el archivo de demo. Ejecuta primero `python data/generate_demo.py`")
        else:
            result = validate_excel(df_raw.copy())
            st.session_state.df_raw = df_raw
            st.session_state.df_validated = result["df"]
            st.session_state.filename = "ejemplo_hr.xlsx (demo)"
            st.session_state.report_saved = False
            if result["warnings"]:
                for w in result["warnings"]:
                    st.sidebar.warning(w)
            st.rerun()

elif uploaded_file is not None:
    with st.spinner(f"Procesando {uploaded_file.name}..."):
        df_raw, err = load_uploaded_file(uploaded_file)
        if df_raw is None:
            st.error(f"❌ Error al leer el archivo: {err}")
        else:
            result = validate_excel(df_raw.copy())
            if not result["valid"]:
                for e in result["errors"]:
                    st.error(e)
            else:
                st.session_state.df_raw = df_raw
                st.session_state.df_validated = result["df"]
                st.session_state.filename = uploaded_file.name
                st.session_state.report_saved = False
                if result["warnings"]:
                    for w in result["warnings"]:
                        st.sidebar.warning(w)
                st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# PANTALLA PRINCIPAL
# ════════════════════════════════════════════════════════════════════════════

if st.session_state.df_validated is None:
    # ── Estado vacío / bienvenida ──────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding: 4rem 2rem;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">👥</div>
        <h1 style="font-size:2rem; font-weight:800; color:#F9FAFB; margin-bottom:0.5rem;">
            HR Analytics Dashboard
        </h1>
        <p style="font-size:1rem; color:#9CA3AF; max-width:480px; margin:0 auto 2rem;">
            Carga tu archivo Excel de RRHH para generar reportes visuales 
            automáticos con KPIs, gráficos y análisis detallados.
        </p>
        <div style="display:flex; gap:1rem; justify-content:center; flex-wrap:wrap; margin-bottom:2rem;">
            <div style="background:#1E2A3A; border:1px solid rgba(255,255,255,0.06); 
                        border-radius:12px; padding:1.25rem; width:180px;">
                <div style="font-size:1.5rem;">📊</div>
                <div style="font-weight:600; margin-top:0.5rem; color:#F9FAFB;">7 KPIs</div>
                <div style="font-size:0.8rem; color:#9CA3AF;">en tiempo real</div>
            </div>
            <div style="background:#1E2A3A; border:1px solid rgba(255,255,255,0.06); 
                        border-radius:12px; padding:1.25rem; width:180px;">
                <div style="font-size:1.5rem;">📈</div>
                <div style="font-weight:600; margin-top:0.5rem; color:#F9FAFB;">10+ Gráficos</div>
                <div style="font-size:0.8rem; color:#9CA3AF;">interactivos</div>
            </div>
            <div style="background:#1E2A3A; border:1px solid rgba(255,255,255,0.06); 
                        border-radius:12px; padding:1.25rem; width:180px;">
                <div style="font-size:1.5rem;">📤</div>
                <div style="font-weight:600; margin-top:0.5rem; color:#F9FAFB;">Exportación</div>
                <div style="font-size:0.8rem; color:#9CA3AF;">Excel + PDF</div>
            </div>
            <div style="background:#1E2A3A; border:1px solid rgba(255,255,255,0.06); 
                        border-radius:12px; padding:1.25rem; width:180px;">
                <div style="font-size:1.5rem;">🔔</div>
                <div style="font-weight:600; margin-top:0.5rem; color:#F9FAFB;">Alertas</div>
                <div style="font-size:0.8rem; color:#9CA3AF;">automáticas</div>
            </div>
        </div>
        <p style="font-size:0.85rem; color:#6B7280;">
            👈 Usa el panel izquierdo para cargar tu archivo o prueba los <strong>datos de demo</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

else:
    df = st.session_state.df_validated
    filter_opts = get_filter_options(df)

    # ── Navegación por tabs ────────────────────────────────────────────────
    tab_dashboard, tab_detalle, tab_historial = st.tabs([
        "📊 Dashboard", "🗂️ Detalle de Empleados", "🕓 Historial"
    ])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1: DASHBOARD
    # ════════════════════════════════════════════════════════════════════════
    with tab_dashboard:

        # ── Header ────────────────────────────────────────────────────────
        col_title, col_meta = st.columns([3, 1])
        with col_title:
            st.markdown(f"""
            <div class="app-header">
                <h1>{APP_ICON} {APP_NAME}</h1>
                <div class="subtitle">
                    📁 {st.session_state.filename} · 
                    🗓️ {datetime.now().strftime('%d/%m/%Y %H:%M')} · 
                    📋 {len(df):,} registros cargados
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── Filtros dinámicos ──────────────────────────────────────────────
        with st.expander("🔍 Filtros dinámicos", expanded=False):
            fc1, fc2, fc3, fc4 = st.columns(4)
            with fc1:
                f_deptos = st.multiselect(
                    "Departamento",
                    options=filter_opts.get("departamentos", []),
                    placeholder="Todos",
                )
            with fc2:
                f_ubics = st.multiselect(
                    "Ubicación",
                    options=filter_opts.get("ubicaciones", []),
                    placeholder="Todas",
                )
            with fc3:
                f_estatus = st.multiselect(
                    "Estatus",
                    options=filter_opts.get("estatus", []),
                    default=filter_opts.get("estatus", []),
                    placeholder="Todos",
                )
            with fc4:
                f_contratos = st.multiselect(
                    "Tipo de Contrato",
                    options=filter_opts.get("tipos_contrato", []),
                    placeholder="Todos",
                )

            # Filtro de fecha
            if "fecha_min" in filter_opts and "fecha_max" in filter_opts:
                fc5, fc6 = st.columns(2)
                with fc5:
                    f_fecha_desde: date | None = st.date_input(
                        "Ingreso desde",
                        value=filter_opts["fecha_min"].date(),
                        min_value=filter_opts["fecha_min"].date(),
                        max_value=filter_opts["fecha_max"].date(),
                    )
                with fc6:
                    f_fecha_hasta: date | None = st.date_input(
                        "Ingreso hasta",
                        value=filter_opts["fecha_max"].date(),
                        min_value=filter_opts["fecha_min"].date(),
                        max_value=filter_opts["fecha_max"].date(),
                    )
            else:
                f_fecha_desde = None
                f_fecha_hasta = None

        # Aplicar filtros
        current_filters: DashboardFilters = {
            "departamentos": f_deptos or None,
            "ubicaciones": f_ubics or None,
            "estatus": f_estatus or None,
            "tipos_contrato": f_contratos or None,
            "fecha_ingreso_desde": pd.Timestamp(f_fecha_desde) if f_fecha_desde else None,
            "fecha_ingreso_hasta": pd.Timestamp(f_fecha_hasta) if f_fecha_hasta else None,
        }
        df_filtered = apply_filters(df, current_filters)
        st.session_state.filters = current_filters

        if len(df_filtered) == 0:
            st.warning("⚠️ Los filtros seleccionados no devuelven registros. Ajusta los criterios.")
            st.stop()

        # ── KPIs ──────────────────────────────────────────────────────────
        render_section_header("KPIs Principales", f"Basado en {len(df_filtered):,} registros filtrados")
        kpis = calculate_kpis(df_filtered)

        kpi_keys = list(kpis.keys())
        kpi_cols = st.columns(len(kpi_keys))
        for col, key in zip(kpi_cols, kpi_keys):
            with col:
                st.markdown(render_kpi_card(kpis[key]), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Gráficos — Fila 1 ─────────────────────────────────────────────
        render_section_header("Distribución de Headcount")
        g1, g2 = st.columns([3, 2])

        with g1:
            hc_depto = get_headcount_por_depto(df_filtered)
            st.plotly_chart(
                chart_headcount_por_depto(hc_depto),
                use_container_width=True, key="chart_hc_depto"
            )

        with g2:
            hc_ubic = get_headcount_por_ubicacion(df_filtered)
            st.plotly_chart(
                chart_headcount_ubicacion(hc_ubic),
                use_container_width=True, key="chart_hc_ubic"
            )

        # ── Gráficos — Fila 2 ─────────────────────────────────────────────
        g3, g4 = st.columns(2)

        with g3:
            dist_contrato = get_distribucion_contrato(df_filtered)
            st.plotly_chart(
                chart_distribucion_donut(dist_contrato, "Tipo_Contrato", "Cantidad", "📋 Distribución por Tipo de Contrato"),
                use_container_width=True, key="chart_contrato"
            )

        with g4:
            if "Genero" in df_filtered.columns:
                dist_genero = get_distribucion_genero(df_filtered)
                st.plotly_chart(
                    chart_distribucion_donut(dist_genero, "Genero", "Cantidad", "⚧ Distribución por Género"),
                    use_container_width=True, key="chart_genero"
                )
            else:
                dist_nivel = get_distribucion_contrato(df_filtered)
                st.plotly_chart(
                    chart_antiguedad_buckets(get_antiguedad_buckets(df_filtered)),
                    use_container_width=True, key="chart_antiguedad_alt"
                )

        # ── Gráficos — Tendencia ───────────────────────────────────────────
        render_section_header("Tendencia de Ingresos")
        tendencia = get_tendencia_ingreso(df_filtered)
        st.plotly_chart(
            chart_tendencia_ingresos(tendencia),
            use_container_width=True, key="chart_tendencia"
        )

        # ── Gráficos — Ausentismo ──────────────────────────────────────────
        render_section_header("Análisis de Ausentismo")
        ga1, ga2 = st.columns([3, 2])

        with ga1:
            aus_depto = get_ausentismo_por_depto(df_filtered)
            st.plotly_chart(
                chart_ausentismo_por_depto(aus_depto),
                use_container_width=True, key="chart_aus_depto"
            )

        with ga2:
            motivos_aus = get_motivos_ausentismo(df_filtered)
            st.plotly_chart(
                chart_motivos_ausentismo(motivos_aus),
                use_container_width=True, key="chart_motivos_aus"
            )

        # ── Gráficos — Nómina y Antigüedad ────────────────────────────────
        render_section_header("Nómina y Antigüedad")
        gn1, gn2 = st.columns(2)

        with gn1:
            nomina_depto = get_nomina_por_depto(df_filtered)
            st.plotly_chart(
                chart_nomina_por_depto(nomina_depto),
                use_container_width=True, key="chart_nomina"
            )

        with gn2:
            ant_buckets = get_antiguedad_buckets(df_filtered)
            st.plotly_chart(
                chart_antiguedad_buckets(ant_buckets),
                use_container_width=True, key="chart_antiguedad"
            )

        # ── Gráfico — Motivos de Baja ──────────────────────────────────────
        if "Motivo_Baja" in df_filtered.columns:
            render_section_header("Rotación y Motivos de Baja")
            motivos_baja = get_motivos_baja(df_filtered)
            st.plotly_chart(
                chart_motivos_baja(motivos_baja),
                use_container_width=True, key="chart_motivos_baja"
            )

        # ── Exportación ────────────────────────────────────────────────────
        render_section_header("Exportar Reporte")
        exp_col1, exp_col2, exp_col3 = st.columns([2, 2, 3])

        with exp_col1:
            excel_bytes = export_to_excel(df_filtered, kpis)
            st.download_button(
                label="📥 Descargar Excel",
                data=excel_bytes,
                file_name=f"reporte_hr_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        with exp_col2:
            if st.button("💾 Guardar en Historial", use_container_width=True):
                save_report(kpis, current_filters, st.session_state.filename)
                st.session_state.report_saved = True
                st.success("✅ Reporte guardado en el historial")

        if st.session_state.report_saved:
            st.info("💡 Puedes ver el historial completo en la pestaña **🕓 Historial**")

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2: DETALLE DE EMPLEADOS
    # ════════════════════════════════════════════════════════════════════════
    with tab_detalle:
        st.markdown("### 🗂️ Detalle de Empleados")

        # Filtro de búsqueda
        search = st.text_input(
            "🔍 Buscar empleado (nombre, puesto, departamento...)",
            placeholder="Escribe para filtrar...",
        )

        df_display = df_filtered.copy()

        # Aplicar búsqueda
        if search:
            mask = pd.Series([False] * len(df_display))
            for col in ["Nombre_Completo", "Puesto", "Departamento", "ID_Empleado", "Ubicacion"]:
                if col in df_display.columns:
                    mask = mask | df_display[col].astype(str).str.contains(search, case=False, na=False)
            df_display = df_display[mask]

        # Columnas a mostrar
        show_cols = [
            c for c in [
                "ID_Empleado", "Nombre_Completo", "Departamento", "Puesto",
                "Tipo_Contrato", "Estatus", "Ubicacion", "Fecha_Ingreso",
                "Antiguedad_Anos", "Dias_Ausentismo", "Genero", "Nivel_Jerarquico",
            ] if c in df_display.columns
        ]

        st.markdown(
            f"<p style='color:#9CA3AF; font-size:0.85rem;'>Mostrando {len(df_display):,} de {len(df):,} registros</p>",
            unsafe_allow_html=True
        )

        # Tabla interactiva
        st.dataframe(
            df_display[show_cols].rename(columns=lambda c: c.replace("_", " ")),
            use_container_width=True,
            height=500,
            column_config={
                "Fecha Ingreso": st.column_config.DateColumn("Fecha Ingreso", format="DD/MM/YYYY"),
                "Antiguedad Anos": st.column_config.NumberColumn("Antigüedad (años)", format="%.1f"),
                "Dias Ausentismo": st.column_config.NumberColumn("Días Ausentes", format="%d"),
                "Estatus": st.column_config.TextColumn("Estatus"),
            },
        )

        # Descarga del detalle filtrado
        detail_excel = export_to_excel(df_display, kpis if "kpis" in dir() else {})
        st.download_button(
            label="📥 Descargar detalle filtrado (Excel)",
            data=detail_excel,
            file_name=f"detalle_empleados_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3: HISTORIAL
    # ════════════════════════════════════════════════════════════════════════
    with tab_historial:
        st.markdown("### 🕓 Historial de Reportes")
        st.markdown(
            "<p style='color:#9CA3AF; font-size:0.85rem;'>"
            "Solo se guardan KPIs agregados. No se almacenan datos personales.</p>",
            unsafe_allow_html=True
        )

        history = get_history()

        if not history:
            st.markdown("""
            <div class="empty-state">
                <div class="icon">📭</div>
                <h3>Sin reportes guardados</h3>
                <p>Genera un reporte en el Dashboard y haz clic en "Guardar en Historial".</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for record in history:
                with st.expander(
                    f"📋 {record.get('fecha_display', '')} — {record.get('archivo', 'Sin nombre')}",
                    expanded=False,
                ):
                    k = record.get("kpis", {})

                    h_cols = st.columns(4)
                    kpi_display = [
                        ("headcount", "👥 Headcount"),
                        ("rotacion_pct", "🔄 Rotación %"),
                        ("ausentismo_pct", "📅 Ausentismo %"),
                        ("nomina_total", "💰 Nómina"),
                    ]
                    for col, (key, label) in zip(h_cols, kpi_display):
                        if key in k:
                            val = k[key]["valor"]
                            estado = k[key]["estado"]
                            numeric_val = float(val)
                            if "pct" in key:
                                val_str = f"{numeric_val:.2f}%"
                            elif key == "nomina_total":
                                val_str = f"${numeric_val:,.0f}"
                            else:
                                val_str = f"{int(numeric_val):,}"
                            col.metric(label, val_str)

                    filtros = record.get("filtros_aplicados", {})
                    if filtros:
                        active_filters = {k: v for k, v in filtros.items() if v}
                        if active_filters:
                            st.markdown(
                                f"**Filtros:** `{active_filters}`",
                                help="Filtros que estaban activos al guardar este reporte"
                            )
