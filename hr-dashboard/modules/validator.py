# =============================================================================
# modules/validator.py
# Validación de archivos Excel cargados por el usuario
# =============================================================================

import pandas as pd
import sys
import os
from typing import cast
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import REQUIRED_COLUMNS, VALID_ESTATUS
from modules.types import FilterOptions, ValidationResult


def validate_excel(df: pd.DataFrame) -> ValidationResult:
    """
    Valida que el DataFrame cargado del Excel cumpla los requisitos.

    Returns:
        dict con claves:
            - 'valid': bool
            - 'errors': list[str]  — errores bloqueantes
            - 'warnings': list[str] — advertencias no bloqueantes
            - 'df': pd.DataFrame limpio (si válido)
    """
    errors = []
    warnings = []

    # 1. Verificar columnas requeridas
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        errors.append(
            f"❌ Columnas faltantes: **{', '.join(missing_cols)}**. "
            f"El archivo debe contener exactamente estas columnas."
        )

    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings, "df": None}

    # 2. Verificar que haya al menos una fila de datos
    if len(df) == 0:
        errors.append("❌ El archivo está vacío (sin filas de datos).")
        return {"valid": False, "errors": errors, "warnings": warnings, "df": None}

    # 3. Limpiar espacios en columnas de texto
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
        df[col] = df[col].replace("nan", None)

    # 4. Validar columna Estatus
    invalid_estatus = df[~df["Estatus"].isin(VALID_ESTATUS + [None, "nan", ""])]["Estatus"].dropna().unique()
    if len(invalid_estatus) > 0:
        warnings.append(
            f"⚠️ Valores no reconocidos en 'Estatus': {list(invalid_estatus)}. "
            f"Se esperan: {VALID_ESTATUS}. Estas filas serán marcadas como 'Desconocido'."
        )
        df["Estatus"] = df["Estatus"].apply(
            lambda x: x if x in VALID_ESTATUS else "Desconocido"
        )

    # 5. Convertir fechas
    date_columns = ["Fecha_Ingreso", "Fecha_Baja", "Fecha_Nacimiento"]
    for col in date_columns:
        if col in df.columns:
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
                null_dates = df[col].isna().sum()
                if null_dates > 0:
                    warnings.append(
                        f"⚠️ {null_dates} filas en '{col}' no tienen fecha válida y serán ignoradas en análisis temporales."
                    )
            except Exception:
                warnings.append(f"⚠️ No se pudo convertir '{col}' a formato fecha.")

    # 6. Convertir columnas numéricas
    numeric_columns = ["Salario", "Dias_Ausentismo"]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            null_count = df[col].isna().sum()
            if null_count > 0:
                warnings.append(
                    f"⚠️ {null_count} filas en '{col}' no tienen valor numérico válido. Se usará 0."
                )
            df[col] = df[col].fillna(0)

    # 7. Verificar duplicados en ID_Empleado
    if "ID_Empleado" in df.columns:
        dupes = df["ID_Empleado"].duplicated().sum()
        if dupes > 0:
            warnings.append(
                f"⚠️ Se detectaron {dupes} filas con ID_Empleado duplicado. "
                f"Solo se conservará la primera aparición."
            )
            df = df.drop_duplicates(subset=["ID_Empleado"], keep="first")

    # 8. Calcular antigüedad si existe Fecha_Ingreso
    if "Fecha_Ingreso" in df.columns and pd.api.types.is_datetime64_any_dtype(df["Fecha_Ingreso"]):
        today = pd.Timestamp.today()
        df["Antiguedad_Anos"] = ((today - df["Fecha_Ingreso"]).dt.days / 365.25).round(1)
        df["Antiguedad_Anos"] = df["Antiguedad_Anos"].clip(lower=0)

    # 9. Calcular edad si existe Fecha_Nacimiento
    if "Fecha_Nacimiento" in df.columns and pd.api.types.is_datetime64_any_dtype(df["Fecha_Nacimiento"]):
        today = pd.Timestamp.today()
        df["Edad"] = ((today - df["Fecha_Nacimiento"]).dt.days / 365.25).astype(int)
        df["Edad"] = df["Edad"].clip(lower=16, upper=80)

    return {
        "valid": True,
        "errors": errors,
        "warnings": warnings,
        "df": df,
    }


def get_filter_options(df: pd.DataFrame) -> FilterOptions:
    """
    Extrae las opciones disponibles para los filtros dinámicos.
    """
    options = {}

    if "Departamento" in df.columns:
        options["departamentos"] = cast(list[str], sorted(df["Departamento"].dropna().unique().tolist()))

    if "Ubicacion" in df.columns:
        options["ubicaciones"] = cast(list[str], sorted(df["Ubicacion"].dropna().unique().tolist()))

    if "Estatus" in df.columns:
        options["estatus"] = cast(list[str], sorted(df["Estatus"].dropna().unique().tolist()))

    if "Tipo_Contrato" in df.columns:
        options["tipos_contrato"] = cast(list[str], sorted(df["Tipo_Contrato"].dropna().unique().tolist()))

    if "Genero" in df.columns:
        options["generos"] = cast(list[str], sorted(df["Genero"].dropna().unique().tolist()))

    if "Nivel_Jerarquico" in df.columns:
        options["niveles"] = cast(list[str], sorted(df["Nivel_Jerarquico"].dropna().unique().tolist()))

    if "Fecha_Ingreso" in df.columns and pd.api.types.is_datetime64_any_dtype(df["Fecha_Ingreso"]):
        options["fecha_min"] = df["Fecha_Ingreso"].min()
        options["fecha_max"] = df["Fecha_Ingreso"].max()

    return options
