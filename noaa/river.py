#! /usr/bin/python
"""Retrieve the river conditions for the requested gauge."""

__author__    = 'Ken Andrews <paddlebike@google.com>'
__copyright__ = 'Copyright (c) 2013'
__license__   = 'Apache License, Version 2.0'

import logging
import urllib2, re
import json
import math


def get_bounding_box(latitude_in_degrees, longitude_in_degrees, half_side, kilometers=False):
	"""
	Calcalates a bounding box based ona location, distance and kilometers/miles
	Returns a bounding box made up of the tuples (west, south, east, north)
	"""
	assert half_side > 0
	assert latitude_in_degrees  >= -180.0 and latitude_in_degrees  <= 180.0
	assert longitude_in_degrees >= -180.0 and longitude_in_degrees <= 180.0

	if kilometers:
		half_side_in_km = half_side
	else:
		half_side_in_km = half_side * 1.609344

	lat = math.radians(latitude_in_degrees)
	lon = math.radians(longitude_in_degrees)

	radius  = 6373
	# Radius of the parallel at given latitude
	parallel_radius = radius*math.cos(lat)

	lat_min = lat - half_side_in_km/radius
	lat_max = lat + half_side_in_km/radius
	lon_min = lon - half_side_in_km/parallel_radius
	lon_max = lon + half_side_in_km/parallel_radius
	rad2deg = math.degrees

	west  = rad2deg(lon_min)
	south = rad2deg(lat_min)
	east  = rad2deg(lon_max)
	north = rad2deg(lat_max)
	return (west, south, east, north)

def distance_on_unit_sphere(lat1, long1, lat2, long2, kilometers=False):
	"""
	Convert latitude and longitude to 
	spherical coordinates in radians.
	"""
	degrees_to_radians = math.pi/180.0
	    
	# phi = 90 - latitude
	phi1 = (90.0 - lat1)*degrees_to_radians
	phi2 = (90.0 - lat2)*degrees_to_radians
	    
	# theta = longitude
	theta1 = long1*degrees_to_radians
	theta2 = long2*degrees_to_radians
	    
	# Compute spherical distance from spherical coordinates.
	    
	# For two locations in spherical coordinates 
	# (1, theta, phi) and (1, theta, phi)
	# cosine( arc length ) = 
	#    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
	# distance = rho * arc length

	cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
	       math.cos(phi1)*math.cos(phi2))
	arc = math.acos( cos )

	# Remember to multiply arc by the radius of the earth 
	# in your favorite set of units to get length.
	if kilometers:
		return arc * 6373
	return arc * 3960

class Rivergauge:
	"""A class for SOAP interfacing with USGS site"""

	def __init__(self):
		"""Contstructor for Rivergauge."""
		self.log = logging.getLogger('Rivergauge')
		self.log.debug("called.")
		self.gauges = {}


	def query_nwis(self, nwis_url):
		"""
		Fetches the json gauge data and parses part of it.
		Takes the NWIS URL.
		"""	
		self.log.info("URL is %s", nwis_url)
		handler  = urllib2.urlopen(nwis_url, timeout=90)
		json_str = handler.read()
		db       = json.loads(json_str)
		handler.close()

		ts    = db[u'value'][u'timeSeries']
		self.gauges = {}

		for item in ts:
			try:
				new_gauge  = {}
				# Get some basic data about the gauge.
				siteCode = item[u'sourceInfo'][u'siteCode'][0][u'value'].encode('latin-1')
				if not siteCode in self.gauges.keys():
					site_name = item[u'sourceInfo'][u'siteName'].encode('latin-1')
					
					gl = item[u'sourceInfo'][u'geoLocation'][u'geogLocation']
					lat = float(gl[u'latitude'])
					lon = float(gl[u'longitude'])

					self.log.debug("Site %s Name  %s Latitude %f Longititde %f.", siteCode,  site_name, lat, lon) 
					self.gauges[siteCode] = {'siteCode':siteCode, 'lat':lat,'lon':lon,'site_name':site_name,'reading':{}}


				type_num = item[u'variable'][u'variableCode'][0][u'value']
				desc     = item[u'variable'][u'variableDescription'].encode('latin-1')
				name     = item[u'variable'][u'unit'][u'unitAbbreviation'].encode('latin-1')
				valList  = item[u'values'][0][u'value']
				value    = valList[len(valList) -1][u'value']
				time     = valList[len(valList) -1][u'dateTime'].encode('latin-1')
				prevVal  = valList[len(valList) -2][u'value']

				self.log.debug('type:%s  Name:%s  Value:%s  Prev:%s at %s', type_num, name,  value, prevVal, time)

				self.gauges[siteCode]['reading'][name] = {'type':type_num, 'description':desc, 'time':time, 'value':value, 'prevVal':prevVal}
			except:
				self.log.debug('Exception processing %s', str(item))

	def query_by_gauge(self, gauge):
		"""
		Fetches the json gauge and parses part of it.
		Takes the gauge number.
		"""
		self.log.debug("called with gauge %s.", gauge)
		nwis_url = 'http://waterservices.usgs.gov/nwis/iv/?period=P1D&format=json&sites=' + gauge
		self.query_nwis(nwis_url)
		return self.gauges

	def query_by_gauges(self, gaugeList):
		"""
		Fetches the json gauge and parses part of it.
		Takes the gauge number.
		"""
		if len(gaugeList) > 0:
			gauge = ','.join(gaugeList)
			self.log.debug("called with gauge %s.", gauge)
			nwis_url = 'http://waterservices.usgs.gov/nwis/iv/?period=P1D&format=json&sites=' + gauge
			self.query_nwis(nwis_url)
		return self.gauges

	def query_by_bbox(self, west, south, east, north):
		"""
		Fetches the json gauge and parses part of it.
		Takes the gauge number.
		"""
		nwis_url = 'http://waterservices.usgs.gov/nwis/iv/?period=P1D&format=json&bBox=%f,%f,%f,%f' % (west, south, east, north)
		self.query_nwis(nwis_url)
		return self.gauges

	def query_by_radius(self, lat, lon, distance, kilometers=False):
		"""
		Fetches the json gauge and parses part of it.
		Takes the gauge number.
		"""
		(west, south, east, north) = get_bounding_box(lat, lon, distance, kilometers)
		nwis_url = 'http://waterservices.usgs.gov/nwis/iv/?period=P1D&format=json&bBox=%f,%f,%f,%f' % (west, south, east, north)
		self.query_nwis(nwis_url)
		return self.gauges

	def site_data_str(self, site):
		""" print the USGS Site Data"""
		out = ''
		keys = site['reading'].keys()
		if 'ft' in keys:
			out +=  '%s : %s located at latitude %f longitude %f\n' % (site['siteCode'], site['site_name'], site['lat'], site['lon'])
			ft      = float(site['reading']['ft']['value'])
			ft_prev = float(site['reading']['ft']['prevVal'])
			out += 'Currently at %s feet ' % site['reading']['ft']['value']
			if 'cfs' in keys:
				out += '(%s CFS) ' % site['reading']['cfs']['value']
			if ft > ft_prev:
				out += 'Rising   '
			elif ft < ft_prev:
				out += 'Failling '
			else:
				out += 'Holding  '
			if 'deg C' in keys:
				out += 'Temp (centegrade) %f ' % float(site['reading']['deg C']['value'])
		return out


		

if __name__ == '__main__':
	log = logging.logger = logging.getLogger('Rivergauge')
	#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	logging.basicConfig(format='%(asctime)s - %(name)s - %(funcName)s - %(message)s', level=logging.INFO)
	log.debug('About to instantiate Rivergauge')

	rg  = Rivergauge()

	print '\n\n============================================='
	print '              Gauges within 30 Miles'
	gauges = rg.query_by_radius(38.96, -77.45, 15)
	for site in gauges.keys():
		print(rg.site_data_str(gauges[site]) + '\n')

	print '\n\n============================================='
	print '              Gauges in Bounded Box'
	gauges = rg.query_by_bbox(-78.0,38.0,-77.5,39.3)
	for site in gauges.keys():
		print(rg.site_data_str(gauges[site]) + '\n')

	print '\n\n============================================='
	print '              Multiple Gauges'
	gauges = rg.query_by_gauges(['01646500','01643700'])
	for site in gauges.keys():
		print(rg.site_data_str(gauges[site]) + '\n')

	print '\n\n============================================='
	print '              Single Gauge'
	gauges = rg.query_by_gauge('01646500')
	for site in gauges.keys():
		print(rg.site_data_str(gauges[site]) + '\n')
	
# http://waterservices.usgs.gov/nwis/iv/?period=P7D&bBox=-78,38,-77,39&format=waterml
