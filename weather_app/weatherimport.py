from datetime import date, datetime
import os
import numpy as np
import weatherdata as wd
import matplotlib.pyplot as plt
import pandas as pd
import enum
from pathlib import Path
from windrose import WindroseAxes

#import warnings
#warnings.simplefilter("error")


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

  if not keepIndex:
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
        print(f"Warning: Value: {item} in column: {df.columns[index_item]} lower than allowed... set to ", -1 * weight)

      elif item > max:
        temp_vector[index_item] = weight
        print(f"Warning: Value: {item} in column: {df.columns[index_item]} higher than allowed... set to", weight)

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

  df = df.dropna() #remove measurements with missing values
  vector = np.empty(len(df.columns)) #create an empty vector with the length of the dataframe

  if df.empty:
    raise ValueError("Dataframe empty after deleting observations containing NA")

  df = df.sort_index() #sortiere nach datum -> top = oldest, bottom = newest

  if type(df.index[-1]) != pd.Timestamp or type(df.index[0]) != pd.Timestamp:
    raise Exception("Index has wrong format!!!")

  num_of_10min_steps =  int((df.index[-1] - df.index[0]).total_seconds() / (10 * 60)) #calculate number of 10 min steps

  if num_of_10min_steps == 0:
    raise ValueError("This window is containing one observation only after deleting all observations containing NA")

  vector = np.empty(len(df.columns)) #create an empty vector with the length of the dataframe
  for index_item in range(0, len(df.columns)): #iterate over attributes
      #extract limitations
      min = lim_weight[index_item][0] * num_of_10min_steps
      max = lim_weight[index_item][1] * num_of_10min_steps
      weight = lim_weight[index_item][2]

      #extract observations
      first_observation = df.iat[0, index_item] #get first observation
      last_observation = df.iat[-1, index_item] #get last observation

      delta = last_observation - first_observation #calculate difference
  
      #range check
      if delta < min:
        vector[index_item] = -1 * weight
        print(f"Warning: Value: {delta} in column: {df.columns[index_item]} lower than allowed... set to ", -1 * weight)

      elif delta > max:
        vector[index_item] = weight
        print(f"Warning: Value: {delta} in column: {df.columns[index_item]} higher than allowed... set to", weight)

      else:
        vector[index_item] = (((normalize_to_plusMinus * 2 * delta) / (max - min)) + ((-1 * normalize_to_plusMinus) - ((normalize_to_plusMinus * 2 * min) / (max - min)))) * weight #linearisierung für: item == max -> 1, item == min -> -1, zwischenresultat * weight -> resultat

  return vector


def nearest_neighbour(station: str, date_searchBestRecord: datetime, timeArea_months: int, day_window_size = '4h', measurements = [Measurement.Air_temp, Measurement.Dew_point], vector_lim_weight = [(-10, 10, 1), (-10, 10, 0.1)]):
  """
  Get date of a day which is the closest to date_searchBestRecord by cos simularity 
  
  Parameters:
  station (string): station
  date_searchBestRecord (datetime): output of this function is searching for a similar day as date_searchBestRecord
  timeArea_months (int): window time bewteen (date_searchBestRecord - timeArea_months, date_searchBestRecord + timeArea_months) every year 
  measurements (list(Measurement)): measurements to include. Example: [Measurement.Air_temp, Measurement.Dew_point]
  vector_lim_weight (list(tuple)): specify min, max and weight for each measurement. Example for measurement Air_temp: (-10, 10, 1) min -> -10, max -> 10, weight = 1: if value = -10 -> X_airTemp = -1 * weight; value = 10 -> X_airTemp = 1 * weight; 
  """

  if len(measurements) != len(vector_lim_weight):
    raise Exception("Each measurement needs a lim_weight tuple")

  if len(measurements) <= 1:
    raise Exception("Its not possible to calculate a cosinus simularity in one dimension... Please add more measurements!")

  print("Start nearest neighbour calculation...")

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

  vector_today_windowed_dict = {}
  for index, table in time_dateSearchFor_windowed: #calculate vector/vector_length of each window
    try:
      vector = construct_window_vector(table.drop(["time"], axis = 1), vector_lim_weight) #remove time attribute and construct vector of day
      len_vector= np.sqrt(sum([vector[i] ** 2 for i in range(0, len(vector))])) #calculate length of vectorToday 
      vector_today_windowed_dict[index.strftime("%H:%M:%S")] = (vector, len_vector) #append vector and length to dict
    except ValueError as ex:
      print("Warning!!! the day we are searching for has empty values... number of window will be shortened -> this can lead to more unprecisely predictions")
    
  if not vector_today_windowed_dict:
    raise Exception("The day we are searching for cannot be vectorized... stopped searching!")

  progress_counter = 0
  progress_steps = [steps for steps in range(0, len(tables_groupedByDay_hist.size()), len(tables_groupedByDay_hist.size()) // 10)]

  #search for best cos
  best_date = dateOnly
  bestCos = np.pi / 2
  for index, table_hist_day in tables_groupedByDay_hist: #iterate over days
    time =  index

    if datetime(time.year, time.month, time.day) == dateOnly: #reference day found
      #print("reference day found:", datetime(time.year, time.month, time.day))
      continue

    table_day = table_hist_day #rename
    
    table_day["time"] = [pd.to_datetime(index, format="%H:%M:%S", errors='ignore') for index in table_day.index] #override date+time and store time only

    time_windowed = table_day.groupby([pd.Grouper(key = 'time', freq=day_window_size, origin = "start_day")], as_index = False) #group by an interval of day_window_size (origin = "start_Day" -> first group starts at midnight and not with first value)


    cosinus_list = [] #list of all window cosinus of that day
    for index, table in time_windowed: #iterate over windows
      key = index.strftime("%H:%M:%S") #get time of this window (also key of vector_today_windowed_dict)

      window = vector_today_windowed_dict.get(key, None) #get window of searchDay

      #if window not found (failure in )
      if not window:
        print("Searching day vector not found (this is resulting due an error while creating the window vectors of our searching day)... Ignore this window")
        continue
      searchVector = window[0]
      length_searchVector = window[1]

      #construct window vector
      try:
        vector = construct_window_vector(table.drop(["time"], axis = 1), vector_lim_weight) #remove time attribute and calculate vector
      except ValueError as ex:
        print(ex)
        print("Window vector couldnt be created... Ignore this window")
        continue
      

      if len(vector) != len(searchVector):
        print(window)
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

    progress_counter += 1

    if progress_counter in progress_steps:
      print(progress_steps.index(progress_counter) * 10,"% reached")
  
  print("Most similar day found: ", best_date, " nearest neighbour calculation finished :)")

  return best_date



if __name__ == '__main__':
  pass