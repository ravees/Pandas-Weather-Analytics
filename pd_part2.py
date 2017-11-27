#!/bin/python
# -*- coding: utf-8 -*-
#Python 2.7.12

import json
import requests
import pandas as pd
import numpy as np

APIKEY = '' # signup to API
LATITUDE = '40.756711'
LONGITUDE = '-73.976085'
#TIME = '150000000'

def get_weather_data(filename):
    URL = 'https://api.darksky.net/forecast/%s/%s,%s' % (APIKEY, LATITUDE, LONGITUDE)
    PARAMS = {'exclude':'currently,minutely,alerts,flags', 'extend':'hourly'}
    headers = {'Accept-encoding': 'gzip'}
    r = requests.get(url=URL, params=PARAMS, headers=headers)
    json_obj = json.loads(r.text)
    json_hourly_out = json.dumps(json_obj['hourly']['data'], sort_keys=True, indent=4)
    json_daily_out = json.dumps(json_obj['daily']['data'], sort_keys=True, indent=4)
    with open( filename, 'w' ) as outfile:
		outfile.write(json_hourly_out)
    print "%s file created in the current working folder" % (filename)
    return json_hourly_out, json_daily_out

def clean_weather_data(json_weather_data):
    json_df = pd.read_json(json_weather_data, orient='table', convert_dates=True)
    _columns = ['time', 'visibility', 'uvIndex', 'precipIntensity', 'dewPoint',
                'cloudCover', 'icon', 'precipType']
    df = pd.DataFrame(json_df, columns=_columns)
    df['time'] = pd.DatetimeIndex(pd.to_datetime(df['time'],
                unit='s', utc=True)).tz_convert('US/Eastern')
    df = df.set_index('time')
    upsampled = df.resample('15Min')
    df = upsampled.interpolate(method='linear')

    # To fill precipType column only when precipIntensity greater than 0
    df['icon'] = df['icon'].fillna(method='ffill')
    df2 = df
    df2['precipType'] = df['precipType'].fillna(method='ffill')
    df2['precipType'] = df['precipType'].fillna(method='bfill')
    conditions = [(pd.isnull(df['precipType'])) & (df['precipIntensity']>0),
                (df['precipIntensity']==0)]
    choices=[df2['precipType'], np.nan]
    df['precipType'] = np.select(conditions, choices, default=df['precipType'])
    df.to_csv('weather.csv', sep='\t')
    print "weather.csv file created, please check the current working folder :)"
    return df

def analyze_weather_data(json_weather_data):
    """
    Choose the day in the week which has the hightest number of occurance
     for each variance.
    """
    json_df = pd.read_json(json_weather_data, orient='table', convert_dates=True)
    _columns = ['time', 'uvIndex', 'dewPoint',
                'cloudCover', 'apparentTemperatureHigh',
                'apparentTemperatureLow', 'apparentTemperatureMax',
                'apparentTemperatureMin', 'ozone', 'humidity',
                'precipProbability', 'pressure', 'temperatureHigh', 'temperatureLow',
                'temperatureMax', 'temperatureMin', 'windGust', 'windSpeed']
    # , 'precipIntensity', 'precipIntensityMax'
    df = pd.DataFrame(json_df, columns=_columns)
    df['time'] = pd.DatetimeIndex(pd.to_datetime(df['time'],
                unit='s', utc=True)).tz_convert('US/Eastern')
    df = df.set_index('time')
    median_df = df.median()
    least_variance = {}
    least_variance_date = {}
    for index, rows in df.iterrows():
        for column in _columns:
            if column=='time':
                continue
            var_df = pd.DataFrame({'data':[median_df[column], rows[column]]})
            variance = var_df.var()
            if column not in least_variance.keys():
                least_variance[column] = variance[0]
                least_variance_date[column] = index
            else:
                if variance[0] < least_variance[column]:
                    # Record the least variance
                    least_variance[column] = variance[0]
                    least_variance_date[column] = index
    # Find date which has the hightest count of least_variance
    count_date = {}
    min_count = float("-inf")
    min_date = None
    for key,value in least_variance_date.items():
        if value not in count_date.keys():
            count_date[value] = 1
        else:
            count_date[value] += 1
            if count_date[value]>min_count:
                min_count = count_date[value]
                min_date = value
    print "Day with most similar weather to other days is: ", min_date
    return

    # TODO: Perhaps train a model using tensorflow with weather.csv input data.
def predict_weather_data():
    pass


def main():
    json_filename = "weather_data.json"
    data_hourly, data_daily = get_weather_data(json_filename)
    pandas_dataFrame = clean_weather_data(data_hourly)
    analyze_weather_data(data_daily)

if __name__ == "__main__":
    main()
