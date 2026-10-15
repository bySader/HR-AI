# =============================================================================
# data/generate_demo.py
# Genera el archivo ejemplo_hr.xlsx con ~250 filas de datos ficticios realistas
# Ejecutar: python data/generate_demo.py
# =============================================================================

import random
import os
import sys
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker

# Configurar Faker en español
fake = Faker("es_MX")
random.seed(42)
Faker.seed(42)

# ── Catálogos ─────────────────────────────────────────────────────────────────
DEPARTAMENTOS = [
    "Recursos Humanos", "Finanzas", "Tecnología", "Operaciones",
    "Ventas", "Marketing", "Legal", "Logística", "Servicio al Cliente", "Dirección",
]

PUESTOS = {
    "Recursos Humanos": ["Gerente de RRHH", "Analista de RRHH", "Reclutador", "Coordinador de Nómina"],
    "Finanzas": ["Director Financiero", "Contador Senior", "Analista Financiero", "Tesorero"],
    "Tecnología": ["CTO", "Desarrollador Senior", "Desarrollador Junior", "Arquitecto de Software", "QA Engineer"],
    "Operaciones": ["Gerente de Operaciones", "Supervisor de Planta", "Técnico de Mantenimiento", "Operador"],
    "Ventas": ["Director de Ventas", "Ejecutivo de Ventas", "Representante Comercial", "KAM"],
    "Marketing": ["Gerente de Marketing", "Especialista Digital", "Diseñador Gráfico", "Analista de Datos"],
    "Legal": ["Director Legal", "Abogado Corporativo", "Asistente Legal"],
    "Logística": ["Gerente de Logística", "Coordinador de Distribución", "Chofer", "Almacenista"],
    "Servicio al Cliente": ["Gerente de CS", "Agente de Atención", "Supervisor de Call Center"],
    "Dirección": ["CEO", "COO", "CFO", "Director General"],
}

UBICACIONES = ["CDMX", "Monterrey", "Guadalajara", "Querétaro", "Puebla", "Cancún"]

TIPOS_CONTRATO = ["Indefinido", "Temporal", "Por Obra", "Honorarios", "Prácticas"]
TIPOS_CONTRATO_PESO = [55, 20, 10, 10, 5]

ESTATUS_OPCIONES = ["Activo", "Activo", "Activo", "Activo", "Baja", "Suspendido"]  # pesos aprox

GENEROS = ["Masculino", "Femenino", "No binario"]
GENEROS_PESO = [52, 45, 3]

NIVELES = ["Operativo", "Analista / Especialista", "Coordinador / Supervisor", "Gerente / Jefe", "Director / VP", "C-Level"]
NIVELES_PESO = [30, 30, 20, 12, 6, 2]

MOTIVOS_AUSENTISMO = [
    "Enfermedad general", "Permiso personal", "Incapacidad IMSS",
    "Cita médica", "Fallecimiento familiar", "Maternidad / Paternidad",
    "Accidente laboral", "Capacitación externa", "Sin motivo registrado",
]

MOTIVOS_BAJA = [
    "Renuncia voluntaria", "Término de contrato", "Despido justificado",
    "Reestructura organizacional", "Jubilación", "Incapacidad permanente",
    "Acuerdo mutuo", "Abandono de empleo",
]

BANDAS_SALARIALES = {
    "Operativo": (8_000, 18_000),
    "Analista / Especialista": (18_000, 35_000),
    "Coordinador / Supervisor": (30_000, 55_000),
    "Gerente / Jefe": (50_000, 90_000),
    "Director / VP": (85_000, 160_000),
    "C-Level": (150_000, 300_000),
}


def fecha_aleatoria(inicio: datetime, fin: datetime) -> datetime:
    delta = fin - inicio
    return inicio + timedelta(days=random.randint(0, delta.days))


def generar_empleado(emp_id: int) -> dict:
    depto = random.choice(DEPARTAMENTOS)
    puesto = random.choice(PUESTOS[depto])
    nivel = random.choices(NIVELES, weights=NIVELES_PESO)[0]
    genero = random.choices(GENEROS, weights=GENEROS_PESO)[0]
    tipo_contrato = random.choices(TIPOS_CONTRATO, weights=TIPOS_CONTRATO_PESO)[0]
    ubicacion = random.choice(UBICACIONES)

    # Salario según nivel con ruido
    sal_min, sal_max = BANDAS_SALARIALES[nivel]
    salario = round(random.uniform(sal_min, sal_max), 0)

    # Fecha de ingreso: últimos 15 años
    hoy = datetime.today()
    fecha_ingreso = fecha_aleatoria(hoy - timedelta(days=15 * 365), hoy)

    # Estatus
    estatus = random.choice(ESTATUS_OPCIONES)

    # Fecha de baja (solo si está de baja)
    fecha_baja = None
    motivo_baja = None
    if estatus == "Baja":
        fecha_baja = fecha_aleatoria(fecha_ingreso + timedelta(days=90), hoy)
        motivo_baja = random.choice(MOTIVOS_BAJA)

    # Ausentismo: 0-25 días, con alta probabilidad de 0
    dias_aus = 0
    motivo_aus = None
    if random.random() < 0.45:  # 45% de empleados tienen al menos 1 día ausente
        dias_aus = random.randint(1, 25)
        motivo_aus = random.choice(MOTIVOS_AUSENTISMO)

    # Nombre según género
    if genero == "Masculino":
        nombre = fake.first_name_male() + " " + fake.last_name() + " " + fake.last_name()
    else:
        nombre = fake.first_name_female() + " " + fake.last_name() + " " + fake.last_name()

    # Fecha de nacimiento: entre 20 y 65 años atrás
    fecha_nac = fecha_aleatoria(hoy - timedelta(days=65 * 365), hoy - timedelta(days=20 * 365))

    return {
        "ID_Empleado": f"EMP{emp_id:04d}",
        "Nombre_Completo": nombre,
        "Departamento": depto,
        "Puesto": puesto,
        "Tipo_Contrato": tipo_contrato,
        "Fecha_Ingreso": fecha_ingreso.date(),
        "Estatus": estatus,
        "Salario": salario,
        "Dias_Ausentismo": dias_aus,
        "Motivo_Ausentismo": motivo_aus,
        "Fecha_Baja": fecha_baja.date() if fecha_baja else None,
        "Motivo_Baja": motivo_baja,
        "Ubicacion": ubicacion,
        "Fecha_Nacimiento": fecha_nac.date(),
        "Genero": genero,
        "Nivel_Jerarquico": nivel,
        "Banda_Salarial": f"{nivel} · ${BANDAS_SALARIALES[nivel][0]:,} - ${BANDAS_SALARIALES[nivel][1]:,}",
    }


def main():
    print("Generando datos ficticios de empleados...")
    empleados = [generar_empleado(i + 1) for i in range(250)]
    df = pd.DataFrame(empleados)

    # Ordenar: activos primero
    df = df.sort_values(["Estatus", "Departamento", "Nombre_Completo"]).reset_index(drop=True)

    # Guardar
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(output_dir, "ejemplo_hr.xlsx")
    df.to_excel(output_path, index=False, engine="openpyxl")

    # Estadísticas de lo generado
    print(f"\n✅ Archivo generado: {output_path}")
    print(f"   Total empleados: {len(df)}")
    print(f"   Activos:         {len(df[df['Estatus']=='Activo'])}")
    print(f"   Bajas:           {len(df[df['Estatus']=='Baja'])}")
    print(f"   Suspendidos:     {len(df[df['Estatus']=='Suspendido'])}")
    print(f"   Departamentos:   {df['Departamento'].nunique()}")
    print(f"   Ubicaciones:     {df['Ubicacion'].nunique()}")
    print(f"   Cols exportadas: {len(df.columns)} → {list(df.columns)}")


if __name__ == "__main__":
    main()
