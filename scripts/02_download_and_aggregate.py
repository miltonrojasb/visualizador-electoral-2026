#!/usr/bin/env python3
"""
Agrega los CSV de escrutinio (mesa a mesa) a nivel nacional, departamental
y municipal, cruzando códigos con los catálogos parseados en 01.

Uso: coloca los 7 CSV ESCRUTINIO_*.csv en data/raw/escrutinio/ y corre:
    python3 scripts/02_download_and_aggregate.py
"""
import csv
import os
from collections import defaultdict

BASE = os.path.dirname(__file__)
RAW_DIR = os.path.join(BASE, "..", "data", "raw", "escrutinio")
OUT_DIR = os.path.join(BASE, "..", "data", "processed")
os.makedirs(OUT_DIR, exist_ok=True)


def load_candidatos():
    """Devuelve dict cod_candidato -> (nombre_completo, cod_partido, nombre_partido)."""
    partidos = {}
    with open(os.path.join(OUT_DIR, "partidos.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            partidos[row["cod_partido"]] = row["nombre_partido"]

    candidatos = {}
    with open(os.path.join(OUT_DIR, "candidatos.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cc = row["cod_candidato"]
            cp = row["cod_partido"]
            candidatos[cc] = (row["nombre_completo"], cp, partidos.get(cp, ""))
    return candidatos


def load_dep_mun():
    d = {}
    with open(os.path.join(OUT_DIR, "departamentos_municipios.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d[(row["cod_departamento"], row["cod_municipio"])] = (
                row["departamento"], row["municipio"]
            )
    return d


def main():
    candidatos = load_candidatos()
    dep_mun = load_dep_mun()

    nacional = defaultdict(int)
    departamental = defaultdict(lambda: defaultdict(int))
    municipal = defaultdict(lambda: defaultdict(int))

    files = sorted(f for f in os.listdir(RAW_DIR) if f.lower().endswith(".csv"))
    if not files:
        print(f"No hay CSV en {RAW_DIR}.")
        return

    total_rows = 0
    total_votos = 0
    for fname in files:
        path = os.path.join(RAW_DIR, fname)
        print(f"Procesando {fname} ...")
        rows_here = 0
        with open(path, encoding="utf-8", errors="replace", newline="") as f:
            reader = csv.DictReader(f, delimiter=";")
            for row in reader:
                rows_here += 1
                total_rows += 1
                cod_dep = (row.get("cod_departamento") or "").strip()
                cod_mun = (row.get("cod_municipio") or "").strip()
                cod_candidato = (row.get("cod_candidato") or "").strip()
                votos_raw = (row.get("votos") or "0").strip().rstrip(";").strip()
                try:
                    votos = int(votos_raw) if votos_raw else 0
                except ValueError:
                    continue

                nacional[cod_candidato] += votos
                departamental[cod_dep][cod_candidato] += votos
                municipal[(cod_dep, cod_mun)][cod_candidato] += votos
                total_votos += votos
        print(f"  {rows_here:,} filas en este archivo")

    # --- Nacional ---
    out_path = os.path.join(OUT_DIR, "resultados_nacional.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cod_candidato", "candidato", "partido", "votos"])
        for cod_cand, votos in sorted(nacional.items(), key=lambda x: -x[1]):
            nombre, _cp, partido_nombre = candidatos.get(cod_cand, (cod_cand, "", ""))
            w.writerow([cod_cand, nombre, partido_nombre, votos])
    print(f"\nresultados_nacional.csv -> {out_path}")

    # --- Departamental ---
    out_path = os.path.join(OUT_DIR, "resultados_departamental.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cod_departamento", "departamento", "cod_candidato", "candidato", "partido", "votos"])
        for cod_dep, cands in sorted(departamental.items()):
            depto_nombre = next(
                (dn for (cd, cm), (dn, mn) in dep_mun.items() if cd == cod_dep), cod_dep
            )
            for cod_cand, votos in sorted(cands.items(), key=lambda x: -x[1]):
                nombre, _cp, partido_nombre = candidatos.get(cod_cand, (cod_cand, "", ""))
                w.writerow([cod_dep, depto_nombre, cod_cand, nombre, partido_nombre, votos])
    print(f"resultados_departamental.csv -> {out_path}")

    # --- Municipal ---
    out_path = os.path.join(OUT_DIR, "resultados_municipal.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cod_departamento", "departamento", "cod_municipio", "municipio",
                     "cod_candidato", "candidato", "partido", "votos"])
        for (cod_dep, cod_mun), cands in sorted(municipal.items()):
            dn, mn = dep_mun.get((cod_dep, cod_mun), (cod_dep, cod_mun))
            for cod_cand, votos in sorted(cands.items(), key=lambda x: -x[1]):
                nombre, _cp, partido_nombre = candidatos.get(cod_cand, (cod_cand, "", ""))
                w.writerow([cod_dep, dn, cod_mun, mn, cod_cand, nombre, partido_nombre, votos])
    print(f"resultados_municipal.csv -> {out_path}")

    print(f"\nTotal filas procesadas: {total_rows:,}")
    print(f"Total votos sumados: {total_votos:,}")


if __name__ == "__main__":
    main()
