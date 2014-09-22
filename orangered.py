#!/usr/bin/env python

import ConfigParser
import httplib2
import urllib2
import simplejson as json
from threading import Timer
import urllib
from urllib import urlencode
import time

def loadCfg(settings):
	config = ConfigParser.ConfigParser()
	config.read(settings)
	return config

def loginReddit(u,p):
	http = httplib2.Http()
	url = 'https://www.reddit.com/api/login'
	body = {'user': u, 'passwd': p}
	headers = {'Content-type': 'application/x-www-form-urlencoded',
	'User-Agent': ua}
	try:
		response, content = http.request(url, 'POST', headers=headers, body=urllib.urlencode(body))
		return response
	except Exception, e:
		print "Login barfed"
		pass

def getMe(cookie):
	http = httplib2.Http()
	headers = {'Cookie': cookie['set-cookie'],
	'User-Agent': ua}
	url = 'https://www.reddit.com/api/me.json'
	try:
		content = http.request(url, 'GET', headers=headers)
		parseMe(content,cookie)

	except Exception, e:
		print "Reading barfed"
		pass

def parseMe(d,c):
	data_json = json.loads(d[1])
	data = data_json['data']

	if data['has_mail'] or data['has_mod_mail']:
		getMessages(c)

def getMessages(cookie):
	http = httplib2.Http()
	headers = {'Cookie': cookie['set-cookie'],
	'User-Agent': ua}
	url = 'https://www.reddit.com/message/unread.json'
	try:
		resp, content = http.request(url, 'GET', headers=headers)
		parseMessage(content)
	except Exception, e:
		print e
		pass

def parseMessage(d):
	msg_json = json.loads(d)
	lastmsg_json = msg_json['data']['children'][0]['data']
	global lastmsg

	unreads = len(msg_json['data']['children'])

	if lastmsg != lastmsg_json['name']:
		lastmsg = lastmsg_json['name']
		print "New Message!"
		if unreads > 1:
			pushdispatcher("{0:d} {1:s}".format(unreads,msgbodym))
			pass
		else:
			pushdispatcher(msgbody)

def pushdispatcher(msg):
	title = "{0:s} ({1:s})".format(msgtitle, user)
	if paenabled:
		pastatus, content = sendPushalot(msg, title)
		if pastatus != 200:
			error_json = json.loads(content)
			desc = error_json['Description']
			print "ERROR: Pushalot Server returned error: {0:d}: {1:s}".format(
			pastatus, desc)
		else:
			print "Pushalot message sent"
			pass
	if poenabled:
		postatus, content = sendPushover(msg, title)
		if postatus != 200:
			error_json = json.loads(content)
			desc = error_json['errors']
			print "ERROR: Pushover Server returned error: {0:d}: {1:s}".format(
			postatus, desc)
		else:
			print "Pushover message sent"
			pass
	if pbenabled:
		postatus, content = sendPushbullet(msg, title)
		if postatus != 200:
			print "ERROR: Pushbullet Server returned error: {0:d}: {1:s}".format(
			postatus)
		else:
			print "Pushbullet message sent"
			pass

def sendPushalot(b, t):
	http = httplib2.Http()
	url = 'https://pushalot.com/api/sendmessage'
	headers = {'Content-type': 'application/x-www-form-urlencoded',
	'User-Agent': ua}
	body = {
		'AuthorizationToken': paauthtoken,
		'Title': t,
		'Body': b,
		'Image': paimg,
		'TimeTolive': pattl,
		'Link': pushurl,
		'LinkTitle': pushurltitle
	}
	try:
		resp, cont = http.request(url, 'POST', headers=headers, body=urllib.urlencode(body))
		return int(resp['status']), cont
	except Exception, e:
		pass

def sendPushover(b, t):
	http = httplib2.Http()
	url = 'https://api.pushover.net/1/messages.json'
	headers = {'Content-type': 'application/x-www-form-urlencoded',
	'User-Agent': ua}
	body = {
		'token': 'aU9TRhEJD1fubJiQAKFmQfvkcQd3q9',
		'user': pousrkey,
		'title': t,
		'message': b,
		'url': pushurl,
		'url_title': pushurltitle
	}
	try:
		resp, cont = http.request(url, 'POST', headers=headers, body=urllib.urlencode(body))
		return int(resp['status']), cont
	except Exception, e:
		pass

def sendPushbullet(b, t):
	http = httplib2.Http()
	url = 'https://api.pushbullet.com/v2/pushes'
	headers = {'Content-type': 'application/x-www-form-urlencoded',
	'User-Agent': ua}
	http.add_credentials(pbtoken, '')
	body = {
		'type': 'link',
		'title': t,
		'body': b,
		'url': pushurl
	}
	try:
		resp, cont = http.request(url, 'POST', headers=headers, body=urllib.urlencode(body))
		return int(resp['status']), cont
	except Exception, e:
		pass

if __name__ == '__main__':
	ua = 'orangered_pusher/0.0.5 by /u/exiva'

	settings     = loadCfg('settings.cfg')
	user         = settings.get('reddit','username')
	passwd       = settings.get('reddit', 'password')
	poll         = settings.getint('reddit','poll')
	msgtitle     = settings.get('global', 'title')
	msgbody      = settings.get('global', 'body')
	msgbodym     = settings.get('global', 'multibody')
	pushurl      = settings.get('global', 'url')
	pushurltitle = settings.get('global', 'urltitle')
	paenabled    = settings.getboolean('pushalot', 'enabled')
	paauthtoken  = settings.get('pushalot','token')
	pattl        = settings.get('pushalot', 'ttl')
	paimg        = settings.get('pushalot', 'image')
	poenabled    = settings.getboolean('pushover', 'enabled')
	pousrkey     = settings.get('pushover', 'key')
	pbenabled    = settings.getboolean('pushbullet', 'enabled')
	pbtoken      = settings.get('pushbullet', 'token')

	cookie = loginReddit(user, passwd)
	lastmsg = 'none';

	#Crude way to run forever. Maybe there's a better way.
	while True:
		if cookie == 0 or cookie['status'] != '200':
			print "Problem logging in. Trying again."
			time.sleep(poll)
			cookie = loginReddit(user, passwd)
			pass
		elif cookie['status'] == '200':
			getMe(cookie)
			time.sleep(poll)
		pass
