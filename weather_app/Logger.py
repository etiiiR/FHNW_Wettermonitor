from datetime import datetime
import weatherimport as wd
import matplotlib.pyplot as plt
import pandas as pd

wd.init()
#print(wd.get_all_measurements("mythenquai", "1d"))

#print(wd.get_measurement(wd.Measurement.Humidity, "mythenquai", "1d"))

#print(wd.extract_anomaly("mythenquai", "100w")) 

wd.generate_spline([wd.Measurement.Air_temp], "mythenquai", "10w", "Temperatur T in °C", showPlot = True, imagePath = "image1.png")

wd.generate_plot_colMatrix([(wd.Measurement.Air_temp, ("Temperatur", "T", "°C")), (wd.Measurement.Humidity, ("Luftfeuchtigkeit", "φ", "%"))], "mythenquai", "1w", showPlot = True, imagePath = "image2.png")

wd.generate_plot_rowMatrix([(wd.Measurement.Air_temp, ("Temperatur", "T", "°C")), (wd.Measurement.Humidity, ("Luftfeuchtigkeit", "φ", "%"))], "mythenquai", (datetime(2021, 9, 1), datetime.now()), showPlot = True, imagePath = "image3.png")

wd.generate_windRose("mythenquai", "1d", showPlot = True, imagePath = "image4.png")

#vorsicht... es gibt teilweise leere datenpunkte (NaN), ausserdem sind zeitsprünge möglich (unterbruch der Messungen)

#forecast: neirest neibour
