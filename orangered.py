#!/usr/bin/env python

import ConfigParser
import requests
import time
import logging


def loadCfg(settings):
    config = ConfigParser.ConfigParser()
    config.read(settings)
    return config


def loginReddit(user, password, clientid, secret):
    url = 'https://www.reddit.com/api/v1/access_token'
    data = {'grant_type': 'password', 'username': user,
            'password': password}
    headers = {'User-Agent': ua}
    try:
        r = requests.post(url, data=data, auth=(clientid, secret),
                          headers=headers)
    except requests.exceptions.ConnectionError as e:
        logging.error('Caught exception logging in. %s', e)
    else:
        try:
            r.json()
        except ValueError as e:
            logging.error('Caught exception logging in. %s', e)
        else:
            return r.json()


def getMe(token, tokentype):
    url = 'https://oauth.reddit.com/api/v1/me'
    headers = {'Authorization': '{0:s} {1:s}'.format(tokentype, token),
               'User-Agent': ua}
    try:
        r = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError as e:
        logging.error('Caught exception reading account info. %s', e)
        return None, None
    else:
        try:
            r.json()
        except ValueError as e:
            logging.error('Me json malformed.')
        else:
            return r.json(), r.status_code


def getMessages(token, tokentype):
    url = 'https://oauth.reddit.com/message/unread.json'
    headers = {'Authorization': '{0:s} {1:s}'.format(tokentype, token),
               'User-Agent': ua}
    try:
        r = requests.get(url, headers=headers)
    except requests.exceptions.ConnectionError as e:
        logging.error('Caught exception reading mail. %s', e)
    else:
        try:
            r.json()
        except ValueError:
            logging.error('Messages json malformed.')
        else:
            parseMessage(r.json())


def parseMessage(data):
    try:
        lastmsg_json = data['data']['children'][0]['data']
    except KeyError:
        logging.error("Message json malformed.")
    else:
        global lastmsg

        unreads = len(data['data']['children'])

        if lastmsg != lastmsg_json['name']:
            lastmsg = lastmsg_json['name']
            logging.info('New Message')
            if unreads > 1:
                pushdispatcher("{0:d} {1:s}".format(unreads, msgbodym))
            else:
                pushdispatcher(msgbody)


def parseMe(data, token, tokentype):
    try:
        data['has_mail']
    except KeyError:
        logging.error("me.json response missing keys")
    else:
        if data['has_mail'] or data['has_mod_mail']:
            getMessages(token, tokentype)


def pushdispatcher(msg):
    title = "{0:s} ({1:s})".format(msgtitle, user)
    if paenabled:
        sendPushalot(msg, title)
    if poenabled:
        sendPushover(msg, title)
    if pbenabled:
        sendPushbullet(msg, title)


def sendPushalot(body, title):
    url = 'https://pushalot.com/api/sendmessage'
    headers = {'User-Agent': ua}
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
        r = requests.post(url, headers=headers, data=body)
    except requests.exceptions.RequestException as e:
        logging.error("Caught exception sending pushalot %s", e)
    else:
        try:
            json = r.json()
        except ValueError:
            logging.error("Pushalot json malformed")
        else:
            if r.status_code is not 200:
                logging.error('Problem sending pushalot. %s: %s',
                              r.status_code, json['Description'])
            elif int(json['Status']) == 200:
                logging.info('Pushalot message sent')
            else:
                logging.error("Something went terribly wrong.")


def sendPushover(body, title):
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
        r = requests.post(url, headers=headers, data=body)
    except requests.exceptions.RequestException as e:
        logging.error("Caught exception sending pushover %s", e)
    else:
        if r.status_code is not 200:
            try:
                json = r.json()
            except ValueError:
                logging.error("Got bad json from pushover.")
            else:
                logging.error('Problem ending pushover. %s: %s',
                              r.status_code, json['errors'])
        else:
            logging.info('Pushover message sent')


def sendPushbullet(body, title):
    url = 'https://api.pushbullet.com/v2/pushes'
    headers = {'Content-type': 'application/x-www-form-urlencoded',
               'User-Agent': ua}
    body = {
        'type': 'link',
        'title': title,
        'body': body,
        'url': pushurl
    }
    try:
        r = requests.post(url, headers=headers, data=body, auth=(pbtoken, ''))
    except requests.exceptions.RequestException as e:
        logging.error("Caught exception sending pushbullet %s", e)
    else:
        if r.status_code is not 200:
            try:
                json = r.json()
            except ValueError:
                logging.error("Got bad json from pushbullet.")
            else:
                logging.error('Problem sending pushbullet. %s: %s',
                              r.status_code, json['status'])
        else:
            logging.info('Pushbullet message sent')


def run(loginresponse):
    while True:
        if loginresponse is not None:
            resp, status = getMe(loginresponse['access_token'],
                                 loginresponse['token_type'])
            if status is 200:
                parseMe(resp, loginresponse['access_token'],
                        loginresponse['token_type'])
                time.sleep(poll)
            elif status is 401:  # token expired
                loginresponse = loginReddit(user, passwd, clientid, secret)
                time.sleep(poll)
            else:
                logging.error("Reddit returned %s. Trying to login", status)
                time.sleep(poll)
                loginresponse = loginReddit(user, passwd, clientid, secret)
        else:
            logging.error("Got no response, reddit is likely down.")
            time.sleep(poll)


if __name__ == '__main__':
    ua = 'python: orangered_pusher/0.2.0 by /u/exiva'

    settings = loadCfg('settings.cfg')
    user = settings.get('reddit', 'username')
    passwd = settings.get('reddit', 'password')
    clientid = settings.get('reddit', 'clientid')
    secret = settings.get('reddit', 'secret')
    poll = settings.getint('reddit', 'poll')
    msgtitle = settings.get('global', 'title')
    msgbody = settings.get('global', 'body')
    msgbodym = settings.get('global', 'multibody')
    pushurl = settings.get('global', 'url')
    pushurltitle = settings.get('global', 'urltitle')
    logfile = settings.get('global', 'log')
    paenabled = settings.getboolean('pushalot', 'enabled')
    paauthtoken = settings.get('pushalot', 'token')
    pattl = settings.get('pushalot', 'ttl')
    paimg = settings.get('pushalot', 'image')
    poenabled = settings.getboolean('pushover', 'enabled')
    pousrkey = settings.get('pushover', 'key')
    pbenabled = settings.getboolean('pushbullet', 'enabled')
    pbtoken = settings.get('pushbullet', 'token')

    logging.basicConfig(filename=logfile, level=logging.INFO)
    logging.getLogger("requests").setLevel(logging.WARNING)

    print "Starting {}.\n...Trying to login with {}...".format(ua, user)
    lastmsg = 'none'

    logindata = loginReddit(user, passwd, clientid, secret)

    try:
        logindata['access_token']
    except KeyError:
        print "Couldn't login. Check credentials and try again."
    else:
        print "Logged in. Checking for new mail..."
        run(logindata)
