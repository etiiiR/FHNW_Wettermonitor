from datetime import datetime
import weatherimport as wd
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

wd.init()
#print(wd.get_all_measurements("mythenquai", "1d"))

#print(wd.get_measurement(wd.Measurement.Humidity, "mythenquai", "1d"))

#print(wd.extract_anomaly("mythenquai", "100w")) 

#wd.generate_spline([wd.Measurement.Air_temp], "mythenquai", "10w", "Temperatur T in °C", showPlot = True, imagePath = "image1.png")

#wd.generate_plot_colMatrix([(wd.Measurement.Air_temp, ("Temperatur", "T", "°C")), (wd.Measurement.Humidity, ("Luftfeuchtigkeit", "φ", "%"))], "mythenquai", "1w", showPlot = True, imagePath = "image2.png")

#wd.generate_plot_rowMatrix([(wd.Measurement.Air_temp, ("Temperatur", "T", "°C")), (wd.Measurement.Humidity, ("Luftfeuchtigkeit", "φ", "%"))], "mythenquai", (datetime(2021, 9, 1), datetime.now()), showPlot = True, imagePath = "image3.png")

#wd.generate_windRose("mythenquai", "1d", showPlot = True, imagePath = "image4.png")

#vorsicht... es gibt teilweise leere datenpunkte (NaN), ausserdem sind zeitsprünge möglich (unterbruch der Messungen)

#forecast: neirest neibour

dateToCheck = datetime(2020, 5, 20)
bestDate = wd.nearest_neighbour("mythenquai", dateToCheck, 1) #suche einen ähnlichen Tag um den 2020.8.20 +- 1 Monat in allen verfügbaren Jahren 
print("DateFound: ", bestDate)

measurements = [wd.Measurement.Air_temp, wd.Measurement.Humidity]
df1 = wd.get_measurements(measurements, "mythenquai", (dateToCheck, datetime(dateToCheck.year, dateToCheck.month, dateToCheck.day, 23, 59)))
df2 = wd.get_measurements(measurements, "mythenquai", (bestDate, datetime(bestDate.year, bestDate.month, bestDate.day, 23, 59)))
fig, axs = plt.subplots(1, 2)
axs[0].plot(df1["time"].values, df1[[measurement.value for measurement in measurements]].values)
axs[1].plot(df2["time"].values, df2[[measurement.value for measurement in measurements]].values)
plt.show()

#test of construct_day_vector function
#df2 = pd.DataFrame(np.array([[1, 4, 7], [2, 5, 8], [3, 6, 9]]),
#                   columns=['a', 'b', 'c'])
#limit = [(1, 3, 1), (4, 6, 1), (7, 9, 1)]
#
#print(df2)
#
#print(wd.construct_day_vector(df2, limit))

