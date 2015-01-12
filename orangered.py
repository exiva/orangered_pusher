#!/usr/bin/env python

import ConfigParser
import httplib2
import requests
# import urllib2
# import simplejson as json
from threading import Timer
import urllib
import time
import logging

def loadCfg(settings):
	config = ConfigParser.ConfigParser()
	config.read(settings)
	return config

def loginReddit(user,password,clientid,secret):
	url = 'https://ssl.reddit.com/api/v1/access_token'
	data = {'grant_type': 'password', 'username': user,
			'password': password}
	headers = {'User-Agent': ua}
	try:
		r = requests.post(url, data=data, auth=(clientid,secret),
							headers=headers)
	except requests.exceptions.RequestException as e:
		logging.info('Caught exception logging in. %s', e)
	else:
		try:
			data = r.json()
		except ValueError as e:
			logging.info('Caught exception logging in. %s', e)
		else:
			return data

def getMe(token,tokentype):
	url = 'https://oauth.reddit.com/api/v1/me'
	headers = {'Authorization': '{0:s} {1:s}'.format(tokentype,token),
				'User-Agent': ua}
	try:
		r = requests.get(url, headers=headers)
	except requests.exceptions.RequestException as e:
		logging.info('Caught exception reading account info. %s', e)
	else:
		return r.json(), r.status_code

def getMessages(cookie):
	http = httplib2.Http()
	headers = {'Cookie': cookie['set-cookie'],
	'User-Agent': ua}
	url = 'https://www.reddit.com/message/unread.json'
	try:
		resp, content = http.request(url, 'GET', headers=headers)
	except Exception as e:
		logging.info('Caught exception reading mail. %s', e)
	else:
		parseMessage(content)


def parseMessage(data):
	try:
		msg_json = json.loads(data)
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

def parseMe(cookie,data):
	try:
		data_json = json.loads(data)
	except json.JSONDecodeError, e:
		logging.error('Error parsing json. %s', e)
	else:
		if 'data' in data_json:
			data = data_json['data']

			if data['has_mail'] or data['has_mod_mail']:
				getMessages(cookie)
		else:
			logging.error('Reddit returned bad json.\n Response: %s\n', data)

def pushdispatcher(msg):
	title = "{0:s} ({1:s})".format(msgtitle, user)
	if paenabled:
		sendPushalot(msg, title)
	if poenabled:
		sendPushover(msg, title)
	if pbenabled:
		sendPushbullet(msg, title)

def sendPushalot(body, title):
	http = httplib2.Http()
	url = 'https://pushalot.com/api/sendmessage'
	headers = { 'User-Agent': ua }
	body = {
		'AuthorizationToken': paauthtoken,
		'Title': title,
		'Body': body,
		'Image': paimg,
		'TimeTolive': pattl,
		'Link': pushurl,
		'LinkTitle': pushurltitle
	}
	try:
		resp, cont = http.request(url, 'POST', headers=headers,
		body=urllib.urlencode(body))
	except Exception as e:
		logging.info('Problem sending pushalot. %s', e)
	else:
		if int(resp['status']) != 200:
			try:
				error_json = json.loads(cont)
			except json.JSONDecodeError:
				logging.error('Couldn\'t decode json')
			else:
				desc = error_json['Description']
				logging.info('Problem sending pushalot. %s: %s',
				resp['status'], desc)
		else:
			logging.info('Pushalot message sent')
			pass

def sendPushover(body, title):
	http = httplib2.Http()
	url = 'https://api.pushover.net/1/messages.json'
	headers = {'Content-type': 'application/x-www-form-urlencoded',
	'User-Agent': ua}
	body = {
		'token': 'aU9TRhEJD1fubJiQAKFmQfvkcQd3q9',
		'user': pousrkey,
		'title': title,
		'message': body,
		'url': pushurl,
		'url_title': pushurltitle
	}
	try:
		resp, cont = http.request(url, 'POST', headers=headers,
		body=urllib.urlencode(body))
	except Exception as e:
		logging.error('Problem sending pushover. %s', e)
	else:
		if int(resp['status']) != 200:
			try:
				error_json = json.loads(cont)
			except json.JSONDecodeError:
				logging.error('Couldn\'t decode json')
			else:
				desc = error_json['errors']
				logging.error('Problem sending pushover. %s: %s',
				resp['status'], desc)
		else:
			logging.info('Pushover message sent')
			pass

def sendPushbullet(body, title):
	http = httplib2.Http()
	url = 'https://api.pushbullet.com/v2/pushes'
	headers = {'Content-type': 'application/x-www-form-urlencoded',
	'User-Agent': ua}
	http.add_credentials(pbtoken, '')
	body = {
		'type': 'link',
		'title': title,
		'body': body,
		'url': pushurl
	}
	try:
		resp, cont = http.request(url, 'POST', headers=headers,
		body=urllib.urlencode(body))
	except Exception as e:
		logging.error('Problem sending pushbullet. %s', e)
	else:
		if int(resp['status']) != 200:
			try:
				error_json = json.loads(cont)
			except json.JSONDecodeError:
				logging.error('Couldn\'t decode json')
			else:
				desc = error_json['error']['message']
				logging.error('Problem sending pushbullet. %s: %s',
				resp['status'], desc)
		else:
			logging.info('Pushbullet message sent')
			pass


def run(loginresponse):
	while True:
		if loginresponse is not None:
			resp, status = getMe(loginresponse['access_token'], 
								 loginresponse['token_type'])
		if resp is None or status is None:
			logging.error("Got no response, reddit is likely down.")
			time.sleep(poll)
			loginresponse = loginReddit(user, passwd, clientid, secret)
		elif status != 200:
			print "Error."
			logging.error("Reddit threw error %s. Trying to login", status)
			time.sleep(poll)
			loginresponse = loginReddit(user, passwd, clientid, secret)
		elif status == 200:
			print "sallgood."
			parseMe()
			time.sleep(poll)

if __name__ == '__main__':
	ua = 'orangered_pusher/0.1.1 by /u/exiva'

	settings     = loadCfg('settings.cfg')
	user         = settings.get('reddit','username')
	passwd       = settings.get('reddit', 'password')
	clientid	 = settings.get('reddit', 'clientid')
	secret		 = settings.get('reddit', 'secret')
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

	logindata = loginReddit(user, passwd, clientid, secret)

	print logindata
	
	if logindata.get('access_token') is None:
		print "Got no response, Reddit is likely down. Try again."
	else:
		print "Logged in, Checking for new mail."
		print logindata.get('access_token')
		run(logindata)
