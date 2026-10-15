# 👥 HR Analytics Dashboard

Dashboard de analítica de Recursos Humanos construido con Python + Streamlit + Plotly.
Permite cargar archivos Excel de empleados y genera automáticamente KPIs, gráficos interactivos y exportaciones.

---

## 🚀 Instalación y ejecución

### 1. Requisitos previos
- Python 3.10 o superior
- pip instalado

### 2. Instalar dependencias

```bash
cd hr-dashboard
pip install -r requirements.txt
```

### 3. Generar datos de demostración (primera vez)

```bash
python data/generate_demo.py
```

Esto crea el archivo `data/ejemplo_hr.xlsx` con 250 empleados ficticios.

### 4. Ejecutar la aplicación

```bash
streamlit run app.py
```

La app se abrirá automáticamente en `http://localhost:8501`

---

## 📋 Estructura del proyecto

```
hr-dashboard/
├── app.py                    # Punto de entrada principal
├── requirements.txt          # Dependencias Python
├── README.md
│
├── config/
│   └── settings.py           # Columnas requeridas, umbrales, paleta de colores
│
├── modules/
│   ├── validator.py          # Validación del archivo Excel
│   ├── processor.py          # Cálculo de KPIs y métricas
│   ├── charts.py             # Gráficos Plotly (dark mode)
│   ├── export_excel.py       # Exportación a Excel (.xlsx)
│   └── history.py            # Historial de reportes (JSON)
│
├── assets/
│   └── style.css             # Estilos dark mode premium
│
├── data/
│   ├── generate_demo.py      # Generador de datos ficticios
│   └── ejemplo_hr.xlsx       # Datos de ejemplo (generado)
│
└── reports/
    └── history.json          # Historial de reportes (auto-generado)
```

---

## 📊 Columnas requeridas en el Excel

| Columna | Tipo | Ejemplo |
|---|---|---|
| `ID_Empleado` | Texto | EMP0001 |
| `Nombre_Completo` | Texto | Ana García López |
| `Departamento` | Texto | Tecnología |
| `Puesto` | Texto | Desarrollador Senior |
| `Tipo_Contrato` | Texto | Indefinido |
| `Fecha_Ingreso` | Fecha | 2022-03-15 |
| `Estatus` | Texto | Activo / Baja / Suspendido |
| `Salario` | Número | 45000 |
| `Dias_Ausentismo` | Número | 3 |
| `Ubicacion` | Texto | CDMX |

### Columnas opcionales (amplían el análisis)

`Motivo_Ausentismo`, `Fecha_Baja`, `Motivo_Baja`, `Fecha_Nacimiento`, `Genero`, `Nivel_Jerarquico`, `Banda_Salarial`

---

## 🎯 KPIs calculados

| KPI | Fórmula | Alerta |
|---|---|---|
| Headcount Activos | COUNT(Estatus=Activo) | — |
| Tasa de Rotación % | Bajas / Total × 100 | 🔴 > 5% |
| Tasa de Ausentismo % | Días ausentes / Días laborables × 100 | 🟡 > 3% |
| Nómina Mensual | SUM(Salario) de activos | — |
| Altas (30 días) | Ingresos en últimos 30 días | — |
| Bajas del período | COUNT(Estatus=Baja) | — |
| Antigüedad Promedio | Media de años desde Fecha_Ingreso | — |

---

## 🔒 Privacidad y seguridad

- **Los archivos Excel nunca se almacenan en disco.** Se procesan exclusivamente en memoria.
- El historial solo guarda **valores numéricos agregados** (KPIs), nunca nombres, IDs ni datos personales.
- El historial se guarda localmente en `reports/history.json` y tiene un máximo de 50 registros.

---

## 📤 Exportaciones disponibles

| Formato | Contenido |
|---|---|
| **Excel (.xlsx)** | 4 hojas: KPIs, Headcount, Ausentismo, Detalle de empleados |
| **Historial (JSON)** | Snapshots de KPIs con fecha y filtros aplicados |

---

## ⚙️ Personalización

Edita `config/settings.py` para cambiar:

```python
# Umbrales de alerta
ALERT_THRESHOLDS = {
    "rotacion_pct": 5.0,      # % rotación → alerta roja
    "ausentismo_pct": 3.0,    # % ausentismo → alerta amarilla
}

# Nombre de empresa en reportes
EXPORT_CONFIG = {
    "company_name": "Tu Empresa S.A. de C.V.",
}

# Columnas requeridas (agregar si tu Excel tiene nombres diferentes)
REQUIRED_COLUMNS = [...]
```

---

## 🔮 Mejoras futuras sugeridas

1. **Exportación a PDF** con captura del dashboard completo (via `playwright` o `kaleido`)
2. **Comparativa entre períodos** (mes actual vs. mes anterior)
3. **Análisis predictivo de rotación** usando scikit-learn
4. **Integración con Active Directory** para sync automático de headcount
5. **Dashboard multi-empresa** con autenticación por tenant
6. **Notificaciones por correo** cuando se supera un umbral de alerta
7. **API REST** para conectar con sistemas HRIS externos (SAP, Workday, BambooHR)
8. **Mapa geográfico** de distribución por ubicación usando Plotly Mapbox
