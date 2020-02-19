import praw
import json
import tweepy
import time
import os
import csv
import configparser
import urllib.parse
import sys
from imgurpython import ImgurClient
from glob import glob
import distutils.core
import itertools
from getmedia import get_media
from getmedia import get_hd_media
from ocr import get_ocr
from googlesearch import search


def get_reddit_posts(subreddit_info):
	post_dict = {}
	print('[ OK ] Getting posts from Reddit...')
	for submission in subreddit_info.hot(limit=POST_LIMIT):
		if (submission.over_18 and NSFW_POSTS_ALLOWED is False):
			# Skip over NSFW posts if they are disabled in the config file
			print('[ OK ] Skipping', submission.id, 'because it is marked as NSFW')
			continue
		elif (submission.is_self and SELF_POSTS_ALLOWED is False):
			# Skip over NSFW posts if they are disabled in the config file
			print('[ OK ] Skipping', submission.id, 'because it is a self post')
			continue
		elif (submission.spoiler and SPOILERS_ALLOWED is False):
			# Skip over posts marked as spoilers if they are disabled in the config file
			print('[ OK ] Skipping', submission.id, 'because it is marked as a spoiler')
			continue
		elif (submission.stickied):
			print('[ OK ] Skipping', submission.id, 'because it is stickied')
			continue
		else:
			# Create dict
			post_dict[submission.id] = submission
	return post_dict

def getOgTweet(query,name=None,single=False):
	hits = []
	if '@'in query:
		for item in search(query, tld="com", num=10, stop=3, pause=2):
			if 'twitter.com/status' in item:
				if name !=None:
					if name in item:
						hits = hits + [item]
				else:
					hits = hits + [item]
	if single and hits:
		return hits[0]
	else:
		return hits


def get_twitter_caption(submission):
	# Create string of hashtags
	hashtag_string = ''
	if HASHTAGS:
		for x in HASHTAGS:
			# Add hashtag to string, followed by a space for the next one
			hashtag_string += '#' + x + ' '
	# Set the Twitter max title length for 280, minus the length of the shortlink and hashtags, minus one for the space between title and shortlink
	twitter_max_title_length = 280 - len(submission.shortlink) - len(hashtag_string) - 1
	# Create contents of the Twitter post
	if len(submission.title) < twitter_max_title_length:
		twitter_caption = submission.title + ' ' + hashtag_string + submission.shortlink
	else:
		twitter_caption = submission.title[:twitter_max_title_length] + '... ' + hashtag_string + submission.shortlink
	return twitter_caption



def setup_connection_reddit(subreddit):
	print('[ OK ] Setting up connection with Reddit...')
	r = praw.Reddit(
		user_agent='tootbotX',
		client_id=REDDIT_AGENT,
		client_secret=REDDIT_CLIENT_SECRET)
	return r.subreddit(subreddit)


def duplicate_check(id):
	value = False
	with open(CACHE_CSV, 'rt', newline='') as f:
		reader = csv.reader(f, delimiter=',')
		for row in reader:
			if id in row:
				value = True
	f.close()
	return value


def log_post(id, post_url):
	with open(CACHE_CSV, 'a', newline='') as cache:
		date = time.strftime("%d/%m/%Y") + ' ' + time.strftime("%H:%M:%S")
		wr = csv.writer(cache, delimiter=',')
		wr.writerow([id, date, post_url])
	cache.close()


def make_post(post_dict):
	for post in post_dict:
		# Grab post details from dictionary
		post_id = post_dict[post].id
		if not duplicate_check(post_id):  # Make sure post is not a duplicate
			# Download Twitter-compatible version of media file (static image or GIF under 3MB)
			if POST_TO_TWITTER:
				media_file = get_media(post_dict[post].url, IMGUR_CLIENT, IMGUR_CLIENT_SECRET)
			# Post on Twitter
			if POST_TO_TWITTER:
				if OCR_ENABLED:
					print(f'[ .. ] processing OCR...')
					try:
						ocr_results = get_ocr(media_file,OCR_KEY)
						print(f'[ OK ] done.')
						print(f'[ OK ] results: {ocr_results}')
					except BaseException as e:
						print(f'[EROR] OCR error: {e}')
						ocr_results = ''
				# Make sure the post contains media, if MEDIA_POSTS_ONLY in config is set to True
				if (((MEDIA_POSTS_ONLY is True) and media_file) or (MEDIA_POSTS_ONLY is False)):
					try:
						auth = tweepy.OAuthHandler(
							CONSUMER_KEY, CONSUMER_SECRET)
						auth.set_access_token(
							ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
						twitter = tweepy.API(auth)
						caption = get_twitter_caption(post_dict[post])
						if ASCII_ONLY:
							caption = caption.encode('ascii', 'ignore').decode('ascii')
						if BLACKLIST:
							BLcaption = caption.lower()
							print('[ .. ] Checking title for words in blacklist...')
							# if ocr is enabled, add its content to the blacklist
							if OCR_ENABLED:
								BLcaption = f'{BLcaption}\n{ocr_results}'
							if any(blwords in BLcaption for blwords in BLACKLIST):
								print("[WARN] Post title contained word from blacklist, skipping...")
								log_post(post_id, 'Error while posting tweet: Contained blacklist word')
								return
							else:
								print("[ OK ] Post title passed blacklist check")

						# Post the tweet
						if (media_file):
							print('[ OK ] Posting this on Twitter with media attachment:', caption)
							media_object = twitter.media_upload(media_file)
							if OCR_ALT_TEXT_ENABLED and OCR_ENABLED:
								twitter.create_media_metadata(media_object.media_id,f'Disclaimer: alt text is automatically generated. {ocr_results}')
							tweet = twitter.update_status(caption,media_ids=[media_object.media_id])
							# Clean up media file
						else:
							print('[ OK ] Posting this on Twitter:',caption)
							tweet = twitter.update_status(status=caption)
						tweet_id = tweet.id_str
						print(tweet_id)
						# If OcrTweet is enabled, reply with OG tweet
						if TWITTER_OCR_ENABLED and OCR_ENABLED:
							print('[ .. ] Looking for original tweet, if it exists...')
							try:
								og_tweet = getOgTweet(ocr_results,single=True)
								if og_tweet:
									print(f'[ OK ] Found {og_tweet}')
									print(f'[ .. ] Replying to own tweet of screenshot...')
									twitter.update_status(f'{og_tweet}',in_reply_to_status_id=int(tweet_id),auto_populate_reply_metadata=True)
									print(f'[ OK ] Completed.')
								else:
									print('[ OK ] None found')
							except BaseException as e:
								print(f'[EROR] Error: {e}')
						try:
							os.remove(media_file)
							print('[ OK ] Deleted media file at', media_file)
						except BaseException as e:
							print('[EROR] Error while deleting media file:', str(e))
						# Log the tweet
						log_post(post_id, 'https://twitter.com/' + twitter_username + '/status/' + tweet_id + '/')
					except BaseException as e:
						print('[EROR] Error while posting tweet:', str(e))
						# Log the post anyways
						log_post(post_id, 'Error while posting tweet: ' + str(e))
				else:
					print('[WARN] Twitter: Skipping', post_id, 'because non-media posts are disabled or the media file was not found')
					# Log the post anyways
					log_post(post_id, 'Twitter: Skipped because non-media posts are disabled or the media file was not found')
			
			# Go to sleep
			print('[ OK ] Sleeping for', DELAY_BETWEEN_TWEETS, 'seconds @', time.strftime("%H:%M:%S"))
			time.sleep(DELAY_BETWEEN_TWEETS)
		else:
			print('[ OK ] Skipping', post_id, 'because it was already posted')


# Check for updates
try:
	with urllib.request.urlopen("https://raw.githubusercontent.com/mocchapi/tootbotX/update-check/current-version.txt") as url:
		s = url.read()
		new_version = s.decode("utf-8").rstrip()
		current_version = 2.6  # Current version of script
		if (current_version < float(new_version)):
			print('[WARN] A new version of tootbotX (' + str(new_version) + ') is available! (you have ' + str(current_version) + ')')
			print('[WARN] Get the latest update from here: https://github.com/mocchapi/tootbotX/')
		else:
			print('[ OK ] You have the latest version of tootbotX (' + str(current_version) + ')')
	url.close()
except BaseException as e:
	print('[EROR] Error while checking for updates:', str(e))
# Make sure config file exists
try:
	config = configparser.ConfigParser()
	config.read('config.ini')
except BaseException as e:
	print('[EROR] Error while reading config file:', str(e))
	sys.exit()
# General settings
CACHE_CSV = config['BotSettings']['CacheFile']
DELAY_BETWEEN_TWEETS = int(config['BotSettings']['DelayBetweenPosts'])
POST_LIMIT = int(config['BotSettings']['PostLimit'])
SUBREDDIT_TO_MONITOR = config['BotSettings']['SubredditToMonitor']
NSFW_POSTS_ALLOWED = bool(distutils.util.strtobool(
	config['BotSettings']['NSFWPostsAllowed']))
SPOILERS_ALLOWED = bool(distutils.util.strtobool(
	config['BotSettings']['SpoilersAllowed']))
SELF_POSTS_ALLOWED = bool(distutils.util.strtobool(
	config['BotSettings']['SelfPostsAllowed']))
if config['BotSettings']['Hashtags']:
	# Parse list of hashtags
	HASHTAGS = config['BotSettings']['Hashtags']
	HASHTAGS = [x.strip() for x in HASHTAGS.split(',')]
else:
	HASHTAGS = ''
ASCII_ONLY = bool(distutils.util.strtobool(
	config['BotSettings']['AsciiOnly']))
OCR_ENABLED = bool(distutils.util.strtobool(
	config['BotSettings']['OcrEnabled']))
if config['BotSettings']['Blacklist']:
	BLACKLIST = list(config['BotSettings']['Blacklist'].split(','))
else:
	BLACKLIST = []
# Settings related to media attachments
MEDIA_POSTS_ONLY = bool(distutils.util.strtobool(
	config['MediaSettings']['MediaPostsOnly']))
# Twitter info
POST_TO_TWITTER = bool(distutils.util.strtobool(
	config['Twitter']['PostToTwitter']))
TWITTER_OCR_ENABLED = bool(distutils.util.strtobool(
	config['Twitter']['OcrTweet']))
OCR_ALT_TEXT_ENABLED = bool(distutils.util.strtobool(
	config['Twitter']['OcrAltText']))

#setup ocr.space
if OCR_ENABLED:
	if not os.path.exists('ocr.secret'):
		print('[WARN] API key for ocr.space not found. Please enter it below.')
		# Whitespaces are stripped from input: https://stackoverflow.com/a/3739939
		OCR_KEY = ''.join(input("[ .. ] Enter ocr.space api key: ").split())
		# Make sure authentication is working
		try:
			ocr_config = configparser.ConfigParser()
			ocr_config['ocr'] = {
				'apikey': OCR_KEY,
			}
			with open('ocr.secret', 'w') as f:
				ocr_config.write(f)
			f.close()
		except BaseException as e:
			print('[EROR] ', str(e))
			print('[EROR] tootbotX cannot continue, now shutting down')
			exit()
	else:
		# Read API keys from secret file
		ocr_config = configparser.ConfigParser()
		ocr_config.read('ocr.secret')
		OCR_KEY = ocr_config['ocr']['apikey']


# Setup and verify Reddit access
if not os.path.exists('reddit.secret'):
	print('[WARN] API keys for Reddit not found. Please enter them below (see wiki if you need help).')
	# Whitespaces are stripped from input: https://stackoverflow.com/a/3739939
	REDDIT_AGENT = ''.join(input("[ .. ] Enter Reddit agent: ").split())
	REDDIT_CLIENT_SECRET = ''.join(
		input("[ .. ] Enter Reddit client secret: ").split())
	# Make sure authentication is working
	try:
		reddit_client = praw.Reddit(
			user_agent='tootbotX', client_id=REDDIT_AGENT, client_secret=REDDIT_CLIENT_SECRET)
		test = reddit_client.subreddit('announcements')
		# It worked, so save the keys to a file
		reddit_config = configparser.ConfigParser()
		reddit_config['Reddit'] = {
			'Agent': REDDIT_AGENT,
			'ClientSecret': REDDIT_CLIENT_SECRET
		}
		with open('reddit.secret', 'w') as f:
			reddit_config.write(f)
		f.close()
	except BaseException as e:
		print('[EROR] Error while logging into Reddit:', str(e))
		print('[EROR] tootbotX cannot continue, now shutting down')
		exit()
else:
	# Read API keys from secret file
	reddit_config = configparser.ConfigParser()
	reddit_config.read('reddit.secret')
	REDDIT_AGENT = reddit_config['Reddit']['Agent']
	REDDIT_CLIENT_SECRET = reddit_config['Reddit']['ClientSecret']
# Setup and verify Imgur access
if not os.path.exists('imgur.secret'):
	print('[WARN] API keys for Imgur not found. Please enter them below (see wiki if you need help).')
	# Whitespaces are stripped from input: https://stackoverflow.com/a/3739939
	IMGUR_CLIENT = ''.join(input("[ .. ] Enter Imgur client ID: ").split())
	IMGUR_CLIENT_SECRET = ''.join(
		input("[ .. ] Enter Imgur client secret: ").split())
	# Make sure authentication is working
	try:
		imgur_client = ImgurClient(IMGUR_CLIENT, IMGUR_CLIENT_SECRET)
		test_gallery = imgur_client.get_album('dqOyj')
		# It worked, so save the keys to a file
		imgur_config = configparser.ConfigParser()
		imgur_config['Imgur'] = {
			'ClientID': IMGUR_CLIENT,
			'ClientSecret': IMGUR_CLIENT_SECRET
		}
		with open('imgur.secret', 'w') as f:
			imgur_config.write(f)
		f.close()
	except BaseException as e:
		print('[EROR] Error while logging into Imgur:', str(e))
		print('[EROR] tootbotX cannot continue, now shutting down')
		exit()
else:
	# Read API keys from secret file
	imgur_config = configparser.ConfigParser()
	imgur_config.read('imgur.secret')
	IMGUR_CLIENT = imgur_config['Imgur']['ClientID']
	IMGUR_CLIENT_SECRET = imgur_config['Imgur']['ClientSecret']
# Log into Twitter if enabled in settings
if POST_TO_TWITTER is True:
	if os.path.exists('twitter.secret'):
		# Read API keys from secret file
		twitter_config = configparser.ConfigParser()
		twitter_config.read('twitter.secret')
		ACCESS_TOKEN = twitter_config['Twitter']['AccessToken']
		ACCESS_TOKEN_SECRET = twitter_config['Twitter']['AccessTokenSecret']
		CONSUMER_KEY = twitter_config['Twitter']['ConsumerKey']
		CONSUMER_SECRET = twitter_config['Twitter']['ConsumerSecret']
		try:
			# Make sure authentication is working
			auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
			auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
			twitter = tweepy.API(auth)
			twitter_username = twitter.me().screen_name
			print('[ OK ] Sucessfully authenticated on Twitter as @' +
				  twitter_username)
		except BaseException as e:
			print('[EROR] Error while logging into Twitter:', str(e))
			print('[EROR] tootbotX cannot continue, now shutting down')
			exit()
	else:
		# If the secret file doesn't exist, it means the setup process hasn't happened yet
		print('[WARN] API keys for Twitter not found. Please enter them below (see wiki if you need help).')
		# Whitespaces are stripped from input: https://stackoverflow.com/a/3739939
		ACCESS_TOKEN = ''.join(
			input('[ .. ] Enter access token for Twitter account: ').split())
		ACCESS_TOKEN_SECRET = ''.join(
			input('[ .. ] Enter access token secret for Twitter account: ').split())
		CONSUMER_KEY = ''.join(
			input('[ .. ] Enter consumer key for Twitter account: ').split())
		CONSUMER_SECRET = ''.join(
			input('[ .. ] Enter consumer secret for Twitter account: ').split())
		print('[ OK ] Attempting to log in to Twitter...')
		try:
			# Make sure authentication is working
			auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
			auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
			twitter = tweepy.API(auth)
			twitter_username = twitter.me().screen_name
			print('[ OK ] Sucessfully authenticated on Twitter as @' +
				  twitter_username)
			# It worked, so save the keys to a file
			twitter_config = configparser.ConfigParser()
			twitter_config['Twitter'] = {
				'AccessToken': ACCESS_TOKEN,
				'AccessTokenSecret': ACCESS_TOKEN_SECRET,
				'ConsumerKey': CONSUMER_KEY,
				'ConsumerSecret': CONSUMER_SECRET
			}
			with open('twitter.secret', 'w') as f:
				twitter_config.write(f)
			f.close()
		except BaseException as e:
			print('[EROR] Error while logging into Twitter:', str(e))
			print('[EROR] tootbotX cannot continue, now shutting down')
			exit()


# Run the main script
while True:
	# Make sure logging file and media directory exists
	if not os.path.exists(CACHE_CSV):
		with open(CACHE_CSV, 'w', newline='') as cache:
			default = ['Reddit post ID', 'Date and time', 'Post link']
			wr = csv.writer(cache)
			wr.writerow(default)
		print('[ OK ] ' + CACHE_CSV + ' file not found, created a new one')
		cache.close()
	# Continue with script
	try:
		subreddit = setup_connection_reddit(SUBREDDIT_TO_MONITOR)
		post_dict = get_reddit_posts(subreddit)
		make_post(post_dict)
	except BaseException as e:
		print('[EROR] Error in main process:', str(e))
	print('[ OK ] Sleeping for', DELAY_BETWEEN_TWEETS, 'seconds @', time.strftime("%H:%M:%S"))
	time.sleep(DELAY_BETWEEN_TWEETS)
	print('[ OK ] Restarting main process...')
