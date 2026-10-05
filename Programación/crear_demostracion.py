from pathlib import Path
import shutil
import sqlite3
import struct
import wave
import zipfile
import zlib


BASE = Path(__file__).resolve().parent / "demostracion"
ENTRADA = BASE / "Entrada"

PDFS = [
    ("factura_demo_01.txt", "Factura de muestra"),
    ("informe_demo_02.bin", "Informe trimestral"),
    ("contrato_demo_03.pdf", "Contrato de prueba"),
    ("reporte_demo_04.pdf", "Reporte anual"),
    ("manual_demo_05.pdf", "Manual de usuario"),
    ("presupuesto_demo_06.pdf", "Presupuesto de ejemplo"),
]
IMAGENES = [
    ("logo_demo.dat", "logo"),
    ("captura_demo_02.tmp", "captura"),
    ("portada_demo_03.png", "portada"),
    ("grafico_demo_04.png", "grafico"),
    ("foto_demo_05.png", "foto"),
    ("icono_demo_06.png", "icono"),
]
CSV = [f"ventas_demo_{indice:02}.csv" for indice in range(1, 9)]
PYTHON = [f"script_demo_{indice:02}.py" for indice in range(1, 6)]
JSON = [f"config_demo_{indice:02}.json" for indice in range(1, 7)]
SQLITE = [f"datos_demo_{indice:02}.sqlite" for indice in range(1, 5)]
ZIP = [f"paquete_demo_{indice:02}.zip" for indice in range(1, 5)]
WAV = [f"audio_demo_{indice:02}.wav" for indice in range(1, 4)]
TEXTOS = [f"nota_demo_{indice:02}.md" for indice in range(1, 4)]
DUPLICADOS = [(f"copia_{grupo}_a.txt", f"copia_{grupo}_b.txt") for grupo in ("uno", "dos", "tres")]
AMBIGUOS = [f"qzxv_{indice:02}.zzq" for indice in range(1, 6)]

NOMBRES_DEMO = {
    "resumen_proyecto.txt", "factura_demo.txt", "logo_demo.dat", "ventas_demo.csv",
    "calcular_total.py", "clientes_demo.sqlite", "paquete_demo.zip", "audio_demo.wav",
    "copia_a.txt", "copia_b.txt", "factura_demo.pdf", "logo_demo.png", "qzxv_104.zzq",
    *[nombre for nombre, _ in PDFS],
    *[nombre for nombre, _ in IMAGENES],
    *CSV, *PYTHON, *JSON, *SQLITE, *ZIP, *WAV, *TEXTOS, *AMBIGUOS,
    *[nombre for grupo in DUPLICADOS for nombre in grupo],
}
CARPETAS_DEMO = {
    ".organizador_cuarentena", "Por_revisar", "Documentos", "Informes", "Datos",
    "Tablas", "Programación", "Código", "Configuración", "Imágenes", "Diseño",
    "Audio", "Multimedia", "Archivos_Comprimidos", "Backups", "Software",
    "Presentaciones", "Textos", "Notas", "Libros", "Material",
}


def crear_png_1x1(semilla=0):
    def chunk(nombre, datos):
        contenido = nombre + datos
        return struct.pack(">I", len(datos)) + contenido + struct.pack(">I", zlib.crc32(contenido) & 0xFFFFFFFF)

    cabecera = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    pixel = bytes((semilla % 256, (semilla * 37 + 64) % 256, (semilla * 73 + 128) % 256))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", cabecera)
        + chunk(b"IDAT", zlib.compress(b"\x00" + pixel))
        + chunk(b"IEND", b"")
    )


def reemplazar_demo_anterior():
    if not ENTRADA.exists():
        return

    desconocidos = []
    for ruta in ENTRADA.rglob("*"):
        relativo = ruta.relative_to(ENTRADA)
        if ruta.is_dir():
            if relativo.parts[0] not in CARPETAS_DEMO:
                desconocidos.append(str(relativo))
        elif ruta.is_file():
            nombre_permitido = (
                ruta.name in NOMBRES_DEMO
                or "_demo" in ruta.stem
                or ruta.name.startswith(("copia_", "qzxv_"))
            )
            metadato_cuarentena = (
                relativo.parts[0] == ".organizador_cuarentena"
                and ruta.name in {"manifest.json", "movements.jsonl"}
            )
            if not nombre_permitido and not metadato_cuarentena:
                desconocidos.append(str(relativo))

    if desconocidos:
        ejemplos = ", ".join(desconocidos[:5])
        raise SystemExit(
            "No he reemplazado la demo porque hay archivos no reconocidos en Entrada: "
            f"{ejemplos}. Muévelos fuera de la carpeta de demostración y vuelve a intentarlo."
        )

    shutil.rmtree(ENTRADA)


def crear_demostracion():
    reemplazar_demo_anterior()
    ENTRADA.mkdir(parents=True, exist_ok=True)
    for nombre, titulo in PDFS:
        (ENTRADA / nombre).write_bytes(
            f"%PDF-1.4\n% {titulo}\n1 0 obj<</Type/Catalog>>endobj\n%%EOF\n".encode("ascii")
        )
    for indice, (nombre, etiqueta) in enumerate(IMAGENES, start=1):
        (ENTRADA / nombre).write_bytes(crear_png_1x1(indice))
    for indice, nombre in enumerate(CSV, start=1):
        (ENTRADA / nombre).write_text(
            f"mes,producto,unidades\nenero,producto_{indice},{indice * 7}\nfebrero,producto_{indice + 1},{indice * 9}\n",
            encoding="utf-8",
        )
    for indice, nombre in enumerate(PYTHON, start=1):
        (ENTRADA / nombre).write_text(
            f"def procesar_lote_{indice}(elementos):\n    return [elemento.strip() for elemento in elementos]\n",
            encoding="utf-8",
        )
    for indice, nombre in enumerate(JSON, start=1):
        (ENTRADA / nombre).write_text(
            f'{{"proyecto": "demo_{indice}", "activo": true, "elementos": [{indice}, {indice + 1}]}}\n',
            encoding="utf-8",
        )
    for indice, nombre in enumerate(SQLITE, start=1):
        with sqlite3.connect(ENTRADA / nombre) as conexion:
            conexion.execute("CREATE TABLE muestras (id INTEGER PRIMARY KEY, etiqueta TEXT)")
            conexion.execute("INSERT INTO muestras (etiqueta) VALUES (?)", (f"registro_demo_{indice}",))
    for indice, nombre in enumerate(ZIP, start=1):
        with zipfile.ZipFile(ENTRADA / nombre, "w", zipfile.ZIP_DEFLATED) as archivo_zip:
            archivo_zip.writestr("LEEME.txt", f"Paquete sintético número {indice}.\n")
    for indice, nombre in enumerate(WAV, start=1):
        with wave.open(str(ENTRADA / nombre), "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(8000)
            audio.writeframes(struct.pack("<h", indice * 300) * 800)
    for indice, nombre in enumerate(TEXTOS, start=1):
        (ENTRADA / nombre).write_text(
            f"Nota de demostración {indice}: organización y revisión de archivos de prueba.\n",
            encoding="utf-8",
        )
    for indice, (nombre_a, nombre_b) in enumerate(DUPLICADOS, start=1):
        contenido = f"Grupo de duplicados sintéticos número {indice}.\n"
        (ENTRADA / nombre_a).write_text(contenido, encoding="utf-8")
        (ENTRADA / nombre_b).write_text(contenido, encoding="utf-8")
    for indice, nombre in enumerate(AMBIGUOS, start=1):
        (ENTRADA / nombre).write_bytes(bytes((valor * (indice + 2)) % 256 for valor in range(256)))
    (ENTRADA / "resumen_proyecto.txt").write_text(
        "Demostración sintética del clasificador. No contiene datos personales.\n",
        encoding="utf-8",
    )

    (BASE / "LEEME.txt").write_text(
        "DEMOSTRACION DEL ORGANIZADOR INTELIGENTE\n\n"
        "Todos los archivos son sintéticos y no contienen datos personales.\n"
        "Incluye 57 muestras de documentos, imágenes, datos, código, audio y ZIP.\n"
        "Algunos archivos tienen extensiones incorrectas, hay tres pares duplicados\n"
        "y cinco muestras ambiguas que deberían quedar en Por_revisar.\n\n"
        "Abre el terminal en la carpeta Programación y ejecuta:\n"
        "FORCE_COLOR=1 python \"alogirtma d'organitazació.py\"\n\n"
        "Para probarlo todo, elige 1 en el menú principal y escribe:\n"
        "demostracion/Entrada\n"
        "Responde s a las aprobaciones para ver renombrado, cuarentena y organización.\n"
        "Al final, mira dentro de Entrada y abre las carpetas de categoría.\n\n"
        "Para empezar de nuevo, ejecuta python crear_demostracion.py desde Programación.\n"
        "Solo reemplaza muestras reconocidas de demostración; si encuentra archivos\n"
        "desconocidos, se detiene sin borrarlos. El corpus pruebas_clasificador no cambia.\n",
        encoding="utf-8",
    )
    print(f"Demo creada: {ENTRADA}")
    print(f"Archivos de prueba: {sum(1 for ruta in ENTRADA.iterdir() if ruta.is_file())}")


if __name__ == "__main__":
    crear_demostracion()
