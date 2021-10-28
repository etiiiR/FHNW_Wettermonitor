from os import path
import weatherdata as wd
import matplotlib.pyplot as plt
import pandas as pd
import enum

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
def get_all_measurements(station : str, start_time : str):
  """
  get all entries in a specific time range (now - start_time)
  """

  df = wd.get_entries(config, station, start_time)
  df["time"] = df.index
  df = df.reset_index(drop = True)

  return df

def get_measurement(measurment : Measurement, station : str, start_time : str):
  """
  get single measurement in a specific time range (now - start_time)
  """

  df = wd.get_attr_entries(config, str(measurment.value), station, start_time)
  df["time"] = df.index
  df = df.reset_index(drop = True)

  return df

def get_measurements(measurements : list(Measurement), station : str, start_time : str):
  """
  get multible measurement in a specific time range (now - start_time)
  """

  df = wd.get_multible_attr_entries(config, [measurement.value for measurement in measurements], station, start_time)
  df["time"] = df.index
  df = df.reset_index(drop = True)

  return df


#generate chart
def generate_chart_singleSeries(measurement : Measurement, station : str, start_time : str, showPlot = False, imagePath = None):
  """
  generate and show/save plot
  """
  
  df = get_measurement(measurement, station, start_time)

  df.plot(x = "time", y = measurement.value)

  if showPlot:
    plt.show()
  else:
    plt.savefig(imagePath)

def generate_chart_multibleSeries(measurements : list(Measurement), station : str, start_time : str, showPlot = False, imagePath = None):
  """
  generate and show/save plot
  """

  df = get_measurements(measurements, station, start_time)

  df.plot(x = "time", y = [measurement.value for measurement in measurements])

  if showPlot:
    plt.show()
  else:
    plt.savefig(imagePath)

if __name__ == '__main__':
  pass