"""
Aqui desarrollare un programa para decargar los datos Tesis
Datos a descargar: FLOWS
"""

#Importo paquetes
import pyautogui
import time
import pandas as pd

#Cargo los RICS
df = pd.read_excel("RIC.xlsx")

### Flows download

for i in df["RIC"]:
    #Identifier...
    pyautogui.moveTo(80, 585, duration=1)

    #Escribo el RIC
    pyautogui.click()
    
    pyautogui.write(str(i))

    #Search
    pyautogui.moveTo(375, 750, duration=1)

    #Click
    pyautogui.click()

    #Espera
    time.sleep(10)

    #Flow history botton
    pyautogui.moveTo(555, 525, duration=1)

    pyautogui.click()

    #Excel download
    pyautogui.moveTo(2920, 580, duration=1)

    pyautogui.click()
    
    time.sleep(1.5)

    #Cerrar aviso
    pyautogui.moveTo(2950, 177, duration=1)

    pyautogui.click()

    #Volver al menu ("Funds")
    pyautogui.moveTo(300, 330, duration=1)

    pyautogui.click()

#Funciono perfecto



