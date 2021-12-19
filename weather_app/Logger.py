from datetime import datetime
from datetime import timedelta
from pandas.io.pytables import Table
import weatherimport as wd
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import random

wd.init()
#print(wd.get_all_measurements("mythenquai", "1d"))

#print(wd.get_measurement(wd.Measurement.Humidity, "mythenquai", "1d"))

#print(wd.extract_anomaly("mythenquai", "100w")) 

#wd.generate_spline([wd.Measurement.Air_temp], "mythenquai", "20w", "Temperatur T in °C", showPlot = True, imagePath = "image1.png")

wd.generate_plot_colMatrix([(wd.Measurement.Air_temp, ("Temperatur", "T", "°C")), (wd.Measurement.Humidity, ("Luftfeuchtigkeit", "φ", "%"))], "mythenquai", "1w", showPlot = True, imagePath = "image2.png", title = "Tagesplot")

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
#dateToCheck = datetime(2021, 11, 25)
#bestDate = wd.forecast_of_tomorrow("mythenquai", dateToCheck)[0]
#print("DateFound: ", bestDate)
#
#show_measurements = [wd.Measurement.Air_temp, wd.Measurement.Humidity]
#df1 = wd.get_measurements(show_measurements, "mythenquai", (dateToCheck, datetime(dateToCheck.year, dateToCheck.month, dateToCheck.day, 23, 59)))
#df2 = wd.get_measurements(show_measurements, "mythenquai", (bestDate, datetime(bestDate.year, bestDate.month, bestDate.day, 23, 59)))
#fig, axs = plt.subplots(len(show_measurements), 2)
#for i in range(0, len(show_measurements)):
#    axs[i, 0].plot(df1["time"].values, df1[show_measurements[i].value].values)
#    axs[i, 1].plot(df2["time"].values, df2[show_measurements[i].value].values)
#    axs[i, 0].set_title(show_measurements[i].name)
#    axs[i, 1].set_title(show_measurements[i].name)
#plt.show()


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



#test construct_day_vector
#d = {"index": [datetime(2008, 5, 25, 3, 0, 0), datetime(2008, 5, 25, 3, 10, 0), datetime(2008, 5, 25, 3, 20, 0)], "col1": [1, 2, 3], "col2": [4, 5, 6]}
#table_day = pd.DataFrame(data = d).set_index("index")
#table_day = table_day.sort_index()
#table_day1 = table_day.copy()
#print(table_day)
#print(wd.construct_day_vector(table_day, [(0, 5, 1), (0, 3, 1)]))
#print(wd.construct_day_vector_old(table_day1, [(0, 5, 1), (0, 3, 1)]))

def generateRandomDate(startDate, endDate) -> datetime:
    time_between_dates = endDate - startDate
    days_between_dates = time_between_dates.days

    random_number_of_days = random.randrange(days_between_dates)
    return startDate + timedelta(days=random_number_of_days)

numberOfDates = 100
startDate = datetime(2008, 1, 1)
endDate = datetime(2020, 12, 1)

dates = []
random.seed(53165441847244654)
for i in range(0, numberOfDates):
    date = generateRandomDate(startDate, endDate)
    dates.append(datetime(date.year, date.month, date.day))

predictions = []
for date in dates:
    try:
        prediction = wd.forecast_of_tomorrow("mythenquai", date)[0]
        predictions.append((date, prediction))
    
    except:
        print("Target day: ", date, " couldn't be forecasted... skip")
    

#comparison
nextDateAlgorithm_mean = []
nearestNeighbourAlgorithm_mean = []
nextDateAlgorithm_std = []
nearestNeighbourAlgorithm_std = []
for prediction in predictions:
    targetDate = prediction[0]
    targetTimeRange =  (datetime(targetDate.year, targetDate.month, targetDate.day, 0, 0, 1), datetime(targetDate.year, targetDate.month, targetDate.day, 23, 59, 59)) 
    nearestNDate = prediction[1]
    print("nearest n date: ", nearestNDate)
    nearestNDateTimeRange =  (datetime(nearestNDate.year, nearestNDate.month, nearestNDate.day, 0, 0, 1), datetime(nearestNDate.year, nearestNDate.month, nearestNDate.day, 23, 59, 59)) 
    nextDate = targetDate + timedelta(days=1)
    nextDateTimeRange =  (datetime(nextDate.year, nextDate.month, nextDate.day, 0, 0, 1), datetime(nextDate.year, nextDate.month, nextDate.day, 23, 59, 59)) 
    
    data_target = wd.get_measurement(wd.Measurement.Air_temp, "mythenquai", targetTimeRange)
    data_nearestN = wd.get_measurement(wd.Measurement.Air_temp, "mythenquai", nearestNDateTimeRange)
    data_nextDate = wd.get_measurement(wd.Measurement.Air_temp, "mythenquai", nextDateTimeRange)
    
    mean_temp_target = np.nanmean(data_target["air_temperature"].tolist())
    mean_temp_nearestN = np.nanmean(data_nearestN["air_temperature"].tolist())
    mean_temp_data_nextDate = np.nanmean(data_nextDate["air_temperature"].tolist())

    std_temp_target = np.nanstd(data_target["air_temperature"].tolist())
    std_temp_nearestN = np.nanstd(data_nearestN["air_temperature"].tolist())
    std_temp_data_nextDate  = np.nanstd(data_nextDate["air_temperature"].tolist())

    difference_mean_nearestN = np.abs(mean_temp_target - mean_temp_nearestN)
    difference_mean_nextDate = np.abs(mean_temp_target - mean_temp_data_nextDate)

    difference_std_nearestN = np.abs(std_temp_target - std_temp_nearestN)
    difference_std_nextDate = np.abs(std_temp_target - std_temp_data_nextDate)

    nearestNeighbourAlgorithm_mean.append(difference_mean_nearestN)
    nextDateAlgorithm_mean.append(difference_mean_nextDate)
    nearestNeighbourAlgorithm_std.append(difference_std_nearestN)
    nextDateAlgorithm_std.append(difference_std_nextDate)

print("Accuracy nearest neighbour (mean difference): +-", np.mean(nearestNeighbourAlgorithm_mean), " °C")
print("Accuracy next date (mean difference): +-", np.mean(nextDateAlgorithm_mean), " °C") 
print("Accuracy nearest neighbour (standard deviation difference): +-", np.mean(nearestNeighbourAlgorithm_std), " °C")
print("Accuracy next date (standard deviation difference): +-", np.mean(nextDateAlgorithm_std), " °C") 





""" #test construct_window_vector
dataFrame = wd.get_measurements([wd.Measurement.Air_temp, wd.Measurement.Humidity], "mythenquai", (datetime(2020, 5, 1, 13, 0), datetime(2020, 5, 1, 13, 50)), keepIndex=True)
dataFrame.iloc[-1, -1] = None

print(dataFrame)

print(wd.construct_window_vector(dataFrame, [(-10, 10, 1), (-40, 40, 0.2)])) """