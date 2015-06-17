#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib2
import json
import time
import os # for os.stat
import sys
import sqlite3
import struct
from nbt import *

config = {}
tppibasedir = '/home/minecraft/tppi-production/'
mcmabasedir = '/home/minecraft/mcma/'
#redditUrl = '38vl93'
redditUrls = ( ('feedthebeastservers', '3a04gn'), ('TestPackPleaseIgnore', '3a0cbr'))
mailTo = ('lwood262','Hastwell')

def callWrapper(fn):
	if fn == None:
		print 'helpop [BaconBot] CallWrapper Assert: Null Function'
		return None
	else:
		try:
			return fn()
		except Exception as e:
			if len(sys.argv) >= 2 and sys.argv[1] == 'raise':
				raise e
			else:
				print 'helpop [BaconBot] %s in %s - %s' % (type(e).__name__, fn.__name__, str(e.args) if len(e.args) > 0 else '[no info provided]')
				return None
def loadConfig():
	f = open(mcmabasedir + 'Exec/baconbot.conf')
	global config
	config = json.loads(f.read())
	f.close()
def saveConfig():
	f = open(mcmabasedir + 'Exec/baconbot.conf','w')
	f.write(json.dumps(config))
	f.close()
def redditBot():
	for i in redditUrls: readReddit(i[0],i[1])

def readReddit(subreddit, redditUrl):
	# form a proper request to add a custom useragent
	#url = 'http://www.reddit.com/r/feedthebeastservers/comments/31e6mv.json?depth=1'
	url = 'http://www.reddit.com/r/' +subreddit+ '/comments/' +redditUrl+ '.json?depth=1'
	#url = '/mnt/uxiesan/Sourcecode/Bacon-HousekeepBot/redditApi-depth1.json'

	reddit = json.loads( wget(url) )
	
	cutoffdate = config['reddit.lastcheck']
	anyFound = False
	
	#reddit[1]['data']['children'][i]['data']
	for i in reddit[1]['data']['children']:
		if i['data']['created_utc'] < cutoffdate: continue
		
		anyFound = True
		cutofflength = 60
		
		# whitespace/newline/ "&" colorcoding defeating
		i['data']['body'] = i['data']['body'].replace('\n', ' ').replace('   ', ' ').replace('  ', ' ').replace('&', '&&')
		
		# preformat time
		i['data']['postdate'] = time.strftime('%d %b %H:%M %Z', time.localtime(i['data']['created_utc']) )
		
		# cut off post if it exceeds arbitrary maximum defined in cutofflength
		if len(i['data']['body']) > cutofflength: i['data']['body'] = i['data']['body'][0:cutofflength] + '...'
		
		# say the goddamn thing
		print "helpop [BaconBot Reddit] http://redd.it/" +redditUrl+ ": %(author)s on %(postdate)s - %(body)s" % i['data']#['author']
		for user in mailTo:
			print "w " +user+ " [BB Reddit] http://redd.it/" +redditUrl+ ": %(author)s on %(postdate)s - %(body)s" % i['data']
			print "mail send " +user+ " [BB Reddit] http://redd.it/" +redditUrl+ ": %(author)s on %(postdate)s - %(body)s" % i['data']
		#print '\t' + str(time.localtime(i['data']['created_utc']))
		#print '\t' + i['data']['postdate']
	
	if anyFound:
		print 'helpop [BaconBot Reddit] http://redd.it/' +redditUrl+ ' to reply'
	else:
		pass
		#print 'helpop [BaconBot Reddit] No Posts This Time :('

	config['reddit.lastcheck'] = time.time()
	saveConfig()
	

def wget(url):
	if url.startswith('http:') or url.startswith('https:'):
		useragent = "BaconBot/0.1 (+bacongaming.net by Hastwell) urllib/2.0"	
		req = urllib2.Request(url, headers={'User-Agent': useragent})
		response = urllib2.urlopen(req)
		return response.read()
	else:
		f = open(url)
		dta = f.read()
		f.close()
		return dta

#chunkBot()
callWrapper(loadConfig)
callWrapper(redditBot)
