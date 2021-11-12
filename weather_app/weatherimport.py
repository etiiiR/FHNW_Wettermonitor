import os
from time import time
from numpy import dsplit
import weatherdata as wd
import matplotlib.pyplot as plt
import pandas as pd
import enum
from pathlib import Path
from windrose import WindroseAxes #pip install windrose

class Measurement(enum.Enum):
  Air_temp = "air_temperature"
  Water_temp = "water_temperature"
  Dew_point = "dew_point"
  Precipitation = "precipitation"
  Water_level = "water_level"
  Pressure = "barometric_pressure_qfe"
  Humidity = "humidity"
  Wind_direction = "wind_direction"
  Wind_force_avg_10min = "wind_force_avg_10min"
  Wind_gust_max_10min = "wind_gust_max_10min"
  Wind_speed_avg_10min = "wind_speed_avg_10min"
  Wind_chill = "windchill"
  Radiation = "global_radiation"



config = wd.Config()
systemInitialized = False #True if database successfully initialized 

def systemInitialized():
  return systemInitialized

def init():
  """
  connect to db, import historic data if not imported, import latest data (no periodic read)
  """
  
  wd.connect_db(config)

  if wd.try_import_csv_file(config, 'mythenquai', str(Path(os.path.dirname(os.path.realpath(__file__))).parent) + "/Messwerte/messwerte_mythenquai_2007-2020.csv") and wd.try_import_csv_file(config, 'tiefenbrunnen', str(Path(os.path.dirname(os.path.realpath(__file__))).parent) + "/Messwerte/messwerte_tiefenbrunnen_2007-2020.csv"):
    wd.import_latest_data(config, periodic_read=False)
    print("Database successfully initialized.")
    systemInitialized = True
    return systemInitialized

  else:
    print("Database partially initialized... Database working but CSV file not importet!!!")
    systemInitialized = False
    return systemInitialized
  


def read_data_continuesly():
  """
  start importing with periodic read
  """

  wd.import_latest_data(config, periodic_read=True)

#functional
def _get_fmt(axis): #from https://stackoverflow.com/questions/49106889/get-the-date-format-on-a-matplotlib-plots-x-axis
    axis.axes.figure.canvas.draw()
    formatter = axis.get_major_formatter()
    locator_unit_scale = float(formatter._locator._get_unit())       
    fmt = next((fmt for scale, fmt in sorted(formatter.scaled.items())
                if scale >= locator_unit_scale),
                       formatter.defaultfmt)
    return fmt

#get entries
def get_all_measurements(station : str, time_range, timeFilling = True):
  """
  get all entries in a specific time range 

  Parameters:
  station (string): station name
  time_range (string or tuple of dateTime): timerange as string -> now to specific time in the past [1d, 2w, 5m...], timerage as tuple -> specific time in the pas to specific time in the past [tuple(dateTime, dateTime)]
  timeFilling (bool -> default: True): fill up missing measurements with NaN
  """

  if type(time_range) is tuple:
    df = wd.get_entries(config, station, start_time = time_range[0], stop_time = time_range[1])

  elif type(time_range) is str:
    df = wd.get_entries(config, station, time_range)

  else:
    raise Exception("time_range has to be a string or a tuple")


  if timeFilling:
    df = df.resample("10min").asfreq()#resample (zeitlücken mit NaN füllen)

  df["time"] = df.index
  df = df.reset_index(drop = True)

  return df

def get_measurement(measurment : Measurement, station : str, time_range, timeFilling = True):
  """
  get a specific entry in a specific time range 

  Parameters:
  measurement (Measurement): select measurement from Measurement [Measurement.air_temp, ...]
  station (string): station name
  time_range (string or tuple of dateTime): timerange as string -> now to specific time in the past [1d, 2w, 5m...], timerage as tuple -> specific time in the pas to specific time in the past [tuple(dateTime, dateTime)]
  timeFilling (bool -> default: True): fill up missing measurements with NaN
  """

  if type(time_range) is tuple:
    df = wd.get_attr_entries(config, str(measurment.value), station, start_time = time_range[0], stop_time = time_range[1])

  elif type(time_range) is str:
    df = wd.get_attr_entries(config, str(measurment.value), station, time_range)

  else:
    raise Exception("time_range has to be a string or a tuple")

  if timeFilling:
    df = df.resample("10min").asfreq()#resample (zeitlücken mit NaN füllen)

  df["time"] = df.index
  df = df.reset_index(drop = True)

  return df

def get_measurements(measurements : list(Measurement), station : str, time_range, timeFilling = True):
  """
  get a specific entries in a specific time range 

  Parameters:
  measurements (list(Measurement)): select measurements from Measurement [list(Measurement.air_temp, ...)]
  station (string): station name
  time_range (string or tuple of dateTime): timerange as string -> now to specific time in the past [1d, 2w, 5m...], timerage as tuple -> specific time in the pas to specific time in the past [tuple(dateTime, dateTime)]
  timeFilling (bool -> default: True): fill up missing measurements with NaN
  """

  if type(time_range) is tuple:
    df = wd.get_multible_attr_entries(config, [measurement.value for measurement in measurements], station, start_time = time_range[0], stop_time = time_range[1])

  elif type(time_range) is str:
    df = wd.get_multible_attr_entries(config, [measurement.value for measurement in measurements], station, time_range)
  else:
    raise Exception("time_range has to be a string or a tuple")

  if timeFilling:
    df = df.resample("10min").asfreq()#resample (zeitlücken mit NaN füllen)
  
  df["time"] = df.index
  df = df.reset_index(drop = True)

  return df


#generate chart
def generate_spline(measurements : list(Measurement), station : str, time_range, ylabel_name : str, showPlot = False, imagePath = None):
  """
  create single or multible splines from a specific time range in one chart

  Parameters:
  measurements (list(Measurement)): select measurements from Measurement [list(Measurement.air_temp, ...)]
  station (string): station name
  time_range (string or tuple of dateTime): timerange as string -> now to specific time in the past [1d, 2w, 5m...], timerage as tuple -> specific time in the pas to specific time in the past [tuple(dateTime, dateTime)]
  ylabel_name (string): label name of y axis
  showPlot (bool -> default: False): for debugging -> True: instead of creating an image, plot it directli
  imagePath (string): path to image to save
  """

  df = get_measurements(measurements, station, time_range)

  df.plot(x = "time", y = [measurement.value for measurement in measurements])

  plt.ylabel(ylabel_name)
  plt.xlabel("Zeit t in [YY:MM:DD hh:mm]")

  if showPlot:
    plt.show()
  else:
    plt.savefig(imagePath, bbox_inches='tight')

def generate_plot_colMatrix(measurements : list(tuple((Measurement, tuple((str, str, str))))), station : str, time_range, showPlot = False, imagePath = None):
  """
  create splines aligned vertically

  Parameters:
  measurements (list(tuple(Measurement, tuple(string, string, string)))): select measurements from Measurement and specify name, formula sign and unit [list(tuple(Measurement.air_temp, tuple(Temperatur, T, °C)), ...)]
  station (string): station name
  time_range (string or tuple of dateTime): timerange as string -> now to specific time in the past [1d, 2w, 5m...], timerage as tuple -> specific time in the pas to specific time in the past [tuple(dateTime, dateTime)]
  showPlot (bool -> default: False): for debugging -> True: instead of creating an image, plot it directli
  imagePath (string): path to image to save
  """

  if len(measurements) <= 1:
    raise Exception("Es müssen mindestens 2 measurements angegeben werden!")

  df = get_measurements([measurement[0] for measurement in measurements], station, time_range)

  fig, axs = plt.subplots(len(measurements), 1)

  for i, measurement in enumerate(measurements):
    measurement_type = measurement[0]
    unit_name = measurement[1][0]
    unit_symbol = measurement[1][1]
    unit = measurement[1][2]

    axs[i].plot(df["time"].values, df[measurement_type.value].values)
    axs[i].set(xlabel = f"Zeit t in {_get_fmt(axs[i].xaxis)}", ylabel = f"{unit_name} {unit_symbol} in {unit}")
    axs[i].legend([unit_name])

  fig.autofmt_xdate()
  fig.tight_layout()

  if showPlot:
    plt.show()
  else:
    plt.savefig(imagePath, bbox_inches='tight')

def generate_plot_rowMatrix(measurements : list(tuple((Measurement, tuple((str, str, str))))), station : str, time_range, showPlot = False, imagePath = None):
  """
  create splines aligned horizontally

  Parameters:
  measurements (list(tuple(Measurement, tuple(string, string, string)))): select measurements from Measurement and specify name, formula sign and unit [list(tuple(Measurement.air_temp, tuple(Temperatur, T, °C)), ...)]
  station (string): station name
  time_range (string or tuple of dateTime): timerange as string -> now to specific time in the past [1d, 2w, 5m...], timerage as tuple -> specific time in the pas to specific time in the past [tuple(dateTime, dateTime)]
  showPlot (bool -> default: False): for debugging -> True: instead of creating an image, plot it directli
  imagePath (string): path to image to save
  """

  if len(measurements) <= 1:
    raise Exception("Es müssen mindestens 2 measurements angegeben werden!")

  df = get_measurements([measurement[0] for measurement in measurements], station, time_range)

  fig, axs = plt.subplots(1, len(measurements))

  for i, measurement in enumerate(measurements):
    measurement_type = measurement[0]
    unit_name = measurement[1][0]
    unit_symbol = measurement[1][1]
    unit = measurement[1][2]

    axs[i].plot(df["time"].values, df[measurement_type.value].values)
    axs[i].set(xlabel = f"Zeit t in {_get_fmt(axs[i].xaxis)}", ylabel = f"{unit_name} {unit_symbol} in {unit}")
    axs[i].legend([unit_name])

  fig.autofmt_xdate()
  fig.tight_layout()

  if showPlot:
    plt.show()
  else:
    plt.savefig(imagePath, bbox_inches='tight')

def generate_windRose(station : str, time_range, showPlot = False, imagePath = None):
  """
  create splines aligned horizontally

  Parameters:
  station (string): station name
  time_range (string or tuple of dateTime): timerange as string -> now to specific time in the past [1d, 2w, 5m...], timerage as tuple -> specific time in the pas to specific time in the past [tuple(dateTime, dateTime)]
  showPlot (bool -> default: False): for debugging -> True: instead of creating an image, plot it directli
  imagePath (string): path to image to save
  """


  df = get_measurements([Measurement.Wind_direction, Measurement.Wind_speed_avg_10min], station, time_range, timeFilling = False)

  ax = WindroseAxes.from_ax()
  ax.bar(df["wind_direction"].values, df["wind_speed_avg_10min"].values, normed = True, opening = 0.8, edgecolor = "white")
  ax.set_legend()

  plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment='right')

  if showPlot:
    plt.show()
  else:
    plt.savefig(imagePath, bbox_inches='tight')
  

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