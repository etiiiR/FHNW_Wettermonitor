from datetime import datetime
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
    if weatherimport.systemInitialized():
        # todoo check if the database has old data if yes then update it and afterwards load the homepage
        wetter = weatherimport.get_measurement(weatherimport.Measurement.Air_temp, station, "1d")
        dict_time = wetter.sort_values(by=['time'])
        obj_air_temp = dict_time['air_temperature'][0]

        df_humidty= weatherimport.get_measurement(weatherimport.Measurement.Humidity, station, "1d")
        sorted_hum = df_humidty.sort_values(by=['time'])
        obj_hum = sorted_hum['humidity'][0]
    else:
        obj_air_temp = "not available yet"
        obj_hum = "not available yet"

    icon_url1 = "rain.png"
    icon_url2 = "sun.png"
    icon_url3 = "windy.png"
    icon_url4 = "weather.png"
    
    context = {
	    'Lufttemp' : obj_air_temp,
	}  
    return render_template('index.html', station = station, Lufttemp = obj_air_temp, Humidity = obj_hum, icon_temp = icon_url4,
    icon_wind = icon_url1, icon_pred = icon_url2, icon_water = icon_url3)

@app.route("/home", methods=['GET'])
def home():
    return render_template('some_page.html')





if __name__ == "__main__":
    weatherimport.init()
    #create_weather_chart()
    ui.run()
    
