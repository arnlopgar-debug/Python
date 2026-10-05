import csv
import getpass
import json
import hashlib
import math
import os
import random
import re
import shutil
import struct
import sys
import time
import unicodedata
import urllib.request
import zipfile
import zlib

# Ruta on l'algorisme desarà el que aprèn
FITXER_MODEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_inteligent.json")
FITXER_CATALOGO_MIME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset_mime_internet.json")
FITXER_RED_NEURONAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "red_neuronal_model.json")
NOM_CUARENTENA = ".organizador_cuarentena"
FUENTE_CATALOGO_MIME = "https://raw.githubusercontent.com/jshttp/mime-db/master/db.json"
MIN_EXEMPLES_PREDICCIO = 3
CONFIANCA_MINIMA = 0.75

COLORES_TERMINAL = {
    "reset": "\033[0m",
    "negrita": "\033[1m",
    "rojo": "\033[91m",
    "verde": "\033[92m",
    "amarillo": "\033[93m",
    "azul": "\033[94m",
    "magenta": "\033[95m",
    "cian": "\033[96m",
}


def colorear(texto, color):
    """Aplica color només en terminals compatibles i si no s'ha desactivat."""
    color_forzado = os.environ.get("FORCE_COLOR", "").lower() in {"1", "true", "yes"}
    if os.environ.get("NO_COLOR") is not None or not (color_forzado or getattr(sys.stdout, "isatty", lambda: False)()):
        return str(texto)
    return f"{COLORES_TERMINAL.get(color, '')}{texto}{COLORES_TERMINAL['reset']}"


def color_categoria(categoria):
    paleta = ("cian", "verde", "amarillo", "magenta", "azul")
    indice = sum(ord(caracter) for caracter in categoria) % len(paleta)
    return paleta[indice]


def barra_confianza(confianza):
    confianza = max(0.0, min(1.0, confianza))
    relleno = round(confianza * 10)
    return f"[{'#' * relleno}{'.' * (10 - relleno)}] {confianza:.0%}"


def imprimir_seccion(titulo):
    separador = "=" * 64
    print("\n" + colorear(separador, "cian"))
    print(colorear(titulo.upper(), "negrita"))
    print(colorear(separador, "cian"))

DATASET_BASE = {
    ".pdf": {"Documentos": 120, "Informes": 36, "Presentaciones": 12},
    ".doc": {"Documentos": 90, "Textos": 28, "Informes": 16},
    ".docx": {"Documentos": 110, "Textos": 30, "Informes": 24},
    ".rtf": {"Documentos": 40, "Textos": 18},
    ".txt": {"Documentos": 85, "Notas": 48, "Textos": 35},
    ".odt": {"Documentos": 42, "Textos": 26},
    ".md": {"Documentos": 52, "Textos": 32, "Programación": 18},
    ".tex": {"Documentos": 30, "Textos": 20, "Informes": 12},
    ".xlsx": {"Datos": 85, "Documentos": 32, "Tablas": 26},
    ".xls": {"Datos": 66, "Documentos": 28, "Tablas": 20},
    ".xlsm": {"Datos": 44, "Documentos": 18, "Tablas": 12},
    ".csv": {"Datos": 92, "Documentos": 25, "Tablas": 14},
    ".tsv": {"Datos": 58, "Documentos": 20},
    ".json": {"Datos": 78, "Programación": 42, "Configuración": 22},
    ".xml": {"Datos": 60, "Configuración": 28, "Documentos": 14},
    ".yaml": {"Configuración": 66, "Datos": 20, "Programación": 15},
    ".yml": {"Configuración": 60, "Datos": 18, "Programación": 12},
    ".ini": {"Configuración": 42, "Programación": 16},
    ".cfg": {"Configuración": 36, "Programación": 12},
    ".toml": {"Configuración": 46, "Programación": 14},
    ".env": {"Configuración": 28, "Programación": 10},
    ".sql": {"Datos": 64, "Programación": 26, "BaseDatos": 18},
    ".db": {"Datos": 48, "BaseDatos": 18},
    ".sqlite": {"Datos": 46, "BaseDatos": 16},
    ".dbf": {"Datos": 22, "BaseDatos": 8},
    ".mdb": {"Datos": 18, "BaseDatos": 6},
    ".ppt": {"Presentaciones": 80, "Documentos": 18},
    ".pptx": {"Presentaciones": 88, "Documentos": 24, "Diseño": 12},
    ".odp": {"Presentaciones": 54, "Documentos": 14},
    ".key": {"Presentaciones": 40, "Diseño": 12},

    ".png": {"Imágenes": 120, "Diseño": 34, "Material": 18},
    ".jpg": {"Imágenes": 116, "Diseño": 30, "Material": 14},
    ".jpeg": {"Imágenes": 112, "Diseño": 28, "Material": 14},
    ".gif": {"Imágenes": 64, "Diseño": 28, "Material": 12},
    ".webp": {"Imágenes": 52, "Diseño": 24, "Material": 10},
    ".svg": {"Diseño": 88, "Imágenes": 34, "Material": 18},
    ".bmp": {"Imágenes": 46, "Diseño": 18},
    ".ico": {"Diseño": 32, "Imágenes": 18},
    ".psd": {"Diseño": 74, "Imágenes": 26},
    ".ai": {"Diseño": 62, "Imágenes": 22},
    ".fig": {"Diseño": 38, "Imágenes": 18},
    ".tiff": {"Imágenes": 40, "Diseño": 16},
    ".tif": {"Imágenes": 38, "Diseño": 14},
    ".heic": {"Imágenes": 32, "Diseño": 10},
    ".raw": {"Imágenes": 26, "Diseño": 9},
    ".nef": {"Imágenes": 22, "Diseño": 8},

    ".mp4": {"Videos": 118, "Multimedia": 24},
    ".avi": {"Videos": 74, "Multimedia": 20},
    ".mkv": {"Videos": 80, "Multimedia": 22},
    ".mov": {"Videos": 62, "Multimedia": 18},
    ".wmv": {"Videos": 38, "Multimedia": 10},
    ".flv": {"Videos": 28, "Multimedia": 8},
    ".mpeg": {"Videos": 42, "Multimedia": 12},
    ".mpg": {"Videos": 38, "Multimedia": 10},
    ".webm": {"Videos": 52, "Multimedia": 14},
    ".3gp": {"Videos": 20, "Multimedia": 6},

    ".mp3": {"Audio": 104, "Multimedia": 24},
    ".wav": {"Audio": 90, "Multimedia": 20},
    ".flac": {"Audio": 52, "Multimedia": 12},
    ".aac": {"Audio": 38, "Multimedia": 10},
    ".ogg": {"Audio": 32, "Multimedia": 8},
    ".m4a": {"Audio": 28, "Multimedia": 7},
    ".wma": {"Audio": 22, "Multimedia": 6},

    ".zip": {"Archivos_Comprimidos": 96, "Backups": 22},
    ".rar": {"Archivos_Comprimidos": 78, "Backups": 18},
    ".7z": {"Archivos_Comprimidos": 64, "Backups": 14},
    ".tar": {"Archivos_Comprimidos": 52, "Backups": 12},
    ".gz": {"Archivos_Comprimidos": 46, "Backups": 10},
    ".bz2": {"Archivos_Comprimidos": 30, "Backups": 7},
    ".xz": {"Archivos_Comprimidos": 24, "Backups": 6},
    ".iso": {"Archivos_Comprimidos": 26, "Software": 12},
    ".tar.gz": {"Archivos_Comprimidos": 44, "Backups": 9},
    ".tar.xz": {"Archivos_Comprimidos": 20, "Backups": 5},

    ".py": {"Programación": 118, "Código": 38, "Datos": 12},
    ".pyw": {"Programación": 22, "Código": 10},
    ".pyc": {"Programación": 16, "Código": 8},
    ".js": {"Programación": 88, "Código": 30, "Web": 24},
    ".jsx": {"Programación": 46, "Web": 20, "Código": 16},
    ".ts": {"Programación": 62, "Código": 24, "Web": 18},
    ".tsx": {"Programación": 42, "Web": 18, "Código": 14},
    ".java": {"Programación": 72, "Código": 22},
    ".jar": {"Programación": 24, "Software": 12},
    ".c": {"Programación": 58, "Código": 18},
    ".cc": {"Programación": 52, "Código": 18},
    ".cpp": {"Programación": 70, "Código": 22},
    ".cs": {"Programación": 44, "Código": 16},
    ".php": {"Programación": 52, "Web": 20},
    ".rb": {"Programación": 28, "Código": 10},
    ".go": {"Programación": 24, "Código": 8},
    ".rs": {"Programación": 20, "Código": 8},
    ".swift": {"Programación": 18, "Código": 8},
    ".kt": {"Programación": 18, "Código": 7},
    ".html": {"Programación": 86, "Web": 32, "Diseño": 14},
    ".htm": {"Programación": 42, "Web": 16, "Diseño": 8},
    ".css": {"Programación": 74, "Diseño": 28, "Web": 20},
    ".scss": {"Programación": 30, "Diseño": 14, "Web": 10},
    ".sass": {"Programación": 24, "Diseño": 12, "Web": 8},
    ".lua": {"Programación": 20, "Código": 8},
    ".sh": {"Programación": 42, "Configuración": 16},
    ".bash": {"Programación": 28, "Configuración": 12},
    ".zsh": {"Programación": 18, "Configuración": 7},
    ".ps1": {"Programación": 22, "Configuración": 10},
    ".bat": {"Programación": 24, "Configuración": 9},
    ".cmd": {"Programación": 20, "Configuración": 8},
    ".pl": {"Programación": 18, "Código": 7},
    ".r": {"Datos": 20, "Programación": 10},
    ".ipynb": {"Programación": 52, "Datos": 22, "Documentos": 10},
    ".dll": {"Programas": 22, "Software": 10},
    ".exe": {"Programas": 62, "Software": 26},
    ".msi": {"Programas": 38, "Software": 16},
    ".apk": {"Programas": 26, "Software": 10},
    ".dmg": {"Programas": 20, "Software": 8},
    ".deb": {"Programas": 18, "Software": 8},
    ".rpm": {"Programas": 16, "Software": 8},
    ".app": {"Programas": 12, "Software": 6},

    ".epub": {"Documentos": 44, "Libros": 18},
    ".mobi": {"Documentos": 30, "Libros": 14},
    ".djvu": {"Documentos": 20, "Libros": 8},
    ".fb2": {"Documentos": 18, "Libros": 7},

    ".bak": {"Backups": 30, "Datos": 14},
    ".old": {"Backups": 18, "Datos": 8},
    ".tmp": {"Backups": 12, "Documentos": 4},
    ".log": {"Datos": 26, "Documentos": 10},
    ".dat": {"Datos": 22, "Backups": 8},
    ".bin": {"Datos": 16, "Archivos_Comprimidos": 6},
    ".hex": {"Datos": 10, "Programación": 6}
}

KEYWORDS_POR_CATEGORIA = {
    "Documentos": ["documento", "factura", "contrato", "informe", "reporte", "resumen", "pdf", "texto", "document"],
    "Imágenes": ["imagen", "foto", "foto", "logo", "icono", "banner", "portada", "captura", "image", "photo"],
    "Videos": ["video", "clip", "movie", "trailer", "film", "reel", "captura"],
    "Audio": ["audio", "musica", "cancion", "podcast", "voz", "sonido"],
    "Archivos_Comprimidos": ["zip", "rar", "backup", "compress", "paquete", "archivo", "copia"],
    "Programación": ["codigo", "programa", "script", "app", "src", "dev", "main", "class", "function", "python", "java", "js"],
    "Datos": ["data", "datos", "csv", "tabla", "sheet", "registro", "dataset", "bd", "base"],
    "Configuración": ["config", "settings", "setup", "configuracion", "ini", "yaml", "toml", "env"],
    "Diseño": ["design", "diseño", "grafico", "layout", "mockup", "ui", "ux", "logo", "brand"],
    "Presentaciones": ["presentacion", "slide", "deck", "powerpoint", "pitch", "seminario"],
    "Software": ["software", "installer", "install", "app", "programa"],
    "Backups": ["backup", "respaldo", "copia", "old", "tmp", "historico"]
}

def inicialitzar_model_base():
    """Crea un model inicial amb extensiones i categories molt comunes."""
    model = {}
    for extensio, categorias in DATASET_BASE.items():
        model.setdefault(extensio, {})
        for categoria, valor in categorias.items():
            model[extensio][categoria] = valor
    return model


def fusionar_model_base(model):
    """Fusiona el dataset base amb el model actual sense perdre l'aprenentatge personal."""
    model_base = inicialitzar_model_base()
    for extensio, categories in model_base.items():
        model.setdefault(extensio, {})
        for categoria, valor in categories.items():
            model[extensio][categoria] = model[extensio].get(categoria, 0) + valor
    return model


def carregar_model():
    """Carrega la memòria de l'algorisme. Si no existeix, en crea una de buida."""
    try:
        with open(FITXER_MODEL, 'r', encoding='utf-8') as f:
            model = json.load(f)
    except FileNotFoundError:
        model = inicialitzar_model_base()
        desar_model(model)
        return model
    except (OSError, json.JSONDecodeError) as error:
        print(f"No s'ha pogut carregar el model ({error}). Se'n crearà un de nou.")
        model = inicialitzar_model_base()
        desar_model(model)
        return model

    if not isinstance(model, dict):
        print("El format del model no és vàlid. Se'n crearà un de nou.")
        model = inicialitzar_model_base()
        desar_model(model)
        return model

    model = fusionar_model_base(model)
    desar_model(model)
    return model

def desar_model(model):
    """Guarda l'aprenentatge al disc dur perquè no oblidi res en tancar el programa."""
    try:
        with open(FITXER_MODEL, 'w', encoding='utf-8') as f:
            json.dump(model, f, indent=4, ensure_ascii=False)
    except OSError as error:
        print(f"No s'ha pogut desar el model: {error}")

# Carreguem la memòria al principi del programa
memoria_algorisme = carregar_model()

def normalitzar_text(text):
    """Normalitza el nom d'un fitxer per poder comparar paraules."""
    text = text.lower()
    reemplaços = {"-": " ", "_": " ", ".": " ", "/": " ", "\\": " "}
    for origen, desti in reemplaços.items():
        text = text.replace(origen, desti)
    return text


PALABRAS_ARCHIVO_GENERICAS = {
    "archivo", "archivos", "file", "files", "documento", "document", "copia", "copy",
    "final", "final2", "nuevo", "new", "recibido", "received", "descarga", "download",
    "export", "exportado", "adjunto", "attachment", "sin", "contexto", "vacio", "vacia",
    "empty", "untitled", "misc", "varios", "otro", "otros", "test", "prueba",
}
EXTENSIONES_AMBIGUAS = {".bin", ".dat", ".tmp", ".bak", ".old", ".log"}


def tokens_contextuales(texto):
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(caracter for caracter in texto if not unicodedata.combining(caracter))
    tokens = {token for token in re.findall(r"[a-z0-9]+", texto) if not token.isdigit()}
    tokens.difference_update(PALABRAS_ARCHIVO_GENERICAS)
    for token in tuple(tokens):
        if len(token) > 4 and token.endswith("es"):
            tokens.add(token[:-2])
        elif len(token) > 3 and token.endswith("s"):
            tokens.add(token[:-1])
    return tokens


def distribucion_por_palabras(texto, categorias):
    tokens = tokens_contextuales(texto)
    coincidencias = {}
    for categoria in categorias:
        vocabulario = set(KEYWORDS_POR_CATEGORIA.get(categoria, ()))
        vocabulario.update(PALABRAS_RED.get(categoria, ()))
        vocabulario.update(PALABRAS_MODELO_EXTRA.get(categoria, ()))
        vocabulario.update(tokens_contextuales(categoria.replace("_", " ")))
        vocabulario = set().union(*(tokens_contextuales(palabra) for palabra in vocabulario)) if vocabulario else set()
        cantidad = len(tokens & vocabulario)
        if cantidad:
            coincidencias[categoria] = float(cantidad)
    total = sum(coincidencias.values())
    if not total:
        return {}
    return {categoria: valor / total for categoria, valor in coincidencias.items()}


def distribucion_contenido_textual(cabecera, categorias):
    if not cabecera or b"\x00" in cabecera[:4096]:
        return {}
    try:
        texto = cabecera.decode("utf-8-sig")
    except UnicodeDecodeError:
        return {}
    primera_linea = texto.lstrip().splitlines()[0].lower() if texto.strip() else ""
    if primera_linea.startswith("#!"):
        return {"Programación": 1.0}
    tokens = tokens_contextuales(texto[:16000])
    if tokens & {"import", "def", "class", "function", "return", "const", "package", "include"}:
        return {"Programación": 1.0}
    if "=" in texto and any(line.strip().startswith("[") and line.strip().endswith("]") for line in texto.splitlines()[:12]):
        return {"Configuración": 1.0}
    return distribucion_por_palabras(texto[:16000], categorias)


def refinar_categoria_por_contexto(categoria_base, ruta, ruta_relativa, red, cabecera):
    subcategorias = [
        categoria for categoria, padre in CATEGORIA_PADRE_MODELO.items()
        if padre == categoria_base
    ]
    if not subcategorias:
        return categoria_base, 0.99, []

    contexto = " ".join((os.path.splitext(os.path.basename(ruta))[0], os.path.dirname(ruta_relativa or "")))
    distribucion_contexto = distribucion_por_palabras(contexto, subcategorias)
    if not distribucion_contexto:
        return categoria_base, 0.99, []
    subcategoria, evidencia_contexto = max(distribucion_contexto.items(), key=lambda item: item[1])
    if evidencia_contexto < 0.75:
        return categoria_base, 0.99, []

    if red is not None:
        try:
            vector = vector_caracteristicas_red(ruta, cabecera)
            _, probabilidades = red.forward(vector)
            probabilidades_por_categoria = dict(zip(red.categorias, probabilidades))
            probabilidad_red = probabilidades_por_categoria.get(subcategoria, 0.0)
            probabilidad_padre = probabilidades_por_categoria.get(categoria_base, 0.0)
            mejor_red = red.categorias[max(range(len(probabilidades)), key=lambda indice: probabilidades[indice])]
            if mejor_red == subcategoria or probabilidad_red >= 0.40:
                return subcategoria, 0.92, ["formato verificado", "contexto de nombre/carpeta", "MLP corrobora subcategoría"]
            if mejor_red == categoria_base and probabilidad_padre >= 0.50:
                return subcategoria, 0.88, ["formato verificado", "nombre específico", "MLP corrobora categoría padre"]
        except (OSError, IndexError, TypeError):
            pass
    return categoria_base, 0.99, []


def clasificar_archivo_inteligente(ruta, modelo, red=None, ruta_relativa=None, cabecera=None):
    """Combina evidencias independientes y devuelve categoría, confianza y explicación."""
    if cabecera is None:
        try:
            with open(ruta, "rb") as fitxer:
                cabecera = fitxer.read(65536)
        except OSError:
            return None, 0.0, ["no se pudo leer el archivo"]

    extension_real, categoria_formato = detectar_extension_por_contenido(ruta, cabecera)
    if extension_real and categoria_formato:
        categoria_refinada, confianza, razones = refinar_categoria_por_contexto(
            categoria_formato, ruta, ruta_relativa, red, cabecera
        )
        razones = [f"formato verificado ({extension_real})"] + razones
        return categoria_refinada, confianza, razones

    categoria_firma = detectar_categoria_por_firma(ruta, cabecera)
    if categoria_firma:
        return categoria_firma, 0.94, ["firma binaria reconocida"]

    extension = os.path.splitext(ruta)[1].lower()
    categorias = set(CATEGORIAS_MODELO) | set(KEYWORDS_POR_CATEGORIA)
    historial = modelo.get(extension, {})
    if isinstance(historial, dict):
        categorias.update(categoria for categoria in historial if isinstance(categoria, str))
    categorias = sorted(categorias)
    evidencias = []

    indice_mime = EXTENSIONES_RED.get(extension)
    if isinstance(indice_mime, int) and 0 <= indice_mime < len(CATEGORIAS_REDES):
        evidencias.append(("extensión/MIME", {CATEGORIAS_REDES[indice_mime]: 1.0}, 0.16))

    historial_valido = {
        categoria: float(valor)
        for categoria, valor in historial.items()
        if isinstance(categoria, str) and isinstance(valor, (int, float)) and valor > 0
    } if isinstance(historial, dict) else {}
    total_historial = sum(historial_valido.values())
    if total_historial:
        distribucion_historial = {
            categoria: valor / total_historial
            for categoria, valor in historial_valido.items()
        }
        peso_historial = 0.20 + 0.12 * min(total_historial / 200.0, 1.0)
        evidencias.append(("historial aprendido", distribucion_historial, peso_historial))

    nombre = os.path.basename(ruta)
    distribucion_nombre = distribucion_por_palabras(os.path.splitext(nombre)[0], categorias)
    if distribucion_nombre:
        evidencias.append(("nombre del archivo", distribucion_nombre, 0.24))

    distribucion_ruta = {}
    contexto_directorio = ruta_relativa or ""
    if contexto_directorio:
        distribucion_ruta = distribucion_por_palabras(os.path.dirname(contexto_directorio), categorias)
        if distribucion_ruta:
            evidencias.append(("carpeta contenedora", distribucion_ruta, 0.28))

    distribucion_texto = distribucion_contenido_textual(cabecera, categorias)
    if distribucion_texto:
        evidencias.append(("contenido legible", distribucion_texto, 0.34))

    if red is not None:
        try:
            vector = vector_caracteristicas_red(ruta, cabecera)
            _, probabilidades = red.forward(vector)
            distribucion_red = dict(zip(red.categorias, probabilidades))
            evidencias.append(("red neuronal", distribucion_red, 0.24))
        except (OSError, IndexError, TypeError):
            pass

    if not evidencias:
        return None, 0.0, ["no hay señales suficientes"]

    suma_pesos = sum(peso for _, _, peso in evidencias)
    puntuaciones = {categoria: 0.0 for categoria in categorias}
    for _, distribucion, peso in evidencias:
        for categoria, valor in distribucion.items():
            puntuaciones[categoria] = puntuaciones.get(categoria, 0.0) + peso * valor / suma_pesos
    ordenadas = sorted(puntuaciones.items(), key=lambda item: item[1], reverse=True)
    categoria, puntuacion = ordenadas[0]
    segunda_puntuacion = ordenadas[1][1] if len(ordenadas) > 1 else 0.0
    confianza = min(0.99, 0.5 + puntuacion - segunda_puntuacion)
    if len(evidencias) == 1:
        confianza = min(confianza, 0.54)
    evidencia_semantica = bool(distribucion_nombre or distribucion_ruta or distribucion_texto)
    try:
        archivo_vacio = os.path.getsize(ruta) == 0
    except OSError:
        archivo_vacio = True
    if archivo_vacio:
        confianza = min(confianza, 0.20)
    elif not evidencia_semantica and (
        extension in EXTENSIONES_AMBIGUAS
        or (extension not in DATASET_BASE and extension not in EXTENSIONES_RED)
    ):
        confianza = min(confianza, 0.54)
    razones = [
        nombre_evidencia for nombre_evidencia, distribucion, _ in evidencias
        if distribucion.get(categoria, 0.0) > 0
    ]
    if archivo_vacio:
        razones.append("archivo vacío; requiere revisión")
    elif confianza < CONFIANCA_MINIMA:
        razones.append("evidencia insuficiente; requiere revisión")
    return categoria, confianza, razones


def obtenir_tokens(nom_arxiu):
    """Extreu paraules útils del nom del fitxer."""
    nom_sense_extensio = os.path.splitext(nom_arxiu)[0]
    text = normalitzar_text(nom_sense_extensio)
    tokens = set()
    for paraula in text.split():
        if paraula and len(paraula) > 2:
            tokens.add(paraula)
    return tokens


def score_amb_nom(extension, nom_arxiu, model):
    """Calcula la puntuació d'una categoria a partir de l'extensió i el nom del fitxer."""
    score = {}
    for categoria in KEYWORDS_POR_CATEGORIA:
        score[categoria] = 0

    historial = model.get(extension, {})
    total_extensio = sum(int(v) for v in historial.values() if isinstance(v, (int, float)))
    if total_extensio > 0:
        for categoria, valor in historial.items():
            if isinstance(valor, (int, float)):
                score[categoria] = float(valor) / total_extensio * 100

    tokens = obtenir_tokens(nom_arxiu or "")
    for categoria, paraules in KEYWORDS_POR_CATEGORIA.items():
        coincidencies = 0
        for token in tokens:
            if token in paraules:
                coincidencies += 1
        if coincidencies:
            score[categoria] += coincidencies * 25

    return score


def predir_categoria(extension, model, nom_arxiu=""):
    """Predicció intel·ligent: combina extensió + nom del fitxer amb puntuació total."""
    if extension not in model or not model[extension]:
        if nom_arxiu:
            score = score_amb_nom(extension, nom_arxiu, model)
            if any(v > 0 for v in score.values()):
                return max(score, key=score.get)
        return None

    score = score_amb_nom(extension, nom_arxiu, model)
    if not score:
        return None

    categoria = max(score, key=score.get)
    return categoria


def obtenir_estadistiques_prediccio(extension, model):
    """Retorna la categoria més freqüent, la seva confiança i el total d'exemples."""
    historial = model.get(extension)
    if not isinstance(historial, dict):
        return None, 0, 0

    historial_valid = {
        categoria: frequencia
        for categoria, frequencia in historial.items()
        if isinstance(categoria, str)
        and isinstance(frequencia, (int, float))
        and not isinstance(frequencia, bool)
        and frequencia > 0
    }
    total_exemples = sum(historial_valid.values())
    if not historial_valid or total_exemples == 0:
        return None, 0, 0

    categoria_guanyadora = max(historial_valid, key=historial_valid.get)
    confianca = historial_valid[categoria_guanyadora] / total_exemples
    return categoria_guanyadora, confianca, total_exemples

def entrenar_algorisme(extension, categoria_correcta, model):
    """
    Funció d'entrenament: Registra una decisió per augmentar 
    la probabilitat d'aquesta categoria en el futur.
    """
    historial = model.setdefault(extension, {})
    if not isinstance(historial, dict):
        historial = {}
        model[extension] = historial

    # Sumem 1 a la puntuació d'aquesta decisió (Reforç)
    historial[categoria_correcta] = historial.get(categoria_correcta, 0) + 1
    desar_model(model)


def obtenir_categoria_usuari(nom_arxiu):
    """Demana una categoria i evita que el nom inclogui una ruta externa."""
    while True:
        categoria = input(
            f"No conec l'arxiu '{nom_arxiu}'. Escriu el nom de la carpeta destí: "
        ).strip()
        if categoria and categoria not in ('.', '..') and '/' not in categoria and '\\' not in categoria:
            return categoria
        print("Introdueix un nom de carpeta vàlid, sense separadors de ruta.")


def confirmar_o_corregir_categoria(nom_arxiu, categoria_predita, confianca, exemples, model, extension):
    """Confirma o corregeix una predicció incerta i aprèn de la resposta."""
    percentatge = confianca * 100
    while True:
        resposta = input(
            f"Predicció per a '{nom_arxiu}': '{categoria_predita}' "
            f"({percentatge:.0f}% de confiança, {exemples} exemples). "
            "Prem Enter per confirmar o escriu la categoria correcta: "
        ).strip()
        if not resposta:
            entrenar_algorisme(extension, categoria_predita, model)
            return categoria_predita
        if resposta not in ('.', '..') and '/' not in resposta and '\\' not in resposta:
            entrenar_algorisme(extension, resposta, model)
            return resposta
        print("Introdueix un nom de carpeta vàlid, sense separadors de ruta.")


def obtenir_ruta_no_colisionant(carpeta_destino, nom_arxiu):
    """Afegeix _1, _2, etc. al nom quan ja existeix al destí."""
    ruta_destino = os.path.join(carpeta_destino, nom_arxiu)
    if not os.path.exists(ruta_destino):
        return ruta_destino

    nom, extensio = os.path.splitext(nom_arxiu)
    numero = 1
    while True:
        ruta_destino = os.path.join(carpeta_destino, f'{nom}_{numero}{extensio}')
        if not os.path.exists(ruta_destino):
            return ruta_destino
        numero += 1


def entrenar_model_manual():
    """Permet entrenar el model manualment sense haver d'organitzar cap carpeta."""
    model = carregar_model()

    print("\nEntrenament manual del model")
    while True:
        extension = input("Extensió (p. ex. .png, .pdf) o 's' per sortir: ").strip()
        if extension.lower() == 's':
            break
        if not extension:
            print("Has d'escriure una extensió vàlida.")
            continue
        categoria = input("Categoria de destinació: ").strip()
        if not categoria:
            print("Has d'escriure una categoria.")
            continue

        entrenar_algorisme(extension.lower(), categoria, model)
        print(f"Aprenentatge registrat: {extension.lower()} -> {categoria}")


def generar_situacions_massives(total=5000):
    """Genera moltes situacions d'entrenament amb nom, extensió i categoria realistes."""
    situacions = []
    base = []
    for extensio, categories in DATASET_BASE.items():
        for categoria in categories:
            base.append((extensio, categoria))

    for i in range(total):
        extensio, categoria = base[i % len(base)]
        nom_fitxer = f"sample_{i}_{categoria.lower().replace(' ', '_')}{extensio}"
        situacions.append((nom_fitxer, extensio, categoria))
    return situacions


def entrenar_model_massiu(total=5000, mostrar_progres=True):
    """Entrena el model amb moltes situacions i mostra la progressió per pantalla."""
    model = carregar_model()
    situacions = generar_situacions_massives(total)

    print(f"\nEntrenament massiu iniciat: {len(situacions)} situacions")
    for index, (nom_fitxer, extensio, categoria) in enumerate(situacions, start=1):
        entrenar_algorisme(extensio.lower(), categoria, model)
        if mostrar_progres and index % 250 == 0:
            print(f"[Progrés] {index}/{len(situacions)} - {nom_fitxer} -> {categoria}")

    print(f"\nEntrenament massiu finalitzat. Model actualitzat amb {len(situacions)} exemples.")
    print(f"Categoria dominant per .pdf: {predir_categoria('.pdf', model)}")
    print(f"Categoria dominant per .png: {predir_categoria('.png', model)}")
    print(f"Categoria dominant per .py: {predir_categoria('.py', model)}")


# ------------------------------------------------------------------
# Red neuronal real desde cero (MLP) para clasificar archivos por:
# - extensión
# - palabras clave del nombre
# - histograma de bytes del inicio del archivo
# ------------------------------------------------------------------

CATEGORIAS_REDES = [
    "Documentos",
    "Imágenes",
    "Videos",
    "Audio",
    "Archivos_Comprimidos",
    "Programación",
    "Datos",
    "Configuración",
    "Diseño",
    "Presentaciones",
    "Software",
    "Backups",
]

CATEGORIAS_MODELO = CATEGORIAS_REDES + sorted(
    {categoria for categorias in DATASET_BASE.values() for categoria in categorias}
    - set(CATEGORIAS_REDES)
)

PALABRAS_MODELO_EXTRA = {
    "Informes": {"informe", "reporte", "report", "resumen", "factura"},
    "Textos": {"texto", "lectura", "escrito", "manuscrito", "essay"},
    "Notas": {"nota", "apunte", "memo", "recordatorio"},
    "Tablas": {"tabla", "hoja", "spreadsheet", "excel", "sheet"},
    "BaseDatos": {"base", "basedatos", "database", "consulta", "sql", "db"},
    "Material": {"material", "recurso", "asset", "imagen"},
    "Multimedia": {"multimedia", "media", "video", "audio"},
    "Código": {"codigo", "code", "fuente", "source"},
    "Web": {"web", "sitio", "pagina", "html", "frontend"},
    "Programas": {"programa", "instalador", "installer", "app"},
    "Libros": {"libro", "ebook", "book", "novela"},
}

CATEGORIA_PADRE_MODELO = {
    "Informes": "Documentos",
    "Textos": "Documentos",
    "Notas": "Documentos",
    "Libros": "Documentos",
    "Tablas": "Datos",
    "BaseDatos": "Datos",
    "Material": "Imágenes",
    "Multimedia": "Videos",
    "Código": "Programación",
    "Web": "Programación",
    "Programas": "Software",
}

PALABRAS_RED = {
    "Documentos": {"factura", "contrato", "informe", "reporte", "resumen", "documento", "texto", "nota", "pdf"},
    "Imágenes": {"foto", "imagen", "logo", "icono", "banner", "cover", "photo", "grafico", "sprite"},
    "Videos": {"video", "clip", "movie", "film", "trailer", "reel", "promo"},
    "Audio": {"audio", "musica", "sonido", "voz", "podcast", "cancion"},
    "Archivos_Comprimidos": {"zip", "rar", "backup", "compress", "paquete", "copia", "archive"},
    "Programación": {"codigo", "programa", "script", "app", "dev", "main", "src", "python", "java", "js"},
    "Datos": {"datos", "data", "tabla", "dataset", "registro", "sheet", "csv", "excel"},
    "Configuración": {"config", "settings", "setup", "env", "yaml", "toml", "ini"},
    "Diseño": {"design", "diseño", "layout", "ui", "ux", "mockup", "brand", "logo"},
    "Presentaciones": {"presentacion", "slide", "deck", "pitch", "powerpoint", "seminario"},
    "Software": {"software", "installer", "install", "programa", "app", "setup"},
    "Backups": {"backup", "respaldo", "old", "tmp", "historico", "copia"},
}

EXTENSIONES_RED = {
    ".pdf": 0,
    ".doc": 1,
    ".docx": 1,
    ".txt": 1,
    ".csv": 6,
    ".json": 6,
    ".xml": 6,
    ".xlsx": 6,
    ".png": 1,
    ".jpg": 1,
    ".jpeg": 1,
    ".gif": 1,
    ".mp4": 2,
    ".avi": 2,
    ".mkv": 2,
    ".mp3": 3,
    ".wav": 3,
    ".zip": 4,
    ".rar": 4,
    ".tar": 4,
    ".gz": 4,
    ".py": 5,
    ".js": 5,
    ".html": 5,
    ".css": 5,
    ".java": 5,
    ".cpp": 5,
    ".c": 5,
    ".sql": 6,
    ".ini": 7,
    ".yaml": 7,
    ".yml": 7,
    ".toml": 7,
    ".psd": 8,
    ".svg": 8,
    ".ai": 8,
    ".pptx": 9,
    ".odp": 9,
    ".exe": 10,
    ".msi": 10,
    ".bak": 11,
    ".tmp": 11,
}


def categoria_desde_mime(tipo_mime, extension):
    tipo_mime = tipo_mime.lower()
    extension = extension.lower()
    if extension in {".csv", ".tsv", ".json", ".xml", ".sql", ".db", ".sqlite", ".xlsx", ".xls"}:
        return "Datos"
    if extension in {".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env"}:
        return "Configuración"
    if extension in {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".h", ".cpp", ".cs", ".go", ".rs", ".php", ".rb", ".sh", ".html", ".css"}:
        return "Programación"
    if tipo_mime.startswith("image/"):
        return "Imágenes"
    if tipo_mime.startswith("video/"):
        return "Videos"
    if tipo_mime.startswith("audio/"):
        return "Audio"
    if any(palabra in tipo_mime for palabra in ("zip", "compressed", "compress", "tar", "rar", "7z")):
        return "Archivos_Comprimidos"
    if any(palabra in tipo_mime for palabra in ("presentation", "powerpoint", "ms-powerpoint")):
        return "Presentaciones"
    if any(palabra in tipo_mime for palabra in ("executable", "x-msdownload", "x-apple-diskimage", "java-archive")):
        return "Software"
    if "font" in tipo_mime:
        return "Diseño"
    if any(palabra in tipo_mime for palabra in ("pdf", "word", "opendocument.text", "epub", "ebook", "rtf")):
        return "Documentos"
    if tipo_mime in {"text/csv", "application/json", "application/xml", "text/xml"}:
        return "Datos"
    if tipo_mime.startswith("text/"):
        return "Documentos"
    return None


def carregar_catalogo_mime_local():
    try:
        with open(FITXER_CATALOGO_MIME, "r", encoding="utf-8") as fitxer:
            catalogo = json.load(fitxer)
    except (OSError, json.JSONDecodeError):
        return []
    entrades = catalogo.get("entries", []) if isinstance(catalogo, dict) else []
    if not isinstance(entrades, list):
        return []
    for entrada in entrades:
        if not isinstance(entrada, dict):
            continue
        extensio = entrada.get("extension")
        categoria = entrada.get("category")
        if isinstance(extensio, str) and categoria in CATEGORIAS_REDES:
            EXTENSIONES_RED[extensio] = CATEGORIAS_REDES.index(categoria)
    return entrades


def preparar_dataset_mime_internet(actualitzar=False):
    """Descarrega i normalitza metadades públiques de MIME DB amb fallback a la còpia local."""
    entrades = []
    try:
        peticio = urllib.request.Request(
            FUENTE_CATALOGO_MIME,
            headers={"User-Agent": "FileClassifierEducational/1.0"},
        )
        with urllib.request.urlopen(peticio, timeout=12) as resposta:
            dades = json.loads(resposta.read().decode("utf-8"))
        per_extensio = {}
        for tipus_mime, metadades in dades.items():
            if not isinstance(metadades, dict):
                continue
            categoria = categoria_desde_mime(tipus_mime, "")
            for extensio in metadades.get("extensions", []):
                extensio = "." + extensio.lower().lstrip(".")
                categoria_extensio = categoria_desde_mime(tipus_mime, extensio) or categoria
                if categoria_extensio:
                    per_extensio.setdefault(extensio, {})[categoria_extensio] = (
                        per_extensio.setdefault(extensio, {}).get(categoria_extensio, 0) + 1
                    )
        for extensio, categories in per_extensio.items():
            categoria = max(categories, key=categories.get)
            entrades.append({"extension": extensio, "category": categoria, "mime_types": len(categories)})
        entrades.sort(key=lambda entrada: entrada["extension"])
        catalogo = {
            "source": FUENTE_CATALOGO_MIME,
            "license": "MIT (mime-db)",
            "dataset_note": "mime-db aporta metadades MIME i extensions; els noms i histogrames de bytes d'entrenament es generen localment i no són fitxers reals descarregats.",
            "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "entries": entrades,
        }
        with open(FITXER_CATALOGO_MIME, "w", encoding="utf-8") as fitxer:
            json.dump(catalogo, fitxer, ensure_ascii=False, indent=2)
        print(f"Catàleg d'Internet carregat: {len(entrades)} extensions classificades.")
    except (OSError, ValueError, urllib.error.URLError) as error:
        print(f"No s'ha pogut actualitzar mime-db ({error}); s'utilitzarà la còpia local.")
        entrades = carregar_catalogo_mime_local()
    for entrada in entrades:
        EXTENSIONES_RED[entrada["extension"]] = CATEGORIAS_REDES.index(entrada["category"])
    return entrades


carregar_catalogo_mime_local()


def normalitzar_text_red(texto):
    texto = texto.lower()
    for simbol in ['-', '_', '.', '/', '\\']:
        texto = texto.replace(simbol, ' ')
    return texto


def tokens_del_nom_red(nombre):
    nombre = os.path.splitext(nombre)[0]
    texto = normalitzar_text_red(nombre)
    tokens = set()
    for token in texto.split():
        if len(token) > 2:
            tokens.add(token)
    return tokens


def histograma_bytes_red(ruta, n_bytes=256, dades=None):
    hist = [0.0] * 256
    if dades is None:
        try:
            with open(ruta, 'rb') as fitxer:
                dades = fitxer.read(n_bytes)
        except OSError:
            return hist
    else:
        dades = dades[:n_bytes]
    for byte in dades:
        hist[byte] += 1.0
    total = sum(hist)
    if total:
        hist = [valor / total for valor in hist]
    return hist


def vector_caracteristicas_desde_datos(nombre, histograma, cabecera=b""):
    extension = os.path.splitext(nombre)[1].lower()
    tokens = tokens_del_nom_red(nombre)
    vector = [0.0] * len(CATEGORIAS_MODELO)
    categoria_extension = EXTENSIONES_RED.get(extension)
    if categoria_extension is not None:
        vector[categoria_extension] = 1.0
    for categoria, frecuencia in DATASET_BASE.get(extension, {}).items():
        indice = CATEGORIAS_MODELO.index(categoria)
        vector[indice] = max(vector[indice], min(float(frecuencia) / 100.0, 1.0))
    for indice, categoria in enumerate(CATEGORIAS_MODELO):
        vocabulario = set(PALABRAS_RED.get(categoria, set()))
        vocabulario.update(PALABRAS_MODELO_EXTRA.get(categoria, set()))
        vocabulario.update(tokens_contextuales(categoria.replace("_", " ")))
        coincidencies = sum(
            bool(tokens & tokens_contextuales(paraula))
            for paraula in vocabulario
        )
        if coincidencies:
            vector[indice] += min(coincidencies, 3) * 0.5
    if "base" in tokens and "datos" in tokens:
        vector[CATEGORIAS_MODELO.index("BaseDatos")] += 1.5
    vector.extend(histograma)
    vector.extend(byte / 255.0 for byte in cabecera[:64])
    vector.extend([0.0] * (64 - min(len(cabecera), 64)))
    return vector


def vector_caracteristicas_red(ruta_archivo, cabecera=None):
    """Vectoriza el nombre y el histograma de bytes inicial del archivo."""
    nombre = os.path.basename(ruta_archivo)
    return vector_caracteristicas_desde_datos(
        nombre, histograma_bytes_red(ruta_archivo, dades=cabecera), cabecera or b""
    )


FIRMAS_BYTES_CATEGORIA = {
    "Documentos": b"%PDF-1.7 document page text",
    "Imágenes": (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR", b"\xff\xd8\xff\xe0\x00\x10JFIF"),
    "Videos": b"ftypisom video stream",
    "Audio": (b"ID3 audio stream frame", b"RIFF\x00\x00\x00\x00WAVEfmt "),
    "Archivos_Comprimidos": (b"PK\x03\x04 archive compressed", b"\x1f\x8b compressed gzip"),
    "Programación": b"def main() { return code; }",
    "Datos": b'{"data": [1, 2, 3], "rows": 10}',
    "Configuración": b"[settings]\nconfig=true\n",
    "Diseño": b"<svg><path d='M0 0'/></svg>",
    "Presentaciones": b"ppt/presentation slide master",
    "Software": b"MZ executable installer binary",
    "Backups": b"backup previous version archive",
}


def generar_dataset_red(num_muestras=6000, entradas_mime=None):
    """Genera ejemplos equilibrados para las categorías generales y específicas."""
    if entradas_mime is None:
        entradas_mime = preparar_dataset_mime_internet()
    extensiones_por_categoria = {categoria: [] for categoria in CATEGORIAS_MODELO}
    for extension, categorias in DATASET_BASE.items():
        for categoria in categorias:
            if extension not in extensiones_por_categoria[categoria]:
                extensiones_por_categoria[categoria].append(extension)
    for entrada in entradas_mime:
        categoria = entrada.get("category")
        extension = entrada.get("extension")
        if categoria in extensiones_por_categoria and extension:
            extensiones_por_categoria[categoria].append(extension)
    for extension, indice in EXTENSIONES_RED.items():
        categoria = CATEGORIAS_REDES[indice]
        if extension not in extensiones_por_categoria[categoria]:
            extensiones_por_categoria[categoria].append(extension)

    if any(not extensiones for extensiones in extensiones_por_categoria.values()):
        vacias = [categoria for categoria, extensiones in extensiones_por_categoria.items() if not extensiones]
        raise ValueError(f"No hay extensiones de entrenamiento para: {', '.join(vacias)}")

    dataset = []
    separadores = ["_", "-", ".", " "]
    for indice in range(num_muestras):
        categoria = CATEGORIAS_MODELO[indice % len(CATEGORIAS_MODELO)]
        extensiones = extensiones_por_categoria[categoria]
        if not extensiones:
            continue
        extension = random.choice(extensiones)
        palabras = list(PALABRAS_RED.get(categoria, set()) | PALABRAS_MODELO_EXTRA.get(categoria, set()))
        if not palabras:
            palabras = tokens_contextuales(categoria)
        random.shuffle(palabras)
        nombre = (
            random.choice(palabras) + random.choice(separadores)
            + random.choice(palabras) + str(random.randint(1, 999999)) + extension
        )
        categoria_firma = CATEGORIA_PADRE_MODELO.get(categoria, categoria)
        firma_disponibles = FIRMAS_BYTES_CATEGORIA[categoria_firma]
        firma = random.choice(firma_disponibles) if isinstance(firma_disponibles, tuple) else firma_disponibles
        carga = firma + bytes(random.choice((0, 1, 32, 65, 127, 128, 255)) for _ in range(64 - len(firma)))
        histograma = [0.0] * 256
        for byte in carga:
            histograma[byte] += 1.0
        total_bytes = sum(histograma)
        histograma = [valor / total_bytes for valor in histograma]
        vector = vector_caracteristicas_desde_datos(nombre, histograma, carga)
        salida = [0.0] * len(CATEGORIAS_MODELO)
        salida[CATEGORIAS_MODELO.index(categoria)] = 1.0
        dataset.append((vector, salida))
    return dataset


class RedNeuronalMLP:
    """Perceptró multicapa des de zero amb càlcul dispers i pesos persistibles."""

    def __init__(self, entradas, ocultas, salidas, categorias=None):
        self.entradas = entradas
        self.ocultas = ocultas
        self.salidas = salidas
        self.categorias = list(categorias or CATEGORIAS_REDES)
        if len(self.categorias) != salidas:
            raise ValueError("La cantidad de etiquetas debe coincidir con las salidas de la red.")
        limite_entrada = math.sqrt(6.0 / (entradas + ocultas))
        limite_salida = math.sqrt(6.0 / (ocultas + salidas))
        self.W1 = [[random.uniform(-limite_entrada, limite_entrada) for _ in range(ocultas)] for _ in range(entradas)]
        self.b1 = [0.0] * ocultas
        self.W2 = [[random.uniform(-limite_salida, limite_salida) for _ in range(salidas)] for _ in range(ocultas)]
        self.b2 = [0.0] * salidas

    def sigmoid(self, x):
        x = max(-60.0, min(60.0, x))
        if x >= 0:
            z = math.exp(-x)
            return 1.0 / (1.0 + z)
        z = math.exp(x)
        return z / (1.0 + z)

    def forward(self, x):
        sumes_ocultes = self.b1[:]
        for indice, valor in enumerate(x):
            if valor:
                pesos = self.W1[indice]
                for j in range(self.ocultas):
                    sumes_ocultes[j] += pesos[j] * valor
        z1 = []
        for j in range(self.ocultas):
            z1.append(self.sigmoid(sumes_ocultes[j]))

        logits = []
        for k in range(self.salidas):
            total = self.b2[k]
            for j, valor in enumerate(z1):
                total += self.W2[j][k] * valor
            logits.append(total)
        maxim = max(logits)
        z2 = [math.exp(max(-60.0, min(0.0, valor - maxim))) for valor in logits]
        suma = sum(z2) or 1.0
        z2 = [valor / suma for valor in z2]
        return z1, z2

    def train(self, x, y, learning_rate=0.02):
        z1, z2 = self.forward(x)

        delta2 = [0.0] * self.salidas
        for k in range(self.salidas):
            delta2[k] = z2[k] - y[k]

        delta1 = [0.0] * self.ocultas
        for j in range(self.ocultas):
            suma = 0.0
            for k in range(self.salidas):
                suma += self.W2[j][k] * delta2[k]
            delta1[j] = suma * z1[j] * (1.0 - z1[j])

        for j in range(self.ocultas):
            for k in range(self.salidas):
                self.W2[j][k] -= learning_rate * z1[j] * delta2[k]
        for k in range(self.salidas):
            self.b2[k] -= learning_rate * delta2[k]

        for i, valor in enumerate(x):
            if not valor:
                continue
            for j in range(self.ocultas):
                self.W1[i][j] -= learning_rate * valor * delta1[j]
        for j in range(self.ocultas):
            self.b1[j] -= learning_rate * delta1[j]

    def predict(self, x):
        _, salida = self.forward(x)
        indice = max(range(len(salida)), key=lambda i: salida[i])
        return self.categorias[indice], salida[indice]


def guardar_red_neuronal(red, num_muestras, epochs):
    """Desa arquitectura i pesos perquè la xarxa entrenada es pugui reutilitzar."""
    datos = {
        "version": 3,
        "source": FUENTE_CATALOGO_MIME,
        "categories": red.categorias,
        "inputs": red.entradas,
        "hidden": red.ocultas,
        "outputs": red.salidas,
        "training_examples": num_muestras,
        "epochs": epochs,
        "W1": red.W1,
        "b1": red.b1,
        "W2": red.W2,
        "b2": red.b2,
    }
    with open(FITXER_RED_NEURONAL, "w", encoding="utf-8") as fitxer:
        json.dump(datos, fitxer, separators=(",", ":"))
    print(f"Pesos desats a: {FITXER_RED_NEURONAL}")


def cargar_red_neuronal():
    try:
        with open(FITXER_RED_NEURONAL, "r", encoding="utf-8") as fitxer:
            datos = json.load(fitxer)
        if datos.get("version") != 3 or datos.get("categories") != CATEGORIAS_MODELO:
            return None
        red = RedNeuronalMLP(
            datos["inputs"], datos["hidden"], datos["outputs"], datos["categories"]
        )
        red.W1, red.b1 = datos["W1"], datos["b1"]
        red.W2, red.b2 = datos["W2"], datos["b2"]
        return red
    except (OSError, ValueError, KeyError, TypeError):
        return None


def entrenar_red_neuronal_massiva(num_muestras=9000, epochs=3, learning_rate=0.02, mostrar_progreso=True, hidden_size=1536):
    """Entrena una MLP ampliada con metadatos MIME y subcategorías del dataset."""
    entradas_mime = preparar_dataset_mime_internet()
    dataset = generar_dataset_red(num_muestras, entradas_mime)
    if not dataset:
        raise ValueError("No hi ha exemples disponibles per entrenar la xarxa.")
    validacion = generar_dataset_red(max(120, num_muestras // 10), entradas_mime)
    input_size = len(dataset[0][0])
    red = RedNeuronalMLP(input_size, hidden_size, len(CATEGORIAS_MODELO), CATEGORIAS_MODELO)

    print(
        f"\nEntrenament MLP: {len(dataset)} exemples, {epochs} èpoques, "
        f"{hidden_size} neuronas ocultas, {input_size} entradas, "
        f"{len(CATEGORIAS_MODELO)} clases de salida"
    )
    for epoca in range(1, epochs + 1):
        random.shuffle(dataset)
        for vector, salida_esperada in dataset:
            red.train(vector, salida_esperada, learning_rate)
        if mostrar_progreso:
            correctes = 0
            for vector, sortida_esperada in validacion:
                categoria_predita, _ = red.predict(vector)
                categoria_real = CATEGORIAS_MODELO[sortida_esperada.index(1.0)]
                correctes += categoria_predita == categoria_real
            encert = correctes / len(validacion)
            print(f"[època {epoca}/{epochs}] encert en holdout sintètic: {encert:.1%}")

    guardar_red_neuronal(red, len(dataset), epochs)
    print("\nEntrenament finalitzat. Xarxa i pesos preparats per reutilitzar.")
    return red


def clasificar_archivo_con_red(red, ruta_archivo, cabecera=None):
    """Classifica exclusivament amb la MLP, sense signatures ni regles externes."""
    if cabecera is None:
        try:
            with open(ruta_archivo, "rb") as fitxer:
                cabecera = fitxer.read(512)
        except OSError:
            cabecera = b""
    vector = vector_caracteristicas_red(ruta_archivo, cabecera)
    categoria, confianza = red.predict(vector)
    return categoria, confianza


def clasificar_archivo_solo_red(red, ruta_archivo, cabecera=None):
    """Retorna la decisió de la xarxa i les probabilitats per explicar-la."""
    if cabecera is None:
        try:
            with open(ruta_archivo, "rb") as fitxer:
                cabecera = fitxer.read(65536)
        except OSError:
            cabecera = b""
    vector = vector_caracteristicas_red(ruta_archivo, cabecera)
    _, probabilidades = red.forward(vector)
    indice = max(range(len(probabilidades)), key=lambda posicion: probabilidades[posicion])
    ordenadas = sorted(enumerate(probabilidades), key=lambda item: item[1], reverse=True)
    alternativas = [
        (red.categorias[posicion], probabilidad)
        for posicion, probabilidad in ordenadas[1:3]
    ]
    return red.categorias[indice], probabilidades[indice], alternativas


def detectar_categoria_por_firma(ruta_archivo, capcalera=None):
    """Identifica formatos binarios por sus bytes iniciales, no por la extensión."""
    if capcalera is None:
        try:
            with open(ruta_archivo, "rb") as fitxer:
                capcalera = fitxer.read(512)
        except OSError:
            return None

    extension = os.path.splitext(ruta_archivo)[1].lower()
    extensio_zip = {
        ".docx": "Documentos", ".docm": "Documentos", ".odt": "Documentos",
        ".xlsx": "Datos", ".xlsm": "Datos", ".ods": "Datos",
        ".pptx": "Presentaciones", ".pptm": "Presentaciones", ".odp": "Presentaciones",
    }
    if capcalera.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        return extensio_zip.get(extension, "Archivos_Comprimidos")
    if capcalera.startswith(b"%PDF-"):
        return "Documentos"
    if capcalera.startswith(b"\x89PNG\r\n\x1a\n"):
        return "Imágenes"
    if capcalera.startswith(b"\xff\xd8\xff"):
        return "Imágenes"
    if capcalera.startswith((b"GIF87a", b"GIF89a", b"BM")):
        return "Imágenes"
    if capcalera.startswith((b"II*\x00", b"MM\x00*")):
        return "Imágenes"
    if capcalera.startswith(b"RIFF") and capcalera[8:12] == b"WEBP":
        return "Imágenes"
    if capcalera.startswith(b"RIFF") and capcalera[8:12] == b"WAVE":
        return "Audio"
    if capcalera.startswith(b"RIFF") and capcalera[8:12] == b"AVI ":
        return "Videos"
    if len(capcalera) >= 8 and capcalera[4:8] == b"ftyp":
        return "Videos"
    if capcalera.startswith(b"\x1a\x45\xdf\xa3"):
        return "Videos"
    if capcalera.startswith((b"ID3", b"fLaC", b"OggS", b"\x1f\x8b", b"BZh", b"\xfd7zXZ\x00")):
        if capcalera.startswith((b"\x1f\x8b", b"BZh", b"\xfd7zXZ\x00")):
            return "Archivos_Comprimidos"
        return "Audio"
    if capcalera.startswith(b"Rar!\x1a\x07") or capcalera.startswith(b"7z\xbc\xaf\x27\x1c"):
        return "Archivos_Comprimidos"
    if capcalera.startswith(b"SQLite format 3\x00"):
        return "Datos"
    if capcalera.startswith(b"\x7fELF") or capcalera.startswith(b"MZ"):
        return "Software"
    if capcalera.startswith(b"#!"):
        return "Programación"
    return None


def entrenar_red_desde_archivos_reales():
    """Entrena la red ampliada con ejemplos variados del catálogo de formatos."""
    red = entrenar_red_neuronal_massiva(
        num_muestras=9000, epochs=3, learning_rate=0.02, mostrar_progreso=True, hidden_size=1536
    )
    print("\nExemples de predicció:")
    for ruta in [
        '/tmp/factura_2024.pdf',
        '/tmp/logo_principal.png',
        '/tmp/main_programa.py',
        '/tmp/video_promo.mp4',
        '/tmp/backup.zip'
    ]:
        categoria, confianza = clasificar_archivo_con_red(red, ruta)
        print(f"{ruta} -> {categoria} ({confianza:.4f})")


def clasificar_archivo_con_red_guardada():
    red = cargar_red_neuronal()
    ruta = input("Introdueix la ruta del fitxer que vols classificar: ").strip()
    if not os.path.isfile(ruta):
        print("La ruta no correspon a un fitxer accessible.")
        return
    categoria, confianza, razones = clasificar_archivo_inteligente(
        ruta, carregar_model(), red, os.path.basename(os.path.dirname(ruta))
    )
    if categoria is None:
        print("No hay evidencias suficientes para clasificar este archivo con seguridad.")
        return
    color_confianza = "verde" if confianza >= 0.9 else "amarillo" if confianza >= CONFIANCA_MINIMA else "rojo"
    print("\n" + colorear("RESULTADO DE LA RED NEURONAL", "negrita"))
    print(f"Categoría: {colorear(categoria, color_categoria(categoria))}")
    print(f"Confianza: {colorear(barra_confianza(confianza), color_confianza)}")
    print("Evidencias:")
    for razon in razones:
        print(f"  - {razon}")


def organitzar_fitxers(carpeta_origen=None, solo_red=False):
    """Classifica, mostra una vista prèvia i organitza amb confirmació."""
    if carpeta_origen is None:
        carpeta_origen = pedir_carpeta("Introdueix la ruta de la carpeta que vols organitzar: ")
        if not carpeta_origen:
            return
    else:
        carpeta_origen = resolver_ruta_carpeta(carpeta_origen)
    if not carpeta_origen:
        print("La ruta no és una carpeta accessible.")
        return

    model = carregar_model()
    red = cargar_red_neuronal()
    fitxers_protegits = {
        os.path.abspath(FITXER_MODEL),
        os.path.abspath(FITXER_CATALOGO_MIME),
        os.path.abspath(FITXER_RED_NEURONAL),
    }
    carpeta_origen = os.path.abspath(carpeta_origen)
    categorias_existentes = set(CATEGORIAS_REDES) | set(KEYWORDS_POR_CATEGORIA) | {"Por_revisar"}
    for historial in model.values():
        if isinstance(historial, dict):
            categorias_existentes.update(historial)

    rutas_origen = []
    for raiz, directorios, nombres in os.walk(carpeta_origen):
        directorios[:] = [
            directorio for directorio in directorios
            if not os.path.islink(os.path.join(raiz, directorio))
            and directorio != NOM_CUARENTENA
            and not (raiz == carpeta_origen and directorio in categorias_existentes)
        ]
        for nombre in nombres:
            ruta = os.path.join(raiz, nombre)
            if os.path.isfile(ruta) and os.path.abspath(ruta) not in fitxers_protegits:
                rutas_origen.append(ruta)

    if not rutas_origen:
        print("No hi ha fitxers per organitzar.")
        return

    imprimir_seccion("Organización de archivos")
    print(f"Carpeta: {carpeta_origen}")
    print(f"Archivos encontrados: {len(rutas_origen)}")
    print("Analizando únicamente con la red neuronal..." if solo_red else "Analizando clasificación y formato...")
    plan = []
    destinos_reservados = set()
    for indice, ruta_origen in enumerate(rutas_origen, start=1):
        nom_arxiu = os.path.basename(ruta_origen)
        extension = os.path.splitext(nom_arxiu)[1].lower()
        try:
            with open(ruta_origen, "rb") as fitxer:
                cabecera = fitxer.read(65536)
        except OSError as error:
            print(f"No s'ha pogut llegir '{ruta_origen}': {error}")
            continue

        ruta_relativa = os.path.relpath(ruta_origen, carpeta_origen)
        if solo_red:
            categoria, confianza, alternativas = clasificar_archivo_solo_red(red, ruta_origen, cabecera)
            metodo = "MLP exclusiva"
        else:
            categoria, confianza, razones = clasificar_archivo_inteligente(
                ruta_origen, model, red, ruta_relativa, cabecera
            )
            metodo = ", ".join(razones) if razones else "sin evidencias"
            if categoria is not None and confianza < CONFIANCA_MINIMA:
                categoria = "Por_revisar"
                metodo = "confiança baixa; revisar"
            elif categoria is None:
                categoria = "Por_revisar"
                metodo = "sense evidències; revisar"

        carpeta_destino = os.path.join(carpeta_origen, categoria)
        ruta_destino = obtenir_ruta_no_colisionant(carpeta_destino, nom_arxiu)
        nombre_base, extension_destino = os.path.splitext(nom_arxiu)
        numero = 1
        while os.path.normcase(os.path.abspath(ruta_destino)) in destinos_reservados:
            ruta_destino = os.path.join(carpeta_destino, f"{nombre_base}_{numero}{extension_destino}")
            numero += 1
        destinos_reservados.add(os.path.normcase(os.path.abspath(ruta_destino)))
        plan.append((ruta_origen, ruta_destino, categoria, metodo, confianza))
        if indice % 500 == 0:
            print(f"Classificats {indice}/{len(rutas_origen)} fitxers...")

    if not plan:
        print("No hi ha fitxers per organitzar.")
        return

    titulo_propuesta = "Propuesta MLP exclusiva" if solo_red else "Propuesta de organización"
    imprimir_seccion(f"{titulo_propuesta}: {len(plan)} archivos")
    comptadors = {}
    for _, _, categoria, _, _ in plan:
        comptadors[categoria] = comptadors.get(categoria, 0) + 1
    for categoria, quantitat in sorted(comptadors.items()):
        print(f"  {colorear(categoria, color_categoria(categoria))}: {quantitat} fitxers")
    para_revisar = comptadors.get("Por_revisar", 0)
    print(colorear(f"Per revisar manualment: {para_revisar} (es mouran a Por_revisar).", "amarillo"))

    print("\nDETALLE (confianza | archivo -> carpeta; máximo 15 archivos)")
    ancho_terminal = shutil.get_terminal_size(fallback=(80, 24)).columns
    for ruta_origen, ruta_destino, categoria, metodo, confianza in plan[:15]:
        color_confianza = "verde" if confianza >= 0.9 else "amarillo" if confianza >= CONFIANCA_MINIMA else "rojo"
        prefijo = f"  {confianza:.0%} | "
        sufijo = f" -> {categoria}" + (" [REVISAR]" if categoria == "Por_revisar" else "")
        nombre = os.path.basename(ruta_origen)
        ancho_nombre = max(8, ancho_terminal - len(prefijo) - len(sufijo) - 1)
        if len(nombre) > ancho_nombre:
            extension_nombre = os.path.splitext(nombre)[1]
            ancho_base = ancho_nombre - len(extension_nombre) - 3
            nombre = (
                nombre[:max(1, ancho_base)] + "..." + extension_nombre
                if ancho_base >= 1
                else nombre[:ancho_nombre - 3] + "..."
            )
        print(
            colorear(prefijo + nombre, color_confianza)
            + " "
            + colorear(sufijo[1:], color_categoria(categoria))
        )
    if len(plan) > 15:
        print(f"  ... i {len(plan) - 15} fitxers més.")
    confirmacion = input("\nVols executar aquests moviments? [s/N]: ").strip().lower()
    if confirmacion not in {"s", "si", "sí", "y", "yes"}:
        print("Organització cancel·lada; no s'ha mogut cap fitxer.")
        return

    movidos = 0
    errores = 0
    movidos_por_categoria = {}
    for indice, (ruta_origen, ruta_destino, categoria, metodo, confianza) in enumerate(plan, start=1):
        try:
            os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
            ruta_destino = obtenir_ruta_no_colisionant(
                os.path.dirname(ruta_destino), os.path.basename(ruta_destino)
            )
            shutil.move(ruta_origen, ruta_destino)
            movidos += 1
            movidos_por_categoria[categoria] = movidos_por_categoria.get(categoria, 0) + 1
            if len(plan) > 25 and indice % 500 == 0:
                print(f"Moguts {indice}/{len(plan)} fitxers...")
        except OSError as error:
            errores += 1
            print(f"No s'ha pogut moure '{os.path.basename(ruta_origen)}': {error}")
    imprimir_seccion("Resultado de la organización")
    print(f"Archivos movidos: {movidos} de {len(plan)}")
    print(f"Errores: {errores}")
    print(f"Puedes encontrarlos dentro de: {carpeta_origen}")
    if movidos_por_categoria:
        print("\nArchivos por carpeta de destino:")
        for categoria, cantidad in sorted(movidos_por_categoria.items()):
            print(f"  {categoria:<24} {cantidad:>4} archivo(s)")


def format_bytes(mida):
    unidades = ("B", "KB", "MB", "GB", "TB")
    valor = float(mida)
    for unidad in unidades:
        if valor < 1024 or unidad == unidades[-1]:
            return f"{valor:.1f} {unidad}"
        valor /= 1024


def hash_archivo(ruta):
    digest = hashlib.sha256()
    with open(ruta, "rb") as fitxer:
        for bloque in iter(lambda: fitxer.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def inventariar_carpeta(carpeta):
    raiz_carpeta = os.path.abspath(carpeta)
    extensiones_mime = {
        entrada.get("extension"): entrada.get("category")
        for entrada in carregar_catalogo_mime_local()
        if isinstance(entrada, dict)
    }
    archivos = []
    errores = 0
    for raiz, directorios, nombres in os.walk(raiz_carpeta):
        directorios[:] = [
            nombre for nombre in directorios
            if nombre != NOM_CUARENTENA
            and not os.path.islink(os.path.join(raiz, nombre))
        ]
        for nombre in nombres:
            ruta = os.path.join(raiz, nombre)
            if os.path.islink(ruta) or os.path.abspath(ruta) in {
                os.path.abspath(FITXER_MODEL),
                os.path.abspath(FITXER_CATALOGO_MIME),
                os.path.abspath(FITXER_RED_NEURONAL),
            }:
                continue
            try:
                estadistica = os.stat(ruta, follow_symlinks=False)
                extension = os.path.splitext(nombre)[1].lower()
                with open(ruta, "rb") as fitxer:
                    cabecera = fitxer.read(512)
                categoria_real = detectar_categoria_por_firma(ruta, cabecera)
                categoria_extension = extensiones_mime.get(extension)
                archivos.append({
                    "path": ruta,
                    "relative": os.path.relpath(ruta, raiz_carpeta),
                    "name": nombre,
                    "extension": extension or "(sin extensión)",
                    "size": estadistica.st_size,
                    "mtime": estadistica.st_mtime,
                    "sha256": None,
                    "expected_category": categoria_extension,
                    "detected_category": categoria_real,
                })
            except OSError:
                errores += 1

    por_tamaño = {}
    for archivo in archivos:
        por_tamaño.setdefault(archivo["size"], []).append(archivo)

    grupos_hash = {}
    candidatos = [archivo for grupo in por_tamaño.values() if len(grupo) > 1 for archivo in grupo]
    for indice, archivo in enumerate(candidatos, start=1):
        try:
            archivo["sha256"] = hash_archivo(archivo["path"])
            clave = (archivo["size"], archivo["sha256"])
            grupos_hash.setdefault(clave, []).append(archivo)
        except OSError:
            errores += 1
        if indice % 1000 == 0:
            print(f"Comprovats {indice}/{len(candidatos)} fitxers candidats a duplicat...")

    duplicats = [grup for grup in grupos_hash.values() if len(grup) > 1]
    duplicats.sort(key=lambda grup: (-sum(archivo["size"] for archivo in grup), grup[0]["path"]))
    mismatches = [
        archivo for archivo in archivos
        if archivo["expected_category"] and archivo["detected_category"]
        and archivo["expected_category"] != archivo["detected_category"]
    ]
    return raiz_carpeta, archivos, duplicats, mismatches, errores


def mostrar_informe_carpeta(carpeta):
    raiz, archivos, duplicats, mismatches, errores = inventariar_carpeta(carpeta)
    if not archivos:
        print("No s'han trobat fitxers accessibles.")
        return

    bytes_totals = sum(archivo["size"] for archivo in archivos)
    extensiones = {}
    for archivo in archivos:
        extensiones[archivo["extension"]] = extensiones.get(archivo["extension"], 0) + 1
    cantidad_duplicada = sum(len(grupo) - 1 for grupo in duplicats)
    espacio_duplicado = sum((len(grupo) - 1) * grupo[0]["size"] for grupo in duplicats)

    imprimir_seccion("Informe de carpeta")
    print(f"Ubicación: {raiz}")
    print(f"Archivos: {len(archivos)} | Espacio total: {format_bytes(bytes_totals)}")
    print(f"Archivos vacíos: {sum(archivo['size'] == 0 for archivo in archivos)}")
    print(f"Grupos duplicados: {len(duplicats)} | Copias redundantes: {cantidad_duplicada}")
    print(f"Espacio redundante estimado: {format_bytes(espacio_duplicado)}")
    print(f"Posibles extensiones incorrectas: {len(mismatches)} | Errores de lectura: {errores}")

    imprimir_seccion("Extensiones más frecuentes")
    for extension, cantidad in sorted(extensiones.items(), key=lambda item: (-item[1], item[0]))[:10]:
        print(f"  {extension}: {cantidad}")

    grandes = sorted(archivos, key=lambda archivo: archivo["size"], reverse=True)[:10]
    imprimir_seccion("Archivos más grandes")
    for archivo in grandes:
        print(f"  {format_bytes(archivo['size'])}  {archivo['relative']}")

    if duplicats:
        imprimir_seccion("Duplicados exactos (mismo tamaño y SHA-256)")
        for grupo in duplicats[:5]:
            print(f"  {format_bytes(grupo[0]['size'])} x {len(grupo)}")
            for archivo in grupo[:3]:
                print(f"    {archivo['relative']}")
            if len(grupo) > 3:
                print(f"    ... y {len(grupo) - 3} más")

    if mismatches:
        imprimir_seccion("Extensiones que no coinciden con la firma")
        for archivo in mismatches[:10]:
            print(
                f"  {archivo['relative']}: la extensión sugiere "
                f"{archivo['expected_category']}, la firma indica {archivo['detected_category']}"
            )
    print("\nEl análisis es de solo lectura; no se ha movido ni borrado nada.")


def resolver_ruta_carpeta(carpeta):
    carpeta = os.path.expanduser(str(carpeta).strip().strip('"'))
    if os.path.isdir(carpeta):
        return os.path.abspath(carpeta)
    if not os.path.isabs(carpeta):
        desde_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), carpeta)
        if os.path.isdir(desde_script):
            return os.path.abspath(desde_script)
    return None


def pedir_carpeta(mensaje):
    carpeta = resolver_ruta_carpeta(input(mensaje))
    if not carpeta:
        print("La ruta no es una carpeta accesible.")
        return None
    return carpeta


def escribir_evento_jsonl(ruta, evento):
    with open(ruta, "a", encoding="utf-8") as fitxer:
        fitxer.write(json.dumps(evento, ensure_ascii=False) + "\n")
        fitxer.flush()


def poner_duplicados_en_cuarentena(carpeta=None):
    if carpeta is None:
        carpeta = pedir_carpeta("Carpeta que quieres analizar: ")
    if not carpeta:
        return
    raiz, archivos, duplicats, _, errores = inventariar_carpeta(carpeta)
    if not duplicats:
        print(f"No se encontraron duplicados exactos. Archivos revisados: {len(archivos)}.")
        return

    mover = []
    for grupo in duplicats:
        conservar = min(grupo, key=lambda archivo: (archivo["mtime"], archivo["path"]))
        mover.extend(archivo for archivo in grupo if archivo is not conservar)
    bytes_cuarentena = sum(archivo["size"] for archivo in mover)
    print(
        f"\nSe pondrán en cuarentena {len(mover)} copias duplicadas "
        f"({format_bytes(bytes_cuarentena)}). Se conservará la copia más antigua de cada grupo."
    )
    for archivo in mover[:20]:
        print(f"  {archivo['relative']} ({format_bytes(archivo['size'])})")
    if len(mover) > 20:
        print(f"  ... y {len(mover) - 20} copias más")
    print("La cuarentena es reversible y no libera espacio hasta que se borre definitivamente.")
    if input("¿Continuar? [s/N]: ").strip().lower() not in {"s", "si", "sí", "y", "yes"}:
        print("No se movió ningún duplicado.")
        return

    raiz_cuarentena = os.path.join(raiz, NOM_CUARENTENA)
    id_sesion = time.strftime("%Y%m%d-%H%M%S") + f"-{time.time_ns() % 1_000_000_000:09d}"
    carpeta_sesion = os.path.join(raiz_cuarentena, id_sesion)
    os.makedirs(carpeta_sesion, exist_ok=False)
    ruta_manifest = os.path.join(carpeta_sesion, "manifest.json")
    with open(ruta_manifest, "w", encoding="utf-8") as fitxer:
        json.dump({"version": 1, "source_root": raiz, "created_at": id_sesion}, fitxer, indent=2)

    ruta_movimientos = os.path.join(carpeta_sesion, "movements.jsonl")
    movidos = 0
    errores_movimiento = 0
    for archivo in mover:
        relativo_cuarentena = os.path.join("files", archivo["relative"])
        destino = os.path.join(carpeta_sesion, relativo_cuarentena)
        try:
            if not os.path.isfile(archivo["path"]):
                raise OSError("El archivo ya no existe.")
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            shutil.move(archivo["path"], destino)
            escribir_evento_jsonl(ruta_movimientos, {
                "original": archivo["relative"],
                "quarantined": relativo_cuarentena,
                "sha256": archivo["sha256"],
                "size": archivo["size"],
            })
            movidos += 1
            if movidos % 500 == 0:
                print(f"En cuarentena {movidos}/{len(mover)} archivos...")
        except OSError as error:
            errores_movimiento += 1
            print(f"No se pudo poner en cuarentena '{archivo['relative']}': {error}")
    print(
        f"\nCuarentena completada: {movidos} movidos, {errores_movimiento} errores. "
        f"Sesión: {id_sesion}"
    )
    if errores:
        print(f"Nota: hubo {errores} errores durante el análisis de archivos.")


def restaurar_cuarentena():
    carpeta = pedir_carpeta("Carpeta original de la cuarentena: ")
    if not carpeta:
        return
    raiz_cuarentena = os.path.join(carpeta, NOM_CUARENTENA)
    if not os.path.isdir(raiz_cuarentena):
        print("No hay ninguna cuarentena para esta carpeta.")
        return

    sesiones = []
    for nombre in os.listdir(raiz_cuarentena):
        ruta_sesion = os.path.join(raiz_cuarentena, nombre)
        ruta_manifest = os.path.join(ruta_sesion, "manifest.json")
        ruta_movimientos = os.path.join(ruta_sesion, "movements.jsonl")
        ruta_restauraciones = os.path.join(ruta_sesion, "restorations.jsonl")
        if not os.path.isfile(ruta_manifest) or not os.path.isfile(ruta_movimientos):
            continue
        try:
            with open(ruta_manifest, "r", encoding="utf-8") as fitxer:
                manifest = json.load(fitxer)
            if os.path.abspath(manifest.get("source_root", "")) != carpeta:
                continue
            with open(ruta_movimientos, "r", encoding="utf-8") as fitxer:
                moviments = [json.loads(linia) for linia in fitxer if linia.strip()]
            restaurats = set()
            if os.path.isfile(ruta_restauraciones):
                with open(ruta_restauraciones, "r", encoding="utf-8") as fitxer:
                    restaurats = {
                        json.loads(linia).get("quarantined")
                        for linia in fitxer if linia.strip()
                    }
            pendents = [
                moviment for moviment in moviments
                if moviment.get("quarantined") not in restaurats
            ]
            if pendents:
                sesiones.append((nombre, ruta_sesion, pendents, ruta_restauraciones))
        except (OSError, ValueError, TypeError):
            continue

    if not sesiones:
        print("No hay sesiones pendientes de restaurar para esta carpeta.")
        return
    print("\nSesiones disponibles:")
    for indice, (nombre, _, pendientes, _) in enumerate(sesiones, start=1):
        print(f"  {indice}) {nombre}: {len(pendientes)} archivos")
    try:
        seleccion = int(input("Número de sesión que quieres restaurar [0 para cancelar]: ").strip())
    except ValueError:
        print("Selección no válida; no se restauró nada.")
        return
    if seleccion == 0:
        print("Restauración cancelada.")
        return
    if not 1 <= seleccion <= len(sesiones):
        print("No existe esa sesión.")
        return

    _, ruta_sesion, pendientes, ruta_restauraciones = sesiones[seleccion - 1]
    if input(f"¿Restaurar {len(pendientes)} archivos? [s/N]: ").strip().lower() not in {"s", "si", "sí", "y", "yes"}:
        print("Restauración cancelada.")
        return

    restaurados = 0
    errores = 0
    for movimiento in pendientes:
        ruta_cuarentena = os.path.abspath(os.path.join(ruta_sesion, movimiento["quarantined"]))
        if os.path.commonpath((ruta_sesion, ruta_cuarentena)) != ruta_sesion:
            errores += 1
            continue
        ruta_original = os.path.abspath(os.path.join(carpeta, movimiento["original"]))
        if os.path.commonpath((carpeta, ruta_original)) != carpeta:
            errores += 1
            continue
        try:
            if not os.path.isfile(ruta_cuarentena):
                raise OSError("No se encontró la copia en cuarentena.")
            os.makedirs(os.path.dirname(ruta_original), exist_ok=True)
            if os.path.exists(ruta_original):
                ruta_destino = obtenir_ruta_no_colisionant(
                    os.path.dirname(ruta_original), os.path.basename(ruta_original)
                )
            else:
                ruta_destino = ruta_original
            shutil.move(ruta_cuarentena, ruta_destino)
            escribir_evento_jsonl(ruta_restauraciones, {
                "quarantined": movimiento["quarantined"],
                "restored_to": os.path.relpath(ruta_destino, carpeta),
            })
            restaurados += 1
        except OSError as error:
            errores += 1
            print(f"No se pudo restaurar '{movimiento['original']}': {error}")
    print(f"\nRestauración completada: {restaurados} archivos, {errores} errores.")


def detectar_extension_por_contenido(ruta, cabecera=None):
    """Devuelve una extensión solo si el formato está identificado con alta certeza."""
    try:
        tamaño_archivo = os.path.getsize(ruta)
    except OSError:
        return None, None
    if cabecera is None:
        try:
            with open(ruta, "rb") as fitxer:
                cabecera = fitxer.read(65536)
        except OSError:
            return None, None

    if (
        tamaño_archivo >= 16
        and cabecera.startswith(b"%PDF-")
        and cabecera[5:8] in {b"1.0", b"1.1", b"1.2", b"1.3", b"1.4", b"1.5", b"1.6", b"1.7", b"2.0"}
    ):
        with open(ruta, "rb") as fitxer:
            fitxer.seek(max(0, tamaño_archivo - 1024))
            final_pdf = fitxer.read(1024)
        if b"%%EOF" in final_pdf:
            return ".pdf", "Documentos"
    if (
        tamaño_archivo >= 45
        and cabecera.startswith(b"\x89PNG\r\n\x1a\n")
        and len(cabecera) >= 33
        and struct.unpack(">I", cabecera[8:12])[0] == 13
        and cabecera[12:16] == b"IHDR"
        and zlib.crc32(cabecera[12:29]) & 0xffffffff == struct.unpack(">I", cabecera[29:33])[0]
        and struct.unpack(">II", cabecera[16:24])[0] != (0, 0)
    ):
        return ".png", "Imágenes"
    if (
        tamaño_archivo >= 10 and cabecera.startswith(b"\xff\xd8\xff")
        and len(cabecera) >= 8 and cabecera[3] == 0xff
        and struct.unpack(">H", cabecera[4:6])[0] >= 2
        and 4 + struct.unpack(">H", cabecera[4:6])[0] <= tamaño_archivo
    ):
        return ".jpg", "Imágenes"
    if (
        tamaño_archivo >= 14 and cabecera.startswith((b"GIF87a", b"GIF89a"))
        and struct.unpack("<HH", cabecera[6:10]) != (0, 0)
    ):
        return ".gif", "Imágenes"
    if (
        tamaño_archivo >= 26 and cabecera.startswith(b"BM")
        and struct.unpack("<I", cabecera[2:6])[0] == tamaño_archivo
        and struct.unpack("<II", cabecera[18:26])[0] != (0, 0)
    ):
        return ".bmp", "Imágenes"
    if (
        tamaño_archivo >= 8
        and (cabecera.startswith(b"II*\x00") or cabecera.startswith(b"MM\x00*"))
        and struct.unpack("<I" if cabecera.startswith(b"II") else ">I", cabecera[4:8])[0] >= 8
        and struct.unpack("<I" if cabecera.startswith(b"II") else ">I", cabecera[4:8])[0] < tamaño_archivo
    ):
        return ".tif", "Imágenes"
    if (
        tamaño_archivo >= 16 and cabecera.startswith(b"RIFF") and cabecera[8:12] == b"WEBP"
        and struct.unpack("<I", cabecera[4:8])[0] + 8 == tamaño_archivo
    ):
        return ".webp", "Imágenes"
    if (
        tamaño_archivo >= 44 and cabecera.startswith(b"RIFF") and cabecera[8:12] == b"WAVE"
        and struct.unpack("<I", cabecera[4:8])[0] + 8 == tamaño_archivo
        and b"fmt " in cabecera[:64] and b"data" in cabecera[:64]
    ):
        return ".wav", "Audio"
    if (
        tamaño_archivo >= 12 and cabecera.startswith(b"RIFF") and cabecera[8:12] == b"AVI "
        and struct.unpack("<I", cabecera[4:8])[0] + 8 <= tamaño_archivo
    ):
        return ".avi", "Videos"
    if (
        len(cabecera) >= 16 and cabecera[4:8] == b"ftyp"
        and 16 <= struct.unpack(">I", cabecera[:4])[0] <= tamaño_archivo
    ):
        marca = cabecera[8:12]
        if marca == b"qt  ":
            return ".mov", "Videos"
        if marca == b"M4V ":
            return ".m4v", "Videos"
        return ".mp4", "Videos"
    if tamaño_archivo >= 32 and cabecera.startswith(b"\x1a\x45\xdf\xa3"):
        if b"webm" in cabecera[:512].lower():
            return ".webm", "Videos"
        return ".mkv", "Videos"
    if (
        tamaño_archivo >= 10 and cabecera.startswith(b"ID3")
        and cabecera[3] in {2, 3, 4} and all((byte & 0x80) == 0 for byte in cabecera[6:10])
        and 10 + sum(cabecera[6 + indice] << (7 * (3 - indice)) for indice in range(4)) <= tamaño_archivo
    ):
        return ".mp3", "Audio"
    if tamaño_archivo >= 42 and cabecera.startswith(b"fLaC"):
        return ".flac", "Audio"
    if tamaño_archivo >= 27 and cabecera.startswith(b"OggS") and cabecera[4] == 0:
        if b"OpusHead" in cabecera:
            return ".opus", "Audio"
        return ".ogg", "Audio"
    if len(cabecera) >= 10 and cabecera.startswith(b"\x1f\x8b\x08") and cabecera[3] & 0xe0 == 0:
        return ".gz", "Archivos_Comprimidos"
    if len(cabecera) >= 10 and cabecera.startswith(b"BZh") and cabecera[3:4] in b"123456789":
        return ".bz2", "Archivos_Comprimidos"
    if tamaño_archivo >= 24 and cabecera.startswith(b"\xfd7zXZ\x00"):
        return ".xz", "Archivos_Comprimidos"
    if tamaño_archivo >= 20 and cabecera.startswith((b"Rar!\x1a\x07\x00", b"Rar!\x1a\x07\x01\x00")):
        return ".rar", "Archivos_Comprimidos"
    if tamaño_archivo >= 32 and cabecera.startswith(b"7z\xbc\xaf\x27\x1c"):
        return ".7z", "Archivos_Comprimidos"
    if (
        tamaño_archivo >= 100 and cabecera.startswith(b"SQLite format 3\x00")
        and struct.unpack(">H", cabecera[16:18])[0] in {1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768, 1}
    ):
        return ".sqlite", "Datos"
    if (
        tamaño_archivo >= 10 and cabecera.startswith(b"\xca\xfe\xba\xbe")
        and 45 <= struct.unpack(">H", cabecera[6:8])[0] <= 70
    ):
        return ".class", "Programación"

    if cabecera.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")):
        try:
            with zipfile.ZipFile(ruta) as archive:
                nombres = set(archive.namelist())
                if "word/document.xml" in nombres:
                    return ".docx", "Documentos"
                if "xl/workbook.xml" in nombres:
                    return ".xlsx", "Datos"
                if "ppt/presentation.xml" in nombres:
                    return ".pptx", "Presentaciones"
                if "mimetype" in nombres:
                    tipo = archive.read("mimetype")
                    formatos_odf = {
                        b"application/vnd.oasis.opendocument.text": (".odt", "Documentos"),
                        b"application/vnd.oasis.opendocument.spreadsheet": (".ods", "Datos"),
                        b"application/vnd.oasis.opendocument.presentation": (".odp", "Presentaciones"),
                    }
                    for firma, resultado in formatos_odf.items():
                        if tipo.startswith(firma):
                            return resultado
        except (OSError, zipfile.BadZipFile, RuntimeError):
            pass
        return ".zip", "Archivos_Comprimidos"

    linea = cabecera.splitlines()[0].lower() if cabecera else b""
    if cabecera.startswith(b"#!"):
        if b"python" in linea:
            return ".py", "Programación"
        if any(shell in linea for shell in (b"/sh", b"bash", b"zsh")):
            return ".sh", "Programación"
        if b"node" in linea:
            return ".js", "Programación"
        if b"ruby" in linea:
            return ".rb", "Programación"
        if b"perl" in linea:
            return ".pl", "Programación"

    texto = cabecera.lstrip().lower()
    if texto.startswith((b"<!doctype html", b"<html")):
        return ".html", "Programación"
    if texto.startswith(b"<?xml"):
        return ".xml", "Datos"
    try:
        if tamaño_archivo <= 65536 and cabecera.lstrip().startswith((b"{", b"[")):
            contenido_json = cabecera.decode("utf-8-sig")
            json.loads(contenido_json)
            return ".json", "Datos"
    except (UnicodeDecodeError, json.JSONDecodeError):
        pass

    try:
        muestra = cabecera.decode("utf-8-sig")
        dialecto = csv.Sniffer().sniff(muestra[:4096], delimiters=",\t;")
        filas = list(csv.reader(muestra.splitlines()[:4], dialecto))
        if len(filas) >= 2 and len(filas[0]) > 1 and all(len(fila) == len(filas[0]) for fila in filas[:3]):
            extension = ".tsv" if dialecto.delimiter == "\t" else ".csv"
            return extension, "Datos"
    except (UnicodeDecodeError, csv.Error):
        pass
    return None, None


def renombrar_extensiones_con_aviso(carpeta=None):
    if carpeta is None:
        carpeta = pedir_carpeta("Carpeta donde quieres revisar extensiones: ")
    if not carpeta:
        return

    equivalentes = {
        ".jpg": {".jpg", ".jpeg"},
        ".tif": {".tif", ".tiff"},
        ".sqlite": {".sqlite", ".sqlite3", ".db"},
        ".html": {".html", ".htm"},
    }
    propuestas = []
    omitidos = 0
    destinos = set()
    for raiz, directorios, nombres in os.walk(carpeta):
        directorios[:] = [
            nombre for nombre in directorios
            if nombre != NOM_CUARENTENA and not os.path.islink(os.path.join(raiz, nombre))
        ]
        for nombre in nombres:
            ruta = os.path.join(raiz, nombre)
            if os.path.islink(ruta) or not os.path.isfile(ruta):
                continue
            extension_actual = os.path.splitext(nombre)[1].lower()
            extension_real, categoria = detectar_extension_por_contenido(ruta)
            if not extension_real:
                continue
            if extension_actual in equivalentes.get(extension_real, {extension_real}):
                continue

            nuevo_nombre = os.path.splitext(nombre)[0] + extension_real
            destino = os.path.join(raiz, nuevo_nombre)
            clave_destino = os.path.normcase(os.path.abspath(destino))
            if os.path.exists(destino) or clave_destino in destinos:
                omitidos += 1
                continue
            destinos.add(clave_destino)
            propuestas.append({
                "source": ruta,
                "destination": destino,
                "name": nombre,
                "old_extension": extension_actual or "(sin extensión)",
                "new_extension": extension_real,
                "category": categoria,
                "relative": os.path.relpath(ruta, carpeta),
            })

    if not propuestas:
        print(f"No hay extensiones corregibles con alta certeza. Conflictos omitidos: {omitidos}.")
        return

    nombre_propietario = input(f"Nombre del propietario [{getpass.getuser()}]: ").strip()
    if not nombre_propietario:
        nombre_propietario = getpass.getuser()
    ejemplos = "; ".join(
        f"{propuesta['name']}: {propuesta['old_extension']} -> {propuesta['new_extension']}"
        for propuesta in propuestas[:3]
    )
    plantilla_predeterminada = (
        "Hola {propietario}: detecté {cantidad} extensiones que no coinciden con el formato real "
        "en {carpeta}. Ejemplos: {ejemplos}. No cambiaré nada sin tu aprobación."
    )
    print("Variables disponibles: {propietario}, {cantidad}, {carpeta}, {ejemplos}")
    plantilla = input("Mensaje personalizado (Enter para usar el predeterminado): ").strip()
    if not plantilla:
        plantilla = plantilla_predeterminada
    valores = {
        "propietario": nombre_propietario,
        "cantidad": len(propuestas),
        "carpeta": carpeta,
        "ejemplos": ejemplos,
    }
    try:
        mensaje = plantilla.format(**valores)
    except (KeyError, ValueError, IndexError) as error:
        print(f"La plantilla contiene una variable o formato no válido: {error}. No se renombró nada.")
        return

    print(f"\nAviso previo para {nombre_propietario}:\n{mensaje}")
    print(f"\nCambios propuestos: {len(propuestas)} | Conflictos de nombre omitidos: {omitidos}")
    for propuesta in propuestas[:20]:
        print(
            f"  {propuesta['relative']}: {propuesta['old_extension']} -> "
            f"{propuesta['new_extension']} ({propuesta['category']})"
        )
    if len(propuestas) > 20:
        print(f"  ... y {len(propuestas) - 20} cambios más.")
    if input("\n¿Aprobar todos estos cambios? [s/N]: ").strip().lower() not in {"s", "si", "sí", "y", "yes"}:
        print("Renombrado cancelado; no se modificó ningún archivo.")
        return

    renombrados = 0
    errores = 0
    for propuesta in propuestas:
        try:
            if os.path.exists(propuesta["destination"]):
                omitidos += 1
                continue
            os.rename(propuesta["source"], propuesta["destination"])
            renombrados += 1
        except OSError as error:
            errores += 1
            print(f"No se pudo renombrar '{propuesta['relative']}': {error}")
    print(f"\nRenombrado completado: {renombrados} archivos, {errores} errores, {omitidos} conflictos omitidos.")


def corregir_ubicaciones_por_contenido(carpeta):
    """Revisa carpetas de categoría ya existentes y propone mover discrepancias seguras."""
    carpeta = os.path.abspath(carpeta)
    modelo = memoria_algorisme
    red = cargar_red_neuronal()
    categorias_validas = set(CATEGORIAS_REDES) | set(KEYWORDS_POR_CATEGORIA)
    for historial in modelo.values():
        if isinstance(historial, dict):
            categorias_validas.update(
                categoria for categoria in historial
                if isinstance(categoria, str) and categoria not in {".", ".."}
                and os.path.basename(categoria) == categoria
            )

    plan = []
    destinos_reservados = set()
    revisados = 0
    inciertos = 0
    for raiz, directorios, nombres in os.walk(carpeta):
        directorios[:] = [
            nombre for nombre in directorios
            if nombre != NOM_CUARENTENA and not os.path.islink(os.path.join(raiz, nombre))
        ]
        for nombre in nombres:
            ruta_origen = os.path.join(raiz, nombre)
            relativo = os.path.relpath(ruta_origen, carpeta)
            categoria_actual = relativo.split(os.sep, 1)[0]
            if categoria_actual not in categorias_validas or os.path.islink(ruta_origen):
                continue
            if os.path.abspath(ruta_origen) in {
                os.path.abspath(FITXER_MODEL),
                os.path.abspath(FITXER_CATALOGO_MIME),
                os.path.abspath(FITXER_RED_NEURONAL),
            }:
                continue
            try:
                with open(ruta_origen, "rb") as fitxer:
                    cabecera = fitxer.read(65536)
            except OSError:
                inciertos += 1
                continue
            categoria, confianza, razones = clasificar_archivo_inteligente(
                ruta_origen, modelo, red, relativo, cabecera
            )
            revisados += 1
            if categoria is None or confianza < CONFIANCA_MINIMA:
                inciertos += 1
                continue
            if categoria == categoria_actual:
                continue

            carpeta_destino = os.path.join(carpeta, categoria)
            ruta_destino = obtenir_ruta_no_colisionant(carpeta_destino, nombre)
            clave = os.path.normcase(os.path.abspath(ruta_destino))
            base, extension = os.path.splitext(nombre)
            sufijo = 1
            while clave in destinos_reservados:
                ruta_destino = os.path.join(carpeta_destino, f"{base}_{sufijo}{extension}")
                clave = os.path.normcase(os.path.abspath(ruta_destino))
                sufijo += 1
            destinos_reservados.add(clave)
            plan.append((ruta_origen, ruta_destino, categoria_actual, categoria, confianza, razones))

    print(f"\nRevisión de ubicaciones: {revisados} archivos examinados, {inciertos} inciertos.")
    if not plan:
        print("No se encontraron ubicaciones que deban corregirse con confianza suficiente.")
        return
    print(f"Cambios de carpeta propuestos: {len(plan)}")
    for origen, destino, actual, nueva, confianza, razones in plan[:25]:
        print(
            f"{os.path.relpath(origen, carpeta)}: {actual} -> {nueva} "
            f"({confianza:.0%}; {', '.join(razones)})"
        )
    if len(plan) > 25:
        print(f"... y {len(plan) - 25} cambios más.")
    if input("¿Corregir estas ubicaciones? [s/N]: ").strip().lower() not in {"s", "si", "sí", "y", "yes"}:
        print("Revisión cancelada; no se movió ningún archivo.")
        return

    movidos = 0
    errores = 0
    for origen, destino, actual, nueva, confianza, razones in plan:
        try:
            os.makedirs(os.path.dirname(destino), exist_ok=True)
            if os.path.exists(destino):
                destino = obtenir_ruta_no_colisionant(os.path.dirname(destino), os.path.basename(destino))
            shutil.move(origen, destino)
            movidos += 1
        except OSError as error:
            errores += 1
            print(f"No se pudo mover '{origen}': {error}")
    print(f"Ubicaciones corregidas: {movidos}, errores: {errores}.")


def asistente_completo():
    """Ejecuta el flujo principal sobre una carpeta con confirmación por acción."""
    carpeta = pedir_carpeta("Carpeta que quieres revisar y organizar: ")
    if not carpeta:
        return

    imprimir_seccion("Paso 1/5 - Informe de archivos, espacio y duplicados")
    mostrar_informe_carpeta(carpeta)

    imprimir_seccion("Paso 2/5 - Revisión de extensiones")
    renombrar_extensiones_con_aviso(carpeta)

    imprimir_seccion("Paso 3/5 - Cuarentena reversible de duplicados")
    respuesta = input("¿Quieres revisar duplicados y poner copias en cuarentena? [s/N]: ").strip().lower()
    if respuesta in {"s", "si", "sí", "y", "yes"}:
        poner_duplicados_en_cuarentena(carpeta)
    else:
        print("Cuarentena omitida.")

    imprimir_seccion("Paso 4/5 - Revisión de ubicaciones existentes")
    corregir_ubicaciones_por_contenido(carpeta)

    imprimir_seccion("Paso 5/5 - Organización decidida por la MLP")
    organitzar_fitxers(carpeta, solo_red=True)
    imprimir_seccion("Asistente completo finalizado")


def ejecutar_menu_avanzado():
    while True:
        print("\n=== Herramientas avanzadas ===")
        print("1) Organizar solo (MLP neuronal)")
        print("2) Enseñar una categoría al modelo")
        print("3) Entrenar el modelo estadístico")
        print("4) Entrenar la red neuronal")
        print("5) Clasificar un archivo")
        print("6) Corregir extensiones con aviso")
        print("7) Analizar espacio y duplicados")
        print("8) Poner duplicados en cuarentena")
        print("9) Restaurar una cuarentena")
        print("10) Corregir archivos mal ubicados")
        print("11) Organizar solo con la MLP neuronal")
        print("0) Volver")
        try:
            opcion = input("Elige una opción [0-11]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nVolviendo al menú principal.")
            return
        if opcion == "0":
            return
        try:
            if opcion == "1":
                organitzar_fitxers()
            elif opcion == "2":
                entrenar_model_manual()
            elif opcion == "3":
                entrenar_model_massiu(total=5000)
            elif opcion == "4":
                entrenar_red_desde_archivos_reales()
            elif opcion == "5":
                clasificar_archivo_con_red_guardada()
            elif opcion == "6":
                renombrar_extensiones_con_aviso()
            elif opcion == "7":
                carpeta = pedir_carpeta("Carpeta que quieres analizar: ")
                if carpeta:
                    mostrar_informe_carpeta(carpeta)
            elif opcion == "8":
                poner_duplicados_en_cuarentena()
            elif opcion == "9":
                restaurar_cuarentena()
            elif opcion == "10":
                carpeta = pedir_carpeta("Carpeta cuyas ubicaciones quieres revisar: ")
                if carpeta:
                    corregir_ubicaciones_por_contenido(carpeta)
            elif opcion == "11":
                organitzar_fitxers(solo_red=True)
            else:
                print("Opción no válida; elige un número del 0 al 11.")
        except KeyboardInterrupt:
            print("\nAcción cancelada; el menú sigue disponible.")
        except (OSError, ValueError) as error:
            print(f"No se pudo completar la acción: {error}")


def ejecutar_menu():
    """Menú principal sencillo con asistente de un solo flujo."""
    while True:
        categorias_aprendidas = {
            categoria
            for historial in memoria_algorisme.values()
            if isinstance(historial, dict)
            for categoria in historial
        } - set(CATEGORIAS_REDES)
        estado_red = "entrenada" if os.path.isfile(FITXER_RED_NEURONAL) else "pendiente de entrenar"
        print("\n=== Organizador inteligente de archivos ===")
        print(f"Red neuronal: {estado_red}")
        print(
            f"MLP: {len(CATEGORIAS_MODELO)} etiquetas "
            f"({len(CATEGORIAS_REDES)} generales + {len(CATEGORIAS_MODELO) - len(CATEGORIAS_REDES)} específicas)"
        )
        print(f"Categorías adicionales aprendidas del usuario: {len(categorias_aprendidas)}")
        print("1) Organizar todo con la MLP neuronal")
        print("2) Herramientas avanzadas")
        print("3) Salir")
        try:
            opcion = input("Elige una opción [1-3]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAplicación cerrada.")
            return
        if opcion == "3":
            print("Hasta luego.")
            return
        try:
            if opcion == "1":
                organitzar_fitxers(solo_red=True)
            elif opcion == "2":
                ejecutar_menu_avanzado()
            else:
                print("Opción no válida. Elige 1, 2 o 3.")
        except KeyboardInterrupt:
            print("\nAcción cancelada. No se ha cerrado el programa.")
        except (OSError, ValueError) as error:
            print(f"No se pudo completar la acción: {error}")


if __name__ == '__main__':
    ejecutar_menu()
