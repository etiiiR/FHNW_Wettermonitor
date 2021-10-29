import weatherimport as wd
import matplotlib.pyplot as plt
import pandas as pd

wd.init()
#print(wd.get_all_measurements("mythenquai", "1d"))

#print(wd.get_measurement(wd.Measurement.Humidity, "mythenquai", "1d"))

#print(wd.extract_anomaly("mythenquai", "100w")) 

wd.generate_spline([wd.Measurement.Air_temp], "mythenquai", "10w", "Temperatur T in °C", showPlot = False, imagePath = "image1.png")

wd.generate_plot_colMatrix([(wd.Measurement.Air_temp, ("Temperatur", "T", "°C")), (wd.Measurement.Humidity, ("Luftfeuchtigkeit", "φ", "%"))], "mythenquai", "1w", showPlot = False, imagePath = "image2.png")

wd.generate_plot_rowMatrix([(wd.Measurement.Air_temp, ("Temperatur", "T", "°C")), (wd.Measurement.Humidity, ("Luftfeuchtigkeit", "φ", "%"))], "mythenquai", "1w", showPlot = False, imagePath = "image3.png")

wd.generate_windRose("mythenquai", "1d", showPlot = False, imagePath = "image4.png")



#vorsicht... es gibt teilweise leere datenpunkte (NaN), ausserdem sind zeitsprünge möglich (unterbruch der Messungen)