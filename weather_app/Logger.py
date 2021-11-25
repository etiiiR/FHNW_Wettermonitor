from datetime import datetime
from pandas.io.pytables import Table
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


#test linear formula
#max = 10
#min = -10
#item = -10
#normalize_to = 2
#weight = 1
#print((((normalize_to * 2 * item) / (max - min)) + ((-1 * normalize_to) - ((normalize_to * 2 * min) / (max - min)))) * weight)


#forecast: neirest neibour
dateToCheck = datetime(2018, 9, 15)
measurements = [wd.Measurement.Air_temp, wd.Measurement.Humidity, wd.Measurement.Pressure]
lim_Weights = [(-10, 10, 0.5), (-40, 40, 0.3), (-10, 10, 1)]
bestDate = wd.nearest_neighbour("mythenquai", dateToCheck, 1, day_window_size = "2h", measurements = measurements, vector_lim_weight = lim_Weights) #suche einen ähnlichen Tag um den 2020.8.20 +- 1 Monat in allen verfügbaren Jahren 
print("DateFound: ", bestDate)

show_measurements = [wd.Measurement.Pressure]
df1 = wd.get_measurements(show_measurements, "mythenquai", (dateToCheck, datetime(dateToCheck.year, dateToCheck.month, dateToCheck.day, 23, 59)))
df2 = wd.get_measurements(show_measurements, "mythenquai", (bestDate, datetime(bestDate.year, bestDate.month, bestDate.day, 23, 59)))
fig, axs = plt.subplots(1, 2)
axs[0].plot(df1["time"].values, df1[[measurement.value for measurement in show_measurements]].values)
axs[1].plot(df2["time"].values, df2[[measurement.value for measurement in show_measurements]].values)
axs[0].legend([measurement.value for measurement in show_measurements])
axs[1].legend([measurement.value for measurement in show_measurements])
plt.show()



#test of construct_day_vector function
#df2 = pd.DataFrame(np.array([[1, 4, 7], [2, 5, 8], [3, 6, 9]]),
#                   columns=['a', 'b', 'c'])
#limit = [(1, 3, 1), (4, 6, 1), (7, 9, 1)]
#
#print(df2)
#
#print(wd.construct_day_vector(df2, limit))


#test window function
#d = {"time": [datetime(2008, 5, 25, 3, 0, 0), datetime(2008, 5, 25, 4, 0, 0), datetime(2008, 5, 25, 10, 0, 0)], "col1": [1, 2, 3]}
#table_day = pd.DataFrame(data= d)

#time_windowed = table_day.groupby([pd.Grouper(key = 'time', freq='4h', origin = "start_day")]) #group by an interval of 4h

#for _, table in time_windowed:
#    print(table)