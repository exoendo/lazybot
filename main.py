#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import time
import socket
import collections
import praw
import settings
from prawoauth2 import PrawOAuth2Mini as pmini


class bot(object):

    def __init__(self, server, channel, nick, password):
        self.channel = channel
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((server, 6667))

        # Values are hostname, username, servername: realname
        # Basically, just make it all nick, it doesn't matter
        self.s.send("USER {0} {1} {2} :{3}\n".format(
            nick, nick, nick, 'I am a bot'))

        self.s.send("NICK {}\n".format(nick))

        while True:
            time.sleep(.5)
            text = self.s.recv(1024)

            if text.find(':End of message of the day.') != -1:
                self.s.send('PRIVMSG nickserv :IDENTIFY {}\n'.format(password))

                time.sleep(5)  # Give time for server to authenticate
                self.s.send('JOIN {}\n'.format(self.channel))
                break
            else:
                pass

            print text

            if text.find('PING :') != -1:
                self.s.send('PONG :{}\n'.format(text.split('PING :')[1]))

    def reddit_connect(self, APP_KEY, APP_SECRET, ACCESS_TOKEN, REFRESH_TOKEN, sub):
        ''' Connects to Reddit API '''

        self.r = praw.Reddit('Fetching mod-related info for IRC')
        scope_list = ['read', 'modlog', 'privatemessages', 'submit']
        self.oauth = pmini(self.r, app_key=APP_KEY,
                           app_secret=APP_SECRET,
                           access_token=ACCESS_TOKEN,
                           refresh_token=REFRESH_TOKEN,
                           scopes=scope_list)

        self.subreddit = self.r.get_subreddit(sub)

    def modlog(self, hours):
        ''' Gets Moderator Log actions for the last 1-168 hours '''

        # This will allow us to ping the user that asked for info
        ping_name = re.findall(r':(.*)!', hours)

        self.s.send('PRIVMSG {} :{}\n'.format(self.channel, '(One moment...)'))
        d = {}

        # split at modlog convert number to int
        hours = int(hours.split(':~modlog')[1])
        if hours > 168:
            self.s.send('PRIVMSG {} :({}) {}\n'.format(self.channel,
                        ping_name[0], 'modlog function caps at 168 hours :)'))
            return
        now = time.time()
        for item in self.subreddit.get_mod_log(limit=None):
            result = now - item.created_utc
            if result / 3600 > hours:
                break
            modname = item.mod
            if modname in d:
                d[modname] += 1
            else:
                d[modname] = 1

        msg = '({}) Mod log actions in last {} hour(s): '.format(
            ping_name[0], hours)

        for info in collections.Counter(d).most_common():
            if info[0] == 'AutoModerator':
                continue
            # We are inserting a zero-width space so no one in chan is pinged
            # Info[0][0] = first letter, \u200B = Space, info[0][1:] = the rest
            name = u'{}\u200B{}'.format(info[0][0], info[0][1:])
            name = name.encode('utf-8', 'ignore')
            msg += '\x02{}: \x0F{} | '.format(name, info[1])

        self.s.send('PRIVMSG {} :{}\n'.format(self.channel, msg))

    def modmail(self, text_stream):
        ''' Parses Modmail when link is given '''

        ping_name = re.findall(r':(.*?)!', text_stream)

        mail_msg = text_stream.split(':~modmail')[1]
        if len(mail_msg) > 425:
            msg = 'Too Long! Msg length caps modmail messages at 425 chars.'
            self.s.send('PRIVMSG {} :({}) {}\n'.format(
                        self.channel, ping_name[0], msg))
            return

        # for finding the msg we sent to reply with a link:
        key_msg = mail_msg[:25]
        title = '{} writes via IRC:'.format(ping_name[0])

        try:
            self.r.send_message(self.subreddit, title, mail_msg)
            gen = self.r.get_mod_mail(subreddit=self.subreddit, limit=3)
            for item in gen:
                if re.search(key_msg, item.body):
                    link = 'http://www.reddit.com/message/messages/{}'.format(
                        item.id)
                    break
                else:
                    link = '(Failed to return Link...)'
            msg = 'Message Sent! {}'.format(link)
            self.s.send('PRIVMSG {} :({}) {}\n'.format(
                self.channel, ping_name[0], msg))

        except Exception as e:
            msg = ('Failed to send modmail for some reason.')

            self.s.send('PRIVMSG {} :({}) {}\n'.format(
                self.channel, ping_name[0], msg))

    def modque(self, text_stream):
        ''' Fetches the count for moderation queue '''

        self.s.send('PRIVMSG {} :{}\n'.format(self.channel, '(One moment...)'))

        # This will allow us to ping the user that asked for info
        ping_name = re.findall(r':(.*)!', text_stream)

        count = 0
        for item in self.subreddit.get_mod_queue(limit=None):
            count += 1
        msg = 'There are currently {} items in the modqueue'.format(count)
        self.s.send('PRIVMSG {} :({}) {}\n'.format(
            self.channel, ping_name[0], msg))

    def unmod(self, text_stream):
        ''' Fetches the count for unmoderated '''

        self.s.send('PRIVMSG {} :{}\n'.format(self.channel, '(One moment...)'))

        # This will allow us to ping the user that asked for info
        ping_name = re.findall(r':(.*)!', text_stream)

        count = 0
        for item in self.subreddit.get_unmoderated(limit=None):
            count += 1
        msg = 'There are currently {} items in the unmodqueue'.format(count)
        self.s.send('PRIVMSG {} :({}) {}\n'.format(
            self.channel, ping_name[0], msg))

    def run(self):
        time.sleep(5)
        while True:

            self.oauth.refresh()  # tokens expire every 60 minutes
            time.sleep(.5)

            text = self.s.recv(1024)
            print text
            if text.find('PING :') != -1:  # func returns -1 if no match
                self.s.send('PONG :{}\n'.format(text.split('PING :')[1]))
                print 'PONG :{}'.format(text.split('PING :')[1])

            elif re.search(':~modlog \d+\r\n$', text):
                self.modlog(text)

            elif text.find(':~modque') != -1:
                self.modque(text)

            elif text.find(':~unmod') != -1:
                self.unmod(text)

            elif text.find(':~modmail') != -1:
                self.modmail(text)
            else:
                pass

if __name__ == "__main__":

    lazy = bot(settings.server,
               settings.channel,
               settings.nick,
               settings.password)

    lazy.reddit_connect(settings.APP_KEY,
                        settings.APP_SECRET,
                        settings.ACCESS_TOKEN,
                        settings.REFRESH_TOKEN,
                        settings.subreddit)
    lazy.run()
