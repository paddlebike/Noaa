===========
NOAA Utilities
===========

Simplifies accessing weather and river data from NOAA and USGS usage
often looks like this::

    #!/usr/bin/env python

    from noaa import NoaaClass
       noaa = NoaaClass()
	try:
		noaa.query_by_lat_lon(38.95,77.343)
	except:
		print 'Unable to get the weather from NOAA.  Make sure you have the right lat.long'
		exit()
	
	print '---------------------------------------------------------------------'
	print "Currently {0} temperature {1} degrees dew point {2}".format(noaa.summary, noaa.temp, noaa.dewpoint)
	print '---------------------------------------------------------------------\n'

	for fc in noaa.forecast:
		print "{0}\n{1}\n".format(fc['period-name'], fc['text'])

	print '---------------------------------------------------------------------\n'


