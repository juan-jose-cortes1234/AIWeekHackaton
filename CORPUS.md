# Bitácora del corpus — <Nombre del equipo>

Bitácora exigida en el paso 5 del enunciado (5 puntos: inventario completo y
trazable 2; justificación frente a la composición del banco 1,5; corpus
reconstruible a partir de las URL declaradas 1,5).

Las tablas entre marcas `AUTO` las regenera `python -m src.corpus.manifest` a
partir de `fuentes.csv` y del corpus procesado; no las editen a mano. La prosa
(criterio, método, lectura de la curva) la escribe el equipo; los borradores
están marcados con `BORRADOR`.

---

## 1. Inventario

Un registro por documento incorporado. Coincide con `corpus_manifest.json`.

<!-- AUTO:inventario -->
| doc_id | Título | Fuente | URL | Fecha de consulta | Artículos | Fragmentos | Áreas |
|---|---|---|---|---|---:|---:|---|
| `constitucion_1991` | Constitución Política de Colombia de 1991 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=4125 | 2026-09-28 | 446 | 731 | Constitucional, Administrativo, Penal, Procesal, Comercial, Civil, Familia, Tributario, Laboral, Mercados |
| `codigo_civil` | Código Civil | Ministerio de Relaciones Exteriores - Normograma | https://cancilleria.gov.co/sites/default/files/Normograma/docs/codigo_civil.htm | 2026-09-28 | 2684 | 3799 | Civil, Familia |
| `ley_1564_2012` | Código General del Proceso (Ley 1564 de 2012) | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=48425 | 2026-09-28 | 628 | 913 | Procesal, Civil, Familia |
| `codigo_comercio` | Código de Comercio | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=41102 | 2026-09-28 | 2032 | 2079 | Comercial |
| `ley_599_2000` | Código Penal (Ley 599 de 2000) | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=6388 | 2026-09-28 | 598 | 670 | Penal |
| `ley_906_2004` | Código de Procedimiento Penal (Ley 906 de 2004) | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=14787 | 2026-09-28 | 583 | 645 | Penal, Procesal |
| `ley_1437_2011` | Código de Procedimiento Administrativo y de lo Contencioso Administrativo (Ley 1437 de 2011) | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=41249 | 2026-09-28 | 321 | 434 | Administrativo, Procesal |
| `codigo_sustantivo_trabajo` | Código Sustantivo del Trabajo | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=199983 | 2026-09-28 | 493 | 553 | Laboral |
| `codigo_procesal_trabajo` | Código Procesal del Trabajo y de la Seguridad Social | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=5259 | 2026-09-28 | 149 | 154 | Laboral, Procesal |
| `estatuto_tributario` | Estatuto Tributario (Decreto 624 de 1989) | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=6533 | 2026-09-28 | 1277 | 1752 | Tributario |
| `ley_1480_2011` | Estatuto del Consumidor (Ley 1480 de 2011) | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=44306 | 2026-09-28 | 75 | 115 | Civil, Mercados |
| `decision_andina_486` | Decisión 486 de 2000 - Régimen Común sobre Propiedad Industrial | Secretaría General de la Comunidad Andina | https://www.comunidadandina.org/StaticFiles/DocOf/DEC486.pdf | 2026-09-28 | 280 | 287 | Comercial, Mercados |
| `ley_1098_2006` | Código de la Infancia y la Adolescencia (Ley 1098 de 2006) | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=22106 | 2026-09-28 | 216 | 265 | Familia, Penal |
| `decreto_2591_1991` | Decreto 2591 de 1991 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=5304 | 2026-09-28 | 34 | 41 | Constitucional, Procesal |
| `decreto_2067_1991` | Decreto 2067 de 1991 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=30150 | 2026-09-28 | 53 | 54 | Constitucional, Procesal |
| `ley_0472_1998` | Ley 472 de 1998 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=188 | 2026-09-28 | 87 | 96 | Constitucional, Administrativo, Procesal |
| `ley_0393_1997` | Ley 393 de 1997 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=338 | 2026-09-28 | 32 | 33 | Constitucional, Administrativo, Procesal |
| `ley_1095_2006` | Ley 1095 de 2006 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=22087 | 2026-09-28 | 10 | 11 | Constitucional, Penal, Procesal |
| `ley_0137_1994` | Ley 137 de 1994 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=13966 | 2026-09-28 | 59 | 68 | Constitucional, Administrativo |
| `ley_0270_1996` | Ley 270 de 1996 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=6548 | 2026-09-28 | 233 | 289 | Constitucional, Procesal, Administrativo |
| `ley_1757_2015` | Ley 1757 de 2015 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=65335 | 2026-09-28 | 113 | 124 | Constitucional, Administrativo |
| `ley_0080_1993` | Ley 80 de 1993 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=304 | 2026-09-28 | 88 | 142 | Administrativo |
| `ley_1150_2007` | Ley 1150 de 2007 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=184686 | 2026-09-28 | 33 | 68 | Administrativo |
| `ley_1474_2011` | Ley 1474 de 2011 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=43292 | 2026-09-28 | 142 | 180 | Administrativo, Penal |
| `decreto_1082_2015` | Decreto 1082 de 2015 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=77653 | 2026-09-28 | 1042 | 1324 | Administrativo |
| `ley_1755_2015` | Ley 1755 de 2015 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=65334 | 2026-09-28 | 23 | 25 | Constitucional, Administrativo |
| `ley_0489_1998` | Ley 489 de 1998 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=186 | 2026-09-28 | 121 | 141 | Administrativo |
| `ley_0909_2004` | Ley 909 de 2004 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=14861 | 2026-09-28 | 58 | 92 | Administrativo, Laboral |
| `ley_1952_2019` | Código General Disciplinario (Ley 1952 de 2019) | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=90324 | 2026-09-28 | 273 | 301 | Administrativo |
| `ley_2094_2021` | Ley 2094 de 2021 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=165113 | 2026-09-28 | 132 | 149 | Administrativo |
| `ley_0678_2001` | Ley 678 de 2001 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=4164 | 2026-09-28 | 31 | 39 | Administrativo, Procesal |
| `ley_0600_2000` | Código de Procedimiento Penal (Ley 600 de 2000) | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=6389 | 2026-09-28 | 536 | 563 | Penal, Procesal |
| `ley_1257_2008` | Ley 1257 de 2008 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=34054 | 2026-09-28 | 39 | 51 | Penal, Familia, Constitucional |
| `ley_1453_2011` | Ley 1453 de 2011 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=43202 | 2026-09-28 | 175 | 215 | Penal, Procesal |
| `ley_2220_2022` | Ley 2220 de 2022 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=188766 | 2026-09-28 | 152 | 179 | Procesal, Administrativo, Civil, Familia, Laboral |
| `ley_1563_2012` | Ley 1563 de 2012 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=48366 | 2026-09-28 | 116 | 144 | Procesal, Comercial, Civil |
| `ley_2213_2022` | Ley 2213 de 2022 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=187626 | 2026-09-28 | 15 | 21 | Procesal |
| `ley_1801_2016` | Código Nacional de Seguridad y Convivencia Ciudadana (Ley 1801 de 2016) | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=80538 | 2026-09-28 | 249 | 346 | Procesal, Administrativo |
| `ley_0222_1995` | Ley 222 de 1995 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=6739 | 2026-09-28 | 247 | 271 | Comercial |
| `ley_1258_2008` | Ley 1258 de 2008 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=34130 | 2026-09-28 | 46 | 50 | Comercial |
| `ley_1116_2006` | Ley 1116 de 2006 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=22657 | 2026-09-28 | 126 | 161 | Comercial, Procesal |
| `decreto_0663_1993` | Estatuto Orgánico del Sistema Financiero (Decreto 663 de 1993) | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=1348 | 2026-09-28 | 341 | 758 | Comercial, Mercados |
| `ley_0527_1999` | Ley 527 de 1999 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=4276 | 2026-09-28 | 47 | 51 | Comercial, Mercados |
| `ley_0964_2005` | Ley 964 de 2005 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=22412 | 2026-09-28 | 86 | 127 | Comercial, Mercados |
| `decreto_4334_2008` | Decreto 4334 de 2008 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=33747 | 2026-09-28 | 15 | 23 | Comercial, Mercados |
| `ley_1676_2013` | Ley 1676 de 2013 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=54297 | 2026-09-28 | 91 | 111 | Comercial, Civil |
| `ley_0153_1887` | Ley 153 de 1887 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=15805 | 2026-09-28 | 327 | 330 | Civil, Tributario |
| `ley_0820_2003` | Ley 820 de 2003 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=8738 | 2026-09-28 | 43 | 55 | Civil, Comercial |
| `decreto_0960_1970` | Estatuto del Notariado (Decreto 960 de 1970) | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=149249 | 2026-09-28 | 233 | 237 | Civil |
| `ley_0791_2002` | Ley 791 de 2002 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=6921 | 2026-09-28 | 13 | 14 | Civil |
| `ley_0054_1990` | Ley 54 de 1990 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=30896 | 2026-09-28 | 9 | 10 | Familia |
| `ley_0979_2005` | Ley 979 de 2005 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=30898 | 2026-09-28 | 6 | 10 | Familia |
| `ley_0025_1992` | Ley 25 de 1992 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=30900 | 2026-09-28 | 15 | 17 | Familia |
| `ley_0721_2001` | Ley 721 de 2001 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=9565 | 2026-09-28 | 12 | 15 | Familia |
| `ley_1996_2019` | Ley 1996 de 2019 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=99712 | 2026-09-28 | 63 | 74 | Familia, Civil |
| `ley_1607_2012` | Ley 1607 de 2012 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=51040 | 2026-09-28 | 320 | 449 | Tributario |
| `ley_1819_2016` | Ley 1819 de 2016 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=79140 | 2026-09-28 | 527 | 822 | Tributario |
| `ley_2010_2019` | Ley 2010 de 2019 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=159687 | 2026-09-28 | 236 | 362 | Tributario |
| `ley_2155_2021` | Ley 2155 de 2021 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=170902 | 2026-09-28 | 68 | 138 | Tributario |
| `ley_2277_2022` | Ley 2277 de 2022 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=199883 | 2026-09-28 | 152 | 213 | Tributario |
| `decreto_1625_2016` | Decreto Único Reglamentario en Materia Tributaria (Decreto 1625 de 2016) | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=83233 | 2026-09-28 | 2116 | 2945 | Tributario |
| `ley_0100_1993` | Ley 100 de 1993 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=5248 | 2026-09-28 | 288 | 350 | Laboral, Constitucional |
| `ley_0050_1990` | Ley 50 de 1990 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=281 | 2026-09-28 | 152 | 171 | Laboral |
| `ley_0789_2002` | Ley 789 de 2002 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=6778 | 2026-09-28 | 54 | 110 | Laboral |
| `ley_1010_2006` | Ley 1010 de 2006 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=18843 | 2026-09-28 | 19 | 25 | Laboral |
| `ley_1562_2012` | Ley 1562 de 2012 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=48365 | 2026-09-28 | 36 | 63 | Laboral |
| `ley_2101_2021` | Ley 2101 de 2021 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=166506 | 2026-09-28 | 9 | 11 | Laboral |
| `ley_2141_2021` | Ley 2141 de 2021 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=168351 | 2026-09-28 | 4 | 6 | Laboral, Familia |
| `ley_2466_2025` | Ley 2466 de 2025 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=260676 | 2026-09-28 | 71 | 96 | Laboral |
| `ley_1581_2012` | Ley 1581 de 2012 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=49981 | 2026-09-28 | 30 | 39 | Mercados, Constitucional |
| `decreto_1377_2013` | Decreto 1377 de 2013 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=53646 | 2026-09-28 | 28 | 33 | Mercados |
| `ley_1266_2008` | Ley 1266 de 2008 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=34488 | 2026-09-28 | 24 | 45 | Mercados, Constitucional |
| `ley_0256_1996` | Ley 256 de 1996 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=38871 | 2026-09-28 | 33 | 34 | Mercados, Comercial |
| `ley_0155_1959` | Ley 155 de 1959 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=38169 | 2026-09-28 | 20 | 25 | Mercados |
| `decreto_2153_1992` | Decreto 2153 de 1992 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=38168 | 2026-09-28 | 59 | 75 | Mercados, Administrativo |
| `ley_1340_2009` | Ley 1340 de 2009 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=36912 | 2026-09-28 | 34 | 47 | Mercados |
| `decreto_4886_2011` | Decreto 4886 de 2011 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=66371 | 2026-09-28 | 30 | 89 | Mercados, Administrativo |
| `ley_0023_1982` | Ley 23 de 1982 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=3431 | 2026-09-28 | 262 | 271 | Mercados |
| `decision_andina_351` | Decisión 351 de 1993 - Régimen Común sobre Derecho de Autor y Derechos Conexos | Secretaría General de la Comunidad Andina | https://www.comunidadandina.org/StaticFiles/DocOf/DEC351.pdf | 2026-09-28 | 61 | 67 | Mercados |
| `sentencia_c-355_2006` | Sentencia C-355 de 2006 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2006/c-355-06.htm | 2026-09-28 | — | 1101 | Constitucional, Penal |
| `sentencia_c-207_2019` | Sentencia C-207 de 2019 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2019/c-207-19.htm | 2026-09-28 | — | 300 | Administrativo |
| `sentencia_sl-3385_2022` | Sentencia SL-3385 de 2022 | Corte Suprema de Justicia - Relatoría | https://www.cortesuprema.gov.co/corte/wp-content/uploads/relatorias/la/bnov2022/SL3385-2022.pdf | 2026-09-28 | — | 21 | Laboral |
| `sentencia_t-323_2024` | Sentencia T-323 de 2024 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2024/t-323-24.htm | 2026-09-28 | — | 270 | Constitucional |
| `sentencia_t-760_2008` | Sentencia T-760 de 2008 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2008/t-760-08.htm | 2026-09-28 | — | 883 | Administrativo, Constitucional |
| `sentencia_c-394_2017` | Sentencia C-394 de 2017 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2017/c-394-17.htm | 2026-09-28 | — | 193 | Constitucional, Familia |
| `sentencia_t-243_2018` | Sentencia T-243 de 2018 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2018/t-243-18.htm | 2026-09-28 | — | 75 | Laboral |
| `sentencia_c-55_2022` | Sentencia C-55 de 2022 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2022/c-055-22.htm | 2026-09-28 | — | 942 | Constitucional, Penal |
| `sentencia_su-315_2025` | Sentencia SU-315 de 2025 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2025/su315-25.htm | 2026-09-28 | — | 175 | Civil |
| `sentencia_c-582_1999` | Sentencia C-582 de 1999 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/1999/c-582-99.htm | 2026-09-28 | — | 23 | Constitucional |
| `sentencia_c-431_2001` | Sentencia C-431 de 2001 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2001/c-431-01.htm | 2026-09-28 | — | 14 | Constitucional, Penal |
| `sentencia_c-507_2004` | Sentencia C-507 de 2004 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2004/c-507-04.htm | 2026-09-28 | — | 259 | Familia |
| `sentencia_c-35_2009` | Sentencia C-35 de 2009 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2009/c-035-09.htm | 2026-09-28 | — | 77 | Tributario |
| `sentencia_c-127_2011` | Sentencia C-127 de 2011 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2011/c-127-11.htm | 2026-09-28 | — | 71 | Constitucional |
| `sentencia_c-746_2011` | Sentencia C-746 de 2011 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2011/c-746-11.htm | 2026-09-28 | — | 32 | Constitucional, Familia |
| `sentencia_c-748_2011` | Sentencia C-748 de 2011 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2011/c-748-11.htm | 2026-09-28 | — | 533 | Civil, Mercados |
| `sentencia_c-259_2015` | Sentencia C-259 de 2015 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2015/c-259-15.htm | 2026-09-28 | — | 121 | Administrativo, Procesal |
| `sentencia_su-214_2016` | Sentencia SU-214 de 2016 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2016/su214-16.htm | 2026-09-28 | — | 563 | Familia |
| `sentencia_t-547_2017` | Sentencia T-547 de 2017 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2017/t-547-17.htm | 2026-09-28 | — | 78 | Constitucional, Laboral |
| `sentencia_c-117_2018` | Sentencia C-117 de 2018 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2018/c-117-18.htm | 2026-09-28 | — | 188 | Tributario |
| `sentencia_c-15_2018` | Sentencia C-15 de 2018 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2018/c-015-18.htm | 2026-09-28 | — | 144 | Constitucional, Penal |
| `sentencia_sl-648_2018` | Sentencia SL-648 de 2018 | Corte Suprema de Justicia - Relatoría | https://www.cortesuprema.gov.co/corte/wp-content/uploads/relatorias/la/bmar2018/SL648-2018.pdf | 2026-09-28 | — | 49 | Laboral |
| `sentencia_c-134_2019` | Sentencia C-134 de 2019 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2019/c-134-19.htm | 2026-09-28 | — | 45 | Constitucional, Familia |
| `sentencia_sp-1945_2019` | Sentencia SP-1945 de 2019 | Corte Suprema de Justicia - Relatoría | https://www.cortesuprema.gov.co/corte/wp-content/uploads/relatorias/pe/b1ago2019/SP1945-2019%2850523%29.PDF | 2026-09-28 | — | 30 | Penal |
| `sentencia_c-94_2021` | Sentencia C-94 de 2021 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2021/c-094-21.htm | 2026-09-28 | — | 126 | Constitucional |
| `sentencia_c-164_2022` | Sentencia C-164 de 2022 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2022/c-164-22.htm | 2026-09-28 | — | 159 | Constitucional, Penal |
| `sentencia_sp-1680_2022` | Sentencia SP-1680 de 2022 | Corte Suprema de Justicia - Relatoría | https://cortesuprema.gov.co/corte/wp-content/uploads/relatorias/pe/b1may2022/SP1680-2022%2860875%29.pdf | 2026-09-28 | — | 39 | Penal |
| `sentencia_c-540_2023` | Sentencia C-540 de 2023 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2023/c-540-23.htm | 2026-09-28 | — | 103 | Tributario |
| `sentencia_c-500_2024` | Sentencia C-500 de 2024 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2024/c-500-24.htm | 2026-09-28 | — | 95 | Procesal, Tributario |
| `sentencia_c-96_2024` | Sentencia C-96 de 2024 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2024/c-096-24.htm | 2026-09-28 | — | 164 | Familia |
| `sentencia_su-111_2025` | Sentencia SU-111 de 2025 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2025/su111-25.htm | 2026-09-28 | — | 180 | Laboral |
| `sentencia_c-149_1993` | Sentencia C-149 de 1993 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/1993/c-149-93.htm | 2026-09-28 | — | 36 | Constitucional |
| `sentencia_c-486_1993` | Sentencia C-486 de 1993 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/1993/c-486-93.htm | 2026-09-28 | — | 62 | Comercial |
| `sentencia_c-225_1995` | Sentencia C-225 de 1995 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/1995/c-225-95.htm | 2026-09-28 | — | 122 | Constitucional |
| `sentencia_c-537_1995` | Sentencia C-537 de 1995 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/1995/c-537-95.htm | 2026-09-28 | — | 54 | Tributario |
| `sentencia_c-22_1996` | Sentencia C-22 de 1996 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/1996/c-022-96.htm | 2026-09-28 | — | 23 | Constitucional |
| `sentencia_c-413_1996` | Sentencia C-413 de 1996 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/1996/c-413-96.htm | 2026-09-28 | — | 20 | Tributario |
| `sentencia_c-239_1997` | Sentencia C-239 de 1997 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/1997/c-239-97.htm | 2026-09-28 | — | 207 | Constitucional |
| `sentencia_c-4_1998` | Sentencia C-4 de 1998 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/1998/c-004-98.htm | 2026-09-28 | — | 24 | Familia |
| `sentencia_c-700_1999` | Sentencia C-700 de 1999 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/1999/c-700-99.htm | 2026-09-28 | — | 218 | Constitucional |
| `sentencia_c-1189_2000` | Sentencia C-1189 de 2000 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2000/c-1189-00.htm | 2026-09-28 | — | 80 | Penal |
| `sentencia_c-533_2000` | Sentencia C-533 de 2000 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2000/c-533-00.htm | 2026-09-28 | — | 23 | Familia |
| `sentencia_t-1001_2001` | Sentencia T-1001 de 2001 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2001/t-1001-01.htm | 2026-09-28 | — | 62 | Constitucional |
| `sentencia_t-1059_2001` | Sentencia T-1059 de 2001 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2001/t-1059-01.htm | 2026-09-28 | — | 44 | Laboral |
| `sentencia_c-1033_2002` | Sentencia C-1033 de 2002 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2002/c-1033-02.htm | 2026-09-28 | — | 41 | Familia |
| `sentencia_c-201_2002` | Sentencia C-201 de 2002 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2002/c-201-02.htm | 2026-09-28 | — | 101 | Laboral |
| `sentencia_c-535_2002` | Sentencia C-535 de 2002 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2002/c-535-02.htm | 2026-09-28 | — | 31 | Laboral |
| `sentencia_c-964_2003` | Sentencia C-964 de 2003 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2003/c-964-03.htm | 2026-09-28 | — | 75 | Familia |
| `sentencia_c-170_2004` | Sentencia C-170 de 2004 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2004/c-170-04.htm | 2026-09-28 | — | 107 | Laboral |
| `sentencia_c-335_2008` | Sentencia C-335 de 2008 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2008/c-335-08.htm | 2026-09-28 | — | 90 | Penal |
| `sentencia_t-1096_2008` | Sentencia T-1096 de 2008 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2008/t-1096-08.htm | 2026-09-28 | — | 65 | Familia |
| `sentencia_c-985_2010` | Sentencia C-985 de 2010 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2010/c-985-10.htm | 2026-09-28 | — | 87 | Familia |
| `sentencia_t-429_2011` | Sentencia T-429 de 2011 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2011/t-429-11.htm | 2026-09-28 | — | 46 | Constitucional |
| `sentencia_c-891_2012` | Sentencia C-891 de 2012 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2012/c-891-12.htm | 2026-09-28 | — | 60 | Tributario |
| `sentencia_t-925_2014` | Sentencia T-925 de 2014 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2014/t-925-14.htm | 2026-09-28 | — | 38 | Constitucional |
| `sentencia_t-970_2014` | Sentencia T-970 de 2014 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2014/t-970-14.htm | 2026-09-28 | — | 108 | Constitucional |
| `sentencia_c-683_2015` | Sentencia C-683 de 2015 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2015/c-683-15.htm | 2026-09-28 | — | 406 | Familia |
| `sentencia_su-240_2015` | Sentencia SU-240 de 2015 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2015/su240-15.htm | 2026-09-28 | — | 100 | Administrativo |
| `sentencia_su-431_2015` | Sentencia SU-431 de 2015 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2015/su431-15.htm | 2026-09-28 | — | 170 | Civil |
| `sentencia_su-500_2015` | Sentencia SU-500 de 2015 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2015/su500-15.htm | 2026-09-28 | — | 222 | Civil |
| `sentencia_su-566_2015` | Sentencia SU-566 de 2015 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2015/su566-15.htm | 2026-09-28 | — | 193 | Administrativo |
| `sentencia_sc-8453_2016` | Sentencia SC-8453 de 2016 | Corte Suprema de Justicia - Relatoría | https://cortesuprema.gov.co/corte/wp-content/uploads/relatorias/ci/doctri2016/SC8453-2016%20%282014-02243-00%29.doc | 2026-09-28 | — | 47 | Comercial |
| `sentencia_t-145_2016` | Sentencia T-145 de 2016 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2016/t-145-16.htm | 2026-09-28 | — | 84 | Laboral |
| `sentencia_t-71_2016` | Sentencia T-71 de 2016 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2016/t-071-16.htm | 2026-09-28 | — | 92 | Familia |
| `sentencia_c-345_2017` | Sentencia C-345 de 2017 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2017/c-345-17.htm | 2026-09-28 | — | 118 | Civil |
| `sentencia_sc-18392_2017` | Sentencia SC-18392 de 2017 | Corte Suprema de Justicia - Relatoría | https://www.cortesuprema.gov.co/corte/wp-content/uploads/2019/02/SC18392-2017-2011-00081-01-1-47.pdf | 2026-09-28 | — | 53 | Comercial |
| `sentencia_c-106_2018` | Sentencia C-106 de 2018 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2018/c-106-18.htm | 2026-09-28 | — | 129 | Constitucional |
| `sentencia_c-131_2018` | Sentencia C-131 de 2018 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2018/c-131-18.htm | 2026-09-28 | — | 70 | Familia |
| `sentencia_c-145_2018` | Sentencia C-145 de 2018 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2018/c-145-18.htm | 2026-09-28 | — | 85 | Comercial |
| `sentencia_sc-1121_2018` | Sentencia SC-1121 de 2018 | Corte Suprema de Justicia - Relatoría | https://cortesuprema.gov.co/corte/wp-content/uploads/2018/10/SC1121-2018-2007-00128-01.pdf | 2026-09-28 | — | 13 | Civil |
| `sentencia_c-145_2020` | Sentencia C-145 de 2020 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2020/c-145-20.htm | 2026-09-28 | — | 313 | Constitucional |
| `sentencia_sl-1730_2020` | Sentencia SL-1730 de 2020 | Corte Suprema de Justicia - Relatoría | https://www.cortesuprema.gov.co/corte/wp-content/uploads/relatorias/la/bjul2020/SL1730-2020.pdf | 2026-09-28 | — | 59 | Laboral |
| `sentencia_su-11_2020` | Sentencia SU-11 de 2020 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2020/su011-20.htm | 2026-09-28 | — | 120 | Administrativo |
| `sentencia_su-455_2020` | Sentencia SU-455 de 2020 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2020/su455-20.htm | 2026-09-28 | — | 105 | Civil |
| `sentencia_c-233_2021` | Sentencia C-233 de 2021 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2021/c-233-21.htm | 2026-09-28 | — | 423 | Constitucional |
| `sentencia_sc-3674_2021` | Sentencia SC-3674 de 2021 | Corte Suprema de Justicia - Relatoría | https://cortesuprema.gov.co/corte/wp-content/uploads/2021/09/SC3674-2021-2015-00017-01.pdf | 2026-09-28 | — | 24 | Comercial |
| `sentencia_sp-3218_2021` | Sentencia SP-3218 de 2021 | Corte Suprema de Justicia - Relatoría | https://cortesuprema.gov.co/corte/wp-content/uploads/relatorias/pe/b1ago2021/SP3218-2021%2847063%29.pdf | 2026-09-28 | — | 106 | Penal |
| `sentencia_su-149_2021` | Sentencia SU-149 de 2021 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2021/su149-21.htm | 2026-09-28 | — | 117 | Laboral |
| `sentencia_su-27_2021` | Sentencia SU-27 de 2021 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2021/su027-21.htm | 2026-09-28 | — | 106 | Laboral |
| `sentencia_su-380_2021` | Sentencia SU-380 de 2021 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2021/su380-21.htm | 2026-09-28 | — | 129 | Civil |
| `sentencia_sp-1167_2022` | Sentencia SP-1167 de 2022 | Corte Suprema de Justicia - Relatoría | https://cortesuprema.gov.co/corte/wp-content/uploads/relatorias/pe/b1may2022/SP1167-2022%2857957%29.pdf | 2026-09-28 | — | 41 | Penal |
| `sentencia_su-207_2022` | Sentencia SU-207 de 2022 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2022/su207-22.htm | 2026-09-28 | — | 134 | Civil |
| `sentencia_c-389_2023` | Sentencia C-389 de 2023 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2023/c-389-23.htm | 2026-09-28 | — | 83 | Tributario |
| `sentencia_c-459_2023` | Sentencia C-459 de 2023 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2023/c-459-23.htm | 2026-09-28 | — | 91 | Constitucional |
| `sentencia_sl-1050_2023` | Sentencia SL-1050 de 2023 | Corte Suprema de Justicia - Relatoría | https://cortesuprema.gov.co/corte/wp-content/uploads/relatorias/la/reiteraciones%20DL/SL1050-2023.pdf | 2026-09-28 | — | 65 | Laboral |
| `sentencia_su-296_2023` | Sentencia SU-296 de 2023 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2023/su296-23.htm | 2026-09-28 | — | 149 | Laboral |
| `sentencia_t-230_2023` | Sentencia T-230 de 2023 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2023/t-230-23.htm | 2026-09-28 | — | 29 | Constitucional |
| `sentencia_sc-3085_2024` | Sentencia SC-3085 de 2024 | Corte Suprema de Justicia - Relatoría | https://archivodigitalapi.cortesuprema.gov.co/share/2024/12/Sentencias/SC3085-2024.pdf | 2026-09-28 | — | 106 | Familia |
| `sentencia_sc-425_2024` | Sentencia SC-425 de 2024 | Corte Suprema de Justicia - Relatoría | https://cortesuprema.gov.co/corte/wp-content/uploads/2024/05/SC425-2024-2019-00063-01.pdf | 2026-09-28 | — | 83 | Comercial |
| `sentencia_su-138_2024` | Sentencia SU-138 de 2024 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2024/su138-24.htm | 2026-09-28 | — | 208 | Civil |
| `sentencia_su-396_2024` | Sentencia SU-396 de 2024 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2024/su396-24.htm | 2026-09-28 | — | 186 | Laboral |
| `sentencia_su-429_2024` | Sentencia SU-429 de 2024 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2024/su429-24.htm | 2026-09-28 | — | 259 | Penal |
| `sentencia_t-445_2024` | Sentencia T-445 de 2024 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2024/t-445-24.htm | 2026-09-28 | — | 138 | Constitucional |
| `sentencia_c-183_2025` | Sentencia C-183 de 2025 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2025/c-183-25.htm | 2026-09-28 | — | 164 | Civil |
| `sentencia_c-276_2025` | Sentencia C-276 de 2025 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2025/c-276-25.htm | 2026-09-28 | — | 128 | Comercial |
| `sentencia_c-332_2025` | Sentencia C-332 de 2025 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2025/c-332-25.htm | 2026-09-28 | — | 108 | Constitucional |
| `sentencia_c-39_2025` | Sentencia C-39 de 2025 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2025/c-039-25.htm | 2026-09-28 | — | 190 | Familia |
| `sentencia_c-80_2025` | Sentencia C-80 de 2025 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2025/c-080-25.htm | 2026-09-28 | — | 128 | Mercados |
| `sentencia_su-425_2025` | Sentencia SU-425 de 2025 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2025/su425-25.htm | 2026-09-28 | — | 79 | Civil |
| `sentencia_t-232_2025` | Sentencia T-232 de 2025 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2025/t-232-25.htm | 2026-09-28 | — | 99 | Familia |
| `sentencia_t-26_2025` | Sentencia T-26 de 2025 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2025/t-026-25.htm | 2026-09-28 | — | 147 | Civil |
| `sentencia_t-262_2025` | Sentencia T-262 de 2025 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2025/t-262-25.htm | 2026-09-28 | — | 108 | Constitucional |
| `sentencia_t-325_2025` | Sentencia T-325 de 2025 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2025/t-325-25.htm | 2026-09-28 | — | 74 | Constitucional |
| `sentencia_t-350_2025` | Sentencia T-350 de 2025 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2025/t-350-25.htm | 2026-09-28 | — | 101 | Familia |
| `sentencia_t-67_2025` | Sentencia T-67 de 2025 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2025/t-067-25.htm | 2026-09-28 | — | 196 | Constitucional |
| `sentencia_t-77_2025` | Sentencia T-77 de 2025 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2025/t-077-25.htm | 2026-09-28 | — | 81 | Familia |
| `sentencia_t-4_2026` | Sentencia T-4 de 2026 | Corte Constitucional - Relatoría | https://www.corteconstitucional.gov.co/relatoria/2026/t-004-26.htm | 2026-09-28 | — | 107 | Civil |
| `cc_t_240_2026` | Sentencia T-240 de 2026 | Relatoría de la Corte Constitucional | https://www.corteconstitucional.gov.co/relatoria/2026/T-240-26.htm | 2026-09-30 | — | 89 | Constitucional, Laboral, Mercados |
| `cc_t_051_2026` | Sentencia T-051 de 2026 | Relatoría de la Corte Constitucional | https://www.corteconstitucional.gov.co/relatoria/2026/T-051-26.htm | 2026-09-30 | — | 112 | Constitucional |
| `cc_su_060_2026` | Sentencia SU-060 de 2026 | Relatoría de la Corte Constitucional | https://www.corteconstitucional.gov.co/relatoria/2026/SU060-26.htm | 2026-09-30 | — | 63 | Constitucional, Penal |
| `cc_c_114_2026` | Sentencia C-114 de 2026 | Relatoría de la Corte Constitucional | https://www.corteconstitucional.gov.co/relatoria/2026/C-114-26.htm | 2026-09-30 | — | 54 | Constitucional, Procesal |
| `cc_t_182_2026` | Sentencia T-182 de 2026 | Relatoría de la Corte Constitucional | https://www.corteconstitucional.gov.co/relatoria/2026/T-182-26.htm | 2026-09-30 | — | 122 | Constitucional, Civil |
| `cc_t_176_2026` | Sentencia T-176 de 2026 | Relatoría de la Corte Constitucional | https://www.corteconstitucional.gov.co/relatoria/2026/T-176-26.htm | 2026-09-30 | — | 98 | Constitucional, Procesal |
| `cc_t_070_2026` | Sentencia T-070 de 2026 | Relatoría de la Corte Constitucional | https://www.corteconstitucional.gov.co/relatoria/2026/T-070-26.htm | 2026-09-30 | — | 39 | Constitucional, Administrativo, Mercados |
| `cc_t_132_2026` | Sentencia T-132 de 2026 | Relatoría de la Corte Constitucional | https://www.corteconstitucional.gov.co/relatoria/2026/T-132-26.htm | 2026-09-30 | — | 94 | Constitucional, Laboral, Familia |
| `cc_t_258_2026` | Sentencia T-258 de 2026 | Relatoría de la Corte Constitucional | https://www.corteconstitucional.gov.co/relatoria/2026/T-258-26.htm | 2026-09-30 | — | 238 | Constitucional |
| `cc_t_160_2026` | Sentencia T-160 de 2026 | Relatoría de la Corte Constitucional | https://www.corteconstitucional.gov.co/relatoria/2026/T-160-26.htm | 2026-09-30 | — | 65 | Constitucional, Administrativo |
| `cc_t_205_2026` | Sentencia T-205 de 2026 | Relatoría de la Corte Constitucional | https://www.corteconstitucional.gov.co/relatoria/2026/T-205-26.htm | 2026-09-30 | — | 72 | Constitucional, Administrativo |
| `cc_t_128_2026` | Sentencia T-128 de 2026 | Relatoría de la Corte Constitucional | https://www.corteconstitucional.gov.co/relatoria/2026/T-128-26.htm | 2026-09-30 | — | 96 | Constitucional, Administrativo |
| `cc_t_103_2026` | Sentencia T-103 de 2026 | Relatoría de la Corte Constitucional | https://www.corteconstitucional.gov.co/relatoria/2026/T-103-26.htm | 2026-09-30 | — | 85 | Constitucional, Administrativo |
| `cc_t_174_2026` | Sentencia T-174 de 2026 | Relatoría de la Corte Constitucional | https://www.corteconstitucional.gov.co/relatoria/2026/T-174-26.htm | 2026-09-30 | — | 126 | Constitucional, Mercados |
| `cc_t_153_2026` | Sentencia T-153 de 2026 | Relatoría de la Corte Constitucional | https://www.corteconstitucional.gov.co/relatoria/2026/T-153-26.htm | 2026-09-30 | — | 126 | Constitucional, Administrativo |
| `cc_t_247_2026` | Sentencia T-247 de 2026 | Relatoría de la Corte Constitucional | https://www.corteconstitucional.gov.co/relatoria/2026/T-247-26.htm | 2026-09-30 | — | 84 | Constitucional |
| `cc_t_231_2026` | Sentencia T-231 de 2026 | Relatoría de la Corte Constitucional | https://www.corteconstitucional.gov.co/relatoria/2026/T-231-26.htm | 2026-09-30 | — | 279 | Constitucional, Administrativo |
| `cc_t_054_2026` | Sentencia T-054 de 2026 | Relatoría de la Corte Constitucional | https://www.corteconstitucional.gov.co/relatoria/2026/T-054-26.htm | 2026-09-30 | — | 132 | Constitucional, Mercados |
| `ce_concepto_2472_2021` | Concepto Rad. 11001-03-06-000-2021-00160-00 (2472) | Consejo de Estado / SAMAI | https://consejodeestado.gov.co/documentos/boletines/260/11001-03-06-000-2021-00160-00%282472%29.pdf | 2026-09-30 | — | 50 | Administrativo |
| `dian_oficio_26859_2019` | Oficio DIAN 26859 de 2019 | Normograma DIAN | https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_26859_2019.htm | 2026-09-30 | — | 4 | Tributario |
| `dian_concepto_10309_2026` | Concepto DIAN 10309 de 2026 | Normograma DIAN | https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_10309_2026.htm | 2026-09-30 | — | 5 | Tributario |
| `dian_concepto_unificado_1_2003` | Concepto Unificado de IVA 000001 de 2003 | Normograma DIAN | https://normograma.dian.gov.co/dian/compilacion/docs/concepto_tributario_dian_0000001_2003.htm | 2026-09-30 | — | 526 | Tributario |
| `dian_oficio_5035_2025` | Oficio DIAN 5035 de 2025 | Normograma DIAN | https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_5035_2025.htm | 2026-09-30 | — | 14 | Tributario |
| `dian_oficio_6206_2025` | Oficio DIAN 6206 de 2025 | Normograma DIAN | https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_6206_2025.htm | 2026-09-30 | — | 7 | Tributario |
| `dian_resolucion_165_2023` | Resolución DIAN 000165 de 2023 | Normograma DIAN | https://normograma.dian.gov.co/dian/compilacion/docs/resolucion_dian_0165_2023.htm | 2026-09-30 | 71 | 146 | Tributario |
| `dian_oficio_1241_2026` | Concepto DIAN 1241 de 2026 | Normograma DIAN | https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_1241_2026.htm | 2026-09-30 | — | 9 | Tributario |
| `dian_oficio_250_2025` | Concepto DIAN 0250 de 2025 | Normograma DIAN | https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_0250_2025.htm | 2026-09-30 | — | 5 | Tributario |
| `dian_oficio_34293_2018` | Oficio DIAN 34293 de 2018 | Normograma DIAN | https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_34293_2018.htm | 2026-09-30 | — | 8 | Tributario |
| `dian_oficio_29882_2019` | Oficio DIAN 29882 de 2019 | Normograma DIAN | https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_29882_2019.htm | 2026-09-30 | — | 8 | Tributario |
| `dian_oficio_2575_2025` | Concepto DIAN 2575 de 2025 | Normograma DIAN | https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_2575_2025.htm | 2026-09-30 | — | 8 | Tributario |
| `dian_oficio_13304_2025` | Concepto DIAN 13304 de 2025 | Normograma DIAN | https://normograma.dian.gov.co/dian/compilacion/docs/oficio_dian_13304_2025.htm | 2026-09-30 | — | 9 | Tributario |
| `sic_concepto_22_229846` | Concepto SIC Rad. 22-229846 — autorización para tratamiento de datos | SIC | https://sedeelectronica.sic.gov.co/sites/default/files/boletin-juridico/conceptos/22-229846.pdf | 2026-09-30 | — | 17 | Mercados |
| `sic_concepto_21_171791` | Concepto SIC 21-171791 — plataformas de comercio electrónico | SIC | https://sedeelectronica.sic.gov.co/sites/default/files/boletin-juridico/boletin/docs/21-171791.pdf | 2026-09-30 | — | 12 | Mercados |
| `sic_concepto_22_51097` | Concepto SIC 22-51097 — portales de contacto y relación de consumo | SIC | https://sedeelectronica.sic.gov.co/sites/default/files/boletin-juridico/conceptos/2251097%20Consumidor.pdf | 2026-09-30 | — | 21 | Mercados |
| `sic_concepto_21_511224` | Concepto SIC 21-511224 — garantía legal en servicios tecnológicos | SIC | https://sedeelectronica.sic.gov.co/sites/default/files/boletin-juridico/conceptos/21-511224%20doctrina.pdf | 2026-09-30 | — | 21 | Mercados |
| `sic_concepto_16_459471` | Concepto SIC Rad. 16-459471 — principio de finalidad | SIC | https://www.sic.gov.co/recursos_user/boletin-juridico-feb2017/conceptos/datos_personales/16459471.PDF | 2026-09-30 | — | 24 | Mercados |
| `sic_concepto_23_571469` | Concepto SIC Rad. 23-571469 — datos corporativos | SIC | https://sedeelectronica.sic.gov.co/sites/default/files/publicaciones/Concepto_Ambito.pdf | 2026-09-30 | — | 10 | Mercados |
| `sic_concepto_20_229899` | Concepto SIC 20-229899 — comercio electrónico y relación de consumo | SIC | https://sedeelectronica.sic.gov.co/sites/default/files/boletin-juridico/conceptos/20-229899_CONCEPTO.pdf | 2026-09-30 | — | 54 | Mercados |
| `sic_decreto_587_2016` | Decreto 587 de 2016 — reversión del pago | SIC | https://sedeelectronica.sic.gov.co/sites/default/files/normatividad/Decreto_587_2016.pdf | 2026-09-30 | 17 | 20 | Mercados |
| `csj_sp2287_2024` | Sentencia SP2287-2024 | Relatoría Corte Suprema de Justicia | https://cortesuprema.gov.co/corte/wp-content/uploads/relatorias/pe/b1sep2024/SP2287-2024%2863785%29.pdf | 2026-09-30 | — | 34 | Penal |
| `csj_sp025_2023` | Sentencia SP025-2023 | Relatoría Corte Suprema de Justicia | https://cortesuprema.gov.co/corte/wp-content/uploads/relatorias/pe/b1mar2023/SP025-2023%2856218%29.pdf | 2026-09-30 | — | 54 | Penal |
| `csj_sp727_2022` | Sentencia SP727-2022 | Relatoría Corte Suprema de Justicia | https://cortesuprema.gov.co/corte/wp-content/uploads/relatorias/pe/b1mar2022/SP727-2022%2856518%29.pdf | 2026-09-30 | — | 55 | Penal |
| `csj_sp2487_2024` | Sentencia SP2487-2024 | Relatoría Corte Suprema de Justicia | https://www.cortesuprema.gov.co/corte/wp-content/uploads/relatorias/pe/b1sep2024/SP2487-2024%2857115%29.pdf | 2026-09-30 | — | 89 | Penal, Procesal |
| `csj_sp3083_2024` | Sentencia SP3083-2024 | Relatoría Corte Suprema de Justicia | https://cortesuprema.gov.co/corte/wp-content/uploads/relatorias/pe/b1ene2025/SP3083-2024%2858584%29.pdf | 2026-09-30 | — | 50 | Penal, Procesal |
| `csj_sp072_2023` | Sentencia SP072-2023 | Relatoría Corte Suprema de Justicia | https://cortesuprema.gov.co/corte/wp-content/uploads/relatorias/pe/b1may2023/SP072-2023%2858706%29.pdf | 2026-09-30 | — | 87 | Penal, Procesal |
| `csj_sl1514_2023` | Sentencia SL1514-2023 | Relatoría Corte Suprema de Justicia | https://cortesuprema.gov.co/corte/wp-content/uploads/relatorias/la/reiteraciones%20DL/SL1514-2023.pdf | 2026-09-30 | — | 24 | Laboral |
| `csj_sl2324_2022` | Sentencia SL2324-2022 | Relatoría Corte Suprema de Justicia | https://cortesuprema.gov.co/corte/wp-content/uploads/2022/09/SL2324-2022.pdf | 2026-09-30 | — | 33 | Laboral |
| `csj_sl780_2023` | Sentencia SL780-2023 | Relatoría Corte Suprema de Justicia | https://cortesuprema.gov.co/corte/wp-content/uploads/relatorias/la/reiteraciones%20DL/SL780-2023.pdf | 2026-09-30 | — | 42 | Laboral |
| `csj_sl4039_2022` | Sentencia SL4039-2022 | Relatoría Corte Suprema de Justicia | https://cortesuprema.gov.co/corte/wp-content/uploads/relatorias/la/reiteraciones%20DL/SL4039-2022.pdf | 2026-09-30 | — | 129 | Laboral |
| `csj_sc701_2025` | Sentencia SC701-2025 | Relatoría Corte Suprema de Justicia | https://cortesuprema.gov.co/wp-content/uploads/relatorias/Civil/NormaSustancial/SC701-2025%5B2007-00087-01%5D.pdf | 2026-09-30 | — | 125 | Civil, Procesal, Comercial |
| `csj_sc072_2025` | Sentencia SC072-2025 | Relatoría Corte Suprema de Justicia | https://archivodigitalapi.cortesuprema.gov.co/share/2025/4/Sentencias/SC072-2025.pdf | 2026-09-30 | — | 138 | Civil |
| `csj_sc651_2025` | Sentencia SC651-2025 | Relatoría Corte Suprema de Justicia | https://ecosistemadigitalindice.cortesuprema.gov.co/api/v1/link/share/67f56153c33e31bc57074317 | 2026-09-30 | — | 53 | Comercial, Civil |
| `ley_2437_2024` | Ley 2437 de 2024 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=256656 | 2026-09-30 | 20 | 42 | Civil, Comercial, Procesal |
| `ley_2452_2025` | Ley 2452 de 2025 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=259639 | 2026-09-30 | 331 | 391 | Laboral, Procesal |
| `ley_1909_2018` | Ley 1909 de 2018 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=87302 | 2026-09-30 | 32 | 38 | Constitucional |
| `ley_2160_2021` | Ley 2160 de 2021 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=173787 | 2026-09-30 | 8 | 12 | Administrativo |
| `ley_1151_2007` | Ley 1151 de 2007 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=25932 | 2026-09-30 | 160 | 339 | Administrativo |
| `decreto_780_2016` | Decreto 780 de 2016 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=77813 | 2026-09-30 | 2090 | 2811 | Administrativo, Laboral, Penal |
| `ley_640_2001` | Ley 640 de 2001 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=6059 | 2026-09-30 | 50 | 53 | Mercados, Procesal |
| `decreto_46_2024` | Decreto 46 de 2024 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=228530 | 2026-09-30 | 6 | 24 | Comercial |
| `decreto_24_2016` | Decreto 24 de 2016 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=67536 | 2026-09-30 | 9 | 12 | Comercial |
| `ley_1700_2013` | Ley 1700 de 2013 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=56283 | 2026-09-30 | 13 | 17 | Comercial, Mercados |
| `ley_2251_2022` | Ley 2251 de 2022 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=189806 | 2026-09-30 | 28 | 34 | Civil |
| `ley_769_2002` | Ley 769 de 2002 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=5557 | 2026-09-30 | 176 | 250 | Civil |
| `ley_160_1994` | Ley 160 de 1994 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=66789 | 2026-09-30 | 113 | 167 | Civil |
| `ley_29_1982` | Ley 29 de 1982 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=256 | 2026-09-30 | 11 | 12 | Civil, Familia |
| `ley_75_1968` | Ley 75 de 1968 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=4828 | 2026-09-30 | 57 | 68 | Civil, Familia |
| `decreto_4436_2005` | Decreto 4436 de 2005 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=18346 | 2026-09-30 | 8 | 10 | Familia |
| `decreto_175_2025` | Decreto 175 de 2025 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=259629 | 2026-09-30 | 10 | 32 | Tributario |
| `decreto_1742_2020` | Decreto 1742 de 2020 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=153986 | 2026-09-30 | 84 | 172 | Tributario |
| `decreto_405_2025` | Decreto 405 de 2025 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=259517 | 2026-09-30 | 7 | 12 | Laboral |
| `ley_2114_2021` | Ley 2114 de 2021 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=167967 | 2026-09-30 | 8 | 18 | Familia, Laboral |
| `ley_2157_2021` | Ley 2157 de 2021 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=173246 | 2026-09-30 | 17 | 22 | Mercados |
| `ley_2080_2021` | Ley 2080 de 2021 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=156590 | 2026-09-30 | 144 | 179 | Administrativo, Procesal |
| `decreto_333_2021` | Decreto 333 de 2021 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=161266 | 2026-09-30 | 4 | 15 | Constitucional, Procesal |
| `ley_1957_2019` | Ley 1957 de 2019 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=94590 | 2026-09-30 | 145 | 221 | Constitucional, Penal, Procesal |
| `ley_1712_2014` | Ley 1712 de 2014 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=56882 | 2026-09-30 | 33 | 40 | Administrativo, Constitucional |
| `ley_1621_2013` | Ley 1621 de 2013 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=52706 | 2026-09-30 | 48 | 58 | Constitucional |
| `ley_1618_2013` | Ley 1618 de 2013 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=52081 | 2026-09-30 | 32 | 104 | Civil, Constitucional |
| `ley_1680_2013` | Ley 1680 de 2013 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=55611 | 2026-09-30 | 15 | 17 | Constitucional, Mercados |
| `ley_1448_2011` | Ley 1448 de 2011 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=43043 | 2026-09-30 | 217 | 346 | Administrativo, Constitucional |
| `ley_1482_2011` | Ley 1482 de 2011 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=44932 | 2026-09-30 | 13 | 16 | Constitucional, Penal |
| `ley_1496_2011` | Ley 1496 de 2011 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=45267 | 2026-09-30 | 11 | 16 | Constitucional, Laboral |
| `ley_1121_2006` | Ley 1121 de 2006 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=22647 | 2026-09-30 | 35 | 53 | Administrativo, Constitucional, Penal, Procesal |
| `ley_863_2003` | Ley 863 de 2003 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=11172 | 2026-09-30 | 79 | 111 | Civil, Constitucional, Familia, Tributario |
| `ley_361_1997` | Ley 361 de 1997 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=343 | 2026-09-30 | 72 | 74 | Constitucional, Laboral |
| `ley_134_1994` | Ley 134 de 1994 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=330 | 2026-09-30 | 109 | 112 | Constitucional |
| `ley_133_1994` | Ley 133 de 1994 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=331 | 2026-09-30 | 19 | 22 | Constitucional |
| `ley_5_1992` | Ley 5 de 1992 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=11368 | 2026-09-30 | 409 | 445 | Administrativo, Constitucional, Procesal |
| `ley_2196_2022` | Ley 2196 de 2022 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=176046 | 2026-09-30 | 85 | 95 | Administrativo |
| `ley_2195_2022` | Ley 2195 de 2022 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=175606 | 2026-09-30 | 81 | 128 | Administrativo, Penal |
| `ley_2126_2021` | Ley 2126 de 2021 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=168066 | 2026-09-30 | 49 | 71 | Administrativo, Familia, Procesal |
| `ley_1978_2019` | Ley 1978 de 2019 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=98210 | 2026-09-30 | 54 | 109 | Administrativo, Mercados |
| `ley_1882_2018` | Ley 1882 de 2018 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=84899 | 2026-09-30 | 26 | 46 | Administrativo |
| `ley_1579_2012` | Ley 1579 de 2012 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=49731 | 2026-09-30 | 100 | 113 | Administrativo, Civil |
| `ley_1341_2009` | Ley 1341 de 2009 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=36913 | 2026-09-30 | 74 | 149 | Administrativo, Mercados |
| `ley_1123_2007` | Ley 1123 de 2007 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=22962 | 2026-09-30 | 112 | 121 | Administrativo, Procesal |
| `ley_1066_2006` | Ley 1066 de 2006 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=20866 | 2026-09-30 | 21 | 27 | Administrativo, Tributario |
| `ley_610_2000` | Ley 610 de 2000 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=5725 | 2026-09-30 | 69 | 72 | Administrativo |
| `ley_152_1994` | Ley 152 de 1994 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=327 | 2026-09-30 | 52 | 62 | Administrativo |
| `ley_1922_2018` | Ley 1922 de 2018 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=87544 | 2026-09-30 | 82 | 99 | Penal, Procesal |
| `ley_1826_2017` | Ley 1826 de 2017 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=79038 | 2026-09-30 | 79 | 86 | Penal, Procesal |
| `ley_1762_2015` | Ley 1762 de 2015 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=65338 | 2026-09-30 | 56 | 78 | Penal, Tributario |
| `ley_1761_2015` | Ley 1761 de 2015 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=65337 | 2026-09-30 | 15 | 16 | Familia, Penal |
| `ley_1708_2014` | Ley 1708 de 2014 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=56475 | 2026-09-30 | 218 | 246 | Penal, Procesal |
| `ley_1273_2009` | Ley 1273 de 2009 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=34492 | 2026-09-30 | 16 | 17 | Mercados, Penal, Tributario |
| `ley_788_2002` | Ley 788 de 2002 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=7260 | 2026-09-30 | 133 | 160 | Penal, Tributario |
| `ley_575_2000` | Ley 575 de 2000 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=5372 | 2026-09-30 | 14 | 17 | Civil, Familia, Penal |
| `ley_294_1996` | Ley 294 de 1996 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=5387 | 2026-09-30 | 30 | 36 | Familia, Penal |
| `ley_65_1993` | Ley 65 de 1993 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=9210 | 2026-09-30 | 196 | 219 | Penal |
| `ley_2541_2025` | Ley 2541 de 2025 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=262716 | 2026-09-30 | 7 | 8 | Civil, Procesal |
| `decreto_772_2020` | Decreto 772 de 2020 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=127362 | 2026-09-30 | 17 | 60 | Comercial, Procesal |
| `decreto_560_2020` | Decreto 560 de 2020 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=113637 | 2026-09-30 | 16 | 45 | Comercial, Procesal |
| `decreto_806_2020` | Decreto 806 de 2020 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=127580 | 2026-09-30 | 16 | 61 | Procesal |
| `ley_1561_2012` | Ley 1561 de 2012 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=48379 | 2026-09-30 | 27 | 36 | Civil, Procesal |
| `ley_2069_2020` | Ley 2069 de 2020 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=160966 | 2026-09-30 | 86 | 115 | Comercial |
| `ley_1735_2014` | Ley 1735 de 2014 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=59835 | 2026-09-30 | 15 | 19 | Comercial |
| `ley_1328_2009` | Ley 1328 de 2009 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=36841 | 2026-09-30 | 107 | 153 | Comercial, Mercados |
| `ley_2442_2024` | Ley 2442 de 2024 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=257036 | 2026-09-30 | 9 | 11 | Civil, Familia |
| `ley_1934_2018` | Ley 1934 de 2018 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=87872 | 2026-09-30 | 22 | 23 | Civil, Familia |
| `ley_258_1996` | Ley 258 de 1996 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=10794 | 2026-09-30 | 13 | 14 | Civil, Familia |
| `decreto_1260_1970` | Decreto 1260 de 1970 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=8256 | 2026-09-30 | 122 | 123 | Civil, Familia |
| `ley_2447_2025` | Ley 2447 de 2025 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=258236 | 2026-09-30 | 23 | 27 | Familia |
| `ley_2306_2023` | Ley 2306 de 2023 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=215030 | 2026-09-30 | 10 | 13 | Familia, Laboral |
| `ley_2097_2021` | Ley 2097 de 2021 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=166186 | 2026-09-30 | 11 | 15 | Familia |
| `decreto_1710_2020` | Decreto 1710 de 2020 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=153846 | 2026-09-30 | 34 | 45 | Familia |
| `ley_1412_2010` | Ley 1412 de 2010 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=40604 | 2026-09-30 | 14 | 15 | Familia |
| `ley_1739_2014` | Ley 1739 de 2014 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=60231 | 2026-09-30 | 79 | 119 | Tributario |
| `ley_1430_2010` | Ley 1430 de 2010 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=41063 | 2026-09-30 | 68 | 85 | Tributario |
| `ley_1111_2006` | Ley 1111 de 2006 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=22580 | 2026-09-30 | 81 | 101 | Tributario |
| `ley_2381_2024` | Ley 2381 de 2024 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=246356 | 2026-09-30 | 91 | 150 | Laboral |
| `ley_2121_2021` | Ley 2121 de 2021 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=167966 | 2026-09-30 | 27 | 34 | Laboral |
| `ley_2088_2021` | Ley 2088 de 2021 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=162970 | 2026-09-30 | 16 | 17 | Laboral |
| `ley_1221_2008` | Ley 1221 de 2008 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=31431 | 2026-09-30 | 10 | 16 | Laboral |
| `ley_797_2003` | Ley 797 de 2003 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=7223 | 2026-09-30 | 30 | 58 | Laboral |
| `ley_860_2003` | Ley 860 de 2003 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=11173 | 2026-09-30 | 6 | 13 | Laboral |
| `ley_776_2002` | Ley 776 de 2002 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=16752 | 2026-09-30 | 23 | 29 | Laboral |
| `ley_2300_2023` | Ley 2300 de 2023 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=213990 | 2026-09-30 | 10 | 11 | Mercados |
| `ley_1915_2018` | Ley 1915 de 2018 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=87419 | 2026-09-30 | 41 | 56 | Mercados |
| `decreto_1083_2015` | Decreto 1083 de 2015 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=62866 | 2026-09-30 | 373 | 823 | Administrativo, Laboral |
| `decreto_1069_2015` | Decreto 1069 de 2015 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=74174 | 2026-09-30 | 1411 | 1695 | Familia, Procesal |
| `decreto_1074_2015` | Decreto 1074 de 2015 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=76608 | 2026-09-30 | 2099 | 2509 | Comercial, Mercados |
| `decreto_2555_2010` | Decreto 2555 de 2010 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=40032 | 2026-09-30 | 1354 | 3091 | Comercial |
| `decreto_1071_2015` | Decreto 1071 de 2015 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=76838 | 2026-09-30 | 1984 | 2263 | Civil |
| `decreto_1072_2015` | Decreto 1072 de 2015 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=72173 | 2026-09-30 | 1405 | 1631 | Laboral |
| `ley_2445_2025` | Ley 2445 de 2025 | Secretaría Jurídica Distrital de Bogotá | https://bogotajuridica.gov.co/sisjur/normas/Norma1.jsp?i=173897 | 2026-09-30 | 48 | 96 | Civil, Procesal |
| `ley_1870_2017` | Ley 1870 de 2017 | Secretaría Jurídica Distrital de Bogotá | https://bogotajuridica.gov.co/sisjur/normas/Norma1.jsp?i=71562 | 2026-09-30 | 5 | 14 | Comercial |
| `ley_675_2001` | Ley 675 de 2001 | Secretaría Jurídica Distrital de Bogotá | https://www.bogotajuridica.gov.co/sisjur/normas/Norma1.jsp?dt=S&i=4162 | 2026-09-30 | 87 | 97 | Civil |
| `ley_2388_2024` | Ley 2388 de 2024 | Colpensiones - Normograma | https://normativa.colpensiones.gov.co/compilacion/docs/ley_2388_2024.htm | 2026-09-30 | 20 | 29 | Familia |
| `decreto_1165_2019` | Decreto 1165 de 2019 | Ministerio TIC - Normograma | https://normograma.mintic.gov.co/mintic/compilacion/docs/decreto_1165_2019.htm | 2026-09-30 | 785 | 1325 | Tributario |
| `ley_1893_2018` | Ley 1893 de 2018 | Departamento Administrativo de la Función Pública - Gestor Normativo | https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=86599 | 2026-09-30 | 3 | 5 | Civil, Familia |
| `ley_1610_2013` | Ley 1610 de 2013 | Colpensiones - Normograma | https://normativa.colpensiones.gov.co/compilacion/docs/ley_1610_2013.htm | 2026-09-30 | 19 | 20 | Laboral |
<!-- /AUTO:inventario -->

**Totales**

<!-- AUTO:totales -->
| Métrica | Valor |
|---|---:|
| Documentos incorporados | 338 |
| Artículos indexados | 36878 |
| Fragmentos en el índice | 68603 |
| Tamaño del corpus procesado | 82.6 MB |
<!-- /AUTO:totales -->

## 2. Criterio de selección

<!-- AUTO:cobertura -->
| Área | Ítems en el banco | Documentos incorporados | Fragmentos | Cobertura del seed (ítems) |
|---|---:|---:|---:|---|
| Derecho constitucional | 134 | 81 | 12169 | 194/197 (98%) |
| Derecho administrativo | 124 | 55 | 13495 | 128/131 (98%) |
| Derecho penal | 123 | 43 | 10971 | 184/185 (99%) |
| Derecho procesal | 111 | 47 | 9811 | 182/184 (99%) |
| Derecho comercial y sociedades | 104 | 35 | 11643 | 202/204 (99%) |
| Derecho civil | 102 | 50 | 13038 | 151/151 (100%) |
| Derecho de familia | 93 | 54 | 11254 | 197/197 (100%) |
| Derecho tributario | 92 | 40 | 11398 | 210/212 (99%) |
| Derecho laboral | 87 | 52 | 10530 | 177/180 (98%) |
| Mercados | 72 | 42 | 7156 | 219/220 (100%) |

_Cobertura del seed_: ítems del banco (según `items_del_banco` de `data/seed_targets.json`) cuyas normas ya están en el corpus. Es una cota inferior: el seed no es exhaustivo.
<!-- /AUTO:cobertura -->

<!-- BORRADOR: justificar la selección frente a las diez áreas y las sub-tareas
del banco (enunciado §4.2). Puntos a cubrir: prioridad por peso de cada área y
por `items_del_banco` de seed_targets.json; códigos incorporados que el seed no
listaba (Código Civil, Comercio, Penal, CPACA…) y por qué; jurisprudencia
incorporada para las sub-tareas de precedente, sentido del fallo y ratio
decidendi. -->

Documentos descartados y el motivo del descarte:

<!-- BORRADOR: qué se consideró y no se incorporó, y por qué (derecho ambiental
e internacional fuera del banco; doctrina con derechos de autor; etc.). -->

## 3. Método de ingesta y limpieza

1. **Descarga.** Manual desde las fuentes oficiales declaradas en `fuentes.csv`
   (URL y fecha de consulta por documento).
2. **Extracción de texto.** HTML con BeautifulSoup (detección de UTF-8 /
   windows-1252, eliminación de navegación, scripts y pies); PDF con PyMuPDF,
   eliminando encabezados y números de página repetidos, y OCR con Tesseract
   solo en páginas sin capa de texto; DOCX con python-docx. Las normas publicadas
   en varias páginas se unen en orden.
3. **Normalización.** Unicode NFC, espacios y saltos de línea uniformes,
   eliminación de caracteres invisibles, unión de palabras partidas por guion.
4. **Segmentación.** Normas: un fragmento por artículo (incluye parágrafos,
   artículos con letra, bis, transitorios, numeración con guion y decretos
   únicos con numeración decimal); las notas de vigencia y jurisprudencia de la
   Secretaría del Senado quedan como fragmento aparte ligado al artículo; las
   concordancias se descartan. Sentencias: por secciones (antecedentes,
   consideraciones, resuelve…) en ventanas de ~300 palabras con 15 % de solape.
   Fragmentos de más de 300 palabras se parten repitiendo el encabezado.
5. **Extracción de metadatos.** Tipo de norma, número, año, artículo, órgano
   emisor, vigencia, áreas y sección; cada fragmento comienza con el nombre
   canónico de su norma (p. ej. “Ley 1150 de 2007, artículo 11.”), lo que
   garantiza la trazabilidad norma–artículo exigida en el paso 1.
6. **Indexación.** Encoder abierto `BAAI/bge-m3` (MIT, 1.024 dimensiones, entrada
   truncada a 512 tokens), vectores normalizados e índice exacto `faiss.IndexFlatIP`;
   caché de embeddings por hash del texto y manifiesto con sha256 de fragmentos e
   índice para congelarlo.
   Recuperación híbrida: BM25 (bm25s, tokenizador jurídico que conserva números de
   artículo y de sentencia) + denso, fusionados con RRF; router directo cuando la
   pregunta cita un artículo; reordenamiento con `BAAI/bge-reranker-v2-m3` (Apache-2.0).

Controles automáticos: 100 % de los fragmentos identifican su norma con el
mismo extractor de citas del evaluador oficial; cada pasaje es literal respecto
al documento procesado (offsets `inicio`/`fin`); guardia anti-fuga contra el
banco de preguntas.

Problemas encontrados y cómo se resolvieron:

<!-- BORRADOR: OCR defectuoso, artículos derogados, numeraciones inconsistentes… -->

## 4. Evolución del puntaje

Puntaje sobre las 50 preguntas de muestra en al menos tres momentos de la
semana, con el efecto atribuible a cada incorporación documental.

| Fecha | Documentos | Fragmentos | Cerradas /20 | Citación /20 | Abstención /10 | Total /50 | Qué cambió |
|---|---:|---:|---:|---:|---:|---:|---|
| 2026-09-29 | 186 | 41.384 | 12,00 | 15,51 | 7,79 | 35,30 | Corpus inicial completo (nivel 1 y 2 de la guía + 150 sentencias del seed). RAGAS 0,4456 (13,37/30) |
| 2026-09-30 | 186 | 41.336 | 12,00 | 15,10 | 7,67 | 34,77 | Corte estricto de secciones en sentencias (mismos documentos) + cambios del sistema C-01..C-05. RAGAS 0,4208 (12,62/30) |
| 2026-10-01 | 238 | 45.201 | 12,00 | 15,92 | 7,91 | 35,83 | +52 fuentes: 18 sentencias T/C/SU de 2026, 13 de la Corte Suprema (SP/SL/SC), 18 conceptos DIAN y SIC, Resolución DIAN 165 de 2023, Decreto 587 de 2016. RAGAS 0,4605 (13,81/30) |
| 2026-10-01 | 338 | 68.603 | 12,00 | 15,10 | 7,67 | 34,77 | +100 leyes y decretos (Función Pública, Bogotá Jurídica, Colpensiones, MinTIC), entre ellos 7 decretos únicos reglamentarios; con C-07. RAGAS 0,3815 (11,45/30): peor que v2 |

Lectura de la curva:

<!-- BORRADOR: qué incorporaciones movieron el puntaje y cuáles no. -->

## 5. Licencia

El corpus se publica bajo CC-BY-4.0. Los textos normativos colombianos son de
dominio público; la licencia cubre el trabajo de procesamiento, segmentación y
extracción de metadatos realizado por el equipo.
