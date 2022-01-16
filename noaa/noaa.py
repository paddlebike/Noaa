#! /usr/bin/python
"""Retrieve the weather report for the requested location."""

__author__    = 'Ken Andrews <paddlebike@google.com>'
__copyright__ = 'Copyright (c) 2013'
__license__   = 'Apache License, Version 2.0'

import logging
import requests
from xml.dom import minidom

class NoaaClass:
	"""A class for SOAP interfacing with NOAA weather reports"""

	def __init__(self):
		"""Contstructor for NoaaClass."""
		self.log = logging.getLogger('NoaaClass')
		self.log.debug("called.")
		self.weather        = {}

	def query_by_lat_lon(self, lat, lon):
		"""
		Fetches the XML weather report and parses part of it.
		Takes the latitude and longetude of a point in the USA.
		"""
		self.log.info("called with lat %f, lon %f.", lat, lon)
		NOAA_WEATHER_URL = 'http://forecast.weather.gov/MapClick.php?lat={0}&lon=-{1}&unit=0&lg=english&FcstType=dwml'.format(lat, lon)
		self.log.debug("URL is %s", NOAA_WEATHER_URL)
		r = requests.get(NOAA_WEATHER_URL)

		dom     = minidom.parseString(r.text)
		r.close()

		weather_data    = dom.getElementsByTagName('data')
		forecast_params = None
		current_params  = None
		time_layout     = None

		# Get the forecast and current data 
		for i in range(0,weather_data.length):
			data_type = weather_data[i].getAttribute('type')
			if data_type == 'forecast':
				forecast_params = weather_data[i].getElementsByTagName('parameters')[0]
				time_layout     = weather_data[i].getElementsByTagName('time-layout')
			elif data_type == 'current observations':
				current_params  = weather_data[i].getElementsByTagName('parameters')[0]
			

		wordedForecast  = forecast_params.getElementsByTagName('wordedForecast')[0]
		timeElement     = wordedForecast.getAttribute('time-layout')
		strings         = wordedForecast.getElementsByTagName('text')
		timeStrings     = None


		# Find the time parameters that have the correct strings for the worded forecast
		for i in range(0, time_layout.length):
			tl =  time_layout[i].getElementsByTagName('layout-key')
			if (tl[0].firstChild.data == timeElement):
				timeStrings = time_layout[i].getElementsByTagName('start-valid-time')

		# Get the current temp, dew point and condition
		current            = {}
		current_temps      = current_params.getElementsByTagName('temperature')
		current_weather    = current_params.getElementsByTagName('weather')[0].getElementsByTagName('weather-conditions')
		current['summary'] = current_weather[0].getAttribute('weather-summary')

		for i in range(0, current_temps.length):
			data_type = current_temps[i].getAttribute('type')
			if data_type == 'apparent':
				current['apparent'] = current_temps[i].getElementsByTagName('value')[0].firstChild.data
			elif data_type == 'dew point':
				current['dew_point'] = current_temps[i].getElementsByTagName('value')[0].firstChild.data


		forecast = []
		for i in range(0, timeStrings.length):
			period = {}
			period['text']        = strings[i].firstChild.data
			period['period-name'] = timeStrings[i].getAttribute('period-name')
			forecast.append(period)

		self.weather['current']  = current
		self.weather['forecast'] = forecast

		return True
	@property
	def current(self):
		"""
		Returns a dictionary with the apparent and dew-point temperatures in
		farenheit.
		"""
		self.log.debug(" called.")
		if 'current' in self.weather.keys():
			return self.weather['current']
		return None


	@property
	def forecast(self):
		"""
		Returns a list of periods each containing a period name and the 
		forecast text.
		"""
		self.log.debug(" called.")
		if 'forecast' in self.weather.keys():
			return self.weather['forecast']
		return None

	@property
	def report(self):
		"""
		Returns a dictionary with the apparent and dew-point temperatures in
		farenheight. and a list of periods each containing a period name and the 
		forecast text.
		"""
		return self.weather

	@property
	def temp(self):
		if 'current' in self.weather.keys():
			return self.weather['current']['apparent']

	@property
	def dewpoint(self):
		if 'current' in self.weather.keys():
			return self.weather['current']['dew_point']
			

	@property
	def summary(self):
		if 'current' in self.weather.keys():
			return self.weather['current']['summary']

if __name__ == '__main__':
	log = logging.logger = logging.getLogger('noaa_main')

	logging.basicConfig(format='%(asctime)s - %(name)s - %(funcName)s - %(message)s', level=logging.DEBUG)
	log.debug('About to instantiate NoaaClass')

	noaa = NoaaClass()
	try:
		noaa.query_by_lat_lon(38.95,77.343)
	except Exception as e:
		print('Unable to get the weather from NOAA.  Make sure you have the right lat.long\n%s\n' % e)
		exit()
	
	print('---------------------------------------------------------------------')
	print("Currently {0} temperature {1} degrees dew point {2}".format(noaa.summary, noaa.temp, noaa.dewpoint))
	print('---------------------------------------------------------------------\n')

	log.debug('About to get_forecast')
	for fc in noaa.forecast:
		print("{0}\n{1}\n".format(fc['period-name'], fc['text']))

	print('---------------------------------------------------------------------\n')

