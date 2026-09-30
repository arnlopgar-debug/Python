import os

CARPETA_A_ORGANITZAR = input("Introduce la ruta de la carpeta que deseas organizar: ")
while not os.path.isdir(CARPETA_A_ORGANITZAR):
    print("La ruta introducida no es válida. Por favor, introduce una ruta de carpeta válida.")
    CARPETA_A_ORGANITZAR = input("Introduce la ruta de la carpeta que deseas organizar: ")

DICCIONARIO_EXTENSIONES = {
    "Documentos": [".pdf", ".docx",".txt", ".xlsx", ".pptx"],
    "Imágenes": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
    "Videos": [".mp4", ".avi", ".mkv", ".mov"],
    "Audio": [".mp3", ".wav", ".flac"],
    "Archivos_Comprimidos": [".zip", ".rar", ".tar", ".gz"],
    "Programación": [".py", ".java", ".c", ".cpp", ".js", ".html", ".css"]
}
archivos = os.listdir(CARPETA_A_ORGANITZAR)

for nombre_archivo in archivos:

    ruta_completa = os.path.join(CARPETA_A_ORGANITZAR, nombre_archivo)

    if os.path.isfile(ruta_completa):
        extension = os.path.splitext(nombre_archivo)[1].lower()

        encontrado = False
        for categoria, extensiones_validas in DICCIONARIO_EXTENSIONES.items():
            if extension in extensiones_validas:
                print(f"L'arxiu ha d'anar a la carpeta: {categoria}")
                carpeta_destino = os.path.join(CARPETA_A_ORGANITZAR, categoria)
                if not os.path.exists(carpeta_destino):
                    os.makedirs(carpeta_destino)
                os.rename(ruta_completa, os.path.join(carpeta_destino, nombre_archivo))

                encontrado = True
                break

        if not encontrado:
            print(f"No se encontró una categoría para el archivo: {nombre_archivo}. Se mantendrá en la carpeta original.")
            crear_carpeta = input("¿Deseas crear un carpeta de organización de todas formas? (s/n): ")
            while True:
                if crear_carpeta.lower() == "s":
                    carpeta_destino = os.path.join(CARPETA_A_ORGANITZAR, "Otros")
                    os.makedirs(carpeta_destino, exist_ok=True)
                    os.rename(ruta_completa, os.path.join(carpeta_destino, nombre_archivo))
                    print(f"Archivo {nombre_archivo} movido a la carpeta 'Otros'.")
                    break
                elif crear_carpeta.lower() == "n":
                    print(f"Archivo {nombre_archivo} se mantendrá en la carpeta original.")
                    break
                else:
                    print("Opción no válida. El archivo se mantendrá en la carpeta original.")