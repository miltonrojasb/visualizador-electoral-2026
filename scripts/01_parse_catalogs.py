#!/usr/bin/env python3
"""
Parsea los catálogos de la Registraduría (formato ancho fijo, latin-1)
y produce diccionarios/tablas limpias en data/processed/.

Fuentes (data/raw/):
- CANDIDATOS_*.TXT   -> candidatos.csv   (cod_partido, cod_candidato, nombre_completo)
- PARTIDOS_*.TXT     -> partidos.csv     (cod_partido, nombre_partido)
- DIVIPOL_*.TXT      -> divipol.csv      (cod_departamento, cod_municipio, cod_zona,
                                           cod_puesto, departamento, municipio, puesto,
                                           potencial, sufragantes, mesas, comuna)
"""
import csv
import glob
import os

RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
os.makedirs(OUT, exist_ok=True)


def find(pattern):
    matches = glob.glob(os.path.join(RAW, pattern))
    if not matches:
        raise FileNotFoundError(f"No se encontró archivo para patrón: {pattern}")
    return matches[0]


# Códigos especiales de votación no asignada a candidato (estándar Registraduría)
VOTOS_ESPECIALES = {
    "996": "No Marcados",
    "997": "Votos Nulos",
    "998": "Votos en Blanco",
}


def parse_candidatos():
    path = find("*CANDIDATOS*.TXT")
    rows = []
    with open(path, encoding="latin-1") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            cod_partido = line[4:16][-4:]
            cod_candidato = line[16:20][:3]
            nombres = line[20:60].strip()
            apellidos = line[60:100].strip()
            nombre_completo = f"{nombres} {apellidos}".strip()
            rows.append({
                "cod_partido": cod_partido,
                "cod_candidato": cod_candidato,
                "nombre_completo": nombre_completo,
            })
    # Agregar códigos especiales
    for cod, nombre in VOTOS_ESPECIALES.items():
        rows.append({"cod_partido": "0000", "cod_candidato": cod, "nombre_completo": nombre})

    out_path = os.path.join(OUT, "candidatos.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cod_partido", "cod_candidato", "nombre_completo"])
        w.writeheader()
        w.writerows(rows)
    print(f"candidatos.csv: {len(rows)} filas -> {out_path}")
    return rows


def parse_partidos():
    path = find("*PARTIDOS*.TXT")
    rows = []
    with open(path, encoding="latin-1") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            cod_partido = line[0:5][-4:]
            nombre = line[5:205].strip()
            rows.append({"cod_partido": cod_partido, "nombre_partido": nombre})
    rows.append({"cod_partido": "0000", "nombre_partido": "Sin partido / Voto especial"})

    out_path = os.path.join(OUT, "partidos.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cod_partido", "nombre_partido"])
        w.writeheader()
        w.writerows(rows)
    print(f"partidos.csv: {len(rows)} filas -> {out_path}")
    return rows


def parse_divipol():
    path = find("*DIVIPOL*.TXT")
    rows = []
    with open(path, encoding="latin-1") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            cod_departamento = line[0:2]
            cod_municipio = line[2:5]
            cod_zona = line[5:7]
            cod_puesto = line[7:9]
            departamento = line[9:21].strip()
            municipio = line[21:51].strip()
            # El bloque final (nombre de puesto + campo numérico de ancho variable +
            # comuna) no tiene una segmentación fija verificable sin documentación
            # oficial de la Registraduría, así que solo se conserva el nombre de la
            # comuna (cuando existe) leyendo desde el final de la línea.
            tail = line[51:]
            comuna_match = None
            import re as _re
            m = _re.search(r"COMUNA\s+\d+.*$|CORREGIMIENTO.*$", tail)
            comuna_nombre = m.group().strip() if m else ""
            puesto_y_num = tail[: m.start()] if m else tail
            # El nombre de puesto es la parte no numérica inicial de ese segmento
            m2 = _re.match(r"([^\d]*)", puesto_y_num)
            puesto = m2.group(1).strip() if m2 else puesto_y_num.strip()
            rows.append({
                "cod_departamento": cod_departamento,
                "cod_municipio": cod_municipio,
                "cod_zona": cod_zona,
                "cod_puesto": cod_puesto,
                "departamento": departamento,
                "municipio": municipio,
                "puesto": puesto,
                "comuna_nombre": comuna_nombre,
            })

    out_path = os.path.join(OUT, "divipol.csv")
    fieldnames = ["cod_departamento", "cod_municipio", "cod_zona", "cod_puesto",
                  "departamento", "municipio", "puesto", "comuna_nombre"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"divipol.csv: {len(rows)} filas -> {out_path}")

    # Tabla resumida única por departamento+municipio (nombres, sin duplicar por puesto)
    dep_mun = {}
    for r in rows:
        key = (r["cod_departamento"], r["cod_municipio"])
        if key not in dep_mun:
            dep_mun[key] = {
                "cod_departamento": r["cod_departamento"],
                "cod_municipio": r["cod_municipio"],
                "departamento": r["departamento"],
                "municipio": r["municipio"],
            }
    out_path2 = os.path.join(OUT, "departamentos_municipios.csv")
    with open(out_path2, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cod_departamento", "cod_municipio", "departamento", "municipio"])
        w.writeheader()
        w.writerows(dep_mun.values())
    print(f"departamentos_municipios.csv: {len(dep_mun)} filas -> {out_path2}")
    return rows


if __name__ == "__main__":
    parse_candidatos()
    parse_partidos()
    parse_divipol()
    print("Listo.")
