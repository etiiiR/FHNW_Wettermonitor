from flask import Flask  
from flask import render_template
from flaskwebgui import FlaskUI
#https://github.com/btashton/flask-influxdb
from flask_influxdb import InfluxDB
import weatherimport
import threading

app = Flask(__name__)
influx_db = InfluxDB(app=app)
ui = FlaskUI(app, fullscreen=False, width=600, height=500, start_server='flask')



def create_weather_chart():
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
    weatherimport.init()
    t=threading.Thread(target=get_data_continuesly)
    t.start()
    return

@app.route("/")
def hello():
    # todoo check if the database has old data if yes then update it and afterwards load the homepage
    wetter = weatherimport.get_measurement(weatherimport.Measurement.Air_temp, "mythenquai", "1d")
    dict_time = wetter.sort_values(by=['time'])
    obj_air_temp = dict_time['air_temperature'][0]

    df_humidty= weatherimport.get_measurement(weatherimport.Measurement.Humidity, "mythenquai", "1d")
    sorted_hum = df_humidty.sort_values(by=['time'])
    obj_hum = sorted_hum['humidity'][0]

    icon_url = ""
    
    context = {
	    'Lufttemp' : obj_air_temp,
	}  
    return render_template('index.html' , Lufttemp = obj_air_temp, Humidity = obj_hum, icon = icon_url)

@app.route("/home", methods=['GET'])
def home():
    return render_template('some_page.html')





if __name__ == "__main__":
    ui.run()
    
