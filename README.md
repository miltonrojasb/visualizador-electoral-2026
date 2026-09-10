# Visualizador Electoral — Presidenciales Colombia 2026

Visualizador de resultados electorales (nacional, departamental y municipal)
para las elecciones presidenciales de Colombia 2026, construido para el
Observatorio de la Calidad de la Democracia Subnacional (OcaDEM),
Universidad de Medellín.

**Ver el sitio en vivo:** una vez publicado con GitHub Pages (ver abajo),
quedará disponible en `https://<tu-usuario>.github.io/visualizador-electoral-2026/site/`.

## ¿Qué hace?

- Muestra los resultados de la elección presidencial en tres niveles:
  **nacional**, **departamental** (con selector) y **municipal** (con
  selector dependiente + buscador de municipios en todo el país).
- Cada vista tiene un gráfico de barras horizontal, tarjetas de resumen y una
  tabla completa y ordenable (clic en los encabezados de columna).
- Los votos especiales (no marcados, nulos, en blanco) se muestran aparte de
  los candidatos.
- Funciona enteramente en el navegador: no necesita servidor ni base de
  datos. Toda la información vive en un solo archivo,
  `site/data/resultados.json`.

## Estructura del proyecto

```
├── data/
│   ├── raw/                        # Catálogos oficiales de la Registraduría (formato ancho fijo)
│   │   ├── CANDIDATOS.TXT
│   │   ├── PARTIDOS.TXT
│   │   ├── DIVIPOL.TXT             # Departamentos, municipios y puestos de votación
│   │   ├── CIRCUNSCRIPCION.TXT
│   │   ├── CORPORACION.TXT
│   │   ├── INDICADORES.TXT
│   │   └── escrutinio/             # CSV de escrutinio mesa a mesa (NO incluidos en este paquete: ~100 MB)
│   └── processed/                  # Generado por los scripts — no editar a mano
│       ├── candidatos.csv
│       ├── partidos.csv
│       ├── divipol.csv
│       ├── departamentos_municipios.csv
│       ├── resultados_nacional.csv
│       ├── resultados_departamental.csv
│       └── resultados_municipal.csv
├── scripts/
│   ├── 01_parse_catalogs.py        # Parsea CANDIDATOS/PARTIDOS/DIVIPOL -> data/processed/*.csv
│   ├── 02_download_and_aggregate.py # Suma los votos de mesa a nacional/departamental/municipal
│   └── 03_build_json.py            # Convierte los CSV agregados en site/data/resultados.json
└── site/
    ├── index.html                  # El visualizador (un solo archivo, sin dependencias externas)
    └── data/resultados.json        # Datos que consume el visualizador
```

## Cómo actualizar los datos (por ejemplo, con nuevos escrutinios)

1. Coloca los CSV de escrutinio de la Registraduría (formato
   `valor_fijo;cod_departamento;cod_municipio;...;cod_candidato;votos`) dentro
   de `data/raw/escrutinio/`. Pueden ser uno o varios archivos — el script los
   suma todos.
2. Si cambian los candidatos, partidos o la división político-administrativa,
   reemplaza también los archivos correspondientes en `data/raw/` (mismo
   formato de ancho fijo de la Registraduría) y corre primero:
   ```bash
   python3 scripts/01_parse_catalogs.py
   ```
3. Agrega los votos a los tres niveles:
   ```bash
   python3 scripts/02_download_and_aggregate.py
   ```
4. Genera el archivo que usa el visualizador:
   ```bash
   python3 scripts/03_build_json.py
   ```
5. Sube (o vuelve a subir) `site/index.html` y `site/data/resultados.json`
   a GitHub. El resto de los archivos son insumos de trabajo, no hace falta
   subirlos de nuevo si no cambiaron.

Requiere Python 3 (sin librerías externas — solo usa la librería estándar).

## Cómo publicar el sitio (GitHub Pages, sin costo)

1. Entra a tu repositorio en GitHub → pestaña **Settings** → sección **Pages**
   (menú izquierdo).
2. En "Source", elige **Deploy from a branch**, rama **main**, carpeta **/(root)**.
   Guarda.
3. Espera 1–2 minutos. GitHub te dará una URL como
   `https://miltonrojasb.github.io/visualizador-electoral-2026/`.
4. Abre esa URL y entra a la carpeta `site/` (o mueve `site/index.html` a la
   raíz del repo si prefieres que la URL principal abra el visualizador
   directamente).

## Notas sobre los datos

- Los códigos de departamento y municipio son los internos de la
  Registraduría (DIVIPOL), **no** los códigos DANE.
- Los candidatos "CARLOS EDUARDO CAICEDO OMAR" y "LUIS GILBERTO MURILLO
  URRUTIA" aparecen con 0 votos en todas las mesas del país — esto es un dato
  real del escrutinio (verificado contra los 7 archivos fuente), no un error
  de procesamiento; lo más probable es que hayan retirado su candidatura
  manteniendo la casilla en el tarjetón.
- Los archivos CSV de escrutinio mesa a mesa (~100 MB en total) no se
  incluyen en este paquete por su tamaño. Si necesitas reprocesar desde cero,
  puedes volver a descargarlos de tu carpeta de Google Drive
  (`Presidenciales_2026`) y colocarlos en `data/raw/escrutinio/`.
