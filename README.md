# Orangered Pusher

Save battery on your mobile devices by turning off polling for new orangered's. Orangered Pusher will push reddit orangered notifications to Windows Phone (and Windows 8) using [Pushalot](http://pushalot.com), and iOS and Android using [Pushover](https://pushover.net) or [Pushbullet](https://pushbullet.com) instantly and using much less battery power.

## Usage
* Create a new script app from the reddit account you want to monitor's settings. (Use any url for the redirect)
* rename settings_example.cfg to settings.cfg
* Edit settings.cfg with your reddit username, and password, as well as the clientid and secret from your script app settings on reddit.
* Enable the push service you wish to use, and populate with the needed tokens.
* install requests with pip, or the requirements.txt file.
* Run the script.

###Requirements
* Python 2.7
* Requests >= 2.3.0

### Todo
* Multiple account support
