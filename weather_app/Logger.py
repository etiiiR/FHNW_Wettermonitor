import weatherimport as wd
import matplotlib.pyplot as plt
import pandas as pd

wd.init()
#print(wd.get_all_measurements("mythenquai", "1d"))

#print(wd.get_measurement(wd.Measurement.Humidity, "mythenquai", "1d"))

df = wd.generate_chart_multibleSeries([wd.Measurement.Humidity, wd.Measurement.Wind_chill], "mythenquai", "1w", showPlot = True)

