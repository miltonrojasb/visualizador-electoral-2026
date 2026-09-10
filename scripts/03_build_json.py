#!/usr/bin/env python3
"""
Convierte los CSV agregados (nacional/departamental/municipal) en un único
JSON compacto que el visualizador carga con fetch(). Corre después de
02_download_and_aggregate.py.

Asigna a cada candidato un "slot" de color categórico fijo (0-7) según su
votación nacional (los primeros 8 en votos reciben color propio; el resto
de candidatos con votos se agrupa como "Otros candidatos" en los gráficos,
aunque su cifra exacta sigue apareciendo en las tablas). Los votos
especiales (no marcados, nulos, blanco) siempre van aparte, en gris neutro.

Salida: site/data/resultados.json
"""
import csv
import json
import os
from collections import defaultdict

BASE = os.path.dirname(__file__)
PROC = os.path.join(BASE, "..", "data", "processed")
OUT = os.path.join(BASE, "..", "site", "data", "resultados.json")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

VOTOS_ESPECIALES = {"996", "997", "998"}


def main():
    # --- Candidatos: orden fijo por votación nacional ---
    nacional_rows = []
    with open(os.path.join(PROC, "resultados_nacional.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            nacional_rows.append(row)
    nacional_rows.sort(key=lambda r: -int(r["votos"]))

    candidatos_meta = {}
    slot_counter = 0
    for row in nacional_rows:
        cc = row["cod_candidato"]
        es_especial = cc in VOTOS_ESPECIALES
        slot = None
        if not es_especial:
            if slot_counter < 8:
                slot = slot_counter
                slot_counter += 1
        candidatos_meta[cc] = {
            "nombre": row["candidato"],
            "partido": row["partido"],
            "especial": es_especial,
            "slot": slot,  # None => se agrupa como "Otros candidatos" en gráficos
        }

    nacional = {r["cod_candidato"]: int(r["votos"]) for r in nacional_rows}
    total_nacional = sum(nacional.values())

    # --- Departamental ---
    departamental = {}
    with open(os.path.join(PROC, "resultados_departamental.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cd = row["cod_departamento"]
            if cd not in departamental:
                departamental[cd] = {"nombre": row["departamento"], "votos": {}, "total": 0}
            v = int(row["votos"])
            departamental[cd]["votos"][row["cod_candidato"]] = v
            departamental[cd]["total"] += v

    # --- Municipal (anidado por departamento) ---
    municipal = defaultdict(dict)
    with open(os.path.join(PROC, "resultados_municipal.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cd = row["cod_departamento"]
            cm = row["cod_municipio"]
            if cm not in municipal[cd]:
                municipal[cd][cm] = {"nombre": row["municipio"], "votos": {}, "total": 0}
            v = int(row["votos"])
            municipal[cd][cm]["votos"][row["cod_candidato"]] = v
            municipal[cd][cm]["total"] += v

    data = {
        "generado": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "candidatos": candidatos_meta,
        "nacional": {"votos": nacional, "total": total_nacional},
        "departamental": departamental,
        "municipal": municipal,
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = os.path.getsize(OUT) / 1024
    print(f"resultados.json generado: {size_kb:.1f} KB -> {OUT}")
    print(f"Total votos nacional: {total_nacional:,}")
    print(f"Departamentos: {len(departamental)}  Municipios: {sum(len(v) for v in municipal.values())}")


if __name__ == "__main__":
    main()
