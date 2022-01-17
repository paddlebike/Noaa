"""Retrieve the river conditions for the requested gauge."""

__author__    = 'Ken Andrews <paddlebike@google.com>'
__copyright__ = 'Copyright (c) 2013'
__license__   = 'Apache License, Version 2.0'

import logging
import json
import math
import requests


def get_bounding_box(latitude_in_degrees, longitude_in_degrees, half_side, kilometers=False):
	"""
	Calculates a bounding box based ona location, distance and kilometers/miles
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

class NWIS_Gauge_Reading:
	"""Container for stream gauge reading"""

	def __init__(self, value):
		self.value = value

class NWIS_Gauge:
	"""A container for stream gauge data"""

	def __init__(self, timeseries):
		try:
			self.code     = timeseries[u'variable'][u'variableCode'][0][u'value']
			self.desc     = timeseries[u'variable'][u'variableDescription']
			self.name     = timeseries[u'variable'][u'unit'][u'unitCode']
			self.val_list = timeseries[u'values'][0][u'value']
		except Exception as e:
				print('Exception %s processing Site %s', e, self.code)


	def __str__(self):
		out = '%s %-8s %-40s' % (self.code, self.name, self.desc)
		vl = len(self.val_list)
		
		if vl > 0:
			out += ' at %s %s' % (self.last_time, self.last)
		if vl > 1:
			out += ' prev %s' % (self.prev)
		
		return out


	@property
	def last(self):
		return self.val_list[len(self.val_list) -1][u'value']


	@property
	def prev(self):
		return self.val_list[len(self.val_list) -2][u'value']


	@property
	def last_time(self):
		return self.val_list[len(self.val_list) -1][u'dateTime']
			


class NWIS_Site:
	"""A container for stream site data"""
	def __init__(self, timeseries):
		self.gauges = {}
		self.siteCode = ''
		try:
			self.siteCode = timeseries[u'sourceInfo'][u'siteCode'][0][u'value']
			self.site_name = timeseries[u'sourceInfo'][u'siteName']
			
			self.gl = timeseries[u'sourceInfo'][u'geoLocation'][u'geogLocation']
			self.lat = float(self.gl[u'latitude'])
			self.lon = float(self.gl[u'longitude'])

		except Exception as e:
			print('Exception %s processing Site %s', e, self.siteCode)


	def __str__(self):
		out = "Site %s Name  %s Latitude %f Longititde %f.\n" % (self.siteCode,  self.site_name, self.lat, self.lon)
		out += 'Gauges:\n'
		for id in self.gauges.keys():
			out += '%s\n' % (self.gauges[id])
		return out

	def add_gauge(self, gauge):
		self.gauges[gauge.code] = gauge

	def gauge_strings(self):
		gauges = 'Gauges:'
		for id in self.gauges.keys():
			gauge = self.gauges[id]
			gauges += '\n%s' % (gauge)


class NWIS:
	"""A class for SOAP interfacing with USGS site"""

	def __init__(self):
		"""Contstructor for Rivergauge."""
		self.log = logging.getLogger('Rivergauge')
		self.log.debug("called.")


	def query_nwis(self, nwis_url):
		"""
		Fetches the json gauge data and parses part of it.
		Takes the NWIS URL.
		"""	
		self.log.info("URL is %s", nwis_url)
		r  = requests.get(nwis_url, timeout=90)
		db = json.loads(r.text)
		r.close()

		ts    = db[u'value'][u'timeSeries']
		sites = {}

		for item in ts:
			try:
				site = NWIS_Site(item)
				if not site.siteCode in sites.keys():
					sites[site.siteCode] = site
				gauge = NWIS_Gauge(item)
				sites[site.siteCode].add_gauge(gauge)
				
			except Exception as e:
				print('Exception %s processing' % (e))
		return sites


	def query_by_site_id(self, site_id):
		"""
		Fetches the json site and parses part of it.
		Takes the site ID.
		"""
		self.log.debug("called with gauge %s.", site_id)
		nwis_url = 'https://waterservices.usgs.gov/nwis/iv/?period=P1D&format=json&sites=' + site_id
		return self.query_nwis(nwis_url)


	def query_by_site_id_list(self, site_id_list):
		"""
		Fetches the json gauge and parses part of it.
		Takes a list of site numbers.
		"""
		if len(site_id_list) > 0:
			sites = ','.join(site_id_list)
			self.log.debug("called with gauge %s.", sites)
			nwis_url = 'https://waterservices.usgs.gov/nwis/iv/?period=P1D&format=json&sites=' + sites
			
		return self.query_nwis(nwis_url)

	def query_by_bbox(self, west, south, east, north):
		"""
		Fetches the json site and parses part of it.
		Takes the geobox co-ordinates.
		"""
		nwis_url = 'https://waterservices.usgs.gov/nwis/iv/?period=P1D&format=json&bBox=%f,%f,%f,%f' % (west, south, east, north)
		return self.query_nwis(nwis_url)


	def query_by_radius(self, lat, lon, distance, kilometers=False):
		"""
		Fetches the json site and parses part of it.
		Takes the radius.
		"""
		(west, south, east, north) = get_bounding_box(lat, lon, distance, kilometers)
		nwis_url = 'http://waterservices.usgs.gov/nwis/iv/?period=P1D&format=json&bBox=%f,%f,%f,%f' % (west, south, east, north)
		return self.query_nwis(nwis_url)
		

if __name__ == '__main__':
	log = logging.logger = logging.getLogger('Rivergauge')
	logging.basicConfig(format='%(asctime)s - %(name)s - %(funcName)s - %(message)s', level=logging.INFO)
	log.debug('About to instantiate Rivergauge')

	rg  = NWIS()

	print('\n\n=============================================\n')
	print('              Gauges within 30 Miles')
	sites = rg.query_by_radius(38.96, -77.45, 15)
	for site_id in sites.keys():
		print(str(sites[site_id]))

	print('\n\n=============================================\n')
	print('              Gauges in Bounded Box')
	sites = rg.query_by_bbox(-78.0,38.0,-77.5,39.3)
	for site_id in sites.keys():
		print(str(sites[site_id]))

	print('\n\n=============================================\n')
	print('              Multiple Sites')
	sites = rg.query_by_site_id_list(['01646500','01643700'])
	for site_id in sites.keys():
		print(str(sites[site_id]))


	print('\n\n=============================================\n')
	print('              Single Site')
	sites = rg.query_by_site_id('01646500')
	for site_id in sites.keys():
		print(str(sites[site_id]))
	
