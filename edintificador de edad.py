import os
import time

def limpiar_pantalla():
    """Limpia la pantalla de la consola."""
    os.system('cls' if os.name == 'nt' else 'clear')

def pedir_intento():
    intentar = input("¿Quieres intentarlo de nuevo? (s/n): ").strip().lower()
    return intentar == "s"


def pedir_edad():
    """Pide una edad y repite hasta recibir un valor válido."""
    while True:
        try:
            edad = int(input("Introduce tu edad: "))
            if edad < 0 or edad > 99:
                raise ValueError
            return edad
        except ValueError:
            print("Por favor, introduce una edad válida")

def pedir_actividad():
    while True:
        print("""
Ecoje una actividad de la lista:
        
1. Discoteca
2. Cine
3. Jumping
4. Parque acuático 

        """)
        numero = input("Introduce el numero de actividad: \n")

        if numero == "1":
            actividad = "discoteca"
            edad_minima = 18
        elif numero == "2":
            actividad = "cine"
            edad_minima = 0
        elif numero == "3":
            actividad = "jumping"
            edad_minima = 8
        elif numero == "4":
            actividad = "parque acuático"
            edad_minima = 12
        else:
            limpiar_pantalla()
            print("Actividad no válida. Por favor, elige una opción del 1 al 4.")
            time.sleep(2)
            limpiar_pantalla()
            continue
        return numero, actividad, edad_minima


while True:
    limpiar_pantalla()
    nombre = input("Introduce tu nombre: ")
    edad = pedir_edad()
    limpiar_pantalla()
    numero_actividad, nombre_actividad, edad_minima = pedir_actividad()

    if edad <= 12:
        categoria = "niño"
    elif edad <= 16:
        categoria = "adolescente"
    elif edad <= 18:
        categoria = "adulto joven"
    elif edad <= 64:
        categoria = "adulto"
    elif edad <= 99:
        categoria = "adulto mayor"
    elif edad >= 100:
        categoria = "edad imposible"

    ##print(f"{nombre} tiene {edad} años y es un/a {categoria}.")

    if edad >= edad_minima and categoria != "edad imposible":
        limpiar_pantalla()
        print(f"Felicidades {nombre}, eres de la categoria {categoria}, y puedes entrar a la actividad {nombre_actividad}.")

    elif categoria == "edad imposible":
        limpiar_pantalla()
        print(f"Lo siento {nombre}, la edad que has introducido es imposible. Por favor, introduce una edad válida.")
        time.sleep(4)
        limpiar_pantalla()
    else:
        limpiar_pantalla()
        print(f"Lo siento {nombre}, eres de la categoria {categoria}, y no puedes entrar a la actividad {nombre_actividad}. Te faltan {edad_minima - edad} años.")

    if not pedir_intento():
        limpiar_pantalla()
        print("Gracias por usar el programa")
        time.sleep(4)
        limpiar_pantalla()
        break

    limpiar_pantalla()
    print("Volviendo a empezar...\n")
    time.sleep(4)
    limpiar_pantalla()


