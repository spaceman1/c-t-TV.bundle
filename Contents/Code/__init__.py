# -*- coding: utf-8 -*-
# The above line is used to allow european / german characters to be used WITHIN this file (code)
#
# First ALPHA release on 05-23-2009
# Version 0.1
#
# ct TV is the weekly broadcast of ct Magazine; europe's biggest computer magazine.
# This plug-in makes the last 28 shows available
# All the comntent is in German
#
# We use FRAMEWORK #1
#
#

import os.path
from lxml.html import fromstring, tostring
from BeautifulSoup import BeautifulSoup
from  htmlentitydefs import entitydefs
import re
import base64
import urllib
import urllib2

PLUGIN_PREFIX = "/video/ctTV"
ROOT_URL = "http://www.heise.de/ct-tv/"
BASE_URL = "http://www.heise.de"
PLUG_IN_LOC = "~/Library/Application\ Support/Plex\ Media\ Server/Plug-ins/c't\ TV.bundle/Contents/Resources"

CACHE_INTERVAL = CACHE_1HOUR

MainArt = 'art-default.png'
MainThumb = 'icon-default.png'

FrontPage = []
SecondPage = []

####################################################################################################

def Start():
	Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, L("c't TV"), 'icon-default.png', 'art-default.png')
	Plugin.AddViewGroup("_List", viewMode="List", mediaType="items")
	Plugin.AddViewGroup("Info", viewMode="InfoList", mediaType="items")
	HTTP.SetCacheTime(4 * CACHE_1HOUR)
	MediaContainer.title1 = "c't TV"
	MediaContainer.viewGroup = '_List'
	DirectoryItem.art = R(MainArt)
	DirectoryItem.thumb = R(MainThumb)

####################################################################################################


def MainMenu(sender = None):
	(mainTitle, mainSubtitle, currentVideoTitle, currentVideoURL, themes, topics, archive) = LoadFP()
	dir = MediaContainer(title1=mainTitle, title2=mainSubtitle, viewGroup="List")
	dir.Append(Function(DirectoryItem(CurrentShowMenu, title=currentVideoTitle), currentVideoURL=currentVideoURL, currentVideoTitle=currentVideoTitle, themes=themes))

	for url, title in topics:
		dir.Append(Function(DirectoryItem(TopicMenu, title=title), TopicURL=url))

	# Add the ARCHIVE to the container
	dir.Append(Function(DirectoryItem(ArchiveMenu, title="Sendungsarchiv"), ArchiveList=archive))
	return dir

def CurrentShowMenu(sender, currentVideoURL, currentVideoTitle, themes):
	dir = MediaContainer(title1=sender.title2, title2=currentVideoTITLE, viewGroup="Info")
	dir.Append(WebVideoItem(currentVideoURL, currentVideoTitle))

	if themes == None:
		check = getURL(currentVideoURL, False)
		if check[1] != {None:None}:
			# Needed Authentication ctTV-Main Page
			show_Main = HTML.ElementFromURL(currentVideoURL, headers=check[1], cacheTime=None, encoding="Latin-1", errors="ignore")
		else:
			show_Main = HTML.ElementFromURL(currentVideoURL, cacheTime=None, encoding="Latin-1", errors="ignore")

		themes = getThemes(show_Main)

	for url, title, summary in themes:
		dir.Append(WebVideoItem(url, title=title, summary=summary))

	return dir

def LoadFP():
	check = getURL(ROOT_URL, False)

	if check[1] != {None:None}:
		# Needed Authentication ctTV-Main Page
		ctTV_Main = HTML.ElementFromURL(ROOT_URL, headers=check[1], cacheTime=0, encoding="Latin-1", errors="ignore")
	else:
		ctTV_Main = HTML.ElementFromURL(ROOT_URL, cacheTime=0, encoding="Latin-1", errors="ignore")

	# Read a string version of the page
	ctTV_MainString = cleanHTML(urllib2.urlopen(check[0]).read())

	# Get some MAIN Meta-Data of c't TV:
	mainTitle = ctTV_Main.xpath("/html/body/div[@id='navi_top']/div[1]/ul[1]/li[2]/a")[0]
	mainTitle = tostring(mainTitle).split('">')[1][:-4].replace('<span>','').replace('</span>','').encode('Latin-1').decode('utf-8')
	mainSubtitle = ctTV_Main.xpath("/html/body/div[@id='navi_top']/div[1]/ul[3]/li[4]/a")[0].text.encode('Latin-1').decode('utf-8')

	# Define current video
	currentVideoTitle1 = ctTV_Main.xpath("//*[@id='hauptbereich']/div[@id='video']/h1/text()")[0].encode('Latin-1').decode('utf-8')
	currentVideoTitle2 = ctTV_Main.xpath("//*[@id='hauptbereich']/div[@id='video']/h1")[0]
	currentVideoTitle2 = tostring(currentVideoTitle2).split('|')[1].split('<')[0].encode('Latin-1').decode('utf-8')
	currentVideoTitle = currentVideoTitle1 + '|' + currentVideoTitle2
	currentVideoURL = ROOT_URL

	themes = getThemes(ctTV_Main)
	topics = getTopics(ctTV_Main)
	archive = getArchive(ctTV_MainString)

	return (mainTitle, mainSubtitle, currentVideoTitle, currentVideoURL, themes, topics, archive)

def getThemes(page):
	themes = list()
	for index, themenSet in enumerate(page.xpath("//*[@id='themenuebersicht']/ul/li/a")):
		try: url = BASE_URL + themenSet.get('href')
		except: continue
		
		try: title = str(index + 1) + ". Teil: " + page.xpath("//*[@id='themenuebersicht']/ul/li/a/span[@class='titel']/text()")[index].encode('Latin-1').decode('utf-8')
		except: title = None

		try: summary = page.xpath("//*[@id='themenuebersicht']/ul/li/a/span[@class='beschreibung']/text()")[Thema].encode('Latin-1').decode('utf-8')
		except: summary = None

		themes.append((url, title, summary))

	return themes


def getTopics(page):
	topics = list()
	for index, topicSet in enumerate(page.xpath("//*[@id='navigation-rubriken']/li/a")):
		try: url = BASE_URL + topicSet.get('href')
		except: continue

		try: 
			title = page.xpath("//*[@id='navigation-rubriken']/li/a")[Topic].text.encode('utf-8')
			# This is horrible and probably unecessary but I'm leaving it for now
			if isinstance(title, str):
				title = unicode(title,'utf-8')
		except:
			title = None

	return topics

def getArchive(ctTV_MainString):
	page = HTML.ElementFromString(ctTV_MainString.split('<script type="text/javascript">')[1].split("</div> \<script\> var scrollto_mini")[0][17:])
	archives = list()
	for ArchiveSet in page.xpath('//a')[:-2]:
		try: url = BASE_URL + archiveSet.get('href')
		except: continue

		try: thumb = BASE_URL + archiveSet.find('img').get('src')
		except: thumb = None

		try: alt = archiveSet.find('img').get('alt')
		except: alt = None

		try: title = archiveSet.find('img').get('title')[:-2].replace('-',' ').encode('Latin-1').decode('utf-8')
		except: title = None

		archives.append((url , thumb, alt, title))

	return archives

def TopicMenu(sender, topicURL):
	FrontPage = LoadFP()
	check = getURL(TopicURL, False)
	if check[1] != {None:None}:
		# Needed Authentication ctTV-Main Page')
		topicMain = HTML.ElementFromURL(topicURL, headers=check[1], cacheTime=None, encoding="Latin-1", errors="ignore")
	else:
		topicMain = HTML.ElementFromURL(topicURL, values=None, cacheTime=None, encoding="Latin-1", errors="ignore")

	# Read a string version of the page
	topicMainString = cleanHTML(urllib2.urlopen(check[0]).read())

	# Collect Video Archive List
	archives = getArchive(topicMainString)

	dir = MediaContainer(title1=sender.title2, title2=sender.itemTitle, viewGroup="Info")

	# OK this is horrible but it's a UI string thing so I'll leave it for now
	if sender.itemTitle == "News":
		title = "Aktuelle " + sender.itemTitle
	else:
		title = "Aktuell " + sender.itemTitle

	subtitle = topicMain.xpath("//*[@id='hauptbereich']/div[3]/h2")[0].text.encode('Latin-1').decode('utf-8')

	if ((sender.itemTitle == "News") or (sender.itemTitle == 'Computer-ABC')):
		summary = topicMain.xpath("//*[@id='hauptbereich']/div[3]/h1")[0].text
		if ((sender.itemTitle == "News")):
			summary = topicMain.xpath("//*/strong")
		else:
			summary += "\n\n" + topicMain.xpath("//*[@id='hauptbereich']/div[3]/p")[0].text
		
		if ((sender.itemTitle == "Computer-ABC")):
			summary = summary.encode('Latin-1').decode('utf-8').encode('Latin-1').decode('utf-8')
		elif ((sender.itemTitle == "News")):
			summary = summary.decode('utf-8')
		else:
			summary = summary.encode('Latin-1').decode('utf-8')

	else:
		summary = topicMain.xpath("//*[@id='hauptbereich']/div[3]/h1")[0].text
		summary += "\n\n" + Topic_Main.xpath("//*[@id='hauptbereich']/div[3]/p")[0].text
		summary += "\n\n" + Topic_Main.xpath("//*[@id='hauptbereich']/div[3]/content_ad_possible/p[1]")[0].text
		
		try:
			summary = summary.encode('Latin-1').decode('utf-8').encode('Latin-1').decode('utf-8')
		except:
			summary = summary.encode('Latin-1').decode('utf-8')

	#class WebVideoItem(self, url, title, subtitle=None, summary=None, duration=None, thumb=None, art=None, **kwargs):
	dir.Append(WebVideoItem(topicURL, title=title, subtitle=subtitle, summary=summary))
	archives.reverse()
	for url , thumb, alt, title in archives[2:]:
		if sender.itemTitle == "Schnurer hilft!":
			try: title = title.split('Video Schnurer hilft ')[1]
			except: title = 'Video Schnurer hilft '
		elif sender.itemTitle == "News":
			try: title= 'News' + title.split('Sendung')[1]
			except: pass
		elif sender.itemTitle == "Computer-ABC":
			try: title = "Was ist: " + title.split('ABC')[1]
			except: pass
		else:
			title = title.split('Video ')[1]

		(subtitle, summary) = getArchiveDetail(sender, URL)

		dir.Append(WebVideoItem(url, title=title, subtitle=subtitle, summary=summary, thumb=thumb))
	return dir

def getArchiveDetail(sender, url):
	check = getURL(URL, False)
	if check[1] != {None:None}:
		# Needed Authentication ctTV-Main Page')
		archiveMain = HTML.ElementFromURL(url, headers=check[1], cacheTime=None, encoding="Latin-1", errors="ignore")
	else:
		Archive_Main = HTML.ElementFromURL(url, cacheTime=None, encoding="Latin-1", errors="ignore")

	subtitle = archiveMain.xpath("//*[@id='hauptbereich']/div[3]/h2")[0].text.encode('Latin-1').decode('utf-8')

	if ((sender.itemTitle == "News") or (sender.itemTitle == 'Computer-ABC')):
		summary = archiveMain.xpath("//*[@id='hauptbereich']/div[3]/h1")[0].text
		if ((sender.itemTitle == "News")):
			summary = archiveMain.xpath("//*/strong")
		else:
			summary += "\n\n" + Archive_Main.xpath("//*[@id='hauptbereich']/div[3]/p")[0].text
		
		if ((sender.itemTitle == "Computer-ABC")):
			summary = summary.encode('Latin-1').decode('utf-8').encode('Latin-1').decode('utf-8')
		elif ((sender.itemTitle == "News")):
			summary = summary.decode('utf-8')
		else:
			summary = summary.encode('Latin-1').decode('utf-8')
			
	else:
		summary = archiveMain.xpath("//*[@id='hauptbereich']/div[3]/h1")[0].text
		summary += "\n\n" + Archive_Main.xpath("//*[@id='hauptbereich']/div[3]/p")[0].text
		
		try: summary += "\n\n" + Archive_Main.xpath("//*[@id='hauptbereich']/div[3]/content_ad_possible/p[1]")[0].text
		except: pass

		try: summary = summary.encode('Latin-1').decode('utf-8').encode('Latin-1').decode('utf-8')
		except:	summary = summary.encode('Latin-1').decode('utf-8')

	return (subtitle, summary)

def ArchiveMenu(sender, archiveList):
	dir = MediaContainer(title1=sender.title2, title2=sender.itemTitle, viewGroup="Info")

	archiveList.reverse()
	for url,thumb, alt, title in archiveList[2:]:
		dir.Append(Function(DirectoryItem(CurrentShowMenu, title=title, thumb=thumb), currentVideoURL=url, currentVideoTitle=title, themes=None))
	return dir


def getURL(url, installDefault=False):
	'''This function tries to get ID / PW from supplied URLs
If needed it can also set the DEFAULT handler with these credentials
making successive calls with no need to specify ID-PW'''

	# I have no idea where these come from. An unimplemented preferences perhaps?
	global Protected
	global Username
	global Password

	header = {None:None}

	req = urllib2.Request(URL)
	
	Log('(PLUG-IN) Try URL: %s %s' % (URL,req))
	
	try: handle = urllib2.urlopen(req)
	except: pass
	else:
		# Here the page isn't protected
		Protected = False
		Log('(PLUG-IN) URL is NOT protected')
		return (url , header)

	if not hasattr(e, 'code') or e.code != 401:
		# we got an error - but not a 401 error
		Log("(PLUG-IN) This page isn't protected by authentication.")
		Log('(PLUG-IN) But we failed for another reason. %s' % (e.code))
		return (None, None)

	authline = e.headers['www-authenticate']
	# this regular expression is used to extract scheme and realm
	matchobj = re.match(r'(?:\s*www-authenticate\s*:)?\s*(\w*)\s+realm=['"]([^'"]+)['"]', authline, re.IGNORECASE)

	if not matchobj:
		# if the authline isn't matched by the regular expression
		# then something is wrong
		Log('(PLUG-IN) The authentication header is badly formed.')
		Log('(PLUG-IN) Authline: %s' % (authline))
		Protected = True
		return (None, None)

	scheme = matchobj.group(1)
	realm = matchobj.group(2)
	# here we've extracted the scheme
	# and the realm from the header
	if scheme.lower() != 'basic':
		Log('(PLUG-IN) This function only works with BASIC authentication.')
		Protected = True
		return (None, None)

	if installDefault:
		# Create an OpenerDirector with support for Basic HTTP Authentication...
		auth_handler = urllib2.HTTPBasicAuthHandler()
		auth_handler.add_password(realm=realm, uri=url, user=Username, passwd=Password)
		opener = urllib2.build_opener(auth_handler)
		# ...and install it globally so it can be used with urlopen.
		urllib2.install_opener(opener)

		# All OK :-)
		Protected = True
		return (url, header)

	base64string = base64.encodestring('%s:%s' % (Username, Password))[:-1]
	authheader = "Basic %s" % base64string
	req.add_header("Authorization", authheader)
	header = {"Authorization": authheader}

	try: handle = urllib2.urlopen(req)
	except IOError:
		# here we shouldn't fail if the username/password is right
		Log("(PLUG-IN) It looks like the username or password is wrong.")
		Protected = True
		return (None, None)

	# All OK :-) # What does this even mean ???
	Protected = True

	return (req, header)

def cleanHTML(text, skipchars=[], extra_careful=1):
	'''This is an attempt to get rid of " &auml; " etc within a string
Still working on it ... any help appreicated.'''

	entitydefs_inverted = {}

	for k,v in entitydefs.items():
		entitydefs_inverted[v] = k

	badchars_regex = re.compile('|'.join(entitydefs.values()))
	been_fixed_regex = re.compile('&\w+;|&#[0-9]+;')

	# if extra_careful we don't attempt to do anything to
	# the string if it might have been converted already.
	if extra_careful and been_fixed_regex.findall(text):
		return text

	if type(skipchars) == type('s'):
		skipchars = [skipchars]

	keyholder= {}
	for x in badchars_regex.findall(text):
		if x not in skipchars:
			keyholder[x] = 1
	text = text.replace('&','&amp;')
	text = text.replace('\x80', '&#8364;')
	for each in keyholder.keys():
		if each == '&':
			continue

		better = entitydefs_inverted[each]
		if not better.startswith('&#'):
			better = '&%s;'%entitydefs_inverted[each]

		text = text.replace(each, better)
	return text
