import  weatherdata as wd

config = wd.Config()
wd.connect_db(config)
print(wd.get_entries(config, "mythenquai", "1d")) #example of extracting a pandas dataframe from dataBase