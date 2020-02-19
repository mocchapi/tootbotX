# TootbotX

This is a Python bot that looks up posts from specified subreddits and automatically posts them on Twitter. It is based on [Tootbot](https://github.com/corbindavenport/tootbot), which is based on [reddit-twitter-bot](https://github.com/rhiever/reddit-twitter-bot).
There are a few notable features that distinguish it from the original Tootbot, primarily issues and features ive needed.
The major drawback to using TBX is that there is no mastodon support, nor is there a heroku version.

**Features:**

* Bug fixes and slightly more cleaned up code [TBX]
* TootbotX allows you to set a list of blacklisted words that will force a post to be skipped [TBX]
* TootbotX includes options for OCR to check images for blacklisted words [TBX]
* TootbotX allows for automated searches for the original tweet if the reddit post is a twitter screenshot, and can post a link to the original as a reply [TBX]
* TootbotX can either run locally, or in the cloud with a free Heroku account
* Media from direct links, Gfycat, Imgur, Reddit, and Giphy is automatically attached in the social media post
* Links that do not contain media can be skipped, ideal for meme accounts like [@traabot](https://twitter.com/traabot)
* NSFW content, spoilers, and self-posts can be filtered
* TootbotX can monitor multiple subreddits at once
* TootbotX is fully open-source, so you don't have to give an external service full access to your social media accounts

Tootbot uses the [tweepy](https://github.com/tweepy/tweepy), [PRAW](https://praw.readthedocs.io/en/latest/), [py-gfycat](https://github.com/ankeshanand/py-gfycat), [imgurpython](https://github.com/Imgur/imgurpython), [Pillow](https://github.com/python-pillow/Pillow) and [OpenCV](https://pypi.org/project/opencv-python/), [Google](https://pypi.org/project/google/), libraries.

## Disclaimer

The developers of Tootbot hold no liability for what you do with this script or what happens to you by using this script. Abusing this script *can* get you banned from Twitter and/or Mastodon, so make sure to read up on proper usage of the API for each site.

## Setup and usage

Instructions are lagerly the same at the [original tootbot instructions](https://github.com/corbindavenport/tootbot/wiki).
TootbotX requires you to run `Get_latest_tweepy.py` *once* to install the latest git version of Tweepy.
This is only temporary and will not be required when Tweepy 3.9 is released.
