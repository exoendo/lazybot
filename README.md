# lazybot
A simple IRC bot that connects to Reddit and provides a few tools for subreddit moderators

# Requirements:

 - Praw
 - prawoauth2 for oauth handling: http://prawoauth2.readthedocs.org/installation.html
 
# Setup:

This bot needs to connect to a Reddit account that has mod access to a sub. Ideally, you should make a seperate mod account as one function of this bot is to send modmail via IRC, and it could be confusing to have modmail sent through your primary account on behalf of others.

* First step is to create an app on Reddit and get both the application key and the secret key. In order to do this, follow step 1 of this guide: http://prawoauth2.readthedocs.org/usage_guide.html#running-prawoauth2server
