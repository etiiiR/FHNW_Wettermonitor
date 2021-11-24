from datetime import datetime, date
import os
import numpy as np
from dateutil.relativedelta import relativedelta
from numpy.core.fromnumeric import shape
import weatherdata as wd
import matplotlib.pyplot as plt
import pandas as pd
import enum
from pathlib import Path
from windrose import WindroseAxes

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

  root = str(Path(os.path.dirname(os.path.realpath(__file__))).parent)
  
  if (wd.try_import_csv_file(config, 'mythenquai',    root + "/Messwerte/messwerte_mythenquai_2007-2020.csv") and
      wd.try_import_csv_file(config, 'tiefenbrunnen', root + "/Messwerte/messwerte_tiefenbrunnen_2007-2020.csv")):
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

#forecast
def construct_day_vector(df: pd.DataFrame, lim_weight: list):
  """
  constructs a vector in dependence of the dataframe

  Parameters:
  df (pandas.DataFrame)
  lim_weight (list(tuple(min, max, weight_factor))): min -> vektorcomponent = 0, max -> vektorcomponent = 1, weight_factor ->  vektorcomponent * x
  """

  df = df.dropna() #remove measurements with missing values
  df = df.reset_index(drop = True) #delete index
  vector = np.empty(len(df.columns)) #create an empty vector with the length of the dataframe

  for _, row in df.iterrows(): #iterate over rows
    
    row = row.reset_index(drop = True) #reset index of rows
    temp_vector = np.empty(len(df.columns)) #create temporary vector
    for index_item, item in row.iteritems(): #iterate over observation
      #extract limitations
      min = lim_weight[index_item][0]
      max = lim_weight[index_item][1]
      weight = lim_weight[index_item][2]

      #range check
      if item < min:
        temp_vector[index_item] = 0
        print(f"Warning: Value: {item} in column: {index_item} lower than allowed... set to 0")

      elif item > max:
        temp_vector[index_item] = weight
        print(f"Warning: Value: {item} in column: {index_item} higher than allowed... set to weight")
        break

      else:
        temp_vector[index_item] = (1 / (max - min)) * (item - min) * weight
      
    vector = np.add(vector, temp_vector)
  
  return np.divide(vector, len(df.index))


def nearest_neighbour(station: str, date_searchBestRecord: datetime, timeArea_months: int):
  """
  Get date of a day which is the closest to date_searchBestRecord by cos simularity 

  Parameters:
  station (string): station
  date_searchBestRecord (datetime): output of this function is searching for a similar day as date_searchBestRecord
  timeArea_months (int): window time bewteen (date_searchBestRecord - timeArea_months, date_searchBestRecord + timeArea_months) every year 
  """

  #measurements = [Measurement.Air_temp, Measurement.Humidity] #selct measurements
  #vector_lim_weight = [(-100, 100, 1), (0, 110, 1)] #min, max, weight

  measurements = [Measurement.Air_temp, Measurement.Dew_point] #selct measurements
  vector_lim_weight = [(-30, 70, 0.8), (-10, 110, 0.2)] #min, max, weight


  measurements_converted = [measurement.value for measurement in measurements] #convert measurements

  tables_hist =  wd.get_multible_attr_entries_yearlyWindow(config, measurements_converted, station, date_searchBestRecord, timeArea_months=timeArea_months) #get time windows (missing measurements are not filled with None)
  table_hist = pd.concat(tables_hist) #concat 
  table_hist["time"] = [index.strftime("%yyyy-mm-%dd") for index in table_hist.index] #add time column containing only year month and day

  dateOnly = datetime(date_searchBestRecord.year, date_searchBestRecord.month, date_searchBestRecord.day) #get date of date_searchBestRecord only
  table_dateSearchFor = get_measurements(measurements, station, (dateOnly, dateOnly + relativedelta(days = +1)), timeFilling=False).drop(["time"], axis = 1) #get measurements from date: date_searchBestRecord (whole day) and drop "time" attribute
  
  tables_groupedByDay_hist = [x for _, x in table_hist.groupby(table_hist['time'])] #group by day

  vector_today = construct_day_vector(table_dateSearchFor, vector_lim_weight) #remove time attribute and construct vector of day
  len_vectorToday = np.sqrt(sum([vector_today[i] ** 2 for i in range(0, len(vector_today))])) #calculate length of vectorToday 
  
  #search for best cos
  best_date = dateOnly
  bestCos = np.pi / 2
  for table_hist_day in tables_groupedByDay_hist:
    time = table_hist_day.index[0]
    
    vector = construct_day_vector(table_hist_day.drop(["time"], axis = 1), vector_lim_weight)

    if len(vector) != len(vector_today):
      raise Exception("Vectors don't have equal length")

    scalarProd = sum([vector[i] * vector_today[i] for i in range(0, len(vector))])
    len_vector = np.sqrt(sum([vector[i] ** 2 for i in range(0, len(vector))])) #calculate length of vector

    result = np.arccos(scalarProd / (len_vector * len_vectorToday))

    if result < bestCos:
      bestCos = result
      best_date = time
    
      
  return best_date

  #print(construct_day_vector(tables[0], vector_lim_weight))

if __name__ == '__main__':
  pass