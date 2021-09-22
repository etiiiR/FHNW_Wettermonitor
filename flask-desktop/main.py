from flask import Flask  
from flask import render_template
from flaskwebgui import FlaskUI

app = Flask(__name__)
ui = FlaskUI(app, width=1000, height=700) 


@app.route("/")
def hello():
    fruits = ["Apple", "Banana", "Mangoes", "Grapes", "Kiwi", "Orange"]
    context = {
	    'fruits' : fruits,
	}  
    return render_template('index.html',  fruits=fruits)

@app.route("/home", methods=['GET'])
def home(): 
    return render_template('some_page.html')


if __name__ == "__main__":
    ui.run()
   
