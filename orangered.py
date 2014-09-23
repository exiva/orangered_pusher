#!/usr/bin/env python

import ConfigParser
import httplib2
import urllib2
import simplejson as json
from threading import Timer
import urllib
from urllib import urlencode
import time
import logging

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
		logging.info('Caught exception logging in. %s', e)
		pass

def getMe(cookie):
	http = httplib2.Http()
	headers = {'Cookie': cookie['set-cookie'],
	'User-Agent': ua}
	url = 'https://www.reddit.com/api/me.json'
	try:
		response, content = http.request(url, 'GET', headers=headers)
		# parseMe(content,cookie)
		return response, content, cookie
	except Exception, e:
		logging.info('Caught exception reading account info. %s', e)
		pass

def parseMe(d,c):
	data_json = json.loads(d)
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
		logging.info('Caught exception reading mail. %s', e)
		pass

def parseMessage(d):
	msg_json = json.loads(d)
	lastmsg_json = msg_json['data']['children'][0]['data']
	global lastmsg

	unreads = len(msg_json['data']['children'])

	if lastmsg != lastmsg_json['name']:
		lastmsg = lastmsg_json['name']
		logging.info('New Message')
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
			logging.info('Problem sending pushalot. %d: %s', pastatus, desc)
		else:
			logging.info('Pushalot message sent')
			pass
	if poenabled:
		postatus, content = sendPushover(msg, title)
		if postatus != 200:
			error_json = json.loads(content)
			desc = error_json['errors']
			logging.info('Problem sending pushover. %d: %s', postatus, desc)
		else:
			logging.info('Pushover message sent')
			pass
	if pbenabled:
		postatus, content = sendPushbullet(msg, title)
		if postatus != 200:
			logging.info('Problem sending pushbullet. %d: %s', pbstatus, desc)
		else:
			logging.info('Pushbullet message sent')
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
		logging.info('Problem sending pushalot. %s', e)
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
		logging.info('Problem sending pushover. %s', e)
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
		logging.info('Problem sending pushbullet. %s', e)
		pass

def run(c):
	while True:
		if c['status'] != '200':
			logging.info('Problem logging in to reddit. Trying again.')
			time.sleep(poll)
			c = loginReddit(user, passwd)
			pass
		elif c['status'] == '200':
			c, r, s = getMe(c)
			if c['status'] == '200':
				parseMe(r, s)
			time.sleep(poll)
		pass

if __name__ == '__main__':
	ua = 'orangered_pusher/0.0.6 by /u/exiva'

	settings     = loadCfg('settings.cfg')
	user         = settings.get('reddit','username')
	passwd       = settings.get('reddit', 'password')
	poll         = settings.getint('reddit','poll')
	msgtitle     = settings.get('global', 'title')
	msgbody      = settings.get('global', 'body')
	msgbodym     = settings.get('global', 'multibody')
	pushurl      = settings.get('global', 'url')
	pushurltitle = settings.get('global', 'urltitle')
	logfile      = settings.get('global', 'log')
	paenabled    = settings.getboolean('pushalot', 'enabled')
	paauthtoken  = settings.get('pushalot','token')
	pattl        = settings.get('pushalot', 'ttl')
	paimg        = settings.get('pushalot', 'image')
	poenabled    = settings.getboolean('pushover', 'enabled')
	pousrkey     = settings.get('pushover', 'key')
	pbenabled    = settings.getboolean('pushbullet', 'enabled')
	pbtoken      = settings.get('pushbullet', 'token')

	logging.basicConfig(filename=logfile, level=logging.INFO)

	print "Starting {}.\n...Trying to login with {}...".format(ua, user)
	cookie = loginReddit(user, passwd)
	lastmsg = 'none';

	if cookie['status'] == '200':
		print "Logged in, Checking for new mail."
		run(cookie)
	else:
		print "Couldn't log in. Check credentials and try again."
