""" Weather Data Collector for Influxdb

This script allows the user to interact with weather data gathered
from city Zurich. See https://data.stadt-zuerich.ch/dataset/sid_wapo_wetterstationen
for further information. The data can be stored in an influxdb, which is required
to be running before using the functions defined in this file.

Authors:
Fabian Märki, Jelle Schutter, Lucas Brönnimann
"""

import logging
import influxdb
import pandas as pd
from pandas import json_normalize
import numpy as np
from influxdb import DataFrameClient
import pandas
import requests
from requests.exceptions import ConnectionError
import json
import signal
import sys
from datetime import datetime, timedelta
import time
import os
import threading
from collections import deque
from requests.models import HTTPError
import main as update


class Config:
    db_host = 'localhost' #database host
    db_port = 8086 #port from database
    db_name = 'meteorology' #database name
    stations = ['mythenquai', 'tiefenbrunnen'] #table names
    stations_force_query_last_entry = False
    stations_last_entries = {} #last entries in database
    keys_mapping = { 
        'values.timestamp_cet.value': 'timestamp_cet',
        'values.air_temperature.value': 'air_temperature',
        'values.barometric_pressure_qfe.value': 'barometric_pressure_qfe',
        'values.dew_point.value': 'dew_point',
        'values.global_radiation.value': 'global_radiation',
        'values.humidity.value': 'humidity',
        'values.precipitation.value': 'precipitation',
        'values.water_level.value': 'water_level',
        'values.water_temperature.value': 'water_temperature',
        'values.wind_direction.value': 'wind_direction',
        'values.wind_force_avg_10min.value': 'wind_force_avg_10min',
        'values.wind_gust_max_10min.value': 'wind_gust_max_10min',
        'values.wind_speed_avg_10min.value': 'wind_speed_avg_10min',
        'values.windchill.value': 'windchill'
    }
    historic_data_chunksize = 10000 #csv file of historic data is read in chunks -> this is the size
    client = None #database client

def say_goodbye():
    print('bye')

def __set_last_db_entry(config, station, entry):
    current_last_time = __extract_last_db_day(config.stations_last_entries.get(station, None), station, None) #get date of "stations_last_entries" from "station"
    entry_time = __extract_last_db_day(entry, station, None) #get last date of uploaded chunk

    if current_last_time is None and entry_time is not None: #not written to "stations_last_entries" yet
        config.stations_last_entries[station] = entry
    elif current_last_time is not None and entry_time is not None and current_last_time < entry_time: #newer last time found
        config.stations_last_entries[station] = entry

def __get_last_db_entry(config, station):
    last_entry = None
    if not config.stations_force_query_last_entry: #force query last entry not enabled
        # speedup for Raspberry Pi - last entry query takes > 2 Sec.!
        last_entry = config.stations_last_entries.get(station, None) #get entry for "station"

    if last_entry is None: #if no entry found or force query last entry enabled
        try:
            # we are only interested in time, however need to provide any field to make query work
            query = f'SELECT air_temperature FROM {station} ORDER BY time DESC LIMIT 1'
            last_entry = config.client.query(query)
        except:
            # There are influxDB versions which have an issue with above query
            print('An exception occurred while querying last entry from DB for ' + station + '. Try alternative approach.')
            query = f'SELECT * FROM {station} ORDER BY time DESC LIMIT 1'
            last_entry = config.client.query(query)

    __set_last_db_entry(config, station, last_entry)
    return last_entry

def __extract_last_db_day(last_entry, station, default_last_db_day):
    if last_entry is not None: #last_entry contains data
        val = None
        if isinstance(last_entry, pd.DataFrame): #last_entry is a pandas Dataframe 
            val = last_entry
        elif isinstance(last_entry, dict): #last_entry is a dictionary
            val = last_entry.get(station, None) #get pd.dataframe from key "station", return "None" if key not found

        if val is not None: #if last entry found
            if not val.index.empty: #index of value is not empty
                return val.index[0].replace(tzinfo = None) #return date and remove tzinfo

    return default_last_db_day

def __get_data_of_day(day, station, periodic_retry = False):
    # convert to local time of station
    base_url = 'https://tecdottir.herokuapp.com/measurements/{}'
    day_str = day.strftime('%Y-%m-%d')
    print('Query ' + station + ' at ' + day_str)
    payload = {
        'startDate': day_str,
        'endDate': day_str
    }
    url = base_url.format(station)
    while True:
        try:
            response = requests.get(url, params = payload)
            if(response.ok):
                jData = json.loads(response.content)
                return jData
            else:
                response.raise_for_status()
                raise ConnectionError(response.status_code)

        except Exception as e:
            if periodic_retry:
                raise e

            print(f'Request for \'{e.request.url}\' failed. ({e})\nTrying again in 10 seconds...')
            time.sleep(10)

def __define_types(data : pandas.DataFrame, date_format):
    '''Description:
    
    renames timestamp column,
    converts cet to utc and use own date format,
    set timestamp to index  column,
    replace empty elements with 0,
    set datatype of all columns (except timestamp) to float64
    '''
    if not data.empty: #data is not empty
        # convert cet to utc
        data['timestamp'] = pd.to_datetime(data['timestamp_cet'], format = date_format) - timedelta(hours = 1) #convert from "timestamp_cet" to new date_format and create new column "timestamp" subtract one hour (why? i think it should be 2 hours)
        data.drop('timestamp_cet', axis = 1, inplace = True) #drop old timestamp column
        data.set_index('timestamp', inplace = True) #set "timestamp" as the index column and delete the old index column (inpace -> instead of creating a new dataframe, override the old one)

    data.replace('.', 0, inplace = True) #repalce al the missing values (represented as .) with a 0
    for column in data.columns[0:]: #iterate trough all columns
        if column != 'timestamp': #not the timestamp column
            data[column] = data[column].astype(np.float64) #set datatype to float

    return data

def __clean_data(config, data_of_last_day, last_db_entry, station):
    normalized = json_normalize(data_of_last_day['result'])

    for column in normalized.columns[0:]:
        mapping = config.keys_mapping.get(column, None)
        if mapping is not None:
            normalized[mapping] = normalized[column]
        if mapping != column:
            normalized.drop(columns = column, inplace = True)

    normalized = __define_types(normalized, '%d.%m.%Y %H:%M:%S')

    # remove all entries older than last element
    if last_db_entry is not None: #if database isn't empty
        last_db_entry_time = None
        if isinstance(last_db_entry, pd.DataFrame):
            last_db_entry_time = last_db_entry
        elif isinstance(last_db_entry, dict):
            last_db_entry_time = last_db_entry.get(station, None)
        last_db_entry_time = last_db_entry_time.index[0].replace(tzinfo = None)
        normalized.drop(normalized[normalized.index <= last_db_entry_time].index, inplace = True)

    return normalized

def __add_data_to_db(config, data, station):
    config.client.write_points(data, station, time_precision = 's', database = config.db_name) #write rows (params: data = DataFrame, station = name of measurement, time_precision = seconds, database = db_name)
    __set_last_db_entry(config, station, data.tail(1)) #get last value from data (newest entry) and store it

def __signal_handler(sig, frame):
    sys.exit(0)


def connect_db(config):
    """Connects to the database and initializes the client

    Parameters:
    config (Config): The Config containing the DB connection info

   """
    if config.client is None: #if you havent already created a client
        # https://www.influxdata.com/blog/getting-started-python-influxdb/
        config.client = DataFrameClient(host = config.db_host, port = config.db_port) #connect to database
        # influxdb may not have finished startup yet
        influx_is_running = False
        while not influx_is_running:
            try:
                logging.info("InfluxDB is up and running. InfluxDB Version: " + str(config.client.ping()))
                influx_is_running = True
            except:
                logging.warning("InfluxDB is not running")

        config.client.create_database(config.db_name) #create a new database
        config.client.switch_database(config.db_name) #select created database
    logging.info("Successfully connected to DB")

def clean_db(config):
    """Drops the whole database and creates it again

    Parameters:
    config (Config): The Config containing the DB connection info

   """
    config.client.drop_database(config.db_name) #drop the database
    config.client.create_database(config.db_name) #create a new database
    config.stations_last_entries.clear() #clear the variable "stations_last_entries" in the config

def try_import_csv_file(config, station, file_name):
    """Imports data from a .csv file

    Parameters:
    config (Config): The Config containing the DB connection info
    station (String): Either 'Mythenquai' or 'Tiefenbrunnen'
    file_name (String): Path to the file from which the data shall be imported

    Returns:
    True: If csv already importet or csv successfully importet
    False: CSV failed to import (csv file not found)
    """
    if __is_csv_imported(config, station):
        print(file_name + ' already imported.')
        return True

    if os.path.isfile(file_name): #does the path point to a file?
        print('\tLoad ' + file_name)
        for chunk in pd.read_csv(file_name, delimiter = ',', chunksize = config.historic_data_chunksize): #read the csv file in chunks
            chunk = __define_types(chunk, '%Y-%m-%dT%H:%M:%S') #preprocess data
            print('Add ' + station + ' from ' + str(chunk.index[0]) + ' to ' + str(chunk.index[-1]))
            __add_data_to_db(config, chunk, station) #add data to database

        return True
    else:
        print(file_name + ' does not seem to exist.')
        return False


def __is_csv_imported(config, station):
    last_db_entry = __get_last_db_entry(config, station)
    last_db_day = __extract_last_db_day(last_db_entry, station, None)
    return last_db_day != None and last_db_day > datetime(2007, 7, 31)


def import_latest_data(config, periodic_read = False, callback = update.update_data):
    """Reads the latest data from the Wasserschutzpolizei Zurich weather API

    Parameters:
    config (Config): The Config containing the DB connection info
    periodic_read (bool): Defines if the function should keep reading after it imported the latest data (blocking through a sleep)
    callback (function): will be executed, when new data is uploaded to database

   """
    # access API for current data
    current_time = datetime.utcnow() + timedelta(hours = 1)
    current_day = current_time.replace(hour = 0, minute = 0, second = 0, microsecond = 0)
    last_db_days = [current_day] * len(config.stations)

    #get last date (day) of last db entry
    for idx, station in enumerate(config.stations):
        last_db_entry = __get_last_db_entry(config, station)
        last_db_days[idx] = __extract_last_db_day(last_db_entry, station, last_db_days[idx]) + timedelta(hours = 1)

    #set signal handler if periodic read available
    if periodic_read and threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGINT, __signal_handler)
        print('\nPress Ctrl+C to stop!\n')

    check_db_day = min(last_db_days) #get oldest date of newest entries
    check_db_day = check_db_day.replace(hour = 0, minute = 0, second = 0, microsecond = 0) #extract date (day) only

    first_cycle = True
    last_cycle = False

    while True:
        # check if all historic data (retrieved from API) has been processed
        #wait 10min until the next call 
        if not first_cycle and periodic_read and check_db_day >= current_day and not first_cycle: #if its not the first cycle, and no new day arrived
            # everytime the clock hits 05', 15', 25', 35', 45' or 55' (The new measurement is always 5 Minutes delayed)
            sleep_seconds = 600 - int((time.time()+300) % 600) + 10 # add ten seconds to compensate for inaccuracy 
            current_time = datetime.utcnow() + timedelta(hours = 1)
            sleep_until = current_time + timedelta(seconds = sleep_seconds, microseconds=0)

            print('Sleep for ' + str(sleep_seconds) + 's (from ' + str(current_time) + ' until ' + str(sleep_until) + ') when next data will be queried.')
            time.sleep(sleep_seconds)
            current_day = current_time.replace(hour = 0, minute = 0, second = 0, microsecond = 0)

        if not periodic_read and check_db_day >= current_day: #if periodic read is disabled and newest data is already stored
            if last_cycle:
                return
            last_cycle = True


        for idx, station in enumerate(config.stations):
            if last_db_days[idx].replace(hour = 0, minute = 0, second = 0, microsecond = 0) > check_db_day: #if newest data of station is already stored -> continue with other station
                continue
            last_db_entry = __get_last_db_entry(config, station)
            last_db_days[idx] = __extract_last_db_day(last_db_entry, station, last_db_days[idx])

            try:
                data_of_last_db_day = __get_data_of_day(check_db_day, station, periodic_read) #get data of station (whole day)

            except Exception as e:
                print(f"Connection to station {station} failed... skipped!")
                continue

            normalized_data = __clean_data(config, data_of_last_db_day, last_db_entry, station) #extract data, that is not stored yet

            if normalized_data.size > 0: #if new data is available
                __add_data_to_db(config, normalized_data, station) #add data to database
                print('Handle ' + station + ' from ' + str(normalized_data.index[0]) + ' to ' + str(normalized_data.index[-1]))

                #do a callback if vailable
                if callback:
                    callback()

            else:
                print('No new data received for ' + station)

        if check_db_day < current_day: #new day arrived
            check_db_day = check_db_day + pd.DateOffset(1) #add day 
        elif periodic_read and check_db_day >= current_day: #if periodic read enabled and it is the same day
            check_db_day = datetime.utcnow() + timedelta(hours = 1) #update day (get current date)

        if first_cycle:
            first_cycle = False

def get_entries(config, station, start_time : str, stop_time : str = None) -> pd.DataFrame:
    """
    query all fields from station in a specific time range -> today to specific time in the past / specific time in the past to specific time in the past

    Parameters:
    config (Config): The Config containing the DB connection info
    station (string): station name
    start_time (str / dateTime): start time of data as string [1d, 1m, 1w...] or dateTime -> only if stop_time != None
    stop_time (dateTime -> default: None): specifies end time 
    """
    if not stop_time: #if stop_time not defined
        query = f'SELECT * FROM {station} WHERE time > now() - {start_time}'

    else:
        query = f'SELECT * FROM {station} WHERE time >= \'{start_time.strftime("%Y-%m-%dT%H:%M:%SZ")}\' AND time <= \'{stop_time.strftime("%Y-%m-%dT%H:%M:%SZ")}\''

    answer = config.client.query(query) #query entries -> dictionary
    val = answer.get(station, None) #get pd.dataframe from key "station", return "None" if key not found
    return val

def get_attr_entries(config, attribute, station, start_time : str, stop_time : str = None) -> pd.DataFrame:
    """
    query a specific field from station in a specific time range -> today to specific time in the past / specific time in the past to specific time in the past

    Parameters:
    config (Config): The Config containing the DB connection info
    attribute (string): field name
    station (string): station name
    start_time (str / dateTime): start time of data as string [1d, 1m, 1w...] or dateTime -> only if stop_time != None
    stop_time (dateTime -> default: None): specifies end time 
    """
    if not stop_time: #if stop_time not defined
        query = f'SELECT {attribute} FROM {station} WHERE time > now() - {start_time}'

    else:
        query = f'SELECT {attribute} FROM {station} WHERE time >= \'{start_time.strftime("%Y-%m-%dT%H:%M:%SZ")}\' AND time <= \'{stop_time.strftime("%Y-%m-%dT%H:%M:%SZ")}\''

    
    answer = config.client.query(query) #query entries -> dictionary
    val = answer.get(station, None) #get pd.dataframe from key "station", return "None" if key not found

    #add empty column if not existent
    if attribute not in val:
            val[attribute] = None
        
    return val

def get_multible_attr_entries(config, attributes, station, start_time : str, stop_time : str = None) -> pd.DataFrame:
    """
    query specific fields from station in a specific time range -> today to specific time in the past / specific time in the past to specific time in the past

    Parameters:
    config (Config): The Config containing the DB connection info
    attributes (list of string): field names
    station (string): station name
    start_time (str / dateTime): start time of data as string [1d, 1m, 1w...] or dateTime -> only if stop_time != None
    stop_time (dateTime -> default: None): specifies end time 
    """

    if not stop_time: #if stop_time not defined
        query = f'SELECT {",".join(attributes)} FROM {station} WHERE time > now() - {start_time}'

    else:
        query = f'SELECT {",".join(attributes)} FROM {station} WHERE time >= \'{start_time.strftime("%Y-%m-%dT%H:%M:%SZ")}\' AND time <= \'{stop_time.strftime("%Y-%m-%dT%H:%M:%SZ")}\''
    
    answer = config.client.query(query) #query entries -> dictionary
    val = answer.get(station, None) #get pd.dataframe from key "station", return "None" if key not found

    #add empty column if not existent
    for attribute in attributes:
        if attribute not in val:
            val[attribute] = None

    return val

def get_multible_attr_entries_yearlyWindow(config, attributes, station, targetDate: datetime, timeArea_months: int = 2) -> pd.DataFrame:
    """
    query specific fields from station in a specific time range every year (targetDate (month, day) +- x months)

    Parameters:
    config (Config): The Config containing the DB connection info
    attributes (list of string): field names
    station (string): station name
    targetDate (datetime): target date 
    timeArea_months (int, default: 2): time window around targetTime
    """

    query = f'SELECT first(air_temperature) FROM {station}'
    answer = config.client.query(query) #query entries -> dictionary
    df_first = answer.get(station, None) #get pd.dataframe from key "station", return "None" if key not found
    oldest_timestamp = str(df_first.index.values[0])

    query = f'SELECT last(air_temperature) FROM {station}'
    answer = config.client.query(query) #query entries -> dictionary
    df_first = answer.get(station, None) #get pd.dataframe from key "station", return "None" if key not found
    newest_timestamp = str(df_first.index.values[0])

    oldest_date = datetime.strptime(oldest_timestamp.split("T")[0], '%Y-%m-%d')
    newest_date = datetime.strptime(newest_timestamp.split("T")[0], '%Y-%m-%d')

    if oldest_date > newest_date:
        raise Exception("Oldest timestamp in Database is newer than newest timestamp???")

    dateTimeRange = []
    buffer = oldest_date
    while True:
        if (targetDate.month - timeArea_months) < 1:
            timeStart = datetime(buffer.year - 1, 12 + (targetDate.month - timeArea_months), targetDate.day)
        else:
            timeStart = datetime(buffer.year, targetDate.month - timeArea_months, targetDate.day)

        if (targetDate.month + timeArea_months) > 12:
            timeEnd = datetime(buffer.year + 1, (targetDate.month + timeArea_months) - 12, targetDate.day)
        else:
            timeEnd = datetime(buffer.year, targetDate.month + timeArea_months, targetDate.day)

        dateTimeRange.append((timeStart, timeEnd))

        buffer = datetime(buffer.year + 1, buffer.month, buffer.day)

        if buffer > newest_date:
            break
    
    tables = []
    for range1, range2 in dateTimeRange:
        query = f'SELECT {",".join(attributes)} FROM {station} WHERE time >= \'{range1.strftime("%Y-%m-%dT%H:%M:%SZ")}\' AND time <= \'{range2.strftime("%Y-%m-%dT%H:%M:%SZ")}\''
        answer = config.client.query(query) #query entries -> dictionary
        
        #add empty column if not existent
        for attribute in attributes:
            if attribute not in answer:
                answer[attribute] = None

        tables.append(answer.get(station, None)) #get pd.dataframe from key "station", return "None" if key not foundcand add to table

    
    return tables

