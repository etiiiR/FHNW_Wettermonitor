import weatherdata as wd

config = wd.Config()

wd.connect_db(config)

wd.try_import_csv_file(config, 'mythenquai', 'messwerte_mythenquai_2007-2020.csv')
wd.try_import_csv_file(config, 'tiefenbrunnen', 'messwerte_tiefenbrunnen_2007-2020.csv')
