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

data = ["Apple", "Banana", "Mangoes", "Grapes", "Kiwi", "Orange"]

def create_weather_chart():
    #todo save a IMAGE of the Weather in the Images Folder
    pass

def get_weather_store_in_data(data):
    #todo get Weather from influx and store it in the Context to refresh the / Route and show the weather
    data = data

def update_data():
    print('Update Data from database')
    data.append("Data")
    return app.render_template('some_page.html')

@app.route("/")
async def hello():
    # todoo check if the database has old data if yes then update it and afterwards load the homepage
    context = {
	    'fruits' : data,
	}  
    return render_template('index.html' , fruits = data)

@app.route("/home", methods=['GET'])
def home():
    return render_template('some_page.html')

@app.before_first_request
def get_data():
    weatherimport.set_up_weather()
    t=threading.Thread(target=get_data_continuesly)
    t.start()
    return

def get_data_continuesly():
    weatherimport.read_data_continuesly()



if __name__ == "__main__":
    ui.run()
    
