#!/usr/bin/env python

import ConfigParser
import httplib2
import urllib2
import simplejson as json
from threading import Timer
import urllib
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
	except Exception, e:
		logging.info('Caught exception logging in. %s', e)
	else:
		return response

def getMe(cookie):
	http = httplib2.Http()
	headers = {'Cookie': cookie['set-cookie'],
	'User-Agent': ua}
	url = 'https://www.reddit.com/api/me.json'
	try:
		response, content = http.request(url, 'GET', headers=headers)
	except Exception, e:
		logging.info('Caught exception reading account info. %s', e)
		return None, None
	else:
		return response, content

def getMessages(cookie):
	http = httplib2.Http()
	headers = {'Cookie': cookie['set-cookie'],
	'User-Agent': ua}
	url = 'https://www.reddit.com/message/unread.json'
	try:
		resp, content = http.request(url, 'GET', headers=headers)
	except Exception, e:
		logging.info('Caught exception reading mail. %s', e)
	else:
		parseMessage(content)


def parseMessage(d):
	try:
		msg_json = json.loads(d)
	except json.JSONDecodeError, e:
		logging.error('Error parsing json. %s', e)
	else:
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

def parseMe(c,d):
	try:
		data_json = json.loads(d)
	except json.JSONDecodeError, e:
		logging.error('Error parsing json. %s', e)
	else:
		data = data_json['data']

		if data['has_mail'] or data['has_mod_mail']:
			getMessages(c)

def pushdispatcher(msg):
	title = "{0:s} ({1:s})".format(msgtitle, user)
	if paenabled:
		sendPushalot(msg, title)
	if poenabled:
		sendPushover(msg, title)
	if pbenabled:
		sendPushbullet(msg, title)

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
	except Exception, e:
		logging.info('Problem sending pushalot. %s', e)
	else:
		if int(resp['status']) != 200:
			try:
				error_json = json.loads(cont)
			except json.JSONDecodeError:
				logging.error('Couldn\'t decode json')
			else:
				desc = error_json['Description']
				logging.info('Problem sending pushalot. %s: %s', resp['status'], desc)
		else:
			logging.info('Pushalot message sent')
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
	except Exception, e:
		logging.error('Problem sending pushover. %s', e)
	else:
		if int(resp['status']) != 200:
			try:
				error_json = json.loads(cont)
			except json.JSONDecodeError:
				logging.error('Couldn\'t decode json')
			else:
				desc = error_json['errors']
				logging.error('Problem sending pushover. %s: %s', resp['status'], desc)
		else:
			logging.info('Pushover message sent')
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
	except Exception, e:
		logging.error('Problem sending pushbullet. %s', e)
	else:
		if int(resp['status']) != 200:
			try:
				error_json = json.loads(cont)
			except json.JSONDecodeError:
				logging.error('Couldn\'t decode json')
			else:
				desc = error_json['error']['message']
				logging.error('Problem sending pushbullet. %s: %s', resp['status'], desc)
		else:
			logging.info('Pushbullet message sent')
			pass


def run(cookie):
	while True:
		c,r = getMe(cookie)
		if c is None:
			logging.error("Got no response, reddit is likely down.")
			time.sleep(poll)
			cookie = loginReddit(user, passwd)
		if c['status'] != '200':
			logging.error("Reddit threw error %s. Trying to login", c['status'])
			time.sleep(poll)
			cookie = loginReddit(user, passwd)
		elif c['status'] == '200':
			parseMe(cookie,r)
			time.sleep(poll)

if __name__ == '__main__':
	ua = 'orangered_pusher/0.0.9 by /u/exiva'

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
	lastmsg = 'none';

	cookie = loginReddit(user, passwd)

	if cookie is None:
		print "Got no response, Reddit is likely down. Try again."
	else:
		if cookie['status'] == '200':
			print "Logged in, Checking for new mail."
			run(cookie)
		else:
			print "Couldn't log in. Check credentials and try again."
