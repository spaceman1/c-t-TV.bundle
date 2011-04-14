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
#from lxml.etree import fromstring, tostring
#from BeautifulSoup import BeautifulSoup
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
	(MainTitle, MainSubtitle, CurrentVideoTitle, CurrentVideoURL, Themes, topics, Archive) = LoadFP()
	dir = MediaContainer(title1=MainTitle, title2=MainSubtitle, viewGroup="List")
	dir.Append(Function(DirectoryItem(CurrentShowMenu, title=CurrentVideoTitle), CurrentVideoURL=CurrentVideoURL, CurrentVideoTITLE=CurrentVideoTitle, Themes=Themes))

	for url, title in topics:
		dir.Append(Function(DirectoryItem(TopicMenu, title=title), TopicURL=url))

	# Add the ARCHIVE to the container
	dir.Append(Function(DirectoryItem(ArchiveMenu, title="Sendungsarchiv"), ArchiveList = Archive))
	return dir

def CurrentShowMenu(sender, CurrentVideoURL, CurrentVideoTITLE, Themes):
	dir = MediaContainer(title1=sender.title2, title2=CurrentVideoTITLE, viewGroup="Info")
	dir.Append(WebVideoItem(CurrentVideoURL, CurrentVideoTITLE))

	check = getURL(CurrentVideoURL, False)
	if check[1] != {None:None}:
		# Needed Authentication ctTV-Main Page
		Show_Main = HTML.ElementFromURL(CurrentVideoURL, headers=check[1], cacheTime=None, encoding="Latin-1", errors="ignore")
	else:
		Show_Main = HTML.ElementFromURL(CurrentVideoURL, cacheTime=None, encoding="Latin-1", errors="ignore")

	themes = getThemes(Show_Main)

	for url, title, summary in themes:
		dir.Append(WebVideoItem(url, title=title, summary=summary))

	return dir

def LoadFP():
	OLDMENU = ""

	MenuItems = []
	Page_Items = []

	# Test if we need ID - PW ... and get it
	check = getURL(ROOT_URL, False)

	# Build a TREE representation of the page
	# Do we need to add the AUTHENTICATION header
	if check[1] != {None:None}:
		# Needed Authentication ctTV-Main Page
		ctTV_Main = HTML.ElementFromURL(ROOT_URL, headers=check[1], cacheTime=0, encoding="Latin-1", errors="ignore")
	else:
		ctTV_Main = HTML.ElementFromURL(ROOT_URL, cacheTime=0, encoding="Latin-1", errors="ignore")

	# Read a string version of the page
	ctTV_MainString = cleanHTML(urllib2.urlopen(check[0]).read())

	# Get some MAIN Meta-Data of c't TV:
	MainTitle = ctTV_Main.xpath("/html/body/div[@id='navi_top']/div[1]/ul[1]/li[2]/a")[0]
	MainTitle = tostring(MainTitle).split('">')[1][:-4].replace('<span>','').replace('</span>','').encode('Latin-1').decode('utf-8')
	MainSubtitle = ctTV_Main.xpath("/html/body/div[@id='navi_top']/div[1]/ul[3]/li[4]/a")[0].text.encode('Latin-1').decode('utf-8')

	# Define current video
	CurrentVideoTitle1 = ctTV_Main.xpath("//*[@id='hauptbereich']/div[@id='video']/h1/text()")[0].encode('Latin-1').decode('utf-8')
	CurrentVideoTitle2 = ctTV_Main.xpath("//*[@id='hauptbereich']/div[@id='video']/h1")[0]
	CurrentVideoTitle2 = tostring(CurrentVideoTitle2).split('|')[1].split('<')[0].encode('Latin-1').decode('utf-8')
	CurrentVideoTitle = CurrentVideoTitle1 + '|' + CurrentVideoTitle2
	CurrentVideoURL = ROOT_URL

	# Collect Theme List
	Themes = getThemes(ctTV_Main)

	# Collect Topic List
	Topics = getTopics(ctTV_Main)

	# Collect Video Archive List
	Archive = getArchive(ctTV_MainString)


	return (MainTitle, MainSubtitle, CurrentVideoTitle, CurrentVideoURL, Themes, Topics, Archive)

def getThemes(WebPageTree):
	# Get the list of Themes from the Element Tree
	Themelist = WebPageTree.xpath("//*[@id='themenuebersicht']/ul/li/a")

	# How many did we get?
	anzahl_themen = len(Themelist)

	Themes = []
	for Thema in range(0,anzahl_themen):
		ThemenSet = Themelist[Thema]
		try:
			URL = BASE_URL + ThemenSet.get('href')
		except:
			URL = "URL Error"
		
		try:
			TITEL = str(Thema+1) + ". Teil: " + WebPageTree.xpath("//*[@id='themenuebersicht']/ul/li/a/span[@class='titel']/text()")[Thema].encode('Latin-1').decode('utf-8')
		except:
			TITEL = "Titel Error"

		try:
			DESCRIPTION = WebPageTree.xpath("//*[@id='themenuebersicht']/ul/li/a/span[@class='beschreibung']/text()")[Thema].encode('Latin-1').decode('utf-8')
		except:
			DESCRIPTION = "DESCRIPTION Error"

		if URL != "": Themes = Themes + [(URL,TITEL,DESCRIPTION)]

	return Themes


def getTopics(WebPageTree):
	Topiclist = WebPageTree.xpath("//*[@id='navigation-rubriken']/li/a")
	anzahl_Topics = len(Topiclist)

	Topics = []
	# Get the URL and TITLE for each Topic
	for Topic in range(0,anzahl_Topics):
		TopicSet = Topiclist[Topic]
		try:
			URL = BASE_URL + TopicSet.get('href')
		except:
			URL = "URL Error"

		try:
			TITEL = WebPageTree.xpath("//*[@id='navigation-rubriken']/li/a")[Topic].text_content().encode('utf-8') #.decode('utf-8').encode('Latin-1').decode('utf-8')
			if isinstance(TITEL, str):
				TITEL = unicode(TITEL,'utf-8')
		except:
			TITEL = "Titel Error"
		
		if URL != "": Topics = Topics + [(URL,TITEL)]

	Log(len(Topics))

	return Topics

def getArchive(ctTV_MainString):
	WebPageTree = ctTV_MainString.split('<script type="text/javascript">')[1].split("</div> \<script\> var scrollto_mini")[0][17:]
	Archivelist = BeautifulSoup(WebPageTree).findAll('a')
	Log(len(Archivelist))
	anzahl_Archives = len(Archivelist)

	Archives = []
	for Show in range(0,anzahl_Archives-2):
		ArchiveSet = Archivelist[Show]
		# We have to TRY each attribute as not all stations have all attributes.
		try:
			URL = BASE_URL + ArchiveSet.get('href')
		except:
			URL = "URL Error"

		try:
			THUMB = BASE_URL + ArchiveSet.find('img').get('src')
		except:
			THUMB = "THUMB Error"

		try:
			ALT = ArchiveSet.find('img').get('alt')
		except:
			ALT = "ALT Error"

		try:
			TITEL = ArchiveSet.find('img').get('title')[:-2].replace('-',' ').encode('Latin-1').decode('utf-8')
		except:
			TITEL = "Titel Error"

		if URL != "":
			Archives = Archives + [(URL,THUMB, ALT, TITEL)]

	Log(len(Archives))

	return Archives

def TopicMenu(sender, TopicURL):
	global FrontPage

	if len(FrontPage) == 0:
		FrontPage = LoadFP()

	# Test if we need ID - PW ... and get it
	check = getURL(TopicURL, False)

	# Build a TREE representation of the page
	# Do we need to add the AUTHENTICATION header
	if check[1] != {None:None}:
		Log('(PLUG-IN) Needed Authentication ctTV-Main Page')
		Topic_Main = HTML.ElementFromURL(TopicURL, values=None, headers=check[1], cacheTime=None, encoding="Latin-1", errors="ignore")
	else:
		Topic_Main = HTML.ElementFromURL(TopicURL, values=None, cacheTime=None, encoding="Latin-1", errors="ignore")

	# Read a string version of the page
	Topic_MainString = cleanHTML(urllib2.urlopen(check[0]).read())

	# Collect Video Archive List
	ArchiveList = getArchive(Topic_MainString)

	dir = MediaContainer(art = MainArt, title1=sender.title2, title2=sender.itemTitle, viewGroup="Info")

	if sender.itemTitle == "News":
		TITEL = "Aktuelle " + sender.itemTitle

	else:
		TITEL = "Aktuell " + sender.itemTitle

	SUBTITLE = Topic_Main.xpath("//*[@id='hauptbereich']/div[3]/h2")[0].text_content().encode('Latin-1').decode('utf-8')

	if ((sender.itemTitle == "News") or (sender.itemTitle == 'Computer-ABC')):
		SUMMARY = Topic_Main.xpath("//*[@id='hauptbereich']/div[3]/h1")[0].text_content()
		TEMP = ""
		if ((sender.itemTitle == "News")):
			SUMMARY = Topic_Main.xpath("//*/strong")
			for item in range(0,len(SUMMARY)):
				try:
					TEMP = TEMP + str(SUMMARY[item].text_content().encode('Latin-1')) + '\n\n'
				except:
					TEMP = TEMP + str(SUMMARY[item].text_content()) + '\n\n'
			SUMMARY = TEMP
		else:
			SUMMARY = SUMMARY + "\n\n" + Topic_Main.xpath("//*[@id='hauptbereich']/div[3]/p")[0].text_content()
		
		if ((sender.itemTitle == "Computer-ABC")):
			SUMMARY = SUMMARY.encode('Latin-1').decode('utf-8').encode('Latin-1').decode('utf-8')
		elif ((sender.itemTitle == "News")):
			SUMMARY = SUMMARY.decode('utf-8')
		else:
			SUMMARY = SUMMARY.encode('Latin-1').decode('utf-8')

	else:
		SUMMARY = Topic_Main.xpath("//*[@id='hauptbereich']/div[3]/h1")[0].text_content()
		SUMMARY = SUMMARY + "\n\n" + Topic_Main.xpath("//*[@id='hauptbereich']/div[3]/p")[0].text_content()
		SUMMARY = SUMMARY + "\n\n" + Topic_Main.xpath("//*[@id='hauptbereich']/div[3]/content_ad_possible/p[1]")[0].text_content()
		
		try:
			SUMMARY = SUMMARY.encode('Latin-1').decode('utf-8').encode('Latin-1').decode('utf-8')
		except:
			SUMMARY = SUMMARY.encode('Latin-1').decode('utf-8')

	#class WebVideoItem(self, url, title, subtitle=None, summary=None, duration=None, thumb=None, art=None, **kwargs):
	dir.Append(WebVideoItem(  TopicURL,
					TITEL,
					subtitle = SUBTITLE,
					summary = SUMMARY,
					duration = None,
					)
			 )

	anzahl_archivelist = len(ArchiveList)

	for Item in range(anzahl_archivelist-2,0,-1):
		(URL,THUMB, ALT, TITEL) = ArchiveList[Item]
		if sender.itemTitle == "Schnurer hilft!":
			try:
				TITEL = TITEL.split('Video Schnurer hilft ')[1]
			except:
				TITEL = 'Video Schnurer hilft '
		elif sender.itemTitle == "News":
			try:
				TITEL = 'News' + TITEL.split('Sendung')[1]
			except:
				TITEL = TITEL
		elif sender.itemTitle == "Computer-ABC":
			try:
				TITEL = "Was ist: " + TITEL.split('ABC')[1]
			except:
				TITEL = TITEL
		else:
			TITEL = TITEL.split('Video ')[1]

		(SUBTITLE, SUMMARY) = getArchiveDetail(sender, URL)

		dir.Append(WebVideoItem(  URL,
						TITEL,
						subtitle = SUBTITLE,
						summary = SUMMARY,
						duration = None,
						thumb = THUMB,
						)
				 )

	return dir

def getArchiveDetail(sender, URL):
	# Test if we need ID - PW ... and get it
	check = getURL(URL, False)

	# Build a TREE representation of the page
	# Do we need to add the AUTHENTICATION header
	if check[1] != {None:None}:
		Log('(PLUG-IN) Needed Authentication ctTV-Main Page')
		Archive_Main = HTML.ElementFromURL(URL, values=None, headers=check[1], cacheTime=None, encoding="Latin-1", errors="ignore")
	else:
		Archive_Main = HTML.ElementFromURL(URL, values=None, cacheTime=None, encoding="Latin-1", errors="ignore")

	SUBTITLE = Archive_Main.xpath("//*[@id='hauptbereich']/div[3]/h2")[0].text.encode('Latin-1').decode('utf-8')

	if ((sender.itemTitle == "News") or (sender.itemTitle == 'Computer-ABC')):
		SUMMARY = Archive_Main.xpath("//*[@id='hauptbereich']/div[3]/h1")[0].text_content()
		TEMP = ""
		if ((sender.itemTitle == "News")):
			SUMMARY = Archive_Main.xpath("//*/strong")
			for item in range(0, len(SUMMARY)):
				try:
					TEMP = TEMP + str(SUMMARY[item].text_content().encode('Latin-1')) + '\n\n'
				except:
					TEMP = TEMP + str(SUMMARY[item].text_content()) + '\n\n'
			SUMMARY = TEMP
		else:
			SUMMARY = SUMMARY + "\n\n" + Archive_Main.xpath("//*[@id='hauptbereich']/div[3]/p")[0].text_content()
		
		if ((sender.itemTitle == "Computer-ABC")):
			SUMMARY = SUMMARY.encode('Latin-1').decode('utf-8').encode('Latin-1').decode('utf-8')
		elif ((sender.itemTitle == "News")):
			SUMMARY = SUMMARY.decode('utf-8')
		else:
			SUMMARY = SUMMARY.encode('Latin-1').decode('utf-8')
			
	else:
		SUMMARY = Archive_Main.xpath("//*[@id='hauptbereich']/div[3]/h1")[0].text_content()
		SUMMARY = SUMMARY + "\n\n" + Archive_Main.xpath("//*[@id='hauptbereich']/div[3]/p")[0].text_content()
		try:
			SUMMARY = SUMMARY + "\n\n" + Archive_Main.xpath("//*[@id='hauptbereich']/div[3]/content_ad_possible/p[1]")[0].text_content()
		except:
			SUMMARY = SUMMARY

		try:
			SUMMARY = SUMMARY.encode('Latin-1').decode('utf-8').encode('Latin-1').decode('utf-8')

		except:
			SUMMARY = SUMMARY.encode('Latin-1').decode('utf-8')

	return (SUBTITLE, SUMMARY)

def ArchiveMenu(sender, ArchiveList):
	global FrontPage
	# Get the items for the FRONT page ... all top-level menu items
	if len(FrontPage) == 0:
		FrontPage = LoadFP()

	dir = MediaContainer(title1=sender.title2, title2=sender.itemTitle, viewGroup="Info")

	anzahl_shows = len(ArchiveList)

	for Show in range(anzahl_shows-2,0,-1):
		(URL,THUMB, ALT, TITEL) = ArchiveList[Show]
		dir.Append(Function(DirectoryItem(CurrentShowMenu,
							title = TITEL,
							subtitle= None,
							summary = None,
							thumb = THUMB,),
						CurrentVideoURL = URL,
						CurrentVideoTITLE = TITEL,
						Themes = None)
				 )
	return dir


def getURL(URL, InstallDefault = False ):
	'''This function tries to get ID / PW from supplied URLs
If needed it can also set the DEFAULT handler with these credentials
making successive calls with no need to specify ID-PW'''

	global Protected
	global Username
	global Password

	HEADER = {None:None}

	req = urllib2.Request(URL)
	
	Log('(PLUG-IN) Try URL: %s %s' % (URL,req))
	
	try: handle = urllib2.urlopen(req)
	except: pass
	else:
		# If we don't fail then the page isn't protected
		Protected = "No"
		Log('(PLUG-IN) URL is NOT protected')
		Log('(PLUG-IN) <==** EXIT getURL')
		return (URL,HEADER)

	if not hasattr(e, 'code') or e.code != 401:
		# we got an error - but not a 401 error
		Log("(PLUG-IN) This page isn't protected by authentication.")
		Log('(PLUG-IN) But we failed for another reason. %s' % (e.code))
		Log('(PLUG-IN) <==** EXIT getURL')
		return (None, None)

	authline = e.headers['www-authenticate']
	# this gets the www-authenticate line from the headers
	# which has the authentication scheme and realm in it

	authobj = re.compile(
		r'''(?:\s*www-authenticate\s*:)?\s*(\w*)\s+realm=['"]([^'"]+)['"]''',
		re.IGNORECASE)
	# this regular expression is used to extract scheme and realm
	matchobj = authobj.match(authline)

	if not matchobj:
		# if the authline isn't matched by the regular expression
		# then something is wrong
		Log('(PLUG-IN) The authentication header is badly formed.')
		Log('(PLUG-IN) Authline: %s' % (authline))
		Protected = "Yes"
		Log('(PLUG-IN) <==** EXIT getURL')
		return (None, None)

	scheme = matchobj.group(1)
	REALM = matchobj.group(2)
	# here we've extracted the scheme
	# and the realm from the header
	if scheme.lower() != 'basic':
		Log('(PLUG-IN) This function only works with BASIC authentication.')
		Protected = "Yes"
		Log('(PLUG-IN) <==** EXIT getURL')
		return (None, None)

	if InstallDefault:
		# Create an OpenerDirector with support for Basic HTTP Authentication...
		auth_handler = urllib2.HTTPBasicAuthHandler()
		auth_handler.add_password(realm=REALM,
						uri=URL,
						user=Username,
						passwd=Password)
		opener = urllib2.build_opener(auth_handler)
		# ...and install it globally so it can be used with urlopen.
		urllib2.install_opener(opener)

		# All OK :-)
		Protected = "Yes"
		Log('(PLUG-IN) ### Alles Ready ! via default Opener###')
		Log('(PLUG-IN) <==** EXIT getURL')
		return (URL, HEADER)

	base64string = base64.encodestring('%s:%s' % (Username, Password))[:-1]
	authheader = "Basic %s" % base64string
	req.add_header("Authorization", authheader)
	HEADER = {"Authorization": authheader}

	try: handle = urllib2.urlopen(req)
	except IOError:
		# here we shouldn't fail if the username/password is right
		Log("(PLUG-IN) It looks like the username or password is wrong.")
		Protected = "Yes"
		Log('(PLUG-IN) <==** EXIT getURL')
		return (None, None)

	# All OK :-)
	Protected = "Yes"

	return (req,HEADER)

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
