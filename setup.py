import praw
from prawoauth2 import PrawOAuth2Server
import sys

agent = 'getting refresh tokens for a script'
r = praw.Reddit(user_agent=agent)
scopes = ['read', 'modlog', 'privatemessages', 'submit']

print '\n\n'

app_key = str(raw_input('Enter your APP Key: '))
app_sec = str(raw_input('Enter your Secret Key: '))

o = PrawOAuth2Server(r, app_key, app_sec, state=agent, scopes=scopes)
o.start()

tokens = o.get_access_codes()

access_token = tokens['access_token']
refresh_token = tokens['refresh_token']

print '\n\nAdd these values to your settings.py file, along with the APP KEY and APP SECRET:\n\n'
print 'access_token = ' + access_token
print 'refresh_token = ' + refresh_token

print '\n\n---> All Done!'
exit()