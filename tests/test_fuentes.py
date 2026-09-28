"""Pruebas del validador de fuentes.csv (datos de prueba, no normas reales)."""
from pathlib import Path

from src.corpus import validar as cli
from src.corpus.fuentes import normalizar_area, validar

CABECERA = ("doc_id,archivo,titulo,tipo,numero,anio,organo_emisor,fuente,url,"
            "fecha_consulta,areas,vigencia,notas")
FILA_LEY = ("ley_1150_2007,normas/ley_1150_2007.html,Ley 1150 de 2007,ley,1150,2007,"
            "Congreso,Secretaría del Senado,http://ejemplo.gov.co/ley_1150_2007.html,"
            "2026-09-28,Derecho administrativo|laboral,vigente,")
FILA_SENT = ("sentencia_c-355_2006,jurisprudencia/c-355-06.htm,Sentencia C-355 de 2006,"
             "sentencia,c-355,2006,Corte Constitucional,Relatoría,https://ejemplo.gov.co/c.htm,"
             "2026-09-28,Derecho constitucional|Derecho penal,,")


def _corpus(tmp_path: Path, filas: list[str], sep: str = ",", bom: bool = False) -> Path:
    (tmp_path / "normas").mkdir()
    (tmp_path / "jurisprudencia").mkdir()
    (tmp_path / "normas" / "ley_1150_2007.html").write_text("TEXTO DE PRUEBA", encoding="utf-8")
    (tmp_path / "jurisprudencia" / "c-355-06.htm").write_text("TEXTO DE PRUEBA", encoding="utf-8")
    lineas = [CABECERA] + filas
    texto = "\n".join(l.replace(",", sep) for l in lineas) + "\n"
    (tmp_path / "fuentes.csv").write_text(texto, encoding="utf-8-sig" if bom else "utf-8")
    return tmp_path


def test_csv_valido_con_coma(tmp_path):
    res = validar(_corpus(tmp_path, [FILA_LEY, FILA_SENT]))
    assert res.ok, res.errores
    ley, sent = res.fuentes
    assert ley.areas == ["Derecho administrativo", "Derecho laboral"]
    assert sent.numero == "C-355"


def test_csv_punto_y_coma_con_bom(tmp_path):
    res = validar(_corpus(tmp_path, [FILA_LEY], sep=";", bom=True))
    assert res.ok, res.errores
    assert res.fuentes[0].doc_id == "ley_1150_2007"


def test_filas_malas(tmp_path):
    malas = [
        FILA_LEY,
        FILA_LEY,  # doc_id repetido
        "Ley Mala,normas/no_existe.html,X,ley,,,Congreso,Senado,ftp://x,28/09/2026,Derecho espacial,rara,",
    ]
    res = validar(_corpus(tmp_path, malas))
    assert not res.ok
    texto = "\n".join(res.errores)
    for esperado in ("doc_id repetido", "minúsculas", "no existe el archivo", "necesita 'numero'",
                     "url debe", "AAAA-MM-DD", "área desconocida", "vigencia"):
        assert esperado in texto, esperado
    assert len(res.fuentes) == 1


def test_sin_columnas(tmp_path):
    (tmp_path / "fuentes.csv").write_text("doc_id,titulo\nx,y\n", encoding="utf-8")
    res = validar(tmp_path)
    assert not res.ok and "faltan columnas" in res.errores[0]


def test_normalizar_area():
    assert normalizar_area("mercados").startswith("Derecho de los mercados")
    assert normalizar_area("derecho de los mercados").startswith("Derecho de los mercados")
    assert normalizar_area("  Derecho  Civil ") == "Derecho civil"
    assert normalizar_area("derecho espacial") is None


def test_cli_sin_corpus_sale_con_cero(tmp_path, capsys):
    assert cli.main(["--dir", str(tmp_path / "vacio")]) == 0
    assert "GUIA_CORPUS.md" in capsys.readouterr().out


def test_cli_con_errores_sale_con_uno(tmp_path):
    assert cli.main(["--dir", str(_corpus(tmp_path, [FILA_LEY, FILA_LEY]))]) == 1
