# Guía para construir el corpus

El enunciado lo dice explícitamente: *el corpus determina el desempeño más que el
modelo*. Esta guía explica qué descargar, en qué orden y cómo dejarlo para que el
pipeline lo consuma sin intervención.

---

## 1. Principios (cómo se gana puntaje con el corpus)

1. **Cada norma que falte es un punto perdido tres veces**: en la exactitud, en
   RAGAS y en citas, porque el modelo no puede citar lo que no recuperó. Las
   citas se comparan por **cuerpo normativo** (ley/código/sentencia), así que
   tener *el documento completo correcto* importa más que la perfección de cada artículo.
2. **Prioricen por peso en el banco**, no por intuición. Hay tres fuentes de señal:
   - Tabla de composición por área (enunciado §4.2): constitucional 134,
     administrativo 124, penal 123, procesal 111, comercial 104, civil 102,
     familia 93, tributario 92, laboral 87, mercados 72.
   - `data/seed_targets.json`: el campo `items_del_banco` dice cuántas preguntas
     del banco completo se apoyan en cada norma (Constitución 90, CGP 65, CST 37,
     Estatuto Tributario 35, Decisión 486 23, Estatuto del Consumidor 13…).
   - Los `legal_basis` de la muestra. **Ojo**: el seed es “deliberadamente no
     exhaustivo” y le faltan códigos enormes que la muestra sí cita (Código
     Civil, Código de Comercio, Código Penal, CPACA, Ley 472 de 1998, Ley 1562
     de 2012…). Esa es la brecha que el reto quiere que cierren.
3. **Texto oficial y completo** (compilado con modificaciones). Nada de resúmenes,
   blogs, libros de doctrina con derechos de autor ni textos generados por IA.
4. **Nunca** metan al corpus el banco de preguntas, la muestra o cualquier
   documento con las respuestas esperadas: es causal de descalificación.
5. Cuando el pipeline exista, corran `python -m src.eval.brechas`: les dice qué
   normas citadas por la muestra y por el seed **aún no están** en el corpus.
   Úsenlo como guía, sin obsesionarse con 50 preguntas (las del sábado son otras 992).

## 2. Qué descargar, por prioridad

Todas las normas se consiguen en fuentes públicas admitidas: Secretaría del
Senado (`secretariasenado.gov.co/senado/basedoc/`), SUIN-Juriscol
(`suin-juriscol.gov.co`), relatorías de la Corte Constitucional, Corte Suprema
y Consejo de Estado, DIAN, SIC y Diario Oficial.

### Nivel 1 — imprescindible (primer día)

| Documento | doc_id sugerido | Áreas principales |
|---|---|---|
| Constitución Política de 1991 | `constitucion_1991` | todas |
| Código Civil (Ley 57 de 1887) | `codigo_civil` | civil, familia |
| Código General del Proceso (Ley 1564 de 2012) | `ley_1564_2012` | procesal, civil, familia |
| Código de Comercio (Decreto 410 de 1971) | `codigo_comercio` | comercial |
| Código Penal (Ley 599 de 2000) | `ley_599_2000` | penal |
| Código de Procedimiento Penal (Ley 906 de 2004) | `ley_906_2004` | penal, procesal |
| CPACA (Ley 1437 de 2011, con Ley 2080 de 2021) | `ley_1437_2011` | administrativo, procesal |
| Código Sustantivo del Trabajo | `codigo_sustantivo_trabajo` | laboral |
| Código Procesal del Trabajo (Decreto-Ley 2158 de 1948) | `codigo_procesal_trabajo` | laboral, procesal |
| Estatuto Tributario (Decreto 624 de 1989) | `estatuto_tributario` | tributario |
| Estatuto del Consumidor (Ley 1480 de 2011) | `ley_1480_2011` | mercados, civil |
| Decisión 486 de 2000 (CAN, propiedad industrial) | `decision_andina_486` | mercados, comercial |
| Código de la Infancia y la Adolescencia (Ley 1098 de 2006) | `ley_1098_2006` | familia, penal |

### Nivel 2 — leyes de alto impacto por área

- **Constitucional**: Decreto 2591 de 1991 (tutela), Decreto 2067 de 1991,
  Ley 472 de 1998 (acciones populares y de grupo), Ley 393 de 1997 (cumplimiento),
  Ley 1095 de 2006 (hábeas corpus), Ley 137 de 1994 (estados de excepción),
  Ley 270 de 1996 (Estatutaria de la Administración de Justicia), Ley 1757 de 2015.
- **Administrativo**: Ley 80 de 1993, Ley 1150 de 2007, Ley 1474 de 2011,
  Decreto 1082 de 2015, Ley 1755 de 2015 (derecho de petición), Ley 489 de 1998,
  Ley 909 de 2004, Código General Disciplinario (Ley 1952 de 2019, con Ley 2094 de 2021),
  Ley 678 de 2001 (repetición).
- **Penal**: Ley 600 de 2000, Ley 1257 de 2008, Ley 1453 de 2011.
- **Procesal**: Ley 2220 de 2022 (conciliación), Ley 1563 de 2012 (arbitraje),
  Ley 2213 de 2022 (virtualidad), Código Nacional de Seguridad y Convivencia (Ley 1801 de 2016).
- **Comercial y sociedades**: Ley 222 de 1995, Ley 1258 de 2008 (SAS),
  Ley 1116 de 2006 (insolvencia), Decreto 663 de 1993 (EOSF), Ley 527 de 1999,
  Ley 964 de 2005, Decreto 4334 de 2008, Ley 1676 de 2013.
- **Civil**: Ley 153 de 1887, Ley 820 de 2003, Decreto 960 de 1970, Ley 791 de 2002.
- **Familia**: Ley 54 de 1990 y Ley 979 de 2005 (unión marital), Ley 25 de 1992,
  Ley 721 de 2001, Ley 1996 de 2019 (capacidad legal), Ley 1257 de 2008.
- **Tributario**: Leyes 1607 de 2012, 1819 de 2016, 2010 de 2019, 2155 de 2021,
  2277 de 2022; Decreto 1625 de 2016 (DUR tributario, extenso: priorizar libros relevantes).
- **Laboral**: Ley 100 de 1993, Ley 50 de 1990, Ley 789 de 2002, Ley 1010 de 2006,
  Ley 1562 de 2012, Ley 2101 de 2021, Ley 2141 de 2021, Ley 2466 de 2025 (reforma laboral).
- **Mercados**: Ley 1581 de 2012 y su reglamentación, Ley 1266 de 2008,
  Ley 256 de 1996, Ley 155 de 1959, Decreto 2153 de 1992, Ley 1340 de 2009,
  Decreto 4886 de 2011, Ley 23 de 1982, Decisión 351 de 1993.

Verifiquen cada número y año en la fuente oficial antes de incorporarlo; esta
lista es un punto de partida y no reemplaza la revisión del equipo.

### Nivel 3 — jurisprudencia

- Todas las sentencias de `seed_targets.json` (hay ~150, casi todas con 1–3 ítems).
  Empiecen por las de mayor `items_del_banco` (C-355/06, C-207/19, SL-3385/22, T-323/24…).
- **Cuidado con el seed**: para sentencias SL, SP, SC y STC pone como fuente la
  Corte Constitucional, pero son de la **Corte Suprema de Justicia** (salas
  Laboral, Penal y Civil). Búsquenlas en la relatoría de la Corte Suprema.
  Las sentencias de unificación del Consejo de Estado (CE-SUJ) van en su relatoría.
- Las sentencias son largas: prioricen la versión completa en HTML de la
  relatoría (Corte Constitucional: `corteconstitucional.gov.co/relatoria/<año>/<C-355-06>.htm`).
- Sentencias hito que suelen aparecer en preguntas de “precedente” y “ratio
  decidendi”: T-760 de 2008, C-355 de 2006, SU-214 de 2016, T-406 de 1992, C-577 de 2011.

**Meta razonable al viernes**: todo el nivel 1, la mayoría del nivel 2 de las
cinco áreas más pesadas y todas las sentencias del seed con ≥ 2 ítems.

## 3. Formato de la carpeta (contrato con el pipeline)

La carpeta puede vivir donde quieran (p. ej. una carpeta sincronizada de
OneDrive). Pongan su ruta en `.env` como `CORPUS_RAW_DIR`. Estructura:

```
<CORPUS_RAW_DIR>/
├── fuentes.csv                     ← una fila por documento (obligatorio)
├── normas/
│   ├── constitucion_1991.html
│   ├── ley_1564_2012.html
│   ├── codigo_civil/               ← si la norma viene partida en varias páginas,
│   │   ├── codigo_civil.html       ← una subcarpeta con todas (se unen en orden alfabético)
│   │   ├── codigo_civil_pr001.html
│   │   └── ...
│   └── decreto_2153_1992.pdf
└── jurisprudencia/
    ├── sentencia_c-355_2006.htm
    └── sentencia_sl-3385_2022.pdf
```

`fuentes.csv` (separador `,` o `;`, UTF-8; se puede editar en Excel y
“Guardar como CSV UTF-8”):

| Columna | Obligatoria | Ejemplo | Notas |
|---|---|---|---|
| `doc_id` | sí | `ley_1150_2007` | minúsculas, sin tildes ni espacios, único |
| `archivo` | sí | `normas/ley_1150_2007.html` | archivo o subcarpeta, relativo a la carpeta |
| `titulo` | sí | `Ley 1150 de 2007` | título oficial |
| `tipo` | sí | `ley` | `constitucion`, `codigo`, `ley`, `decreto`, `decreto_ley`, `acto_legislativo`, `decision_andina`, `resolucion`, `circular`, `sentencia`, `concepto` |
| `numero` | según tipo | `1150` | para sentencias: `C-355`, `SL-3385` |
| `anio` | según tipo | `2007` | |
| `organo_emisor` | sí | `Congreso de la República` | |
| `fuente` | sí | `Secretaría del Senado` | |
| `url` | sí | `http://www.secretariasenado.gov.co/...` | URL exacta de descarga (la bitácora exige reconstruir el corpus desde aquí) |
| `fecha_consulta` | sí | `2026-09-29` | |
| `areas` | sí | `Derecho administrativo\|Derecho laboral` | nombres oficiales separados por `\|` |
| `vigencia` | no | `vigente` | `vigente`, `derogada`, `parcial` |
| `notas` | no | | cualquier observación |

Para códigos que son leyes con número (CGP = Ley 1564 de 2012, Código Penal =
Ley 599 de 2000, CPACA = Ley 1437 de 2011, Código de la Infancia = Ley 1098 de
2006, Estatuto Tributario = Decreto 624 de 1989, Estatuto del Consumidor = Ley
1480 de 2011) usen `tipo=codigo` **y** llenen `numero`/`anio`: el pipeline
genera el encabezado “Código General del Proceso (Ley 1564 de 2012), artículo N.”,
que el evaluador reconoce por ambas vías.

## 4. Consejos prácticos de descarga

- **Secretaría del Senado**: los códigos largos vienen partidos en varias
  páginas (`…_pr001.html`, `…_pr002.html`, …). Descarguen **todas** o el
  código quedará incompleto. Guarden el HTML tal cual (“Guardar como → Página
  web, solo HTML”); el pipeline limpia la navegación.
- Las páginas del Senado traen “Notas de vigencia” y “Jurisprudencia
  vigencia” debajo de cada artículo: **déjenlas**, el pipeline las separa
  como fragmentos aparte y sirven para preguntas de vigencia y precedente.
- **SUIN-Juriscol** sirve cuando el Senado no tiene la norma (decretos,
  normas antiguas). Guarden el HTML de la vista del documento.
- **PDF escaneados**: si al seleccionar texto en el PDF no se selecciona nada,
  es imagen; el pipeline intentará OCR, pero si existe versión HTML, prefiéranla.
- **OneDrive**: marquen la carpeta como “Mantener siempre en este dispositivo”.
  Los archivos “solo en línea” son marcadores de posición y fallan al leerse.
- Anoten `url` y `fecha_consulta` **en el momento** de descargar; reconstruir
  esos datos después cuesta horas y vale 1,5 puntos de la bitácora.
- Nombren los archivos con el `doc_id` para no confundirse.

## 5. Control de calidad (antes de pedir reindexar)

1. `python -m src.corpus.validar` → cero errores en `fuentes.csv`.
2. `python -m src.corpus.build` → revisen el resumen: número de artículos por
   documento. Referencias aproximadas: Constitución ≈ 380 artículos + transitorios;
   Código Civil ≈ 2.684; Código de Comercio ≈ 2.032; CGP ≈ 627. Si un código
   sale con muy pocos artículos, falta alguna página o falló la segmentación.
3. Abran `build/corpus/<doc_id>.txt` y lean tres artículos al azar: encabezado
   correcto, sin menús ni basura.
4. `python -m src.eval.recuperacion --split sample` → el recall@10 de cuerpos
   debe subir cada vez que agregan documentos pertinentes. Si no sube, el
   problema es de recuperación, no de corpus.
5. Anoten cada incorporación importante en la tabla “Evolución del puntaje” de
   `CORPUS.md` (la exige la bitácora).

## 6. Reparto sugerido del trabajo del equipo

- Persona A: nivel 1 completo (códigos grandes) + verificación de conteos.
- Persona B: nivel 2 de constitucional, administrativo, penal y procesal.
- Persona C: nivel 2 de comercial, civil, familia, tributario, laboral, mercados + jurisprudencia del seed.
- Todos: `fuentes.csv` al día, `url` y `fecha_consulta` al descargar.
