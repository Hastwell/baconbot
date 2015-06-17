#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib2
import json
import time
import os # for os.stat
import sqlite3
import MySQLdb as mdb
import json
import operator # for sorting

import struct
from nbt import *
import sys

chunkWarningThreshold = 40
mailToUsers = ('Hastwell','lwood262')
#mailToUsers = ('Hastwell',)

creativeBlocks = \
{
	(1316,0): 'Creative Supplier',
	(2005,0): 'Creative Energy Cell',
	(2006,0): 'Creative Tank',
	(2007,0): 'Creative Strongbox',
	(2151,0): 'Creative Reactor Coolant Port',
	(2151,1): 'Creative Turbine Coolant Port',
	(9318,1125): 'Creative Bedrock Barrel',
	(2668,14): 'Upgrade: Creative Mode',
	(4361,8): 'ME Creative Cell',
	# creative builder's wand left off intentionally as it lacks creative powers despite the name
	(14376,0): 'Creative Tool Modifier',
	(20261,0): 'Creative Flux Capacitor',
	(25072,7): 'Barrel Hammer (Creative)',
	(25073,10): 'Creative Upgrade',
	(29997,61): 'Creative Engine',
	(29997,72): 'Creative Tank',
	(29997,76): 'Creative Hull',
	(29997,96): 'Creative Incinerator',
	(29997,97): 'Creative Supplies',
	(431,3): 'Quantum Generator',
	(22413,0): 'Dislocation Wand Focus (Non-Creative but Banned)'
}

config = {}
tppibasedir = '/home/minecraft/tppi-production/'
configDir = '/home/minecraft/mcma/Exec/'
#configDir = '/home/hastwell/baconbot-dev/'

limitSql = ' LIMIT 0,4' if len(sys.argv) == 1 or sys.argv[1] != 'all' else ''

def callWrapper(fn):
	if fn == None:
		print 'helpop [BaconBot] CallWrapper Assert: Null Function'
		return None
	else:
		try:
			return fn()
		except Exception as e:
			print 'helpop [BaconBot] %s in %s - %s' % (type(e).__name__, fn.__name__, e.args[0] if len(e.args) > 0 else '[no info provided]')
			return None
def loadConfig():
	f = open(configDir + 'baconbot.conf')
	global config
	config = json.loads(f.read())
	f.close()
def saveConfig():
	f = open(configDir + 'baconbot.conf','w')
	f.write(json.dumps(config))
	f.close()

def chunkBot():
	baseDir = tppibasedir + 'world/data/'

	# create and provision the Chunkloaders SQLite DB in memory.
	conn = sqlite3.connect(':memory:')
	c = conn.cursor()
	c.execute("""CREATE TABLE loaders (loaderId real PRIMARY KEY, player text, dimension text, location text)""")
	c.execute("""CREATE TABLE chunks (loaderid real, location text)""")
	
	# parse the list of worlds containing dimanchors
	worldFiles = []
	f = open(baseDir + 'ICL-worlds.dat')
	numDims = struct.unpack('>i', f.read(4))
	for i in range(numDims[0]):
		dimNum = struct.unpack('>i', f.read(4))[0]
		worldFiles.append( ('ICL-DIM%d.dat' % dimNum) if dimNum != 0 else 'ICL-null.dat' )
	f.close()

	loaderId = 0
	newestICLFile = 0
	
	# friendly names for dimensions (unless you REALLY want to remember what DIM21 stands for)
	worldNameAliases = {'ICL-null.dat': 'world', 'ICL-DIM-1.dat': 'nether', 'ICL-DIM1.dat': 'end', 'ICL-DIM21.dat': 'mining', 'ICL-DIM7.dat': 'twiforest'}
	
	for h in worldFiles:
		# determine the newest chunkloader data file. Used to show the last time loaders were changed.
		if newestICLFile < os.stat(baseDir+h).st_mtime: newestICLFile = os.stat(baseDir+h).st_mtime
		dta = nbt.NBTFile(baseDir + h)
		worldname = '[parse-err %s]' % h # default name if we can't guess what dimension it's in from the filename
		# default failsafe worldname is [parse-err ICL-DIM49.dat]
		
		if h in worldNameAliases: worldname = worldNameAliases[h] # give it a friendly name if one exists for this dimension
		elif h.startswith('ICL-'): worldname = h[4:-4] # strip the ICL bit if needed
		
		for i in dta['data']['loaders']:
			player = i['owner'].value
			# the 1st digit of the owner value determines what type of loader this is (either human player, server-owned, or a corrupted loader)
			if player == '1': player = '[Server]'
			elif player == '3': player = '[Corrupted]'
			elif player.startswith('2'): player = player[1:]
			else: player = '!!UNKNOWN PLAYER "%s"' % player
			
			# add this loader and the chunks it's loading. The chunk coords loaded by this loader are also recorded so we don't double count them
			c.execute('''INSERT INTO loaders VALUES (?, ?, ?, ?)''', (loaderId, player, worldname, str(i['X'])+'x'+str(i['Y'])+"x"+str(i['Z']) ))
			for chunks in i['chunks']:
				c.execute('''INSERT INTO chunks VALUES (?, ?)''', (loaderId, str(chunks['x'].value)+':'+str(chunks['z'].value) ) )

			loaderId += 1
	print "helpop Chunkloader Stats as of %s" % time.strftime('%d %b %H:%M %Z', time.localtime(newestICLFile) )
	print "helpop Top 4 individual loaders"	
	for row in c.execute('SELECT player, count(chunks.location) as numChunks, dimension, loaders.location FROM loaders JOIN chunks ON loaders.loaderId = chunks.loaderId GROUP BY loaders.loaderId ORDER BY numChunks DESC' + limitSql):
		prefix = ''
		if row[1] > chunkWarningThreshold: prefix = '!!!'
		print 'helpop '+prefix+'   %s [%dc] at %s:%s' % row
		
	# curse SQLite not being able to do a COUNT(DISTINCT GROUP BY) easily!
	print "helpop Top 4 loading players"
	for row in c.execute('''
		SELECT player, COUNT(location) as numChunks FROM
		(
			SELECT COUNT(DISTINCT chunks.location) as location, player FROM chunks JOIN loaders ON chunks.loaderId = loaders.loaderId GROUP BY chunks.location
		)
		GROUP BY player ORDER BY numChunks DESC'''
		+limitSql):
			prefix = ''
			
			# warn players if they've gone overboard on total chunks loaded
			if row[1] > chunkWarningThreshold:
				prefix = '!!!'
				if row[0] == '[Server]':
					print "helpop [BB] /me thinks server shouldn't be loading this many chunks..."
				else:
					print "w %s [BaconBot] You're loading %d chunks, which seems like a lot. &6&lConfine chunkloaders to essential areas or consider using them more efficently. &aThank you :3" % row
			print 'helpop '+prefix+'   %s - %d chunks' % row		
	
	# retrieve total stats for the entire server
	c.execute('SELECT COUNT(DISTINCT chunks.location) FROM chunks')
	numchunks = c.fetchone()[0]

	c.execute('SELECT COUNT(*) FROM loaders')
	numloaders = c.fetchone()[0]

	print 'helpop %d total chunks loaded over %d chunkloaders' % (numchunks, numloaders)
	conn.commit()
	conn.close()
	
# run a search against prism searching for recent activity with creative blocks
def reportCreativeAboose():
	con = mdb.connect('localhost', '$sqluser', '$sqlpasswd', '$sqldb'); # yeah no, not listing my production credentials here
	cur = con.cursor()

	# get autoincrement index. get this first to ensure that we don't miss any records in the time it takes to make our second quarry
	cur.execute("SELECT AUTO_INCREMENT FROM information_schema.tables WHERE table_name = 'prism_data' AND table_schema = DATABASE()")
	nextAutoIncrement = int(cur.fetchall()[0][0])

	lastAutoIncrement = config['prism.lastautoincrement'] #13101859
	cur.execute("""	SELECT player, block_id, block_subid, COUNT(*) as transacts FROM `prism_data`
		INNER JOIN prism_players ON prism_data.player_id = prism_players.player_id
		INNER JOIN prism_actions ON prism_data.action_id = prism_actions.action_id
		LEFT JOIN prism_data_extra ON prism_data.id = prism_data_extra.data_id
		WHERE player NOT IN ('Hastwell','lwood262') AND id >= """ +str(lastAutoIncrement)+ """ AND 
		(
			"""+ " OR ".join(["(block_id = %d AND block_subid = %d)" % i for i in creativeBlocks]) +"""
		)
		GROUP BY player, block_id, block_subid""")
	# (('MicroCampaign', 2007, 0, 1L),)
	for i in cur.fetchall():
		itemName = creativeBlocks[ (i[1],i[2]) ]
		print "helpop BaconBot: %s interacted with %s [%d:%d] recently! (%d times in last ~1hr period)" % (i[0],itemName,i[1],i[2],i[3])

		for mailTo in mailToUsers:
			print "mail send %s BaconBot: %s interacted with %s [%d:%d] recently! (%d times in last ~1hr period)" % (mailTo,i[0],itemName,i[1],i[2],i[3])

	con.close()
	
	config['prism.lastautoincrement'] = nextAutoIncrement
def wget(url):
	if url.startswith('http:') or url.startswith('https:'):
		useragent = "BaconBot/0.2 (+bacongaming.net by u/Hastwell) urllib/2.0"	
		req = urllib2.Request(url, headers={'User-Agent': useragent})
		response = urllib2.urlopen(req)
		return response.read()
	else:
		f = open(url)
		dta = f.read()
		f.close()
		return dta

callWrapper(loadConfig)
callWrapper(chunkBot)
callWrapper(reportCreativeAboose)
callWrapper(saveConfig)
