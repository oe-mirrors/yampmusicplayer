
# -*- coding: utf-8 -*-
#######################################################################
#
#	YAMP - Yet Another Music Player - Lyrics
#	Version 3.3.1 2023-12-24
#	Coded by  by AlfredENeumann (c)2016-2023
#	Support: www.vuplus-support.org, board.newnigma2.to
#
#	This program is free software; you can redistribute it and/or
#	modify it under the terms of the GNU General Public License
#	as published by the Free Software Foundation; either version 2
#	of the License, or (at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#######################################################################

from YampGlobals import *

from Components.ConfigList import ConfigListScreen
#from Components.FileList import FileList

from Components.Pixmap import Pixmap, MultiPixmap
from Components.ScrollLabel import ScrollLabel

#from Screens.InfoBarGenerics import InfoBarSeek #, InfoBarNotifications
from Screens.HelpMenu import HelpableScreen
from Screens.ChoiceBox import ChoiceBox
#from Screens.VirtualKeyBoard import VirtualKeyBoard

from twisted.web.client import downloadPage, getPage

from urllib import quote, quote_plus, unquote
from xml.etree.cElementTree import fromstring as xml_fromstring

#Lyricslist

from Components.GUIComponent import GUIComponent
from Components.MultiContent import MultiContentEntryText

from Components.Input import Input
from Screens.InputBox import InputBox

from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_VALIGN_CENTER, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER

from skin import parseFont, parsePosition, parseSize
from enigma import fontRenderClass
from enigma import eVideoWidget

import mutagen
from mutagen.apev2 import APEv2
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4
from mutagen.flac import Picture, FLAC, StreamInfo
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis

# our own modules
from __init__ import _
from YampConfig import YampConfigScreenV33
from YampLyricsFunctions import *
from YampBoxDisplay import *
from YampPixmaps import YampCoverArtPixmap

GETLYRICSTIMEOUT = 10

#class YampLyricsScreenV33Screen, InfoBarSeek):
class YampLyricsScreenV33(Screen,HelpableScreen):
	def __init__(self, session, parent, videoPreviewOnPar):

		try:
			Screen.__init__(self, session)
			with open(os.path.join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampLyrics.xml"), 'r') as f:
				self.skin = f.read()
			self.parent = parent
			self.videoPreviewOn = videoPreviewOnPar
		except Exception as e:
			LOG('YampLyricsScreen: init: EXCEPT: ' + str(e), 'err') 
	
		self["title"] = Label(_("YAMP Music Player Lyrics"))
		self.lyricslist = YampLyricsList()
		self.lyrics=''
		self.lyricsAzError = ''
		self.lyricsChartError = ''

		self.lyricsEditMode = False
		self.editIndex = 0
		self.copiedLine = ''
		self.pigElement = None
		self.par1 = None

		self["lyrics"] = self.lyricslist
		self["songtitle"] = Label ("")
		self["artist"] = Label ("")
		self["album"] = Label ("")
		self["Tracknr"] = Label(_("Track-No"))
		self["tracknr"] = Label("")
		self["Length"] = Label(_("length"))
		self["length"] = Label("")
		self["Date"] = Label(_("Date"))
		self["date"] = Label("")
		self["bitrate"] = Label("")

		self["providedby"] = Label (_("songtext provided by:"))
		self["provider"] = MultiPixmap()
		self["coverArt"] = YampCoverArtPixmap()
		self["cprovidedby"] = Label (_("Cover provided by:"))
		self["cprovider"] = MultiPixmap()
		
		self["key_red"] = Label (_("Exit"))
		self["key_green"] = Label ("")
		self["key_yellow"] = Label ("")
		self["key_blue"] = Label ("")

		# Action maps		
		self["Menuactions"] = HelpableActionMap(self,"YampActions",
		{
			"menu": (self.showMenu, _("Lyrics / Karaoke timestamp edit options")),				
			"play": (self.keyPlay, _("play title")),
			"pause": (self.keyPause, _("Pause/resume title")),
			"stop": (self.keyStop, _("Stop title")),
			"prevTitle": (self.previousEntry, _("Play previous title")),
			"nextTitle": (self.nextEntry, _("Play next title")),
			"exit": (self.keyExit, _("Close lyrics screen")),
			"altMoveTop": (self.skipToListbegin, _("Move to first line")),
			"altMoveEnd": (self.skipToListend, _("Move to last line")),
			"key1": (self.key1, _("jump back in title short")),
			"key3": (self.key3, _("jump forward in title short")),
			"key4": (self.key4, _("jump back in title middle")),
			"key6": (self.key6, _("jump forward in title middle")),
			"key7": (self.key7, _("jump back in title long")),
			"key9": (self.key9, _("jump forward in title long")),
		}, -2)

		self["actions"] = ActionMap(["YampActions", "YampOtherActions"], 
		{
			"red": self.keyExit,
			"ok": self.ok,
			"up": self.moveup,
			"down": self.movedown,
			"green": self.keyGreen,
			"yellow": self.keyYellow,
			"blue": self.keyBlue,
		}, -1)

		self["LyrHelpActions"] = ActionMap(["YampHelpActions"],
		{
			"help": self.showHelp,
		}, -2)

		self.onLayoutFinish.append(self.layoutFinished)
		self.onClose.append(self.cleanup)
		self.isDreamOS = os.path.exists("/var/lib/dpkg/status")
		self.triggerTimer = eTimer()
		if self.isDreamOS: self.triggerTimer_conn=self.triggerTimer.timeout.connect(self.triggerStartActions)
		else: self.triggerTimer.callback.append(self.triggerStartActions)
		self.updateTimer = eTimer()
		if self.isDreamOS: self.updateTimer_conn=self.updateTimer.timeout.connect(self.updateInfoCyclic)
		else: self.updateTimer.callback.append(self.updateInfoCyclic)
		self.lyricsAutoSaveTimer = eTimer()
		if self.isDreamOS: self.lyricsAutoSaveTimer_conn=self.lyricsAutoSaveTimer.timeout.connect(self.autoSaveLyrics)
		else: self.lyricsAutoSaveTimer.callback.append(self.autoSaveLyrics)

		self.LcdText = ''
		self.autoMoveOn = True
		self.allowTimeEdit = False
		self.songPos = 0
		self.songtitle = self.artist=self.album=''
		self.scrollMinLines = config.plugins.yampmusicplayer.lyricsMinLinesScroll.value
		self.scrollLine = config.plugins.yampmusicplayer.lyricsScrollLine.value - 1
		self.timeStampOffset = config.plugins.yampmusicplayer.lyricsOffsetTime.value  #milliseconds offset
		self.timeStampChanged = False
		self.lyrisFileChanged = False
		self.lyricsFileName=self.lyricsFileNameLrc=self.lyricsFileNameLong=self.lyricsFileNameLrcLong=self.lyricsFileActive=''
		self.pixNumCover = COVERS_NO
		self.coverArtFile = ''
		self.pixNumLyrics = LYRICSS_NO
		self.lyricsFoundPrio = LYRICSS_NO

		self.replaceText = self.parent.infoBarNaReplace
		self.waitForSaveAnswer = False

	def layoutFinished(self):
		try:
			self.findPigElement()
			self.showHideVideoPreview()
			self.setSongInfo()
		except Exception as e:
			LOG('YampLyricsScreen: layoutFinished: setSongInfo: EXCEPT: ' + str(e), 'err') 
		
		self.setTextGreenKey()
		self.setTextYellowKey()
		self.setTextBlueKey()
		self.triggerTimer.start(50,True)
		self.updateTimer.start(200,False)		#for autoMove
		
		try: self.getLyrics()
		except Exception as e:
			LOG('YampLyricsScreen: layoutFinished: getLyrics: EXCEPT: ' + str(e), 'err')
		try: self.lyricslist.selectionEnabled(1)
		except Exception as e:
			LOG('YampLyricsScreen: layoutFinished: selectionEnabled: EXCEPT: ' + str(e), 'err') 
		try: self.lyricslist.moveToIndex(0)
		except Exception as e:
			LOG('YampLyricsScreen: layoutFinished: moveToIndex: EXCEPT: ' + str(e), 'err') 


	def lyricsChanged(self):
		try:
			self["provider"].setPixmapNum(self.pixNumLyrics % LYRICSS_NO)
		except Exception as e:
			LOG('YampLyricsScreen: lyricsChanged: setPixmapNum: EXCEPT: ' + str(e), 'err')
		try:
			self.buildNewLyrics()
		except Exception as e:
			LOG('YampLyricsScreen: lyricsChanged: buildNewLyrics: EXCEPT: ' + str(e), 'err')
		self.setTextGreenKey()
			
#-----------------------------
# Show Lyrics methods
#
# 1. Look for lyrics in ID3 tag (for mp3s, flac), 2. Look for lyrics in lyrics directory, 3. Search lyrics with azlyrics.com 4. Search lyrics with chartlyrics.com
#1..4 are only the 4 methods; the actual search sequence is defined in the config

	def getLyrics(self):
		self.pixNumLyrics = LYRICSS_NO
		self.lyricsFoundPrio = LYRICSS_NO
		self.lyrics = _("Sorry, (still) no lyrics found")
		self.lyricsChanged()	#trigger buildNewLyrics (make list)
		
		try:
			if self.parent.playerState == STATE_PLAY:
				songFilename = self.parent.playlist.getServiceRefList()[self.parent.playlist.getCurrentIndex()].getPath()
			else:
				songFilename = self.parent.playlist.getServiceRefList()[self.parent.playlist.getSelectionIndex()].getPath()
			self.lyricsFileName,self.lyricsFileNameLong,self.lyricsFileNameLrc,self.lyricsFileNameLrcLong=getLyricsFileNames(songFilename)
		   			
		except Exception as e:
			LOG('YampLyricsScreen: getLyrics: songFileName: EXCEPT' + str(e), 'err')
		
		self.searchId3(songFilename)
		if self.pixNumLyrics != LYRICSS_NO: self.lyricsChanged()
			
		if self.searchFile(songFilename): self.lyricsChanged()
		self.searchAZlyrics()
		self.searchChartlyrics()

	#Lyrics search azlyrics.com
	def searchAZlyrics(self):
		import re
		import requests
		self.lyricsAzError = ''
		if config.plugins.yampmusicplayer.prioLyrics1.value == 'lyricsAZ': prio = 1
		elif config.plugins.yampmusicplayer.prioLyrics2.value == 'lyricsAZ': prio = 2
		elif config.plugins.yampmusicplayer.prioLyrics3.value == 'lyricsAZ': prio = 3
		elif config.plugins.yampmusicplayer.prioLyrics4.value == 'lyricsAZ': prio = 4
		else: return

		LOG('\n\nYampLyricsScreen: searchAzLyrics: Start:  artist: %s title: %s ' %(self.artist, self.songtitle), 'all')

		if self.lyricsFoundPrio < prio: return		#already found with higher priority
		artist = unicode(self.artist,'utf-8').lower()
		title = unicode(self.songtitle,'utf-8').lower()

		artist=self.replaceAzlyricsSpecial(artist)

		artistList = [artist]
		artistList.append(re.sub('^the', '', artist))	#remove leading 'the'
		artistList.append(re.sub('(feat)(.*)','',artist)) #remove 'featuring....'

		try:
			titleNoBrackets = re.sub('\([^)]*\)','', title)	#remove everything between brackets
		except Exception as e:
			LOG('YampLyricsScreen: searchAzLyrics:NoBrackets: title remove brackets: EXCEPT: ' + str(e), 'err')
		try:
			titleNoExt= re.sub('\-[\w|\d|"|\'|\s]*$','', title)	#remove everything beginning with last "-" (title extension)
			titleNoBrackNoExt= re.sub('\-[\w|\d|\s]*$','', titleNoBrackets)	#same without everything between brackets
		except Exception as e:
			LOG('YampLyricsScreen: searchAzLyrics:NoExt title remove Extension: EXCEPT: ' + str(e), 'err')

		title=self.replaceAzlyricsSpecial(title)
		titleNoBrackets=self.replaceAzlyricsSpecial(titleNoBrackets)
		titleNoExt=self.replaceAzlyricsSpecial(titleNoExt)
		titleNoBrackNoExt=self.replaceAzlyricsSpecial(titleNoBrackNoExt)

		titleList=[title,titleNoExt, titleNoBrackets,titleNoBrackNoExt]
		titleList.append(title[:-1])			 #remove last letter songtitle (maybe ' )
		titleList.append(titleNoBrackets[:-1])
		titleList.append(titleNoExt[:-1])		
		titleList.append(titleNoBrackNoExt[:-1])
		titleList.append(re.sub('^the', '', title))	#remove leading 'the'
		titleList.append(re.sub('^the', '', titleNoBrackets))
		titleList.append(re.sub('^the', '', titleNoExt))
		titleList.append(re.sub('^the', '', titleNoBrackNoExt))

		artistList = sorted(set(artistList), key=artistList.index) #remove doubles
		titleList = sorted(set(titleList), key=titleList.index)

		if len(artistList)==0 or len(titleList)==0: return
		servAnswer = 0
		servReason = ''
		user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'
		headers = {'User-Agent': user_agent}
		base = 'https://www.azlyrics.com/'
		baselyrics = base + 'lyrics/'
		try:
			found = False
			for a in artistList:
				if found: break
				for t in titleList:
					resp = self.checkAzlyricsOptions(baselyrics,headers,a,t)
					if type(resp) == str:	#SSL Error
						servAnswer = resp
						servReason=''
						break
					else:	
						if resp.status_code == 200:
							found = True
							break
						else:	
							servAnswer = resp.status_code
							servReason = resp.reason
		except Exception as e:
			LOG('\n\nYampLyricsScreen: searchAzLyrics: resp: EXCEPT: ' + str(e), 'err')

		try:
			from bs4 import BeautifulSoup
			if type(resp) == str:	#SSL Error
				l = None
			else:	
				soup = BeautifulSoup(resp.content, "html.parser")
				l = soup.find_all("div", attrs={"class": None, "id": None})
			if not l:
				self.lyricsAzError = _("Not found on azlyrics. Answer from Server: ") + '\n'+ str(servAnswer) + ' ' + servReason
				if self.pixNumLyrics ==  LYRICSS_NO: #already found with lower priority? 
					self.lyrics = self.lyricsAzError + '\n\n' + self.lyricsChartError
					self.lyricsChanged()
			elif l:
				t = [x.getText() for x in l]
				self.lyrics = str(t[0])
				self.pixNumLyrics = LYRICSS_AZ
				self.lyricsFoundPrio = prio
				self.lyricsChanged()
		except Exception as e:
			LOG('YampLyricsScreen: searchAZlyrics: BeautifulSoup: EXCEPT: ' + str(e), 'err')

	def checkAzlyricsOptions(self,baselyrics, headers, artist, title):
		import requests
		search_url = baselyrics + artist + "/" + title + ".html"
		try:
			resp = requests.get(search_url, headers=headers, allow_redirects=True, verify=False)
		except Exception as e:
			resp = str(e)
			LOG('YampLyricsScreen: checkAzlyricsOptions: EXCEPT: ' + str(e), 'err')
		return resp

	def replaceAzlyricsSpecial(self, text):
		import re
		text=re.sub(r'[(,),\',\-,\s]','',text)
		text = text.replace("’", "").replace("!","i")
		text = text.replace('ä','a').replace('ö','o').replace('ü','u')
		return text

#---------- hier war genius

	#Lyrics search chartlyrics.com
	def searchChartlyrics(self):
		self.lyricsChartError = ''
		if config.plugins.yampmusicplayer.prioLyrics1.value == 'lyricsChart': prio = 1
		elif config.plugins.yampmusicplayer.prioLyrics2.value == 'lyricsChart': prio = 2
		elif config.plugins.yampmusicplayer.prioLyrics3.value == 'lyricsChart': prio = 3
		elif config.plugins.yampmusicplayer.prioLyrics4.value == 'lyricsChart': prio = 4
		else: return

		if self.lyricsFoundPrio < prio: return		#already found with higher priority

		artist = self.artist.replace("'","")
		title = self.songtitle.replace("'","")
		if artist and title:
			url = "http://api.chartlyrics.com/apiv1.asmx/SearchLyricDirect?artist=%%22%s%%22&song=%%22%s%%22" % (quote(artist), quote(title))
			try:
				getPage(url, timeout=GETLYRICSTIMEOUT).addCallback(self.getLyricsParseXML,prio).addErrback(self.getChartlyricsFailed)
			except Exception as e:
				LOG('YampLyricsScreen: searchChartlyrics: getPage: EXCEPT: ' + str(e), 'err')
				
	def getLyricsParseXML(self, xmlstring, prio):

		if self.lyricsFoundPrio < prio: return		#already found with higher priority
		xmlElement = xml_fromstring(xmlstring)
		lyrics = htmlUnescape(unquote(xmlElement.findtext("{http://api.chartlyrics.com/}Lyric").encode("utf-8", 'ignore')))
		title = htmlUnescape(unquote(xmlElement.findtext("{http://api.chartlyrics.com/}LyricSong").encode("utf-8", 'ignore')))
		artist = htmlUnescape(unquote(xmlElement.findtext("{http://api.chartlyrics.com/}LyricArtist").encode("utf-8", 'ignore')))
		if lyrics:
			try:
				self.lyrics = lyrics
				self.pixNumLyrics = LYRICSS_CHARTL
				self.lyricsFoundPrio = prio
				self.lyricsChanged()
			except Exception as e:
				LOG('YampLyricsScreen: getLyricsParseXML: self.lyrics: EXCEPT: ' + str(e), 'err')
		else:
			self.lyricsChartError = _('Lyrics for this title not found on chartlyrics.com')
			if self.pixNumLyrics ==  LYRICSS_NO: #already found with lower priority? 
				self.lyrics = self.lyricsAzError + '\n\n' + self.lyricsChartError
				self.lyricsChanged()
			
		
	def getChartlyricsFailed(self,result):
		self.lyricsChartError = _("Access to chartlyrics.com failed.") + "\n\n%s" % str(result.getErrorMessage())
		if self.pixNumLyrics ==  LYRICSS_NO: #already found with lower priority? 
			self.lyrics = self.lyricsAzError + '\n\n' + self.lyricsChartError
			if self.lyricsFoundPrio == LYRICSS_NO: self.lyricsChanged()
		
	#Lyrics search ID3	
	def searchId3(self,songFilename):
		lyrics, pixNumLyrics,self.lyricsFoundPrio = getLyricsID3(songFilename,self.lyricsFoundPrio)
		if lyrics != '': 
			self.lyrics = lyrics
			self.pixNumLyrics = pixNumLyrics

	#Lyrics search file
	def searchFile(self,songFilename):
		lyrics, self.lyricsFileActive, self.lyricsFoundPrio = searchLyricsfromFiles(songFilename, self.lyricsFoundPrio)
		if lyrics == '': return False

		self.lyrics = lyrics
		if config.plugins.yampmusicplayer.useSingleLyricsPath.value: self.pixNumLyrics = LYRICSS_LYRDIR
		else: self.pixNumLyrics = LYRICSS_FILE
		return True

#--------------------- edit karaoke timestamp		
	def setTimestamp(self):
		if not self.allowTimeEdit: return
		try:
			selIndex = self["lyrics"].getSelectionIndex()
			index = selIndex + self.startIndex
		except Exception as e:
			LOG('YampLyricsScreen: setTimestamp: set index: EXCEPT: ' + str(e), 'err')
		try:
			milliseconds = (self.songPos / 90) - self.timeStampOffset
			if milliseconds < 0: milliseconds = 10
			minutes = milliseconds / 60000
			seconds = (milliseconds % 60000) / 1000.0
		except Exception as e:
			LOG('YampLyricsScreen: setTimestamp: calculate time: EXCEPT: ' + str(e), 'err')
		try:
			self.tiStamp[index]='[%02d:%05.2f]' %(minutes,seconds)
			self.timeStampChanged = True
		except Exception as e:
			LOG('YampLyricsScreen: setTimestamp: tiStamp: EXCEPT: ' + str(e), 'err')
		try:
			self.buildLyricsMenuList(self.txtLines[self.startIndex:],self.tiStamp[self.startIndex:])
		except Exception as e:
			LOG('YampLyricsScreen: setTimestamp: buildLyricsMenuList: EXCEPT: ' + str(e), 'err')
		self.movedown()

	def autoMove(self):
		if not self.autoMoveOn: return
		try:
			for index in range(len(self.tiStampMsec90)-1, -1, -1):
				if self.songPos >= self.tiStampMsec90[index] and self.tiStampMsec90[index] != 0:
					#new textline has to be displayed
					try:	
						if index < self.startIndex:			#list has been manually scrolled down -> scroll back
							self.startIndex = index
							if self.allowTimeEdit: self.buildLyricsMenuList(self.txtLines[self.startIndex:],self.tiStamp[self.startIndex:])
							else: self.buildLyricsMenuList(self.txtLines[self.startIndex:])
					except Exception as e:
						LOG('YampLyricsScreen: autoMove: index < self.startIndex: EXCEPT: ' + str(e), 'err')
					
					self.lyricslist.moveToIndex(index-self.startIndex)
					if self.txtLines[index].strip() == '': self.movedown()
					
					#check scrolling
					if self.lenLyricslist > self.scrollMinLines:		#only scroll when more lines than page  
						while self["lyrics"].getSelectionIndex() > self.scrollLine:
							self.startIndex += 1   
							if self.allowTimeEdit: self.buildLyricsMenuList(self.txtLines[self.startIndex:],self.tiStamp[self.startIndex:])
							else: self.buildLyricsMenuList(self.txtLines[self.startIndex:])
					break
		except Exception as e:
			LOG('YampLyricsScreen: autoMove: index: EXCEPT: ' + str(e), 'err')
		
			
	def moveup(self):
		self["lyrics"].up()
		try:
			sel = self["lyrics"].getSelection().text.strip()
		except Exception as e:
			LOG('YampLyricsScreen: moveup: getSelection: EXCEPT: ' + str(e), 'err') 
		try:
			selIndex =self["lyrics"].getSelectionIndex()
		except Exception as e:
			LOG('YampLyricsScreen: moveup: getSelectionIndex: EXCEPT: ' + str(e), 'err') 
		try:	
			if sel == '' and not self.lyricsEditMode and selIndex < self.scrollLine and self.startIndex == 0: 
				self.moveup()	#extra move empty line
		except Exception as e:		
			LOG('YampLyricsScreen: moveup: while: EXCEPT: ' + str(e), 'err') 

		#check scrolling
		try:	
			if selIndex > 0: 
				try:
					selIndex = self["lyrics"].getSelectionIndex()
				except Exception as e:
					LOG('YampLyricsScreen: moveup: selIndex: EXCEPT: ' + str(e), 'err') 
				if selIndex <= self.scrollLine and self.startIndex > 0:
					try:
						self.startIndex -= 1 
						if self.startIndex < 0: self.startIndex = 0 
						if self.allowTimeEdit: self.buildLyricsMenuList(self.txtLines[self.startIndex:],self.tiStamp[self.startIndex:])
						else: self.buildLyricsMenuList(self.txtLines[self.startIndex:])
					except Exception as e:
						LOG('YampLyricsScreen: moveup: buildLyricsMenuList: EXCEPT: ' + str(e), 'err') 
					try:
						self.lyricslist.moveToIndex(self.scrollLine)
					except Exception as e:
						LOG('YampLyricsScreen: moveup: moveToIndex: EXCEPT: ' + str(e), 'err') 
					try:
						sel = self["lyrics"].getSelection().text.strip()
						if sel == '' and not self.lyricsEditMode: self.moveup()
					except Exception as e:
						LOG('YampLyricsScreen: moveup: moveup end: EXCEPT: ' + str(e), 'err') 
		except Exception as e:
			LOG('YampLyricsScreen: moveup: check scrolling: EXCEPT: ' + str(e), 'err') 

			
	def movedown(self):
		self["lyrics"].down()
		try:
			sel =self["lyrics"].getSelection().text.strip()
		except:
			LOG('YampLyricsScreen: movedown: getSelection: EXCEPT: ' + str(e), 'err') 
		try:
			selIndex = self["lyrics"].getSelectionIndex()
		except Exception as e:
			LOG('YampLyricsScreen: movedown: getSelectionIndex: EXCEPT: ' + str(e), 'err') 
		try:	
			if sel == '' and not self.lyricsEditMode and ((selIndex <= self.scrollLine and self.startIndex == 0) or self.lenLyricslist <= self.scrollMinLines): 
				self.movedown()	#extra move empty line
		except Exception as e:		
			LOG('YampLyricsScreen: movedown extra: EXCEPT: ' + str(e), 'err') 

		#check scrolling
		try:	
			if self.lenLyricslist > self.scrollMinLines:		#only scroll when more lines than page 
				try:
					selIndex = self["lyrics"].getSelectionIndex()
				except Exception as e:
					LOG('YampLyricsScreen: movedown: selIndex: EXCEPT: ' + str(e), 'err') 
				if selIndex > self.scrollLine:   # and selIndex + self.startIndex <= len(self.txtLines)
					try:
						self.startIndex += 1
						if self.allowTimeEdit: self.buildLyricsMenuList(self.txtLines[self.startIndex:],self.tiStamp[self.startIndex:])
						else: self.buildLyricsMenuList(self.txtLines[self.startIndex:])
					except Exception as e:
						LOG('YampLyricsScreen: movedown: buildLyricsMenuList: EXCEPT: ' + str(e), 'err') 
					try:
						self.lyricslist.moveToIndex(self.scrollLine)
					except Exception as e:
						LOG('YampLyricsScreen: movedown: moveToIndex: EXCEPT: ' + str(e), 'err') 
					try:
						sel = self["lyrics"].getSelection().text.strip()
						if sel == '' and not self.lyricsEditMode: self.movedown()
					except Exception as e:
						LOG('YampLyricsScreen: movedown: movedown end: EXCEPT: ' + str(e), 'err') 
		except Exception as e:
			LOG('YampLyricsScreen: movedown: check scrolling: EXCEPT: ' + str(e), 'err') 

	def autoSaveLyrics(self):	
		LOG('YampLyricsScreen: autoSaveLyrics start: autoSaveLyrics: %d' %(config.plugins.yampmusicplayer.autoSaveLyrics.value), 'all')
		try:
			import os
		except Exception as e:		
			LOG('YampLyricsScreen: autoSaveLyrics: import: EXCEPT: ' + str(e), 'err') 

		if not config.plugins.yampmusicplayer.autoSaveLyrics.value: return
		if not self.pixNumLyrics == LYRICSS_CHARTL and not self.pixNumLyrics == LYRICSS_AZ: return
		if (os.path.exists(self.lyricsFileNameLong) or os.path.exists(self.lyricsFileNameLrcLong)) and (os.path.isfile(self.lyricsFileNameLong) or os.path.isfile(self.lyricsFileNameLrcLong)): return
		self.saveLyrics()

	def saveLyrics(self):	
		try:
			index = 0
			text = ''
			for line in self.txtLines:
				text=text + self.tiStamp[index] + line + '\n'
				index +=1
			file = open(self.lyricsFileNameLong, "w")
			file.write(text)
			file.close()
			self.timeStampChanged = self.lyrisFileChanged = False
			self.session.open(MessageBox, _("Lyrics saved to %s") %(self.lyricsFileNameLong), type = MessageBox.TYPE_INFO,timeout = 5 )
		except Exception as e:
			LOG('YampLyricsScreen: saveLyrics: EXCEPT: ' + str(e), 'err') 
			self.session.open(MessageBox, _("Saving lyrics %s failed") %(self.lyricsFileNameLong), type = MessageBox.TYPE_WARNING,timeout = 10 )
			
	def overwriteConfirmed(self,answer):
		if answer: self.saveLyrics()

	def deleteConfirmed(self,answer):
		try:
			if answer:
				os.remove(self.lyricsFileActive)
				try:
					self.getLyrics()
				except Exception as e:
					LOG('YampLyricsScreen: deleteConfirmed: getlyrics: EXCEPT: ' + str(e), 'err') 
		except Exception as e:
			LOG('YampLyricsScreen: deleteConfirmed: EXCEPT: ' + str(e), 'err') 
		

			
	def setSongInfo(self):
		try:
			if self.parent.playerState == STATE_PLAY:  #actual playing title
				self.songtitle = self.parent.currTitle
				self.artist = self.parent.currArtist
				self.album = self.parent.currAlbum
				self.tracknr = self.parent.currTracknr
				self.bitrate = self.parent.currBitRate
				self.length = self.parent.currLength
				date = self.parent.currDate
			else:									   #selected title in playlist
				songFilename = self.parent.playlist.getServiceRefList()[self.parent.playlist.getSelectionIndex()].getPath()
				self.songtitle, self.album, genre, self.artist, date, self.length, self.tracknr, self.bitrate = readID3Infos(songFilename)

			self["songtitle"].setText(self.songtitle.replace('n/a',self.replaceText))
			self["artist"].setText(self.artist.replace('n/a',self.replaceText))
			self["album"].setText(self.album.replace('n/a',self.replaceText))
			if self.tracknr > 999:  #including CD-number
				self["tracknr"].setText(str(self.tracknr/1000) + '-' + str(self.tracknr%1000))
			elif self.tracknr > 0: 
				self["tracknr"].setText(str(self.tracknr))
			else: self["tracknr"].setText('')
			self["length"].setText(self.length.replace('n/a',self.replaceText))
			try:
				self["date"].setText(date)
			except Exception as e:
				LOG('YampLyricsScreen: setSongInfo: date: EXCEPT: ' + str(e), 'err') 
			self["bitrate"].setText(self.bitrate.replace('n/a',self.replaceText))
		except Exception as e:
			LOG('YampLyricsScreen: setSongInfo: EXCEPT: ' + str(e), 'err') 

	def setCover(self):
		lcdMode = config.plugins.yampmusicplayer.yampLcdMode.value
		if lcdMode != 'off' and lcdMode != 'running':
			self.summaries.setCover()

			if self.parent.playerState != STATE_PLAY:
				try:	
					path = self.parent.playlist.getServiceRefList()[self.parent.playlist.getSelectionIndex()].getPath()
					if path == None: path = '' 
					else:	
						title, album, genre, artist,date, length, tracknr, strBitrate = readID3Infos(path)
						self.parent.updateCover(artist, album, title, path)				
				except Exception as e:
					LOG('\nYampLyricsScreen: setCover: from playlistselection: EXCEPT: ' + str(e), 'err')

		try: 
			newCoverArtFile, newPixNumCover = self.parent.getCoverArtFile()
			actCoverArtFile = self["coverArt"].getFileName()
			if newCoverArtFile.strip().lower() != actCoverArtFile.strip().lower():
				self["coverArt"].showCoverArt(newCoverArtFile)
				self["cprovider"].setPixmapNum(newPixNumCover)
				LOG('YampLyricsScreen: setCover: setNewCover: coverArtFile: *%s*' %(newCoverArtFile), 'all')
		except Exception as e:
			LOG('YampLyricsScreen: setCover: EXCEPT: ' + str(e), 'err') 
			

	def updateInfoCyclic(self):
		if self.parent.playerState != STATE_PLAY: return
		self.showHideVideoPreview()

		try:
			len, self.songPos = self.parent.getSeekData()
		except Exception as e:
			LOG('YampLyricsScreen: updateInfoCyclic EXCEPT: ' + str(e), 'err')
		self.autoMove()
		if self.parent.coverChangedLyrics:
			self.parent.coverChangedLyrics = False
			self.setCover() 
		if self.parent.coverChangedGoogleLyrics:
			self.parent.coverChangedGoogleLyrics = False
			self.setCover() 
		if self.songtitle != self.parent.currTitle:		#new Song
			LOG('YampLyricsScreen: updateInfoCyclic: new song: songtitle: %s  parentsongtitle: %s' %(self.songtitle,self.parent.currTitle), 'all')
			if self.parent.currentIsVideo and not config.plugins.yampmusicplayer.showLyricsOnVideo.value:
				self.close()
				return

			self.allowTimeEdit = False
			self.setTextBlueKey()
			if self.timeStampChanged or self.lyrisFileChanged:
				self.waitForSaveAnswer = True
				self.timeStampChanged = self.lyrisFileChanged = False
				self.setTextGreenKey()
				self.session.openWithCallback(self.saveConfirmed, MessageBox, _("Lyrics have been changed\nDo yo want to save the lyrics file?"), default = True)
				return
			if self.waitForSaveAnswer: return
			
			self.setSongInfo()
			self.setLcdText()
			self.getLyrics()
			self.autoMoveOn = True
			self.setTextYellowKey()
			self.setTextBlueKey()

	def saveConfirmed(self,answer):
		if answer: self.saveLyrics()
		self.waitForSaveAnswer = False

			
	def buildNewLyrics(self):
		LOG('YampLyricsScreen: buildNewLyrics: Start', 'all')
		self.lyrics = lyricsClean(self.lyrics)

		try:
			self.tiStamp, self.tiStampMsec90, self.txtLines, tStampMin = textToList(self.lyrics)
		except Exception as e:
			LOG('YampLyricsScreen: buildNewLyrics: textToList: EXCEPT: ' + str(e), 'err')
		try:
			self.buildLyricsMenuList(self.txtLines)
		except Exception as e:
			LOG('YampLyricsScreen: buildNewLyrics: buildLyricsMenuList: EXCEPT: ' + str(e), 'err')
		try:
			self.startIndex = 0	
			self.lenLyricslist = len(self.lyricslist)
			self.lyricslist.moveToIndex(0)		
		except Exception as e:
			LOG('YampLyricsScreen: buildNewLyrics: setparameters: EXCEPT: ' + str(e), 'err')
		try:
			if self.lyricsAutoSaveTimer.isActive(): self.lyricsAutoSaveTimer.stop() 
			self.lyricsAutoSaveTimer.start((GETLYRICSTIMEOUT + 10)*1000,True)
		except Exception as e:
			LOG('YampLyricsScreen: buildNewLyrics: autosavelyrics: EXCEPT: ' + str(e), 'err')

	def buildLyricsMenuList(self, text, timeStamp=None):
		self.lyricslist.list = []

		if len(text) > 1:
			self.lyricslist.list = []
		if timeStamp is None:
			try:
				self.lyricslist.setWithTimeStamp(False)
				for line in text:
					self.lyricslist.append(LyricslistEntryComponent(text = line))
			except:
				pass
		else:
			try:
				self.lyricslist.setWithTimeStamp(True)
				index = 0
				for line in text:
					self.lyricslist.append(LyricslistEntryComponent(text = line, tiStamp = timeStamp[index]))
					index += 1
			except Exception as e:
				LOG('YampLyricsScreen: buildLyricsMenuList: for line in text:  EXCEPT: ' + str(e) , 'err')
		self.lyricslist.updateList()
		if len(self.lyricslist) > 1:
			self.autoMove()
			
#--------------- user key reactions -----------

	def keyGreen(self):
		try:
			if (self.pixNumLyrics == LYRICSS_FILE or self.pixNumLyrics == LYRICSS_LYRDIR) and not self.allowTimeEdit and not self.timeStampChanged and not self.lyrisFileChanged:
				if os.path.exists(self.lyricsFileNameLong) and os.path.isfile(self.lyricsFileNameLong):
					self.lyricsFileActive = self.lyricsFileNameLong
				elif os.path.exists(self.lyricsFileName) and os.path.isfile(self.lyricsFileName):
					self.lyricsFileActive = self.lyricsFileName
					
				self.session.openWithCallback(self.deleteConfirmed, MessageBox, _("Do yo want to delete the lyrics file\n%s ?") %(self.lyricsFileActive), default = True)
			else: 
				if os.path.exists(self.lyricsFileNameLong) and os.path.isfile(self.lyricsFileNameLong):
					self.session.openWithCallback(self.overwriteConfirmed, MessageBox, _("Lyrics-file\n\n%s\n\nexisting already.\n\nDo you really want to overwrite ?") %(self.lyricsFileNameLong), default = False)
				else:	
					self.saveLyrics()
		except Exception as e:
			LOG('YampLyricsScreen: keyGreen: EXCEPT: ' + str(e), 'err') 

	def keyYellow(self):
		try:
			self.autoMoveOn = not self.autoMoveOn
			self.setTextYellowKey()
		except Exception as e:
			LOG('YampLyricsScreen: key_yellow: EXCEPT: ' + str(e), 'err') 

	def keyBlue(self):
		try:
			self.allowTimeEdit = not self.allowTimeEdit
			self.setTextBlueKey()
			if self.allowTimeEdit: 
				self.buildLyricsMenuList(self.txtLines[self.startIndex:],self.tiStamp[self.startIndex:])
				self.autoMoveOn = False
			else: 
				self.buildLyricsMenuList(self.txtLines[self.startIndex:])
			self.setTextYellowKey()
			self.setTextGreenKey()
		except Exception as e:
			LOG('YampLyricsScreen: keyBlue: EXCEPT: ' + str(e), 'err') 

	def keyPause(self):
		try: self.parent.pause()
		except Exception as e:
			LOG('YampLyricsScreen: pause: EXCEPT: ' + str(e), 'err') 

	def keyPlay(self):
		try:
			self.parent.play()
			self.showHideVideoPreview()
		except Exception as e:
			LOG('YampLyricsScreen: play: EXCEPT: ' + str(e), 'err') 

	def previousEntry(self):
		try: self.parent.previousEntry()
		except Exception as e:
			LOG('YampLyricsScreen: previousEntry: EXCEPT: ' + str(e), 'err') 

	def nextEntry(self):
		try: self.parent.nextEntry()
		except Exception as e:
			LOG('YampLyricsScreen: nextEntry: EXCEPT: ' + str(e), 'err') 
			
	def ok(self):
		try:
			self.setTimestamp()
		except Exception as e:
			LOG('YampLyricsScreen: ok: EXCEPT: ' + str(e), 'err') 

	def keyStop(self):
		self.parent.stopEntry()
		self.showHideVideoPreview()

	def key1(self):
		self.parent.seekOwn(1)

	def key3(self):
		self.parent.seekOwn(3)

	def key4(self):
		self.parent.seekOwn(4)

	def key6(self):
		self.parent.seekOwn(6)

	def key7(self):
		self.parent.seekOwn(7)

	def key9(self):
		self.parent.seekOwn(9)

	def keyPrevious(self):
		self.parent.seekOwn(11)

	def keyNext(self):
		self.parent.seekOwn(12)

	def skipToListbegin(self):
		try: self.lyricslist.moveToIndex(0)
		except: pass	

	def skipToListend(self):
		try: self.lyricslist.moveToIndex(len(self.lyricslist) - 1)
		except: pass	
		
	def keyExit(self):
		if self.timeStampChanged or self.lyrisFileChanged:
			self.session.openWithCallback(self.exitConfirmed, MessageBox, _("Lyrics  have been changed\nDo yo want to save before exit?"), default = True)
		else:
			self.close()
			
	def exitConfirmed(self,answer):
		if answer:
			self.saveLyrics()
		self.close()

	def showHelp(self):
		HelpableScreen.showHelp(self)

#--------------- lyrics edit functions

	def showMenu(self):						#Build Menu Entries
		menu = []
		try:
			if self.lyricsEditMode: menu.append(((_('deactivate edit mode (scroll over empty lines)' )), 'editmode'))
			else: menu.append(((_('activate edit mode (empty lines also accessible)' )), 'editmode'))
			menu.append(((_('edit selected line ' )), 'editline'))
			menu.append(((_('add line after current ' )), 'addline'))
			menu.append(((_('copy line ' )), 'copyline'))
			menu.append(((_('insert copied line after current ' )), 'insertline'))
			menu.append(((_('delete selected line' )), 'delline'))
			if max(self.tiStampMsec90) == 0: 
				menu.append(((_('No time data in lyrics, no time offset option')), 'noOffset'))
			else:
				offsetVal = float(config.plugins.yampmusicplayer.karaokeFileOffsetVal.value)/1000.0
				menu.append(((_('Set time stamp offset value for all times in file')), 'offsetval'))
				textPlus = _('Offset for timestamp (text later)     :   ') 
				textMinus = _('Offset for timestamp  (text earlier) :  -')
				strOffset = '%02.3f' %(offsetVal)
				pass
				menu.append(((textPlus + strOffset +' s'), 'offsetpos'))
				menu.append(((textMinus + strOffset +' s'), 'offsetneg'))
		except Exception as e:		
			LOG('YampLyricsScreen: showMenu: EXCEPT: ' + str(e), 'err') 

		if len(menu) >= 1:
			if self.parent.lyricsKarMsgboxShow:
				message = _("Lyrics Edit / Karaoke Timestamp Offset\n\nHint: You may try and test as much as you want, changes will be active 'on the fly' immediately, including offset in Karaoke Timestamp.\n\nYou will be asked before the file with any changes will be saved.\n\nThe different edit options also are described in the Help screen, Page 11. Reminder: Help Screen: INFO/EPG LONG\n\nDo you want to deactivate this message for the current session?")
				self.par1 = menu
				self.session.openWithCallback(self.karMsgboxShowCB, MessageBox, message, default = True, timeout = 20)
			else:
				self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_('Lyrics Editor / Karaoke Timestamp Offset'), list=menu)
			
		
	def karMsgboxShowCB(self,answer):
		self.parent.lyricsKarMsgboxShow = not answer
		self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_('Lyrics Editor / Karaoke Timestamp Offset'), list=self.par1)

	def menuCallback(self, choice):
		if choice is None or choice[1] == "noOffset": return 

		elif choice[1] == 'offsetval': 
			try:
				self.session.openWithCallback(self.inputOffsetCb, InputBox, title=_('Please enter timestamp offset value in milliseconds'),text=' ' * 10,maxSize=10, type=Input.NUMBER)
			except Exception as e:		
				LOG('YampLyricsScreen: menuCallback: OffsetValO EXCEPT: ' + str(e), 'err') 
			return	

		elif choice[1] == 'offsetpos' or choice[1] == 'offsetneg':
			offsetVal = float(config.plugins.yampmusicplayer.karaokeFileOffsetVal.value)
			if offsetVal == 0.0: return
			if choice[1] == 'offsetneg': offsetVal = offsetVal * (-1)
			try:
				addTimeOffset(offsetVal,self.tiStampMsec90,self.tiStamp)
				self.buildLyricsMenuList(self.txtLines,self.tiStamp)
				self.lyrisFileChanged = True
				self.setTextGreenKey()
			except Exception as e:		
				LOG('YampLyricsScreen: menuCallback: addTimeOffset EXCEPT: ' + str(e), 'err') 
			return

		try:
			self.editIndex = self["lyrics"].getSelectionIndex() + self.startIndex 
		except Exception as e:		
			LOG('YampLyricsScreen: menuCallback: editIndex EXCEPT: ' + str(e), 'err') 
		try:
			textLine = unicode(self['lyrics'].getSelection().text.strip())
		except Exception as e:		
			LOG('YampLyricsScreen: menuCallback editline: getSelection: EXCEPT: ' + str(e), 'err') 

		if choice[1] == 'editmode':
			self.lyricsEditMode = not self.lyricsEditMode
			return

		elif choice[1] == 'editline':
			try:
				self.session.openWithCallback(self.editLineCb, InputBox, title=_('Edit lyrics line '),text=textLine, type=Input.TEXT)
			except Exception as e:		
				LOG('YampLyricsScreen: menuCallback: InputBox editline EXCEPT: ' + str(e), 'err') 

		elif choice[1] == 'addline':
			try:
				self.session.openWithCallback(self.addLineCb, InputBox, title=_('Add lyrics line '),text='', type=Input.TEXT)
			except Exception as e:		
				LOG('YampLyricsScreen: menuCallback: InputBox editline EXCEPT: ' + str(e), 'err') 

		elif choice[1] == 'copyline':
			self.copiedLine = textLine

		elif choice[1] == 'insertline':
			try:
				newIdx = self.editIndex + 1
				self.tiStampMsec90.insert(newIdx,0)
				self.tiStamp.insert(newIdx,'[00:00.00]')
				self.txtLines.insert(newIdx, str(self.copiedLine))
				self.lyrisFileChanged = True
				self.setTextGreenKey()
			except Exception as e:		
				LOG('YampLyricsScreen: menuCallback: insertline EXCEPT: ' + str(e), 'err') 

		elif choice[1] == 'delline':
			try:
				delLyricsLine(self.editIndex,self.tiStampMsec90,self.tiStamp,self.txtLines)
				self.lyrisFileChanged = True
				self.setTextGreenKey()
			except Exception as e:		
				LOG('YampLyricsScreen: menuCallback: delLyricsLine EXCEPT: ' + str(e), 'err') 
		self.buildLyricsMenuList(self.txtLines[self.startIndex:])

	def inputOffsetCb(self,Result):
		try:
			if Result is not None:
				if Result.strip() != '':
					config.plugins.yampmusicplayer.karaokeFileOffsetVal.value = int(Result)
		except Exception as e:		
			LOG('YampLyricsScreen: inputOffsetCb: EXCEPT: ' + str(e), 'err')

	def editLineCb(self,Result):
		try:
			if Result is not None:
				self.txtLines[self.editIndex]= Result.strip()
				self.lyrisFileChanged = True
				self.setTextGreenKey()
		except Exception as e:		
			LOG('YampLyricsScreen: editLineCb: EXCEPT: ' + str(e), 'err')
		self.buildLyricsMenuList(self.txtLines[self.startIndex:])

	def addLineCb(self,Result):
		try:
			newIdx = self.editIndex + 1
			self.tiStampMsec90.insert(newIdx,0)
			self.tiStamp.insert(newIdx,'[00:00.00]')
			self.txtLines.insert(newIdx, Result.strip())
			self.lyrisFileChanged = True
			self.setTextGreenKey()
		except Exception as e:		
			LOG('YampLyricsScreen: addLineCb: EXCEPT: ' + str(e), 'err')
		self.buildLyricsMenuList(self.txtLines[self.startIndex:])

	
#--------------- help functions

	def setTextGreenKey(self):	
		if (self.pixNumLyrics == LYRICSS_FILE or self.pixNumLyrics == LYRICSS_LYRDIR) and not self.allowTimeEdit and not self.timeStampChanged and not self.lyrisFileChanged: self["key_green"].setText(_("Delete"))
		else: self["key_green"].setText(_("Save"))

	def setTextYellowKey(self):	
		if self.autoMoveOn: self["key_yellow"].setText(_("Auto move Off"))
		else: self["key_yellow"].setText(_("Auto move On"))

	def setTextBlueKey(self):		
		if self.allowTimeEdit: self["key_blue"].setText(_("Disallow time edit"))
		else:	self["key_blue"].setText(_("Allow time edit"))

	def triggerStartActions(self):
		self.setCover()
		self.setLcdText()
		
	def setLcdText(self):
		if config.plugins.yampmusicplayer.yampLcdMode.value == 'off': return
		if config.plugins.yampmusicplayer.yampLcdMode.value == 'running':
			self.updateLCDText(self.songtitle + ' - ' + self.artist + ' - ' + self.album,1)
		else:	
			self.updateLCDText(self.songtitle, 1)
			self.updateLCDText(self.artist, 2)
			self.updateLCDText(self.album, 3)


	def findPigElement(self): 
		self.pigElement=None
		if not 'fhd' in config.plugins.yampmusicplayer.yampSkin.value: return
		try:
			for element in self.renderer:
				if 'eVideoWidget' in str(vars(element)):
					self.pigElement = element
		except Exception as e:
			LOG('\nYampLyricsScreen: findPigElement: EXCEPT: ' + str(e), 'err')

	def showHideVideoPreview(self):
		if self.pigElement is not None:
			if self.videoPreviewOn == True:
				self.pigElement.instance.show()
			else: 
				self.pigElement.instance.hide()
		else:
			skin=config.plugins.yampmusicplayer.yampSkin.value
			if not 'fhd' in config.plugins.yampmusicplayer.yampSkin.value: return
			LOG('\nYampLyricsScreen:showHideVideoPreview: pigElementNone','err')
			
	def cleanup(self):
		self.triggerTimer.stop()
		self.updateTimer.stop()
		self.lyricsAutoSaveTimer.stop()
		del self.triggerTimer
		del self.updateTimer
		del self.lyricsAutoSaveTimer
		
	def updateLCDText(self, text, line):
		if config.plugins.yampmusicplayer.yampLcdMode.value == 'running':
			try:
				self.LcdText = text
			except:
				pass
		else:	
			self.summaries.setText(text,line)
		
	def getLcdText(self):	#for LCD Running Text
		return(self.LcdText)
		
	def createSummary(self):
		confLcd = config.plugins.yampmusicplayer.yampLcdMode.value
		if confLcd == 'off': return
		elif confLcd == 'running': return YampLCDRunningScreenV33
		else: return YampLCDScreenV33

	def lockShow(self):
		pass

	def unlockShow(self):
		pass


		
#######################################################################
#
#	class LyricsList
#			
#######################################################################

class YampLyricsList(GUIComponent):
	def __init__(self, enableWrapAround=False):   #!!!!
		GUIComponent.__init__(self)

		try:   #!!!evtl. noch andere Vorgaben fuer FHD
			self.itemFont = parseFont("Regular;18", ((1,1),(1,1)))
			self.myItemHeight = 23
		except Exception as e:
			LOG('YampLyricsList: init: setDefaults:  EXCEPT: ' + str(e), 'err') 
			
		self.isDreamOS = os.path.exists("/var/lib/dpkg/status")

		self.list = []
		self.withTimeStamp = False
		self.title = ""
		self.onSelectionChanged = [ ]
		self.enableWrapAround = enableWrapAround
		self.l = eListboxPythonMultiContent()
		try:
			self.l.setBuildFunc(self.buildEntry)
		except Exception as e:
			LOG('YampLyricsList:__init__:set self.l.setBuildFunc: EXCEPT: ' + str(e), 'err') 
		
	GUI_WIDGET = eListbox

	def buildEntry(self, item):

		self.w = self.l.getItemSize().width()
		self.h = self.myItemHeight
		res = [ None ]

		liney = int(self.fonth * 0.01) + 1
		lineh = int(self.fonth * 1.05)

		if self.withTimeStamp:
			if len(item.text.strip()) == 0: item.tiStamp = ''
			widthTiStamp = int(lineh * 4.5)
			res.append (MultiContentEntryText(pos=(0, liney), size=(widthTiStamp, lineh), font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = "%s" % item.tiStamp))
			res.append (MultiContentEntryText(pos=(widthTiStamp, liney), size=(self.w-widthTiStamp, lineh), font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = "%s" % item.text))
		else:
			res.append (MultiContentEntryText(pos=(0, liney), size=(self.w, lineh), font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = "%s" % item.text))
		return res

	def applySkin(self, desktop, parent):
		attribs = []
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "itemFont":
					self.itemFont = parseFont(value, ((1,1),(1,1)))
				else:
					attribs.append((attrib, value))

		self.fonth = int(fontRenderClass.getInstance().getLineHeight(self.itemFont))
		self.myItemHeight = int(self.fonth * 1.15)
		self.l.setItemHeight(self.myItemHeight)

		try:
			self.l.setFont(0, self.itemFont)
		except Exception as e:
			LOG('YampLyricsList: applySkin: setFont0 EXCEPT: ' + str(e), 'err') 
		try:
			self.skinAttributes = attribs
		except Exception as e:
			LOG('YampLyricsList: applySkin: SetskinAttributes EXCEPT: ' + str(e), 'err') 
		return GUIComponent.applySkin(self, desktop, parent)


	def postWidgetCreate(self, instance):
		try:
			pass
		except Exception as e:
			LOG('YampLyricsList: postWidgetCreate: Start: EXCEPT: ' + str(e), 'err')
		instance.setContent(self.l)
		if self.isDreamOS: instance.selectionChanged_conn=instance.selectionChanged.connect(self.selectionChanged)
		else: instance.selectionChanged.get().append(self.selectionChanged)
		if self.enableWrapAround:
			self.instance.setWrapAround(True)
		try:
			pass
		except Exception as e:
			LOG('YampLyricsList: postWidgetCreate: End: EXCEPT: ' + str(e), 'err')

	def preWidgetRemove(self, instance):
		instance.setContent(None)
		if self.isDreamOS: instance.selectionChanged_conn = None
		else: instance.selectionChanged.get().remove(self.selectionChanged)
		
	def selectionChanged(self):
		for f in self.onSelectionChanged:
			f()

	def updateList(self):
		self.l.setList(self.list)

	def moveToIndex(self, index):
		self.instance.moveSelectionTo(index)
		
	def append(self, item):
		self.list.append((item,))

	def selectionEnabled(self, enabled):
		if self.instance is not None:
			self.instance.setSelectionEnable(enabled)

	def pageUp(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.pageUp)

	def pageDown(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.pageDown)

	def up(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.moveUp)

	def down(self):
		if self.instance is not None:
			self.instance.moveSelection(self.instance.moveDown)

	def getSelection(self):
		return self.l.getCurrentSelection() and self.l.getCurrentSelection()[0]

	def getSelectionIndex(self):
		return self.l.getCurrentSelectionIndex()

	def getLyricsList(self):
		return self.list

	def setWithTimeStamp(self, withTimeStamp):
		self.withTimeStamp = withTimeStamp

	def setTitle(self, title):
		self.title = title

	def __len__(self):
		return len(self.list)


class LyricslistEntryComponent:
	def __init__(self, text = "", tiStamp=""):
		self.text = text
		self.tiStamp = tiStamp
