import weatherimport as wd
import matplotlib.pyplot as plt
import pandas as pd

wd.init()
#print(wd.get_all_measurements("mythenquai", "1d"))

#print(wd.get_measurement(wd.Measurement.Humidity, "mythenquai", "1d"))

df = wd.generate_spline([wd.Measurement.Air_temp], "mythenquai", "1w", showPlot = True)

wd.generate_plot_matrix_x_1([(wd.Measurement.Air_temp, ("Temperatur", "T", "°C")), (wd.Measurement.Humidity, ("Luftfeuchtigkeit", "φ", "%"))], "mythenquai", "1w", showPlot = True)

wd.generate_windRose("mythenquai", "1d", showPlot = True)