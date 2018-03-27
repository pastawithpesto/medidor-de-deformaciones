from tkinter import *
import tkinter.font
import time
import spidev
import statistics as stats
import csv
from reportlab.pdfgen import canvas
import numpy as np

#ADAFRUIT LIBS
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
from decimal import Decimal


# MATPLOTLIB
import matplotlib as mpl
mpl.use('tkagg')
import matplotlib.pyplot as plt

color_boton = 'ivory4'

SPI_PORT   = 0
SPI_DEVICE = 0

mcp = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
#GUI DEFINITIONS

win = Tk()
win.title("Medidor de Deformaciones Beta")
myFont = tkinter.font.Font(family = 'Helvetica', size = 12, weight = 'bold')

#####funciones######
#Define Variables
delay = 0.5
ldr_channel = 0
contador_mediciones = 0
mediciones = []
#Create SPI
spi = spidev.SpiDev()
spi.open(0, 0)
mediciones_ver1 = []

# return 1 es solo para que deje correr el programa sin tener la funcion escrita
def tomar_medicion():
    #medir y activar todos los botones de estadistica despues de 2 mediciones
    global contador_mediciones
    contador_mediciones += 1
    if contador_mediciones >= 2:
        histograma_button.config(state = 'normal')
        desv_std_button.config(state = 'normal')
        win.menubar.entryconfig("Graficar", state="normal")
    if contador_mediciones >= 1:
        win.menubar.entryconfig("CSV", state="normal")
        win.menubar.entryconfig("Gen. PDF", state="normal")

    readadc()
    return 1

def histograma():
    #hacer histograma despues de tomar 2 mediciones o mas
	plt.hist(mediciones, bins = 'auto', facecolor = 'red', alpha = 0.5)
	plt.show()
	return 1

def desv_std():
    #devolver el valor de la desviacion std
    desviacionEstandar = stats.pstdev(mediciones)
    return desviacionEstandar

def graficar():
    #genera una grafica y guarda un png de esta ademas que la muestra
    plt.plot(mediciones_ver1)
    plt.show()
    return 1

def guardar_csv():
    #guarda los datos tomados en un archivo csv
	mediciones_str_csv = ", ".join(str(h) for h in mediciones)
	with open('mediciones.csv','w') as valores_guardados:
          wr=csv.writer(valores_guardados, quoting=csv.QUOTE_NONE)
          wr.writerow(mediciones)
	return 1

def generar_pdf():
    #genera un pdf con los datos y grafica.
	c = canvas.Canvas("Mediciones_Reporte_" + str(time.strftime("_%Y_%m_%d_%H_%M_%S")) + ".pdf")
	c.drawString(100,750, "Reporte generado por Medidor de Deformaciones")
	mediciones_str = ", ".join(str(e) for e in mediciones)
	c.drawString(100,670, "Mediciones tomadas se pueden encontrar en el archivo CSV.")
	#c.drawString(100,630, "La desviacion estandar es de " + str(round(desv_std(),3)) + ", la varianza es de " + str(round(stats.pvariance(mediciones),3)) + ",")
	c.drawString(100, 600, "el valor minimo es de " + str(min(mediciones)) + " y el valor maximo es de " + str(max(mediciones)))
	c.drawString(100,570, " El promedio es: " + str(stats.mean(mediciones)))
	c.save()
	return 0

def reset_mediciones():
	global mediciones
	mediciones = []
	contador_mediciones = 0
	histograma_button.config(state = DISABLED)
	desv_std_button.config(state = DISABLED)
	win.menubar.entryconfig("Graficar", state="normal")
	win.menubar.entryconfig("CSV", state="normal")
	win.menubar.entryconfig("Gen. PDF", state="normal")
	return 1

calibraciones = []



def calibrar():
	global promedio_calibrado
	calibracion_gr = calibracion_input.get()
	try:
		calibracion_input_ = float(calibracion_gr)
	except:
		calibracion_input_= 0
	# Calibrar con regla de 3 simple
	for i in range(29):
		calibraciones.append(readadc())

	promedio_calibrado= round(stats.mean(calibraciones),3)
	print(str(promedio_calibrado))
	promedio_calibrado = (calibracion_input_/promedio_calibrado)
	print("IN: " + str(calibracion_input_))

	print("VALOR CALIBRADO x: " + str(promedio_calibrado))
	return promedio_calibrado

promedio_calibrado = 1

varias_mediciones = []
def medir_varios():
    histograma_button.config(state = 'normal')
    desv_std_button.config(state = 'normal')
    win.menubar.entryconfig("Graficar", state="normal")
    win.menubar.entryconfig("CSV", state="normal")
    win.menubar.entryconfig("Gen. PDF", state="normal")
    numero_escrito = numeroEntry.get()
    try:
        numero_ = int(numero_escrito) # Numero_escrito es entero
    except:
        numero_ = 0 #numero_escrito NO es entero

    if (numero_ >= 0) and (numero_ < 201):
	    for num in range(numero_):
		    readadc()
		    time.sleep(.01)
    else:
	    pass

    return 1
prom_mediciones = []
datos_calibrados = []
def readadc():
    global prom_mediciones
    # read SPI data from the MCP3008, 8 channels in total
    data = mcp.read_adc(0)
    for i in range(35):
        data = mcp.read_adc(0)
        datos_calibrados = data * promedio_calibrado # GRAMOS
        prom_mediciones.append(datos_calibrados) #los gramos se van a promediar.
        time.sleep(.01)
    prom_mediciones1 = stats.mean(prom_mediciones) # Pro_mediciones toma valor de su promedio
    mediciones.append(prom_mediciones) ## solo hace append un valor que es el promedio. esta parte se repetira n veces y se graficara.
    return prom_mediciones1

# Barra de menu
win.menubar = Menu(win)
win.menubar.add_command(label="Graficar", command = graficar, state = DISABLED)
win.menubar.add_command(label="CSV", command = guardar_csv, state = DISABLED)
win.menubar.add_command(label="Gen. PDF", command = generar_pdf, state = DISABLED)
# display the menu
win.config(menu=win.menubar)


#widgets
label_datos = tkinter.Label(win, text = "Datos")
label_datos.grid(row = 0, column = 1)

label_numerodemuestras = tkinter.Label(win, text = "Medicion")
label_numerodemuestras.grid(row = 0, column = 2,padx=10, pady=10)

numeroEntry = tkinter.Entry(win)
numeroEntry.grid(row = 2 , column = 1)

medir_variosButton = Button(win, command = medir_varios, text = "Med. Cont.", state = "normal")
medir_variosButton.grid(row = 2, column = 2)

label_configuracion_de_puente = tkinter.Label(win, text = "Calibracion")
label_configuracion_de_puente.grid(row = 2, column = 3)

calibracion_input = tkinter.Entry(win)
calibracion_input.grid(row = 3 , column = 3)

calibrarButton = Button(win, command = tomar_medicion, text = "Medir", font = myFont, bg = color_boton)
calibrarButton.grid(row = 2, column = 3)

medirButton = Button(win, command = reset_mediciones, text = 'Reset', font = myFont, bg = color_boton) #Creacion del boton, agregar funcion en parametro command
medirButton.grid(row = 2, column = 4) #posicion del boton

resetButton = Button(win, command = calibrar, text = "Configurar", font = myFont, bg = color_boton )
resetButton.grid(row = 3, column = 4)

histograma_button = Button(win, command = histograma, text = "Histograma", state = DISABLED)
histograma_button.grid(row = 3, column = 1, pady = 10)

desv_std_button = Button(win, command = desv_std, text = "Calcular Desv. Est.", state = DISABLED)
desv_std_button.grid(row = 4, column = 1, pady = 10)

#end
win.protocol("WM_DELETE_WINDOW") #Exit properly add close function if needed ("WM_DELETE_WINDOW",close)
win.mainloop() #loop forever
