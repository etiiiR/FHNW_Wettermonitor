from datetime import datetime, timedelta
import time
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


def create_weather_chart():
    #todays plots
    weatherimport.generate_plot_colMatrix([(weatherimport.Measurement.Air_temp, ("Temperatur", "T", "°C")), (weatherimport.Measurement.Humidity, ("Luftfeuchtigkeit", "", "%"))], "mythenquai", (datetime.today().date(), datetime.now()), imagePath=str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/Images/Temp_Hum_Today_Mythenquai.png")
    weatherimport.generate_plot_colMatrix([(weatherimport.Measurement.Air_temp, ("Temperatur", "T", "°C")), (weatherimport.Measurement.Humidity, ("Luftfeuchtigkeit", "", "%"))], "tiefenbrunnen", (datetime.today().date(), datetime.now()), imagePath=str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/Images/Temp_Hum_Today_Tiefenbrunnen.png")
    weatherimport.generate_windRose("mythenquai", (datetime.today().date(), datetime.now()), imagePath=str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/Images/WindRose_Today_Mythenquai.png")
    weatherimport.generate_windRose("tiefenbrunnen", (datetime.today().date(), datetime.now()), imagePath=str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/Images/WindRose_Today_Tiefenbrunnen.png")

    #historical plots
    weatherimport.generate_plot_colMatrix([(weatherimport.Measurement.Air_temp, ("Temperatur", "T", "°C")), (weatherimport.Measurement.Humidity, ("Luftfeuchtigkeit", "", "%"))], "mythenquai", (datetime(2015, 1, 1), datetime.now()), imagePath=str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/Images/Temp_Hum_Hist_Mythenquai.png")
    weatherimport.generate_plot_colMatrix([(weatherimport.Measurement.Air_temp, ("Temperatur", "T", "°C")), (weatherimport.Measurement.Humidity, ("Luftfeuchtigkeit", "", "%"))], "tiefenbrunnen", (datetime(2015, 1, 1), datetime.now()), imagePath=str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/Images/Temp_Hum_Hist_Tiefenbrunnen.png")
    weatherimport.generate_windRose("mythenquai", (datetime(2015, 1, 1), datetime.now()), imagePath=str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/Images/WindRose_Hist_Mythenquai.png")
    weatherimport.generate_windRose("tiefenbrunnen", (datetime(2015, 1, 1), datetime.now()), imagePath=str(Path(os.path.dirname(os.path.realpath(__file__)))) + "/Images/WindRose_Hist_Tiefenbrunnen.png")
    
    #todo save a IMAGE of the Weather in the Images Folder
    pass

def get_weather_store_in_data(data):
    #todo get Weather from influx and store it in the Context to refresh the / Route and show the weather
    data = data

def update_data():
    print('Update Data from database')


def get_data_continuesly():
    weatherimport.read_data_continuesly()

@app.before_first_request
def get_data():
    t=threading.Thread(target=get_data_continuesly)
    t.start()


@app.route('/')
def index():
    return redirect("/mythenquai")


@app.route("/mythenquai")
def mythenquai():
    return front_page("mythenquai")


@app.route("/tiefenbrunnen")
def tiefenbrunnen():
    return front_page("tiefenbrunnen")

def front_page(station):
    measurements = [weatherimport.Measurement.Air_temp,
                    weatherimport.Measurement.Humidity,
                    weatherimport.Measurement.Wind_gust_max_10min,
                    weatherimport.Measurement.Wind_speed_avg_10min,
                    weatherimport.Measurement.Wind_force_avg_10min,
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
        for measurement in measurements:
            if measurement.value not in weather:
                weather[measurement.value] = "-"
        weather["minutes_since_last_measurement"] = (datetime.now(weather['time'].tzinfo) - weather['time'])/timedelta(minutes=1)
    else:
        weather = { measurement.value: "-" for measurement in measurements }
        
    
    return render_template('index.html', 
        station = station,
        weather = weather,
        refresh_seconds = 600 - int((time.time()+300) % 600) + 20 # add 20 seconds to compensate for inaccuracy
        )


if __name__ == "__main__":
    weatherimport.init()
    #create_weather_chart()
    ui.run()
    
