from os import path

from numpy import dsplit
import weatherdata as wd
import matplotlib.pyplot as plt
import pandas as pd
import enum
from windrose import WindroseAxes #pip install windrose

class Measurement(enum.Enum):
  Air_temp = "air_temperature"
  Dew_point = "dew_point"
  Humidity = "humidity"
  Wind_direction = "wind_direction"
  Wind_force_avg_10min = "wind_force_avg_10min"
  Wind_gust_max_10min = "wind_gust_max_10min"
  Wind_speed_avg_10min = "wind_speed_avg_10min"
  Wind_chill = "windchill"



config = wd.Config()

def init():
  """
  connect to db, import historic data if not imported, import latest data (no periodic read)
  """

  wd.connect_db(config)
  wd.try_import_csv_file(config, 'mythenquai', '../Messwerte/messwerte_mythenquai_2007-2020.csv')
  wd.try_import_csv_file(config, 'tiefenbrunnen', '../Messwerte/messwerte_tiefenbrunnen_2007-2020.csv')
  wd.import_latest_data(config, periodic_read=False)


def read_data_continuesly():
  """
  start importing with periodic read
  """

  wd.import_latest_data(config, periodic_read=True)


#get entries
def get_all_measurements(station : str, start_time : str, timeFilling = True):
  """
  get all entries in a specific time range (now - start_time) and fill up missing timeSteps with NaN (can be disabled)
  """

  df = wd.get_entries(config, station, start_time)

  if timeFilling:
    df = df.resample("10min").asfreq()#resample (zeitlücken mit NaN füllen)

  df["time"] = df.index
  df = df.reset_index(drop = True)

  return df

def get_measurement(measurment : Measurement, station : str, start_time : str, timeFilling = True):
  """
  get single measurement in a specific time range (now - start_time) and fill up missing timeSteps with NaN (can be disabled)
  """

  df = wd.get_attr_entries(config, str(measurment.value), station, start_time)

  if timeFilling:
    df = df.resample("10min").asfreq()#resample (zeitlücken mit NaN füllen)

  df["time"] = df.index
  df = df.reset_index(drop = True)

  return df

def get_measurements(measurements : list(Measurement), station : str, start_time : str, timeFilling = True):
  """
  get multible measurements in a specific time range (now - start_time) and fill up missing timeSteps with NaN (can be disabled)
  """

  df = wd.get_multible_attr_entries(config, [measurement.value for measurement in measurements], station, start_time)
  
  if timeFilling:
    df = df.resample("10min").asfreq()#resample (zeitlücken mit NaN füllen)
  
  df["time"] = df.index
  df = df.reset_index(drop = True)

  return df


#generate chart
def generate_spline(measurements : list(Measurement), station : str, start_time : str, showPlot = False, imagePath = None):
  """
  generate and show/save plot (missing time -> fill with NaN)
  """

  df = get_measurements(measurements, station, start_time)

  df.plot(x = "time", y = [measurement.value for measurement in measurements])

  #plt.plot(x = df["time"].values, y = df[[measurement.value for measurement in measurements]].values)

  if showPlot:
    plt.show()
  else:
    plt.savefig(imagePath)

def generate_plot_vector(measurements : list(tuple((Measurement, tuple((str, str, str))))), station : str, start_time : str, showPlot = False, imagePath = None):
  """
  generiere vektor aus plots mit x Zeilen (missing time -> fill with NaN), Params: (measurements: liste aus Messungen und deren Einheiten tuple(name z.B. Temperatur, Formelzeichen: T, einheit: °C), station: stationsname, 
                                                            start_time: startzeit der Messungen z.B. 1d, showPlot: true -> plotte | false -> generiere image, imagepath: speicherpfad des images) 
  """

  if len(measurements) <= 1:
    raise Exception("Es müssen mindestens 2 measurements angegeben werden!")

  df = get_measurements([measurement[0] for measurement in measurements], station, start_time)

  fig, axs = plt.subplots(len(measurements), 1, sharex=True)

  for i, measurement in enumerate(measurements):
    measurement_type = measurement[0]
    unit_name = measurement[1][0]
    unit_symbol = measurement[1][1]
    unit = measurement[1][2]

    print(unit_name)
    print(unit)

    axs[i].plot(df["time"].values, df[measurement_type.value].values)
    axs[i].set(xlabel = "time", ylabel = f"{unit_name} {unit_symbol} in {unit}")
    axs[i].legend([unit_name])

  if showPlot:
    plt.show()
  else:
    plt.savefig(imagePath)

def generate_windRose(station : str, start_time : str, showPlot = False, imagePath = None):
  """
  generiere eine windrose (missing time -> wird ignoriert), Params: (station: stationsname, start_time: startzeit der Messungen z.B. 1d, showPlot: true -> plotte | false -> generiere image, imagepath: speicherpfad des images))
  """


  df = get_measurements([Measurement.Wind_direction, Measurement.Wind_speed_avg_10min], station, start_time, timeFilling = False)

  ax = WindroseAxes.from_ax()
  ax.bar(df["wind_direction"].values, df["wind_speed_avg_10min"].values, normed = True, opening = 0.8, edgecolor = "white")
  ax.set_legend()

  if showPlot:
    plt.show()
  else:
    plt.savefig(imagePath)
  

#anomaly detection
def extract_anomaly(station : str, start_time : str):
  """
  return stange data (null values, no values, data interruption)
  """

  df = get_all_measurements(station, start_time)
  df_anomaly = pd.DataFrame

  is_NaN = df.isnull()
  row_has_NaN = is_NaN.any(axis=1)
  df_has_NaN = df[row_has_NaN]

  is_Na = df.isna()
  row_has_Na = is_Na.any(axis=1)
  df_has_Na = df[row_has_Na]

  df_anomaly = pd.concat([df_has_NaN, df_has_Na])

  return df_anomaly

if __name__ == '__main__':
  pass