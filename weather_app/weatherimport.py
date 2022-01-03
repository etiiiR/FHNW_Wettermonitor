from datetime import datetime, timedelta
import os
import logging
from signal import default_int_handler
from typing import List
from pandas.core.frame import DataFrame
import schedule
import numpy as np
import weatherdata as wd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import enum
import locale
from pathlib import Path
from windrose import WindroseAxes
import shutil
import pytz
import matplotlib
from matplotlib import dates as mpl_dates


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

def init():
  """
  connect to db, import historic data if not imported, import latest data (no periodic read)
  """
  global systemInitialized

  try:
    locale.setlocale(locale.LC_ALL, 'de_DE') # formats dates on plots correct
  except:
    pass # ignore
  matplotlib.rcParams['timezone'] = 'Europe/Zurich'

  wd.connect_db(config)

  root = str(Path(os.path.dirname(os.path.realpath(__file__))).parent)
  
  if (wd.try_import_csv_file(config, 'mythenquai',    root + "/Messwerte/messwerte_mythenquai_2007-2020.csv") and
      wd.try_import_csv_file(config, 'tiefenbrunnen', root + "/Messwerte/messwerte_tiefenbrunnen_2007-2020.csv")):
    wd.import_latest_data(config, periodic_read=False)
    logging.info("Database successfully initialized.")
    systemInitialized = True
    return systemInitialized
  else:
    raise Exception("Couldn't find csv files to import")
  


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

  if df is None:
    raise Exception("Measurements not available for this day!")

  if timeFilling:
    df = df.resample("10min").asfreq()#resample (zeitlücken mit NaN füllen)

  zurich = pytz.timezone('Europe/Zurich')
  df.index = df.index.map(lambda date: date.astimezone(zurich))

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

  zurich = pytz.timezone('Europe/Zurich')
  df.index = df.index.map(lambda date: date.astimezone(zurich))

  df["time"] = df.index
  df = df.reset_index(drop = True)

  return df

def get_measurements(measurements : list(Measurement), station : str, time_range, timeFilling = True, keepIndex = False):
  """
  get a specific entries in a specific time range 

  Parameters:
  measurements (list(Measurement)): select measurements from Measurement [list(Measurement.air_temp, ...)]
  station (string): station name
  time_range (string or tuple of dateTime): timerange as string -> now to specific time in the past [1d, 2w, 5m...], timerage as tuple -> specific time in the pas to specific time in the past [tuple(dateTime, dateTime)]
  timeFilling (bool -> default: True): fill up missing measurements with NaN
  refactorIndex (Boolean, default: True): set index as column "time" and resets if true
  """

  if type(time_range) is tuple:
    df = wd.get_multible_attr_entries(config, [measurement.value for measurement in measurements], station, start_time = time_range[0], stop_time = time_range[1])

  elif type(time_range) is str:
    df = wd.get_multible_attr_entries(config, [measurement.value for measurement in measurements], station, time_range)
  else:
    raise Exception("time_range has to be a string or a tuple")
  
  if timeFilling:
    df = df.resample("10min").asfreq()#resample (zeitlücken mit NaN füllen)

  zurich = pytz.timezone('Europe/Zurich')
  df.index = df.index.map(lambda date: date.astimezone(zurich))

  if not keepIndex:
    df["time"] = df.index
    df = df.reset_index(drop = True)

  return df

# generate plots 

# TODO maybe move this to a different file.

# Colors from https://coolors.co/264653-2a9d8f-e9c46a-f4a261-e76f51
colors = {
  "blue":      "#264653",
  "turquoise": "#2A9D8F",
  "yellow":    "#E9C46A",
  "orange":    "#F4A261",
  "red":       "#E76F51"
}

wind_measurements = [Measurement.Wind_speed_avg_10min,
                     Measurement.Wind_gust_max_10min,
                     Measurement.Wind_force_avg_10min,
                     Measurement.Wind_direction] # currently not plotted, since plotting is not that easy and therefore out of scope

def get_graph_location():
  return str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs"

def reset_graphs():
  # replace possible old graphs with a message
  static_images = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images"
  for station in ["tiefenbrunnen", "mythenquai"]:
      for category in ["wind", "temperature", "watertemp", "dewpoint", "waterlevel", "pressure"]:
          for type in ["today", "tomorrow", "history"]:
              shutil.copyfile(static_images+"/generating_plot.png", f"{get_graph_location()}/{station}_{category}_{type}.png")

def generate_wind_graph(station, type, time_range = None):
  if type != "history" and type != "today" and type != "tomorrow":
    raise Exception(f"Unknown type: {type}")
  
  if type == "tomorrow":
    wind = get_measurements(wind_measurements, station, time_range)
  else:
    wind = get_measurements(wind_measurements, station, "7d" if type == "history" else "1d")

  if type == "history":
    # aggregate window every 1 hour
    wind = wind.resample('H', on='time').agg(
      { Measurement.Wind_speed_avg_10min.value:'mean',
        Measurement.Wind_gust_max_10min .value:'max',
        Measurement.Wind_force_avg_10min.value:'median',
        Measurement.Wind_direction      .value:'median'})

    wind["time"] = wind.index
    wind = wind.reset_index(drop = True)

  fig, ax1 = plt.subplots(figsize=(12,5))

  # first y-Axis
  ax1.plot(wind['time'], wind[Measurement.Wind_speed_avg_10min.value], color=colors["blue"])
  ax1.plot(wind['time'], wind[Measurement.Wind_gust_max_10min .value], color=colors["turquoise"])
  # expand the limits to make sure y=0, y=10 are on the axis
  bottom, top = ax1.get_ylim()
  ax1.set_ylim(bottom if bottom < 0 else 0, top if top > 10 else 10)
  ax1.set_ylabel('m/s')
  ax1.legend(["Durchschnittliche Windgeschwindigkeit", "Maximale Geschwindigkeit Windböen"], loc="upper left")

  # second y-Axis
  ax2 = ax1.twinx()
  ax2.plot(wind['time'], wind[Measurement.Wind_force_avg_10min.value], color=colors["yellow"], alpha=0.75)
  # expand the limits to make sure y=0, y=7 are on the axis
  bottom, top = ax2.get_ylim()
  ax2.set_ylim(bottom if bottom < 0 else 0, top if top > 7 else 7)
  ax2.set_ylabel('Beaufortskala')
  ax2.legend(["Windstärke"], loc="upper right")

  # x-Axis
  ax1.set_xlabel('Zeit')
  if type == "history":
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%A, %d %b'))
  else:
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

  for label in ax1.get_xticklabels(which='major'):
      label.set(rotation=30, horizontalalignment='right')

  fig.tight_layout()
  fig.savefig(get_graph_location() + f"/{station}_wind_{type}.png", bbox_inches='tight')
  plt.close(fig)


def generate_today_graphs():
  logging.info("#generate_today_graphs()")
  # wind
  generate_wind_graph("tiefenbrunnen", "today")
  generate_wind_graph("mythenquai", "today")
  ############################################# todays graphs #############################################

  ## get data
  mythenquai_df = get_measurements([Measurement.Air_temp, 
                                                      Measurement.Humidity,
                                                      Measurement.Water_temp,
                                                      Measurement.Water_level,
                                                      Measurement.Dew_point,
                                                      Measurement.Pressure],
                                    station = "mythenquai",
                                    time_range = "1d")

  tiefenbrunnen_df = get_measurements([Measurement.Air_temp, 
                                                      Measurement.Humidity,
                                                      Measurement.Water_temp,
                                                      Measurement.Water_level,
                                                      Measurement.Dew_point,
                                                      Measurement.Pressure],
                                        station = "tiefenbrunnen",
                                        time_range = "1d")

  ## convert to arrays
  timestamps_mythenquai = np.array(mythenquai_df["time"].fillna(value = 0))
  temperatur_mythenquai = np.array(mythenquai_df["air_temperature"].fillna(value = 0))
  dewpoint_mythenquai = np.array(mythenquai_df["dew_point"].fillna(value = 0))

  timestamps_tiefenbrunnen = np.array(tiefenbrunnen_df["time"].fillna(value = 0))
  temperatur_tiefenbrunnen = np.array(tiefenbrunnen_df["air_temperature"].fillna(value = 0))
  dewpoint_tiefenbrunnen = np.array(tiefenbrunnen_df["dew_point"].fillna(value = 0))
  watertemp_tiefenbrunnen = np.array(tiefenbrunnen_df["water_temperature"].fillna(value = 0))
  waterlevel_tiefenbrunnen = np.array(tiefenbrunnen_df["water_level"].fillna(value = 0))
  pressure_tiefenbrunnen = np.array(tiefenbrunnen_df["barometric_pressure_qfe"].fillna(value = 0))

  ## plots mythenquai (No watertemperature, waterlevel and pressure, because no data)
  generate_simple_plot(station = "mythenquai",
                                      measurements_array = temperatur_mythenquai,
                                      timestamps = timestamps_mythenquai,
                                      unit_symbols = ["Temperatur", "T", "°C"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/mythenquai_temperature_today.png",
                                      dateformatter = "%d %b %H:%M",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )

  generate_simple_plot(station = "mythenquai",
                                      measurements_array = dewpoint_mythenquai,
                                      timestamps = timestamps_mythenquai,
                                      unit_symbols = ["Taupunkt", "T", "°C"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/mythenquai_dewpoint_today.png",
                                      dateformatter = "%d %b %H:%M",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )

  ## plots tiefenbrunnen

  generate_simple_plot(station = "tiefenbrunnen",
                                      measurements_array = temperatur_tiefenbrunnen,
                                      timestamps = timestamps_tiefenbrunnen,
                                      unit_symbols = ["Temperatur", "T", "°C"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/tiefenbrunnen_temperature_today.png",
                                      dateformatter = "%d %b %H:%M",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )

  generate_simple_plot(station = "tiefenbrunnen",
                                      measurements_array = dewpoint_tiefenbrunnen,
                                      timestamps = timestamps_tiefenbrunnen,
                                      unit_symbols = ["Taupunkt", "T", "°C"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/tiefenbrunnen_dewpoint_today.png",
                                      dateformatter = "%d %b %H:%M",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )

  generate_simple_plot(station = "tiefenbrunnen",
                                      measurements_array = waterlevel_tiefenbrunnen,
                                      timestamps = timestamps_tiefenbrunnen,
                                      unit_symbols = ["Wasserstand", "", "m.ü.m"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/tiefenbrunnen_waterlevel_today.png",
                                      dateformatter = "%d %b %H:%M",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )

  generate_simple_plot(station = "tiefenbrunnen",
                                      measurements_array = watertemp_tiefenbrunnen,
                                      timestamps = timestamps_tiefenbrunnen,
                                      unit_symbols = ["Wassertemperatur", "T", "°C"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/tiefenbrunnen_watertemp_today.png",
                                      dateformatter = "%d %b %H:%M",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )

  generate_simple_plot(station = "tiefenbrunnen",
                                      measurements_array = pressure_tiefenbrunnen,
                                      timestamps = timestamps_tiefenbrunnen,
                                      unit_symbols = ["Luftdruck", "P", "Pa"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/tiefenbrunnen_pressure_today.png",
                                      ylim = (900, 1000),
                                      dateformatter = "%d %b %H:%M",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )



  return schedule.CancelJob

def generate_last_7_days_graphs():
  logging.info("#generate_last_7_days_graphs()")
  # wind
  generate_wind_graph("tiefenbrunnen", "history")
  generate_wind_graph("mythenquai", "history")
  
  ############################################# this week graphs #############################################
  ## get data
  mythenquai_df = get_measurements([Measurement.Air_temp, 
                                                      Measurement.Humidity,
                                                      Measurement.Water_temp,
                                                      Measurement.Water_level,
                                                      Measurement.Dew_point,
                                                      Measurement.Pressure],
                                      station = "mythenquai",
                                      time_range = "7d")

  tiefenbrunnen_df = get_measurements([Measurement.Air_temp, 
                                                      Measurement.Humidity,
                                                      Measurement.Water_temp,
                                                      Measurement.Water_level,
                                                      Measurement.Dew_point,
                                                      Measurement.Pressure],
                                          station = "tiefenbrunnen",
                                          time_range = "7d")

  ## convert to arrays
  timestamps_mythenquai = np.array(mythenquai_df["time"].fillna(value = 0))
  temperatur_mythenquai = np.array(mythenquai_df["air_temperature"].fillna(value = 0))
  dewpoint_mythenquai = np.array(mythenquai_df["dew_point"].fillna(value = 0))

  timestamps_tiefenbrunnen = np.array(tiefenbrunnen_df["time"].fillna(value = 0))
  temperatur_tiefenbrunnen = np.array(tiefenbrunnen_df["air_temperature"].fillna(value = 0))
  dewpoint_tiefenbrunnen = np.array(tiefenbrunnen_df["dew_point"].fillna(value = 0))
  watertemp_tiefenbrunnen = np.array(tiefenbrunnen_df["water_temperature"].fillna(value = 0))
  waterlevel_tiefenbrunnen = np.array(tiefenbrunnen_df["water_level"].fillna(value = 0))
  pressure_tiefenbrunnen = np.array(tiefenbrunnen_df["barometric_pressure_qfe"].fillna(value = 0))



  ## plots mythenquai (No watertemperature, waterlevel and pressure, because no data)
  generate_simple_plot(station = "mythenquai",
                                      measurements_array = temperatur_mythenquai,
                                      timestamps = timestamps_mythenquai,
                                      unit_symbols = ["Temperatur", "T", "°C"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/mythenquai_temperature_history.png",
                                      dateformatter = "%d %b",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )

  generate_simple_plot(station = "mythenquai",
                                      measurements_array = dewpoint_mythenquai,
                                      timestamps = timestamps_mythenquai,
                                      unit_symbols = ["Taupunkt", "T", "°C"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/mythenquai_dewpoint_history.png",
                                      dateformatter = "%d %b",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )

  ## plots tiefenbrunnen

  generate_simple_plot(station = "tiefenbrunnen",
                                      measurements_array = temperatur_tiefenbrunnen,
                                      timestamps = timestamps_tiefenbrunnen,
                                      unit_symbols = ["Temperatur", "T", "°C"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/tiefenbrunnen_temperature_history.png",
                                      dateformatter = "%d %b",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )

  generate_simple_plot(station = "tiefenbrunnen",
                                      measurements_array = dewpoint_tiefenbrunnen,
                                      timestamps = timestamps_tiefenbrunnen,
                                      unit_symbols = ["Taupunkt", "T", "°C"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/tiefenbrunnen_dewpoint_history.png",
                                      dateformatter = "%d %b",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )

  generate_simple_plot(station = "tiefenbrunnen",
                                      measurements_array = waterlevel_tiefenbrunnen,
                                      timestamps = timestamps_tiefenbrunnen,
                                      unit_symbols = ["Wasserstand", "", "m.ü.m"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/tiefenbrunnen_waterlevel_history.png",
                                      dateformatter = "%d %b",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )

  generate_simple_plot(station = "tiefenbrunnen",
                                      measurements_array = watertemp_tiefenbrunnen,
                                      timestamps = timestamps_tiefenbrunnen,
                                      unit_symbols = ["Wassertemperatur", "T", "°C"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/tiefenbrunnen_watertemp_history.png",
                                      dateformatter = "%d %b",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )

  generate_simple_plot(station = "tiefenbrunnen",
                                      measurements_array = pressure_tiefenbrunnen,
                                      timestamps = timestamps_tiefenbrunnen,
                                      unit_symbols = ["Luftdruck", "P", "Pa"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/tiefenbrunnen_pressure_history.png",
                                      ylim = (900, 1000),
                                      dateformatter = "%d %b",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )


def generate_prediction_graphs():
  logging.info("#generate_prediction_graphs()")
  date = datetime.now(pytz.utc) + timedelta(days=-1)
  ## tiefenbrunnen
  forecast_date, df = forecast_of_tomorrow("tiefenbrunnen", date)
  logging.info(f"nearest date to {date} for tiefenbrunnen: {forecast_date}")

  # wind
  start_date = forecast_date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=pytz.timezone('Europe/Zurich'))
  end_date = start_date + timedelta(days=1)
  time_range = (start_date.astimezone(pytz.utc), end_date.astimezone(pytz.utc))
  
  generate_wind_graph("tiefenbrunnen", "tomorrow", time_range)

  tiefenbrunnen_df = get_measurements([
                                        Measurement.Air_temp, 
                                        Measurement.Humidity,
                                        Measurement.Water_temp,
                                        Measurement.Water_level,
                                        Measurement.Dew_point,
                                        Measurement.Pressure
                                      ],
                                      station = "tiefenbrunnen",
                                      time_range = time_range)

  timestamps_tiefenbrunnen = np.array(tiefenbrunnen_df["time"].fillna(value = 0))
  temperatur_tiefenbrunnen = np.array(tiefenbrunnen_df["air_temperature"].fillna(value = 0))
  dewpoint_tiefenbrunnen = np.array(tiefenbrunnen_df["dew_point"].fillna(value = 0))
  watertemp_tiefenbrunnen = np.array(tiefenbrunnen_df["water_temperature"].fillna(value = 0))
  waterlevel_tiefenbrunnen = np.array(tiefenbrunnen_df["water_level"].fillna(value = 0))
  pressure_tiefenbrunnen = np.array(tiefenbrunnen_df["barometric_pressure_qfe"].fillna(value = 0))

  generate_simple_plot(station = "tiefenbrunnen",
                                      measurements_array = temperatur_tiefenbrunnen,
                                      timestamps = timestamps_tiefenbrunnen,
                                      unit_symbols = ["Temperatur", "T", "°C"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/tiefenbrunnen_temperature_tomorrow.png",
                                      dateformatter = "%H:%M",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )

  generate_simple_plot(station = "tiefenbrunnen",
                                      measurements_array = dewpoint_tiefenbrunnen,
                                      timestamps = timestamps_tiefenbrunnen,
                                      unit_symbols = ["Taupunkt", "T", "°C"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/tiefenbrunnen_dewpoint_tomorrow.png",
                                      dateformatter = "%H:%M",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )

  generate_simple_plot(station = "tiefenbrunnen",
                                      measurements_array = waterlevel_tiefenbrunnen,
                                      timestamps = timestamps_tiefenbrunnen,
                                      unit_symbols = ["Wasserstand", "", "m.ü.m"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/tiefenbrunnen_waterlevel_tomorrow.png",
                                      dateformatter = "%H:%M",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )

  generate_simple_plot(station = "tiefenbrunnen",
                                      measurements_array = watertemp_tiefenbrunnen,
                                      timestamps = timestamps_tiefenbrunnen,
                                      unit_symbols = ["Wassertemperatur", "T", "°C"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/tiefenbrunnen_watertemp_tomorrow.png",
                                      dateformatter = "%H:%M",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )

  generate_simple_plot(station = "tiefenbrunnen",
                                      measurements_array = pressure_tiefenbrunnen,
                                      timestamps = timestamps_tiefenbrunnen,
                                      unit_symbols = ["Luftdruck", "P", "Pa"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/tiefenbrunnen_pressure_tomorrow.png",
                                      ylim = (900, 1000),
                                      dateformatter = "%H:%M",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )

  ## mythenquai
  forecast_date, df = forecast_of_tomorrow("mythenquai", date)
  logging.info(f"nearest date to {date} for mythenquai: {forecast_date}")

  # wind
  start_date = forecast_date.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=pytz.timezone('Europe/Zurich'))
  end_date = start_date + timedelta(days=1)
  time_range = (start_date.astimezone(pytz.utc), end_date.astimezone(pytz.utc))
  generate_wind_graph("mythenquai", "tomorrow", time_range)
  
  mythenquai_df = get_measurements([Measurement.Air_temp, 
                                                      Measurement.Humidity,
                                                      Measurement.Water_temp,
                                                      Measurement.Water_level,
                                                      Measurement.Dew_point,
                                                      Measurement.Pressure],
                                    station = "mythenquai",
                                    time_range = time_range)

  timestamps_mythenquai = np.array(mythenquai_df["time"].fillna(value = 0))
  temperatur_mythenquai = np.array(mythenquai_df["air_temperature"].fillna(value = 0))
  dewpoint_mythenquai = np.array(mythenquai_df["dew_point"].fillna(value = 0))

  ## plots mythenquai (No watertemperature, waterlevel and pressure, because no data)
  generate_simple_plot(station = "mythenquai",
                                      measurements_array = temperatur_mythenquai,
                                      timestamps = timestamps_mythenquai,
                                      unit_symbols = ["Temperatur", "T", "°C"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/mythenquai_temperature_tomorrow.png",
                                      dateformatter = "%H:%M",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )

  generate_simple_plot(station = "mythenquai",
                                      measurements_array = dewpoint_mythenquai,
                                      timestamps = timestamps_mythenquai,
                                      unit_symbols = ["Taupunkt", "T", "°C"],
                                      imagepath = str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/static/Images/graphs/mythenquai_dewpoint_tomorrow.png",
                                      dateformatter = "%H:%M",
                                      showMin = True,
                                      showMean = True,
                                      showMax = True
                                      )


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

def generate_plot_colMatrix(measurements : list(tuple((Measurement, tuple((str, str, str))))), station : str, time_range, showPlot = False, imagePath = None, showMin = True, showMean = True, showMax = True, title = str, showLatest = True):
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

    # Plot values
    axs[i].plot(df["time"].values, df[measurement_type.value].values, label = f"{unit_name}")

    # Plot mean as a line
    if showMean:
      mean_measurements = df[measurement_type.value][np.logical_not(np.isnan(df[measurement_type.value]))].values.mean()        #calculate mean without na
      axs[i].axhline(mean_measurements, color = "r", label = f"Mean: {round(mean_measurements, 1)}{unit}", linewidth = 1)                  #plot mean line

    # get offsets for positioning annotation text for min/max
    if unit_name == "Temperatur":
      offset_annotation = 5
    elif unit_name == "Luftfeuchtigkeit":
      offset_annotation = 10

    # Mark max in red
    if showMax:
     
      ymax = 0    
      xpos = 0    #index xmax
      xmax = 0

      for e in range(0, len(df[measurement_type.value].values)):    #Loop through column with index
        if df[measurement_type.value].values[e] > ymax:             #Find max
          ymax = df[measurement_type.value].values[e]               
          xpos = e                                                  #Get Index of ymax

      xmax = df["time"][xpos]                                #Get xmax with index of ymax

      axs[i].scatter(xmax, ymax, color = "red", s = 15)                        #Plot max point
      axs[i].annotate(f"Max: {ymax}{unit}", xy=(xmax, ymax), xytext=(xmax, ymax + offset_annotation))     #Plot label

    # Mark min in red
    if showMin:

      ymin = 1000    
      xpos = 0    #index xmin
      xmin = 0

      for e in range(0, len(df[measurement_type.value].values)):    #Loop through column with index
        if df[measurement_type.value].values[e] < ymin:             #Find min
          ymin = df[measurement_type.value].values[e]               
          xpos = e                                                  #Get Index of ymin

      xmin = df["time"][xpos]                                 #Get xmin with index of ymin

      axs[i].scatter(xmin, ymin, color = "red", s = 15)                        #Plot min point
      axs[i].annotate(f"Min: {ymin}{unit}", xy=(xmin, ymin), xytext=(xmin, ymin - offset_annotation))      #Plot label

    # Mark latest value
    if showLatest:
      axs[i].scatter(df["time"].values[-1], df[measurement_type.value].values[-1], color = "green", s = 15, label = f"Aktuell: {df[measurement_type.value].values[-1]}{unit}") 


    #Titles and labels
    axs[i].set(xlabel = f"Zeit t in {_get_fmt(axs[i].xaxis)}", ylabel = f"{unit_name} {unit_symbol} in {unit}")
    axs[i].legend(loc = "center left",  bbox_to_anchor=(1, 0.5))
    axs[i].title.set_text(f"{title}, {unit_name} in {unit}")
    if unit_name == "Temperatur":
      axs[i].set_ylim(-20, 50)
    elif unit_name == "Luftfeuchtigkeit":
      axs[i].set_ylim(0, 125)
    left, right = axs[i].get_xlim()
    axs[i].set_xlim(left, right + 0.05)

  # Format layout
  fig.autofmt_xdate()
  fig.tight_layout()
  fig.set_figwidth(10)

  # set date formatter
  if title == "Tagesplot":
    date_formatter = mpl_dates.DateFormatter("%d %b %H:%M")
    for ax in axs:
      ax.xaxis.set_major_formatter(date_formatter)


  if showPlot:
    plt.show()
  else:
    plt.savefig(imagePath, bbox_inches='tight')

## get max value and position in df
def get_ymax(df_col = np.array):
    temp_df = df_col[df_col != np.array(None)]
    xpos_max = 0
    ymax = 0
    for i in range(len(temp_df)):
        if temp_df[i] > ymax:
            ymax = temp_df[i]
            xpos_max = i
    return [ymax, xpos_max]

## get min value and position in df
def get_ymin(df_col = np.array):
    temp_df = df_col[df_col != np.array(None)]
    xpos_min = 0
    ymin = 100000000
    for i in range(len(temp_df)):
        if temp_df[i] < ymin:
            ymin = temp_df[i]
            xpos_min = i
    return [ymin, xpos_min]

def generate_simple_plot(station, 
                        measurements_array,
                        timestamps,
                        unit_symbols = List, 
                        imagepath = str,
                        dateformatter = str, 
                        showMin = True, 
                        showMean = True, 
                        showMax = True,
                        ylim: list = None
                        ):
  """
  create simple plot

  Parameters:
  station (str) 
  measurements (numpy array) array with measurements for the plot
  timestamps (numpy array) array with measurements for the plot needs to have the same lenght as measurements
  unit_symbols (List(Name, Unit, Symbol)) z.B: für Temperatur (Temperatur, T, °C)
  imagepath (str) imagepath where png is saved to
  xlim (List(left, right)) X-Axis limitter
  ylim (List(Top, Bottom)) Y-Axis limitter
  dateformatter (str) formatter for timestamps
  showMin (Bool --> Default = True) plot red point and value for Min Value
  showMean (Bool --> Default = True) plot red horizontal line and value for Mean Value
  showMax (Bool --> Default = True) plot red point and value for Max Value
  """
  ## Exception for lack of values
  if len(measurements_array) <= 1:
    raise Exception("Es müssen mindestens 2 measurements angegeben werden!")
  
  ## generate axs and figure
  fig, ax = plt.subplots()

  ## statistics / annotations
  if showMin:
    ymin, xpos_min = get_ymin(np.array(measurements_array))
    ax.scatter(x = timestamps[xpos_min], 
                y = ymin, 
                color = "red", 
                label = f"Min: {round(ymin, 2)}{unit_symbols[2]}")

  if showMean:
    ymean = np.nanmean(measurements_array)
    ax.axhline(y = ymean, 
                color = "red", 
                label = f"Mean: {round(ymean, 2)}{unit_symbols[2]}")

  if showMax:
    ymax, xpos_max = get_ymax(np.array(measurements_array))
    ax.scatter(x = timestamps[xpos_max], 
                y = ymax, 
                color = "red", 
                label = f"Max: {round(ymax, 2)}{unit_symbols[2]}")

  ## plot axis
  ax.plot(timestamps, measurements_array, label = f"Aktueller Wert: {round(measurements_array[-1], 2)}{unit_symbols[2]}")

  ## set axis attributes
  ax.legend(loc = "center left",  bbox_to_anchor=(1.02, 0.8), fontsize = 6)
  ax.grid()
  ax.set_title(f"Number of measuremens: {len(np.array(measurements_array))}", fontsize = 6)
  ax.set_ylabel(f"{unit_symbols[0]} {unit_symbols[1]} in {unit_symbols[2]}", fontsize = 8)
  ax.set_xlabel(f"Zeitachse", fontsize = 6)
  if ylim != None:
    ax.set_ylim(ylim[0], ylim[1])
  ax.xaxis.set_major_formatter(mpl_dates.DateFormatter(dateformatter))

 ## set figure attributes
  fig.set_figheight(3)
  fig.set_figwidth(6)
  fig.suptitle(f"Wetterstation {station}: {unit_symbols[0]} {unit_symbols[1]} in {unit_symbols[2]}", fontsize = 6, fontweight = "bold")
  fig.autofmt_xdate()
  fig.tight_layout()

  #set ticksize 
  plt.xticks(fontsize = 6)

  # save plot
  plt.savefig(imagepath, bbox_inches='tight', dpi = 500)
  plt.close(fig)


def generate_plot_rowMatrix(measurements : list(tuple((Measurement, tuple((str, str, str))))), station : str, time_range, showPlot = False, imagePath = None, showMean = False, showMax = False, showMin = False, title = str ):
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


def wind_direction_to_text(wind_direction):
    return {
        0:  "Norden",
        1:  "Nordnordosten",
        2:  "Nordosten",
        3:  "Ostnordosten",
        4:  "Osten",
        5:  "Ostsüdosten",
        6:  "Südosten",
        7:  "Südsüdosten",
        8:  "Süden",
        9:  "Südsüdwesten",
        10: "Südwesten",
        11: "Westsüdwesten",
        12: "Westen",
        13: "Westnordwesten",
        14: "Nordwesten",
        15: "Nordnordwesten",
        16: "Norden"
    }.get((wind_direction + 11.25) // 22.5, "-")


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

#forecast
def construct_window_vector_old(df: pd.DataFrame, lim_weight: list, normalize_to_plusMinus = 1):
  """
  constructs a vector in dependence of the dataframe

  Parameters:
  df (pandas.DataFrame)
  lim_weight (list(tuple(min, max, weight_factor))): min -> vektorcomponent = 0, max -> vektorcomponent = 1, weight_factor ->  vektorcomponent * x; minMax for the difference between 10min Steps
  """

  if df.empty:
    raise ValueError("Empty dataframe received")

  df = df.dropna() #remove measurements with missing values
  df = df.reset_index(drop = True) #delete index
  vector = np.empty(len(df.columns)) #create an empty vector with the length of the dataframe

  if df.empty:
    raise ValueError("Dataframe empty after deleting observations containing NA")

  for i_row_new in range(1, len(df.index)): #iterate over observations
    row_old = df.iloc[[i_row_new - 1]].reset_index(drop = True) #reset index of rows
    row_new = df.iloc[[i_row_new]].reset_index(drop = True) #reset index of rows
    
    temp_vector = np.empty(len(df.columns)) #create temporary vector
    for index_item in range(0, len(row_new.columns)): #iterate over attributes

      item = row_new.iat[0, index_item] - row_old.iat[0, index_item] #calculate difference
      
      #extract limitations
      min = lim_weight[index_item][0]
      max = lim_weight[index_item][1]
      weight = lim_weight[index_item][2]

      #range check
      if item < min:
        temp_vector[index_item] = -1 * weight
        logging.warning(f"Warning: Value: {item} in column: {df.columns[index_item]} lower than allowed... set to ", -1 * weight)

      elif item > max:
        temp_vector[index_item] = weight
        logging.warning(f"Warning: Value: {item} in column: {df.columns[index_item]} higher than allowed... set to", weight)

      else:
        temp_vector[index_item] = (((normalize_to_plusMinus * 2 * item) / (max - min)) + ((-1 * normalize_to_plusMinus) - ((normalize_to_plusMinus * 2 * min) / (max - min)))) * weight #linearisierung für: item == max -> 1, item == min -> -1, zwischenresultat * weight -> resultat

    vector = np.add(vector, temp_vector)

  return np.divide(vector, len(df.index) - 1)

def construct_window_vector(df: pd.DataFrame, lim_weight: list, normalize_to_plusMinus = 1):
  """
  constructs a vector in dependence of the dataframe

  Parameters:
  df (pandas.DataFrame)
  lim_weight (list(tuple(min, max, weight_factor))): min -> vektorcomponent = 0, max -> vektorcomponent = 1, weight_factor ->  vektorcomponent * x; minMax for the difference between 10min Steps
  """

  if df.empty:
    raise ValueError("Empty dataframe received")

  ##########################df = df.dropna() #remove measurements with missing values (not needed anymore)
  vector = np.empty(len(df.columns)) #create an empty vector with the length of the dataframe

  if df.empty:
    raise ValueError("Dataframe empty after deleting observations containing NA")

  df = df.sort_index() #sortiere nach datum -> top = oldest, bottom = newest

  if type(df.index[-1]) != pd.Timestamp or type(df.index[0]) != pd.Timestamp:
    raise Exception("Index has wrong format!!!")

  vector = np.empty(len(df.columns)) #create an empty vector with the length of the dataframe
  for index_item in range(0, len(df.columns)): #iterate over attributes
      column = df.iloc[:, index_item] #get column and reset index

      first_valid_index = column.first_valid_index()
      last_valid_index = column.last_valid_index()

      if (first_valid_index is None) or (last_valid_index is None):
        raise ValueError("An attribute of this window doesn't contain data!")
      
      oldest_valid_value = column.loc[first_valid_index] #get first (oldest measurement) element of column with a valid value (not nan)
      newest_valid_value = column.loc[last_valid_index] #get last (newest measurement) element of column with a valid value (not nan)

      num_of_10min_steps =  int((last_valid_index - first_valid_index).total_seconds() / (10 * 60)) #calculate number of 10 min steps between measurements

      if num_of_10min_steps == 0: #if window only containing one observation
        raise ValueError("An attribute of this window only contains one datapoint!")

      #extract limitations
      min = lim_weight[index_item][0] * num_of_10min_steps
      max = lim_weight[index_item][1] * num_of_10min_steps
      weight = lim_weight[index_item][2]


      delta = newest_valid_value - oldest_valid_value #calculate difference
      
      #range check
      if delta < min:
        vector[index_item] = -1 * weight
        logging.warning(f"Warning: Value: {delta} in column: {df.columns[index_item]} lower than allowed... set to ", -1 * weight)

      elif delta > max:
        vector[index_item] = weight
        logging.warning(f"Warning: Value: {delta} in column: {df.columns[index_item]} higher than allowed... set to", weight)

      else:
        vector[index_item] = (((normalize_to_plusMinus * 2 * delta) / (max - min)) + ((-1 * normalize_to_plusMinus) - ((normalize_to_plusMinus * 2 * min) / (max - min)))) * weight #linearisierung für: item == max -> 1, item == min -> -1, zwischenresultat * weight -> resultat

  return vector

def get_mean_of_day(df, measurements_converted, vector_lim_weight):
  """
  calculates mean of day in a normalized way

  parameters:
  df (pandas Dataframe): dataframe of day
  measurements_converted (list(Measurement)): list of all measurements (converted to value of measurements)
  vector_lim_weight (list(tuple)): specify min, max and weight for each measurement
  """
  #calculate mean of measurements
  mean_of_measurements_dateSearchFor_normalized_list = []
  for i, measurement in enumerate(measurements_converted):
    range0 = vector_lim_weight[0][1] - vector_lim_weight[0][0]
    rangei = vector_lim_weight[i][1] - vector_lim_weight[i][0]

    weight = (range0 / rangei) * vector_lim_weight[i][2] #calculate weight in dependence to first measurement and measurement weight

    mean_of_measurements_dateSearchFor_normalized_list.append(np.nanmean(df[measurement]) * weight)

    pythoagoras = 0
    for mean_measurement in mean_of_measurements_dateSearchFor_normalized_list:
      pythoagoras += mean_measurement ** 2

    pythoagoras = np.sqrt(pythoagoras)

  return pythoagoras


def nearest_neighbour(station: str, date_searchBestRecord: datetime, timeArea_months: int, day_window_size = '4h', measurements = [Measurement.Air_temp, Measurement.Dew_point], vector_lim_weight = [(-10, 10, 1), (-10, 10, 0.1)], mean_in_range_percent = 0):
  """
  Get date of a day which is the closest to date_searchBestRecord by cos simularity and mean difference
  
  Parameters:
  station (string): station
  date_searchBestRecord (datetime): output of this function is searching for a similar day as date_searchBestRecord
  timeArea_months (int): window time bewteen (date_searchBestRecord - timeArea_months, date_searchBestRecord + timeArea_months) every year 
  measurements (list(Measurement)): measurements to include. Example: [Measurement.Air_temp, Measurement.Dew_point]
  vector_lim_weight (list(tuple)): specify min, max and weight for each measurement. Example for measurement Air_temp: (-10, 10, 1) min -> -10, max -> 10, weight = 1: if value = -10 -> X_airTemp = -1 * weight; value = 10 -> X_airTemp = 1 * weight; 
  mean_in_range_percent (int (0 to 100)): this parameter specifies, how many percents of the mean difference range is allowed. Example: mean_in_range_percent -> min meanDifference is 2 and max meanDifference is 10 and mean_in_range_percent is 10% -> difference of historical day to  date_searchBestRecord has to be equal or less as (2 + ((10 - 2) / 100 * 10)) = 2.8
  """

  if len(measurements) != len(vector_lim_weight):
    raise Exception("Each measurement needs a lim_weight tuple")

  if len(measurements) <= 1:
    raise Exception("Its not possible to calculate a cosinus simularity in one dimension... Please add more measurements!")

  logging.info("Start nearest neighbour calculation...")

  measurements_converted = [measurement.value for measurement in measurements] #convert measurements

  tables_hist =  wd.get_multible_attr_entries_yearlyWindow(config, measurements_converted, station, date_searchBestRecord, timeArea_months=timeArea_months) #get time windows (missing measurements are not filled with None)
  table_hist = pd.concat(tables_hist) #concat 
  table_hist["time"] = [datetime(index.year, index.month, index.day) for index in table_hist.index] #add time column containing only year month and day
  tables_groupedByDay_hist = table_hist.groupby(table_hist['time']) #group by day

  #create vector list of date_searchBestRecord
  dateOnly = datetime(date_searchBestRecord.year, date_searchBestRecord.month, date_searchBestRecord.day) #get date of date_searchBestRecord only
  table_dateSearchFor = get_measurements(measurements, station, (dateOnly, datetime(dateOnly.year, dateOnly.month, dateOnly.day, hour = 23, minute = 59, second = 59)), timeFilling=False, keepIndex = True)#get measurements from date: date_searchBestRecord (whole day) 
  table_dateSearchFor["time"] = [pd.to_datetime(index, format="%H:%M:%S", errors='ignore') for index in table_dateSearchFor.index] #override time and store time only
  time_dateSearchFor_windowed = table_dateSearchFor.groupby([pd.Grouper(key = 'time', freq=day_window_size, origin = "start_day")]) #group by an interval of 4h (origin = "start_Day" -> first group starts at midnight and not with first value)

  #calculate mean of all measurements
  mean_of_dateSearchFor_norm = get_mean_of_day(table_dateSearchFor, measurements_converted, vector_lim_weight)

  #calculate max length of groups of a day with all values
  date_range = pd.date_range("2018-01-01", periods=144, freq="10min")
  date_range_df_windowed = pd.DataFrame(date_range, columns = ["time"]).groupby([pd.Grouper(key = 'time', freq=day_window_size, origin = "start_day")], as_index = False) 
  max_group_length = len(date_range_df_windowed)

  vector_today_windowed_dict = {}
  for index, table in time_dateSearchFor_windowed: #calculate vector/vector_length of each window
    try:
      vector = construct_window_vector(table.drop(["time"], axis = 1), vector_lim_weight) #remove time attribute and construct vector of day
      len_vector= np.sqrt(sum([vector[i] ** 2 for i in range(0, len(vector))])) #calculate length of vectorToday 
      vector_today_windowed_dict[index.strftime("%H:%M:%S")] = (vector, len_vector) #append vector and length to dict
    except ValueError as ex:
      logging.error("Warning!!! the day we are searching for has empty values... number of window will be shortened -> this can lead to more unprecisely predictions")
    
  if not vector_today_windowed_dict:
    raise Exception("The day we are searching for cannot be vectorized... stopped searching!")

  #calculate min mean difference of measurements between historical date and searchdate
  best_meanDifference = None
  worst_meanDifference = None
  diff_means = []
  for index, table_hist_day in tables_groupedByDay_hist:
    time =  index

    if datetime(time.year, time.month, time.day) == dateOnly: #reference day found
      #logging.info("reference day found:", datetime(time.year, time.month, time.day))
      continue


    diffMean_of_hist_day_norm = abs(get_mean_of_day(table_hist_day, measurements_converted, vector_lim_weight) - mean_of_dateSearchFor_norm)
    diff_means.append(diffMean_of_hist_day_norm) #add value


    if not best_meanDifference: #if no value stored
      best_meanDifference = diffMean_of_hist_day_norm

    elif diffMean_of_hist_day_norm < best_meanDifference:
      best_meanDifference = diffMean_of_hist_day_norm

    if not worst_meanDifference: #if no value stored
      worst_meanDifference = diffMean_of_hist_day_norm

    elif diffMean_of_hist_day_norm > best_meanDifference:
      worst_meanDifference = diffMean_of_hist_day_norm
  
  meanDifference_range = worst_meanDifference - best_meanDifference #calculate range
  min_meanDifference = ((meanDifference_range / 100) * mean_in_range_percent) + best_meanDifference #mean of historical date has to be in range of meanDifference_range / 10 
  

  #progress counter
  num_of_values_in_range = 0
  for diffMean in diff_means:
    if diffMean <= min_meanDifference:
      num_of_values_in_range += 1

  progress_steps = [round(steps, 0) for steps in np.arange(0, num_of_values_in_range, num_of_values_in_range / 10)]

  #search for best cos
  best_date = dateOnly
  bestCos = np.pi / 2
  progress_counter = 0
  for index, table_hist_day in tables_groupedByDay_hist: #iterate over days
    time =  index

    table_day = table_hist_day #rename

    if datetime(time.year, time.month, time.day) == dateOnly: #reference day found
      #logging.info("reference day found:", datetime(time.year, time.month, time.day))
      continue
    


    ####if mean difference is in range####
    mean_of_hist_day_norm = get_mean_of_day(table_day, measurements_converted, vector_lim_weight) #get mean of hist_Day measurements

    #continue if mean difference is not in allowed range
    if abs(mean_of_hist_day_norm - mean_of_dateSearchFor_norm) > min_meanDifference:
      continue

    progress_counter += 1



    ####find best cos####
    table_day["time"] = [pd.to_datetime(index, format="%H:%M:%S", errors='ignore') for index in table_day.index] #override date+time and store time only

    time_windowed = table_day.groupby([pd.Grouper(key = 'time', freq=day_window_size, origin = "start_day")], as_index = False) #group by an interval of day_window_size (origin = "start_Day" -> first group starts at midnight and not with first value)

    #if day has missing windows -> skip this day
    if len(time_windowed) < max_group_length:
      continue

    cosinus_list = [] #list of all window cosinus of that day
    for index, table in time_windowed: #iterate over windows
      key = index.strftime("%H:%M:%S") #get time of this window (also key of vector_today_windowed_dict)

      window = vector_today_windowed_dict.get(key, None) #get window of searchDay

      #if window not found (failure in )
      if not window:
        logging.warning("Searching day vector not found (this is resulting due an error while creating the window vectors of our searching day)... Ignore this window")
        continue
      searchVector = window[0]
      length_searchVector = window[1]

      #construct window vector
      try:
        vector = construct_window_vector(table.drop(["time"], axis = 1), vector_lim_weight) #remove time attribute and calculate vector
      except ValueError as ex:
        logging.error(ex)
        logging.error("Window vector couldnt be created... Ignore this window")
        continue
      

      if len(vector) != len(searchVector):
        logging.info(window)
        raise Exception("Vectors don't have equal length")

      scalarProd = sum([vector[i] * searchVector[i] for i in range(0, len(vector))]) #calculate scalar product of window
      len_vector = np.sqrt(sum([vector[i] ** 2 for i in range(0, len(vector))])) #calculate length of window vector

      #if a vector has the length of 0
      if len_vector == 0 or length_searchVector == 0:
        continue

      simularity = scalarProd / (len_vector * length_searchVector) #calculate simularity

      #due to caluclation inaccuracy
      if simularity > 1:
        result = np.arccos(1)

      elif simularity < 0:
        result = np.arccos(0)

      else:
        result = np.arccos(simularity)

      cosinus_list.append(result)

    #compare only if list isn't empty -> this can happen, if construct_window_vector creates only empty vectors a day long
    if cosinus_list:
      mean_cosinus =  np.mean(cosinus_list)

      if mean_cosinus < bestCos:
        bestCos = mean_cosinus
        best_date = time

    if progress_counter in progress_steps:
      logging.info(str(progress_steps.index(progress_counter) * 10) + "% reached")

  logging.info("Most similar day found: "+ str(best_date) +" nearest neighbour calculation finished :)")

  return best_date

def forecast_of_tomorrow(station: str, date_searchBestRecord: datetime):
  """
  Get date and values of a day  which is the closest to date_searchBestRecord by cos simularity 
  
  Parameters:
  station (string): station
  date_searchBestRecord (datetime): output of this function is searching for a similar day as date_searchBestRecord

  returns:
  tuple(dateTime, pandas.DataFrame): returns a tuple containing the date of the predicted tomorrow and the values of the predicted tomorrow
  """

  possibleMeasurements = [Measurement.Air_temp, Measurement.Humidity]
  config_possibleMeasurements = [(-10, 10, 1), (-40, 40, 0)]

  start_date = date_searchBestRecord.replace(hour=0, minute=0, second=0, microsecond=0)
  end_date = start_date + timedelta(days=1)
  start_date = start_date.astimezone(pytz.utc)
  end_date = end_date.astimezone(pytz.utc)

  try:
    test_measurement = get_all_measurements(station, (start_date, end_date), timeFilling=False)
  
  except Exception as ex:
    raise Exception("Forecast of this day couldn't be created: ", ex)


  #get indexes of available measurements with its config
  indexAvailable = []
  for i, name in enumerate([name.value for name in possibleMeasurements]):
      if name in test_measurement.columns:
        indexAvailable.append(i)

  #if not enough measurements available (min: >= 2)
  if len(indexAvailable) <= 1:
    logging.error("Not enough attributes available to do the nearest neighbour!")
    return None
      
  #get measurements to observe
  availableMeasurements = []
  config_availableMeasurements = []
  for i in indexAvailable:
    availableMeasurements.append(possibleMeasurements[i])
    config_availableMeasurements.append(config_possibleMeasurements[i])

  date_of_nearestNeighbour = nearest_neighbour(station, date_searchBestRecord, 2, "2h", availableMeasurements, config_availableMeasurements, mean_in_range_percent = 10) #get nearest date

  predicted_date = date_of_nearestNeighbour + timedelta(days = 1) #add 1 day

  test_measurement_data = get_all_measurements(station, (predicted_date, datetime(predicted_date.year, predicted_date.month, predicted_date.day, hour = 23, minute = 59, second = 59)), timeFilling=False) #get values of predicted date
    
  return (predicted_date, test_measurement_data)

if __name__ == '__main__':
  pass