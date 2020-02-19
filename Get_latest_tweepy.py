import os
if __name__ == '__main__':
	print('''Hi! This utility will download and install the latest tweepy version.
This will be required until tweepy 3.9 is released, since tweepy 3.8 is missing some important features.
Using the latest tweepy build might cause some problems, so if TootbotX doesn't run properly,
try running this script again in a week or so (or use the original tootbot until tweepy 3.9 is released)
If you are from the future and tweepy 3.9 (or higher) is released, you can completely ignore this 
script and install it by typing "pip install tweepy" in your terminal.

[Please note that this script requires admin permissions on windows]

To continue press enter
To exit close the window''')
	input()
	print('Installing...')
	try:
		os.system('pip uninstall tweepy')
		os.system('pip3 uninstall tweepy')
	except:
		pass
	try:
		os.system('pip install git+https://github.com/tweepy/tweepy.git')
		print('Installation complete, press enter to exit\n')
	except BaseException as e:
		if os.name == 'posix':
			print(f'Error ({e})\n Trying pip3...')
			try:
				os.system('pip3 install git+https://github.com/tweepy/tweepy.git')
				print('Installation complete, press enter to exit\n')
			except:
				pass
		print(e)
	input()
	exit()