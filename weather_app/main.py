from datetime import datetime, timedelta
import time
import schedule
import logging
from typing import Match
from flask import Flask  
from flask import render_template, redirect, url_for

from flaskwebgui import FlaskUI
#https://github.com/btashton/flask-influxdb
from flask_influxdb import InfluxDB
import weatherimport
import threading
from pathlib import Path
import os

app = Flask(__name__)
influx_db = InfluxDB(app=app)
ui = FlaskUI(app, fullscreen=True, width=600, height=500, start_server='flask')

def get_weather_store_in_data(data):
    #todo get Weather from influx and store it in the Context to refresh the / Route and show the weather
    data = data

def update_data():
    # use the scheduler to plot inside the main thread
    # generate_today_graphs() will cancel the job, so the job is only run once
    schedule.every().second.do(weatherimport.generate_today_graphs) # update graphs with new data
    logging.info('Update Data from database')


def check_for_pending_jobs():
    while 1:
        n = schedule.idle_seconds()
        if n is None:
            n = 1
        if n > 0:
            # sleep exactly the right amount of time
            time.sleep(n)
        schedule.run_pending()


@app.before_first_request
def get_data_continuesly():
    threading.Thread(target=weatherimport.read_data_continuesly).start()


@app.route('/')
@app.route('/wetterstation')
def index():
    """
    Leitet den Client weiter auf die Übersichtsseite der Messstation Tiefenbrunnen.
    """
    return redirect("/wetterstation/tiefenbrunnen")


@app.route("/wetterstation/<station>")
def wetterstation(station: str):
    """
    Zeigt eine Übersicht der Wetterdaten der Messstation station an.

    Args:
        station (str): Name der Wetterstation.
    """
    measurements = [weatherimport.Measurement.Air_temp,
                    weatherimport.Measurement.Humidity,
                    weatherimport.Measurement.Wind_gust_max_10min,
                    weatherimport.Measurement.Wind_speed_avg_10min,
                    weatherimport.Measurement.Wind_force_avg_10min,
                    weatherimport.Measurement.Wind_direction,
                    weatherimport.Measurement.Water_temp,
                    weatherimport.Measurement.Dew_point,
                    weatherimport.Measurement.Wind_chill,
                    weatherimport.Measurement.Precipitation,
                    weatherimport.Measurement.Water_level,
                    weatherimport.Measurement.Pressure,
                    weatherimport.Measurement.Radiation]
    if weatherimport.systemInitialized():
        # TODO: check if the database has old data if yes then update it and afterwards load the homepage
        weather = weatherimport.get_measurements(measurements, station, "1d")
        weather = weather.sort_values(by=['time'], ascending=False).to_dict("records")[0]
        for key in weather:
            if weather[key] == None:
                weather[key] = "-"
        weather["minutes_since_last_measurement"] = (datetime.now(weather['time'].tzinfo) - weather['time'])/timedelta(minutes=1)
        weather["wind_direction_text"] = weatherimport.wind_direction_to_text(weather["wind_direction"])
    else:
        logging.warning("No measurements are available")
        weather = { measurement.value: "-" for measurement in measurements }
    
    return render_template('index.html', 
        subpage = "main",
        station = station,
        weather = weather,
        refresh_seconds = 600 - int((time.time()+300) % 600) + 20 # add 20 seconds to compensate for inaccuracy
    )

@app.route("/wetterstation/<station>/<category>")
def wetterstation_details_0(station: str, category: str):
    return redirect(f"/wetterstation/{station}/{category}/history")

@app.route("/wetterstation/<station>/<category>/<type>")
def wetterstation_details(station: str, category: str, type: str):
    """
    Zeigt eine Grafik für eine Messstation für eine bestimmte Kategorie von Messwerten
    und einem bestimmten Zeitraum an. 
    
    Args:
        station (str): Der Name der Messstation.
        category (str): Die Kategorie der anzuzeigenden Messwerte (wind, temperature, water).
        type (str): Der Zeitraum der anzuzeigenden Messwerte (today, tomorrow, history).
    """
    return render_template('index.html', 
        subpage = "graph",
        category = category,
        type = type,
        station = station,
        refresh_seconds = 600 - int((time.time()+300) % 600) + 20 # add 20 seconds to compensate for inaccuracy
    )

def run():
    ui.run()

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(asctime)s - %(message)s')
    logging.info("Programm has started")

    weatherimport.init()

    schedule.every(5).seconds.do(weatherimport.generate_last_7_days_graphs)


    schedule.every().day.at("00:30").do(weatherimport.generate_last_7_days_graphs)
    schedule.every().day.at("01:00").do(weatherimport.generate_prediction_graphs)
    
    # matplotlib needs to run in the main thread
    threading.Thread(target=run).start()
    
    check_for_pending_jobs()

    logging.info("Programm ended")
    
