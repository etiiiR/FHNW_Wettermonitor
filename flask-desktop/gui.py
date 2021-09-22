from flaskwebgui import FlaskUI
from main import app

FlaskUI(app, fullscreen=True, width=600, height=500, start_server='flask').run()
