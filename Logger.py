import threading
import  weatherdata as wd
from threading import Thread

config = wd.Config() #connect to DB





def initDB() -> tuple(bool, Exception):
    """
    Connect to DataBase and add old stats to dataBase if not loaded yet
    """

    try:
        wd.connect_db(config) #connect to DB

        wd.try_import_csv_file(config, 'mythenquai', 'messwerte_mythenquai_2007-2020.csv')
        wd.try_import_csv_file(config, 'tiefenbrunnen', 'messwerte_tiefenbrunnen_2007-2020.csv')

        return (True, None)
    except Exception as e:

        return (False, e)


#Threads

def logger():
    while True:
        try:
            wd.import_latest_data(config, periodic_read=True)

        except Exception as e:
            print("Failed to update latest weather data to dataBase:\n", e)

if __name__ == "__Main__":
    dbInit_sucess, error = initDB()

    if dbInit_sucess:
        thread_logger = Thread(target = logger)
        thread_logger.start()
        
    else:
        print("Database initialization failed:\n", error)

