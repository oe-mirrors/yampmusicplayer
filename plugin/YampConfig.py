#######################################################################
#
# YAMP - Yet Another Music Player - YampConfig
# Version 3.3.2 2024-03-17
# Coded by JohnHenry (c)2013 (up to V2.6.5)
# Extended by AlfredENeumann (c)2016-2024
# Last change: 2025-09-27 by Mr.Servo @OpenATV
# Support: www.vuplus-support.org, board.newnigma2.to
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
#######################################################################

from os.path import join, exists, isfile
from enigma import eTimer, getDesktop
from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry, configfile
from Components.ConfigList import ConfigListScreen
from Components.FileList import FileList
from Components.Label import Label
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from .YampFileFunctions import readCustomCoverSize, writeVTIRunningRenderer, readRcButtonTexts
from .YampBoxDisplay import YampLCDRunningScreenV33, YampLCDScreenV33
from .YampGlobals import yampDir
from .myLogger import LOG
from . import _

TEXTLCD = _('Configuration')


class YampConfigScreenV33(Screen, ConfigListScreen):

	def __init__(self, session, parent, videoPreviewOnPar):
		Screen.__init__(self, session)
		xmlfile = join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampConfig.xml")
		if not exists(xmlfile):
			LOG('YampConfigScreenV33: __init__: File not found: "%s"' % xmlfile, 'err')
			return
		with open(xmlfile, 'r') as f:
			self.skin = f.read()
		self.parent = parent
		self.videoPreviewOn = videoPreviewOnPar
		if getDesktop(0).size().width() > 1280:
			WIDTH = 151
		else:
			WIDTH = 130
		EMPTYLINE = "".ljust(WIDTH, " ")
		dummy1, self.txtRcPvrVideo, txtBouq = readRcButtonTexts()
		self.list = []
		self.callingKeyLeft = False
		self.groupIdx = []
		self.buildConfig()
		ConfigListScreen.__init__(self, self.list, session, on_change=self.changedEntry)
		self["title"] = Label(_("YAMP Music Player Configuration"))
		self["help"] = Label()
		self["key_yellow"] = Label("")
		self["textBouquet"] = Label("")
		self["setupActions"] = ActionMap(["YampActions", "YampOtherActions"],
		{
			"prevBouquet": self.pageup,
			"nextBouquet": self.pagedown,
			"red": self.keyExit,
			"exit": self.keyExit,
			"green": self.keyGreen,
			"blue": self.keyBlue,
			"yellow": self.keyYellow,
			"ok": self.keyOK,
		}, -1)
		self.onLayoutFinish.append(self.layoutFinished)
		self.onClose.append(self.cleanup)
		self.startTimer = eTimer()
		self.startTimer.callback.append(self.startActions)
		self.updateTimer = eTimer()
		self.updateTimer.callback.append(self.updateTimerActions)
		self.LcdText = ''
		# save previous values to detect necessary restart/filesave actions
		self.previousSkin = config.plugins.yampmusicplayer.yampSkin.value
		self.previousDbPath = config.plugins.yampmusicplayer.databasePath.value
		self.previousLcdMode = self.prevMode = config.plugins.yampmusicplayer.yampLcdMode.value
		self.previousLcdSize = config.plugins.yampmusicplayer.lcdSize.value
		self.previousLcdFontSize = config.plugins.yampmusicplayer.lcdFontSize.value
		self.previousLcdTextLen = config.plugins.yampmusicplayer.lcdTextLen.value
		self.previousLcdTextHor = config.plugins.yampmusicplayer.lcdTextHoriz.value
		self.previousLcdTextPosX = config.plugins.yampmusicplayer.lcdTextPosX.value
		self.previousLcdColor1 = config.plugins.yampmusicplayer.lcdColorLine1.value
		self.previousLcdColor2 = config.plugins.yampmusicplayer.lcdColorLine2.value
		self.previousLcdColor3 = config.plugins.yampmusicplayer.lcdColorLine3.value
		self.previousLcdRunFontSize = config.plugins.yampmusicplayer.lcdRunningFontSize.value
		self.previousLcdCoverSize = config.plugins.yampmusicplayer.lcdCoverSize.value
		self.previousLcdCoverHoriz = config.plugins.yampmusicplayer.lcdCoverHoriz.value
		self.previousLcdCoverVert = config.plugins.yampmusicplayer.lcdCoverVert.value
		try:
			if self.selectionChanged not in self["config"].onSelectionChanged:
				self["config"].onSelectionChanged.append(self.selectionChanged)
		except Exception:
			LOG('YampConfigScreen: init: EXCEPT', 'err')
		self.skinFaultcustom = self.skinFaultfhdCustom = False
		config.plugins.yampmusicplayer.lcdTextLeftMin.value = 6  # text position x
		config.plugins.yampmusicplayer.lcdTextTopMin.value = 5  # text position y

	def layoutFinished(self):
		dummy1, dummy2, txtBouq = readRcButtonTexts()
		self["textBouquet"].setText(txtBouq)
		self.showHidePig(self.videoPreviewOn)
		self.startTimer.start(250, True)
		# remove custom skin options where Yamp.xml is missing
		skinPath = join(yampDir, 'skins/')
		if not isfile(skinPath + 'custom/Yamp.xml'):
			self.deleteSkinOption('custom')
		if not isfile(skinPath + 'fhdCustom/Yamp.xml'):
			self.deleteSkinOption('fhdCustom')
		if not isfile(skinPath + 'customDreamOS/Yamp.xml'):
			self.deleteSkinOption('customDreamOS')
		if not isfile(skinPath + 'fhdCustomDreamOS/Yamp.xml'):
			self.deleteSkinOption('fhdCustomDreamOS')

	def startActions(self):
		self.updateLCDText(TEXTLCD, 1)
		self.updateTimer.start(1000, False)

	def keyStop(self):
		self.parent.stopEntry()

	def keyLeft(self):
		self.callingKeyLeft = True
		ConfigListScreen.keyLeft(self)

	def keyRight(self):
		self.callingKeyLeft = False
		ConfigListScreen.keyRight(self)

	def msgWriteLcdFilesFailed(self, which):
		filename = join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, which)
		msg = _('Box display configuration file\n\n%s\n\ncould not be written!\n\nWrite protected? Wrong format?\n\nIf not corrected, changes will be lost...') % (filename)
		self.session.open(MessageBox, msg, type=MessageBox.TYPE_ERROR, timeout=30)

	def checkValidSkin(self):
		newSkin = failed = ''
		newSkin = config.plugins.yampmusicplayer.yampSkin.value
		failed, oldCustom = self.parent.checkSkinFiles(newSkin)
		if ('Yamp.xml' in failed) and ('custom' in newSkin.lower()):  # custom skin,Yamp.xml missing: Custom not existing, no message, just deactivate
			return newSkin, failed
		if failed:
			try:
				msg = _('Skin <%s> not possible, as\n\n%s\n\n(and maybe more) is missing\n\nSkin is disabled now! To enable it again, Yamp has to be restarted') % (self.parent.getSkinName(newSkin), failed)
				self.session.open(MessageBox, msg, type=MessageBox.TYPE_INFO, timeout=30)
			except Exception:
				LOG('YampConfigScreen: checkValidSkin: MessageBox EXCEPT', 'err')
		elif oldCustom:
			try:
				msg = _('This custom skin most likely has been copied from an old version, and probably is not up-to-date.\n\nIt is recommended to switch to a standard skin and check and revise the custom skin (compare it with the accordingstandard skin)!')
				self.session.open(MessageBox, msg, type=MessageBox.TYPE_INFO, timeout=30)
			except Exception:
				LOG('YampConfigScreen: checkValidSkin: MessageBox EXCEPT', 'err')
		return newSkin, failed

	def deleteSkinOption(self, skin):
		skinChoices = config.plugins.yampmusicplayer.yampSkin.choices.choices
		for skinValue in skinChoices:
			if skinValue[0] == skin:
				skinChoices.remove((skinValue[0], skinValue[1]))
				self["config"].l.invalidate()  # refresh configlist after remove skinoption

	def getCustomCoverSize(self):
		customCoverSize = 0
		try:
			customCoverSize = readCustomCoverSize()
		except Exception as e:
			pass
		if customCoverSize != -1:
			config.plugins.yampmusicplayer.lcdCoverSize.value = customCoverSize
		else:
			self.msgReadCoverSizeFromFileFailed()
		return customCoverSize

	def buildConfig(self):
		self.list = []
		WIDTH = 151 if getDesktop(0).size().width() > 1280 else 130
		EMPTYLINE = "".ljust(WIDTH, " ")

		# General Adjustments
		self.confSepGen = getConfigListEntry(_('  General Adjustments  ').center(WIDTH, "-"), config.plugins.yampmusicplayer.separator)
		self.list.append(self.confSepGen)
		self.groupIdx.append([x[0] for x in self.list].index(self.confSepGen[0]))
		self.confSkin = getConfigListEntry(_("YAMP skin (restart required)"), config.plugins.yampmusicplayer.yampSkin)
		self.list.append(self.confSkin)
		self.confDbPath = getConfigListEntry(_("YAMP database directory"), config.plugins.yampmusicplayer.databasePath)
		self.list.append(self.confDbPath)
		self.confMusicPath = getConfigListEntry(_("Filebrowser startup directory"), config.plugins.yampmusicplayer.musicFilePath)
		self.list.append(self.confMusicPath)
		self.confGenSaveLastPath = getConfigListEntry(_("Save filebrowser directory on exit"), config.plugins.yampmusicplayer.saveLastFilebrowserPath)
		self.list.append(self.confGenSaveLastPath)
		self.confPlPath = getConfigListEntry(_("Directory for saved playlists"), config.plugins.yampmusicplayer.playlistPath)
		self.list.append(self.confPlPath)
		self.confGenSingleLyr = getConfigListEntry(_("Use single directory for lyrics"), config.plugins.yampmusicplayer.useSingleLyricsPath)
		self.list.append(self.confGenSingleLyr)
		self.confLyricsPath = getConfigListEntry(_("Directory for saved lyrics"), config.plugins.yampmusicplayer.lyricsPath)
		self.list.append(self.confLyricsPath)
		self.confSlidePath = getConfigListEntry(_("Screensaver slideshow directory"), config.plugins.yampmusicplayer.screenSaverSlidePath)
		self.list.append(self.confSlidePath)
		self.confArtworkPath = getConfigListEntry(_("Artwork slideshow base directory"), config.plugins.yampmusicplayer.screenSaverArtworkPath)
		self.list.append(self.confArtworkPath)

		# Databaselist / Playlist
		self.confSepDbPl = getConfigListEntry(_('  Filelist / Databaselist / Playlist  ').center(WIDTH, "-"), config.plugins.yampmusicplayer.separator)
		self.list.append(self.confSepDbPl)
		self.groupIdx.append([x[0] for x in self.list].index(self.confSepDbPl[0]))
		self.confDbPlFilelist = getConfigListEntry(_("Layout of Title of Filelist"), config.plugins.yampmusicplayer.fileListTitleLayout)
		self.list.append(self.confDbPlFilelist)
		self.confDbExcludeDir = getConfigListEntry(_("Exclude directories in DB-Search starting with"), config.plugins.yampmusicplayer.dbExcludeDir)
		self.list.append(self.confDbExcludeDir)
		self.confDbArtistReduce = getConfigListEntry(_("Reduce number of artists by ignoring everything beginning with 'feat'"), config.plugins.yampmusicplayer.dbArtistReduce)
		self.list.append(self.confDbArtistReduce)
		self.confDbPlTitleOnce = getConfigListEntry(_("Title only once in artist/genre selection"), config.plugins.yampmusicplayer.titleOnlyOnceInSelection)
		self.list.append(self.confDbPlTitleOnce)
		self.confDbPlStandard = getConfigListEntry(_("Standardize title and artist names"), config.plugins.yampmusicplayer.capitalizeTitleAndArtist)
		self.list.append(self.confDbPlStandard)
		self.confDbPlPlLayout = getConfigListEntry(_("Playlist layout"), config.plugins.yampmusicplayer.playlistLayout)
		self.list.append(self.confDbPlPlLayout)
		self.confDbPlNext = getConfigListEntry(_("Layout for display of >next song<"), config.plugins.yampmusicplayer.displayNext)
		self.list.append(self.confDbPlNext)
		self.confDbPlUnknown = getConfigListEntry(_("Display unknown element (n/a) in info-bar as"), config.plugins.yampmusicplayer.displayUnknown)
		self.list.append(self.confDbPlUnknown)
		self.confDbPlSavePl = getConfigListEntry(_("Remember playlist on exit"), config.plugins.yampmusicplayer.savePlaylistOnExit)
		self.list.append(self.confDbPlSavePl)
		self.confDbPlRepeat = getConfigListEntry(_("Repeat playlist at end"), config.plugins.yampmusicplayer.repeatPlaylistAtEnd)
		self.list.append(self.confDbPlRepeat)
		self.confDbPlWrap = getConfigListEntry(_("Enable wrap around on move titles in playlist"), config.plugins.yampmusicplayer.wrapMovePlaylist)
		self.list.append(self.confDbPlWrap)
		self.confDbPlImmediate = getConfigListEntry(_("Start playing immediate (if playlist exists)"), config.plugins.yampmusicplayer.startImmediate)
		self.list.append(self.confDbPlImmediate)
		self.confDbPlGap = getConfigListEntry(_("Gap reduction (1/10 seconds, 0 = off)"), config.plugins.yampmusicplayer.gapCorrection)
		self.list.append(self.confDbPlGap)

		# Cover Search
		self.confSepCoverSearch = getConfigListEntry(_('  Cover Search / Auto Save  ').center(WIDTH, "-"), config.plugins.yampmusicplayer.separator)
		self.list.append(self.confSepCoverSearch)
		self.groupIdx.append([x[0] for x in self.list].index(self.confSepCoverSearch[0]))
		self.confCoverSearchP1 = getConfigListEntry(_("Cover search priority 1 (highest)"), config.plugins.yampmusicplayer.prioCover1)
		self.list.append(self.confCoverSearchP1)
		self.confCoverSearchP2 = getConfigListEntry(_("Cover search priority 2"), config.plugins.yampmusicplayer.prioCover2)
		self.list.append(self.confCoverSearchP2)
		self.confCoverSearchP3 = getConfigListEntry(_("Cover search priority 3"), config.plugins.yampmusicplayer.prioCover3)
		self.list.append(self.confCoverSearchP3)
		self.confCoverSearchP4 = getConfigListEntry(_("Cover search priority 4"), config.plugins.yampmusicplayer.prioCover4)
		self.list.append(self.confCoverSearchP4)
		self.confCoverSearchP5 = getConfigListEntry(_("Cover search priority 5 (lowest)"), config.plugins.yampmusicplayer.prioCover5)
		self.list.append(self.confCoverSearchP5)
		self.confCoverSearchVideo = getConfigListEntry(_("Google cover search for videos"), config.plugins.yampmusicplayer.searchGoogleCoverVideo)
		self.list.append(self.confCoverSearchVideo)
		self.confCoverSave = getConfigListEntry(_("Google cover auto save in title directory"), config.plugins.yampmusicplayer.saveCover)
		self.list.append(self.confCoverSave)

		# Lyrics Search
		self.confSepLyrSearch = getConfigListEntry(_('  Lyrics Search / Auto Save  ').center(WIDTH, "-"), config.plugins.yampmusicplayer.separator)
		self.list.append(self.confSepLyrSearch)
		self.groupIdx.append([x[0] for x in self.list].index(self.confSepLyrSearch[0]))
		self.confLyrSearchP1 = getConfigListEntry(_("Lyrics Search priority 1 (highest)"), config.plugins.yampmusicplayer.prioLyrics1)
		self.list.append(self.confLyrSearchP1)
		self.confLyrSearchP2 = getConfigListEntry(_("Lyrics Search priority 2"), config.plugins.yampmusicplayer.prioLyrics2)
		self.list.append(self.confLyrSearchP2)
		self.confLyrSearchP3 = getConfigListEntry(_("Lyrics Search priority 3"), config.plugins.yampmusicplayer.prioLyrics3)
		self.list.append(self.confLyrSearchP3)
		self.confLyrSearchP4 = getConfigListEntry(_("Lyrics Search priority 4 (lowest)"), config.plugins.yampmusicplayer.prioLyrics4)
		self.list.append(self.confLyrSearchP4)
		self.confLyrAutoSave = getConfigListEntry(_("Auto-save lyrics found online"), config.plugins.yampmusicplayer.autoSaveLyrics)
		self.list.append(self.confLyrAutoSave)

		# Fanart Search
		self.confSepFanartSearch = getConfigListEntry(_('  Artist-Art / MbId Search  ').center(WIDTH, "-"), config.plugins.yampmusicplayer.separator)
		self.list.append(self.confSepFanartSearch)
		self.groupIdx.append([x[0] for x in self.list].index(self.confSepFanartSearch[0]))
		self.confFanartSearchOnl = getConfigListEntry(_("Artist-Art-Pictures online search at fanart.tv"), config.plugins.yampmusicplayer.searchFanart)
		self.list.append(self.confFanartSearchOnl)
		self.confFanartSearchKey = getConfigListEntry(_("fanart.tv personal api key"), config.plugins.yampmusicplayer.fanarttvPersonal)
		self.list.append(self.confFanartSearchKey)
		self.confFanartMbidMode = getConfigListEntry(_("Musicbrainz-Artist-ID (MbId) search mode"), config.plugins.yampmusicplayer.searchMbidMode)
		self.list.append(self.confFanartMbidMode)
		self.confFanartMbidScore = getConfigListEntry(_("Musicbrainz Artist identification min score"), config.plugins.yampmusicplayer.searchMbidMinScore)
		self.list.append(self.confFanartMbidScore)

		# Screensaver
		self.confSepSS = getConfigListEntry(_('  Screensaver / Dia-Show / Artist-Art  ').center(WIDTH, "-"), config.plugins.yampmusicplayer.separator)
		self.list.append(self.confSepSS)
		self.groupIdx.append([x[0] for x in self.list].index(self.confSepSS[0]))
		self.confSSMode = getConfigListEntry(_("Type of screensaver"), config.plugins.yampmusicplayer.screenSaverMode)
		self.list.append(self.confSSMode)
		self.confSSBG = getConfigListEntry(_("Screensaver pictures in background (Info-Bar visible)"), config.plugins.yampmusicplayer.screenSaverBg)
		self.list.append(self.confSSBG)
		self.confSSResetBG = getConfigListEntry(_("Key <Audio> adjustment is reset at end of song"), config.plugins.yampmusicplayer.resetScreenSaverBg)
		self.list.append(self.confSSResetBG)
		self.confSSSuBDir = getConfigListEntry(_("Include subdirs in slideshow (custom or artwork) directory"), config.plugins.yampmusicplayer.screenSaverSubDirs)
		self.list.append(self.confSSSuBDir)
		self.confSSWait = getConfigListEntry(_("Wait for screensaver (seconds, 0 = off)"), config.plugins.yampmusicplayer.screenSaverWait)
		self.list.append(self.confSSWait)
		self.confSSNext = getConfigListEntry(_("Wait-time for next screensaver slide (seconds)"), config.plugins.yampmusicplayer.screenSaverNextSlide)
		self.list.append(self.confSSNext)
		self.confSSsort = getConfigListEntry(_("Sorting of screensaver pictures"), config.plugins.yampmusicplayer.screenSaverSort)
		self.list.append(self.confSSsort)
		self.confSSLeft = getConfigListEntry(_("Screensaver in dblist/filelist"), config.plugins.yampmusicplayer.screenSaverLeft)
		self.list.append(self.confSSLeft)
		self.confSSmanKey = getConfigListEntry(_("Manual activate/deactivate Screensaver by <%s> Button") % (self.txtRcPvrVideo), config.plugins.yampmusicplayer.manKeyScreensaver)
		self.list.append(self.confSSmanKey)
		self.confSSmaxOffMan = getConfigListEntry(_("Max. Screensaver Off-Time manual (seconds, 0=unlimited)"), config.plugins.yampmusicplayer.maxTimeSSoffMan)
		self.list.append(self.confSSmaxOffMan)
		self.confSSBgInfobar = getConfigListEntry(_("Show background in Info-Bar (visibility)"), config.plugins.yampmusicplayer.showInfoBarBg)
		self.list.append(self.confSSBgInfobar)
		self.confSSclock = getConfigListEntry(_("Show clock while screensaver active"), config.plugins.yampmusicplayer.showClockSS)
		self.list.append(self.confSSclock)

		# Operation / Display
		self.confSepOper = getConfigListEntry(_('  Operation / Display  ').center(WIDTH, "-"), config.plugins.yampmusicplayer.separator)
		self.list.append(self.confSepOper)
		self.groupIdx.append([x[0] for x in self.list].index(self.confSepOper[0]))
		self.confOperMoveLong = getConfigListEntry(_("Playlist entry move multiple lines"), config.plugins.yampmusicplayer.playlistMoveMulti)
		self.list.append(self.confOperMoveLong)
		self.confOperMaxCovScroll = getConfigListEntry(_('Max. display time "Cover Scroll" seconds, 0=off)'), config.plugins.yampmusicplayer.coverScrollTime)
		self.list.append(self.confOperMaxCovScroll)
		self.confOperIconFL = getConfigListEntry(_("Show file icons in filelist"), config.plugins.yampmusicplayer.fileListIcons)
		self.list.append(self.confOperIconFL)
		self.confOperIconPL = getConfigListEntry(_("Show file icons in playlist"), config.plugins.yampmusicplayer.playListIcons)
		self.list.append(self.confOperIconPL)

		self.confDispSkin = getConfigListEntry(_("Display used skin name in Main Screen"), config.plugins.yampmusicplayer.displaySkinname)
		self.list.append(self.confDispSkin)
		self.confDispHelp = getConfigListEntry(_("Display button description in Display (TV, Radio, %s)") % (self.txtRcPvrVideo), config.plugins.yampmusicplayer.displayButtonHelp)
		self.list.append(self.confDispHelp)
		self.confDiaName = getConfigListEntry(_("Display filename of current picture in Dia-Show"), config.plugins.yampmusicplayer.displayDiaName)
		self.list.append(self.confDiaName)

		self.confOperPlayLen = getConfigListEntry(_("Calculate and display playlist run time"), config.plugins.yampmusicplayer.showPlayListLen)
		self.list.append(self.confOperPlayLen)
		self.confHelpStart = getConfigListEntry(_("Show Yamp Help on Start (always with INFO LONG)"), config.plugins.yampmusicplayer.showHelpStart)
		self.list.append(self.confHelpStart)
		self.confOperExit = getConfigListEntry(_("Exit button jumps to upper directory in filelist/databaselist"), config.plugins.yampmusicplayer.newExitKey)
		self.list.append(self.confOperExit)
		self.confOperCommPlayP = getConfigListEntry(_("Common button for play / pause"), config.plugins.yampmusicplayer.commonPlayPause)
		self.list.append(self.confOperCommPlayP)
		self.confOperCommTvR = getConfigListEntry(_("Common button for Tv / Radio"), config.plugins.yampmusicplayer.commonTvRadio)
		self.list.append(self.confOperCommTvR)
		self.confOperConfExit = getConfigListEntry(_("Confirm exit"), config.plugins.yampmusicplayer.yampConfirmExit)
		self.list.append(self.confOperConfExit)
		self.confOperTV = getConfigListEntry(_("Show TV during Yamp"), config.plugins.yampmusicplayer.yampShowTV)
		self.list.append(self.confOperTV)

		# Lyrics
		self.confSepLyrics = getConfigListEntry(_('  Lyrics - Scroll / Time Edit - Karaoke  ').center(WIDTH, "-"), config.plugins.yampmusicplayer.separator)
		self.list.append(self.confSepLyrics)
		self.groupIdx.append([x[0] for x in self.list].index(self.confSepLyrics[0]))
		self.confLyrMinScroll = getConfigListEntry(_("Min. number of lines for scrolling text"), config.plugins.yampmusicplayer.lyricsMinLinesScroll)
		self.list.append(self.confLyrMinScroll)
		self.confLyrScrollLine = getConfigListEntry(_("Line number for scrolling (this line stays selected)"), config.plugins.yampmusicplayer.lyricsScrollLine)
		self.list.append(self.confLyrScrollLine)
		self.confLyrOffset = getConfigListEntry(_("Offset for time stamp in lyrics edit (milliseconds)"), config.plugins.yampmusicplayer.lyricsOffsetTime)
		self.list.append(self.confLyrOffset)
		self.confPlayOffset = getConfigListEntry(_("Offset for lyrics display while playing (milliseconds)"), config.plugins.yampmusicplayer.lyricsPlayOffsetTime)
		self.list.append(self.confPlayOffset)
		self.confLyrMaxTime = getConfigListEntry(_("Lyrics line max display time (seconds, 0 = no limit)"), config.plugins.yampmusicplayer.karaokeMaxTime)
		self.list.append(self.confLyrMaxTime)
		self.confLyrKarBlack = getConfigListEntry(_("Black background on Lyrics Line (Karaoke)"), config.plugins.yampmusicplayer.karaokeBg)
		self.list.append(self.confLyrKarBlack)

		# Video
		self.confSepVideo = getConfigListEntry(_('  Videoclip settings  ').center(WIDTH, "-"), config.plugins.yampmusicplayer.separator)
		self.list.append(self.confSepVideo)
		self.groupIdx.append([x[0] for x in self.list].index(self.confSepVideo[0]))
		self.confVidFull = getConfigListEntry(_("Automatic Full Screen Start Mode for Videos"), config.plugins.yampmusicplayer.videoAutoFull)
		self.list.append(self.confVidFull)
		self.confVidTitle = getConfigListEntry(_("Display time of Title for Videos (seconds, 0=off)"), config.plugins.yampmusicplayer.showTimeVideoTitle)
		self.list.append(self.confVidTitle)
		self.confVidClock = getConfigListEntry(_("Show clock while Video is running"), config.plugins.yampmusicplayer.showClockVideo)
		self.list.append(self.confVidClock)
		self.confVidLyrics = getConfigListEntry(_("Allow Lyrics screen on videos"), config.plugins.yampmusicplayer.showLyricsOnVideo)
		self.list.append(self.confVidLyrics)
		self.confVidBlank = getConfigListEntry(_("Insert Blank Video after Video"), config.plugins.yampmusicplayer.insertBlankVideo)
		self.list.append(self.confVidBlank)
		self.confVidBlankDel = getConfigListEntry(_("Blank Video runtime (ms)"), config.plugins.yampmusicplayer.blankVideoDelay)
		self.list.append(self.confVidBlankDel)

		# Box Display
		self.confSepDisp = getConfigListEntry(_('  Box Display  ').center(WIDTH, "-"), config.plugins.yampmusicplayer.separator)
		self.list.append(self.confSepDisp)
		self.groupIdx.append([x[0] for x in self.list].index(self.confSepDisp[0]))
		lcdSizeCustom = config.plugins.yampmusicplayer.lcdSize.value == 'custom'
		lcdMode = config.plugins.yampmusicplayer.yampLcdMode.value
		threeLines = lcdMode == 'threelines' or lcdMode == 'cover3'
		oneLine = lcdMode == 'oneline' or lcdMode == 'cover1' or threeLines
		cover = 'cover' in lcdMode
		self.confSizeOfLcd = getConfigListEntry(_("Size of box display used"), config.plugins.yampmusicplayer.lcdSize)
		self.confModeLcd = getConfigListEntry(_("Mode of box display used"), config.plugins.yampmusicplayer.yampLcdMode)
		self.confLcdFontSize = getConfigListEntry(_("Fontsize line(s) 1(..3)"), config.plugins.yampmusicplayer.lcdFontSize)
		self.confLcdTextLen = getConfigListEntry(_("Text length line(s) 1(..3)"), config.plugins.yampmusicplayer.lcdTextLen)
		self.confLcdTextHoriz = getConfigListEntry(_("Text horiz. alignment line(s) 1(..3)"), config.plugins.yampmusicplayer.lcdTextHoriz)
		self.confLcdColorLine1 = getConfigListEntry(_("Color textline 1"), config.plugins.yampmusicplayer.lcdColorLine1)
		self.confLcdColorLine2 = getConfigListEntry(_("Color text line 2"), config.plugins.yampmusicplayer.lcdColorLine2)
		self.confLcdColorLine3 = getConfigListEntry(_("Color text line 3"), config.plugins.yampmusicplayer.lcdColorLine3)
		self.confCoverSize = getConfigListEntry(_("Cover size"), config.plugins.yampmusicplayer.lcdCoverSize)
		self.confCoverColor = getConfigListEntry(_("Cover color"), config.plugins.yampmusicplayer.lcdCoverColor)
		self.confCoverHoriz = getConfigListEntry(_("Cover horiz. alignment"), config.plugins.yampmusicplayer.lcdCoverHoriz)
		self.confCoverVert = getConfigListEntry(_("Cover vertical alignment"), config.plugins.yampmusicplayer.lcdCoverVert)
		self.confLcdRollFont = getConfigListEntry(_("Font size for Graphical running text"), config.plugins.yampmusicplayer.lcdRunningFontSize)
		if lcdMode != 'off':
			self.list.append(self.confSizeOfLcd)
		if not lcdSizeCustom:
			self.list.append(self.confModeLcd)
			if oneLine or threeLines:
				self.list.append(self.confLcdFontSize)
				self.list.append(self.confLcdTextLen)
				self.list.append(self.confLcdTextHoriz)
				self.list.append(self.confLcdColorLine1)
			if threeLines:
				self.list.append(self.confLcdColorLine2)
				self.list.append(self.confLcdColorLine3)
			if lcdMode == 'running':
				self.list.append(self.confLcdRollFont)
			if cover:
				self.list.append(self.confCoverSize)
				self.list.append(self.confCoverColor)
				self.list.append(self.confCoverHoriz)
				self.list.append(self.confCoverVert)
		else: # custom display size
			self.list.append(self.confCoverSize)
			self.list.append(self.confCoverColor)
		# Miscellaneous
		self.confSepMisc = getConfigListEntry(_('  Miscellaneous / Debug  ').center(WIDTH, "-"), config.plugins.yampmusicplayer.separator)
		self.list.append(self.confSepMisc)
		self.groupIdx.append([x[0] for x in self.list].index(self.confSepMisc[0]))
		self.confYampExt = getConfigListEntry(_("YAMP in extended plugin list"), config.plugins.yampmusicplayer.yampInExtendedPluginlist)
		self.list.append(self.confYampExt)
		self.confYampMain = getConfigListEntry(_("YAMP in main menu"), config.plugins.yampmusicplayer.yampInMainMenu)
		self.list.append(self.confYampMain)
		self.confDebugMode = getConfigListEntry(_("Debug Mode"), config.plugins.yampmusicplayer.yampDebugMode)
		self.list.append(self.confDebugMode)
		self.confDebugPath = getConfigListEntry(_("Debug directory"), config.plugins.yampmusicplayer.debugPath)
		self.list.append(self.confDebugPath)
		self.confDebugMem = getConfigListEntry(_("Debug memory usage"), config.plugins.yampmusicplayer.yampDebugMemory)
		self.list.append(self.confDebugMem)

	# Display Help Texts
	def selectionChanged(self):
		try:
			currSelection = self["config"].getCurrent()
			txtYellow = ("")
			txtCoverSearch = _("left-right:\n\nOptions should be self-explaining.\n\nAllowed extensions: '.jpg', '.jpeg','.png', '.gif'\nThe options are processed in the priority order; when a Cover is found, no further searching in lower priorities\n\n Google-Search does not always find pictures with good resolution, so other options are preferable.\n\n")
			txtLyricsSearch = _("left-right\n\nOptions should be self-explaining.\n\nAllowed file extensions: .txt, .lrc (lrc with Karaoke time stamps).\n\nLyrics-directory depends on the setting in General Adjustments: Song directory or Common Lyrics directory\n\nThe options are processed in the priority order; when Lyrics are found, no further searching in lower priorities\n\n")
			if currSelection == self.confSepGen:
				self["help"].setText(_("More help is available at\n\nwww.vuplus-support.org/wbb4\n and\nboard.newnigma2.to/wbb4/\n\njust search for Yamp.\n\nA manual is available there for download also, and 'Frequently Asked Questions' (FAQ).\nPlease use it. :-)\n\nHave fun!\n\n@AlfredENeumann & @ekremtt"))
			elif currSelection == self.confSkin:
				self["help"].setText(_("left-right:\n\nselect used skin\n\nif custom skin is selected and there is an error in the skin (Yamp starts with black screen, no reaction on keys), delete or rename any file in /usr/lib/enigma2/python/Plugins/Extensions/YampMusicPlayer/skins/custom or .../fhdCustom, and it will automatically change back to the default screen on the next start"))
			elif currSelection == self.confDbPath:
				self["help"].setText(_("ok:\n\n opens filebrowser to select database path\n\nrecommended: /media/usb/Yamp/DB\n\ndefault: /media/hdd"))
			elif currSelection == self.confMusicPath:
				self["help"].setText(_("ok:\n\n opens filebrowser to select start path for music files\n\nrecommended: location of your music files\n\ndefault: /media/hdd"))
			elif currSelection == self.confGenSaveLastPath:
				self["help"].setText(_("left-right:\n\n if On, start path will we overwritten with actual path on exit\n\ndefault: Off"))
			elif currSelection == self.confPlPath:
				self["help"].setText(_("ok:\n\n opens filebrowser to select path for saving playlists\n\nrecommended: /media/usb/Yamp/Playlists\n\ndefault: /media/hdd"))
			elif currSelection == self.confGenSingleLyr:
				self["help"].setText(_("left-right:\n\n if On, saved lyrics will be stored in the lyrics path.\n\nif Off, saved lyrics will be stored in the directory of the music file\n\nrecommended: On\n\ndefault: On"))
			elif currSelection == self.confLyricsPath:
				self["help"].setText(_("ok:\n\n opens filebrowser to select path for lyrics (if above option is set to On)\n\nrecommended: /media/usb/Yamp/Lyrics\n\ndefault: /media/hdd"))
			elif currSelection == self.confSlidePath:
				self["help"].setText(_("ok:\n\n opens filebrowser to select path for screensaver pictures (if screensaver is set to Slideshow)\n\nrecommended: /media/usb/Yamp/Slides\n\ndefault: /media/hdd"))
			elif currSelection == self.confArtworkPath:
				self["help"].setText(_("ok:\n\n opens filebrowser to select path for base directory for screensaver artist-art pictures (if screensaver is set to artist-art).\n\nBase directory has to exist already, sub-directoryies for artists will be created automatically if selected.\nA subdirectory 'Default' should exist for artists without pictures\n\nrecommended: /media/usb/Yamp/ArtistPics\n\ndefault: /media/hdd"))
			elif currSelection == self.confSepDbPl:
				self["help"].setText(_("Options for the display and behaviour of Filelist/Database list / Playlist"))
			elif currSelection == self.confDbPlFilelist:
				self["help"].setText(_("left-right:\n\n choose, if the title of the filelist should include the path\n\ndefault: Title and Path"))
			elif currSelection == self.confDbExcludeDir:
				self["help"].setText(_("left-right:\n\n choose, if sub-directories should be excluded from scanninng into database\n\navailable option entries can be changed in the file <ExcludeSubDirs.txt> in Yamp-directory\n\nsub-directories starting with selected letters will not be scanned into database\n\na maximum of 2 sub-dirs can be excluded\n\ndefault: depending on your exclude file"))
			elif currSelection == self.confDbArtistReduce:
				self["help"].setText(_("left-right:\n\n choose, if the number of artists in the DB overview should be reduced by removing all in the artist name starting with 'feat'\n\nThus, the artist 'P!nk Feat. Scratch' (or featuring...) will be treated as 'P!nk' only\n\nin the details (and the info bar) still the full name will be visible\n\nthe selection is NOT case sensitive, i.e. small or big letters are treated the same\n\ndefault: On"))
			elif currSelection == self.confDbPlTitleOnce:
				self["help"].setText(_("left-right:\n\n On: if there is  more than one song with the same title and artist name or title and genre name in the database, only one will be displayed in the appropriate database list\n\ndefault: On"))
			elif currSelection == self.confDbPlStandard:
				self["help"].setText(_("left-right:\n\n On: Titles and artists will be 'titlecased', i.e. start with an upper case letter and continuing with lower case letters. \nThis is useful, when there are different spellings of the same title or artist in the ID3 tags. It works best with words in English language\n\nRemark: In <YampDir> there is a file 'NoTitlecase.txt' where excludes can be defined. Entries in this file will remain unchanged. Default entries: AC-DC, BAP, fun., INXS\n\ndefault: On"))
			elif currSelection == self.confDbPlPlLayout:
				self["help"].setText(_("left-right:\n\n Different options for the layout of the playlist.\n\nAttention: this setting is only used for new entries, it will not change already existing entries.\n If you want the same layout for all entries, you should not change this setting on an existing playlist.\n\ndefault: Title and Artist"))
			elif currSelection == self.confDbPlNext:
				self["help"].setText(_("left-right:\n\n Different options for the layout of the information 'next song'.\n\ndefault: Title - Artist - Album"))
			elif currSelection == self.confDbPlUnknown:
				self["help"].setText(_("left-right:\n\n Different options for the display of unknown elements (n/a) in info-bar.\n\ndefault: No change: <n/a>"))
			elif currSelection == self.confDbPlSavePl:
				self["help"].setText(_("left-right:\n\n On: actual playlist is temporary saved on exit and automatically reloaded on next start of Yamp. It is NOT saved as playlist file, so if you want to save it permanently, you have to save it manually (Options with key <Menu> in Playlist)\n\nAttention: Long playlists will delay the next start on slow machines.\n\ndefault: On"))
			elif currSelection == self.confDbPlRepeat:
				self["help"].setText(_("left-right:\n\n On: endless playing, will start with 1st song at end of list.\n Off: playing ends at the end of the list\n\n\nCan be temporary changed anytime with <TV>-key\n\ndefault: On"))
			elif currSelection == self.confDbPlWrap:
				self["help"].setText(_("left-right:\n\n On: moving of titles in playlist is possible with wrap around'.\n Off: moving stops at 1st and last entry\n\ndefault: On"))
			elif currSelection == self.confDbPlImmediate:
				self["help"].setText(_("left-right:\n\n On: Yamp begins playing immediately after start with the song last played in the playlist.\n\ndefault: Off"))
			elif currSelection == self.confDbPlGap:
				self["help"].setText(_("enter number:\n\n Try to narrow the gap between songs, given in 1/10 seconds.\n\nNot being perfect, this may improve the playback of live albums.\nThe next song is started the number of 1/10 seconds before the end of the current song\n\nExample: Value = 25: Next song will start 2.5 seconds before the end of the current song.\n\nRange: 0 .. 100 = 0 .. 10 Seconds\ndefault: 0"))
			elif currSelection == self.confSepCoverSearch:
				self["help"].setText(_("Options for the Cover Search and Cover Saving"))
			elif currSelection == self.confCoverSearchP1:
				self["help"].setText(txtCoverSearch + _("recommended = default:\nsearch in ID3-tags"))
			elif currSelection == self.confCoverSearchP2:
				self["help"].setText(txtCoverSearch + _("recommended = default:\nsearch for <title>.<ext>"))
			elif currSelection == self.confCoverSearchP3:
				self["help"].setText(txtCoverSearch + _("recommended = default:\nsearch for albumcover.<ext>"))
			elif currSelection == self.confCoverSearchP4:
				self["help"].setText(txtCoverSearch + _("default: off"))
			elif currSelection == self.confCoverSearchP5:
				self["help"].setText(txtCoverSearch + _("recommended = default:\nsearch at google online"))
			elif currSelection == self.confCoverSearchVideo:
				self["help"].setText(_("left-right:\n\n this is adjustable, as Cover Search for Videos sometimes has strange results.\n\ndefault: Off"))
			elif currSelection == self.confCoverSave:
				self["help"].setText(_("left-right:\n\n select option for saving online found covers in title directory, options should be self-explaining.\n\ndefault: Off"))
			elif currSelection == self.confSepLyrSearch:
				self["help"].setText(_("Options for the Lyrics Search and Lyrics Saving"))
			elif currSelection == self.confLyrSearchP1:
				self["help"].setText(txtLyricsSearch + _("recommended = default:\nsearch in lyrics-directory"))
			elif currSelection == self.confLyrSearchP2:
				self["help"].setText(txtLyricsSearch + _("recommended = default:\nsearch in ID3-tags"))
			elif currSelection == self.confLyrSearchP3:
				self["help"].setText(txtLyricsSearch + _("recommended = default:\nsearch at azlyrics.com online"))
			elif currSelection == self.confLyrSearchP4:
				self["help"].setText(txtLyricsSearch + _("recommended = default:\nsearch at chartlyrics.com online"))
			elif currSelection == self.confLyrAutoSave:
				self["help"].setText(_("left-right:\n\n On: Online found Lyrics are saved in Title-Directory or in Lyrics Directory, depending on setting under 'General Adjustments, Use single directory for lyrics'.\n\ndefault: Off"))
			elif currSelection == self.confSepFanartSearch:
				self["help"].setText(_("Options for the Artist-Art and MusicBrainz-ID (MbID) - Search. Only active when Database is used\n\n\nHint: Whenever <Yamp-Directory> is mentioned, this means\n\n/usr/lib/enigma2/python/Plugins/Extensions/YampMusicPlayer"))
			elif currSelection == self.confFanartSearchOnl:
				self["help"].setText(_("left-right:\n\n Artist-Art-Online search is only possible if the artist is in the database.\n\n'search always' can only be selected temporary and is not saved, as Yamp could be banned at fanart.tv if traffic is too high.\n\nThe every xx days period is calculated for each artist seperately.\n\nFaster download if you get a personal api key (see manual)\nrecommended = default:\nsearch every 60 days"))
			elif currSelection == self.confFanartSearchKey:
				self["help"].setText(_("enter key:\n\n Personal api key for fanart.tv is available for free at fanart.tv.\n\nFaster download if you have a personal api key.\n\nkey may be also entered by providing it in the file\n<YampFanarttvPersonalApi.key>\nin the Yamp-Directory. The file is existing after installation with a (useless) dummy-key"))
			elif currSelection == self.confFanartMbidMode:
				self["help"].setText(_("left-right:\n\n Musicbrainz-ID (MbID) for artists is needed for fanart-download at fanart.tv.\n\nJust check which setting has the best results on your machine (see manual)\n\ndefault: standard..."))
			elif currSelection == self.confFanartMbidScore:
				self["help"].setText(_("enter number:\n\n Searching for MbID for artists often leads to more than 1 result.\n\n With the min-score you define how exact the result should be. \n\nLower numbers leads to more findings, higher numbers might not find the artist. Default: 90.\n\nSee also on musicbrainz online page\n\nRange: 1 .. 100, default: 95"))
			elif currSelection == self.confSepSS:
				self["help"].setText(_("Options for the Screensaver"))
			elif currSelection == self.confSSMode:
				self["help"].setText(_("left-right:\n\n Options:\nBlank screen: black screen\n\nStandard Screensaver: pictures in Yamp subdir 'saver' are displayed\n\nCustom Screensaver (Dia-Show): pictures in Screensaver slideshow directory (adjusted in General Adjustments) are displayed\n\nArtwork as Screensaver: Pictures in artwork directory, subdir <artist>, are displayed (or subdir 'Default', if no pictures exist)\n\ndefault: Artwork"))
			elif currSelection == self.confSSBG:
				self["help"].setText(_("left-right:\n\n On: Info-Bar is visible while screensaver is active\n\n Off: Info-Bar is not visible (screensaver-pictures only)\n\ncan be temporary changed with <Audio>-key while screensaver is active\n\ndefault: On"))
			elif currSelection == self.confSSResetBG:
				self["help"].setText(_("left-right:\n\n On: screensaver temporary switched on/off with <Audio>-key is set back to the above adjusted setting at song change\n\ndefault: On"))
			elif currSelection == self.confSSSuBDir:
				self["help"].setText(_("left-right:\n\n On: pictures in subdirectories are also displayed, valid for custom (slideshow) and artwork\n\ndefault: On"))
			elif currSelection == self.confSSWait:
				self["help"].setText(_("enter number:\n\nafter starting a song from playlist, wait this number of seconds before starting screensaver.\n\n0: disable screensaver\n\nRange: 0 .. 600, default: 10"))
			elif currSelection == self.confSSNext:
				self["help"].setText(_("enter number:\n\nchange screensaver pictures all x seconds\n\ndo not adjust a too short time, specially on slow machines\n\nHint: additionally, you can switch to another picture anytime manually with the left/right-keys\n\nRange: 5 .. 99, default: 10"))
			elif currSelection == self.confSSsort:
				self["help"].setText(_("left-right:\n\noptions should be self-explaining, valid for custom (slideshow) and artwork\n\ndefault: shuffling"))
			elif currSelection == self.confSSLeft:
				self["help"].setText(_("left-right:\n\n On: screensaver will start also when on left side (file list or database)\n\n Off: screensaver will only start when on right side (playlist)\n\ndefault: On"))
			elif currSelection == self.confSSmanKey:
				self["help"].setText(_("left-right:\n\n On: screensaver may be manually activated / deactivated with <%s>-key\n\nbasic condition: screensaver must not be deactivated (time = 0)\n\ndefault: On") % (self.txtRcPvrVideo))
			elif currSelection == self.confSSmaxOffMan:
				self["help"].setText(_("enter number:\n\nif screensaver has been deactivated by pressing <%s>-key, it will be reactivated after this time\n\nRange: 0 .. 1.200, default: 600") % (self.txtRcPvrVideo))
			elif currSelection == self.confSSBgInfobar:
				self["help"].setText(_("left-right:\n\n On: Black background for Info-Bar while screensaver is active (better readability)\n\n Off: no background, picture visibility better\n\ndefault: On"))
			elif currSelection == self.confSSclock:
				self["help"].setText(_("left-right:\n\noptions to show/hide clock and date while screensaver is active\n\ndefault: No"))
			elif currSelection == self.confSepOper:
				self["help"].setText(_("Common Options for Display and Operation"))
			elif currSelection == self.confOperMoveLong:
				self["help"].setText(_("enter number:\n\nwith red-long and green-long entries in playlist may be moved up/down by this number of lines\n\nRange: 2 .. 50, default: 10"))
			elif currSelection == self.confOperMaxCovScroll:
				self["help"].setText(_("enter number:\n\nwhen scrolling in the filelist, database or playlist, the cover (and the according information) of the selected song may be displayed. After this time it will display the actual cover and info again.\n\nMay cause performance problems on slow machines\n\n0: 'Scroll Cover' display disabled\n\nRange: 0 .. 600, default: 10"))
			elif currSelection == self.confOperIconFL:
				self["help"].setText(_("left-right:\n\nshow or hide file icons in filelist\n\ndefault: On (show)"))
			elif currSelection == self.confOperIconPL:
				self["help"].setText(_("left-right:\n\nshow or hide file icons in playlist\n\ndefault: On (show)"))
			elif currSelection == self.confOperPlayLen:
				self["help"].setText(_("left-right:\n\nshow or hide playlist total runtime length and remaining time length.\n\nthis display can only be calculated correct if all songs in the playlist are in the database.\n\nAlso, calculation for long playlists may take some time specially on slow boxes. Therefore it can be disabled.\n\ndefault: On"))
			elif currSelection == self.confHelpStart:
				self["help"].setText(_("left-right:\n\n On: The Yamp help is shown on each start of Yamp. Recommended for beginners, or, if your remote does not support INFO LONG. \n\nOff: The Yamp help is only shown only once after an update. Howewever, with INFO LONG it can be shown anytime\n\ndefault: On"))
			elif currSelection == self.confOperExit:
				self["help"].setText(_("left-right:\n\n On: Exit button jumps to upper directory in filelist/databaselist\n\n Off: Exit button only used for Exit\n\ndefault: On"))
			elif currSelection == self.confOperCommPlayP:
				self["help"].setText(_("left-right:\n\nSelect, if your remote has a common play/pause button\n\ndefault: Off"))
			elif currSelection == self.confOperCommTvR:
				self["help"].setText(_("left-right:\n\nSelect, if your remote has a common TV / Radio button, and how it should behave: may prevent the need to change the keymap.xml\n\nBasic: If your remote sends the TV signal with this button, use one of the TV adjustments, otherwise Radio. just try\n\nshuffle, Long PL endless: short keypess will toggle shuffle\n\nPL endless, Long shuffle: short keypress will toggle PL endless\n\ndefault: No"))
			elif currSelection == self.confOperConfExit:
				self["help"].setText(_("left-right:\n\n On: closing Yamp has to be confirmed\n\n Off: Yamp will close without confirmation\n\ndefault: On"))
			elif currSelection == self.confOperTV:
				self["help"].setText(_("left-right:\n\nSelect Option for TV in Yamp Video-Preview-Window\n\n on Start only means, TV stops when the first song is played \n\n always means: Tv starts on Yamp start, stops when a song is played, and resumes when no song is played\n\ndefault: depends on the used skin"))
			elif currSelection == self.confSepLyrics:
				self["help"].setText(_("Options for Lyrics Display in Lyrics screen and Karaoke-Line in Screensaver screen"))
			elif currSelection == self.confLyrMinScroll:
				self["help"].setText(_("enter number:\n\nif the line number in lyrics screen is less than this number, no scrolling will occur\n\nRange: 0 .. 100, default: 20"))
			elif currSelection == self.confLyrScrollLine:
				self["help"].setText(_("enter number:\n\nwhen scrolling through the text in lyrics screen, this line will stay selected (srolling occurs 'around' this line)\n\nRange: 1 .. 100, default: 7"))
			elif currSelection == self.confLyrOffset:
				self["help"].setText(_("enter number:\n\nwhen editing the time stamp in lyrics screen, the stored time will be earlier this number of milliseconds than the time the ok key is pressed (correction of reaction time)\n\nRange: 0 .. 5.000, default: 1.000"))
			elif currSelection == self.confPlayOffset:
				self["help"].setText(_("enter number:\n\nwhen playing, the display of the current line in lyrics screen or the karaoke-line will be offset by this time.\n\nspecially helpful when using .lrc-files with a fixed offset\n\nRemark: as the remote does not have a Minus-key: Use yellow key to switch between + and -\n\nRange: -10.000 .. 10.000, default: 0"))
				txtYellow = ("+/-")
			elif currSelection == self.confLyrMaxTime:
				self["help"].setText(_("enter number:\n\n'Karaoke Light': Lyrics line when screensaver is active.\nactivate/deactivate with <Text (L)>, see manual.\n\nThis is the maximum time, a karaoke line will be displayed on the screen.\n\nhelpful, when there is a long instrumental passage with no text\n\nRange: 0 .. 600, default: 10"))
			elif currSelection == self.confLyrKarBlack:
				self["help"].setText(_("left-right:\n\nOptions to select or deselect black background for karaoke-line(s).\n\nOff: picture is less 'disturbed'\nOn: Karaoke-text better readable\n\ndefault: small and big..."))
			elif currSelection == self.confSepVideo:
				self["help"].setText(_("Options for the Playback of Music-Videoclips"))
			elif currSelection == self.confVidFull:
				self["help"].setText(_("left-right:\n\nOptions for starting Videoclips in FullScreen:\n\nimmediate: start immediate in Fullscreen mode\n\nscreensaver: start after screensaver-delay in Fullscreen mode\n\nmanual: start only manually in Fullscreen mode (key ok)\n\ndefault: screensaver delay"))
			elif currSelection == self.confVidTitle:
				self["help"].setText(_("enter number:\n\nshow the Info-Bar in Fullscreen-Video for this time, then hide it\n\n0: Info-Bar off on Video\n10.000: On during complete clip\n\nRange: 0 .. 10.000, default: 10"))
			elif currSelection == self.confVidClock:
				self["help"].setText(_("left-right:\n\noptions to show/hide clock and date while playing Video in Fullscreen mode\n\ndefault: No"))
			elif currSelection == self.confVidLyrics:
				self["help"].setText(_("left-right:\n\nAllow switching to lyrics screen while playing Video\n\ndefault: On"))
			elif currSelection == self.confVidBlank:
				self["help"].setText(_("left-right:\n\nto prevent the last video picture as background, on some boxes it is necessary to insert a short 'black' video after the end of a video.\n\nAttention: This is experimental, try on your own risk. If the system hangs, try with EXIT several times.\n\ndefault: Off"))
			elif currSelection == self.confVidBlankDel:
				self["help"].setText(_("enter number:\n\nlength of the 'black' video from the setting above\n\nagain: Just try.\n\nRange: 0 .. 6.000, default: 500"))
			elif currSelection == self.confSepDisp:
				self["help"].setText(_("Options for the Box-Display.\n\nThe display should NOT be skinned in the used box-skin; otherwise the settings here will NOT have any effect!\n\nMany settings here will change the files YampLCD.xml and/or YampLcdRunning.xml in the used Yamp-Skin-directory!\n\nIf you do not want this, you have to use <custom size> for the display.\n\nOtherwise (you do not want to edit the xml-files manualy): Please select first the size of the display, this will activate many other options"))
			elif currSelection == self.confSizeOfLcd:
				self["help"].setText(_("left-right:\n\nResolution of the box display. Changing this setting will overwrite/limit some settings to reasonable values, you may adjust them after. It will also overwrite YampLCD.xml and YampLcdRunning.xml in the used Yamp-Skin-directory! You will be asked before.\n\nCustom: no changes are made to the xml-files, you have to edit and adjust these files manually.\n\ndefault: custom"))
			elif currSelection == self.confModeLcd:
				self["help"].setText(_("left-right:\n\nOptions for the Box display\n\noff: no control of the display by Yamp. Useful if you use external software (LCD4linux or similar)\n\n1 line, 3 lines: 1 or 3 lines text display\n\nRunning Text: Only selectable if Renderer RunningText is installed. See manual\n\nCover with or without text.\n\ndefault: 3 lines display"))
			elif currSelection == self.confLcdFontSize:
				self["help"].setText(_("enter number:\n\nFontsize of the text line(s) 1(..3).\n\nRange: 10 .. 200, default: 32"))
			elif currSelection == self.confLcdTextLen:
				self["help"].setText(_("enter number:\n\nText length for the text line(s) 1(..3).\n\nSpecially helpful if you use a display mode with cover display - so you are able to choose if the text is only outside the cover or overlapping.\n\nRange: 10 .. 999, default: 160"))
			elif currSelection == self.confLcdTextHoriz:
				self["help"].setText(_("left-right:\n\nselect horizontal alignment of the text line(s) 1(..3).\n\nx-position of line(s) 1 (..3) will be calculated out of display size and text length\n\ndefault: left"))
			elif currSelection == self.confLcdRollFont:
				self["help"].setText(_("enter number:\n\nfont size of Running Text\n\nRange: 1 .. 500, default: 32"))
			elif currSelection == self.confLcdColorLine1:
				self["help"].setText(_("left-right:\n\nselect color for text line 1 in box display\n\ndefault: white"))
			elif currSelection == self.confLcdColorLine2:
				self["help"].setText(_("left-right:\n\nselect color for text line 2 in box display\n\ndefault: white"))
			elif currSelection == self.confLcdColorLine3:
				self["help"].setText(_("left-right:\n\nselect color for text line 3 in box display\n\ndefault: white"))
			elif currSelection == self.confCoverSize:
				if config.plugins.yampmusicplayer.lcdSize.value == 'custom':
					self["help"].setText(_("\n\ncustom size of Display selected.\n\nYamp is trying to read the size from YampLCD.xml!!\n\nNo adjustment possible"))
				else:
					self["help"].setText(_("enter number:\n\nsize of the cover in box-display\n\nRange: 10 .. 999, default: 60"))
			elif currSelection == self.confCoverColor:
				self["help"].setText(_("left-right:\n\nselect cover color in box display.\n\nyou have to try if transparent or non transparent is working, as this is different on different box-displays\n\n!!! Attention VTi: !!!\nOn some Vu-Boxes with VTi only color-selctions\nblack & white\ncolor transparent\nare working; with a different selection you will get a skin error\n<pixmap file /tmp/coverlcd.png not found>\n\nReasan unknown. If you get this error on Yamp-start, change the color setting!\n\ndefault: black & white"))
			elif currSelection == self.confCoverHoriz:
				self["help"].setText(_("left-right:\n\nselect horizontal alignment of the cover.\n\nx-position of the cover will be calculated out of display size and cover size\n\ndefault: right"))
			elif currSelection == self.confCoverVert:
				self["help"].setText(_("left-right:\n\nselect vertical alignment of the cover.\n\ny-position of the cover will be calculated out of display size and cover size\n\ndefault: center"))
			elif currSelection == self.confSepMisc:
				self["help"].setText(_("Misc. basic and debug settings"))
			elif currSelection == self.confDispSkin:
				self["help"].setText(_("left-right:\n\nselect if you want to see the used Yamp-skin in the title line\n\ndefault: On"))
			elif currSelection == self.confDispHelp:
				self["help"].setText(_("left-right:\n\nselect if you want to see help-texts for buttons repeat (TV), shuffle (Radio) and Screensaver (%s) in main screen\n\ndefault: On") % (self.txtRcPvrVideo))
			elif currSelection == self.confDiaName:
				self["help"].setText(_("left-right:\n\nselect if you want to see the filename with or without path of the current picture in screensaver-mode individual - dia show\n\nfor both options it is selectable if the text is shown with black background (better readability) or without background (picture is less 'disturbed')\n\ndefault: No"))
			elif currSelection == self.confYampExt:
				self["help"].setText(_("left-right:\n\nselect if you want to see Yamp in the extension menu\n\ndefault: On"))
			elif currSelection == self.confYampMain:
				self["help"].setText(_("left-right:\n\nselect if you want to see Yamp in the main menu\n\ndefault: Off"))
			elif currSelection == self.confDebugMode:
				self["help"].setText(_("left-right:\n\nDebug Mode: Standard: error only\n\nif everything is ok, you may switch to 'off'.\n\nUse 'all' or one of the 'specials' only if you are asked for it by the author\n\ndefault: errors only"))
			elif currSelection == self.confDebugPath:
				self["help"].setText(_("ok:\n\n opens filebrowser to select the directory where to store the debug file\n\nrecommended: /media/usb/Yamp/Debug\n\ndefault: /media/hdd"))
			elif currSelection == self.confDebugMem:
				self["help"].setText(_("left-right:\n\nSwitch debug mode for used memory on or off.\n\nShould never be necessary.\n\ndefault: Off"))
			else:
				self["help"].setText("")
			self["key_yellow"].setText(txtYellow)
		except Exception as e:
			LOG('YampConfigScreen: selectionChanged: EXCEPT: %s' % (str(e)), 'err')

	def calcNewLCDvalues(self):
		limitTextLenMin = limitCoverSizeMin = 10
		limitTextLenMax = 999
		limitCoverSizeMax = 999
		textMinLeft = config.plugins.yampmusicplayer.lcdTextLeftMin.value
		lcdMode = config.plugins.yampmusicplayer.yampLcdMode.value
		lcdSize = config.plugins.yampmusicplayer.lcdSize.value
		fontSize = config.plugins.yampmusicplayer.lcdFontSize.value
		runningFontSize = config.plugins.yampmusicplayer.lcdRunningFontSize.value
		textLen = config.plugins.yampmusicplayer.lcdTextLen.value
		coverSizeSetting = config.plugins.yampmusicplayer.lcdCoverSize.value
		if lcdMode == 'off':
			return
		if lcdSize == 'custom':
			self.previousLcdSize = lcdSize
			customCoverSize = self.getCustomCoverSize()
			if customCoverSize == -1:  # new  custom could not read cover size from file
				if self.callingKeyLeft:
					ConfigListScreen.keyRight(self)
				else:
					ConfigListScreen.keyLeft(self)
				return
			else:
				coverSizeSetting = limitCoverSizeMin = limitCoverSizeMax = customCoverSize
				config.plugins.yampmusicplayer.lcdCoverSize.value = customCoverSize
		else:  # non custom: Calculate preset values
			try:
				lcdSizeList = lcdSize.split('x')  # lcdSizeList: 0: Width 1: Height
				lcdWidth = int(lcdSizeList[0])
				coverInMode = ('cover' in lcdMode)
				coverInModePrev = ('cover' in self.previousLcdMode)
				lcdSizeChanged = self.previousLcdSize != lcdSize
				if lcdSizeChanged:  # or self.previousLcdMode != lcdMode:
					# LCD size changed: Set preset values
					self.previousLcdSize = lcdSize
					if lcdSizeChanged:
						if lcdSize == '800x480':
							fontSize = 64
							runningFontSize = 150
							coverSizeSetting = 400
						elif lcdSize == '480x320':
							fontSize = 55
							runningFontSize = 130
							coverSizeSetting = 300
						elif lcdSize == '400x240' or lcdSize == '320x240':
							fontSize = 45
							runningFontSize = 120
							coverSizeSetting = 230
						elif lcdSize == '220x176':
							fontSize = 33
							runningFontSize = 110
							coverSizeSetting = 170
						elif lcdSize == '132x64':
							fontSize = 14
							runningFontSize = 16
							coverSizeSetting = 60
						if coverInMode:
							textLen = lcdWidth - coverSizeSetting - textMinLeft
						else:
							textLen = lcdWidth - 2 * textMinLeft

						if coverInMode:
							textLen = lcdWidth - coverSizeSetting - textMinLeft
						else:
							textLen = lcdWidth - 2 * textMinLeft
					self.previousLcdMode = lcdMode
				# set new limits
				limitTextLenMax = lcdWidth - textMinLeft * 2  # LCD width
				limitCoverSizeMax = int(lcdSizeList[1])  # LCD height
				config.plugins.yampmusicplayer.lcdTextLen.limits = [(limitTextLenMin, limitTextLenMax),]
				config.plugins.yampmusicplayer.lcdTextLen.value = textLen
				config.plugins.yampmusicplayer.lcdFontSize.value = fontSize
				config.plugins.yampmusicplayer.lcdRunningFontSize.value = runningFontSize
				config.plugins.yampmusicplayer.lcdTextPosX.value = self.CalcTextLeftValue(lcdWidth, textLen)
				config.plugins.yampmusicplayer.lcdCoverPosX.value, config.plugins.yampmusicplayer.lcdCoverPosY.value = self.CalcCoverLeftTopValue(lcdSizeList, coverSizeSetting)
			except Exception as e:
				LOG('YampConfigScreen: calcNewLCDvalues: EXCEPT: ' + str(e), 'err')
		try:  # all (custom - not custom)
			config.plugins.yampmusicplayer.lcdCoverSize.limits = [(limitCoverSizeMin, limitCoverSizeMax),]
			coverSizeSetting = max(min(coverSizeSetting, limitCoverSizeMax), limitCoverSizeMin)
			config.plugins.yampmusicplayer.lcdCoverSize.value = coverSizeSetting
		except Exception as e:
			LOG('YampConfigScreen: calcNewLCDvalues: lcdCoverSize: EXCEPT: ' + str(e), 'err')

	def CalcCoverLeftTopValue(self, lcdSizeList, coverSize):  # lcdSizeList: 0: Width 1: Height
		alignHor = config.plugins.yampmusicplayer.lcdCoverHoriz.value
		alignVer = config.plugins.yampmusicplayer.lcdCoverVert.value
		textMinLeft = config.plugins.yampmusicplayer.lcdTextLeftMin.value
		textMinTop = config.plugins.yampmusicplayer.lcdTextTopMin.value
		if alignHor == 'left':
			posX = textMinLeft
		elif alignHor == 'center':
			posX = (int(lcdSizeList[0]) - coverSize) / 2
		else:
			posX = int(lcdSizeList[0]) - coverSize - textMinLeft
		if alignVer == 'top':
			posY = textMinTop
		elif alignVer == 'center':
			posY = (int(lcdSizeList[1]) - coverSize) / 2
		else:
			posY = int(lcdSizeList[1]) - coverSize - textMinTop
		if posX < 0:
			posX = 0
		if posY < 0:
			posY = 0
		return posX, posY

	def CalcTextLeftValue(self, lcdWidth, txtWidth):
		txtAlign = config.plugins.yampmusicplayer.lcdTextHoriz.value
		textMinLeft = config.plugins.yampmusicplayer.lcdTextLeftMin.value
		if txtAlign == 'left':
			return (textMinLeft)
		elif txtAlign == 'center':
			return ((lcdWidth - txtWidth) / 2)
		else:
			return (lcdWidth - txtWidth - textMinLeft)

	def updateTimerActions(self):
		self.updateLCDText(TEXTLCD, 1)

	def cleanup(self):
		del self.startTimer
		del self.updateTimer

	def updateLCDText(self, text, line):
		if config.plugins.yampmusicplayer.yampLcdMode.value == 'running':
			try:
				self.LcdText = text
			except Exception:
				pass
		else:
			self.summaries.setText(text, line)

	def getLcdText(self):  # for LCD Running Text
		return (self.LcdText)

	def createSummary(self):
		if config.plugins.yampmusicplayer.yampLcdMode.value == 'running':
			return YampLCDRunningScreenV33
		else:
			return YampLCDScreenV33

	def pagedown(self):
		try:
			selection = self["config"].getCurrentIndex()
			nextIdx = [x for x in self.groupIdx if x > selection][0]
			self["config"].instance.moveSelectionTo(nextIdx)
		except Exception:
			pass

	def pageup(self):
		try:
			selection = self["config"].getCurrentIndex()
			nextIdx = [x for x in self.groupIdx if x < selection][-1]
			self["config"].instance.moveSelectionTo(nextIdx)
		except Exception:
			pass

	def keyOK(self):
		selection = self["config"].getCurrent()
		if selection == self.confDbPath:
			self.session.openWithCallback(self.pathSelectedDatabase, YampSelectPathScreenV33, config.plugins.yampmusicplayer.databasePath.value, _('database'))
		elif selection == self.confMusicPath:
			self.session.openWithCallback(self.pathSelectedFilebrowser, YampSelectPathScreenV33, config.plugins.yampmusicplayer.musicFilePath.value, _('music files base dir'))
		elif selection == self.confLyricsPath:
			self.session.openWithCallback(self.pathSelectedLyrics, YampSelectPathScreenV33, config.plugins.yampmusicplayer.lyricsPath.value, _('lyrics'))
		elif selection == self.confPlPath:
			self.session.openWithCallback(self.pathSelectedPlaylist, YampSelectPathScreenV33, config.plugins.yampmusicplayer.playlistPath.value, _('playlists'))
		elif selection == self.confSlidePath:
			self.session.openWithCallback(self.pathSelectedScreenSaver, YampSelectPathScreenV33, config.plugins.yampmusicplayer.screenSaverSlidePath.value, _('screensaver individual (Dia-Show)'))
		elif selection == self.confArtworkPath:
			self.session.openWithCallback(self.pathSelectedScreenSaverArtwork, YampSelectPathScreenV33, config.plugins.yampmusicplayer.screenSaverArtworkPath.value, _('screensaver artwork base dir'))
		elif selection == self.confDebugPath:
			self.session.openWithCallback(self.pathSelectedDebugPath, YampSelectPathScreenV33, config.plugins.yampmusicplayer.debugPath.value, _('debug files'))

	def changeLyricsPlayOffsetTime(self, val):
		selection = self["config"].getCurrent()
		if selection == self.confPlayOffset:
			try:
				config.plugins.yampmusicplayer.lyricsPlayOffsetTime.value += val
			except Exception as e:
				LOG('YampConfigScreen: changeLyricsPlayOffsetTime: lcdCoverSize: EXCEPT: ' + str(e), 'err')
			try:
				self["config"].instance.moveSelection(self["config"].instance.moveDown)
				self["config"].instance.moveSelection(self["config"].instance.moveUp)
			except Exception as e:
				LOG('YampConfigScreen: changeLyricsPlayOffsetTime: moveDown: EXCEPT: ' + str(e), 'err')

	def key1(self):
		self.changeLyricsPlayOffsetTime(-10)

	def key3(self):
		self.changeLyricsPlayOffsetTime(10)

	def key4(self):
		self.changeLyricsPlayOffsetTime(-50)

	def key6(self):
		self.changeLyricsPlayOffsetTime(50)

	def key7(self):
		self.changeLyricsPlayOffsetTime(-500)

	def key9(self):
		self.changeLyricsPlayOffsetTime(500)

	def pathSelectedDatabase(self, result):
		if result is not None:
			config.plugins.yampmusicplayer.databasePath.value = result

	def pathSelectedFilebrowser(self, result):
		if result is not None:
			config.plugins.yampmusicplayer.musicFilePath.value = result

	def pathSelectedLyrics(self, result):
		if result is not None:
			config.plugins.yampmusicplayer.lyricsPath.value = result

	def pathSelectedPlaylist(self, result):
		if result is not None:
			config.plugins.yampmusicplayer.playlistPath.value = result

	def pathSelectedScreenSaver(self, result):
		if result is not None:
			config.plugins.yampmusicplayer.screenSaverSlidePath.value = result

	def pathSelectedScreenSaverArtwork(self, result):
		if result is not None:
			config.plugins.yampmusicplayer.screenSaverArtworkPath.value = result

	def pathSelectedDebugPath(self, result):
		if result is not None:
			config.plugins.yampmusicplayer.debugPath.value = result

	def keyGreen(self):
		newLcdSize = config.plugins.yampmusicplayer.lcdSize.value
		newLcdMode = config.plugins.yampmusicplayer.yampLcdMode.value
		newLcdOff = newLcdMode == 'off'
		newLcdCustom = newLcdSize == 'custom'
		newLcdOffOrCustom = newLcdOff or newLcdCustom
		newTextPosX = config.plugins.yampmusicplayer.lcdTextPosX.value
		covSize = 0
		lcdTextLenChanged, lcdTextLeftChanged, lcdTextAlignChanged, lcdCoverSizeChanged, covAlignChanged = False, False, False, False, False
		if not newLcdOffOrCustom:
			newTextLen = config.plugins.yampmusicplayer.lcdTextLen.value
			lcdTextLenChanged = self.previousLcdTextLen != newTextLen
			lcdTextAlignChanged = config.plugins.yampmusicplayer.lcdTextHoriz.value != self.previousLcdTextHor
			lcdTextLeftChanged = newTextPosX != self.previousLcdTextPosX
			covSize = config.plugins.yampmusicplayer.lcdCoverSize.value
			lcdCoverSizeChanged = self.previousLcdCoverSize != covSize  # and not newLcdOffOrCustom
			covAlignChanged = config.plugins.yampmusicplayer.lcdCoverHoriz.value != self.previousLcdCoverHoriz or config.plugins.yampmusicplayer.lcdCoverVert.value != self.previousLcdCoverVert
		for x in self["config"].list:
			x[1].save()
		try:
			configfile.save()
		except Exception as e:
			LOG('YampConfigScreen: keyGreen: EXCEPT save: %s' % (str(e)), 'err')
		skinChanged = self.previousSkin != config.plugins.yampmusicplayer.yampSkin.value
		if ('fhd' in config.plugins.yampmusicplayer.yampSkin.value) or ('TV' in config.plugins.yampmusicplayer.yampSkin.value):
			self.askTvon()
		newModeCover = 'cover' in newLcdMode
		oldModeCover = 'cover' in self.previousLcdMode
		newModeText1 = newLcdMode == 'oneline' or newLcdMode == 'cover1'
		newModeText3 = newLcdMode == 'threelines' or newLcdMode == 'cover3'
		oldModeText1 = self.previousLcdMode == 'oneline' or self.previousLcdMode == 'cover1'
		oldModeText3 = self.previousLcdMode == 'threelines' or self.previousLcdMode == 'cover3'
		newModeRunning = newLcdMode == 'running'
		# lcdModeChanged: only True for mode changes which require restart
		lcdModeChanged = (self.previousLcdMode != newLcdMode)
		lcdTextChanged = newModeText1 != oldModeText1 or newModeText3 != oldModeText3
		lcdSizeChanged = self.previousLcdSize != newLcdSize
		lcdFontChanged = self.previousLcdFontSize != config.plugins.yampmusicplayer.lcdFontSize.value
		lcdColor1Changed = self.previousLcdColor1 != config.plugins.yampmusicplayer.lcdColorLine1.value
		lcdColor2Changed = self.previousLcdColor2 != config.plugins.yampmusicplayer.lcdColorLine2.value
		lcdColor3Changed = self.previousLcdColor3 != config.plugins.yampmusicplayer.lcdColorLine3.value
		lcdRunFontChanged = self.previousLcdRunFontSize != config.plugins.yampmusicplayer.lcdRunningFontSize.value or newModeRunning and lcdModeChanged
		lcdXmlChanged = lcdRunningChanged = False
		if not newLcdOffOrCustom:
			lcdXmlChanged = lcdTextChanged or lcdFontChanged or lcdTextLenChanged or lcdTextLeftChanged or lcdTextAlignChanged or lcdColor1Changed or lcdColor2Changed or lcdColor3Changed or lcdCoverSizeChanged or covAlignChanged
			lcdRunningChanged = lcdRunFontChanged
		# lcdChanged: only True for mode changes which require restart
		lcdChanged = lcdModeChanged or lcdSizeChanged or lcdXmlChanged or lcdRunningChanged
		dbPathChanged = self.previousDbPath != config.plugins.yampmusicplayer.databasePath.value
		self.close(False, skinChanged, dbPathChanged, lcdChanged, lcdXmlChanged, lcdRunningChanged)

	def askTvon(self):
		if config.plugins.yampmusicplayer.yampShowTV.value == 'no':
			choices = []
			choices.append((_('no TV at all'), 'no'))
			choices.append((_('Audio only on Start only'), 'AudioStart'))
			choices.append((_('With picture on Start only'), 'AudioPicStart'))
			choices.append((_('Audio always'), 'Audio'))
			choices.append((_('With picture always'), 'AudioPic'))

			self.session.openWithCallback(self.askTvonChoice, ChoiceBox, title=_('you selected a skin with video-preview\nPlease select if you want to switch on TV in preview window now:'), list=choices)

	def askTvonChoice(self, choice):
		if choice is not None:
			try:
				config.plugins.yampmusicplayer.yampShowTV.choices.choices = [
				("no", _("no TV at all")),
				("AudioStart", _("Audio only on Start only")),
				("AudioPicStart", _("With picture on Start only")),
				("Audio", _("Audio always")),
				("AudioPic", _("With picture always")),
				]
			except Exception as e:
				LOG('YampConfigScreen: askTvonChoice: setchoices: EXCEPT: ' + str(e), 'err')
			config.plugins.yampmusicplayer.yampShowTV.value = choice[1]
			config.plugins.yampmusicplayer.yampShowTV.save()

	def keyBlue(self):
		pass

	def keyYellow(self):
		selection = self["config"].getCurrent()
		if selection == self.confPlayOffset:
			try:
				config.plugins.yampmusicplayer.lyricsPlayOffsetTime.value *= -1
			except Exception as e:
				LOG('YampConfigScreen: keyYellow1: EXCEPT: ' + str(e), 'err')
			try:
				self["config"].instance.moveSelection(self["config"].instance.moveDown)
				self["config"].instance.moveSelection(self["config"].instance.moveUp)
			except Exception as e:
				LOG('YampConfigScreen: keyYellow2: EXCEPT: ' + str(e), 'err')

	def keyExit(self):
		try:
			for x in self["config"].list:
				x[1].cancel()
		except Exception as e:
			LOG('YampConfigScreen: keyExit: EXCEPT: ' + str(e), 'err')
		self.close(True, False, False, False, False, False)

	def showHidePig(self, show):
		try:
			for element in self.renderer:
				if "eVideoWidget" in str(vars(element)):
					if show:
						element.instance.show()
					else:
						element.instance.hide()
		except Exception as e:
			LOG('YampConfigScreen: showHidePig: EXCEPT: ' + str(e), 'err')

	def changedEntry(self):
		selection = self["config"].getCurrent()
		try:
			actidx = self["config"].getCurrentIndex()

			if selection == self.confSkin:
				newSkin, failed = self.checkValidSkin()
				if failed:
					if self.callingKeyLeft:
						ConfigListScreen.keyRight(self)
					else:
						ConfigListScreen.keyLeft(self)
					self.deleteSkinOption(newSkin)
			if selection == self.confModeLcd:
				if config.plugins.yampmusicplayer.yampLcdMode.value == 'running':
					if writeVTIRunningRenderer():
						self.msgWriteLcdFilesFailed('YampLcdRunning.xml')
			if selection == self.confSizeOfLcd or selection == self.confModeLcd:
				self.buildConfig()
				self["config"].setList(self.list)
			# bring selection back to previous selected item, if Mode no longer displayed
			if selection == self.confModeLcd:
				if config.plugins.yampmusicplayer.yampLcdMode.value == 'off':
					self["config"].instance.moveSelectionTo(actidx - 1)
				elif self.prevMode == 'off':
					self["config"].instance.moveSelectionTo(actidx + 1)
				self.prevMode = config.plugins.yampmusicplayer.yampLcdMode.value
			self.calcNewLCDvalues()
		except Exception as e:
			LOG('YampConfigScreen: changedEntry: EXCEPT: ' + str(e), 'err')

	def msgReadCoverSizeFromFileFailed(self):
		filename = join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, 'YampLCD.xml')
		msg = _('Could not read cover size from\n\n%s\n\nWrong formatted?\n\nSelection of box-display size <custom> disabled.') % (filename)
		self.session.open(MessageBox, msg, type=MessageBox.TYPE_ERROR, timeout=30)


class YampSelectPathScreenV33(Screen):
	def __init__(self, session, initDir, text):
		Screen.__init__(self, session)
		xmlfile = join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampSelectPath.xml")
		if not exists(xmlfile):
			LOG('YampSelectPathScreenV33: __init__: File not found: "%s"' % xmlfile, 'err')
			return
		with open(xmlfile, 'r') as f:
			self.skin = f.read()
		inhibitDirs = ["/bin", "/boot", "/dev", "/etc", "/lib", "/proc", "/sbin", "/sys", "/usr", "/var"]
		inhibitMounts = []
		self["title"] = Label(_('YAMP Music Player - Select Path for %s') % (text))
		self["filelist"] = FileList(initDir, showDirectories=True, showFiles=False, inhibitMounts=inhibitMounts, inhibitDirs=inhibitDirs)
		self["target"] = Label()
		self["actions"] = ActionMap(["YampActions", "YampOtherActions"],
		{
			"exit": self.keyExit,
			"left": self.keyPageUp,
			"right": self.keyPageDown,
			"up": self.keyMoveUp,
			"down": self.keyMoveDown,
			"ok": self.keyOK,
			"green": self.keyGreen,
			"red": self.keyExit,
			"prevBouquet": self.keyPageUp,
			"nextBouquet": self.keyPageDown,
			"altMoveTop": self.keyMoveTop,
			"altMoveEnd": self.keyMoveEnd,
		}, -1)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		self.keyOK()

	def keyExit(self):
		self.close(None)

	def keyGreen(self):
		self.close(self["filelist"].getSelection()[0])

	def keyMoveUp(self):
		self["filelist"].up()
		self.updateTarget()

	def keyMoveTop(self):
		self["filelist"].moveToIndex(0)
		self.updateTarget()

	def keyMoveDown(self):
		self["filelist"].down()
		self.updateTarget()

	def keyMoveEnd(self):
		self["filelist"].moveToIndex(10000)
		self.updateTarget()

	def keyPageUp(self):
		self["filelist"].pageUp()
		self.updateTarget()

	def keyPageDown(self):
		self["filelist"].pageDown()
		self.updateTarget()

	def keyOK(self):
		if self["filelist"].canDescent():
			self["filelist"].descent()
			self.updateTarget()

	def updateTarget(self):
		currFolder = self["filelist"].getSelection()[0]
		if currFolder is not None:
			self["target"].setText(currFolder)
		else:
			self["target"].setText(_("Invalid Location"))
