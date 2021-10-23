import weatherdata as wd

config = wd.Config()


def read_data_continuesly():
  wd.connect_db(config)
  wd.import_latest_data(config, periodic_read=True)
  return True



def set_up_weather():
  wd.connect_db(config)
  wd.try_import_csv_file(config, 'mythenquai', '../Messwerte/messwerte_mythenquai_2007-2020.csv')
  wd.try_import_csv_file(config, 'tiefenbrunnen', '../Messwerte/messwerte_tiefenbrunnen_2007-2020.csv')
  wd.import_latest_data(config, periodic_read=False)
  return True



if __name__ == '__main__':
  pass