#######################################################################
#
#	YAMP - Yet Another Music Player
#	Version 3.3.2 2024-03-22
#	Coded by JohnHenry (c)2013 (up to V2.6.5)
#	Extended by AlfredENeumann (c)2016-2024
#   Last change: 2025-09-26 by Mr.Servo @OpenATV
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
#	Thanks to the authors of Merlin Music Player and OpenPli Media
#	Player for ideas and code snippets
#
#######################################################################
#TYPES OF LOGGING:
#spe:	Coversuche
#spe2:	Bildschirmschoner checks
#spe3:
#spe4:

from base64 import b64decode
from datetime import datetime
from io import BytesIO
from os import makedirs, system, walk, access, listdir, remove, stat, R_OK, W_OK
from os.path import join, exists, abspath, isfile, isdir, splitext, basename, dirname
from PIL import Image
from random import shuffle
from re import findall, sub, compile, split, I
from sqlite3 import Row, IntegrityError, connect
from sys import path as sys_path
from threading import Thread, Lock
from time import time, strftime
from traceback import print_exc
from urllib.parse import quote, quote_plus
from twisted.internet.reactor import callInThread
import xml.etree.ElementTree as xmlET
from mutagen.flac import Picture, FLAC, error as FLACError
from mutagen.id3 import ID3
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
from enigma import eServiceCenter, eServiceReference, getDesktop, iServiceInformation, iPlayableService, ePythonMessagePump, eTimer
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.config import config, ConfigSubsection, ConfigDirectory, ConfigYesNo, ConfigSelection, ConfigInteger, ConfigText, configfile
from Components.Label import Label
from Components.Pixmap import Pixmap, MultiPixmap
from Components.ServiceEventTracker import ServiceEventTracker, InfoBarBase
from Components.Sources.Boolean import Boolean
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBarGenerics import InfoBarSeek, InfoBarNotifications
from Screens.MessageBox import MessageBox
from Screens.HelpMenu import HelpableScreen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Screens.Screen import Screen
from ServiceReference import ServiceReference
from Tools.BoundFunction import boundFunction
from Tools.Directories import resolveFilename, SCOPE_CONFIG
from .YampConfig import YampConfigScreenV33
from .YampDatabaseList import YampDatabaseList, DblistStackEntry, DblistEntryComponent
from .YampFileFunctions import writeLcd, writeLcdRunning
from .YampFileList import YampFileList
from .YampLyrics import YampLyricsScreenV33
from .YampLyricsFunctions import getLyricsID3, textToList, searchLyricsfromFiles
from .YampPixmaps import YampCoverArtPixmap, YampScreenSaver
from .YampPlayList import YampPlayList
from .YampPlaylistParsers import YampParserE2pls, YampParserM3u, YampParserPls
from .YampBoxDisplay import YampLCDRunningScreenV33, YampLCDScreenV33
from .YampVideoSpecial import YampVideoTitleV33, YampVideoLyricsV33
from .YampFileFunctions import readRcButtonTexts
from .YampCommonFunctions import readID3Infos
from .YampHelp import YampHelpScreenV33
from .YampCommonFunctions import getUrlData
from .YampGlobals import *  # exceptionally with '*' because there are dozens of globals
from .myLogger import LOG
from . import _, __version__

YAMPVERSION = 'V ' + __version__ + '  2025-09-26'
VERSIONDATE = 20240322
DOWNLOADBASETIME = 125
FANARTDLTIMEMUL = 48
FANARTDLTIMEPERSONALMUL = 4
FANARTDLTIME = DOWNLOADBASETIME * FANARTDLTIMEMUL
FANARTDLTIMEPERSONAL = DOWNLOADBASETIME * FANARTDLTIMEPERSONALMUL
FANARTTVPERSAPIFILE = '/etc/enigma2/YampFanarttvPersonalApi.key'  #TOTO resolveFilename
INFOBARTEXTLIST = ('n/a', '   ', ' - ', ' . ')
COVER_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp", ".gif"]
AUDIO_EXTENSIONS = (".mp2", ".mp3", ".wav", ".ogg", ".flac", ".m4a", ".wma")
COVER_MINSIZE = 500
selectedDirExcludeValue = 0
dirExcludeOptions = []

colors = [
	("#FFFFFF", _("white")),
	("#FF0000", _("red")),
	("#00FF00", _("green")),
	("#0000FF", _("blue")),
	("#FFFF00", _("yellow")),
	("#A4C400", _("lime green")),
	("#BDFF2F", _("light green")),
	("#FF69B4", _("pink")),
	("#FF00FF", _("magenta")),
	("#A81CEE", _("violett")),
	("#1BA1E2", _("cyan")),
	("#33B5E5", _("light blue")),
	("#FFB347", _("orange")),
	]

# Configuration Entries
config.plugins.yampmusicplayer = ConfigSubsection()
config.plugins.yampmusicplayer.yampInExtendedPluginlist = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.yampInMainMenu = ConfigYesNo(default=False)
config.plugins.yampmusicplayer.debugPath = ConfigDirectory(default="/home/root/logs")
config.plugins.yampmusicplayer.yampDebugMode = ConfigSelection(default="error", choices=[
			("off", _("off")),
			("error", _("errors only")),
			("all", _("all")),
			("special", _("special")),
			("special2", _("special2")),
			("special3", _("special3")),
			("special4", _("special4")),
			])
skinTexts = [_("Standard skin HD"), _("Standard skin HD with Video Preview"), _("Custom skin HD"), ("Full HD standard skin"), ("Full HD coffee skin"), _("Full HD standard skin (special VTi)"), _("Custom Full HD skin")]

#General Adjustments
RESOLUTION = "FHD" if getDesktop(0).size().width() > 1280 else "HD"
if RESOLUTION == "FHD":
	config.plugins.yampmusicplayer.yampSkin = ConfigSelection(default="fhd", choices=[
		("default", _("Standard skin (HD)")),
		("defaultTV", _("Standard skin (HD) with Video Preview")),
		("custom", _("Custom skin (HD)")),
		("fhd", _("Full HD standard skin")),
		("fhdCoffee", _("Full HD 'coffee' skin")),
		("fhdCustom", _("Custom Full HD skin")),
		])
else:  # HD
	config.plugins.yampmusicplayer.yampSkin = ConfigSelection(default="default", choices=[
		("default", _("Standard skin (HD)")),
		("defaultTV", _("Standard skin (HD) with Video Preview")),
		("fhdCoffee", _("Full HD 'coffee' skin")),
		("custom", _("Custom skin (HD)")),
		])

textfile = join(yampDir, 'ExcludeSubDirs.txt')
if exists(textfile):
	with open(textfile, 'r') as f:
		lines = f.readlines()
	try:
		for line in lines:
			if line[0] != ';' and len(line.strip()):
				dirExcludeOptions.append(line.strip())
	except Exception as e:
		LOG('Yamp: Start: dirExcludeOptions: EXCEPT: ' + str(e), 'err')
else:
	LOG('YampScreen: GLOBALS: File not found: "%s"' % textfile, 'err')
	del textfile

config.plugins.yampmusicplayer.databasePath = ConfigDirectory(default="/media/hdd/Yamp/")
config.plugins.yampmusicplayer.musicFilePath = ConfigDirectory(default="/media/hdd/")
config.plugins.yampmusicplayer.saveLastFilebrowserPath = ConfigYesNo(default=False)
config.plugins.yampmusicplayer.playlistPath = ConfigDirectory(default="/media/hdd/Yamp/Playlists/")
config.plugins.yampmusicplayer.useSingleLyricsPath = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.lyricsPath = ConfigDirectory(default="/media/hdd/Yamp/Lyrics/")
config.plugins.yampmusicplayer.screenSaverSlidePath = ConfigDirectory(default="/media/hdd/")
config.plugins.yampmusicplayer.screenSaverArtworkPath = ConfigDirectory(default="/media/hdd/Yamp/ArtistPics/")
for cpath in [
	config.plugins.yampmusicplayer.debugPath.value,
	config.plugins.yampmusicplayer.databasePath.value,
	config.plugins.yampmusicplayer.lyricsPath.value,
	config.plugins.yampmusicplayer.playlistPath.value,
	config.plugins.yampmusicplayer.screenSaverArtworkPath.value]:
	if not exists(cpath):
		makedirs(cpath)

#Databaselist / Playlist
config.plugins.yampmusicplayer.fileListTitleLayout = ConfigSelection(default="titleAndPath", choices=[
		("titleOnly", _("Title Only")),
		("pathOnly", _("Path Only")),
		("titleAndPath", _("Title and Path")),
		])
lenDirExclOptions = len(dirExcludeOptions)
excludeOpt = [("0", _("no exclude")),]
if lenDirExclOptions >= 1:
	excludeOpt.append(("1", dirExcludeOptions[0]))
if lenDirExclOptions >= 2:
	opt3 = _('%s or %s') % (dirExcludeOptions[0], dirExcludeOptions[1])
	exclL2 = [("2", dirExcludeOptions[1]), ("3", opt3)]
	excludeOpt.extend(exclL2)
if lenDirExclOptions >= 2:
	config.plugins.yampmusicplayer.dbExcludeDir = ConfigSelection(default="3", choices=excludeOpt)
elif lenDirExclOptions == 1:
	config.plugins.yampmusicplayer.dbExcludeDir = ConfigSelection(default="1", choices=excludeOpt)
else:
	config.plugins.yampmusicplayer.dbExcludeDir = ConfigSelection(default="0", choices=excludeOpt)
config.plugins.yampmusicplayer.dbArtistReduce = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.titleOnlyOnceInSelection = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.capitalizeTitleAndArtist = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.playlistLayout = ConfigSelection(default="titart", choices=[
		("fn", _("Filename without Extension")),
		("fnext", _("Filename with Extension")),
		("tit", _("Title")),
		("titart", _("Title and Artist")),
		("titart2", _("Artist and Title")),
		])
config.plugins.yampmusicplayer.displayNext = ConfigSelection(default="0", choices=[
		("0", _("Title - Artist - Album")),
		("1", _("Title - Album - Artist")),
		("2", _("Artist - Title - Album")),
		("3", _("Artist - Album - Title")),
		("4", _("Title - Artist")),
		("5", _("Title - Album")),
		("6", _("Artist - Title")),
		("7", _("Artist - Album")),
		("8", _("Title")),
		])
config.plugins.yampmusicplayer.displayUnknown = ConfigSelection(default="0", choices=[
		("0", _("no change: <n/a>")),
		("1", _("3 x blank: <   >")),
		("2", _("blank - minus - blank: < - >")),
		("3", _("blank - dot - blank: < . >")),
		])
config.plugins.yampmusicplayer.savePlaylistOnExit = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.repeatPlaylistAtEnd = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.wrapMovePlaylist = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.startImmediate = ConfigYesNo(default=False)
config.plugins.yampmusicplayer.gapCorrection = ConfigInteger(0, limits=(0, 100))

#Cover Search
coverSearchChoices = [
		("0", _("off")),
		("coverID3", _("search in ID3-tags (mp3, flac, m4a, mp4)")),
		("coverDirTitle", _("search for <title>.<ext> in title-directory")),
		("coverAlbum", _("search for albumcover.<ext> in title-directory")),
		("coverDirAny", _("search for any picture in title-directory")),
		("coverGoogle", _("search at google online")),
		]
config.plugins.yampmusicplayer.prioCover1 = ConfigSelection(default="coverID3", choices=coverSearchChoices)
config.plugins.yampmusicplayer.prioCover2 = ConfigSelection(default="coverDirTitle", choices=coverSearchChoices)
config.plugins.yampmusicplayer.prioCover3 = ConfigSelection(default="coverAlbum", choices=coverSearchChoices)
config.plugins.yampmusicplayer.prioCover4 = ConfigSelection(default="0", choices=coverSearchChoices)
config.plugins.yampmusicplayer.prioCover5 = ConfigSelection(default="coverGoogle", choices=coverSearchChoices)
config.plugins.yampmusicplayer.searchGoogleCoverVideo = ConfigYesNo(default=False)
config.plugins.yampmusicplayer.saveCover = ConfigSelection(default="0", choices=[
		("0", _("off")),
		("titleNoPicture", _("save <title>.<ext> if no picture in song dir")),
		("titleNoTitle", _("save <title>.<ext> if not existing in song dir")),
		("titleAlways", _("save <title>.<ext>, overwrite existing")),
		("albumNoAlbum", _("save albumcover.<ext> if not existing")),
		("albumAlways", _("save albumcover.<ext>, overwrite existing")),
		])

#Lyrics Search
lyrSearchChoices = [
		("0", _("off")),
		("lyricsFile", _("search in lyrics-directory")),
		("lyricsID3", _("search in ID3-tags (mp3, flac, m4a, mp4)")),
		("lyricsAZ", _("search at azlyrics.com online")),
		("lyricsChart", _("search at chartlyrics.com online")),
#		("lyricsGenius", _("search at genius.com online")),
		]
config.plugins.yampmusicplayer.prioLyrics1 = ConfigSelection(default="lyricsFile", choices=lyrSearchChoices)
config.plugins.yampmusicplayer.prioLyrics2 = ConfigSelection(default="lyricsID3", choices=lyrSearchChoices)
config.plugins.yampmusicplayer.prioLyrics3 = ConfigSelection(default="lyricsAZ", choices=lyrSearchChoices)
config.plugins.yampmusicplayer.prioLyrics4 = ConfigSelection(default="lyricsChart", choices=lyrSearchChoices)
config.plugins.yampmusicplayer.autoSaveLyrics = ConfigYesNo(default=False)

#Fanart Search
config.plugins.yampmusicplayer.searchFanart = ConfigSelection(default="60", choices=[
		("off", _("off")),
		("newArtists", _("search only for new artists")),
		("15", _("search every 15 days")),
		("30", _("search every 30 days")),
		("60", _("search every 60 days")),
		("90", _("search every 90 days")),
		("180", _("search every 180 days")),
		("always", _("search always")),
		])
config.plugins.yampmusicplayer.fanarttvPersonal = ConfigText(default='1234567890abcdef7890123456789012', fixed_size=True, visible_width=33)			 #personal api key
config.plugins.yampmusicplayer.fanarttvPersonal.setUseableChars('0123456789abcdef')
config.plugins.yampmusicplayer.searchMbidMode = ConfigSelection(default="standard", choices=[
		("standard", _("standard like on muscicbrainz website")),
		("special", _("special, use if standard is not working")),
		])
config.plugins.yampmusicplayer.searchMbidMinScore = ConfigInteger(95, limits=(1, 100))

#Screensaver
config.plugins.yampmusicplayer.screenSaverMode = ConfigSelection(default="artwork", choices=[
		("blank", _("Blank screen")),
		("standard", _("Standard Screensaver")),
		("custom", _("Custom Screensaver (Dia-Show)")),
		("artwork", _("Artwork as Screensaver")),
		])
config.plugins.yampmusicplayer.screenSaverBg = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.resetScreenSaverBg = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.screenSaverSubDirs = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.screenSaverWait = ConfigInteger(10, limits=(0, 600))
config.plugins.yampmusicplayer.screenSaverNextSlide = ConfigInteger(10, limits=(5, 99))
config.plugins.yampmusicplayer.screenSaverSort = ConfigSelection(default="shuffle", choices=[
		("nosort", _("not sorting")),
		("sortA", _("sorting A->Z")),
		("sortZ", _("sorting Z->A")),
		("shuffle", _("shuffling")),
		])
config.plugins.yampmusicplayer.screenSaverLeft = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.manKeyScreensaver = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.maxTimeSSoffMan = ConfigInteger(600, limits=(0, 1200))
config.plugins.yampmusicplayer.showInfoBarBg = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.showClockSS = ConfigSelection(default="no", choices=[
		("no", _("no")),
		("clock", _("clock only")),
		("clockbg", _("clock with background")),
		("date", _("date only")),
		("datebg", _("date with background")),
		("clockdate", _("clock and date")),
		("clockdatebg", _("clock and date with background")),
		])

#Operation / Display
config.plugins.yampmusicplayer.playlistMoveMulti = ConfigInteger(10, limits=(2, 50))
config.plugins.yampmusicplayer.coverScrollTime = ConfigInteger(10, limits=(0, 600))
config.plugins.yampmusicplayer.fileListIcons = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.playListIcons = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.displaySkinname = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.displayButtonHelp = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.displayDiaName = ConfigSelection(default="no", choices=[
		("no", _("no")),
		("name", _("filename only")),
		("namebg", _("filename with background")),
		("pathname", _("path + filename")),
		("pathnamebg", _("path + filename with background")),
		])
config.plugins.yampmusicplayer.showPlayListLen = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.newExitKey = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.commonPlayPause = ConfigYesNo(default=False)
config.plugins.yampmusicplayer.commonTvRadio = ConfigSelection(default="no", choices=[
		("no", _("no")),
		("TvShuffle", _("Tv shuffle, TvLong PL endless")),
		("TvEndless", _("Tv PL endless, TvLong shuffle")),
		("RadioShuffle", _("Radio shuffle, RadioLong PL endless")),
		("RadioEndless", _("Radio PL endless, RadioLong shuffle")),
		])
config.plugins.yampmusicplayer.showHelpStart = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.yampConfirmExit = ConfigYesNo(default=True)

if config.plugins.yampmusicplayer.yampSkin.value == 'default' or config.plugins.yampmusicplayer.yampSkin.value == 'defaultDreamOS':
	config.plugins.yampmusicplayer.yampShowTV = ConfigSelection(default="no", choices=[
		("no", _("no TV at all")),
		("AudioStart", _("Audio only on Start only")),
		("Audio", _("Audio always")),
		])
else:
	config.plugins.yampmusicplayer.yampShowTV = ConfigSelection(default="no", choices=[
		("no", _("no TV at all")),
		("AudioStart", _("Audio only on Start only")),
		("AudioPicStart", _("With picture on Start only")),
		("Audio", _("Audio always")),
		("AudioPic", _("With picture always")),
		])

#Lyrics
config.plugins.yampmusicplayer.lyricsMinLinesScroll = ConfigInteger(20, limits=(0, 100))
config.plugins.yampmusicplayer.lyricsScrollLine = ConfigInteger(7, limits=(1, 100))
config.plugins.yampmusicplayer.lyricsOffsetTime = ConfigInteger(1000, limits=(0, 5000))
config.plugins.yampmusicplayer.lyricsPlayOffsetTime = ConfigInteger(0, limits=(-10000, 10000))
config.plugins.yampmusicplayer.karaokeMaxTime = ConfigInteger(10, limits=(0, 600))
config.plugins.yampmusicplayer.karaokeBg = ConfigSelection(default="both", choices=[
		("no", _("no")),
		("small", _("only small karaoke line (key Text)")),
		("big", _("only big karaoke line (key Text long)")),
		("both", _("small and big karaoke line")),
		])

#Video
config.plugins.yampmusicplayer.videoAutoFull = ConfigSelection(default="screensaver", choices=[
		("immediate", _("immediate")),
		("screensaver", _("screensaver delay")),
		("manual", _("only manual (key ok)")),
		])
config.plugins.yampmusicplayer.showTimeVideoTitle = ConfigInteger(10, limits=(0, 10000))
config.plugins.yampmusicplayer.showClockVideo = ConfigSelection(default="no", choices=[
		("no", _("no")),
		("clock", _("clock only")),
		("clockbg", _("clock with background")),
		("date", _("date only")),
		("datebg", _("date with background")),
		("clockdate", _("clock and date")),
		("clockdatebg", _("clock and date with background")),
		])
config.plugins.yampmusicplayer.showLyricsOnVideo = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.insertBlankVideo = ConfigYesNo(default=False)
config.plugins.yampmusicplayer.blankVideoDelay = ConfigInteger(250, limits=(0, 6000))

#Box Display
try:
	config.plugins.yampmusicplayer.yampLcdMode = ConfigSelection(default="threelines", choices=[
			("off", _("off - useful for LCD4linux or similar")),
			("oneline", _("1 line display")),
			("threelines", _("3 lines display")),
			("cover", _("display cover (graphical)")),
			("cover1", _("display cover (graphical) + 1 line text")),
			("cover3", _("display cover (graphical) + 3 lines text")),
			("running", _("Running Text (graphical)")),
			])
	config.plugins.yampmusicplayer.lcdSize = ConfigSelection(default="custom", choices=[
			("800x480", _("800 x 480")),
			("480x320", _("480 x 320")),
			("400x240", _("400 x 240")),
			("320x200", _("320 x 240")),
			("220x176", _("220 x 176")),
			("132x64", _("132 x 64")),
			("custom", _("custom")),
			])
	config.plugins.yampmusicplayer.lcdFontSize = ConfigInteger(32, limits=(10, 200))
	config.plugins.yampmusicplayer.lcdTextLen = ConfigInteger(160, limits=(10, 999))
	config.plugins.yampmusicplayer.lcdTextHoriz = ConfigSelection(default="left", choices=[
			("left", _("left")),
			("center", _("center")),
			("right", _("right")),
			])

	config.plugins.yampmusicplayer.lcdColorLine1 = ConfigSelection(default="#FFFFFF", choices=colors)
	config.plugins.yampmusicplayer.lcdColorLine2 = ConfigSelection(default="#FFFFFF", choices=colors)
	config.plugins.yampmusicplayer.lcdColorLine3 = ConfigSelection(default="#FFFFFF", choices=colors)

	config.plugins.yampmusicplayer.lcdCoverSize = ConfigInteger(60, limits=(10, 999))
	config.plugins.yampmusicplayer.lcdCoverColor = ConfigSelection(default="bw", choices=[
			("bw", _("black & white")),
			("bwt", _("black & white transparent")),
			("color", _("color")),
			("colort", _("color transparent")),
			])
	config.plugins.yampmusicplayer.lcdCoverHoriz = ConfigSelection(default="right", choices=[
			("left", _("left")),
			("center", _("center")),
			("right", _("right")),
			])
	config.plugins.yampmusicplayer.lcdCoverVert = ConfigSelection(default="center", choices=[
			("top", _("top")),
			("center", _("center")),
			("bottom", _("bottom")),
			])
except Exception:
	pass
config.plugins.yampmusicplayer.lcdRunningFontSize = ConfigInteger(38, limits=(1, 500))

#Miscellaneous
config.plugins.yampmusicplayer.yampInExtendedPluginlist = ConfigYesNo(default=True)
config.plugins.yampmusicplayer.yampInMainMenu = ConfigYesNo(default=False)
config.plugins.yampmusicplayer.yampDebugMode = ConfigSelection(default="error", choices=[
		("off", _("off")),
		("error", _("errors only")),
		("all", _("all")),
		("special", _("special")),
		("special2", _("special2")),
		("special3", _("special3")),
		("special4", _("special4")),
		])
config.plugins.yampmusicplayer.debugPath = ConfigDirectory(default="/home/root/logs")
config.plugins.yampmusicplayer.yampDebugMemory = ConfigYesNo(default=False)

#config entries not configurable by user
#--------------------------------------------
config.plugins.yampmusicplayer.lastVersionDate = ConfigInteger(0)
config.plugins.yampmusicplayer.startWithDatabase = ConfigYesNo(default=False)
config.plugins.yampmusicplayer.shuffle = ConfigYesNo(default=False)
config.plugins.yampmusicplayer.lastPlaylistIndex = ConfigInteger(-1)
config.plugins.yampmusicplayer.lastSlide = ConfigText(default="")
config.plugins.yampmusicplayer.debugFile = ConfigText(default="")
config.plugins.yampmusicplayer.lcdTextPosX = ConfigInteger(0)
config.plugins.yampmusicplayer.lcdTextLeftMin = ConfigInteger(0)
config.plugins.yampmusicplayer.lcdTextTopMin = ConfigInteger(0)
config.plugins.yampmusicplayer.lcdCoverPosX = ConfigInteger(0)
config.plugins.yampmusicplayer.lcdCoverPosY = ConfigInteger(0)
config.plugins.yampmusicplayer.karaokeFileOffsetVal = ConfigInteger(0)
config.plugins.yampmusicplayer.separator = ConfigSelection(default="1", choices=[('1', '')])

global yamp_session
yamp_session = None


def checkAttributes(element, NameText, searchText):
	check = False
	if element.skinAttributes is not None:
		for (attrib, value) in element.skinAttributes:
			try:
				if attrib == NameText and value == searchText:
					check = True
			except Exception as e:
				LOG('YampScreen: checkAttributes: if ATTR: EXCEPT %s' % (str(e)), 'err')
	return check

# The YAMP main screen class - needs minimum a HD skin (minimum 1280x720)


class YampScreenV33(Screen, InfoBarBase, InfoBarSeek, InfoBarNotifications, HelpableScreen):
#	@classmethod
	def __init__(self, session):
		global selectedDirExcludeValue
		global yampTitlecaseNochange
		self.logpath = config.plugins.yampmusicplayer.debugPath.value
		self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
		config.plugins.yampmusicplayer.debugFile.value = self.logpath + 'yamp_debug_' + self.timestamp + '.log'
		try:  #create a coverlcd.png in /tmp
			filename1 = yampDir + 'common/coverlcddummy.png'
			filename2 = '/tmp/coverlcd.png'
			system("cp %s %s" % (filename1, filename2))
		except Exception as e:
			LOG('YampScreen: Init: create coverlcd.png: EXCEPT: %s' % (str(e)), 'err')
		Screen.__init__(self, session)
		self.memlog = config.plugins.yampmusicplayer.yampDebugMemory.value
		self.memlogfile = self.logpath + 'yamp_mem_' + self.timestamp + '.log'
		self.configSkin, self.newSkin, self.skinChangedMissing, self.oldCustomSkin = self.checkCustomSkins()
		skinText = self.getSkinName(self.configSkin)
		LOG('YampScreenV33: __init__: configSkin: "%s", skinChangedMissing: "%s" ' % (self.configSkin, self.skinChangedMissing), 'all')
		selectedDirExcludeValue = int(config.plugins.yampmusicplayer.dbExcludeDir.value)
		xmlfile = join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "Yamp.xml")
		if not exists(xmlfile):
			LOG('YampScreenV33: GLOBALS: File not found: "%s"' % xmlfile, 'err')
			return
		with open(xmlfile, 'r') as f:
			self.skin = f.read()
		InfoBarBase.__init__(self)
		InfoBarNotifications.__init__(self)
		HelpableScreen.__init__(self)
		self.versionNumber = VERSIONNUMBER
		self.screenSaverFirstCall = True  # avoid switching to next picture on first call of timer
		self.screenSaverManOff = False
		self.isVideoFullScreen = False
		self.lyrics = ''
		self.lyricsKarMsgboxShow = True
		self.LcdText = ""
		self.videoPreviewOn = False
		self.setTVOptions()
		self.session = session
		self.myOldService = self.session.nav.getCurrentlyPlayingServiceReference()
		if self.TvOff:
			self.session.nav.stopService()
		self.playlistparsers = {}  # parsers for external playlists
		self.addPlaylistParser(YampParserM3u, ".m3u")
		self.addPlaylistParser(YampParserPls, ".pls")
		self.addPlaylistParser(YampParserE2pls, ".e2pls")
		self.playedSec = 0
		self.totalSec = 0
		self.totalMin = 0
		startingDir = config.plugins.yampmusicplayer.musicFilePath.value
		self.filelist = YampFileList(startingDir, matchingPattern=r"(?i)^.*\.(mp2|mp3|ogg|ts|wav|m3u|pls|e2pls|mpg|vob|avi|divx|m4v|mkv|mp4|m4a|dat|flac|mov|m2ts)", showDirectories=True, showFiles=True, useServiceRef=True, enableWrapAround=True, additionalExtensions="4098:m3u 4098:e2pls 4098:pls")
		try:  # for blank video only
			startingDir2 = '/usr/lib/enigma2/python/Plugins/Extensions/YampMusicPlayer/common/'
			self.filelistint = YampFileList(startingDir2, matchingPattern=r"(?i)^.*\.(mp4)", showDirectories=False, showFiles=True, useServiceRef=True, enableWrapAround=False, additionalExtensions="4098:m3u 4098:e2pls 4098:pls")
		except Exception as e:
			LOG('YampScreen: Init: filelistint: EXCEPT: %s' % (str(e)), 'err')
		self["filelist"] = self.filelist
		self.dblist = YampDatabaseList()
		self["dblist"] = self.dblist
		self["title"] = Label("YAMP Music Player  " + YAMPVERSION)
		self["actskin"] = Label(skinText)
		self["leftContentTitle"] = Label("")
		self["rightContentTitle"] = Label(_("P l a y l i s t"))
		self.playlist = YampPlayList()
		self["playlist"] = self.playlist
		self["songtitle"] = Label("")
		self["artist"] = Label("")
		self["album"] = Label("")
		self["year"] = Label("")
		self["genre"] = Label("")
		self["nextsong"] = Label(_("Next Song"))
		self["nextsongtitle"] = Label("")
		self["coverArt"] = YampCoverArtPixmap()
		self["screenSaver"] = YampScreenSaver()
		self["screenSaver"].hide()
		self["screenSaverBackground"] = Pixmap()
		self["screenSaverBackground"].hide()
		self["repeat"] = MultiPixmap()
		self["shuffle"] = MultiPixmap()
		self["saver"] = MultiPixmap()
		self["txtRepeat"] = Label()
		self["txtShuffle"] = Label()
		self["key_red"] = Label("")
		self["key_green"] = Label("")
		self["key_yellow"] = Label("")
		self["key_blue"] = Label("")
		self["textInfo"] = Label("INFO")
		self["textSaver"] = Label("PVR")
		self["fanartdownload"] = Label("")
		self["musicbrainzlogo"] = Boolean(False)
		self["fanartlogo"] = Boolean(False)
		self["downloadBackground"] = Label("")
		self["clockBackground"] = Pixmap()
		self["dateBackground"] = Pixmap()
		self["songInfoBg"] = Boolean(True)
		self["session.CurrentService"] = Boolean(False)
		self["karaoke"] = Boolean(False)
		self["karaokeBig"] = Boolean(False)
		self["bitRate"] = Label("")
		self["lyricsLine"] = Label("")
		self["lyricsLineBackground"] = Pixmap()
		self["lyricsLineBig"] = Label("")
		self["lyricsLineBackgroundBig"] = Pixmap()
		self["pathNameSSDia"] = Label("")
		self["pathNameSSDiaBackground"] = Pixmap()

# Timers
		self.screenSaverTimer = eTimer()
		self.screenSaverTimer.callback.append(self.screenSaverStartTimeout)
		self.coverScrollTimer = eTimer()
		self.coverScrollTimer.callback.append(self.coverScrollTimerTimeout)
		self.nextSlideTimer = eTimer()
		self.nextSlideTimer.callback.append(self.nextSlide)
		self.screenSaverManTimer = eTimer()
		self.screenSaverManTimer.callback.append(self.screenSaverMaxManOff)
		self.eofbugTimer = eTimer()
		self.eofbugTimer.callback.append(self.checkEOF)
		self.gapTimer = eTimer()
		self.gapTimer.callback.append(self.checkGap)
		self.startupTimer = eTimer()
		self.startupTimer.callback.append(self.startupChecks)
		self.blankVideoTimer = eTimer()
		self.blankVideoTimer.callback.append(self.stopBlankVideo)
		self.fanartDlTimer = eTimer()
		self.fanartDlTimer.callback.append(self.fanartDlOk)
		self.fanartDisplayTimer = eTimer()
		self.fanartDisplayTimer.callback.append(self.fanartDisplayStop)
		self.karaokeTimer = eTimer()
		self.karaokeTimer.callback.append(self.checkKaraoke)
		self.karaokeTime = 250  # update time Karaoke line (ms)
		self.karaokeMaxtimeTimer = eTimer()
		self.karaokeMaxtimeTimer.callback.append(self.karaokeMaxtimeTimeout)
		self.AlbumPath = ""
		self.AlbumArtist = ""
		self.AlbumTitle = ""
		self.dbUpgradeInfo331 = 0
		self.dbUpgradeInfo332 = 0

		# Action maps
		self["Actions"] = HelpableActionMap(self, "YampActions",
		{
			"ok": (self.ok, _("Open dir, append to playlist | Play title, toggle screensaver")),
			"play": (self.play, _("Insert into playlist and play")),
			"playLong": (self.playLong, _("Insert incl. subdirs into playlist and play")),
			"pause": (self.pause, _("Pause/resume title")),
			"stop": (self.stopEntry, _("Stop title")),
			"exit": (self.exit, _("Exit screensaver, subscreens or YAMP")),
			"menu": (self.showMenu, _("Show context menu")),
			"prevTitle": (self.previousKey, _("Play previous title")),
			"nextTitle": (self.nextEntry, _("Play next title")),
			"prevBouquet": (self.pageup, _("Previous page")),
			"nextBouquet": (self.pagedown, _("Next page")),
			"right": (self.switchToPlayList, _("Switch to playlist, Screensaver: next slide")),
			"left": (self.switchToFileList, _("Switch to filelist/database, Screensaver: previous slide")),
			"info": (self.showLyrics, _("Show lyrics")),
			"infoLong": (self.infoLongActions, _("Show Yamp Help Screen")),
			"toggleSaver": (self.pausePlaySlideShow, _("Pause/resume screensaver slideshow")),
			"altMoveTop": (self.skipToListbegin, _("Move to start of list")),
			"altMoveEnd": (self.skipToListend, _("Move to end of list")),
			"Tv": (self.tvActions, _("Toggle repeat")),
			"Radio": (self.radioActions, _("Toggle shuffle")),
			"Audio": (self.toggleSsBg, _("Display/Hide Infobar")),
			"Pvr": (self.pvrActions, _("Activate/deactivate screensaver slideshow")),
			"Text": (self.keyTextActions, _("Show/hide Lyrics Line ")),
			"TextLong": (self.keyTextLongActions, _("Show/hide Big Lyrics Line (Karaoke)")),
			"key5": (self.key5Actions, _("Jump back to current playing song")),
			"redLong": (self.redLongActions, _("Screensaver: Blacklist current picture (don't show again)")),
			"keyPercentJumpFw": (self.keyPercentJumpFwActions, _("Jump Forward 10%")),
			"keyPercentJumpBw": (self.keyPercentJumpBwActions, _("Jump Backward 10%")),
			"keyPercentJumpFwLong": (self.keyPercentJumpFwLActions, _("Jump Forward 20%")),
			"keyPercentJumpBwLong": (self.keyPercentJumpBwLActions, _("Jump Backward 20%")),
		}, -2)
		self["OtherActions"] = ActionMap(["YampOtherActions"],
		{
			"up": self.moveup,
			"down": self.movedown,
			"moveTop": self.skipToListbegin,
			"moveEnd": self.skipToListend,
			"red": self.redActions,
			"green": self.greenActions,
			"greenLong": self.greenLongActions,
			"yellow": self.yellowActions,
			"yellowLong": self.yellowLongActions,
			"blue": self.blueActions,
			"blueLong": self.blueLongActions,
			"TvLong": self.tvLongActions,
			"RadioLong": self.radioLongActions,
		}, -2)

		self["HelpActions"] = ActionMap(["YampHelpActions"],
		{
			"help": self.showHelp,
		}, -2)
		InfoBarSeek.__init__(self, actionmap="YampSeekActions")
		self.manKeyScreensaver = config.plugins.yampmusicplayer.manKeyScreensaver.value
		self.currList = "dblist" if config.plugins.yampmusicplayer.startWithDatabase.value else "filelist"
		self.currPath = ""
		self.currFilePath = startingDir
		self.extPlaylistName = ""  # no external playlist loaded
		self.repeat = config.plugins.yampmusicplayer.repeatPlaylistAtEnd.value
		self.ssBackground = config.plugins.yampmusicplayer.screenSaverBg.value
		self.playLongActive = False
		self.redLongActive = False
		self.greenLongActive = False
		self.yellowLongActive = False
		self.blueLongActive = False
		self.infoLongActive = False
		self.textLongActive = False
		self.tvLongActive = False
		self.radioLongActive = False
		self.jumpFwLongActive = False
		self.jumpBwLongActive = False
		self.previousPressed = False
		self.dbStack = []  # for navigation in the database list
		self.dbTitleList = []
		self.dbArtistList = []
		self.dbAlbumList = []
		self.databaseChanged = True
		self.currTitle = ""
		self.currArtist = ""
		self.currAlbum = ""
		self.currLength = ""
		self.currTracknr = -1
		self.currGenre = ""
		self.currYear = ""
		self.currDate = ""
		self.currBitRate = ""
		self.oldTitle = ""
		self.oldArtist = ""
		self.oldAlbum = ""
		self.nextsongtitle = ""
		self.nextSongDisplay = ""
		self.previousIsVideo = False
		self.blankVideoInserted = -1
		self.slidePath = ""
		self.screenSaverOn = True
		self.screenSaverActive = False
		self.slideShowPaused = False
		self.playerState = STATE_NONE
		self.currentIsVideo = False
		self.configScreenActive = False
		self.lyricsScreenActive = False
		self.dbScreenActive = False
		self.virtKeyboardActive = False
		self.pixNumCover = COVERS_NO
		self.requestNum = 0
		self.requestNumSav1 = 0
		self.requestNumSav2 = 0
		self.coverIndex = 0
		self.coverChangedLyrics = False  # for Lyrics
		self.coverChangedGoogleLyrics = False  # for Lyrics
		self.artistIdFanart = 0  # for fanart download
		self.artistFanartDl = ''  # for fanart download
		self.artistFanartDlFinished = False
		self.fanartDlTime = FANARTDLTIME
		self.fanartNumberDl = 0  # total number of available new pictures
		self.fanartSuccessDl = 0  # total number of succesfully downloadedpictures
		self.infoBarNaReplace = 'n/a'
		self.fanarttvAppApikey = '560a6463c90eaa2c586b6abe1c936826'
		self.fanarttvPersonalApikey = ''
		self.videoStartMode = config.plugins.yampmusicplayer.videoAutoFull.value
		self.lyricsPlayOffsetTime90 = config.plugins.yampmusicplayer.lyricsPlayOffsetTime.value * 90
		self.lastPlaylistSearch = ''
		self.lastTextSearch = ''
		self.lastDbSearch = ''
		self.pigElement = self.elementClock = self.elementDate = None
		self.previousCalcLenLists = False
		self.previousFanartDLconfig = ''
		self.artistBgPicsList = []
		self.newArtistBg = False
		self.onLayoutFinish.append(self.layoutFinished)
		self.onClose.append(self.cleanup)
		self.oldLyricsText = ''  # last found Lyrics text
		self.displayLyricsText = ''  # lyrics text in display
		self.oldTiStampMsec90 = -1
		self.lyricsLineShow = False
		self.lyricsLineShowBig = False
		self["lyricsLine"].hide()
		self["lyricsLineBig"].hide()
		self["actPlayNumber"] = Label("0 / 0")
		self["txtPlayLen"] = Label(_("total:"))
		self["playLen"] = Label("00:00:00")
		self["txtPlayLenRem"] = Label(_("remaining:"))
		self["playLenRem"] = Label("00:00:00")
		self.videoScreenActive = False
		self.videoLyricsScreenActive = False
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap={
				iPlayableService.evUpdatedInfo: self.__evUpdatedInfo,
				iPlayableService.evUser + 10: self.__evAudioDecodeError,
				iPlayableService.evUser + 11: self.__evVideoDecodeError,
				iPlayableService.evUser + 12: self.__evPluginError,
			})
		yampDirAbs = abspath(yampDir)
		if yampDirAbs not in sys_path:
			sys_path.append(yampDirAbs)
		textfile = join(yampDir, 'NoTitlecase.txt')
		if exists(textfile):
			with open(textfile, 'r') as f:
				yampTitlecaseNochange = f.read().splitlines()
			for idx in reversed(range(len(yampTitlecaseNochange))):
				if yampTitlecaseNochange[idx].startswith('#') or yampTitlecaseNochange[idx].startswith('\t'):
					yampTitlecaseNochange.pop(idx)
		else:
			LOG('YampScreenV33: __init__: File not found: "%s"' % textfile, 'err')

	def setTVOptions(self):
		showTvConfig = config.plugins.yampmusicplayer.yampShowTV.value
		self.TvOff = showTvConfig == 'no'
		self.TvAudioStart = showTvConfig == 'AudioStart'
		self.TvStart = showTvConfig == 'AudioPicStart'
		self.TvAudio = showTvConfig == 'Audio'
		self.Tv = showTvConfig == 'AudioPic'

	def key5Actions(self):
		try:
			self.playlist.moveToIndex(self.playlist.getCurrentIndex())
			self.updatePlaylistInfo()
			self.calcRemainPlaylist()
		except Exception:
			pass

	def checkSkinFiles(self, skin):
		oldCustom = False
		failed = ''
		flist = []
		flists = []
		path = ""
		try:
			path = join(yampDir, "skins", skin)
		except Exception as e:
			LOG('YampScreen: checkSkinFiles: EXCEPT path1: %s' % (str(e)), 'err')
		try:
			versionFile = path + '/V' + VERSIONNUMBER + '.ver'
			oldCustom = not isfile(versionFile) and 'custom' in skin.lower()
		except Exception as e:
			LOG('YampScreen: checkSkinFiles: EXCEPT checkversion: %s' % (str(e)), 'err')
		try:
			for root, dirs, files in walk(path):
				flists.append(files)
		except OSError as e:
			LOG('YampScreen: checkSkinFiles: EXCEPT path: %s' % (str(e)), 'err')
		try:
			flist = flists[0]  # root
		except Exception:
			pass
		try:
			flist = flist + flists[1]  # subdir 1 filelist
		except Exception:
			pass
		try:
			flist = flist + flists[2]  # subdir 2 prov
		except Exception:
			pass
		try:
			for req in ('Yamp.xml', 'YampConfig.xml', 'YampDatabase.xml', 'YampLCD.xml', 'YampLyrics.xml', 'YampSelectPath.xml', 'YampVideoLyrics.xml', 'YampVideoTitle.xml', 'YampLcdRunning.xml'):  #check Xml
				if req not in flist:
					failed = path + '/' + req
					break
		except Exception as e:
			LOG('YampScreen: checkSkinFiles: EXCEPT skinReqXml: %s' % (str(e)), 'err')

		try:
			if not failed:
				for req in ('yamp.png', 'fanarttv.png', 'Karaoke.png', 'Karaoke_Big.png', 'musicbrainz.png', 'no_coverArt.png', 'no_videocoverArt.png', 'repeat_off.png', 'repeat_on.png', 'saver_off.png', 'saver_on.png', 'shuffle_off.png', 'shuffle_on.png'):  # check Png
					if req not in flist:
						failed = path + '/' + req
						break
		except Exception as e:
			LOG('YampScreen: checkSkinFiles: EXCEPT skinReqPng: %s' % (str(e)), 'err')
		try:
			if not failed:
				for req in ('prov_no.png', 'prov_mp3.png', 'prov_flac.png', 'prov_file.png', 'prov_chartlyrics.png', 'prov_genius.png', 'prov_azlyrics.png', 'prov_mp4.png', 'prov_m4a.png', 'prov_ogg.png', 'prov_lyricsdir.png', 'prov_fileany.png', 'prov_filealbum.png', 'prov_google.png', 'prov_filetitle.png'):  # check Png Provider
					if req not in flist:
						failed = path + '/prov/' + req
						break
		except Exception as e:
			LOG('YampScreen: checkSkinFiles: EXCEPT skinReqPngProv: %s' % (str(e)), 'err')
		try:
			if not failed:
				for req in ('music_m4a.png', 'music_mp2.png', 'music_mp3.png', 'music_wav.png', 'music_wma.png', 'music_ogg.png', 'music_flac.png', 'movie_ts.png', 'movie_avi.png', 'movie_divx.png', 'movie_m4v.png', 'movie_mpg.png', 'movie_mpeg.png', 'movie_mkv.png', 'movie_mp4.png', 'movie_mov.png', 'movie_m2ts.png', 'movie_flv.png', 'movie_mwv.png', 'playl_m3u.png', 'playl_e2pls.png', 'picture_jpg.png', 'picture_jpeg.png', 'picture_png.png', 'picture_bmp.png', 'dir.png'):  # check Png Filelist
					if req not in flist:
						failed = path + '/filelist/' + req
						break
		except Exception as e:
			LOG('YampScreen: checkSkinFiles: EXCEPT skinReqPngFile: %s' % (str(e)), 'err')
		try:
			if not failed and (skin == 'default' or skin == 'defaultTV' or skin == 'custom'):
#				LOG('YampScreen: checkSkinFiles: check  skinReqPngHD', 'err')
				for req in ('Bg_181517_trans.png', 'black.png', 'smallshadowline.png',):
					if req not in flist:
						failed = path + '/' + req
						break
		except Exception as e:
			LOG('YampScreen: checkSkinFiles: EXCEPT skinReqPngHD: %s' % (str(e)), 'err')
		try:
			if not failed and (skin == 'fhd' or skin == 'fhdCoffee' or skin == 'fhdCustom'):
#				LOG('YampScreen: checkSkinFiles: check  skinReqPngFHD', 'err')
				for req in ('Bg_181517_trans.png', 'black.png', 'smallshadowline_1920.png'):
					if req not in flist:
						failed = path + '/' + req
						break
		except Exception as e:
			LOG('YampScreen: checkSkinFiles: EXCEPT skinReqPngFHD: %s' % (str(e)), 'err')
		return failed, oldCustom

	def checkCustomSkins(self):
		configSkin, newSkin, missing, oldCustom = "", "", "", ""
		try:
			configSkin = newSkin = config.plugins.yampmusicplayer.yampSkin.value
			missing, oldCustom = self.checkSkinFiles(configSkin)
			if missing:
				if configSkin == 'custom':
					newSkin = 'default'
				elif configSkin == 'fhdCustom':
					newSkin = 'fhd'
			config.plugins.yampmusicplayer.yampSkin.value = newSkin
			config.plugins.yampmusicplayer.yampSkin.save()
			return configSkin, newSkin, missing, oldCustom
		except Exception as e:
			LOG('YampScreen: checkCustomSkins: EXCEPT: %s' % (str(e)), 'err')
		return configSkin, newSkin, missing, oldCustom

	def getSkinName(self, skin):
		try:
			if skin == 'default':
				return skinTexts[0]
			elif skin == 'defaultTV':
				return skinTexts[1]
			elif skin == 'custom':
				return skinTexts[2]
			elif skin == 'fhd':
				return skinTexts[3]
			elif skin == 'fhdCoffee':
				return skinTexts[4]
			elif skin == 'fhdCustom':
				return skinTexts[4]
		except Exception as e:
			LOG('YampScreen: getSkinName: EXCEPT: %s' % (str(e)), 'err')

	def lockShow(self):
		pass

	def unlockShow(self):
		pass

	def findPigElement(self):
		self.pigElement = None
		skin = config.plugins.yampmusicplayer.yampSkin.value
		if skin == 'default' or skin == 'defaultDreamOS':
			return
		try:
			for element in self.renderer:
				if "eVideoWidget" in str(vars(element)):
					self.pigElement = element
		except Exception as e:
			LOG('YampScreen: findPigElement: EXCEPT: %s' % (str(e)), 'err')

	def showHideVideoPreview(self, show):
		if self.pigElement is not None:
			self.videoPreviewOn = show
			if show:
				self.pigElement.show()
			else:
				self.pigElement.hide()

# Start and end methods, handle some events from e2
	def layoutFinished(self):
		try:
			self.findPigElement()
			self.showHideVideoPreview(False)  # layout finished
		except Exception as e:
			LOG('YampScreen: layoutFinished: showHideVideoPreview: EXCEPT: %s' % (str(e)), 'err')
		dbupgradev33 = dbUpgradeV33()
		if dbupgradev33 and dbupgradev33 > 0:
			clearDatabase()  # empty or problem on upgrade -> delete and create new
		self.dbUpgradeInfo331 = dbUpgradeV331()
		self.dbUpgradeInfo332 = dbUpgradeV332()
		self["fanartdownload"].hide()
		self["downloadBackground"].hide()
		self.currDblist = DblistStackEntry()
		self.buildDbMenuList(MENULIST, menutitle=_("M u s i c  D a t a b a s e"))
		if config.plugins.yampmusicplayer.startWithDatabase.value:
			self.setLeftContent("dblist")
		else:
			self.setLeftContent("filelist")
		self.setRepeatButton()
		self.setShuffleButton()
		self.setHelpTexts()
		self.setColorButtons()
		self["songInfoBg"].setBoolean(False)
		self["lyricsLineBackground"].hide()
		self["lyricsLineBackgroundBig"].hide()
		if config.plugins.yampmusicplayer.displaySkinname.value:
			self["actskin"].show()
		else:
			self["actskin"].hide()
		if config.plugins.yampmusicplayer.showPlayListLen.value:
			self["playLen"].show()
			self["txtPlayLen"].show()
			self["playLenRem"].show()
			self["txtPlayLenRem"].show()
		else:
			self["playLen"].hide()
			self["txtPlayLen"].hide()
			self["playLenRem"].hide()
			self["txtPlayLenRem"].hide()
		try:
			self.updatePlaylistInfo()
		except Exception as e:
			LOG('YampScreen: layoutFinished: updatePlaylistInfo: EXCEPT: %s' % (str(e)), 'err')
		try:
			self.createLcdCoverImage(join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, 'no_coverArt.png'))
		except Exception as e:
			LOG('YampScreen: layoutFinished: createLcdCoverImage: EXCEPT: %s' % (str(e)), 'err')
		self.startupTimer.start(1000, True)
		try:
			self.infoBarNaReplace = INFOBARTEXTLIST[int(config.plugins.yampmusicplayer.displayUnknown.value)]
		except Exception as e:
			LOG('YampScreen: layoutFinished: infoBarNaReplace: EXCEPT: %s' % (str(e)), 'err')
		self.searchFanartConfig = config.plugins.yampmusicplayer.searchFanart.value
		LOG('YampScreen: layoutFinished: before read file: fanarttvPersonalApikey: %s' % (self.fanarttvPersonalApikey), 'all')
		LOG('YampScreen: layoutFinished: before read file: config fanarttvPersonal: %s' % (config.plugins.yampmusicplayer.fanarttvPersonal.value), 'all')
		if isfile(FANARTTVAPPAPIFILE):
			with open(FANARTTVAPPAPIFILE, "r") as f:
				keyname = f.read().strip()
			if len(keyname) > 0:
				self.fanarttvAppApikey = keyname
			LOG('YampScreen: layoutFinished: read from file: fanarttvAppApikey: %s' % (self.fanarttvAppApikey), 'all')
		if isfile(FANARTTVPERSAPIFILE):
			with open(FANARTTVPERSAPIFILE, "r") as f:
				keyname = f.read().strip()
			LOG('YampScreen: layoutFinished: read personal API from file: len: %d keyname: *%s*' % (len(keyname), keyname), 'all')
			if len(keyname) > 30:
				self.fanarttvPersonalApikey = keyname
				config.plugins.yampmusicplayer.fanarttvPersonal.value = self.fanarttvPersonalApikey
				LOG('YampScreen: layoutFinished: personal api key written to config from file: %s' % (self.fanarttvPersonalApikey), 'all')
		self.fanarttvPersonalApikey = config.plugins.yampmusicplayer.fanarttvPersonal.value
		if self.fanarttvPersonalApikey.strip().startswith('1234567890abcdef'):
			self.fanarttvPersonalApikey = ''
		if 'abcdef7890' in self.fanarttvPersonalApikey.strip():
			self.fanarttvPersonalApikey = ''
		LOG('YampScreen: layoutFinished: after read file: fanarttvPersonalApikey: %s' % (self.fanarttvPersonalApikey), 'all')
		LOG('YampScreen: layoutFinished: after read file: config fanarttvPersonal: %s' % (config.plugins.yampmusicplayer.fanarttvPersonal.value), 'all')
		try:
			self.filelistint.selectionEnabled(1)
		except Exception as e:
			LOG('YampScreen: layoutFinished: filelistint: EXCEPT: %s' % (str(e)), 'err')
		try:
			self.findClockElement()
		except Exception as e:
			LOG('YampScreen: layoutfinished: call findClockElement: EXCEPT: %s' % (str(e)), 'err')
		try:
			self.showHideClock()
		except Exception as e:
			LOG('YampScreen: layoutfinished: call showHideClock: EXCEPT: %s' % (str(e)), 'err')
		txtInfo, txtSaver, dummy = readRcButtonTexts()
		self["textInfo"].setText(txtInfo)
		self["textSaver"].setText(txtSaver)
		if config.plugins.yampmusicplayer.searchFanart.value == 'always':
			config.plugins.yampmusicplayer.searchFanart.value = '60'
			config.plugins.yampmusicplayer.searchFanart.save()
		self.searchFanartConfig = config.plugins.yampmusicplayer.searchFanart.value
		self.showHideSlideName(False)
		self.checkCoverScroll()

	def findClockElement(self):
		try:
			for element in self.renderer:
				if "Converter.ClockToText." in str(vars(element)):
					if checkAttributes(element, "text", "clockHide"):
						self.elementClock = element
					elif checkAttributes(element, "text", "dateHide"):
						self.elementDate = element
		except Exception as e:
			LOG('Yampscreen: findClockElement: EXCEPT: %s' % (str(e)), 'err')

	def showHideClock(self, Modus="Standard"):  # "SS", "Video"
		try:
			configSS = config.plugins.yampmusicplayer.showClockSS.value
			configVid = config.plugins.yampmusicplayer.showClockVideo.value
			if self.elementClock is not None:
				if Modus == "Standard" and not self.screenSaverActive:
					self.elementClock.instance.hide()
					self["clockBackground"].hide()
				elif Modus == "SS":
					if configSS == "no" or configSS == "date" or configSS == "datebg":
						self.elementClock.instance.hide()
						self["clockBackground"].hide()
					elif configSS == "clock" or configSS == "clockdate":
						self.elementClock.instance.show()
						self["clockBackground"].hide()
					elif configSS == "clockbg" or configSS == "clockdatebg":
						self.elementClock.instance.show()
						self["clockBackground"].show()
				elif Modus == "Video":
					if configVid == "no" or configVid == "date" or configVid == "datebg":
						self.elementClock.instance.hide()
						self["clockBackground"].hide()
					elif configVid == "clock" or configVid == "clockdate":
						self.elementClock.instance.show()
						self["clockBackground"].hide()
					elif configVid == "clockbg" or configVid == "clockdatebg":
						self.elementClock.instance.show()
						self["clockBackground"].show()
			if self.elementDate is not None:
				if Modus == "Standard" and not self.screenSaverActive:
					self.elementDate.instance.hide()
					self["dateBackground"].hide()
				elif Modus == "SS":
					if configSS == "no" or configSS == "clock" or configSS == "clockbg":
						self.elementDate.instance.hide()
						self["dateBackground"].hide()
					elif configSS == "date" or configSS == "clockdate":
						self.elementDate.instance.show()
						self["dateBackground"].hide()
					elif configSS == "datebg" or configSS == "clockdatebg":
						self.elementDate.instance.show()
						self["dateBackground"].show()
				elif Modus == "Video":
					if configVid == "no" or configVid == "clock" or configVid == "clockbg":
						self.elementDate.instance.hide()
						self["dateBackground"].hide()
					elif configVid == "date" or configVid == "clockdate":
						self.elementDate.instance.show()
						self["dateBackground"].hide()
					elif configVid == "datebg" or configVid == "clockdatebg":
						self.elementDate.instance.show()
						self["dateBackground"].show()
						self.elementDate.instance.hide()
		except Exception as e:
			LOG('Yampscreen: showHideClock: EXCEPT: %s' % (str(e)), 'err')

	def redActions(self):
		if self.redLongActive:
			self.redLongActive = False
		else:
			if not self.screenSaverActive and not self.isVideoFullScreen:
				if self.currList == "playlist":
					self.resetScreenSaverTimer()
					self.playingMoved = self.playlist.getSelectionIndex() == self.playlist.getCurrentIndex()
					self.moveEntryLenLists(self.playlist.getSelectionIndex(), -1, config.plugins.yampmusicplayer.wrapMovePlaylist.value)
					self.playlist.moveEntryUp(self.playlist.getSelectionIndex(), config.plugins.yampmusicplayer.wrapMovePlaylist.value)
					self.playlist.updateList()
					self.updatePlaylistInfo()
					self.updateNextSong()
				else:
					if self.currList == "filelist":
						self.currList = "dblist"
						if self.databaseChanged:
							self.updateDbMenuList()
							self.databaseChanged = False
					else:  # dblist
						self.currList = "filelist"
					self.setLeftContent(self.currList)
					self.setColorButtons()
					self.updateLCDInfo()

	def greenActions(self):
		if self.greenLongActive:
			self.greenLongActive = False
		else:
			if not self.screenSaverActive and not self.isVideoFullScreen:
				if self.currList == "playlist":  # playlist
					self.resetScreenSaverTimer()
					self.playingMoved = self.playlist.getSelectionIndex() == self.playlist.getCurrentIndex()
					self.moveEntryLenLists(self.playlist.getSelectionIndex(), 1, config.plugins.yampmusicplayer.wrapMovePlaylist.value)
					self.playlist.moveEntryDown(self.playlist.getSelectionIndex(), config.plugins.yampmusicplayer.wrapMovePlaylist.value)
				elif self.currList == "filelist":
					if self.filelist.canDescent():
						self.addDir(self.filelist.getSelection()[0], recursive=False)
					else:
						self.addFile()
					self.playlist.moveToIndex(len(self.playlist) - 1)
					self.movedown()
				else:  # dblist
					navx = self.dblist.getSelection().nav
					if not navx:
						mode = self.dblist.mode
						if mode >= TITLELIST:
							sref = ServiceReference(self.dblist.getSelection().ref)
							self.addService(sref.ref, self.dblist.getSelection().title, self.dblist.getSelection().artist)
							self.playlist.updateList()
							self.updateNextSong()
						elif mode in (PLAYLISTLIST, SEARCHPLAYLISTLIST):
							self.addExtPlaylist(self.dblist.getSelection().filename)
						elif mode in (ARTISTLIST, SEARCHARTISTLIST):
							self.addCategory(query=self.dblist.getSelection().artistID)
						elif mode in (ALBUMLIST, ARTISTALBUMLIST, GENREALBUMLIST, SEARCHALBUMLIST):
							self.addCategory(query=self.dblist.getSelection().albumID)
						elif mode in (GENRELIST, SEARCHGENRELIST):
							self.addCategory(query=self.dblist.getSelection().genreID)
						self.playlist.moveToIndex(len(self.playlist) - 1)
						self.movedown()
				self.recalcLenListsComplete()
				self.playlist.updateList()
				self.updatePlaylistInfo()
				self.updateNextSong()

	def yellowActions(self):
		if self.yellowLongActive:
			self.yellowLongActive = False
		else:
			if not self.screenSaverActive and not self.isVideoFullScreen:
				self.resetScreenSaverTimer()
				if self.currList == "filelist":
					if self.filelist.canDescent():
						self.showDatabaseScreen()
					else:
						self.addFileToDb()
					self.movedown()
					self.databaseChanged = True
				elif self.currList == "dblist":
					numChoice = self.dblist.getSelectionIndex()
					choice = self.dblist.getSelection()
					if self.dblist.mode in (ARTISTLIST, SEARCHARTISTLIST):
						self.pushDblistStack(numChoice)
						self.buildDbMenuList(mode=ARTISTALBUMLIST, query=choice.artistID, menutitle=choice.artist)
					elif self.dblist.mode in (GENRELIST, SEARCHGENRELIST):
						self.pushDblistStack(numChoice)
						self.buildDbMenuList(mode=GENREALBUMLIST, query=choice.genreID, menutitle=choice.genre)
					elif self.dblist.mode in (TITLELIST, ARTISTTITLELIST, GENRETITLELIST, DATETITLELIST, SEARCHTITLELIST, SEARCHFILELIST, SEARCHARTISTTITLELIST):
						self.pushDblistStack(numChoice)
						self.buildDbMenuList(mode=ALBUMTITLELIST, query=choice.albumID, menutitle=choice.album)
					elif self.dblist.mode in (ALBUMTITLELIST, SEARCHALBUMTITLELIST):
						self.pushDblistStack(numChoice)
						self.buildDbMenuList(mode=ARTISTTITLELIST, query=choice.artistID, menutitle=choice.artist)
					self.setLeftContentTitle()
					self.setColorButtons()
				else:
					src = self["coverArt"].getFileName()
					if src:
						ext = splitext(basename(src))[1]
						dest = splitext(self.playlist.getServiceRefList()[self.playlist.getCurrentIndex()].getPath())[0] + ext
						try:
							open(dest, 'wb').write(open(src, 'rb').read())
							self.session.open(MessageBox, _("Cover saved"), type=MessageBox.TYPE_INFO, timeout=2)
						except Exception as e:
							self.session.open(MessageBox, _("Saving cover failed"), type=MessageBox.TYPE_INFO, timeout=30)
							LOG('YampScreen: yellowActions: save Cover: EXCEPT: %s' % (str(e)), 'err')

	def blueActions(self):
		if self.blueLongActive:
			self.blueLongActive = False
		else:
			if not self.screenSaverActive and not self.isVideoFullScreen and self.currList == "playlist":
				self.deleteEntry()
				self.updatePlaylistInfo()
			self.resetScreenSaverTimer()

	def redLongActions(self):
		self.redLongActive = True
		if self.screenSaverActive and not self.isVideoFullScreen:
			if self["screenSaver"].getLen() < 2:
				self.session.open(MessageBox, _("Slide is the last slide and can not be removed"), type=MessageBox.TYPE_INFO, timeout=5)
				return
			currSlide = ""
			try:
				currSlide = self["screenSaver"].getCurrentSlide()
				LOG('YampScreen: redLongActions: getCurrentSlide: %s' % (currSlide), 'all')
			except Exception as e:
				LOG('YampScreen: redLongActions: getCurrentSlide: EXCEPT: %s' % (str(e)), 'err')
			try:
				if len(currSlide) > 0 and currSlide != (yampDir + 'saverblank/black.png'):
					if config.plugins.yampmusicplayer.screenSaverMode.value == "artwork":
						slidepath = config.plugins.yampmusicplayer.screenSaverArtworkPath.value
					else:
						slidepath = self.slidePath
					message = _('this picture will be blacklisted to %sblacklist.txt\nand will not be shown any more!\n\ndo you really want to blacklist this picture?') % (slidepath)
					try:
						self.par1 = slidepath
						self.par2 = currSlide
						self.session.openWithCallback(self.blackListConfirmed, MessageBox, message)
					except Exception as e:
						LOG('YampScreen: redLongActions: message: EXCEPT: %s' % (str(e)), 'err')
			except Exception as e:
				LOG('YampScreen: redLongActions: getCurrentSlide: EXCEPT: %s' % (str(e)), 'err')
		if self.currList == "playlist" and not self.isVideoFullScreen:
			self.resetScreenSaverTimer()
			self.moveEntryLenLists(self.playlist.getSelectionIndex(), (-1) * config.plugins.yampmusicplayer.playlistMoveMulti.value, config.plugins.yampmusicplayer.wrapMovePlaylist.value)
			self.playlist.moveEntryUpMul(self.playlist.getSelectionIndex(), config.plugins.yampmusicplayer.playlistMoveMulti.value, config.plugins.yampmusicplayer.wrapMovePlaylist.value)
			self.playlist.updateList()
			self.updatePlaylistInfo()
			self.updateNextSong()

	def greenLongActions(self):
		self.greenLongActive = True
		if self.screenSaverActive or self.isVideoFullScreen:
			return
		if self.currList == "playlist":
			self.resetScreenSaverTimer()
			self.moveEntryLenLists(self.playlist.getSelectionIndex(), config.plugins.yampmusicplayer.playlistMoveMulti.value, config.plugins.yampmusicplayer.wrapMovePlaylist.value)
			self.playlist.moveEntryDownMul(self.playlist.getSelectionIndex(), config.plugins.yampmusicplayer.playlistMoveMulti.value, config.plugins.yampmusicplayer.wrapMovePlaylist.value)
		elif self.currList == "filelist":
			if self.filelist.canDescent():
				self.addDir(self.filelist.getSelection()[0], recursive=True)
			else:
				self.addAllFiles()
			self.playlist.moveToIndex(len(self.playlist) - 1)
			self.recalcLenListsComplete()
		elif self.currList == "dblist":
			for x in self.dblist.getDatabaseList():
				if not x[0].nav and self.dblist.mode >= TITLELIST:
					sref = ServiceReference(x[0].ref)
					self.addService(sref.ref, x[0].title, x[0].artist)
			self.playlist.moveToIndex(len(self.playlist) - 1)
			self.recalcLenListsComplete()
		self.playlist.updateList()
		self.updatePlaylistInfo()
		self.updateNextSong()

	def yellowLongActions(self):
		self.yellowLongActive = True
		if not self.screenSaverActive and not self.isVideoFullScreen:
			if self.currList == "filelist":
				if self.filelist.canDescent():
					self.showDatabaseScreen(recursive=True)
				else:
					self.addFileToDb()
				self.movedown()
				self.databaseChanged = True
			elif self.currList == "dblist":
				if self.dblist.mode in (TITLELIST, ALBUMTITLELIST, GENRETITLELIST, SEARCHTITLELIST, SEARCHFILELIST, SEARCHALBUMTITLELIST):
					numChoice = self.dblist.getSelectionIndex()
					self.pushDblistStack(numChoice)
					choice = self.dblist.getSelection()
					self.buildDbMenuList(mode=ARTISTTITLELIST, query=choice.artistID, menutitle=choice.artist)
				self.setLeftContentTitle()
				self.setColorButtons()
			else:
				src = self["coverArt"].getFileName()
				if src:
					ext = splitext(basename(src))[1]
					dest = join(dirname(self.playlist.getServiceRefList()[self.playlist.getCurrentIndex()].getPath()), "albumcover") + ext
					try:
						open(dest, 'wb').write(open(src, 'rb').read())
						self.session.open(MessageBox, _("Albumcover saved"), type=MessageBox.TYPE_INFO, timeout=5)
					except Exception:
						self.session.open(MessageBox, _("Saving albumcover failed"), type=MessageBox.TYPE_INFO, timeout=30)

	def blueLongActions(self):
		self.blueLongActive = True
		self.resetScreenSaverTimer()
		if not self.screenSaverActive and not self.isVideoFullScreen and self.currList == "playlist":
			self.hideScreenSaver()
			self.session.openWithCallback(self.clearPlaylistConfirmed, MessageBox, _("Do you really want to delete the current playlist?"), default=False, timeout=10)

	def infoLongActions(self):
		self.infoLongActive = True
		try:
			self.session.openWithCallback(self.helpScreenCB, YampHelpScreenV33)
		except Exception as e:
			LOG('YampScreen: infoLongActions: openHelpScreen: EXCEPT: %s' % (str(e)), 'err')

	def keyPercentJumpFwActions(self):
		if self.jumpFwLongActive:
			self.jumpFwLongActive = False
		else:
			self.seekOwn(21)

	def keyPercentJumpBwActions(self):
		if self.jumpBwLongActive:
			self.jumpBwLongActive = False
		else:
			self.seekOwn(22)

	def keyPercentJumpFwLActions(self):
		self.jumpFwLongActive = True
		self.seekOwn(23)

	def keyPercentJumpBwLActions(self):
		self.jumpBwLongActive = True
		self.seekOwn(24)

	def helpScreenCB(self):
		config.plugins.yampmusicplayer.lastVersionDate.value = VERSIONDATE
		config.plugins.yampmusicplayer.lastVersionDate.save()

	def setScreensaverBg(self):
		try:
#			if config.plugins.yampmusicplayer.screenSaverBg.value:
			if self.ssBackground:
				self["screenSaverBackground"].setZPosition(4)  # 4  5
				self["screenSaver"].setZPosition(5)  # 5  9
#				self["songInfoBg"].setBoolean(True)
			else:
				self["screenSaverBackground"].setZPosition(9)  # 9  1
				self["screenSaver"].setZPosition(10)  # 10 10
		except Exception as e:
			LOG('YampScreen: setScreensaverBg: setZPosition : EXCEPT : %s' % (str(e)), 'err')
		try:
			self["screenSaver"].refreshPic()
		except Exception as e:
			LOG('YampScreen: setScreensaverBg: refreshPic : EXCEPT : %s' % (str(e)), 'err')

	def memoryLog(self):
		MEMCONFFILE = 'yamp_memlog.cfg'
		try:
			with open("/proc/meminfo", "r") as meminfo:
				memlines = meminfo.read().split('\n')
			configfile = None
			conffilepath = self.logpath + MEMCONFFILE
			if not access(conffilepath, R_OK):
				LOG('YampScreen: memoryLog: config file %s does not exist, debugging all meminfo, creating config file' % (conffilepath), 'err')
				configlist = []
				for x in range(len(memlines) - 1):
					configlist.append(str(x))
				try:
					with open(conffilepath, "w") as configfile:
						configfile.write(','.join(configlist))
				except Exception as e:
					LOG('YampScreen: memoryLog: could not create config file: %s' % (conffilepath), 'all')
					LOG('YampScreen: memoryLog: create config file: EXCEPT: %s' % (str(e)), 'err')
			else:
				with open(conffilepath, "r") as configfile:
					configlist = configfile.read().split(',')
			logfile = open(self.memlogfile, 'a')
			logfile.write(datetime.now().strftime("%Y.%m.%d-%H:%M:%S.%f") + '\n')
			line = "0"
			for line in configlist:
				logfile.write(line + ':\t' + memlines[int(line)] + '\n')
			logfile.write('\n')
			logfile.close()
			del logfile, meminfo, memlines, configfile, configlist, line
		except Exception as e:
			LOG('YampScreen: memoryLog: EXCEPT: %s' % (str(e)), 'err')

	def createSummary(self):
		confLcd = config.plugins.yampmusicplayer.yampLcdMode.value
		if confLcd == 'off':
			return
		elif confLcd == 'running':
			return YampLCDRunningScreenV33
		else:
			return YampLCDScreenV33

	def exit(self):
		self.exitYamp = True
		if self.screenSaverActive and not self.isVideoFullScreen:
			self.resetScreenSaverTimer()
			return
		if config.plugins.yampmusicplayer.newExitKey.value:
			# new exit key: no immediate exit of yamp in dblist / filelist
			if self.currList == 'dblist' and self.dblist.mode > MENULIST:
				self.exitYamp = False
			if self.currList == 'filelist':
				if self.filelist.getSelection()[1]:  # is directory
					try:
						strConfigPath = config.plugins.yampmusicplayer.musicFilePath.value
						strPath = self.filelist.getSelection()[0] or ""
						if self.filelist.getSelectionIndex() == 0 and strPath == strConfigPath:
							self.exitYamp = False
						else:
							Pos = strPath.rfind('/', 0, len(strPath) - 1)
							strPath = strPath[:Pos + 1]
							if len(strPath) > len(strConfigPath):
								self.exitYamp = False
					except Exception as e:
						LOG('YampScreen: exit(): filelist is directory: EXCEPT : %s' % (str(e)), 'err')
				else:
					self.exitYamp = False

			if not self.exitYamp:
				try:
					self.skipToListbegin()
				except Exception as e:
					LOG('YampScreen: exit(): skipToListbegin: EXCEPT: %s' % (str(e)), 'err')
				try:
					self.ok()
				except Exception as e:
					LOG('YampScreen: exit(): ok: EXCEPT: %s' % (str(e)), 'err')
				self.setLeftContentTitle()
				return
		self.hideScreenSaver()
		if config.plugins.yampmusicplayer.searchFanart.value == 'always':
			config.plugins.yampmusicplayer.searchFanart.value = self.previousFanartDLconfig
		config.plugins.yampmusicplayer.searchFanart.save()
		if config.plugins.yampmusicplayer.yampConfirmExit.value:
			self.session.openWithCallback(self.exitConfirmed, MessageBox, _("Do you really want to exit?"))
		else:
			self.exitConfirmed(True)

	def exitConfirmed(self, answer):
		if not answer:  # no exit
			self.resetScreenSaverTimer()
		else:
			try:  # to prevent crash on immediate exit before Yamp was fully loaded
				self.YampParserE2pls.clear()
				if config.plugins.yampmusicplayer.savePlaylistOnExit.value:
					for x in self.playlist.shadowList:
						self.YampParserE2pls.addService(ServiceReference(x[0]))
				self.YampParserE2pls.save(resolveFilename(SCOPE_CONFIG, "yampsl.e2pls"))
				self.YampParserE2pls.clear()
				if config.plugins.yampmusicplayer.savePlaylistOnExit.value:
					config.plugins.yampmusicplayer.lastPlaylistIndex.value = self.playlist.getCurrentIndex()
					try:
						config.plugins.yampmusicplayer.lastPlaylistIndex.save()
					except Exception:
						pass
					for x in self.playlist.list:
						self.YampParserE2pls.addService(ServiceReference(x[0]))
				self.YampParserE2pls.save(resolveFilename(SCOPE_CONFIG, "yamp.e2pls"))
			except Exception:
				pass
			if config.plugins.yampmusicplayer.saveLastFilebrowserPath.value:
				try:
					config.plugins.yampmusicplayer.musicFilePath.value = self["filelist"].getCurrentDirectory()
				except Exception:
					config.plugins.yampmusicplayer.musicFilePath.value = ""
				if config.plugins.yampmusicplayer.musicFilePath.value:
					config.plugins.yampmusicplayer.musicFilePath.save()
			config.plugins.yampmusicplayer.shuffle.value = self.playlist.isShuffeled
			config.plugins.yampmusicplayer.shuffle.save()
			config.plugins.yampmusicplayer.repeatPlaylistAtEnd.value = self.repeat
			config.plugins.yampmusicplayer.repeatPlaylistAtEnd.save()
			if self.leftContent == "dblist":
				config.plugins.yampmusicplayer.startWithDatabase.value = True
			else:
				config.plugins.yampmusicplayer.startWithDatabase.value = False
			config.plugins.yampmusicplayer.startWithDatabase.save()
			if len(self["screenSaver"]) > 0:
				config.plugins.yampmusicplayer.lastSlide.value = self["screenSaver"].getCurrentSlide()
			else:
				config.plugins.yampmusicplayer.lastSlide.value = ""
			config.plugins.yampmusicplayer.lastSlide.value = ""  #!!!! Test
			config.plugins.yampmusicplayer.lastSlide.save()
			self.currentIsVideo = False
			configfile.save()
			del self["coverArt"].picload
			del self["screenSaver"].picload
			self.close(self.session, self.myOldService)

	def cleanup(self):
		del self.screenSaverTimer
		del self.coverScrollTimer
		del self.nextSlideTimer
		del self.screenSaverManTimer
		del self.eofbugTimer
		del self.gapTimer
		del self.startupTimer
		del self.blankVideoTimer
		del self.fanartDlTimer
		del self.fanartDisplayTimer
		del self.karaokeTimer
		del self.karaokeMaxtimeTimer
		for file in listdir('/tmp/'):
			if file.startswith('.coverart') or file == '.cover' or file == '.id3coverart':
				remove(join('/tmp/', file))

	def makeNextSongDisplay(self):
		selection = int(config.plugins.yampmusicplayer.displayNext.value)
		if selection == 0:
			self.nextSongDisplay = self.nextsongtitle + "  -  " + self.nextsongartist + "  -  " + self.nextsongalbum
		elif selection == 1:
			self.nextSongDisplay = self.nextsongtitle + "  -  " + self.nextsongalbum + "  -  " + self.nextsongartist
		elif selection == 2:
			self.nextSongDisplay = self.nextsongartist + "  -  " + self.nextsongtitle + "  -  " + self.nextsongalbum
		elif selection == 3:
			self.nextSongDisplay = self.nextsongartist + "  -  " + self.nextsongalbum + "  -  " + self.nextsongtitle
		elif selection == 4:
			self.nextSongDisplay = self.nextsongtitle + "  -  " + self.nextsongartist
		elif selection == 5:
			self.nextSongDisplay = self.nextsongtitle + "  -  " + self.nextsongalbum
		elif selection == 6:
			self.nextSongDisplay = self.nextsongartist + "  -  " + self.nextsongtitle
		elif selection == 7:
			self.nextSongDisplay = self.nextsongartist + "  -  " + self.nextsongalbum
		elif selection == 8:
			self.nextSongDisplay = self.nextsongtitle

	def updateNextSong(self):
#		LOG('updateNextSong: Start', 'spe3')
		if self.memlog:
			self.memoryLog()
		try:
			if len(self.playlist) == 0:
				self.nextsongtitle = self.nextsongalbum = self.nextsongartist = ''
			elif self.playlist.getCurrentIndex() < len(self.playlist) - 1:
				path = self.playlist.getServiceRefList()[self.playlist.getCurrentIndex() + 1].getPath()
				self.nextsongtitle, self.nextsongalbum, self.nextsonggenre, self.nextsongartist, albumartist, self.nextsongdate, self.nextsonglength, self.nextsongtracknr, strBitrate = readID3Infos(path)
			elif self.repeat:
				path = self.playlist.getServiceRefList()[0].getPath()
				self.nextsongtitle, self.nextsongalbum, self.nextsonggenre, self.nextsongartist, albumartist, self.nextsongdate, self.nextsonglength, self.nextsongtracknr, strBitrate = readID3Infos(path)
			else:
				self.nextsongtitle = self.nextsongalbum = self.nextsongartist = ''
		except Exception as e:
			LOG('YampScreen: updateNextSong: nextsongtitle: EXCEPT : %s' % (str(e)), 'err')
		try:
			self.makeNextSongDisplay()
			self.updateSingleMusicInformation("nextsongtitle", self.nextSongDisplay)
		except Exception as e:
			LOG('YampScreen: updateNextSong: EXCEPT: %s' % (str(e)), 'err')

	def CheckIfNormalSongStarted(self):
		actservice = None
		try:
			actservice = self.session.nav.getCurrentlyPlayingServiceReference()
		except Exception as e:
			LOG('YampScreen: CheckIfNormalSongStarted: EXCEPT: %s' % (str(e)), 'err')
		try:
			if actservice is None:
				return False
		except Exception as e:
			LOG('YampScreen: CheckIfNormalSongStarted: EXCEPT2: %s' % (str(e)), 'err')
		try:
			if actservice == self.myOldService:
				return False
		except Exception as e:
			LOG('YampScreen: CheckIfNormalSongStarted: EXCEPT3: %s' % (str(e)), 'err')
		return True

	def __evUpdatedInfo(self):
		if not self.CheckIfNormalSongStarted():
			return
		actPath = self.playlist.getServiceRefList()[self.playlist.getCurrentIndex()].getPath()
		if self.currPath != actPath:
			# for 'next song'
			self.updateNextSong()
			self.fanartDisplayStop()
			# for 'actual title'
			# __evUpdatedInfo may be called more than once per title, therefore:
			self.currPath = actPath
			# Reading Info-Strings with getInfoString does not work with "Umlauts", so use mutagen methods
			path = self.playlist.getServiceRefList()[self.playlist.getCurrentIndex()].getPath()
			try:
				self.currentIsVideo = self.checkIsVideo(path)
			except Exception as e:
				LOG('YampScreen: __evUpdatedInfo: currentIsVideo: EXCEPT : %s' % (str(e)), 'err')
			self.updateMusicInformation(path)
			# Karaoke
			try:
				self.buildNewLyricsKaraoke()
			except Exception as e:
				LOG('YampScreen: __evUpdatedInfo new Song: buildNewLyrics: EXCEPT' + str(e), 'err')

	def buildNewLyricsKaraoke(self):
		foundPrio = LYRICSS_NO
		bgMode = config.plugins.yampmusicplayer.karaokeBg.value
		self.showBgSmall = (bgMode == 'small' or bgMode == 'both') and self.lyricsLineShow
		self.showBgBig = (bgMode == 'big' or bgMode == 'both') and self.lyricsLineShowBig
		try:
			if self.karaokeTimer.isActive():
				self.karaokeTimer.stop()
			self["lyricsLine"].setText('')
			self["lyricsLineBig"].setText('')
			self.oldLyricsText = ''
			songFilename = self.playlist.getServiceRefList()[self.playlist.getCurrentIndex()].getPath()
		except Exception as e:
			songFilename = ''
			LOG('YampScreen: buildNewLyricsKaraoke: Start: EXCEPT' + str(e), 'err')
		timeDataInLyrics = False
		lyrics = self.lyrics = ''
		if not songFilename:
			return
		# search in files
		lyrics, lyricsFileActive, foundPrio = searchLyricsfromFiles(songFilename, foundPrio)
		if lyrics:
			self.lyrics = lyrics
			# check for time data
			try:
				self.tiStamp, self.tiStampMsec90, self.txtLines, self.minTiStamp = textToList(lyrics)
			except Exception as e:
				LOG('YampScreen: buildNewLyricsKaraoke: textToList: EXCEPT : %s' % (str(e)), 'err')
			if max(self.tiStampMsec90) > 0:
				timeDataInLyrics = True
				self.lyrics = lyrics
			else:
				foundPrio = LYRICSS_NO  # not usable for karaoke
		# search in ID3
		lyrics, pixNumLyrics, foundPrio = getLyricsID3(songFilename, foundPrio)

		if lyrics and not timeDataInLyrics:
			self.lyrics = lyrics
			# check for time data
			try:
				self.tiStamp, self.tiStampMsec90, self.txtLines, self.minTiStamp = textToList(lyrics)
			except Exception as e:
				LOG('YampScreen: buildNewLyricsKaraoke: textToList: EXCEPT : %s' % (str(e)), 'err')
			if max(self.tiStampMsec90) > 0:
				timeDataInLyrics = True
				self.lyrics = lyrics
		# no lyrics found in files or id3
		if not self.lyrics:
			self.oldLyricsText = self.displayLyricsText = _('no lyrics in file or ID3 found (or not activated in configuration)')
			self["lyricsLine"].setText(self.oldLyricsText)
			self["lyricsLineBig"].setText(self.oldLyricsText)
			if self.screenSaverActive:
				self.startKaraokeMaxTimer()
				if self.lyricsLineShow:
					self["lyricsLine"].show()
					if self.showBgSmall:
						self["lyricsLineBackground"].show()
					else:
						self["lyricsLineBackground"].hide()
				if self.lyricsLineShowBig:
					self["lyricsLineBig"].show()
					if self.showBgBig:
						self["lyricsLineBackgroundBig"].show()
					else:
						self["lyricsLineBackgroundBig"].hide()
			return
		try:
			if not timeDataInLyrics:
				# found, but no time data
				if lyricsFileActive:
					self.oldLyricsText = self.displayLyricsText = _('no time data in lyrics file')
				else:
					self.oldLyricsText = self.displayLyricsText = _('no time data in lyrics file (ID3)')
				self["lyricsLine"].setText(self.displayLyricsText)
				self["lyricsLineBig"].setText(self.displayLyricsText)
				if self.screenSaverActive:
					if self.lyricsLineShow:
						self["lyricsLine"].show()
					if self.lyricsLineShowBig:
						self["lyricsLineBig"].show()
					if self.showBgSmall:
						self["lyricsLineBackground"].show()
					if self.showBgBig:
						self["lyricsLineBackgroundBig"].show()
					self.startKaraokeMaxTimer()
				return
		except Exception as e:
			LOG('YampScreen: buildNewLyricsKaraoke: set text no time stamp: EXCEPT: %s' % (str(e)), 'err')
		try:
			if self.screenSaverActive:
				if self.lyricsLineShow:
					self["lyricsLine"].show()
					if self.showBgSmall:
						self["lyricsLineBackground"].show()
					else:
						self["lyricsLineBackground"].hide()
				if self.lyricsLineShowBig:
					self["lyricsLineBig"].show()
					if self.showBgBig:
						self["lyricsLineBackgroundBig"].show()
					else:
						self["lyricsLineBackgroundBig"].hide()
			self.karaokeTimer.start(self.karaokeTime)
		except Exception as e:
			LOG('YampScreen: buildNewLyricsKaraoke: startKaraokeTimer: EXCEPT : %s' % (str(e)), 'err')

	def checkKaraoke(self):
		if self.playerState != STATE_PLAY or (not self.lyricsLineShow and not self.lyricsLineShowBig):
			return
		try:
			length, pos = self.getSeekData()
		except Exception as e:
			length = pos = 0
			LOG('YampScreen: checkKaraoke: songPos: EXCEPT : %s' % (str(e)), 'err')
		try:
			# play position < first text
			if pos < self.minTiStamp + self.lyricsPlayOffsetTime90:
				newText = self.oldLyricsText = self.displayLyricsText = ''
				self["lyricsLine"].setText(newText)
				self["lyricsLineBig"].setText(newText)
				self["lyricsLineBackground"].hide()
				self["lyricsLineBackgroundBig"].hide()
				return
		except Exception as e:
			LOG('YampScreen: checkKaraoke: pos < self.minTiStamp: EXCEPT : %s' % (str(e)), 'err')
		try:
			for index in range(len(self.tiStampMsec90) - 1, -1, -1):
				if pos >= self.tiStampMsec90[index] + self.lyricsPlayOffsetTime90 and self.tiStampMsec90[index] != 0:
					newText = self.txtLines[index]
					if self.tiStampMsec90[index] != self.oldTiStampMsec90:
						self.oldTiStampMsec90 = self.tiStampMsec90[index]
						self.startKaraokeMaxTimer()
					if newText != self.oldLyricsText:
						self.oldLyricsText = self.displayLyricsText = newText
						self["lyricsLine"].setText(newText)
						self["lyricsLineBig"].setText(newText)
						if self.showBgSmall:
							self["lyricsLineBackground"].show()
						if self.showBgBig:
							self["lyricsLineBackgroundBig"].show()
					break
			if not self.karaokeMaxtimeTimer.isActive() and config.plugins.yampmusicplayer.karaokeMaxTime.value > 0:
				self.oldLyricsText = ''
				self.displayLyricsText = ''
				self["lyricsLine"].setText('')
				self["lyricsLineBig"].setText('')
				self["lyricsLineBackground"].hide()
				self["lyricsLineBackgroundBig"].hide()
			try:
				if len(self["lyricsLine"].getText()):
					if self.showBgSmall:
						self["lyricsLineBackground"].show()
					if self.showBgBig:
						self["lyricsLineBackgroundBig"].show()
			except Exception as e:
				LOG('YampScreen: checkKaraoke: Text lyrics: EXCEPT: %s' % (str(e)), 'err')
			if not self.screenSaverActive:
				self["lyricsLineBackground"].hide()
				self["lyricsLineBackgroundBig"].hide()
		except Exception as e:
			LOG('YampScreen: checkKaraoke: index: EXCEPT: %s' % (str(e)), 'err')

	def karaokeMaxtimeTimeout(self):
		if not self.karaokeTimer.isActive() and config.plugins.yampmusicplayer.karaokeMaxTime.value > 0:
			self.oldLyricsText = ''
			self.displayLyricsText = ''
			self["lyricsLine"].setText('')
			self["lyricsLineBig"].setText('')
			self["lyricsLineBackground"].hide()
			self["lyricsLineBackgroundBig"].hide()

	def startKaraokeMaxTimer(self):
		maxTime = config.plugins.yampmusicplayer.karaokeMaxTime.value * 1000
		if self.karaokeMaxtimeTimer.isActive():
			self.karaokeMaxtimeTimer.stop()
		if maxTime > 0:
			self.karaokeMaxtimeTimer.start(maxTime, True)

	def startcoverScrollTimer(self):
		maxTime = config.plugins.yampmusicplayer.coverScrollTime.value * 1000
		if self.coverScrollTimer.isActive():
			self.coverScrollTimer.stop()
		if maxTime > 0:
			self.coverScrollTimer.start(maxTime, True)

	def __evAudioDecodeError(self):
		currPlay = self.session.nav.getCurrentService()
		sTagAudioCodec = currPlay.info().getInfoString(iServiceInformation.sTagAudioCodec)
		LOG("[YampScreeen: __evAudioDecodeError] audio-codec %s can't be decoded by hardware" % (sTagAudioCodec), 'err')
		self.session.open(MessageBox, _("This Box can't decode %s streams!") % sTagAudioCodec, type=MessageBox.TYPE_INFO, timeout=20)

	def __evVideoDecodeError(self):
		currPlay = self.session.nav.getCurrentService()
		sTagVideoCodec = currPlay.info().getInfoString(iServiceInformation.sTagVideoCodec)
		LOG("[YampScreeen: __evVideoDecodeError] video-codec %s can't be decoded by hardware" % (sTagVideoCodec), 'err')
		self.session.open(MessageBox, _("This Box can't decode %s streams!") % sTagVideoCodec, type=MessageBox.TYPE_INFO, timeout=20)

	def __evPluginError(self):
		currPlay = self.session.nav.getCurrentService()
		message = currPlay.info().getInfoString(iServiceInformation.sUser + 12)
		LOG("[YampScreeen: __evPluginError] %s" % (message), 'err')
		self.session.open(MessageBox, message, type=MessageBox.TYPE_INFO, timeout=20)


# YAMP Main Screen actions
# There are 2 groups of actions, one depends on the active list (filelist, dblist or playlist), the other not
# List dependent actions:


	def ok(self):
		# screensaver or Fullscreen Video: go back
		if self.screenSaverActive or self.isVideoFullScreen:
			if self.screenSaverActive:
				self.hideScreenSaver()
				if self.playerState < STATE_STOP and self.manKeyScreensaver:
					self.resetScreenSaverTimer()
			if self.isVideoFullScreen:
				self.showYampScreenHideVideo()
			return
		if self.currList == "filelist":
			if self.filelist.canDescent():
				self.currFilePath = self.filelist.getSelection()[0]
				self.setLeftContentTitle()
				self.filelist.descent()
				self.updateLCDInfo()
			else:
				self.addFile()
				self.playlist.moveToIndex(len(self.playlist) - 1)
			self.movedown()
		elif self.currList == "dblist":
			self.dblistActions()
			self.updateLCDInfo()
			self.setLeftContentTitle()
			self.setColorButtons()
			self.checkCoverScroll()
		elif self.currList == "playlist":
			alreadyPlaying = (self.playlist.getCurrentIndex() == self.playlist.getSelectionIndex()) and (self.playerState == STATE_PLAY)
			if not alreadyPlaying:
				self.changeEntry(self.playlist.getSelectionIndex())
			previewVideoManual = self.currentIsVideo and self.videoStartMode == "manual"
			previewVideoImmediate = self.currentIsVideo and self.videoStartMode == "immediate"
			if self.playlist.getCurrentIndex() == self.playlist.getSelectionIndex():
				if not self.screenSaverActive:
					if self.playerState == STATE_PLAY and self.session.nav.getCurrentlyPlayingServiceReference() is not None:
						if not previewVideoManual:
							if alreadyPlaying or previewVideoImmediate:
								self.screenSaverStartTimeout()
							else:
								self.resetScreenSaverTimer()
						else:
							if alreadyPlaying:
								self.hideYampScreenShowVideo()

	def play(self):
		if self.playLongActive:
			self.playLongActive = False
			return
		if self.currList == "filelist":
			if self.screenSaverActive or self.specialScreenActive():
				self.switchPlayPause()
			else:
				lenPlayList = len(self.playlist)
				if self.filelist.canDescent():
					self.insertDir(self.filelist.getSelection()[0])
				else:
					self.insertFile()
				if len(self.playlist) > lenPlayList:
					self.movedown()
					self.nextEntry()
		elif self.currList == "dblist":
			try:
				navx = self.dblist.getSelection().nav
			except Exception:
				navx = False
			if self.screenSaverActive or self.specialScreenActive():
				self.switchPlayPause()
			elif not navx:  # if not navx:
				mode = self.dblist.mode
				if mode >= TITLELIST:
					sref = ServiceReference(self.dblist.getSelection().ref)
					self.insertService(self.playlist.getCurrentIndex() + 1, sref.ref, self.dblist.getSelection().title, self.dblist.getSelection().artist)
				elif mode in (PLAYLISTLIST, SEARCHPLAYLISTLIST):
					self.insertExtPlaylist(self.dblist.getSelection().filename)
				elif mode in (ARTISTLIST, SEARCHARTISTLIST):
					self.addCategory(query=self.dblist.getSelection().artistID, mode="insert", pos=self.playlist.getCurrentIndex() + 1)
				elif mode in (ALBUMLIST, ARTISTALBUMLIST, GENREALBUMLIST, SEARCHALBUMLIST):
					self.addCategory(query=self.dblist.getSelection().albumID, mode="insert", pos=self.playlist.getCurrentIndex() + 1)
				elif mode in (GENRELIST, SEARCHGENRELIST):
					self.addCategory(query=self.dblist.getSelection().genreID, mode="insert", pos=self.playlist.getCurrentIndex() + 1)
				self.nextEntry()
				self.movedown()
		elif self.currList == "playlist":
			self.switchPlayPause()

	def playLong(self):
		self.playLongActive = True
		if self.currList == "filelist":
			if not self.screenSaverActive and not self.specialScreenActive():
				lenPlayList = len(self.playlist)
				if self.filelist.canDescent():
					self.insertDir(self.filelist.getSelection()[0], recursive=True)
				else:
					self.insertFile()
				if len(self.playlist) > lenPlayList:
					self.nextEntry()
					self.movedown()

	def switchPlayPause(self):
		if config.plugins.yampmusicplayer.commonPlayPause.value:
			if self.playerState == STATE_PLAY:
				self.myOldMusicService = self.session.nav.getCurrentlyPlayingServiceReference()
				self.setSeekState(self.SEEK_STATE_PAUSE)
				self.playerState = STATE_PAUSE
			elif self.playerState == STATE_PAUSE:
				self.setSeekState(self.SEEK_STATE_PLAY)
				self.playerState = STATE_PLAY
				self.startScreenSaverTimer()
			elif self.playerState == STATE_STOP or self.playerState == STATE_NONE:
				self.changeEntry(self.playlist.getSelectionIndex())
				self.startScreenSaverTimer()
		else:
			self.changeEntry(self.playlist.getSelectionIndex())
			self.startScreenSaverTimer()

	def pause(self):
		self.pauseService()
		if self.seekstate == self.SEEK_STATE_PAUSE:
			self.hideScreenSaver()
			self.playerState = STATE_PAUSE
		else:
			if self.currList == "playlist":
				self.showScreenSaver()
			self.playerState = STATE_PLAY

	def blackListConfirmed(self, answer):
		try:
			LOG('YampScreen: blackListConfirmed: Start: slidepath: %s currslide: %s' % (self.par1, self.par2), 'all')
		except Exception as e:
			LOG('YampScreen: blackListConfirmed: Start: EXCEPT : %s' % (str(e)), 'err')
		if answer:  # insert into blacklist
			try:
				file = open(self.par1 + 'blacklist.txt', "a")  # self.par1: slidepath
				file.write(self.par2 + '\n')  # self.par2: slide
				file.close
			except Exception as e:
				self.session.open(MessageBox, _("blacklist file could not be saved"), type=MessageBox.TYPE_INFO, timeout=5)
				LOG('YampScreen: blackListConfirmed: writeSlideBlacklist: EXCEPT: %s' % (str(e)), 'err')
			try:
				self["screenSaver"].removeSlide(self.par2)
				self.resetSlideTimer()
			except Exception as e:
				LOG('YampScreen: blackListConfirmed: removeCurrentSlide: EXCEPT : %s' % (str(e)), 'err')

	def getSeekOwn(self):
		service = self.session.nav.getCurrentService()
		if service is None:
			return None
		seek = service.seek()
		if seek is None or not seek.isCurrentlySeekable():
			return None
		return seek

	def seekOwn(self, key):
		len, pos = self.getSeekData()
		jumplong = len / 900000  # 10%
		try:
			secs = 0
			if key == 1:
				secs = config.seek.selfdefined_13.value * (-1)
			elif key == 3:
				secs = config.seek.selfdefined_13.value
			elif key == 4:
				secs = config.seek.selfdefined_46.value * (-1)
			elif key == 6:
				secs = config.seek.selfdefined_46.value
			elif key == 7:
				secs = config.seek.selfdefined_79.value * (-1)
			elif key == 9:
				secs = config.seek.selfdefined_79.value
			elif key == 11:
				self.previousEntry()
				self.previousPressed = True
				return
			elif key == 12:
				self.nextEntry()
				return
			elif key == 21:  # 10% FW
				secs = jumplong
			elif key == 22:  # 10% BW
				secs = jumplong * (-1)
			elif key == 23:   #20% FW
				secs = jumplong * 2
			elif key == 24:   # 20% BW
				secs = jumplong * (-2)
			pts = secs * 90000
			if pos + pts > len:  # jump over end
				pts = len - 5 * 90000 - pos  # 5 seconds before end
			seekable = self.getSeek()
			if seekable is None:
				LOG('YampScreen: seekOwn: seekable NONE', 'err')
				return
			seekable.seekRelative(pts < 0 and -1 or 1, abs(pts))
		except Exception as e:
			LOG('YampScreen: seekOwn: EXCEPT: %s' % (str(e)), 'err')

	def showDatabaseScreen(self, recursive=False):
		self.showYampScreenHideVideo()
		self.searchFanartConfig = 'off'
		self.hideScreenSaver()
		self.screenSaverManTimer.stop()
		self.dbScreenActive = True
		try:
			self.session.openWithCallback(self.showDbScreenCB, YampDatabaseScreenV33, "add", self.filelist.getFilename(), recursive=recursive)
		except Exception as e:
			LOG('YampScreen: showDatabaseScreen: EXCEPT: %s' % (str(e)), 'err')

	def showDbScreenCB(self):
		self.searchFanartConfig = config.plugins.yampmusicplayer.searchFanart.value
		self.startScreenSaverManTimer()
		self.dbScreenActive = False
		if not self.currentIsVideo or self.videoStartMode != "manual":
			self.resetScreenSaverTimer()

	def switchToFileList(self):
		if self.screenSaverActive and self.playerState < STATE_STOP:
			self.prevSlide()
		elif self.currList == "playlist":
			if not config.plugins.yampmusicplayer.screenSaverLeft.value:
				self.hideScreenSaver()
			if self.leftContent == "filelist":
				self.currList = "filelist"
				self.filelist.selectionEnabled(1)
			else:
				self.currList = "dblist"
				self.dblist.selectionEnabled(1)
			self.playlist.selectionEnabled(0)
			self.setColorButtons()
			self.updateLCDInfo()
			self.resetScreenSaverTimer()

	def switchToPlayList(self):
		if self.screenSaverActive:
			self.nextSlide()
		elif self.currList != "playlist" and len(self.playlist) > 0:
			self.currList = "playlist"
			self.filelist.selectionEnabled(0)
			self.dblist.selectionEnabled(0)
			self.playlist.selectionEnabled(1)
			self.checkCoverScroll()
			self.setColorButtons()
			self.updateLCDInfo()
			self.resetScreenSaverTimer()

	def toggleSsBg(self):
		if not self.isVideoFullScreen:
			if self["screenSaver"].refreshPic(test=True) == 0:
				return
			self.ssBackground = not self.ssBackground
			self.setScreensaverBg()

	def toggleRepeat(self):
		if not self.isVideoFullScreen:
			self.repeat = not self.repeat
			self.setRepeatButton()

	def setRepeatButton(self):
		if self.repeat:
			self["repeat"].setPixmapNum(1)
		else:
			self["repeat"].setPixmapNum(0)
		self.updateNextSong()

	def tvActions(self):
		if self.tvLongActive:
			self.tvLongActive = False
		else:
			commonTvRadio = config.plugins.yampmusicplayer.commonTvRadio.value
			if commonTvRadio == 'no' or commonTvRadio == 'TvEndless':
				self.toggleRepeat()
			elif commonTvRadio == 'TvShuffle':
				self.toggleShuffle()

	def tvLongActions(self):
		self.tvLongActive = True
		commonTvRadio = config.plugins.yampmusicplayer.commonTvRadio.value
		if commonTvRadio == 'TvShuffle':
			self.toggleRepeat()
		elif commonTvRadio == 'TvEndless':
			self.toggleShuffle()

	def radioActions(self):
		if self.radioLongActive:
			self.radioLongActive = False
		else:
			commonTvRadio = config.plugins.yampmusicplayer.commonTvRadio.value
			if commonTvRadio == 'no' or commonTvRadio == 'RadioShuffle':
				self.toggleShuffle()
			elif commonTvRadio == 'RadioEndless':
				self.toggleRepeat()

	def radioLongActions(self):
		self.radioLongActive = True
		commonTvRadio = config.plugins.yampmusicplayer.commonTvRadio.value
		if commonTvRadio == 'RadioShuffle':
			self.toggleRepeat()
		elif commonTvRadio == 'RadioEndless':
			self.toggleShuffle()

	def toggleShuffle(self):
		if not self.isVideoFullScreen:
			if self.currList == "playlist" and not self.screenSaverActive:
				self.playlist.shuffleList()
				self.setShuffleButton()
				self.updatePlaylistInfo()
				self.recalcLenListsComplete()
				self.updateNextSong()

	def setShuffleButton(self):
		if self.playlist.isShuffeled:
			self["shuffle"].setPixmapNum(1)
		else:
			self["shuffle"].setPixmapNum(0)

	def setSaverButton(self):
		if self.screenSaverTimer.isActive():
			self["saver"].setPixmapNum(1)
		else:
			self["saver"].setPixmapNum(0)

	def setHelpTexts(self):
		if config.plugins.yampmusicplayer.displayButtonHelp.value:
			commonTvRadio = config.plugins.yampmusicplayer.commonTvRadio.value
			txtRepeat, txtShuffle = "", ""
			if commonTvRadio == 'no':
				txtShuffle = 'Radio'
				txtRepeat = 'TV'
			elif commonTvRadio == 'TvShuffle':
				txtShuffle = 'TV'
				txtRepeat = 'TV L'
			elif commonTvRadio == 'TvEndless':
				txtShuffle = 'TV L'
				txtRepeat = 'TV'
			elif commonTvRadio == 'RadioShuffle':
				txtShuffle = 'Radio'
				txtRepeat = 'Rad L'
			elif commonTvRadio == 'RadioEndless':
				txtShuffle = 'Rad L'
				txtRepeat = 'Radio'
			self["txtRepeat"].setText(txtRepeat)
			self["txtShuffle"].setText(txtShuffle)

			self["txtRepeat"].show()
			self["txtShuffle"].show()
			self["textSaver"].show()
		else:
			self["txtRepeat"].hide()
			self["txtShuffle"].hide()
			self["textSaver"].hide()

	def setColorButtons(self):
		if self.currList == "playlist":
			self["key_blue"].setText(_("Delete Playlist Entry\nClear Playlist"))
		else:
			self["key_blue"].setText('')
		if self.currList == "filelist":
			self["key_red"].setText(_("Database Mode"))
			self["key_green"].setText(_("Add to Playlist\nAdd to PL incl.Subdirs"))
			self["key_yellow"].setText(_("Add to Database\nAdd to DB incl.Subdirs"))
		elif self.currList == "dblist":
			mode = self.dblist.mode
			self["key_red"].setText(_("Filelist Mode"))
			self["key_green"].setText("")
			if mode > MENULIST:
				if mode >= TITLELIST:
					self["key_green"].setText(_("Add to Playlist\nAdd all to Playlist"))
				else:
					self["key_green"].setText(_("Add to Playlist"))
			self["key_yellow"].setText("")
			if mode in (TITLELIST, GENRETITLELIST, SEARCHTITLELIST, SEARCHFILELIST):
				self["key_yellow"].setText(_("Show Album\nShow Artist"))
			elif mode in (ARTISTLIST, GENRELIST, SEARCHARTISTLIST, SEARCHGENRELIST):
				self["key_yellow"].setText(_("Show Albums"))
			elif mode in (ARTISTTITLELIST, SEARCHARTISTTITLELIST):
				self["key_yellow"].setText(_("Show Album"))
			elif mode in (ALBUMTITLELIST, SEARCHALBUMTITLELIST):
				self["key_yellow"].setText(_("Show Artist"))
		else:  # playlist
			repeatMove = config.plugins.yampmusicplayer.playlistMoveMulti.value
			try:
				self["key_red"].setText(_('Move Entry Up\nMove Entry Up by %d') % repeatMove)
			except Exception:
				pass
			self["key_green"].setText(_("Move Entry Down\nMove Entry Down by %d") % repeatMove)
			self["key_yellow"].setText(_("Save Cover\nSave Album Cover"))

	def setLeftContent(self, list):
		if list == "dblist":
			self.leftContent = "dblist"
			self["filelist"].hide()
			self["dblist"].show()
			self.dblist.selectionEnabled(1)
			self.filelist.selectionEnabled(0)
		else:
			self.leftContent = "filelist"
			self["dblist"].hide()
			self["filelist"].show()
			self.filelist.selectionEnabled(1)
			self.dblist.selectionEnabled(0)
		self.setLeftContentTitle()

	def setLeftContentTitle(self):
		if self.leftContent == "filelist":
			layoutFileList = config.plugins.yampmusicplayer.fileListTitleLayout.value
			currFilePath = self.currFilePath or ""
			if layoutFileList == 'titleOnly':
				self["leftContentTitle"].setText(_("M u s i c  F i l e s"))
			elif layoutFileList == 'pathOnly':
				self["leftContentTitle"].setText(currFilePath)
			else:
				self["leftContentTitle"].setText(_("Music Files") + '  ' + currFilePath)
		else:
			self["leftContentTitle"].setText(self.dblist.title)

# list independent actions
	def showHelp(self):
		self.hideScreenSaver()
		if self.isVideoFullScreen:
			self.showYampScreenHideVideo()
		if hasattr(HelpableScreen, 'showHelp'):
			HelpableScreen.showHelp(self)  # old method
		else:
			Screen.showHelp(self)  # new method

	def nextEntry(self):
		LOG('YampScreen: nextEntry: Start: specialScreenActive(): %d' % (self.specialScreenActive()), 'all')
		# reset SS background setting
		if config.plugins.yampmusicplayer.resetScreenSaverBg.value:
			self.ssBackground = config.plugins.yampmusicplayer.screenSaverBg.value
			self.setScreensaverBg()
			LOG('YampScreen: nextEntry: reset Screensaver Background to initial setting: %d' % (self.ssBackground), 'all')
		actual = self.playlist.getCurrentIndex()
		nextEntry = actual + 1
		if nextEntry < len(self.playlist):  # normal next song
			self.changeEntry(nextEntry)
		elif (len(self.playlist) > 0) and self.repeat:  # last song and repeat: jump to first
			self.changeEntry(0)
		elif (len(self.playlist) == actual + 1) and not self.repeat:  # last song, no repeat
			self.stopEntry()

	def previousKey(self):
		self.previousPressed = True
		self.previousEntry()

	def previousEntry(self):
		LOG('YampScreen: previousEntry: Start: specialScreenActive(): %d' % (self.specialScreenActive()), 'all')
		# reset SS background setting
		if config.plugins.yampmusicplayer.resetScreenSaverBg.value:
			self.ssBackground = config.plugins.yampmusicplayer.screenSaverBg.value
			self.setScreensaverBg()
			LOG('YampScreen: previousEntry: reset Screensaver Background to initial setting: %d' % (self.ssBackground), 'all')
		nextEntry = self.playlist.getCurrentIndex() - 1
		if nextEntry >= 0:
			self.changeEntry(nextEntry)
		elif self.repeat:
			self.changeEntry(len(self.playlist) - 1)

	def pagedown(self):
		if not self.screenSaverActive and not self.isVideoFullScreen:
			self[self.currList].pageDown()
			self.checkCoverScroll()
			self.updatePlaylistInfo()
			self.updateLCDInfo()
		if not self.currentIsVideo or self.videoStartMode != "manual":
			self.resetScreenSaverTimer()
		self.showYampScreenHideVideo()

	def pageup(self):
		if not self.screenSaverActive and not self.isVideoFullScreen:
			self[self.currList].pageUp()
			self.checkCoverScroll()
			self.updatePlaylistInfo()
			self.updateLCDInfo()
		if not self.currentIsVideo or self.videoStartMode != "manual":
			self.resetScreenSaverTimer()
		self.showYampScreenHideVideo()

	def getSongLength(self, path=""):
		con, result = ConnectDatabase()
		if con:
			cursor = con.cursor()
			try:
				cursor.execute('SELECT length FROM Titles WHERE Titles.filename = "%s";' % (path))
			except Exception as e:
				LOG('YampScreen: getSongLength: cursor.execute: EXCEPT: %s' % (str(e)), 'err')
			t = datetime.now()
			try:
				for row in cursor:
					try:
						lenData = row[0]
						if lenData == 'n/a':
							lenData = '0:00'
						if len(lenData) > 5:
							strFormat = '%H:%M:%S'
						else:
							strFormat = '%M:%S'
						t = datetime.strptime(lenData, strFormat)
						r = row[0]
						if isinstance(r, bytes):
							r = r.decode()
						t = datetime.strptime(r, '%M:%S')
					except Exception as e:
						t = datetime.strptime("00:00", '%M:%S')
						LOG("YampScreen: DEBUG getSongLength %s %s" % (row[0], type(row[0])), 'err')
						LOG('YampScreen: getSongLength: for row: row %s path: %s EXCEPT2: %s' % (row, path, str(e)), 'err')
			except Exception as e:
				LOG('YampScreen: getSongLength: for row: EXCEPT : %s' % (str(e)), 'err')
			cursor.close()
			con.close()
			try:
				return (t.minute + t.hour * 60, t.second)
			except Exception:
				pass
		return (0, 0)

	def getAlbumInfo(self, ID=61, path=""):
		con, result = ConnectDatabase()
		self.AlbumPath = ""
		self.AlbumArtist = ""
		self.AlbumTitle = ""
		if con:
			cursor = con.cursor()
			try:
				cursor.execute("SELECT title_id, title, filename, Titles.artist_id, Artists.artist, Titles.album_id, Albums.album FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id INNER JOIN Albums ON Titles.album_id = Albums.album_id WHERE Titles.album_id = %d ORDER BY upper(title), upper(Albums.album);" % (ID))
			except Exception as e:
				LOG('YampScreen: getAlbumInfo: cursor.execute: EXCEPT: %s' % (str(e)), 'err')
			try:
				for row in cursor:
					path = str(row[2])
					self.AlbumPath = str(row[2])
					self.AlbumArtist = str(row[4])
					self.AlbumTitle = str(row[1])
					break
			except Exception as e:
				LOG('YampScreen: getAlbumInfo: for row: EXCEPT: %s' % (str(e)), 'err')
			try:
				cursor.close()
			except Exception:
				pass
			try:
				con.close()
			except Exception:
				pass
		else:
			LOG('YampScreen: getAlbumInfo: con is none', 'err')

	def checkCoverScroll(self):
		if config.plugins.yampmusicplayer.coverScrollTime.value == 0:
			return
		self.startcoverScrollTimer()
		path = ""
		if not self.screenSaverActive and not self.isVideoFullScreen:
			if self.currList == "playlist":  # playlist
				path = self.playlist.getServiceRefList()[self.playlist.getSelectionIndex()].getPath() or ""
				self.updateMusicInformation(path, current=False)
			elif self.currList == "filelist":
				if self.filelist.getSelection()[1]:  # is directory
					path = self.filelist.getFilename() or ""
				self.updateMusicInformation(path, current=False)
			else:  # dblist
				try:
					nav = self.dblist.getSelection().nav
				except Exception as e:
					nav = False
					LOG('YampScreen: checkCoverScroll: dblist: nav: EXCEPT: %s' % (str(e)), 'err')
				if nav and self.dblist.mode == ALBUMLIST:
					pass
				if not nav:
					mode = self.dblist.mode
					if mode >= TITLELIST or mode == ALBUMLIST:
						path = self.dblist.getSelection().filename
						try:
							if mode == ALBUMLIST:
								self.updateMusicInformation(path, current=False, isAlbum=True)
							else:
								self.updateMusicInformation(path, current=False)
							self.updateMusicInformation(path, current=False)
						except Exception as e:
							LOG('YampScreen: checkCoverScroll: dblist: updateMusicInformation: EXCEPT: %s' % (str(e)), 'err')
				else:  # no selection of files, overview
					self.updateMusicInformation(clear=True, current=False)

	def moveup(self):
		if not self.screenSaverActive and not self.isVideoFullScreen:
			self[self.currList].up()
			self.updatePlaylistInfo()
			self.checkCoverScroll()
			self.updateLCDInfo()
		if not self.currentIsVideo or self.videoStartMode != "manual":
			self.resetScreenSaverTimer()
		self.showYampScreenHideVideo()

	def movedown(self):
		if not self.screenSaverActive and not self.isVideoFullScreen:
			self[self.currList].down()
			self.updatePlaylistInfo()
			self.checkCoverScroll()
			self.updateLCDInfo()
		if not self.currentIsVideo or self.videoStartMode != "manual":
			self.resetScreenSaverTimer()
		self.showYampScreenHideVideo()

	def skipToListbegin(self):
		if not self.isVideoFullScreen:
			if not self.screenSaverActive:
				self[self.currList].moveToIndex(0)
				self.checkCoverScroll()
				self.updatePlaylistInfo()
				self.updateLCDInfo()
			self.resetScreenSaverTimer()

	def skipToListend(self):
		if not self.isVideoFullScreen:
			if not self.screenSaverActive:
				self[self.currList].moveToIndex(len(self[self.currList]) - 1)
				self.checkCoverScroll()
				self.updatePlaylistInfo()
				self.updateLCDInfo()
			self.resetScreenSaverTimer()

	def clearPlaylistConfirmed(self, answer):
		self.resetScreenSaverTimer()
		if answer:
			self.clearPlaylist()
			self.updatePlaylistInfo()

# Add and Insert methods from YampFileList into PlayList

	def addFile(self):
		global secList, minList
		f = self.filelist.getFilename()
		if f.lower().endswith(".m3u") or f.lower().endswith(".pls") or f.lower().endswith(".e2pls"):
			self.addExtPlaylist(f)
		else:
			ref = self.filelist.getServiceRef()
			self.addService(self.filelist.getServiceRef())
			self.playlist.updateList()
			if ref:
				songmin, songsec = self.getSongLength(ref.getPath())
				secList.append(songsec)
				minList.append(songmin)
			self.calcLenPlaylist()
			self.updateNextSong()

	def addAllFiles(self):
		for x in self.filelist.getFileList():
			if x[0][1] is False:  # ordinary file
				f = x[0][0].getPath()
				if f.lower().endswith(".m3u") or f.lower().endswith(".pls") or f.lower().endswith(".e2pls"):
					pass  # don't copy playlists
				else:
					self.addService(x[0][0])
		self.playlist.updateList()
		self.updateNextSong()

	def addDir(self, dir, recursive=True):
		filelist = YampFileList(dir, matchingPattern=r"(?i)^.*\.(mp2|mp3|ogg|ts|wav|m3u|pls|e2pls|mpg|vob|avi|divx|m4v|mkv|mp4|m4a|dat|flac|mov|m2ts)", useServiceRef=True, showMountpoints=False, isTop=True)
		for x in filelist.getFileList():
			if x[0][1] is True:  # isDir
				if recursive and x[0][0] != dir:
					self.addDir(x[0][0])
			else:
				self.addService(x[0][0])
		self.playlist.updateList()
		self.updateNextSong()

	def addExtPlaylist(self, pl):
		global secList, minList
		ext = splitext(pl)[1]
		if ext in self.playlistparsers:
			playlistParser = self.playlistparsers[ext]()
			plist = playlistParser.open(pl)
			if plist:
				for x in plist:
					try:
						songmin, songsec = self.getSongLength(x.getPath())
						secList.append(songsec)
						minList.append(songmin)
						self.playlist.addService(x.ref)  # No layout change for playlists
					except Exception as e:
						LOG('YampScreen: addExtPlaylist: EXCEPT: %s' % (str(e)), 'err')
				self.playlist.updateList()
				self.calcLenPlaylist()
				if ext == ".e2pls":
					self.extPlaylistName = splitext(basename(pl))[0]

	def insertFile(self):
		f = self.filelist.getFilename()
		ext = splitext(f)[1]
		if ext in (".m3u", ".pls", ".e2pls"):
			self.insertExtPlaylist(f)
			return False
		else:
			ref = self.filelist.getServiceRef()
			newIdx = self.playlist.getCurrentIndex() + 1
			self.insertService(newIdx, ref)
			self.insertEntryLenLists(ref, newIdx)
			self.calcLenPlaylist()
			self.playlist.updateList()
			self.updateNextSong()
			return True

	def insertDir(self, dir, recursive=False):
		filelist = YampFileList(dir, matchingPattern=r"(?i)^.*\.(mp2|mp3|ogg|ts|wav|m3u|pls|e2pls|mpg|vob|avi|divx|m4v|mkv|mp4|m4a|dat|flac|mov|m2ts)", useServiceRef=True, showMountpoints=False, isTop=True)
		for x in reversed(filelist.getFileList()):
			if x[0][1] is False:  # not isDir and recursive
				self.insertService(self.playlist.getCurrentIndex() + 1, x[0][0])
		self.recalcLenListsComplete()
		self.playlist.updateList()
		self.updateNextSong()

	def insertExtPlaylist(self, pl):
		ext = splitext(pl)[1]
		if ext in self.playlistparsers:
			playlistParser = self.playlistparsers[ext]()
			plist = playlistParser.open(pl)
			if plist:
				for x in plist:
					self.insertService(self.playlist.getCurrentIndex() + 1, x.ref)
				self.playlist.updateList()
				self.updateNextSong()
				if ext == ".e2pls":
					self.extPlaylistName = splitext(basename(pl))[0]

#
# Add and Insert methods from DatabaseList into PlayList
#
	def addCategory(self, query, mode="append", pos=0):
		con, result = ConnectDatabase()
		mypos = 0
		addMode = mode
		if addMode == "insert":
			mypos = pos - 1
		if con is not None:
			con.text_factory = str
			cursor = con.cursor()
			mode = self.dblist.mode
			if mode in (ARTISTLIST, SEARCHARTISTLIST):
				if config.plugins.yampmusicplayer.titleOnlyOnceInSelection.value:
					cursor.execute("SELECT min(title_id), sref, title, Artists.artist FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id WHERE Titles.artist_id = %d GROUP BY upper(title);" % (query))
				else:
					cursor.execute("SELECT title_id, sref, title, Artists.artist FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id INNER JOIN Albums ON Titles.album_id = Albums.album_id WHERE Titles.artist_id = %d ORDER BY upper(title), upper(Albums.album);" % (query))
			elif mode in (ALBUMLIST, ARTISTALBUMLIST, GENREALBUMLIST, SEARCHALBUMLIST, DATEALBUMLIST):
				cursor.execute("SELECT title_id, sref, title, Artists.artist FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id INNER JOIN Albums ON Titles.album_id = Albums.album_id WHERE Titles.album_id = %d ORDER BY tracknr, filename;" % (query))
			elif mode in (GENRELIST, SEARCHGENRELIST):
				if config.plugins.yampmusicplayer.titleOnlyOnceInSelection.value:
					cursor.execute("SELECT min(title_id), sref, title, Artists.artist FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id WHERE Titles.genre_id = %d GROUP BY upper(title);" % (query))
				else:
					cursor.execute("SELECT title_id, sref, title, Artists.artist FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id INNER JOIN Albums ON Titles.album_id = Albums.album_id WHERE Titles.genre_id = %d ORDER BY upper(title), upper(Albums.album);" % (query))
			elif mode in (DATELIST, SEARCHDATELIST):
				if config.plugins.yampmusicplayer.titleOnlyOnceInSelection.value:
					cursor.execute("SELECT min(title_id), sref, title, Artists.artist FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id WHERE Titles.date_id = %d GROUP BY upper(title);" % (query))
				else:
					cursor.execute("SELECT title_id, sref, title, Artists.artist FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id INNER JOIN Albums ON Titles.album_id = Albums.album_id WHERE Titles.date_id = %d ORDER BY upper(title), upper(Albums.album);" % (query))
			for row in cursor:
				sref = ServiceReference(row[1])
				if addMode == "append":
					self.addService(sref.ref, row[2], row[3])
				else:
					mypos += 1
					self.insertService(mypos, sref.ref, row[2], row[3])
			self.playlist.updateList()
			self.updateNextSong()
			cursor.close()
			con.close()

# Add and Insert helper methods
	def addService(self, ref, title="", artist=""):
		self.applyLayout(ref, title, artist)
		self.playlist.addService(ref)

	def insertService(self, index, ref, title="", artist=""):
		self.applyLayout(ref, title, artist)
		self.playlist.insertService(index, ref)

	def applyLayout(self, sref, title, artist):
		path = sref.getPath()
		if config.plugins.yampmusicplayer.playlistLayout.value.startswith("fn"):
			path = basename(path)
			if config.plugins.yampmusicplayer.playlistLayout.value == "fn":
				path = splitext(path)[0]
			sref.setName(path)
		elif config.plugins.yampmusicplayer.playlistLayout.value.startswith("tit"):
			if not title or not artist:
				title, album, genre, artist, albumartist, date, length, tracknr, strBitrate = readID3Infos(path)
			if config.plugins.yampmusicplayer.playlistLayout.value == "tit":
				name = title
			elif config.plugins.yampmusicplayer.playlistLayout.value == "titart":
				name = title + " - " + artist
			else:
				name = artist + " - " + title
			if not name:
				name = splitext(basename(path))[0]
			sref.setName(name)
		else:  # for now no other layout options
			pass

# dblist actions
# For navigation, the dblist maintains its own stack
	def dblistActions(self):
		global secList, minList
		try:
			navx = self.dblist.getSelection().nav
		except Exception:
			navx = False
		if navx:
#		if self.dblist.getSelection().nav:
			entry = self.popDblistStack()
			self.buildDbMenuList(mode=entry.mode, query=entry.query, menutitle=entry.menutitle, queryString=entry.queryString)
			self.dblist.moveToIndex(entry.selIndex)
		else:
			numChoice = self.dblist.getSelectionIndex()
			mode = self.dblist.mode
			if mode == MENULIST:
				self.pushDblistStack(numChoice)
				if numChoice == 0:
					self.buildDbMenuList(mode=PLAYLISTLIST, menutitle=_("E x t .  P l a y l i s t s"))
				elif numChoice == 1:
					self.buildDbMenuList(mode=ARTISTLIST, menutitle=_("A r t i s t s"))
				elif numChoice == 2:
					self.buildDbMenuList(mode=ALBUMLIST, menutitle=_("A l b u m s"))
				elif numChoice == 3:
					self.buildDbMenuList(mode=TITLELIST, menutitle=_("T i t l e s"))
				elif numChoice == 4:
					self.buildDbMenuList(mode=GENRELIST, menutitle=_("G e n r e s"))
				elif numChoice == 5:
					self.buildDbMenuList(mode=DATELIST, menutitle=_("D a t e s"))
			elif mode in (ARTISTLIST, SEARCHARTISTLIST):
				self.pushDblistStack(numChoice)
				choice = self.dblist.getSelection()
				self.buildDbMenuList(mode=ARTISTTITLELIST, query=choice.artistID, menutitle=_('Artist') + ':  ' + choice.artist)
			elif mode in (ALBUMLIST, ARTISTALBUMLIST, GENREALBUMLIST, SEARCHALBUMLIST):
				self.pushDblistStack(numChoice)
				choice = self.dblist.getSelection()
				self.buildDbMenuList(mode=ALBUMTITLELIST, query=choice.albumID, menutitle=_('Album') + ':  ' + choice.album + ' - ' + choice.artist)
			elif mode in (GENRELIST, SEARCHGENRELIST):
				self.pushDblistStack(numChoice)
				choice = self.dblist.getSelection()
				self.buildDbMenuList(mode=GENRETITLELIST, query=choice.genreID, menutitle=_('Genre') + ':  ' + choice.genre)
			elif mode in (DATELIST, SEARCHDATELIST):
				self.pushDblistStack(numChoice)
				choice = self.dblist.getSelection()
				self.buildDbMenuList(mode=DATETITLELIST, query=choice.dateID, menutitle=_('Year') + ':  ' + choice.date)
			elif mode in (PLAYLISTLIST, SEARCHPLAYLISTLIST):
				self.addExtPlaylist(self.dblist.getSelection().filename)
			elif mode >= TITLELIST:
				sref = ServiceReference(self.dblist.getSelection().ref)
				self.addService(sref.ref, self.dblist.getSelection().title, self.dblist.getSelection().artist)
				try:
					try:
						t = datetime.strptime(self.dblist.getSelection().length, '%M:%S')
					except Exception:
						t = datetime.strptime("00:00", '%M:%S')
					secList.append(t.second)
					minList.append(t.minute)
				except Exception as e:
					LOG('YampScreen: dbListAction: adddservice: EXCEPT: %s' % (str(e)), 'err')
				self.playlist.updateList()
				self.calcLenPlaylist()
				self.updateNextSong()
				self.movedown()

	def startupChecks(self):
		if self.skinChangedMissing:
			try:
				if self.configSkin == self.newSkin:
					msg = _('Attention! Crash possible!\n\nIn actual skin <%s> the file %s\nis missing\n\nPlease check and repair!') % (self["actskin"].getText(), self.skinChangedMissing)
					msgboxType = MessageBox.TYPE_ERROR
				else:
					self["actskin"].setText(self.getSkinName(self.newSkin))
					msg = _('Skin changed to\n\n<%s>,  as\n\n%s\n\n(and maybe more) not existing') % (self.getSkinName(self.newSkin), self.skinChangedMissing)
					msgboxType = MessageBox.TYPE_INFO

				self.session.open(MessageBox, msg, type=msgboxType, timeout=30)
			except Exception as e:
				LOG('YampScreen: startupChecks: MessageBox EXCEPT: %s' % (str(e)), 'err')
		if self.oldCustomSkin:
			msg = _('This custom skin most likely has been copied from an old version, and probably is not up-to-date.\n\nIt is recommended to switch to a standard skin and check and revise the custom skin (compare it with the according standard skin)!')
			msgboxType = MessageBox.TYPE_INFO
			self.session.open(MessageBox, msg, type=msgboxType, timeout=30)
		self.checkDatabaseConnection()
		self.findClockElement()
		self.loadLastPlaylist()
		try:
			if len(self.playlist) > 0:
				if config.plugins.yampmusicplayer.startImmediate.value:  # Start playlist immediate
					self.changeEntry(self.playlist.getSelectionIndex())
					self.startScreenSaverTimer()
				else:  # show selected songinfos
					artist = title = album = path = ''
					if self.currList == "playlist":
						try:
							path = self.playlist.getServiceRefList()[self.playlist.getSelectionIndex()].getPath()
							if path is not None:
								self.updateMusicInformation(path)
						except Exception as e:
							LOG('YampScreen: startupChecks: checkMusicInfo: EXCEPT: %s' % (str(e)), 'err')
		except Exception as e:
			LOG('YampScreen: startupChecks: checkplaylist: EXCEPT: %s' % (str(e)), 'err')
		# info DB Upgrade V332
		msg = ''
		if self.dbUpgradeInfo332 == 1 or self.dbUpgradeInfo332 > 999:
			msg = _('Database has been upgraded to V3.3.2. ID3-tag AlbumArtist is recognized now. You should rescan at least your Sampler-Albums (various artists) into the database...')
		elif self.dbUpgradeInfo332 < 0:
			msg = _('There was an error when upgrading the Database to V3.3.2 (or database not existing). To get all advantages from the new DB options, think about deleting the database and rebuild it by re-inserting all files...')
		elif self.dbUpgradeInfo332 == 999:
			if config.plugins.yampmusicplayer.searchFanart.value != 'off':
				msg = _('Database has been upgraded to V3.3.2, but the database is empty. Online-search for fanart-pictures has been deactivated. To get all advantages from the new DB options, think about adding files to the database... As long as the online search is deactivated, you will not see this message again!')
				config.plugins.yampmusicplayer.searchFanart.value = 'off'
				config.plugins.yampmusicplayer.searchFanart.save()
				self.searchFanartConfig = config.plugins.yampmusicplayer.searchFanart.value
		if msg:
			self.session.open(MessageBox, msg, type=MessageBox.TYPE_INFO, timeout=20)
		# info DB Upgrade V331
		msg = ''
		if self.dbUpgradeInfo331 > 1000:
			msg = _("DB-Upgrade to V3.3.1:\n%d titles have been actualized to the new feature 'Several Albums Greatest Hits separated by Artist possible'.\nPlease check ..." % (self.dbUpgradeInfo331 - 1000))
		if msg:
			self.session.open(MessageBox, msg, type=MessageBox.TYPE_INFO, timeout=30)
		if self.dbUpgradeInfo331 == 1 or self.dbUpgradeInfo331 > 999:
			msg = _('Database has been upgraded to V3.3.1. To get all advantages from the new DB options, you should actualize the database. Just insert all your files again to the database...')
		elif self.dbUpgradeInfo331 < 0:
			msg = _('There was an error when upgrading the Database to V3.3.1 (or database not existing). To get all advantages from the new DB options, think about deleting the database and rebuild it by re-inserting all files...')
		elif self.dbUpgradeInfo331 == 999:
			if config.plugins.yampmusicplayer.searchFanart.value != 'off':
				msg = _('Database has been upgraded to V3.3.1, but the database is empty. Online-search for fanart-pictures has been deactivated. To get all advantages from the new DB options, think about adding files to the database... As long as the online search is deactivated, you will not see this message again!')
				config.plugins.yampmusicplayer.searchFanart.value = 'off'
				config.plugins.yampmusicplayer.searchFanart.save()
				self.searchFanartConfig = config.plugins.yampmusicplayer.searchFanart.value
		if msg:
			self.session.open(MessageBox, msg, type=MessageBox.TYPE_INFO, timeout=20)
		self.updatePlaylistInfo()
		self.showCompleteScreen()
		if self.playerState != STATE_PLAY:  # immediate start
			self.showHideVideoPreview(self.TvStart or self.Tv)
		self.updateLCDInfo()
		self.initScreenSaver()
		# Screensaver in Background
		self.setScreensaverBg()
		self.setSaverButton()
		if config.plugins.yampmusicplayer.lastVersionDate.value < VERSIONDATE or config.plugins.yampmusicplayer.showHelpStart.value:
			self.session.openWithCallback(self.helpScreenCB, YampHelpScreenV33)

	def checkDatabaseConnection(self):
		dbPath = join(config.plugins.yampmusicplayer.databasePath.value, "yamp.db")
		con, result = ConnectDatabase()
		if con:
			if result == 1:
				self.session.open(MessageBox, _('Cannot open database file %s.') % (dbPath), type=MessageBox.TYPE_ERROR, timeout=15)
			elif result == 2:
				self.session.open(MessageBox, _('Cannot write to database %s. Maybe Read-Only?') % (dbPath), type=MessageBox.TYPE_ERROR, timeout=15)
			con.close()

	def buildDbMenuList(self, mode=None, query=-1, menutitle="", queryString=""):
		con, result = ConnectDatabase()
		if con is not None:
			con.text_factory = str
			cursor = con.cursor()
			if mode is not None:
				self.dblist.setMode(mode)
				if mode >= TITLELIST:
					self.dblist.setLines(2)
				else:
					self.dblist.setLines(1)
			self.dblist.setTitle(menutitle)
			self.dblist.list = []
			if self.dblist.mode == MENULIST:  # Main Menu
				# Playlists
				cursor.execute("SELECT COUNT (*) FROM Playlists;")
				row = cursor.fetchone()
				self.dblist.append(DblistEntryComponent(text=_("Playlists (%d)") % row[0]))
				# Artists
				if config.plugins.yampmusicplayer.dbArtistReduce.value:
					sql = 'SELECT artistShort FROM Artists GROUP BY artistShort;'
					cursor.execute(sql)
					row = cursor.fetchall()
					count = len(row)
				else:
					cursor.execute("SELECT COUNT (*) FROM Artists;")
					row = cursor.fetchone()
					count = row[0]
				self.dblist.append(DblistEntryComponent(text=_("Artists (%d)") % count))
				# Albums
				cursor.execute("SELECT COUNT (*) FROM Albums;")
				row = cursor.fetchone()
				self.dblist.append(DblistEntryComponent(text=_("Albums (%d)") % row[0]))
				# Titles
				cursor.execute("SELECT COUNT (*) FROM Titles;")
				row = cursor.fetchone()
				self.dblist.append(DblistEntryComponent(text=_("Titles (%d)") % row[0]))
				# Genres
				cursor.execute("SELECT COUNT (*) FROM Genres;")
				row = cursor.fetchone()
				self.dblist.append(DblistEntryComponent(text=_("Genres (%d)") % row[0]))
				# Dates
				try:
					sql = 'SELECT substr(Dates.date,1,4) FROM Dates GROUP BY substr(Dates.date,1,4)'
					cursor.execute(sql)
					rows = cursor.fetchall()
					self.dblist.append(DblistEntryComponent(text=_("Years (%d)") % len(rows)))
				except Exception as e:
					LOG('YampScreen: buildDbMenuList: Dates: EXCEPT: %s' % (str(e)), 'err')
				self.dblist.updateList()
			else:  # Lists
				self.dblist.append(DblistEntryComponent(text=_("[back]"), nav=True))
				if self.dblist.mode == PLAYLISTLIST:
					cursor.execute("SELECT playlist_id, playlist_title, playlist_filename FROM Playlists ORDER BY upper(playlist_title);")
					for row in cursor:
						self.dblist.append(DblistEntryComponent(titleID=row[0], text=row[1], title=row[1], filename=row[2]))
				elif self.dblist.mode == SEARCHPLAYLISTLIST:
					cursor.execute("SELECT playlist_id, playlist_title, playlist_filename FROM Playlists WHERE playlist_filename LIKE '%s' ORDER BY upper(playlist_title);" % (queryString))
					for row in cursor:
						self.dblist.append(DblistEntryComponent(titleID=row[0], text=row[1], title=row[1], filename=row[2]))
				elif self.dblist.mode == ARTISTLIST:
					if len(self.dbArtistList) == 0:
						if config.plugins.yampmusicplayer.dbArtistReduce.value:
							cursor.execute("SELECT Artists.artist_id, Artists.artistShort, COUNT (*) FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id GROUP BY Artists.artistShort ORDER BY upper(Artists.artistShort);")
						else:
							cursor.execute("SELECT Artists.artist_id, Artists.artist, COUNT (*) FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id GROUP BY Titles.artist_id ORDER BY upper(Artists.artist);")
						for row in cursor:
							self.dblist.append(DblistEntryComponent(text="%s (%d)" % (row[1], row[2]), artistID=row[0], artist=row[1]))
						self.dbArtistList = self.dblist.list[:]  # cache artist list
					else:
						self.dblist.list = self.dbArtistList[:]
				elif self.dblist.mode == SEARCHARTISTLIST:
					cursor.execute("SELECT Artists.artist_id, Artists.artist, COUNT (*) FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id WHERE Artists.artist LIKE '%s' GROUP BY Titles.artist_id ORDER BY upper(Artists.artist);" % (queryString))
					for row in cursor:
						self.dblist.append(DblistEntryComponent(text="%s (%d)" % (row[1], row[2]), artistID=row[0], artist=row[1]))
				elif self.dblist.mode == ALBUMLIST:
					if len(self.dbAlbumList) == 0:
						cursor.execute("SELECT Albums.album_id, Albums.album, Artists.artist, Titles.filename, COUNT (*) FROM Titles INNER JOIN Albums ON Titles.album_id = Albums.album_id INNER JOIN Artists ON Titles.albumartist_id = Artists.artist_id GROUP By Albums.album_id ORDER BY upper(Albums.album);")
						for row in cursor:
							try:
								self.dblist.append(DblistEntryComponent(text="%s - %s (%d)" % (row[1], row[2], row[4]), albumID=row[0], album=row[1], artist=row[2], filename=row[3]))
							except Exception:
								LOG('YampScreen: buildDbMenuList: APPEND: EXCEPT: filename: %s' % ('filename'), 'err')
						self.dbAlbumList = self.dblist.list[:]  # cache album list
					else:
						self.dblist.list = self.dbAlbumList[:]
				elif self.dblist.mode == SEARCHALBUMLIST:
					cursor.execute("SELECT Albums.album_id, Albums.album, COUNT (*) FROM Titles INNER JOIN Albums ON Titles.album_id = Albums.album_id WHERE Albums.album LIKE '%s' GROUP BY Titles.album_id ORDER BY Albums.album;" % (queryString))
					for row in cursor:
						self.dblist.append(DblistEntryComponent(text="%s (%d)" % (row[1], row[2]), albumID=row[0], album=row[1]))
				elif self.dblist.mode == ARTISTALBUMLIST:
					cursor.execute("SELECT Albums.album_id, Albums.album FROM Titles INNER JOIN Albums ON Titles.album_id = Albums.album_id WHERE Titles.artist_id = %d GROUP BY Titles.album_id ORDER BY upper(Albums.album);" % (query))
					for row in cursor:
						self.dblist.append(DblistEntryComponent(text="%s" % (row[1]), albumID=row[0], album=row[1]))
				elif self.dblist.mode == GENREALBUMLIST:
					cursor.execute("SELECT Albums.album_id, Albums.album FROM Titles INNER JOIN Albums ON Titles.album_id = Albums.album_id WHERE Titles.genre_id = %d GROUP BY Titles.album_id ORDER BY upper(Albums.album);" % (query))
					for row in cursor:
						self.dblist.append(DblistEntryComponent(text="%s" % (row[1]), albumID=row[0], album=row[1]))
				elif self.dblist.mode == GENRELIST:
					cursor.execute("SELECT Genres.genre_id,Genres.genre, COUNT (*) FROM Titles INNER JOIN Genres ON Titles.genre_id = Genres.genre_id GROUP BY Titles.genre_id ORDER BY Genres.genre;")
					for row in cursor:
						self.dblist.append(DblistEntryComponent(text="%s (%d)" % (row[1], row[2]), genreID=row[0], genre=row[1]))
				elif self.dblist.mode == SEARCHGENRELIST:
					cursor.execute("SELECT Genres.genre_id,Genres.genre, COUNT (*) FROM Titles INNER JOIN Genres ON Titles.genre_id = Genres.genre_id WHERE Genres.genre LIKE '%s' GROUP BY Titles.genre_id ORDER BY Genres.genre;" % (queryString))
					for row in cursor:
						self.dblist.append(DblistEntryComponent(text="%s (%d)" % (row[1], row[2]), genreID=row[0], genre=row[1]))
				elif self.dblist.mode == DATELIST:
					try:
						cursor.execute("SELECT Dates.date_id,Dates.date, COUNT (*) FROM Titles INNER JOIN Dates ON Titles.date_id = Dates.date_id GROUP BY Titles.date_id ORDER BY Dates.date;")
						for row in cursor:
							self.dblist.append(DblistEntryComponent(text="%s (%d)" % (row[1], row[2]), dateID=row[0], date=row[1]))
					except Exception:
						LOG('YampScreen: buildDbMenuList: EXCEPT NO DATE IN DATABASE', 'err')
						self.session.open(MessageBox, _("No Year in Database, see Documentation"), type=MessageBox.TYPE_INFO, timeout=20)
				elif self.dblist.mode == SEARCHDATELIST:
					try:
						cursor.execute("SELECT Dates.date_id,Dates.date, COUNT (*) FROM Titles INNER JOIN Dates ON Titles.date_id = Dates.date_id WHERE Dates.date LIKE '%s' GROUP BY Titles.date_id ORDER BY Dates.date;" % (queryString))
						for row in cursor:
							self.dblist.append(DblistEntryComponent(text="%s (%d)" % (row[1], row[2]), genreID=row[0], genre=row[1]))
					except Exception:
						pass
				elif self.dblist.mode == TITLELIST:
					if len(self.dbTitleList) == 0:
						cursor.execute("SELECT title_id, title, filename, Titles.artist_id, Artists.artist, Titles.album_id, Albums.album, Titles.genre_id, Genres.genre, date, length, tracknr, sref FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id INNER JOIN Albums ON Titles.album_id = Albums.album_id INNER JOIN Genres ON Titles.genre_id = Genres.genre_id ORDER BY upper(title), upper(Albums.album);")
						for row in cursor:
							self.dblist.append(DblistEntryComponent(titleID=row[0], title=row[1], filename=row[2], artistID=row[3], artist=row[4], albumID=row[5], album=row[6], genreID=row[7], genre=row[8], date=row[9], length=row[10], tracknr=row[11], ref=row[12]))
						self.dbTitleList = self.dblist.list[:]  # cache title list
					else:
						self.dblist.list = self.dbTitleList[:]
				elif self.dblist.mode == ARTISTTITLELIST:
					sqlBase = 'SELECT title_id, title, filename, Titles.artist_id, Artists.artist, Titles.album_id, Albums.album, Titles.genre_id, Genres.genre, date, length, tracknr, sref FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id INNER JOIN Albums ON Titles.album_id = Albums.album_id INNER JOIN Genres ON Titles.genre_id = Genres.genre_id WHERE '
					sqlOrder = ' ORDER BY upper(title), upper(Albums.album);'
					if query == -1:
						return
					if config.plugins.yampmusicplayer.dbArtistReduce.value:
						sql = sqlBase + self.getSqlArtistShort(cursor, query)
					else:
						sql = sqlBase + 'Titles.artist_id = %d ' % (query)
					try:
						if config.plugins.yampmusicplayer.titleOnlyOnceInSelection.value:
							sql = sql + 'GROUP BY upper(title)' + sqlOrder
						else:
							sql = sql + sqlOrder
						cursor.execute(sql)
					except Exception:
						pass  # prevent green screen after update without "artistShort"
					try:
						for row in cursor:
							self.dblist.append(DblistEntryComponent(titleID=row[0], title=row[1], filename=row[2], artistID=row[3], artist=row[4], albumID=row[5], album=row[6], genreID=row[7], genre=row[8], date=row[9], length=row[10], tracknr=row[11], ref=row[12]))
					except Exception:
						pass  # prevent green screen after update without "artistShort"
				elif self.dblist.mode == ALBUMTITLELIST:
					cursor.execute("SELECT title_id, title, filename, Titles.artist_id, Artists.artist, Titles.album_id, Albums.album, Titles.genre_id, Genres.genre, date, length, tracknr, sref FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id INNER JOIN Albums ON Titles.album_id = Albums.album_id INNER JOIN Genres ON Titles.genre_id = Genres.genre_id WHERE Titles.album_id = %d ORDER BY tracknr, filename;" % (query))
					for row in cursor:
						if row[11] > 999:
							txtTrack = str(row[11] / 1000) + '-' + str(row[11] % 1000)
						else:
							txtTrack = str(row[11])
						self.dblist.append(DblistEntryComponent(txtTrack + '. ', titleID=row[0], title=row[1], filename=row[2], artistID=row[3], artist=row[4], albumID=row[5], album=row[6], genreID=row[7], genre=row[8], date=row[9], length=row[10], tracknr=row[11], ref=row[12]))
				elif self.dblist.mode == GENRETITLELIST:
					if config.plugins.yampmusicplayer.titleOnlyOnceInSelection.value:
						cursor.execute("SELECT min(title_id), title, filename, Titles.artist_id, Artists.artist, Titles.album_id, Albums.album, Titles.genre_id, Genres.genre, date, length, tracknr, sref FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id INNER JOIN Albums ON Titles.album_id = Albums.album_id INNER JOIN Genres ON Titles.genre_id = Genres.genre_id WHERE Titles.genre_id = %d GROUP BY upper(title);" % (query))
					else:
						cursor.execute("SELECT title_id, title, filename, Titles.artist_id, Artists.artist, Titles.album_id, Albums.album, Titles.genre_id, Genres.genre, date, length, tracknr, sref FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id INNER JOIN Albums ON Titles.album_id = Albums.album_id INNER JOIN Genres ON Titles.genre_id = Genres.genre_id WHERE Titles.genre_id = %d ORDER BY upper(title), upper(Albums.album);" % (query))
					for row in cursor:
						self.dblist.append(DblistEntryComponent(titleID=row[0], title=row[1], filename=row[2], artistID=row[3], artist=row[4], albumID=row[5], album=row[6], genreID=row[7], genre=row[8], date=row[9], length=row[10], tracknr=row[11], ref=row[12]))
				elif self.dblist.mode == DATETITLELIST:
					if config.plugins.yampmusicplayer.titleOnlyOnceInSelection.value:
						cursor.execute("SELECT min(title_id), title, filename, Titles.artist_id, Artists.artist, Titles.album_id, Albums.album, Titles.genre_id, Titles.date_id, Genres.genre, Dates.date, length, tracknr, sref FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id INNER JOIN Albums ON Titles.album_id = Albums.album_id INNER JOIN Genres ON Titles.genre_id = Genres.genre_id INNER JOIN Dates ON Titles.date_id = Dates.date_id WHERE Titles.date_id = %d GROUP BY upper(title);" % (query))
					else:
						cursor.execute("SELECT title_id, title, filename, Titles.artist_id, Artists.artist, Titles.album_id, Albums.album, Titles.genre_id, Titles.date_id, Genres.genre, Dates.date, length, tracknr, sref FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id INNER JOIN Albums ON Titles.album_id = Albums.album_id INNER JOIN Genres ON Titles.genre_id = Genres.genre_id INNER JOIN Dates ON Titles.date_id = Dates.date_id WHERE Titles.date_id = %d GROUP BY upper(title);" % (query))
					for row in cursor:
						self.dblist.append(DblistEntryComponent(titleID=row[0], title=row[1], filename=row[2], artistID=row[3], artist=row[4], albumID=row[5], album=row[6], genreID=row[7], genre=row[9], date=row[10], length=row[11], tracknr=row[12], ref=row[13]))
				elif self.dblist.mode == SEARCHTITLELIST:
					cursor.execute("SELECT title_id, title, filename, Titles.artist_id, Artists.artist, Titles.album_id, Albums.album, Titles.genre_id, Genres.genre, date, length, tracknr, sref FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id INNER JOIN Albums ON Titles.album_id = Albums.album_id INNER JOIN Genres ON Titles.genre_id = Genres.genre_id WHERE Titles.title LIKE '%s' ORDER BY upper(title), upper(Albums.album);" % (queryString))
					for row in cursor:
						self.dblist.append(DblistEntryComponent(titleID=row[0], title=row[1], filename=row[2], artistID=row[3], artist=row[4], albumID=row[5], album=row[6], genreID=row[7], genre=row[8], date=row[9], length=row[10], tracknr=row[11], ref=row[12]))
				elif self.dblist.mode == SEARCHFILELIST:
					cursor.execute("SELECT title_id, title, filename, Titles.artist_id, Artists.artist, Titles.album_id, Albums.album, Titles.genre_id, Genres.genre, date, length, tracknr, sref FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id INNER JOIN Albums ON Titles.album_id = Albums.album_id INNER JOIN Genres ON Titles.genre_id = Genres.genre_id WHERE Titles.filename LIKE '%s' ORDER BY upper(title), upper(Albums.album);" % (queryString))
					for row in cursor:
						self.dblist.append(DblistEntryComponent(titleID=row[0], title=row[1], filename=row[2], artistID=row[3], artist=row[4], albumID=row[5], album=row[6], genreID=row[7], genre=row[8], date=row[9], length=row[10], tracknr=row[11], ref=row[12]))
				elif self.dblist.mode == SEARCHARTISTTITLELIST:
					if config.plugins.yampmusicplayer.titleOnlyOnceInSelection.value:
						cursor.execute("SELECT min(title_id), title, filename, Titles.artist_id, Artists.artist, Titles.album_id, Albums.album, Titles.genre_id, Genres.genre, date, length, tracknr, sref FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id INNER JOIN Albums ON Titles.album_id = Albums.album_id INNER JOIN Genres ON Titles.genre_id = Genres.genre_id WHERE Artists.artist LIKE '%s' GROUP BY upper(title);" % (queryString))
					else:
						cursor.execute("SELECT title_id, title, filename, Titles.artist_id, Artists.artist, Titles.album_id, Albums.album, Titles.genre_id, Genres.genre, date, length, tracknr, sref FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id INNER JOIN Albums ON Titles.album_id = Albums.album_id INNER JOIN Genres ON Titles.genre_id = Genres.genre_id WHERE Artists.artist LIKE '%s' ORDER BY upper(title), upper(Albums.album);" % (queryString))
					for row in cursor:
						self.dblist.append(DblistEntryComponent(titleID=row[0], title=row[1], filename=row[2], artistID=row[3], artist=row[4], albumID=row[5], album=row[6], genreID=row[7], genre=row[8], date=row[9], length=row[10], tracknr=row[11], ref=row[12]))
				elif self.dblist.mode == SEARCHALBUMTITLELIST:
					cursor.execute("SELECT title_id, title, filename, Titles.artist_id, Artists.artist, Titles.album_id, Albums.album, Titles.genre_id, Genres.genre, date, length, tracknr, sref FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id INNER JOIN Albums ON Titles.album_id = Albums.album_id INNER JOIN Genres ON Titles.genre_id = Genres.genre_id WHERE Albums.album LIKE '%s' ORDER BY tracknr, filename;" % (queryString))
					for row in cursor:
						self.dblist.append(DblistEntryComponent(titleID=row[0], title=row[1], filename=row[2], artistID=row[3], artist=row[4], albumID=row[5], album=row[6], genreID=row[7], genre=row[8], date=row[9], length=row[10], tracknr=row[11], ref=row[12]))
				self.dblist.updateList()
				if len(self.dblist) > 1:
					self.dblist.moveToIndex(1)
			cursor.close()
			con.close()
			self.currDblist = DblistStackEntry(self.dblist.mode, query, self.dblist.getSelectionIndex(), menutitle, queryString)  # for refresh after DB changes

	def getSqlArtistShort(self, cursor, artistID):
		sql = 'SELECT Artists.artistShort from Artists WHERE artist_id = %d;' % (artistID)
		cursor.execute(sql)
		row = cursor.fetchone()  # Name of ArtistShort
		sql2 = 'SELECT Artists.artist_id FROM Artists WHERE artistShort = "%s";' % (row[0])
		cursor.execute(sql2)
		row2 = cursor.fetchall()  # get List of Tuples of all artistIds of artistShort
		SQL = ''
		for id in row2:
			SQL += 'OR Titles.artist_id = %d ' % (id[0])
		SQL = SQL.replace('OR', '', 1)
		return (SQL)

	def updateDbMenuList(self):
		self.dbTitleList = []
		self.dbArtistList = []
		self.dbAlbumList = []
		self.buildDbMenuList(mode=self.currDblist.mode, query=self.currDblist.query, menutitle=self.currDblist.menutitle, queryString=self.currDblist.queryString)

	def pushDblistStack(self, sel):
		self.dbStack.append(DblistStackEntry(mode=self.currDblist.mode, query=self.currDblist.query, selIndex=sel, menutitle=self.currDblist.menutitle, queryString=self.currDblist.queryString))

	def popDblistStack(self):
		entry = self.dbStack[-1]
		del self.dbStack[-1]
		return entry

# Methods for reading external playlists (.m3u, .pls, .e2pls) and writing e2pls playlists
	def addPlaylistParser(self, parser, extension):
		self.playlistparsers[extension] = parser

	def calcLenPlaylist(self):
		if config.plugins.yampmusicplayer.showPlayListLen.value:
			songhours, songmin, songsec = 0, 0, 0
			try:
				totalSec = sum(secList)
				sec = totalSec % 60
				totalMin = sum(minList) + int(totalSec / 60)
				songmin = totalMin % 60
				songhours = totalMin / 60
			except Exception as e:
				LOG('YampScreen: calcLenPlaylist: EXCEPT1: %s' % (str(e)), 'err')
			try:
				self["playLen"].setText("%02d:%02d:%02d" % (songhours, songmin, songsec))
			except Exception as e:
				LOG('YampScreen: calcLenPlaylist: EXCEPT2: %s' % (str(e)), 'err')

	def calcRemainPlaylist(self):
		if config.plugins.yampmusicplayer.showPlayListLen.value:
			try:
				fromidx = self.playlist.getSelectionIndex()
				self.totalSec = sum(secList[fromidx:])
				self.totalMin = sum(minList[fromidx:])
			except Exception as e:
				LOG('YampScreen: calcRemainPlaylist: EXCEPT: %s' % (str(e)), 'err')
			self.calcRemainPlaylistCyclic()

	def calcRemainPlaylistCyclic(self):
		currentSelectedPlaying = (self.playlist.getCurrentIndex() == self.playlist.getSelectionIndex()) and (self.playerState == STATE_PLAY)
		playedSec = self.playedSec if currentSelectedPlaying else 0
		songhours, songmin, songsec = 0, 0, 0,
		try:
			totalSec = self.totalSec - playedSec
			if totalSec < 0:
				totalSec = 0
			songsec = totalSec % 60
			totalMin = self.totalMin + int(totalSec / 60)
			songmin = totalMin % 60
			songhours = totalMin / 60
		except Exception as e:
			LOG('YampScreen: calcRemainPlaylistCyclic: EXCEPT1: %s' % (str(e)), 'err')
		try:
			self["playLenRem"].setText("%02d:%02d:%02d" % (songhours, songmin, songsec))
		except Exception as e:
			LOG('YampScreen: calcRemainPlaylistCyclic: EXCEPT2: %s' % (str(e)), 'err')

	def recalcLenListsComplete(self):
		self.setPlayListLenLists()
		self.calcLenPlaylist()

	def setPlayListLenLists(self):
		global secList, minList
		if config.plugins.yampmusicplayer.showPlayListLen.value:
			minList, secList = [], []
			songmin, songsec = 0, 0
			try:
				ppath = ""
				for x in range(len(self.playlist)):
					try:
						ppath = self.playlist.getServiceRefList()[x].getPath()
					except Exception as e:
						LOG('YampScreen: setPlayListLenLists: EXCEPT1: %s' % (str(e)), 'err')
					try:
						songmin, songsec = self.getSongLength(ppath)
					except Exception as e:
						LOG('YampScreen: setPlayListLenLists: EXCEPT2: %s' % (str(e)), 'err')
					secList.append(songsec)
					minList.append(songmin)
			except Exception as e:
				LOG('YampScreen: setPlayListLenLists: EXCEPT: %s' % (str(e)), 'err')

	def insertEntryLenLists(self, ref, newIdx):
		global secList, minList
		if config.plugins.yampmusicplayer.showPlayListLen.value:
			songmin, songsec = self.getSongLength(ref.getPath())
			secL = []
			minL = []
			secL.append(songsec)
			minL.append(songmin)
			secList = secList[:newIdx] + secL + secList[newIdx:]
			minList = minList[:newIdx] + minL + minList[newIdx:]

	def moveEntryLenLists(self, index, move, wrap):
		global secList, minList
		if config.plugins.yampmusicplayer.showPlayListLen.value:
			lenPlaylist = len(self.playlist)
			if index + move >= lenPlaylist:  # move behind last
				if wrap:
					newIndex = move - lenPlaylist + index
				else:
					newIndex = lenPlaylist - 1
			elif index + move < 0:
				if wrap:
					newIndex = lenPlaylist + index + move
				else:
					newIndex = 0
			else:
				newIndex = index + move
			secSav = secList[index]
			minSav = minList[index]
			secList = secList[:index] + secList[index + 1:]  # remove original
			secList.insert(newIndex, secSav)
			minList = minList[:index] + minList[index + 1:]  # remove original
			minList.insert(newIndex, minSav)

	def loadLastPlaylist(self):
		totalMin = totalSec = 0
		self.YampParserE2pls = YampParserE2pls()
		plist = self.YampParserE2pls.open(resolveFilename(SCOPE_CONFIG, "yamp.e2pls"))
		global secList, minList
		secList = []
		minList = []
		if plist:
			for x in plist:
				try:
					if config.plugins.yampmusicplayer.showPlayListLen.value:
						songmin, songsec = self.getSongLength(x.getPath())
						secList.append(songsec)
						minList.append(songmin)
				except Exception as e:
					LOG('YampScreen: loadLastPlaylist: EXCEPT: %s' % (str(e)), 'err')
				self.playlist.addService(x.ref)  # No layout change for playlist
			lastPlayed = config.plugins.yampmusicplayer.lastPlaylistIndex.value
			self.playlist.setCurrentPlaying(lastPlayed)
			self.playlist.stopService()  # show stop icon
			self.playerState = STATE_STOP  # inhibit screen saver
			self.calcLenPlaylist()
			list = self.YampParserE2pls.open(resolveFilename(SCOPE_CONFIG, "yampsl.e2pls"))
			if list:
				del self.playlist.shadowList[:]
				for x in list:
					self.playlist.addShadowService(x.ref)
			self.playlist.updateList()
			self.playlist.isShuffeled = config.plugins.yampmusicplayer.shuffle.value
			self.setShuffleButton()
			self.switchToPlayList()

	def sortPlaylist(self, mode):
		self.playlist.sortList(mode)
		self.setShuffleButton()

	def searchPlaylist(self):
		self.virtKeyboardActive = True
		self.session.openWithCallback(self.searchPlaylistCallback, VirtualKeyBoard, title=_("YAMP - Please enter query:"), text=self.lastPlaylistSearch)

	def searchPlaylistCallback(self, choice):
		if choice is not None:
			self.lastPlaylistSearch = choice.lower()
			self.playlist.searchList(self.lastPlaylistSearch)
			self.updatePlaylistInfo()
		self.virtKeyboardActive = False

	def savePlaylist(self, mode):
		self.par1 = mode
		self.virtKeyboardActive = True
		self.session.openWithCallback(self.savePlaylistCallback, VirtualKeyBoard, title=_("YAMP - Please enter filename:"), text=self.extPlaylistName)

	def savePlaylistCallback(self, name):
		if name is not None:
			name = name.strip()
			if not name:
				name = strftime("%y%m%d-%H%M%S")
			self.extPlaylistName = name
			# Save e2pls
			if self.par1 == 1 or self.par1 == 3:
				fname = name + ".e2pls"
				pathfilename = join(config.plugins.yampmusicplayer.playlistPath.value, fname)
				self.YampParserE2pls = YampParserE2pls()
				self.YampParserE2pls.clear()
				for x in self.playlist.list:
					self.YampParserE2pls.addService(ServiceReference(x[0]))
				try:
					nok = self.YampParserE2pls.save(pathfilename)
				except Exception as e:
					nok = 5
					LOG('YampScreen: savePlaylistCallback e2pls: nok: %d EXCEPT: %s' % (nok, str(e)), 'err')
				if nok:
					self.session.open(MessageBox, _('Playlist saving as %s failed') % (fname), type=MessageBox.TYPE_INFO, timeout=7)
				else:
					self.session.open(MessageBox, _('Playlist saved as %s') % (fname), type=MessageBox.TYPE_INFO, timeout=7)
				self.addFileToDb(pathfilename)
			# Save m3u
			if self.par1 == 2 or self.par1 == 3:
#				LOG('YampScreen: savePlaylistCallback: m3u', 'err')
				fname = name + ".m3u"
				pathfilename = join(config.plugins.yampmusicplayer.playlistPath.value, fname)
				try:
					self.YampParserM3u = YampParserM3u()
				except Exception as e:
					LOG('YampScreen: savePlaylistCallback m3u: self.YampParserM3u: EXCEPT: %s' % (str(e)), 'err')
				try:
					self.YampParserM3u.clear()
				except Exception as e:
					LOG('YampScreen: savePlaylistCallback m3u: clear: EXCEPT: %s' % (str(e)), 'err')
				try:
					for x in self.playlist.list:
						self.YampParserM3u.addService(ServiceReference(x[0]))
				except Exception as e:
					LOG('YampScreen: savePlaylistCallback m3u: for x : EXCEPT: %s' % (str(e)), 'err')
				try:
					nok = self.YampParserM3u.save(pathfilename)
				except Exception as e:
					nok = 5
					LOG('YampScreen: savePlaylistCallback m3u: nok: %d EXCEPT: %s' % (nok, str(e)), 'err')
				if nok:
					self.session.open(MessageBox, _('Playlist saving as %s failed') % (fname), type=MessageBox.TYPE_INFO, timeout=7)
				else:
					self.session.open(MessageBox, _('Playlist saved as %s') % (fname), type=MessageBox.TYPE_INFO, timeout=7)
					self.addFileToDb(pathfilename)
			self.filelist.refresh()
		self.virtKeyboardActive = False

	def deletePlaylist(self):
		playlist = self.filelist.getFilename()
		if exists(playlist):
			remove(playlist)
			self.filelist.refresh()

# More methods for playlists and playlist entries
	def checkSkipShowHideLock(self):  # method override from InfoBarGenerics
		if not self.CheckIfNormalSongStarted():
			return
		if self.seekstate == self.SEEK_STATE_PAUSE:
			self.playlist.pauseService()
			self.playerState = STATE_PAUSE
		elif self.seekstate == self.SEEK_STATE_PLAY:
			self.playlist.playService()
			self.playerState = STATE_PLAY

	def doEofInternal(self, playing):
		if playing and self.playerState != STATE_STOP:
			self.nextEntry()
		else:
			self.hideScreenSaver()

	def deleteEntry(self):
		global minList, secList
		if len(self.playlist) > 0:
			deletedCurrentEntry = False
			if self.currList == "playlist":
				index = self.playlist.getSelectionIndex()
			else:
				index = self.playlist.getCurrentIndex()
			if index == self.playlist.getCurrentIndex():
				deletedCurrentEntry = True
			self.playlist.deleteService(index)
			self.playlist.updateList()
			try:
				minList = minList[:index] + minList[index + 1:]
				secList = secList[:index] + secList[index + 1:]
				self.calcLenPlaylist()
			except Exception:
				pass
			self.updateNextSong()
			if len(self.playlist) == 0:
				self.switchToFileList()
			elif deletedCurrentEntry:
				if (self.playerState == STATE_PLAY) and (len(self.playlist) > 0):
					self.nextEntry()  # only in play
			self.updateLCDInfo()
			self.updateNextSong()

	def checkIsVideo(self, filepath):
		try:
			ext = splitext(filepath)[1].lower()
			return False if ext in AUDIO_EXTENSIONS else True
		except Exception as e:
			LOG('YampScreen: checkIsVideo: EXCEPT: %s' % (str(e)), 'err')
		return False

	def insertBlankVideo(self):
		try:
			self.blankVideoTimer.start(config.plugins.yampmusicplayer.blankVideoDelay.value, True)
		except Exception as e:
			LOG('YampScreen: insertblankvideo: EXCEPT1: %s' % (str(e)), 'err')
		try:
			self.blankVideoInserted = self.playlist.getCurrentIndex() + 1
		except Exception as e:
			LOG('YampScreen: insertblankvideo: EXCEPT2: %s' % (str(e)), 'err')
		try:
			self.insertService(self.blankVideoInserted, self.filelistint.getServiceRef())
		except Exception as e:
			LOG('YampScreen: insertblankvideo: EXCEPT4: %s' % (str(e)), 'err')
		try:
			currRef = self.playlist.getServiceRefList()[self.blankVideoInserted]
			self.playlist.setCurrentPlaying(self.blankVideoInserted)
			self.session.nav.playService(currRef)
		except Exception as e:
			LOG('YampScreen: insertblankvideo: EXCEPT5: %s' % (str(e)), 'err')
		try:
			self.previousIsVideo = False
		except Exception as e:
			LOG('YampScreen: insertblankvideo: EXCEPT6: %s' % (str(e)), 'err')

	def stopBlankVideo(self):
		try:
			lx = self.filelistint.getFileList()
			blankRef = lx[0][0][0]
			refList = self.playlist.getServiceRefList()
			foundIdx = -1
			if refList[self.blankVideoInserted] == blankRef:
				foundIdx = self.blankVideoInserted
			else:
				for x in range(len(refList)):
					if refList[x] == blankRef:
						foundIdx = x
						break
			if foundIdx > -1:
				self.playlist.deleteService(foundIdx)
		except Exception as e:
			LOG('YampScreen: stopBlankVideo: EXCEPT1: %s' % (str(e)), 'err')
		try:
			if self.previousPressed:
				self.previousEntry()
			else:
				self.nextEntry()
		except Exception as e:
			LOG('YampScreen: stopBlankVideo: EXCEPT2: %s' % (str(e)), 'err')

	def changeEntry(self, index):
		self.playedSec = 0
		newIsVideo = ""
		try:
			newRef = self.playlist.getServiceRefList()[index]
			newIsVideo = self.checkIsVideo(newRef.getPath())
		except Exception as e:
			LOG('YampScreen: changeEntry: newIsVideo: EXCEPT: %s' % (str(e)), 'err')
		if config.plugins.yampmusicplayer.insertBlankVideo.value and not newIsVideo and self.previousIsVideo and (self.blankVideoInserted == -1) and not self.previousPressed:
			self.insertBlankVideo()
		else:
			if newIsVideo:
				self.showHideVideoPreview(True)  # changeEntry is video
				self.currentIsVideo = True
				if not self.specialScreenActive():
					# Video Start Mode full or preview
					if self.videoStartMode == "manual":
						self.resetScreenSaverTimer()  # hide SS and Start SS Timer
						self.screenSaverTimer.stop()
						self.setSaverButton()
						if self.isVideoFullScreen:
							self.hideYampScreenShowVideo()  # display Title/Lyrics-Screen
					elif self.videoStartMode == "immediate":
						self.hideYampScreenShowVideo()
						if not self.screenSaverActive:
							self.startScreenSaverTimer()  # self.resetScreenSaverTimer()
					else:  # start video after time
						if self.screenSaverActive:
							self.hideYampScreenShowVideo()
						else:
							self.resetScreenSaverTimer()
			else:
				# Music, no Video
				self.showHideVideoPreview(False)  # changentry music

				if not self.specialScreenActive():
					self.showYampScreenHideVideo()
					if not self.screenSaverActive:
						self.resetScreenSaverTimer()
				self.resetSlideTimer()
			self.previousPressed = False
			self.changeEntryNormal(index)

	def changeEntryNormal(self, index):
		samePlaying = False
		currentPlaying, nextPlaying = None, None
		try:
			self.blankVideoInserted = -1
			currentPlaying = self.session.nav.getCurrentlyPlayingServiceReference()
			nextPlaying = self.playlist.getServiceRefList()[index]
		except Exception as e:
			LOG('YampScreen: changeEntryNormal: currentPlaying: EXCEPT1: %s' % (str(e)), 'err')
		try:
			if currentPlaying is not None and nextPlaying is not None:
				samePlaying = currentPlaying == nextPlaying
				serviceHandler = eServiceCenter.getInstance()
				info = serviceHandler.info(currentPlaying)
				nameCurr = info and info.getName(currentPlaying) or "."
				info = serviceHandler.info(nextPlaying)
				nameNext = info and info.getName(nextPlaying) or "."
				LOG('YampScreen: changeEntryNormal: currentPlaying: %s nextPlaying: %s' % (nameCurr, nameNext), 'all')
			LOG('YampScreen: changeEntryNormal: samePlaying: %s' % (samePlaying), 'all')
		except Exception as e:
			LOG('YampScreen: changeEntryNormal: samePlaying: %s : EXCEPT: %s' % (samePlaying, str(e)), 'err')
		self.playlist.setCurrentPlaying(index)
		self.calcRemainPlaylist()
		if len(self.playlist.getServiceRefList()) == 1 or samePlaying:
			self.playlist.stopService()
			self.playerState = STATE_STOP  # check!!!
			self.session.nav.stopService()
			LOG('YampScreen: changeEntryNormal: Len = 1 or samePlaying: Stop', 'all')
			if not self.repeat and self.session.nav.getCurrentlyPlayingServiceReference() is not None:
				LOG('YampScreen: changeEntryNormal: Len = 1: Stop complete', 'all')
				self.stopEntry()
				self.currentIsVideo = False
				return

		if len(self.playlist.getServiceRefList()):
			currRef = self.playlist.getServiceRefList()[self.playlist.getCurrentIndex()]
			self.session.nav.playService(currRef)
			self.setSeekState(self.SEEK_STATE_PLAY)
			self.playerState = STATE_PLAY
			self.currentIsVideo = self.checkIsVideo(currRef.getPath())
			if self.eofbugTimer.isActive():
				self.eofbugTimer.stop()
			self.playPosition = -1
			self.playLength = -1
			self.eofbugTimer.start(1000)

	def showCompleteScreen(self):
		self["title"].show()
		self["leftContentTitle"].show()
		self["filelist"].show()
		if self.leftContent == "dblist":
			self["filelist"].hide()
			self["dblist"].show()
		else:
			self["filelist"].show()
			self["dblist"].hide()
		self["rightContentTitle"].show()
		self["playlist"].show()
		self["actPlayNumber"].show()
		self.showHideClock()
		self["repeat"].show()
		self["shuffle"].show()
		self["saver"].show()
		self.setHelpTexts()
		self["key_red"].show()
		self["key_green"].show()
		self["key_yellow"].show()
		self["key_blue"].show()

	def hideScreenExceptTitleInfo(self):
		self["title"].hide()
		self["leftContentTitle"].hide()
		self["filelist"].hide()
		self["dblist"].hide()
		self["rightContentTitle"].hide()
		self["playlist"].hide()
		self["actPlayNumber"].hide()
		self["repeat"].hide()
		self["shuffle"].hide()
		self["saver"].hide()
		self.setHelpTexts()
		self["key_red"].hide()
		self["key_green"].hide()
		self["key_yellow"].hide()
		self["key_blue"].hide()

	def showYampScreenHideVideo(self):
		if not self.specialScreenActive():
			self.show()
		self.isVideoFullScreen = False
		if self.screenSaverActive:
			self.showHideClock('SS')
		else:
			self.showHideClock()

	def hideYampScreenShowVideo(self):  # show Video
		if self.specialScreenActive():
			return
		if not self.specialScreenActive():
			self.hide()
		self.showHideClock("Video")
		self.isVideoFullScreen = True
		autoStartTime = config.plugins.yampmusicplayer.showTimeVideoTitle.value
		self.displayHideLyricsLine()
		if autoStartTime > 0:
			self.session.openWithCallback(self.videoTitleClosedCB, YampVideoTitleV33, self, autoStartTime=autoStartTime)
		else:
			self.session.openWithCallback(self.videoLyricsClosedCB, YampVideoLyricsV33, self)

	def videoTitleClosedCB(self, param):
		try:  # because sometimes "modal open are allowed only from a screen which is modal!" is created, reason unknown
			if param == 'startupTimerTimeout' or param == 'keyAudio':
				if self.currentIsVideo:
					self.session.openWithCallback(self.videoLyricsClosedCB, YampVideoLyricsV33, self)
			elif param == 'updateSongInfo':
				pass
			elif param == 'keyClose':
				self.ok()
			elif param == 'keyOk':
				self.ok()
			elif param == 'keyUp':
				self.moveup()
			elif param == 'keyDown':
				self.movedown()
			elif param == 'keyMoveTop':
				self.skipToListbegin()
			elif param == 'keyMoveEnd':
				self.skipToListend()
			elif param == 'keyMenu':
				self.showYampScreenHideVideo()
				self.showMenu()
			elif param == 'keyInfo':
				self.showLyrics()
			elif param == 'keyStop':
				pass
		except Exception as e:
			pass
#			LOG('YampScreen: videoTitleClosedCB: EXCEPT: %s' % (str(e)), 'err')

	def videoLyricsClosedCB(self, param):
		try:  # because sometimes "modal open are allowed only from a screen which is modal!" is created, reason unknown
			if param == 'updateSongInfo':
				pass
			elif param == 'keyAudio':
				if self.currentIsVideo:
					self.session.openWithCallback(self.videoTitleClosedCB, YampVideoTitleV33, self, 0)
			elif param == 'keyClose':
				self.ok()
			elif param == 'keyOk':
				self.ok()
			elif param == 'keyUp':
				self.moveup()
			elif param == 'keyDown':
				self.movedown()
			elif param == 'keyMoveTop':
				self.skipToListbegin()
			elif param == 'keyMoveEnd':
				self.skipToListend()
			elif param == 'keyMenu':
				self.showYampScreenHideVideo()
				self.showMenu()
			elif param == 'keyInfo':
				self.showLyrics()
			elif param == 'keyStop':
				pass
		except Exception as e:
			LOG('YampScreen: videoLyricsClosedCB: EXCEPT: %s' % (str(e)), 'err')

	def showTVservice(self):
		if self.myOldService is not None and (self.TvAudio or self.Tv):
			self.session.nav.playService(self.myOldService)
			self.showHideVideoPreview(self.TvStart or self.Tv)  # showtvservice

	def stopEntry(self):
		self.playlist.stopService()
		self.playerState = STATE_STOP
		self.session.nav.stopService()
		self.playedSec = 0
		self.hideScreenSaver()
		self.showYampScreenHideVideo()
		self.showTVservice()  # stopentry

	def clearPlaylist(self):
		global minList, secList
		minList = []
		secList = []
		self["playLen"].setText('00:00:00')
		self["playLenRem"].setText('00:00:00')
		if len(self.playlist) > 0:
			self.stopEntry()
			self.playlist.clear()
			self.setShuffleButton()
			self.switchToFileList()
			self.updateLCDInfo()
			self.updateNextSong()

	def checkEOF(self):
		if self.blankVideoInserted != -1:
			return
		if self.playerState == STATE_PLAY:
			datalen, datapos = self.getSeekData()
			self.playLength = datalen
			if config.plugins.yampmusicplayer.showPlayListLen.value:
				self.playedSec = int(datapos / 90000)
				self.calcRemainPlaylistCyclic()
			if self.playPosition == datapos:
				self.nextEntry()
			else:
				self.playPosition = datapos
				if datalen and datapos and config.plugins.yampmusicplayer.gapCorrection.value:  # and not self.currentIsVideo:
					if (datalen - datapos) <= 945000:  # 90.000 = 1 second -> check gap for the last 10.5 seconds
						if not self.gapTimer.isActive():
							self.gapTimer.start(100)
		if self.eofbugTimer.isActive():
			self.eofbugTimer.stop()
		self.eofbugTimer.start(1000)

	def checkGap(self):
		try:
			gap = config.plugins.yampmusicplayer.gapCorrection.value
			datalen, datapos = self.getSeekData()
			if (datalen - datapos) <= (gap * 9000 + 4500):  # add 4500 = 0.05 seconds / software delay
				if self.CheckIfNormalSongStarted():
					self.nextEntry()
				self.gapTimer.stop()
		except Exception as e:
			LOG('YampScreen: checkGap: : EXCEPT: %s' % (str(e)), 'err')

	def getSeekData(self):
		service = self.session.nav.getCurrentService()
#		seek = service and service.seek()
		seek = service.seek()
		if seek is None:
			return (0, 0)
		playlen = seek.getLength()
		playpos = seek.getPlayPosition()
		if playlen[0] or playpos[0]:
			return (0, 0)
		return (playlen[1], playpos[1])

# Yamp Screen Saver
	def initScreenSaver(self, artist=''):
		LOG('YampScreen: initScreenSaver: Start: artist: %s' % (artist), 'all')
		# Blank Screensaver
		slidePath, artworkPath = "", ""
		if self.currentIsVideo:
			slidePath = yampDir + "saverblank/"
		# Standard Screensaver
		elif config.plugins.yampmusicplayer.screenSaverMode.value == "standard":
			slidePath = yampDir + "saver/"
		# Custom Screensaver
		elif config.plugins.yampmusicplayer.screenSaverMode.value == "custom":
			slidePath = config.plugins.yampmusicplayer.screenSaverSlidePath.value
		# Artwork Screensaver
		elif config.plugins.yampmusicplayer.screenSaverMode.value == "artwork":
			LOG('YampScreen: initScreenSaver: Artwork: artist %s' % (artist), 'all')
			filelist = []
			artworkPath = config.plugins.yampmusicplayer.screenSaverArtworkPath.value
			if artist:
				LOG('YampScreen: initScreenSaver: Artwork: artworkPath %s' % (artworkPath), 'all')
				slidePath = self.getArtistArtDir(artworkPath, artist)
				LOG('YampScreen: initScreenSaver: Artwork: slidePath %s' % (slidePath), 'all')
				try:
					filelist = self.fileListByExt(slidePath, COVER_EXTENSIONS, config.plugins.yampmusicplayer.screenSaverSubDirs.value, 500)
					LOG('YampScreen: initScreenSaver: len filelistArtistArt: %d' % (len(filelist)), 'spe2')
					LOG('YampScreen: initScreenSaver: filelistArtistArt: %s' % (filelist), 'spe2')
				except Exception:
					LOG('YampScreen: initScreenSaver: filelistArtistArt: EXCEPT: No artist-art files found for artist %s' % (artist), 'err')
			# artist name = "" or no pictures found: try default path
			try:
				if len(filelist) == 0:
					slidePath = artworkPath + 'Default/'
			except Exception as e:
				LOG('YampScreen: initScreenSaver: len(filelist): EXCEPT: %s' % (str(e)), 'err')
				slidePath = artworkPath + 'Default/'
		# Blank Screensaver
		else:
			slidePath = yampDir + "saverblank/"
		if not exists(slidePath):
			slidePath = yampDir + "saver/"  # fallback if no images
		LOG('YampScreen: initScreenSaver: self.slidePath: %s slidePath: %s artist: %s' % (self.slidePath, slidePath, artist), 'all')
		if (self.slidePath != slidePath):
			try:
				LOG('YampScreen: initScreenSaver: New slidePath: %s' % (slidePath), 'all')
			except Exception:
				pass
			self.slidePath = slidePath
			slideList = []
			slideIndex = 0
			# Build Filelists and Slidelists
			if slidePath == yampDir + "saverblank/":  # blank
				slideList.append(join(self.slidePath, "black.png"))
			# custom or artistart screensaver
			else:
				fileList = self.buildFileList()  # scan folders (including subfolders), create filelist
				for filename in fileList:
					try:
						if splitext(filename)[1].lower() in COVER_EXTENSIONS:
							fullname = join(self.slidePath, filename)
							if isfile(fullname) and stat(fullname).st_size > 500:
								slideList.append(fullname)
					except Exception as e:
						LOG('YampScreen: initScreenSaver: filename: EXCEPT: %s' % (str(e)), 'err')
				LOG('\nYampScreen: initScreenSaver: before blacklist: len(slideList): %d \nslideList: %s' % (len(slideList), slideList), 'spe2')
				try:
					if config.plugins.yampmusicplayer.screenSaverMode.value == "artwork":
						slidePath = artworkPath
					slideList = self.checkBlackList(slideList, slidePath)
					LOG('\nYampScreen: initScreenSaver: after blacklist: len(slideList): %d \nslideList: %s' % (len(slideList), slideList), 'spe2')
				except Exception as e:
					LOG('YampScreen: initScreenSaver: call blacklist: EXCEPT: %s' % (str(e)), 'err')
			sorting = config.plugins.yampmusicplayer.screenSaverSort.value
			if sorting == 'sortA':
				slideList.sort()
			elif sorting == 'sortZ':
				slideList.sort(reverse=True)
			elif sorting == 'shuffle':
				shuffle(slideList)
			ind = 0
			for slide in slideList:
				if slide == config.plugins.yampmusicplayer.lastSlide.value:
					slideIndex = ind - 1
					break
				ind += 1
			if len(slideList) == 0:
				slideList.append(join(yampDir + "saverblank/", "black.png"))  #delete old pic on config change, if list empty
			self["screenSaver"].setList(slideList, slideIndex, showImmediate=True)

	def checkBlackList(self, slidelist, basepath):
		try:
			blackFilePath = join(basepath, 'blacklist.txt')
			if not access(blackFilePath, R_OK):
				return slidelist
			with open(blackFilePath, "r") as f:
				lines = f.readlines()
			for line in lines:
				blacklist = line.strip()
				LOG('YampScreen: checkBlackList: blacklist line: %s ' % (blacklist), 'all')
				if blacklist in slidelist:
					LOG('YampScreen: checkBlackList: blacklisted slide found: %s ' % (blacklist), 'all')
					slidelist.remove(blacklist)
		except Exception as e:
			LOG('YampScreen: checkBlackList: EXCEPT: %s' % (str(e)), 'err')
		return slidelist

	# custom or artistart screensaver: scan folders (including subfolders), create filelist
	def buildFileList(self):
		fileList = []
		try:
			if config.plugins.yampmusicplayer.screenSaverSubDirs.value:
				try:
					for dirpath, dirnames, files in walk(self.slidePath):
						try:
							for name in files:
								fileList.append(join(dirpath, name))
						except Exception as e:
							LOG('YampScreen: buildFileList: fileList: EXCEPT1: %s' % (str(e)), 'err')
				except Exception as e:
					LOG('YampScreen: buildFileList: fileList: EXCEPT2: %s' % (str(e)), 'err')
				LOG('YampScreen: buildFileList: fileList: %s' % (fileList), 'all')
			else:
				for filename in listdir(self.slidePath):
					fileList.append(filename)
				LOG('YampScreen: buildFileList: fileList: %s' % (fileList), 'all')
		except Exception as e:
			LOG('YampScreen: buildFileList: fileList complete: EXCEPT: %s' % (str(e)), 'err')
		return fileList

	def getArtistArtDir(self, artworkPath, artist):
		LOG('YampScreen: getArtistArtDir: Start: artworkPath: %s artist: %s' % (artworkPath, artist), 'all')
		artist = self.getArtistAlias(artworkPath, artist)
		LOG('YampScreen: getArtistArtDir: artist after alias: %s' % (artist), 'all')
		subDirArtist = titlecase(sub(r'[/\\.]*', '', artist).strip())  # delete / \. from artist for directory
		LOG('YampScreen: getArtistArtDir: subDirArtist: %s' % (subDirArtist), 'all')
		fullname = artworkPath + subDirArtist
		for subDir in listdir(artworkPath):
			if isdir(artworkPath + subDir) and subDirArtist.lower() == subDir.lower():
				fullname = artworkPath + subDir
				break
		LOG('YampScreen: getArtistArtDir: return pdir: %s' % (fullname), 'all')
		return fullname

	def getArtistAlias(self, artworkPath, artist):
		try:
			aliasfilename = join(artworkPath, 'YampArtistReplace.txt')
		except Exception as e:
			LOG('YampScreen: getArtistAlias: aliasfilename: EXCEPT: %s' % (str(e)), 'err')
			return artist
		if not exists(aliasfilename) or not isfile(aliasfilename):
			return artist
		LOG('YampScreen: getArtistAlias: aliasfilename: %s existing' % (aliasfilename), 'all')
		artistalias = artist
		try:
			file = open(aliasfilename, "r")
			for line in file:
				artistreplace = line.strip().split(',')
				try:
					if artistreplace[0].lower() == artist.lower():
						if len(artistreplace[1]) > 0:
							artistalias = artistreplace[1]
						break
				except Exception as e:
					LOG('YampScreen: getArtistAlias: artistreplace: EXCEPT: %s' % (str(e)), 'err')
			file.close()
		except Exception:
			LOG('YampScreen: getArtistAlias: file: EXCEPT: no artistalias-file', 'all')
		return artistalias

	def resetScreenSaverTimer(self):
		self.hideScreenSaver()
		self.startScreenSaverTimer()

	def startScreenSaverTimer(self):
		if self.screenSaverManOff:
			return
		msecs = config.plugins.yampmusicplayer.screenSaverWait.value * 1000
		if self.screenSaverTimer.isActive() or self.screenSaverActive:
			pass
		elif self.playerState < STATE_STOP and (self.currList == "playlist" or self.currList != "playlist" and config.plugins.yampmusicplayer.screenSaverLeft.value) and msecs > 0:
			self.screenSaverTimer.start(msecs)
		self.setSaverButton()

	def hideScreenSaver(self):
		self.screenSaverActive = False
		self.showHideClock()
		self["lyricsLine"].hide()
		self["lyricsLineBackground"].hide()
		self["lyricsLineBig"].hide()
		self["lyricsLineBackgroundBig"].hide()
		self["screenSaverBackground"].hide()
		self["screenSaver"].hide()
		self.showHideSlideName(False)
		if self.screenSaverTimer.isActive():
			self.screenSaverTimer.stop()
		if self.nextSlideTimer.isActive():
			self.nextSlideTimer.stop()
		self.setSaverButton()
		try:
			self["songInfoBg"].setBoolean(False)
		except Exception as e:
			LOG('YampScreen: hideScreenSaver: self[songInfoBg].setBoolean(False): EXCEPT: %s' % (str(e)), 'err')
		self.updateLCDInfo()

	def screenSaverMaxManOff(self):  # timer-callback
		self.screenSaverManOff = False
		self.startScreenSaverTimer()
		self.setSaverButton()

	def startScreenSaverManTimer(self):
		secs = config.plugins.yampmusicplayer.maxTimeSSoffMan.value - config.plugins.yampmusicplayer.screenSaverWait.value
		if secs < 0:
			secs = 0
		if secs > 0:
			self.screenSaverManTimer.start(secs * 1000, True)
		else:
			self.screenSaverManTimer.stop()

	def keyTextActions(self):
		if self.textLongActive:
			self.textLongActive = False
		else:
			self.lyricsLineShow = not self.lyricsLineShow
			self.lyricsLineShowBig = False
			self.displayHideLyricsLine()

	def keyTextLongActions(self):
		self.textLongActive = True
		self.lyricsLineShowBig = not self.lyricsLineShowBig
		self.lyricsLineShow = False
		self.displayHideLyricsLine()

	def displayHideLyricsLine(self):
		try:
			bgMode = config.plugins.yampmusicplayer.karaokeBg.value
			if not self.lyricsLineShow:
				self["lyricsLine"].hide()
				self["lyricsLineBackground"].hide()
				self["karaoke"].setBoolean(False)
			if not self.lyricsLineShowBig:
				self["lyricsLineBig"].hide()
				self["lyricsLineBackgroundBig"].hide()
				self["karaokeBig"].setBoolean(False)
			self.showBgSmall = (bgMode == 'small' or bgMode == 'both') and self.lyricsLineShow
			self.showBgBig = (bgMode == 'big' or bgMode == 'both') and self.lyricsLineShowBig
			if self.lyricsLineShow or self.lyricsLineShowBig:
				if (self.screenSaverActive or self.isVideoFullScreen) and self.playerState < STATE_STOP:
					if self.lyricsLineShow:
						self["lyricsLine"].setText(self.oldLyricsText)
						self["lyricsLine"].show()
						self["lyricsLineBig"].hide()
						if self.showBgSmall:
							self["lyricsLineBackground"].show()
						else:
							self["lyricsLineBackground"].hide()
					else:
						self["lyricsLineBig"].setText(self.oldLyricsText)
						self["lyricsLineBig"].show()
						if self.showBgBig:
							self["lyricsLineBackgroundBig"].show()
						else:
							self["lyricsLineBackgroundBig"].hide()
						self["lyricsLine"].hide()
						self["lyricsLineBackground"].hide()
					self.startKaraokeMaxTimer()
			self["karaoke"].setBoolean(self.lyricsLineShow)
			self["karaokeBig"].setBoolean(self.lyricsLineShowBig)
		except Exception as e:
			LOG('YampScreen: displayHideLyricsLine: EXCEPT: %s' % (str(e)), 'err')

	def pvrActions(self):
		if self.isVideoFullScreen:
			try:
				self.session.openWithCallback(self.videoTitleClosedCB, YampVideoTitleV33, self)
			except Exception as e:
				LOG('YampScreen: pvrActions: openYampVideoTitleV33: EXCEPT: %s' % (str(e)), 'err')
		elif not self.currentIsVideo or self.videoStartMode != "manual":
			self.showhideScreenSaverMan()

	def showhideScreenSaverMan(self):
		if self.manKeyScreensaver:
			if not (self.screenSaverTimer.isActive() or self.screenSaverActive) and self.playerState < STATE_STOP:
				self.screenSaverManOff = False
				self.startScreenSaverTimer()
			else:
				self.screenSaverManOff = True
				self.startScreenSaverManTimer()
				self.hideScreenSaver()
			self.setSaverButton()

	def coverScrollTimerTimeout(self):
		try:
			if len(self.playlist) == 0:
				return
			path = self.playlist.getServiceRefList()[self.playlist.getCurrentIndex()].getPath()
			self.updateMusicInformation(path, current=False)
		except Exception as e:
			LOG('YampScreen: coverScrollTimerTimeout: EXCEPT: ' + str(e), 'err')

	def screenSaverStartTimeout(self):
		bgMode = config.plugins.yampmusicplayer.karaokeBg.value
		self.showScreenSaver()
		self.displayHideLyricsLine()
		self.startKaraokeMaxTimer()
		if self.currentIsVideo and not self.isVideoFullScreen:
			self.hideYampScreenShowVideo()
		if self.screenSaverFirstCall:
			self.screenSaverFirstCall = False
			self.resetSlideTimer()
			if config.plugins.yampmusicplayer.screenSaverMode.value == 'custom':
				self.nextSlide()
		else:
			self.nextSlide()

	def specialScreenActive(self):
		return self.lyricsScreenActive or self.configScreenActive or self.dbScreenActive or self.virtKeyboardActive

	def showScreenSaver(self):
		if self.screenSaverManOff or self.specialScreenActive():
			return
		self.showHideClock("SS")
		self.screenSaverActive = True
		self.setSaverButton()
		if self.screenSaverTimer.isActive():
			self.screenSaverTimer.stop()
		self["screenSaverBackground"].show()
		self["screenSaver"].show()
		self.showHideSlideName(True)
		if config.plugins.yampmusicplayer.showInfoBarBg.value:
			self["songInfoBg"].setBoolean(True)
			try:
				if len(self["fanartdownload"].getText()) > 0:
					self["fanartdownload"].show()
					self["downloadBackground"].show()
					self.showFanartNumberDl()
			except Exception as e:
				LOG('YampScreen: showScreenSaver: showInfoBarBg: EXCEPT: %s' % (str(e)), 'err')
		self.updateLCDInfo()

	def nextSlide(self):
		if not self.currentIsVideo:
			self["screenSaver"].showNextPic()
		self.resetSlideTimer()
		self.showHideSlideName(True)

	def prevSlide(self):
		if not self.currentIsVideo:
			self["screenSaver"].showPrevPic()
		self.resetSlideTimer()
		self.showHideSlideName(True)

	def showHideSlideName(self, show):
		mode = config.plugins.yampmusicplayer.displayDiaName.value
		if not show or config.plugins.yampmusicplayer.screenSaverMode.value != "custom" or mode == 'no':
			self["pathNameSSDia"].hide()
			self["pathNameSSDiaBackground"].hide()
			self["pathNameSSDia"].setText('')
		else:
			if 'path' in mode:
				self["pathNameSSDia"].setText(self["screenSaver"].getCurrentSlide())
			else:
				self["pathNameSSDia"].setText(basename(self["screenSaver"].getCurrentSlide()))
			self["pathNameSSDia"].show()
			if 'bg' in mode:
				self["pathNameSSDiaBackground"].show()

	def resetSlideTimer(self):
		msecs = config.plugins.yampmusicplayer.screenSaverNextSlide.value * 1000
		if not self.slideShowPaused:
			self.nextSlideTimer.stop()
			self.nextSlideTimer.start(msecs)

	def pausePlaySlideShow(self):
		if self.screenSaverActive and not self.isVideoFullScreen:
			if self.slideShowPaused:
				self.slideShowPaused = False
				self.nextSlide()
			else:
				if self.nextSlideTimer.isActive():
					self.nextSlideTimer.stop()
					self.slideShowPaused = True
		self.setSaverButton()

# Menu key actions
# These actions depend on the active list and/or the current item in the list
# The configuration is always callable
	def showMenu(self):  # Build Menu Entries
		self.hideScreenSaver()
		menu = []
		actSortMode = None
		if self.currList == "playlist":
			actSortMode = self.playlist.getSortMode()
			menu.append((_("Search in Playlist"), "searchplaylist"))
		if self.leftContent == "dblist" and self.currTitle:
			menu.append((_("Search current title"), "searchcurrentsong"))
		if self.leftContent == "dblist" and self.currArtist:
			menu.append((_("Search current artist"), "searchcurrentartist"))
		if self.leftContent == "dblist" and self.currAlbum:
			menu.append((_("Search current album"), "searchcurrentalbum"))
		if self.currList == "playlist":
			if actSortMode != 0:
				menu.append((_("Unsort Playlist"), "unsortplaylist"))
			if actSortMode != 1:
				menu.append((_("Sort Playlist A-Z"), "sortplaylistaz"))
			if actSortMode != 2:
				menu.append((_("Sort Playlist Z-A"), "sortplaylistza"))
			menu.append((_("Save Playlist e2pls"), "saveplayliste2pls"))
			menu.append((_("Save Playlist m3u"), "saveplaylistm3u"))
			menu.append((_("Save Playlist e2pls + m3u"), "saveplaylistboth"))
			menu.append((_("Search path/filename of current title"), "searchfilename"))
		elif self.currList == "filelist":
			menu.append((_("Search path"), "searchfilelist1"))  # paths
			menu.append((_("Search filename"), "searchfilelist2"))  # filenames
			if self.filelist.getFilename() is not None:
				if self.filelist.getFilename().lower().endswith(".e2pls") or self.filelist.getFilename().lower().endswith(".m3u"):
					menu.append((_("Delete playlist"), "deleteplaylist"))
		else:  # database list
			if self.dblist.mode == MENULIST:
				if self.dblist.getSelectionIndex() == 0:  # Playlists
					menu.append((_("Search playlists"), "searchplaylists"))
				elif self.dblist.getSelectionIndex() == 1:  # Artistlist
					menu.append((_("Search artists"), "searchartists"))
					menu.append((_("Delete ALL artist's musicbrainz-ID entries"), "deleteartistmbidallentries"))
				elif self.dblist.getSelectionIndex() == 2:  # Albumlist
					menu.append((_("Search albums"), "searchalbums"))
				elif self.dblist.getSelectionIndex() == 3:  # Titellist
					menu.append((_("Search titles"), "searchsongs"))
					menu.append((_("Search files"), "searchfiles"))
				elif self.dblist.getSelectionIndex() == 4:  # Genrelist
					menu.append((_("Search genres"), "searchgenres"))
				elif self.dblist.getSelectionIndex() == 5:  # Datelist
					menu.append((_("Search dates"), "searchdates"))
			elif self.dblist.mode == ARTISTLIST:
				menu.append((_("Search artists"), "searchartists"))
				menu.append((_("Jump to entry"), "jumptoentry"))
				menu.append((_("Delete artist's title entries"), "deleteartistsongentries"))
				menu.append((_("Delete artist's musicbrainz-ID entries"), "deleteartistmbidentries"))
			elif self.dblist.mode in (ALBUMLIST, GENREALBUMLIST, ARTISTALBUMLIST, DATEALBUMLIST):
				menu.append((_("Search albums"), "searchalbums"))
				menu.append((_("Jump to entry"), "jumptoentry"))
				menu.append((_("Delete album entries"), "deletealbumsongentries"))
			elif self.dblist.mode == GENRELIST:
				menu.append((_("Search genres"), "searchgenres"))
				menu.append((_("Jump to entry"), "jumptoentry"))
				menu.append((_("Delete genre's title entries"), "deletegenresongentries"))
			elif self.dblist.mode == DATELIST:
				menu.append((_("Search dates"), "searchdates"))
				menu.append((_("Jump to entry"), "jumptoentry"))
				menu.append((_("Delete date's title entries"), "deletedatesongentries"))
			elif self.dblist.mode == PLAYLISTLIST:
				menu.append((_("Search playlists"), "searchplaylists"))
				menu.append((_("Jump to entry"), "jumptoentry"))
				menu.append((_("Delete ext. playlist entry"), "deleteplaylistentry"))
			elif self.dblist.mode >= TITLELIST:
				menu.append((_("Show similar titles"), "showsimilarsongs"))
				menu.append((_("Search titles"), "searchsongs"))
				menu.append((_("Search files"), "searchfiles"))
				menu.append((_("Jump to entry"), "jumptoentry"))
				menu.append((_("Delete title entry"), "deletesongentry"))
			menu.append((_("Compact music database"), "compactdatabase"))
			menu.append((_("Clear music database"), "cleardatabase"))
		menu.append((_("Edit Configuration"), "config"))

		if len(menu) > 1:
			if self.currList == "playlist":
				self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_("Playlist actions"), list=menu)
			elif self.currList == "filelist":
				self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_("Filelist actions"), list=menu)
			else:  # database list
				self.session.openWithCallback(self.menuCallback, ChoiceBox, title=_("Database actions"), list=menu)
		else:
			self.config()

	def menuCallback(self, choice):
		if choice is None:
			if not self.currentIsVideo or self.videoStartMode != "manual":
				self.resetScreenSaverTimer()
			return
		if choice[1] == "searchfilelist1":
			self.searchFilelist1()
		elif choice[1] == "searchfilelist2":
			self.searchFilelist2()
		elif choice[1] == "unsortplaylist":
			self.sortPlaylist(0)
		elif choice[1] == "sortplaylistaz":
			self.sortPlaylist(1)
		elif choice[1] == "sortplaylistza":
			self.sortPlaylist(2)
		elif choice[1] == "searchplaylist":
			self.searchPlaylist()
		elif choice[1] == "saveplayliste2pls":
			self.savePlaylist(1)
		elif choice[1] == "saveplaylistm3u":
			self.savePlaylist(2)
		elif choice[1] == "saveplaylistboth":
			self.savePlaylist(3)
		elif choice[1] == "searchfilename":
			self.getPlaylistFile()
		elif choice[1] == "deleteplaylist":
			self.deletePlaylist()
		elif choice[1] == "jumptoentry":
			self.jumpToEntry()
		elif choice[1] == "deleteartistsongentries":
			self.deleteArtistSongEntries()
		elif choice[1] == "deleteartistmbidentries":
			self.deleteArtistMbid()
		elif choice[1] == "deleteartistmbidallentries":
			self.deleteArtistMbidAll()
		elif choice[1] == "deletealbumsongentries":
			self.deleteAlbumSongEntries()
		elif choice[1] == "deletegenresongentries":
			self.deleteGenreSongEntries()
		elif choice[1] == "deletedatesongentries":  # !!!!
			self.deleteDateSongEntries()
		elif choice[1] == "deleteplaylistentry":
			self.deletePlaylistEntry()
		elif choice[1] == "deletesongentry":
			self.deleteSongEntry()
		elif choice[1] == "showsimilarsongs":
			self.showSimilarSongs()
		elif choice[1] == "searchsongs":
			self.searchSongs()
		elif choice[1] == "searchfiles":
			self.searchFiles()
		elif choice[1] == "searchplaylists":
			self.searchPlaylists()
		elif choice[1] == "searchartists":
			self.searchArtists()
		elif choice[1] == "searchalbums":
			self.searchAlbums()
		elif choice[1] == "searchgenres":
			self.searchGenres()
		elif choice[1] == "searchcurrentsong":
			self.searchCurrentSong()
		elif choice[1] == "searchcurrentartist":
			self.searchCurrentArtist()
		elif choice[1] == "searchcurrentalbum":
			self.searchCurrentAlbum()
		elif choice[1] == "checkdatabase":
			pass  # to be implemented
		elif choice[1] == "compactdatabase":
			self.compactDatabase()
		elif choice[1] == "cleardatabase":
			self.clearDatabaseFromMenu()
		elif choice[1] == "config":
			self.config()
		if choice[1] != "config":  # no Screensaver start in config
			if not self.currentIsVideo or self.videoStartMode != "manual":
				self.resetScreenSaverTimer()

	def getPlaylistFile(self):
		songpath = ''
		try:
			sel = self.playlist.getSelection()
			if sel is not None:
				songpath = sel.getPath()
		except Exception as e:
			LOG('YampScreen: getPlaylistFile: get songpath: EXCEPT: %s' % (str(e)), 'err')
		if not songpath:
			return
		if not exists(songpath) or not isfile(songpath):
			msg = _("file %s not existing or not reachable") % (songpath)
			self.session.open(MessageBox, msg, type=MessageBox.TYPE_INFO)
			return
		try:
			if self.leftContent != "filelist":
				try:
					self.leftContent = "filelist"
				except Exception as e:
					LOG('YampScreen: getPlaylistFile: searchFile: EXCEPT2: %s' % (str(e)), 'err')
				try:
					self.setLeftContent("filelist")
				except Exception as e:
					LOG('YampScreen: getPlaylistFile: searchFile: EXCEPT3: %s' % (str(e)), 'err')
				try:
					self.setColorButtons()
				except Exception as e:
					LOG('YampScreen: getPlaylistFile: searchFile: EXCEPT4: %s' % (str(e)), 'err')
				try:
					self.updateLCDInfo()
				except Exception as e:
					LOG('YampScreen: getPlaylistFile: searchFile: EXCEPT5: %s' % (str(e)), 'err')
		except Exception as e:
			LOG('YampScreen: getPlaylistFile: searchFile: EXCEPT6: %s' % (str(e)), 'err')
		try:
			self.currFilePath = dirname(songpath)
			self.filelist.changeDir(self.currFilePath)
			self.filelist.searchPath(self.currFilePath)
			self.setLeftContentTitle()
		except Exception as e:
			LOG('YampScreen: getPlaylistFile: searchFile: EXCEPT: %s' % (str(e)), 'err')
		try:
			for idx in range(len(self.filelist)):
				self.filelist.moveToIndex(idx)
				actFileName = self.filelist.getFilename()
				if actFileName == songpath:
					break
			self.switchToFileList()
		except Exception as e:
			LOG('YampScreen: getPlaylistFile: idx: EXCEPT: %s' % (str(e)), 'err')

	def config(self):
		self.hideScreenSaver()
		self.previousCalcLenLists = config.plugins.yampmusicplayer.showPlayListLen.value
		self.screenSaverManTimer.stop()
		self.configScreenActive = True
		if config.plugins.yampmusicplayer.searchFanart.value != 'always':
			self.previousFanartDLconfig = config.plugins.yampmusicplayer.searchFanart.value
		self.session.openWithCallback(self.configFinished, YampConfigScreenV33, self, self.videoPreviewOn)

	def writeLcdConfirmed(self, answer):
		if answer:  # overwrite ok
			if self.par1 and writeLcd():
				self.msgWriteLcdFilesFailed('YampLCD.xml')
			if self.par2 and writeLcdRunning():
				self.msgWriteLcdFilesFailed('YampLcdRunning.xml')

	def configFinished(self, noChange, skinChanged, dbPathChanged, lcdChanged, lcdXmlChanged, lcdRunningChanged):
		global selectedDirExcludeValue
		self.dbArtistList = []
		if dbPathChanged:
			checkDatabaseHasData()
		try:
			self.buildDbMenuList()
		except Exception as e:
			LOG('YampScreen: configFinished: buildDbMenuList: EXCEPT: %s' % (str(e)), 'err')
		selectedDirExcludeValue = int(config.plugins.yampmusicplayer.dbExcludeDir.value)
		newLcdOff = config.plugins.yampmusicplayer.yampLcdMode.value == 'off'
		newLcdRunning = config.plugins.yampmusicplayer.yampLcdMode.value == 'running'
		msg1 = ""
		if skinChanged:
			msg1 = _('Skin')
			config.plugins.yampmusicplayer.yampSkin.save()
		if lcdChanged:
			msg1 = _('Box-Display')
		if skinChanged or lcdChanged:
			msg = msg1 + _(" changed, Yamp restart required to apply new selection\n\nDo you want to close Yamp now?")
			self.session.openWithCallback(self.exitConfirmed, MessageBox, msg, timeout=15)
		if lcdXmlChanged or lcdRunningChanged:
			msgStart = _('to activate the new configuration for the Box-Display, ')
			msgEnd = _('\n\nwill be overwitten.\n\nDo you agree?')
			f1, f2, msg = "", "", ""
			if lcdXmlChanged:
				f1 = join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, 'YampLCD.xml')
				msg = msgStart + _('the file\n\n%s') % (f1) + msgEnd
			if lcdRunningChanged:
				f2 = join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, 'YampLcdRunning.xml')
				msg = msgStart + _('the file\n\n%s') % (f2) + msgEnd
			if lcdXmlChanged and lcdRunningChanged:
				msg = msgStart + _('the files\n\n%s\nand\n%s') % (f1, f2) + msgEnd
			self.par1 = lcdXmlChanged
			self.par2 = lcdRunningChanged
			self.session.openWithCallback(self.writeLcdConfirmed, MessageBox, msg, timeout=10)
		self.searchFanartConfig = config.plugins.yampmusicplayer.searchFanart.value
		if self.previousCalcLenLists != config.plugins.yampmusicplayer.showPlayListLen.value:
			if config.plugins.yampmusicplayer.showPlayListLen.value:
				self.recalcLenListsComplete()
				self["playLen"].show()
				self["txtPlayLen"].show()
				self["playLenRem"].show()
				self["txtPlayLenRem"].show()
			else:
				self["playLen"].hide()
				self["txtPlayLen"].hide()
				self["playLenRem"].hide()
				self["txtPlayLenRem"].hide()
		self.configScreenActive = False
		self.initScreenSaver(artist=self.currArtist)
		self.startScreenSaverTimer()
		self.setHelpTexts()
		self.infoBarNaReplace = INFOBARTEXTLIST[int(config.plugins.yampmusicplayer.displayUnknown.value)]
		self.lyricsPlayOffsetTime90 = config.plugins.yampmusicplayer.lyricsPlayOffsetTime.value * 90
		if config.plugins.yampmusicplayer.displaySkinname.value:
			self["actskin"].show()
		else:
			self["actskin"].hide()
		if self.logpath != config.plugins.yampmusicplayer.debugPath.value:
			self.logpath = config.plugins.yampmusicplayer.debugPath.value
			self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
			config.plugins.yampmusicplayer.debugFile.value = self.logpath + 'yamp_debug_' + self.timestamp + '.log'
		self.memlog = config.plugins.yampmusicplayer.yampDebugMemory.value
		self.memlogfile = self.logpath + 'yamp_mem_' + self.timestamp + '.log'
		self.videoStartMode = config.plugins.yampmusicplayer.videoAutoFull.value
		fanarttvpersonal = config.plugins.yampmusicplayer.fanarttvPersonal.value.strip()
		if len(fanarttvpersonal) == 32 and not fanarttvpersonal.strip().startswith('1234567890abcdef') and 'abcdef7890' not in fanarttvpersonal.strip():
			if self.fanarttvPersonalApikey != fanarttvpersonal:
				self.fanarttvPersonalApikey = fanarttvpersonal
				LOG('YampScreen: configFinished: len: %d  fanarttvPersonalApikey: %s' % (len(self.fanarttvPersonalApikey), self.fanarttvPersonalApikey), 'all')
				try:
					with open(FANARTTVPERSAPIFILE, "w") as f:
						f.write(fanarttvpersonal)
					LOG('YampScreenV33: configFinished: Personal api key written to file: *%s*' % (fanarttvpersonal), 'all')
				except OSError:
					LOG('YampScreenV33: configFinished: EXCEPT: Personal api key could not be written to file', 'err')
		self.startScreenSaverManTimer()
		if self.screenSaverActive:
			if config.plugins.yampmusicplayer.showInfoBarBg.value:
				try:
					self["songInfoBg"].setBoolean(True)
				except Exception:
					LOG('YampScreen: configFinished: self[songInfoBg].setBoolean(True): EXCEPT', 'err')
			else:
				try:
					self["songInfoBg"].setBoolean(False)
				except Exception:
					LOG('YampScreen: configFinished: self[songInfoBg].setBoolean(False): EXCEPT', 'err')
		config.plugins.yampmusicplayer.yampShowTV.save()
		self.setTVOptions()
		if noChange:
			return
		self.repeat = config.plugins.yampmusicplayer.repeatPlaylistAtEnd.value
		self.setRepeatButton()
		# Screensaver in Background
		self.ssBackground = config.plugins.yampmusicplayer.screenSaverBg.value
		self.setScreensaverBg()

	def msgWriteLcdFilesFailed(self, which):
		filename = join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, which)
		msg = _('Box display configuration file\n\n%s\n\ncould not be written!\n\nWrite protected? Wrong format?\n\nIf not corrected, changes will be lost...') % (filename)
		self.session.open(MessageBox, msg, type=MessageBox.TYPE_ERROR, timeout=30)
#-------------------- Update methods for title info and cover

	def updateMusicInformation(self, path="", clear=False, current=True, isAlbum=False):
		title, album, genre, artist, albumartist, date, length, tracknr, strBitrate = readID3Infos(path)
		try:
			newYear = date[:4]
		except Exception:
			newYear = date
		if current:
			self.currTitle = title
			self.currArtist = artist
			self.currAlbum = album
			self.currLength = length
			self.currTracknr = tracknr
			self.currGenre = genre
			self.currBitRate = strBitrate
		else:
			if not title and not artist and not album:
				title = self.currTitle
				artist = self.currArtist
				album = self.currAlbum
				length = self.currLength
				tracknr = self.currTracknr
				genre = self.currGenre
				strBitrate = self.currBitRate
		self.currYear = newYear
		self.currDate = date
		newCover = False
		newArtist = False
		if title != self.oldTitle:
			if isAlbum:
				self.updateSingleMusicInformation("songtitle", "")
			else:
				self.updateSingleMusicInformation("songtitle", title)
			self.updateSingleMusicInformation("year", self.currYear)
			self.updateSingleMusicInformation("genre", genre)
			self.updateSingleMusicInformation("bitRate", strBitrate)
			newCover = True
		if artist != self.oldArtist:
			self.updateSingleMusicInformation("artist", artist)
			newArtist = True
		if album != self.oldAlbum:
			self.updateSingleMusicInformation("album", album)
			newCover = True
		self.updatePlaylistInfo()
		self.oldTitle = title
		self.oldArtist = artist
		self.oldAlbum = album
		if self.previousIsVideo == self.currentIsVideo:
			newArtist = True
		self.previousIsVideo = self.currentIsVideo
		if clear:
			self["coverArt"].showDefaultCover()
		elif newCover:
			self.updateCover(artist, album, title, path)
		if config.plugins.yampmusicplayer.yampLcdMode.value == 'running':
			self.updateLCDText(title + ' - ' + artist + ' - ' + album, 1)
		else:
			self.updateLCDText(title, 1)
			self.updateLCDText(artist, 2)
			self.updateLCDText(album, 3)
		LOG('YampScreen: UpdateMusicInfo: Artist: %s' % (artist), 'all')
		if config.plugins.yampmusicplayer.screenSaverMode.value == "artwork":
			if clear:
				self.hideScreenSaver()
			else:
				if newArtist and not self.currentIsVideo:  # !!!Video
					if artist != 'n/a' and current:
						self.initScreenSaver(artist)
						self.getArtistPics(artist)

	def updateSingleMusicInformation(self, name, info):
		info = info.replace('n/a', self.infoBarNaReplace)
		if self[name].getText() != info:
			self[name].setText(info)

	def coverChanged(self, filename):
		LOG('YampScreen: coverChanged: Start: filename: %s pixnum: %d' % (filename, self.pixNumCover), 'all')
		num = self.pixNumCover % COVERS_NO
		if num == 0:
			LOG('YampScreen: coverChanged: default cover', 'all')
			self["coverArt"].showDefaultCover()
			name, pix = self.getCoverArtFile()
			if self.lyricsScreenActive:
				self.coverChangedLyrics = True  # for Lyrics
			self.createLcdCoverImage(join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, 'no_coverArt.png'))
			return
		if num == COVERS_GOOGLE:
			LOG('YampScreen: coverChanged: coverChangedGoogle = True', 'all')
			self["coverArt"].showCoverArt(filename)
			name, pix = self.getCoverArtFile()
			LOG('YampScreen: coverChanged: coverChangedGoogleLyrics = True: getCoverArtFile: %s' % (name), 'all')
			if self.lyricsScreenActive:
				self.coverChangedGoogleLyrics = True  # for Lyrics
			self.saveCoverAuto(name)
		else:
			LOG('YampScreen: coverChanged: coverChanged else', 'all')
			self["coverArt"].showCoverArt(filename)
			name, pix = self.getCoverArtFile()
			LOG('YampScreen: coverChanged: coverChangedLyrics = True  getCoverArtFile: %s' % (name), 'all')
			if self.lyricsScreenActive:
				self.coverChangedLyrics = True  # for Lyrics
		self.createLcdCoverImage(name)

	def createLcdCoverImage(self, picFile):
		lcdMode = config.plugins.yampmusicplayer.yampLcdMode.value
		if lcdMode == 'off' or lcdMode == 'running':
			return
		if 'cover' not in lcdMode:
			self.summaries.setCover()  # delete old cover
			self.updateLCDInfo()
			return
		LOG('YampScreen: createLcdCoverImage: picfile: %s' % (picFile), 'all')
		im = Image.open(picFile)
		color = config.plugins.yampmusicplayer.lcdCoverColor.value
		if color == 'bw':
			ic = im.convert("L")
		elif color == 'bwt':
			ic = im.convert("LA")
		elif color == 'color':
			ic = im.convert("RGB")
		else:
			ic = im.convert("RGBA")
		size = config.plugins.yampmusicplayer.lcdCoverSize.value
		ir = ic.resize((size, size))
		ir.save('/tmp/coverlcd.png')
		self.summaries.setCover()
		self.updateLCDInfo()

	def saveCoverAuto(self, srcpath):
		configSave = config.plugins.yampmusicplayer.saveCover.value
		try:
			if configSave == '0':
				return
		except Exception as e:
			LOG('YampScreen: saveCoverAuto: srcpath, configSave: EXCEPT: return: %s' % (str(e)), 'err')
			return
		if not srcpath:
			return
		try:
			ext = splitext(basename(srcpath))[1].strip()
			if configSave in ['titleNoPicture', 'titleNoTitle', 'titleAlways']:
				destpath = splitext(self.playlist.getServiceRefList()[self.playlist.getCurrentIndex()].getPath())[0] + ext
			else:
				destpath = join(dirname(self.playlist.getServiceRefList()[self.playlist.getCurrentIndex()].getPath()), 'albumcover' + ext)
			LOG('YampScreen: saveCoverAuto: destpath: %s' % (destpath), 'spe')
			# check for existing file
			if configSave == 'titleNoPicture':
				filelist = self.fileListByExt(dirname(destpath), COVER_EXTENSIONS)
				LOG('YampScreen: saveCoverAuto: filelist: %s' % (filelist), 'spe')
				if len(filelist) > 0:
					LOG('YampScreen: saveCoverAuto: at least 1 pic existing in: %s, do not save cover' % (dirname(destpath)), 'spe')
					return
			if configSave == 'titleNoTitle':
				filelist = self.fileListByExt(dirname(destpath), COVER_EXTENSIONS)
				LOG('YampScreen: saveCoverAuto: filelist: %s' % (filelist), 'spe')
				for filename in filelist:
					if splitext(basename(filename))[0].lower().strip() == splitext(basename(destpath))[0].lower().strip():
						LOG('YampScreen: saveCoverAuto: <title>.<ext> existing in: %s, do not save cover' % (dirname(destpath)), 'spe')
						return
			if configSave == 'albumNoPicture':
				filelist = self.fileListByExt(dirname(destpath), COVER_EXTENSIONS)
				for filename in filelist:
					if splitext(basename(filename))[0].lower().strip() == 'albumcover':
						LOG('YampScreen: saveCoverAuto: albumcover.<ext> existing in: %s, do not save cover' % (dirname(destpath)), 'spe')
						return
			try:
				self.readWriteFileBinary(srcpath, destpath)
#				self.session.open(MessageBox, _("Cover saved"), type = MessageBox.TYPE_INFO,timeout = 5 )
			except Exception as e:
				LOG('YampScreen: saveCoverAuto: writecover: EXCEPT: %s' % (str(e)), 'err')
#				self.session.open(MessageBox, _("Saving cover failed"), type = MessageBox.TYPE_INFO,timeout = 30 )
		except Exception as e:
			LOG('YampScreen: saveCoverAuto: END: EXCEPT: %s' % (str(e)), 'err')

#Look for cover in ID3 tag (mp3/mp4/m4a/flac/ogg), in current directory, albumCover in current directory, Search cover with Google, if enabled
	def updateCover(self, artist, album, title, path=""):
		self.coverFoundPrio = COVERS_NO
		self.pixNumCover = COVERS_NO
		self.requestNum = (self.requestNum + 1) % 10
		if self.playerState == STATE_STOP and artist == album == title == path == "":
			self.coverChanged("")
			return
		prioList = [
			config.plugins.yampmusicplayer.prioCover1.value,
			config.plugins.yampmusicplayer.prioCover2.value,
			config.plugins.yampmusicplayer.prioCover3.value,
			config.plugins.yampmusicplayer.prioCover4.value,
			config.plugins.yampmusicplayer.prioCover5.value
		]
		LOG('YampScreen: UpdateCover prioList: %s' % (prioList), 'spe')
		filename = self.searchCoverID3(path, prioList)
		LOG('YampScreen: updateCover: before searchCoverDirectoryTitle: filename: %s' % (filename), 'spe')
		filename = self.searchCoverDirectoryTitle(path, filename, title, prioList)
		LOG('YampScreen: updateCover: before searchCoverAlbum: filename: %s' % (filename), 'spe')
		filename = self.searchCoverAlbum(path, filename, prioList)
		LOG('YampScreen: updateCover: before searchCoverDirectoryAny: filename: %s' % (filename), 'spe')
		filename = self.searchCoverDirectoryAny(path, filename, prioList)
		LOG('YampScreen: updateCover: call coverChanged: filename: %s' % (filename), 'spe')
		if filename:
			self.coverChanged(filename)
		LOG('YampScreen: updateCover: before searchCoverGoogle', 'spe')
		self.searchCoverGoogle(artist, album, title, prioList)

#Search cover with Google, if enabled

	def searchCoverGoogle(self, artist, album, title, prioList):
		if 'coverGoogle' in prioList:
			prio = prioList.index('coverGoogle') + 1
		else:
			return
		LOG('YampScreen: searchCoverGoogle: currentIsVideo: %d  configSearchVideo: %d' % (self.currentIsVideo, config.plugins.yampmusicplayer.searchGoogleCoverVideo.value), 'spe')
		if self.currentIsVideo and not config.plugins.yampmusicplayer.searchGoogleCoverVideo.value:
			return
		LOG('YampScreen: searchCoverGoogle: prio: %d  coverFoundPrio: %d' % (prio, self.coverFoundPrio), 'spe')
		if self.coverFoundPrio < prio:
			return  # already found with higher priority
		LOG('YampScreen: call getGoogleCover', 'spe')
		self.getGoogleCover(artist, album, title, prio)

	def getGoogleCover(self, artist, album, title, prio):
		LOG('YampScreen: getGoogleCover: Start: artist: %s  album: %s  title: %s' % (artist, album, title), 'spe')
		if artist == 'n/a':
			artist = ''
		if album == 'n/a':
			album = ''
		if title == 'n/a':
			title = ''
		if album == '+':
			album = 'plus'
		callback = boundFunction(self.coverGoogleUrlFound, prio, self.requestNum)
		if artist and album:
			url = "http://images.google.de/images?q=%s+%s&udm=2" % (quote_plus(artist), quote_plus(album))
			LOG('YampScreen: getGoogleCover a, a: url: %s' % (url), 'spe')
			callInThread(getUrlData, url, callback=callback, fail=self.coverGoogleUrlFailed)
		elif artist and title:
			url = "http://images.google.de/images?q=%%22%s%%22+%%22%s%%22&udm=2" % (quote_plus(artist), quote_plus(title))
			LOG('YampScreen: getGoogleCover a, t: url: %s' % (url), 'spe')
			callInThread(getUrlData, url, callback=callback, fail=self.coverGoogleUrlFailed)
		elif title:
			url = "http://images.google.de/images?q=%%22%s%%22&udm=2" % (quote_plus(title))
			LOG('YampScreen: getGoogleCover title: url: %s' % (url), 'spe')
			callInThread(getUrlData, url, callback=callback, fail=self.coverGoogleUrlFailed)
		else:
			LOG('YampScreen: getGoogleCover No artist, title, album', 'all')

	def coverGoogleUrlFound(self, prio, requestNum, response):
		self.requestNumSav1 = requestNum
		LOG('YampScreen: coverGoogleUrlFound self.requestNum: %d self.requestNumSav1 : %d' % (self.requestNum, self.requestNumSav1), 'spe')
		if self.requestNum != self.requestNumSav1:
			return
		result = response.text
		foundList = findall(r'\["(.*?)",', result)
		LOG('YampScreen: coverGoogleUrlFound: foundList: %s' % foundList, 'spe')
		url, ext = "", ""
		for entry in findall(r'\["(.*?)",', result):
			if url:
				break
			for x in COVER_EXTENSIONS:
				if x in entry:
					url, ext = entry, ext
					break
		if url:
			LOG('YampScreen: coverGoogleUrlFound URL: %s ' % (url), 'spe')
			filename = "/tmp/.coverartgoogle%s%s" % (self.coverIndex, ext)
			self.coverIndex = (self.coverIndex + 1) % COVER_MAXINDEX
			LOG('YampScreen: coverGoogleUrlFound: filename: %s ' % (filename), 'spe')
			callback = boundFunction(self.coverDownloadFinished, filename, prio, requestNum)
			callInThread(getUrlData, url, filename, callback=callback, fail=self.coverGoogleUrlFailed)
		else:
			LOG('YampScreen: coverGoogleUrlFound: No cover found', 'spe')

	def coverGoogleUrlFailed(self, errMsg):
		LOG('YampScreen: coverGoogleUrlFailed: %s' % errMsg, 'err')

	def coverDownloadFinished(self, filename, prio, requestNum, result):
		self.requestNumSav2 = requestNum
		LOG('YampScreen: coverDownloadFinished self.requestNum: %d self.requestNumSav2 : %d' % (self.requestNum, self.requestNumSav2), 'spe')
		if self.requestNum != self.requestNumSav2:
			return
		LOG('YampScreen: coverDownloadFinished: filename: %s' % (filename), 'spe')
		self.pixNumCover = COVERS_GOOGLE
		self.coverFoundPrio = prio
		self.coverChanged(filename)

	# Mp3 /mp4 /M4a / Flac / ogg: ID3 Cover search
	def searchCoverID3(self, path, prioList):
		# mp3: ID3 Tag search
		filename = ''
		if 'coverID3' in prioList:
			prio = prioList.index('coverID3') + 1
		else:
			return
		LOG('YampScreen: searchCoverID3: prio: %d  coverFoundPrio: %d' % (prio, self.coverFoundPrio), 'spe')
		if self.coverFoundPrio < prio:
			return  # already found with higher priority
		mime = None
		isFlac = isMp4 = isM4a = isOgg = False
		audio, e = "", ""
		# mp3, mp4, m4a
		if path.lower().endswith(".mp3") or path.lower().endswith(".mp4") or path.lower().endswith(".m4a"):
			LOG('YampScreen: searchCoverID3: Mp3/Mp4/m4a', 'spe')
			try:
				audio = ID3(path)
			except Exception:
				LOG('YampScreen: searchCoverID3 : audio = NONE', 'spe')
				audio = None
			try:
				title, album, genre, artist, albumartist, date, length, tracknr, strBitrate = readID3Infos(path)
			except Exception as e:
				LOG('YampScreen: searchCoverID3 : date, length, tracknr: EXCEPT: %s' % (str(e)), 'err')
		ftype, data, e = 0, None, ""
		if path.lower().endswith(".mp3") and audio:
			apicframes = audio.getall("APIC")
			if len(apicframes) > 0:
				mime = apicframes[0].mime
				data = apicframes[0].data  #  check for type=3 (FrontCover)?
				ftype = apicframes[0].type
		if path.lower().endswith(".mp4") or path.lower().endswith(".m4a"):
			if path.lower().endswith(".mp4"):
				isMp4 = True
			elif path.lower().endswith(".m4a"):
				isM4a = True
			try:
				video = MP4(path)
			except Exception as e:
				LOG('YampScreen: searchCoverID3: Mp4: video = NONE: %s' % (str(e)), 'spe')
				video = None
			try:
				if video and len(video["covr"]):
					data = video["covr"][0]
					mime = 'jpeg'
					ftype = 0
			except Exception:
				pass
		# flac
		elif path.lower().endswith(".flac"):
			LOG('YampScreen: searchCoverID3: Flac', 'spe')
			isFlac = True
			try:
				flacInfo = FLAC(path)
			except Exception:
				flacInfo = None
			if flacInfo:
				try:
					LOG('YampScreen: searchCoverID3 : 	flacInfo: %s' % (flacInfo), 'spe')
				except Exception as e:
					LOG('YampScreen: searchCoverID3 : 	flacInfo: EXCEPT: %s' % (str(e)), 'err')
				picture_list = flacInfo.pictures
				if len(picture_list) > 0:
					mime = picture_list[0].mime
					data = picture_list[0].data  #  check for type=3 (FrontCover)?
					ftype = picture_list[0].type
		elif path.lower().endswith(".ogg"):
			LOG('YampScreen: searchCoverID3: ogg', 'spe')
			try:
				file_ = OggVorbis(path)
				for b64_data in file_.get("metadata_block_picture", []):
					try:
						data = b64decode(b64_data)
					except (TypeError, ValueError):
						continue
					try:
						picture = Picture(data)
					except FLACError:
						continue
					if picture is not None:
						isOgg = True
						mime = picture.mime
						data = picture.data  #  check for type=3 (FrontCover)?
						ftype = 3
			except Exception:
				print_exc()
		# mp3, mp4, ogg and flac
		if mime:
			LOG('YampScreen: searchCoverID3 : 	mime: %s' % (mime), 'spe')
			LOG('YampScreen: searchCoverID3 : 	type: %d' % (ftype), 'spe')
			if mime.lower().endswith("png"):
				ext = ".png"
			elif mime.lower().endswith("jpg"):
				ext = ".jpg"
			elif mime.lower().endswith("jpeg"):
				ext = ".jpeg"
			else:
				try:
					ext = mime.lower().rsplit('/', 1)[1]
				except Exception:
					ext = ""
				LOG('YampScreen: searchCoverID3: MP3/Flac: ignored cover file with extension %s' % (ext), 'spe')
				ext = ""  # ignore all other files (bmp, ...)
			if ext:
				filename = "/tmp/.coverartid3_" + str(self.coverIndex) + ext
				self.coverIndex = (self.coverIndex + 1) % COVER_MAXINDEX
				LOG('YampScreen: searchCoverID3: MP3/Flac: write coverart file: %s' % (filename), 'spe')
				if data:
					img = Image.open(BytesIO(data))  # save coverArtFile with max fixed size or smaller
					img.thumbnail((600, 450) if RESOLUTION == "FHD" else (400, 300), Image.LANCZOS)
					img.save(filename, format="jpeg", quality=25)
					img.close()
#					with open(filename, 'wb') as coverArtFile:  # save coverArtFile with original size
#						coverArtFile.write(data)
				if isMp4:
					self.pixNumCover = COVERS_MP4
				elif isM4a:
					self.pixNumCover = COVERS_M4A
				elif isFlac:
					self.pixNumCover = COVERS_FLAC
				elif isOgg:
					self.pixNumCover = COVERS_OGG
				else:
					self.pixNumCover = COVERS_MP3
				self.coverFoundPrio = prio
		LOG('YampScreen: searchCoverID3: end: return filename: %s' % (filename), 'spe')
		return filename

	# Look for <title>.<ext> in current directory (without albumcover.*)
	def searchCoverDirectoryTitle(self, path, fullname, title, prioList):
		if 'coverDirTitle' in prioList:
			prio = prioList.index('coverDirTitle') + 1
		else:
			return fullname
		LOG('YampScreen: searchCoverDirectoryTitle: prio: %d  coverFoundPrio: %d' % (prio, self.coverFoundPrio), 'spe')
		if self.coverFoundPrio < prio:
			return fullname  # already found with higher priority
		pdir = dirname(path)
		titleFileName = ''  #!!!check
		try:  # !!!!
			titleFileName = basename(splitext(self.playlist.getServiceRefList()[self.playlist.getCurrentIndex()].getPath())[0])
		except Exception:
			pass  # !!!!
		LOG('YampScreen: searchCoverDirectoryTitle: dir: %s titleFileName: %s' % (pdir, titleFileName), 'spe')
		filelist = self.fileListByExt(pdir, COVER_EXTENSIONS, False, COVER_MINSIZE)
		LOG('YampScreen: searchCoverDirectoryTitle: len(filelist): %d' % (len(filelist)), 'spe')
		coverNameExt = ''
		if len(filelist) > 0:
			for singleFile in filelist:
				LOG('YampScreen: searchCoverDirectoryTitle: singleFile: %s titleFileName: %s' % (singleFile, titleFileName), 'spe')
				if splitext(singleFile)[0].lower().strip() == titleFileName.lower().strip():
					coverNameExt = singleFile
					self.pixNumCover = COVERS_TITLE
					self.coverFoundPrio = prio
					LOG('YampScreen: searchCoverDirectoryTitle: cover found: %s' % (singleFile), 'spe')
					break
		if not coverNameExt:
			return fullname
		coverExt = splitext(coverNameExt)[1]
		try:
			coverSourcepath = join(pdir, coverNameExt)
			fullname = "/tmp/.coverartdirtitle" + str(self.coverIndex) + coverExt
			self.coverIndex = (self.coverIndex + 1) % COVER_MAXINDEX
			self.readWriteFileBinary(coverSourcepath, fullname)
		except Exception as e:
			LOG('YampScreen: searchCoverDirectoryTitle: write coverartdirtitle: EXCEPT: %s' % (str(e)), 'err')
		LOG('YampScreen: searchCoverDirectoryTitle: end: fullname %s' % (fullname), 'spe')
		return fullname

	# Look for any picture in current directory (without albumcover.*)
	def searchCoverDirectoryAny(self, path, fullname, prioList):
		if 'coverDirAny' in prioList:
			prio = prioList.index('coverDirAny') + 1
		else:
			return fullname
		LOG('YampScreen: searchCoverDirectoryAny: prio: %d  coverFoundPrio: %d' % (prio, self.coverFoundPrio), 'spe')
		if self.coverFoundPrio < prio:
			LOG('YampScreen: searchCoverDirectoryAny: already found: fullname %s' % (fullname), 'spe')
			return fullname  # already found with higher priority
		pdir = dirname(path)
		LOG('YampScreen: searchCoverDirectoryAny: pdir: %s' % (pdir), 'spe')
		filelist = self.fileListByExt(pdir, COVER_EXTENSIONS, False, COVER_MINSIZE)
		LOG('YampScreen: searchCoverDirectoryAny: len(filelist): %d' % (len(filelist)), 'spe')
		if len(filelist) > 0:
			for singleFile in filelist:
				LOG('YampScreen: searchCoverDirectoryAny: singlefile: %s' % (singleFile), 'spe')
				if singleFile.lower().startswith('albumcover'):
					LOG('YampScreen: searchCoverDirectoryAny: singleFile in Filelist startswith: %s' % (singleFile), 'spe')
					filelist.remove(singleFile)
		if len(filelist) > 0:
			self.pixNumCover = COVERS_DIRANY
			self.coverFoundPrio = prio

			coverNameExt = filelist[0]
			LOG('YampScreen: searchCoverDirectoryAny: coverNameExt: %s' % (coverNameExt), 'spe')
			coverExt = splitext(coverNameExt)[1]
			try:
				coverSourcepath = join(pdir, coverNameExt)
				LOG('YampScreen: searchCoverDirectoryAny: coverSourcepath: %s' % (coverSourcepath), 'spe')
				fullname = "/tmp/.coverartdirany" + str(self.coverIndex) + coverExt
				self.coverIndex = (self.coverIndex + 1) % COVER_MAXINDEX
				self.readWriteFileBinary(coverSourcepath, fullname)
			except Exception as e:
				LOG('YampScreen: searchCoverDirectoryAny: write coverartdirany: EXCEPT: %s' % (str(e)), 'err')
			LOG('YampScreen: searchCoverDirectoryAny: end: coverArtfile: %s' % (fullname), 'spe')
		return fullname

	#	Look for albumCover in current directory
	def searchCoverAlbum(self, path, fullname, prioList):
		if 'coverAlbum' in prioList:
			prio = prioList.index('coverAlbum') + 1
		else:
			return fullname
		LOG('YampScreen: searchCoverAlbum: prio: %d  coverFoundPrio: %d' % (prio, self.coverFoundPrio), 'spe')
		if self.coverFoundPrio < prio:
			LOG('YampScreen: searchCoverAlbum: already found: fullname %s' % (fullname), 'spe')
			return fullname		#already found with higher priority
		pdir = dirname(path)
		LOG('YampScreen: searchCoverAlbum: pdir: %s' % (pdir), 'spe')
		filelist = list(self.fileListByExt(pdir, COVER_EXTENSIONS, False, COVER_MINSIZE))
		LOG('YampScreen: searchCoverAlbum: filelist): %s' % (filelist), 'spe')
		if len(filelist) > 0:
			rlist = []
			for i in range(len(filelist)):
				LOG('YampScreen: searchCoverAlbum: singlefile: %s' % (filelist[i]), 'spe')
				if not filelist[i].lower().startswith('albumcover'):
					LOG('YampScreen: searchCoverAlbum: removelist: singlefile: %s' % (filelist[i]), 'spe')
					rlist.append(i)
			for i in rlist[::-1]:
				LOG('YampScreen: searchCoverAlbum: remove: singlefile: %s' % (filelist[i]), 'spe')
				filelist.pop(i)
		LOG('YampScreen: searchCoverAlbum: len(filelist): %d' % (len(filelist)), 'spe')
		if len(filelist) > 0:
			LOG('YampScreen: searchCoverAlbum: filelist[0]: %s' % (filelist[0]), 'spe')
			self.pixNumCover = COVERS_ALB
			self.coverFoundPrio = prio
			coverNameExt = filelist[0]
			coverExt = splitext(coverNameExt)[1]
			LOG('YampScreen: searchCoverAlbum: coverNameExt: %s  coverExt: %s' % (coverNameExt, coverExt), 'spe')
			try:
				coverSourcepath = join(pdir, coverNameExt)
				fullname = "/tmp/.coverartalbum" + str(self.coverIndex) + coverExt
				self.coverIndex = (self.coverIndex + 1) % COVER_MAXINDEX
				LOG('YampScreen: searchCoverAlbum: coverSourcepath: %s  fullname: %s' % (coverSourcepath, fullname), 'spe')
				self.readWriteFileBinary(coverSourcepath, fullname)
			except Exception as e:
				LOG('YampScreen: searchCoverAlbum: write coverartalbum: EXCEPT: %s' % (str(e)), 'err')
			LOG('YampScreen: searchCoverAlbum: end: coverArtfile: %s' % (fullname), 'spe')
		return fullname

	def fileListByExt(self, path, extensions, subDirs=False, minSize=0):
		flist = []
		if subDirs:
			subFolders = []
			for dirpath, dirnames, files in walk(path):
				try:
					for file in files:
						ext = splitext(file)[1]
						try:
							size = stat(dirpath + '/' + file).st_size
						except Exception as e:
							size = 0
							LOG('YampScreen: fileListByExt: subDirs: walk: filesize EXCEPT: %s' % (str(e)), 'err')
						if ext.lower() in extensions and size >= minSize:
							flist.append(file)
				except Exception as e:
					LOG('YampScreen: fileListByExt: subDirs: : EXCEPT: %s' % (str(e)), 'err')
		else:
			try:  # !!!!check
				for file in listdir(path):
					ext = splitext(file)[1]
					try:
						size = stat(path + '/' + file).st_size
					except Exception as e:
						size = 0
						LOG('YampScreen: fileListByExt: walk: filesize EXCEPT: %s' % (str(e)), 'err')
					if ext.lower() in extensions and size >= minSize:
						flist.append(file)
			except Exception:
				pass  # !!!!check
		return flist

	def readWriteFileBinary(self, filePathSrc, filePathDest):
		if exists(filePathSrc):
			try:
				with open(filePathSrc, 'rb') as file:
					data = file.read()
				with open(filePathDest, 'wb') as file:
						file.write(data)
			except OSError as e:
				LOG('YampScreen: readWriteFile: EXCEPT: %s' % (str(e)), 'err')
		else:
			LOG('YampScreen: readWriteFile: File not found: "%s"' % filePathSrc, 'err')

	def showLyrics(self):
		if self.infoLongActive:
			self.infoLongActive = False
			return
		if not self.currentIsVideo or config.plugins.yampmusicplayer.showLyricsOnVideo.value:
			self.hideScreenSaver()
			self.screenSaverManTimer.stop()
			self.lyricsScreenActive = True
			self.session.openWithCallback(self.showLyricsCB, YampLyricsScreenV33, self, self.videoPreviewOn)

	def showLyricsCB(self):
		self.startScreenSaverManTimer()
		self.coverChangedLyrics = False
		self.coverChangedGoogleLyrics = False
		self.lyricsScreenActive = False
		if not self.currentIsVideo or self.videoStartMode != "manual":
			self.resetScreenSaverTimer()

	def getCoverArtFile(self):
		self.coverArtFile = self["coverArt"].getFileName()
		return self.coverArtFile, self.pixNumCover % COVERS_NO

	def updatePlaylistInfo(self):
		if len(self.playlist):
			self["actPlayNumber"].setText(str(self.playlist.getSelectionIndex() + 1) + ' / ' + str(len(self.playlist)))
			self.calcRemainPlaylist()
		else:
			self["actPlayNumber"].setText('0 / 0')

#--------------------- Box display methods
	def updateLCDInfo(self):
		lcdMode = config.plugins.yampmusicplayer.yampLcdMode.value
		if lcdMode == 'off':
			return
		textList = []
		text1, text2, text3 = "", "", ""
		if self.currList == "filelist":
			text1 = _("filelist")
			text2 = self.filelist.getName()
		elif self.currList == "dblist":
			text1 = _("database")
			sel = self.dblist.getSelection()
			if sel is not None:
				if sel.text.strip():
					text2 = sel.text.strip()
				else:
					text2 = sel.title.strip()
					text3 = sel.artist.strip()
		else:
			sel = self.playlist.getSelection()
			if sel is not None:
				text1 = self["songtitle"].getText()
				text2 = self["artist"].getText()
				text3 = self["album"].getText()
		if lcdMode == 'running':
			self.updateLCDText(text1 + ' - ' + text2 + ' - ' + text3, 1)
		elif lcdMode == 'oneline' or lcdMode == 'cover1':
			self.updateLCDText(text1 + ' ' + text2 + ' ' + text3, 1)
		else:
			self.updateLCDText(text1, 1)
			self.updateLCDText(text2, 2)
			self.updateLCDText(text3, 3)

	def updateLCDText(self, text, line):
		lcdMode = config.plugins.yampmusicplayer.yampLcdMode.value
		if lcdMode == 'off':
			return
		try:
			if lcdMode == 'running':
				self.LcdText = text
			else:
				self.summaries.setText(text, line)
		except Exception:
			pass

	def getLcdText(self):  # for LCD Running Text
		return (self.LcdText)

#---------------- Filelist actions
	def searchFilelist1(self):  # Search in pathname
		self.virtKeyboardActive = True
		self.session.openWithCallback(self.searchFilelistCallback1, VirtualKeyBoard, title=_("YAMP - Please enter query:"), text=self.lastTextSearch)

	def searchFilelist2(self):  # Search in filename
		self.virtKeyboardActive = True
		self.session.openWithCallback(self.searchFilelistCallback2, VirtualKeyBoard, title=_("YAMP - Please enter query:"), text=self.lastTextSearch)

	def searchFilelistCallback1(self, choice):
		if choice is not None:
			self.lastTextSearch = choice
			self.filelist.searchPath(choice)
			self.updateLCDInfo()
		self.virtKeyboardActive = False

	def searchFilelistCallback2(self, choice):
		if choice is not None:
			self.lastTextSearch = choice
			self.filelist.searchFile(choice)
			self.updateLCDInfo()
		self.virtKeyboardActive = False

#--------------- Database actions within YampScreen
# Only quick actions are executed in foreground
# Slow actions are executed in background and are interruptable, ideally without changes to the database
	def addFileToDb(self, f=''):
		con, result = ConnectDatabase()
		if con:
			con.text_factory = str
			cursor = con.cursor()
			if not f:
				f = self.filelist.getFilename()
			if f.lower().endswith(".m3u") or f.lower().endswith(".pls") or f.lower().endswith(".e2pls"):
				try:
					dbInsert(con, cursor, eServiceReference(4097, 0, f), table="playlists", update=True)
				except Exception as e:
					LOG('YampScreen: addFileToDb: playlist: dbInsert EXCEPT: %s' % (str(e)), 'err')
			else:
				dbInsert(con, cursor, self.filelist.getServiceRef(), table="titles", update=True)
			con.commit()
			cursor.close()
			con.close()
			self.updateDbMenuList()
			self.databaseChanged = True

	def deletePlaylistEntry(self):
		con, result = ConnectDatabase()
		if con:
			actIndex = 0
			try:
				actIndex = self.dblist.getSelectionIndex()
			except Exception as e:
				LOG('YampScreen: deletePlaylistEntry: actIndex: EXCEPT: %s' % (str(e)), 'err')
			con.text_factory = str
			cursor = con.cursor()
			cursor.execute('DELETE FROM Playlists WHERE playlist_id = %d;' % self.dblist.getSelection().titleID)
			con.commit()
			cursor.close()
			con.close()
			self.updateDbMenuList()
			try:
				self.dblist.moveToIndex(actIndex)
			except Exception as e:
				LOG('YampScreen: deletePlaylistEntry: moveToIndex: EXCEPT: %s' % (str(e)), 'err')

	def deleteSongEntry(self):
		con, result = ConnectDatabase()
		if con:
			actIndex = 0
			try:
				actIndex = self.dblist.getSelectionIndex()
			except Exception as e:
				LOG('YampScreen: deleteSongEntry: actIndex: EXCEPT: %s' % (str(e)), 'err')
			con.text_factory = str
			cursor = con.cursor()
			cursor.execute('DELETE FROM Titles WHERE title_id = %d;' % self.dblist.getSelection().titleID)
			con.commit()
			cursor.close()
			con.close()
			self.updateDbMenuList()
			try:
				self.dblist.moveToIndex(actIndex)
			except Exception as e:
				LOG('YampScreen: deleteSongEntry: moveToIndex: EXCEPT: %s' % (str(e)), 'err')

	def deleteArtistMbid(self):
		con, result = ConnectDatabase()
		if con:
			cursor = con.cursor()
			artistId = ""
			try:
				artistId = self.dblist.getSelection().artistID
			except Exception as e:
				LOG('YampScreen: deleteArtistMbid: artistId: EXCEPT: %s' % (str(e)), 'err')
			try:
				cursor.execute("UPDATE Artists SET mbid = NULL WHERE artist_id = %d" % (artistId))
			except Exception:
				LOG('YampScreen: deleteArtistMbid: mbid: EXCEPT', 'err')
			try:
				cursor.execute("UPDATE Artists SET picsLoadedDate = '%s' WHERE artist_id = %d" % ('2000-01-01', artistId))
			except Exception as e:
				LOG('YampScreen: deleteArtistMbid: picsLoadedDate: EXCEPT: %s' % (str(e)), 'err')
			con.commit()
			try:
				cursor.close()
			except Exception:
				pass
			con.close()
#			self.updateDbMenuList()

	def deleteArtistMbidAll(self):
		self.session.openWithCallback(self.deleteArtistMbidAllConfirmed, MessageBox, _("Do you really want to delete the musicbrainz-IDs for all artists from database?"))

	def deleteArtistMbidAllConfirmed(self, confirmed):
		con, result = ConnectDatabase()
		if con:
			cursor = con.cursor()
			cursor.execute("UPDATE Artists SET mbid = NULL")
			cursor.execute("UPDATE Artists SET picsLoadedDate = '%s'" % ('2000-01-01'))
			con.commit()
			cursor.close()
			con.close()

	def deleteArtistSongEntries(self):
		self.session.openWithCallback(self.deleteArtistSongEntriesConfirmed, MessageBox, _("Do you really want to delete all titles of artist %s from database?") % self.dblist.getSelection().artist)

	def deleteArtistSongEntriesConfirmed(self, confirmed):
		if confirmed:
			con, result = ConnectDatabase()
			if con:
				actIndex = 0
				try:
					actIndex = self.dblist.getSelectionIndex()
				except Exception as e:
					LOG('YampScreen: deleteArtistSongEntriesConfirmed: actIndex: EXCEPT: %s' % (str(e)), 'err')
				con.text_factory = str
				cursor = con.cursor()
				cursor.execute('DELETE FROM Titles WHERE artist_id = %d;' % self.dblist.getSelection().artistID)
				cursor.execute('DELETE FROM Artists WHERE artist_id = %d;' % self.dblist.getSelection().artistID)
				con.commit()
				cursor.close()
				con.close()
				self.updateDbMenuList()
				try:
					self.dblist.moveToIndex(actIndex)
				except Exception as e:
					LOG('YampScreen: deleteArtistSongEntriesConfirmed: moveToIndex: EXCEPT: %s' % (str(e)), 'err')

	def deleteAlbumSongEntries(self):
		self.session.openWithCallback(self.deleteAlbumSongEntriesConfirmed, MessageBox, _("Do you really want to delete all titles of album %s from database?") % self.dblist.getSelection().album)

	def deleteAlbumSongEntriesConfirmed(self, confirmed):
		if confirmed:
			con, result = ConnectDatabase()
			if con:
				actIndex = 0
				try:
					actIndex = self.dblist.getSelectionIndex()
				except Exception as e:
					LOG('YampScreen: deleteAlbumSongEntriesConfirmed: actIndex: EXCEPT: %s' % (str(e)), 'err')
				con.text_factory = str
				cursor = con.cursor()
				cursor.execute('DELETE FROM Titles WHERE album_id = %d;' % self.dblist.getSelection().albumID)
				cursor.execute('DELETE FROM Albums WHERE album_id = %d;' % self.dblist.getSelection().albumID)
				con.commit()
				cursor.close()
				con.close()
				self.updateDbMenuList()
				try:
					self.dblist.moveToIndex(actIndex)
				except Exception as e:
					LOG('YampScreen: deleteAlbumSongEntriesConfirmed: moveToIndex: EXCEPT: %s' % (str(e)), 'err')

	def deleteGenreSongEntries(self):
		self.session.openWithCallback(self.deleteGenreSongEntriesConfirmed, MessageBox, _("Do you really want to delete all titles of genre %s from database?") % self.dblist.getSelection().genre)

	def deleteGenreSongEntriesConfirmed(self, confirmed):
		if confirmed:
			con, result = ConnectDatabase()
			if con:
				actIndex = 0
				try:
					actIndex = self.dblist.getSelectionIndex()
				except Exception as e:
					LOG('YampScreen: deleteGenreSongEntriesConfirmed: actIndex: EXCEPT: %s' % (str(e)), 'err')
				con.text_factory = str
				cursor = con.cursor()
				cursor.execute('DELETE FROM Titles WHERE genre_id = %d;' % self.dblist.getSelection().genreID)
				cursor.execute('DELETE FROM Genres WHERE genre = %d;' % self.dblist.getSelection().genreID)
				con.commit()
				cursor.close()
				con.close()
				self.updateDbMenuList()
				try:
					self.dblist.moveToIndex(actIndex)
				except Exception as e:
					LOG('YampScreen: deleteGenreSongEntriesConfirmed: moveToIndex: EXCEPT: %s' % (str(e)), 'err')

	def deleteDateSongEntries(self):
		self.session.openWithCallback(self.deleteDateSongEntriesConfirmed, MessageBox, _("Do you really want to delete all titles of date %s from database?") % self.dblist.getSelection().date)

	def deleteDateSongEntriesConfirmed(self, confirmed):
		if confirmed:
			con, result = ConnectDatabase()
			if con:
				actIndex = 0
				try:
					actIndex = self.dblist.getSelectionIndex()
				except Exception as e:
					LOG('YampScreen: deleteDateSongEntriesConfirmed: actIndex: EXCEPT: %s' % (str(e)), 'err')
				con.text_factory = str
				cursor = con.cursor()
				cursor.execute('DELETE FROM Titles WHERE date_id = %d;' % self.dblist.getSelection().dateID)
				cursor.execute('DELETE FROM Dates WHERE date = %d;' % self.dblist.getSelection().dateID)
				con.commit()
				cursor.close()
				con.close()
				self.updateDbMenuList()
				try:
					self.dblist.moveToIndex(actIndex)
				except Exception as e:
					LOG('YampScreen: deleteDateSongEntriesConfirmed: moveToIndex: EXCEPT: %s' % (str(e)), 'err')

	def showSimilarSongs(self):
		numChoice = self.dblist.getSelectionIndex()
		self.pushDblistStack(numChoice)
		choice = self.dblist.getSelection()
		qs = "%" + choice.title.replace("'", "''") + "%"
		self.buildDbMenuList(mode=SEARCHTITLELIST, queryString=qs, menutitle=_('Search') + ':  ' + choice.title)
		self.setLeftContentTitle()
		self.setColorButtons()

	def searchSongs(self):
		self.virtKeyboardActive = True
		self.session.openWithCallback(self.searchSongsCallback, VirtualKeyBoard, title=_("YAMP - Please enter query:"), text=self.lastDbSearch)

	def searchSongsCallback(self, choice):
		if choice is not None:
			self.lastDbSearch = choice
			numChoice = self.dblist.getSelectionIndex()
			self.pushDblistStack(numChoice)
			qs = "%" + choice.replace("'", "''") + "%"
			self.buildDbMenuList(mode=SEARCHTITLELIST, queryString=qs, menutitle=_("Search: %s") % choice)
			self.setLeftContentTitle()
			self.setColorButtons()
		self.virtKeyboardActive = False

	def searchFiles(self):
		self.virtKeyboardActive = True
		self.session.openWithCallback(self.searchFilesCallback, VirtualKeyBoard, title=_("YAMP - Please enter query:"), text="")

	def searchFilesCallback(self, choice):
		if choice is not None:
			numChoice = self.dblist.getSelectionIndex()
			self.pushDblistStack(numChoice)
			qs = "%" + choice.replace("'", "''") + "%"
			self.buildDbMenuList(mode=SEARCHFILELIST, queryString=qs, menutitle=_("Search: %s") % choice)
			self.setLeftContentTitle()
			self.setColorButtons()
		self.virtKeyboardActive = False

	def searchPlaylists(self):
		self.virtKeyboardActive = True
		self.session.openWithCallback(self.searchPlaylistsCallback, VirtualKeyBoard, title=_("YAMP - Please enter query:"), text="")

	def searchPlaylistsCallback(self, choice):
		if choice is not None:
			numChoice = self.dblist.getSelectionIndex()
			self.pushDblistStack(numChoice)
			qs = "%" + choice.replace("'", "''") + "%"
			self.buildDbMenuList(mode=SEARCHPLAYLISTLIST, queryString=qs, menutitle=_("Search: %s") % choice)
			self.setLeftContentTitle()
			self.setColorButtons()
		self.virtKeyboardActive = False

	def searchArtists(self):
		self.virtKeyboardActive = True
		self.session.openWithCallback(self.searchArtistsCallback, VirtualKeyBoard, title=_("YAMP - Please enter query:"), text="")

	def searchArtistsCallback(self, choice):
		if choice is not None:
			numChoice = self.dblist.getSelectionIndex()
			self.pushDblistStack(numChoice)
			qs = "%" + choice.replace("'", "''") + "%"
			self.buildDbMenuList(mode=SEARCHARTISTLIST, queryString=qs, menutitle=_("Search: %s") % choice)
			self.setLeftContentTitle()
			self.setColorButtons()
		self.virtKeyboardActive = False

	def searchAlbums(self):
		self.virtKeyboardActive = True
		self.session.openWithCallback(self.searchAlbumsCallback, VirtualKeyBoard, title=_("YAMP album search - Please enter query:"), text="")

	def searchAlbumsCallback(self, choice):
		if choice is not None and choice:
			numChoice = self.dblist.getSelectionIndex()
			self.pushDblistStack(numChoice)
			qs = "%" + choice.replace("'", "''") + "%"
			self.buildDbMenuList(mode=SEARCHALBUMLIST, queryString=qs, menutitle=_("album search: %s") % choice)
			self.setLeftContentTitle()
			self.setColorButtons()
		self.virtKeyboardActive = False

	def searchGenres(self):
		self.virtKeyboardActive = True
		self.session.openWithCallback(self.searchGenresCallback, VirtualKeyBoard, title=_("YAMP - Please enter query:"), text="")

	def searchGenresCallback(self, choice):
		if choice is not None:
			numChoice = self.dblist.getSelectionIndex()
			self.pushDblistStack(numChoice)
			qs = "%" + choice.replace("'", "''") + "%"
			self.buildDbMenuList(mode=SEARCHGENRELIST, queryString=qs, menutitle=_("Search: %s") % choice)
			self.setLeftContentTitle()
			self.setColorButtons()
		self.virtKeyboardActive = False

	def searchCurrentSong(self):
		numChoice = self.dblist.getSelectionIndex()
		self.pushDblistStack(numChoice)
		choice = self.currTitle
		qs = "%" + choice.replace("'", "''") + "%"
		self.buildDbMenuList(mode=SEARCHTITLELIST, queryString=qs, menutitle=choice)
		self.setLeftContentTitle()
		self.setColorButtons()

	def searchCurrentArtist(self):
		numChoice = self.dblist.getSelectionIndex()
		self.pushDblistStack(numChoice)
		choice = self.currArtist
		qs = "%" + choice.replace("'", "''") + "%"
		self.buildDbMenuList(mode=SEARCHARTISTTITLELIST, queryString=qs, menutitle=choice)
		self.setLeftContentTitle()
		self.setColorButtons()

	def searchCurrentAlbum(self):
		numChoice = self.dblist.getSelectionIndex()
		self.pushDblistStack(numChoice)
		choice = self.currAlbum
		qs = "%" + choice.replace("'", "''") + "%"
		self.buildDbMenuList(mode=SEARCHALBUMTITLELIST, queryString=qs, menutitle=choice)
		self.setLeftContentTitle()
		self.setColorButtons()

	def jumpToEntry(self):
		self.virtKeyboardActive = True
		self.session.openWithCallback(self.jumpToEntryCallback, VirtualKeyBoard, title=_("YAMP - Jump to letter(s):"), text="")

	def jumpToEntryCallback(self, choice):
		if choice is not None:
			upperChoice = choice.upper()
			length = len(self.dblist)
			if length > 1:
				self.dblist.moveToIndex(1)
				if self.dblist.mode < TITLELIST:
					while self.dblist.getSelection().text.upper() < upperChoice and self.dblist.getSelectionIndex() < length - 1:
						self.dblist.down()
				else:
					while self.dblist.getSelection().title.upper() < upperChoice and self.dblist.getSelectionIndex() < length - 1:
						self.dblist.down()
				self.dblist.updateList()
		self.virtKeyboardActive = False

	def compactDatabase(self):
		msg = _("Do you really want to compact the database?\nThis may take a while...")
		self.session.openWithCallback(self.compactDatabaseConfirmed, MessageBox, msg)

	def compactDatabaseConfirmed(self, confirmed):
		if confirmed:
			con, result = ConnectDatabase()
			if con:
				try:
					con.execute('VACUUM')
				except Exception as e:
					LOG('YampScreen: compactDatabaseConfirmed: compact (VACUUM): EXCEPT: %s' % (str(e)), 'err')
				try:
					con.close()
					self.updateDbMenuList()
				except Exception as e:
					LOG('YampScreen: compactDatabaseConfirmed: close Database: EXCEPT: %s' % (str(e)), 'err')

	def clearDatabaseFromMenu(self):
		self.session.openWithCallback(self.clearDatabaseConfirmed, MessageBox, _("Do you really want to clear the whole database?"))

	def clearDatabaseConfirmed(self, confirmed):
		if confirmed:
			clearDatabase()
			try:
				self.updateDbMenuList()
			except Exception as e:
				LOG('YampScreen: clearDatabaseConfirmed: close Database: EXCEPT: %s' % (str(e)), 'err')

#-------------- Artist Art functions
	def getArtistPics(self, artist):
		if self.searchFanartConfig == 'off':
			return
		if not self.fanarttvPersonalApikey.strip():
			self.fanartDlTime = FANARTDLTIME
		else:
			self.fanartDlTime = FANARTDLTIMEPERSONAL
		LOG('YampScreen: getArtistPics: Start: artist: %s artistFanartDl: %s fanartdltime: %d' % (artist, self.artistFanartDl, self.fanartDlTime), 'all')

		if config.plugins.yampmusicplayer.capitalizeTitleAndArtist.value:
			artist = titlecase(artist)
		if self.artistFanartDl:
			return  # last download not yet finished
		if self.fanartDisplayTimer.isActive:
			self.fanartDisplayTimer.stop()
		self.artistFanartDl = artist
		self.getArtistMbid()  # Muscibrainz Artist id from database or online

	def getArtistPicsCB(self, artistId, mbid, picsLoadedDate='2000-01-01'):
		self.showFanartNumberDl()
		if mbid is None:
			mbid = ''
			self.artistFanartDl = ''
		LOG('YampScreen: getArtistPicsCB: artist: %s artistid: %d mbid: %s ' % (self.artistFanartDl, artistId, mbid), 'all')
		self.newArtistBg = False
		if self.searchFanartConfig == 'off':
			return
		try:
			if mbid:
				if self.searchFanartConfig == 'newArtists':
					if picsLoadedDate == '2000-01-01':
						configDays = 0  # is new Artist, search for pics
					else:
						configDays = 1000  # no new Artist, do notsearch for pics
				elif self.searchFanartConfig == 'always':
					configDays = 0  # search for pics
				else:
					configDays = int(self.searchFanartConfig)  # take period from config
				today = datetime.now().date()
				picsLoadedDate = datetime.strptime(picsLoadedDate, '%Y-%m-%d').date()
				diff = today - picsLoadedDate
				days = diff.days
				if (today - picsLoadedDate).days < configDays:
					LOG('YampScreen: getArtistPicsCB: artist: %s: pics already loaded, finish' % (self.artistFanartDl), 'all')
					self.artistFanartDl = ''
					return
				artworkPath = config.plugins.yampmusicplayer.screenSaverArtworkPath.value
				self.pathArtistPic = self.getArtistArtDir(artworkPath, self.artistFanartDl)
				LOG('YampScreen: getArtistPicsCB: pathArtistPic: %s' % (self.pathArtistPic), 'all')
				try:
					if not exists(self.pathArtistPic):
						makedirs(self.pathArtistPic)
					try:
						self.getFanarttv(mbid, artistId)
					except Exception as e:
						LOG('YampScreen: getArtistPicsCB: getFanarttv: EXCEPT: %s' % (str(e)), 'err')
						self.artistFanartDl = ''
				except Exception as e:
					LOG('YampScreen: getArtistPicsCB: could not create Artistartdir %s EXCEPT: %s' % (self.pathArtistPic, str(e)), 'err')
					self.artistFanartDl = ''
		except Exception as e:
			LOG('YampScreen: getArtistPicsCB: End: EXCEPT: %s' % (str(e)), 'err')
			self.artistFanartDl = ''

	def fanartDisplayStop(self):
		if self.fanartDisplayTimer.isActive():
			self.fanartDisplayTimer.stop()
		self.showFanartNumberDl()

	def showFanartNumberDl(self, text='', failed=False):
		try:
			if failed:
				self.fanartDisplayTimer.start(8000, True)
			if not text:
				lenList = len(self.artistBgPicsList)
				if lenList > 0:
					txt = _("Artist-Art-Pictures\ndownloading: ")
					if config.plugins.yampmusicplayer.yampSkin.value.startswith("fhd"):
						txt = txt + '\n'
					txt = txt + str(self.fanartNumberDl - lenList + 1) + ' / ' + str(self.fanartNumberDl)
				else:
					txt = ''
			else:
				txt = text
			if txt:
				self["musicbrainzlogo"].setBoolean(True)
				self["fanartlogo"].setBoolean(True)
				self["fanartdownload"].show()
				self["downloadBackground"].show()
			else:
				self["musicbrainzlogo"].setBoolean(False)
				self["fanartlogo"].setBoolean(False)
				self["fanartdownload"].hide()
				self["downloadBackground"].hide()
			self["fanartdownload"].setText(txt)
		except Exception as e:
			LOG('YampScreen: showFanartNumberDl: End: EXCEPT: %s' % (str(e)), 'err')

# get artist mbid form database or musicbrainz online
	def getArtistMbid(self):
		con, result = ConnectDatabase()
		mbid = None
		if con:
			LOG('YampScreen: getArtistMbid: search artist: %s' % (self.artistFanartDl), 'all')
			con.row_factory = Row
			cursor = con.cursor()
			cursor.execute('SELECT * FROM Artists WHERE artist="%s";' % (self.artistFanartDl))
			rows = cursor.fetchone()
			try:
				artistId = rows['artist_id']
			except Exception:
				LOG('YampScreen: getArtistMbid: No Artist-ID in DB: EXCEPT', 'all')
				msg = _("Artist %s not in database,\nonline search for artist-art at fanart.tv not possible") % (self.artistFanartDl)
				self.session.open(MessageBox, msg, type=MessageBox.TYPE_INFO, timeout=8)
				self.artistFanartDl = ''
				cursor.close()
				con.close()
				return
			artistname = rows['artist']
			mbid = rows['mbid']
			picsLoadedDate = rows['picsLoadedDate']
			LOG('YampScreen: getArtistMbid: found artist in DB: artistname: %s mbid: %s picsLoadedDate: %s artistId: %d' % (artistname, mbid, picsLoadedDate, artistId), 'all')
			cursor.close()
			con.close()
			try:
				if mbid is not None:
					LOG('YampScreen: getArtistMbid: mbid: %s artistId: %d' % (mbid, artistId), 'all')
					self.getArtistPicsCB(artistId, mbid, picsLoadedDate)
				else:
					LOG('YampScreen: getArtistMbid: mbid: None, try to get it online', 'all')
					try:
						self.getMbidOnline(artistId)
					except Exception as e:
						self.artistFanartDl = ''
						LOG('YampScreen: getArtistMbid: getMbidOnline: EXCEPT: %s' % (str(e)), 'err')
			except Exception as e:
				self.artistFanartDl = ''
				LOG('YampScreen: getArtistMbid: End: EXCEPT: %s' % (str(e)), 'err')

	def getMbidOnline(self, artistId):
		mbid = None
		artistlist = []
		try:
			txt = _('trying to get ')
			if config.plugins.yampmusicplayer.yampSkin.value.startswith("fhd"):
				txt = txt + '\n'
			txt = txt + 'MbID\nMusicbrainz-ID...'
			self.showFanartNumberDl(txt)
			searchArtist = self.artistFanartDl.replace('!', r'\!')
			searchArtist = searchArtist.replace('/', r'\/').strip()
			LOG('YampScreen: getMbidOnline: Artist: %s searchArtist: %s ' % (self.artistFanartDl, searchArtist), 'all')
			if config.plugins.yampmusicplayer.searchMbidMode.value == 'standard':
				url = "http://musicbrainz.org/ws/2/artist/?query=%s&dismax=true" % (quote(searchArtist))
			else:
				url = "http://musicbrainz.org/ws/2/artist/?query=%s" % (quote(searchArtist))
			LOG('YampScreen: getMbidOnline: url: %s' % (url), 'all')
			callback = boundFunction(self.getMbidParseXML, artistId)
			callInThread(getUrlData, url, callback=callback, fail=self.getMbidFailed)
		except Exception as e:
			self.artistFanartDl = ''
			LOG('YampScreen: getMbidOnline: result musicbrainz search: EXCEPT: %s' % (str(e)), 'err')

	def getMbidParseXML(self, artistId, response):
		xmlstring = response.text
		artistlist = self.mbidParse(xmlstring)
		LOG('YampScreen: getMbidParseXML: artistlist: %s' % (artistlist), 'all')
		if len(artistlist) == 0:
			msg = _("Music-Brainz ID for Artist %s not found,\nonline search for artist-art at fanart.tv not possible") % (self.artistFanartDl)
			self.session.open(MessageBox, msg, type=MessageBox.TYPE_INFO, timeout=8)
			self.artistFanartDl = ''
			self.showFanartNumberDl(text=_('MbID\n not found'), failed=True)
		else:
			self.showArtistSelection(artistlist, artistId)  # maybe several artists found

	def mbidParse(self, xmlstring):
		minscore = config.plugins.yampmusicplayer.searchMbidMinScore.value
		if self.currentIsVideo:
			minscore = 90
		LOG('YampScreen: mbidParse: Start: minscore: %d xmlstring: %s' % (minscore, xmlstring), 'all')
		artistlist = []
		try:
			xmlstring = xmlstring.replace('#', '')
			xmlstring = sub(' xmlns:ext=(")+.+ext-2.0', "", xmlstring)
			xmlstring = sub(' xmlns=.+mmd-2.0', "", xmlstring)
			xmlstring = xmlstring.replace("ns2:score", "score")
			xmlstring = xmlstring.replace('\"\"\"', '\"')
			xmlstring = xmlstring.replace('\"\"', '\"')
		except Exception as e:
			LOG('YampScreen: mbidParse: xmlstring = sub: EXCEPT: %s' % (str(e)), 'err')
		root = [{}]
		try:
			root = xmlET.fromstring(xmlstring)
		except Exception as e:
			self.artistFanartDl = ''
			LOG('YampScreen: mbidParse: xmlET.fromstring: EXCEPT: %s' % (str(e)), 'err')
		artistListXml = root[0]
		try:
			for artists in artistListXml:
				score = artists.get('score')
				if score is None or int(score) == 0:
					score = minscore
				if int(score) >= minscore:
					elArea = ""
					name, atype, gender, country, disambiguation, area, artistid = "", "", "", "", "", "", ""
					try:
						artistid = artists.get('id', '')
						atype = artists.get('type', '')
						name = ''
						country = ''
						disambiguation = ''
						gender = ''
						area = ''
						nametag = artists.find('name')
						if nametag is not None:
							name = nametag.text
						countrytag = artists.find('country')
						if countrytag is not None:
							country = countrytag.text
						disambiguationtag = artists.find('disambiguation')
						if disambiguationtag is not None:
							disambiguation = disambiguationtag.text
						gendertag = artists.find('gender')
						if gendertag is not None:
							gender = gendertag.text
						elArea = artists.find('area')
					except Exception as e:
						LOG('YampScreen: mbidParse: parser1: EXCEPT: %s' % (str(e)), 'err')
					if elArea is not None:
						areaNametag = elArea.find('name')
						if areaNametag:
							area = areaNametag
					try:
						artistlist.append([name, atype, gender, country, disambiguation, area, artistid])
					except Exception as e:
						LOG('YampScreen: mbidParse: artistlist.append: EXCEPT: %s' % (str(e)), 'err')
		except Exception as e:
			LOG('YampScreen: mbidParse: for artists...: EXCEPT: %s' % (str(e)), 'err')
		return artistlist

	def getMbidFailed(self, result):
		self.artistFanartDl = ''
		self.showFanartNumberDl(text=_('MbID\n download failed'), failed=True)

	def writeMbidToDb(self, mbid, artistId):
		LOG('YampScreen: writeMbidToDb: Start: artistId: %d mbid: %s' % (artistId, mbid or ''), 'all')
		if not mbid:
			con, result = ConnectDatabase()
			if con:
				cursor = con.cursor()
				mbid = str(mbid)
				cursor.execute("UPDATE Artists SET mbid='%s' WHERE artist_id=%d" % (mbid, artistId))
				con.commit()
				cursor.close()
				con.close()

	def getFanarttv(self, mbid, artistId):
		user_agent = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3'
		headers = {'User-Agent': user_agent}
		mbid = str(mbid)
		self.artistIdFanart = artistId
		url = "http://webservice.fanart.tv/v3/music/%s?api_key=%s" % (quote_plus(mbid), quote_plus(self.fanarttvAppApikey))
		if self.fanarttvPersonalApikey.strip():
			url = url + '&client_key=%s' % (quote_plus(self.fanarttvPersonalApikey))
		LOG('YampScreen: getFanarttv:  url: %s' % url, 'all')
		callInThread(getUrlData, url, callback=self.getFanartParseJson, fail=self.getFanartFailed)
		self.showFanartNumberDl(text=_('trying to get\npicture list...'))

	def getFanartParseJson(self, resultString):
		try:
			LOG('YampScreen: getFanartParseJson: Start: artist: %s resultString > 100: %d' % (self.artistFanartDl, len(resultString.content) > 100), 'all')
			jsonDict = resultString.json()
			if 'artistbackground' in jsonDict:
				numberPics = len(jsonDict["artistbackground"])
			else:
				numberPics = 0
			LOG('YampScreen: getFanartParseJson: number of pictures: %d' % (numberPics), 'all')
			if numberPics == 0:
				LOG('YampScreen: getFanartParseJson: no artistart pictures found for %s' % (self.artistFanartDl), 'all')
				self.artistFanartDl = ''
				self.showFanartNumberDl(text=_('no pictures\nfound'), failed=True)
				self.writePicsloadedToDb()  # no pictures, do not search again
				return
			picNum = 0
			fulllist = []
			for pic in jsonDict["artistbackground"]:
				picNum += 1
				url = pic["url"]
				LOG('YampScreen: getFanartParseJson: No: %d  url: %s' % (picNum, url), 'all')
				fulllist.append(url)
			# check, if picture already existing
			tempList = []
			for pic in fulllist:
				searchPath = join(self.pathArtistPic, basename(pic))  # .encode()
				if not exists(searchPath) or not isfile(searchPath):
					tempList.append(pic)
			self.artistBgPicsList = tempList
			LOG('YampScreen: getFanartParseJson: BgListaftercheck: len: %d \n%s' % (len(self.artistBgPicsList), '\n'.join(self.artistBgPicsList)), 'all')
			try:
				if len(self.artistBgPicsList) > 0:  # pictures existing for download
					self.fanartNumberDl = len(self.artistBgPicsList)
					self.fanartSuccessDl = 0
					self.downloadPiclist()
				else:
					self.writePicsloadedToDb()  # no pictures
					self.artistFanartDl = ''
			except Exception as e:
				self.artistFanartDl = ''
				LOG('YampScreen: getFanartParseJson: downloadPiclist: EXCEPT: %s' % (str(e)), 'err')
		except Exception as e:
			self.artistFanartDl = ''
			try:
				LOG('YampScreen: getFanartParseJson: artist: %s resultString > 100: %d EXCEPT: %s' % (self.artistFanartDl, len(resultString) > 100, str(e)), 'err')
			except Exception as e:
				LOG('YampScreen: getFanartParseJson: LOG: EXCEPT: %s' % (str(e)), 'err')
		self.showFanartNumberDl()

	def getFanartFailed(self, result):
		try:
			if '404 not found' in str(result).lower():
				self.showFanartNumberDl(text=_('fanart.tv\nno picture found'), failed=True)
				LOG('YampScreen: getFanartFailed: 404 not found', 'all')
				self.writePicsloadedToDb()
			else:
				self.showFanartNumberDl(text=_('picture list\ndownload failed'), failed=True)
				LOG('YampScreen: getFanartFailed: result: %s' % (str(result)), 'all')
		except Exception as e:
			LOG('YampScreen: getFanartFailed: EXCEPT: %s' % (str(e)), 'err')
		self.artistFanartDl = ''

	def downloadPiclist(self):
		LOG('YampScreen: downloadPiclist: Start: artist: %s len(artistBgPicsList): %d newArtistBg: %d' % (self.artistFanartDl, len(self.artistBgPicsList), self.newArtistBg), 'all')
		if self.fanartDlTime == FANARTDLTIME and (self.fanartNumberDl - len(self.artistBgPicsList)) == 5:
			LOG('YampScreen: downloadPiclist: limit personal api key', 'all')
			self.artistBgPicsList = []
		# download finished and artist is still the artist of download -> initScreensaver
		if len(self.artistBgPicsList) == 0:
			LOG('YampScreen: downloadPiclist: no (more) pictures', 'all')
			if self.fanartSuccessDl == self.fanartNumberDl:
				LOG('YampScreen: downloadPiclist: all successfully downloaded, writePicsloadedToDb: success: %d total: %d' % (self.fanartSuccessDl, self.fanartNumberDl), 'all')
				self.writePicsloadedToDb()
			if self.newArtistBg:
				currartist = self.currArtist
				if config.plugins.yampmusicplayer.capitalizeTitleAndArtist.value:
					currartist = titlecase(currartist)
				if currartist == self.artistFanartDl:
					self.initScreenSaver(artist=currartist)
					LOG('YampScreen: downloadPiclist: new artistbgpictures: initScreenSaver', 'all')
			self.artistFanartDl = ''
			self.showFanartNumberDl()
			return
		LOG('YampScreen: downloadPiclist: len(list) > 0: artistBgPicsList: %s' % (self.artistBgPicsList), 'all')
		url = ""
		try:
			url = self.artistBgPicsList[0]  # .encode()
		except Exception as e:
			LOG('YampScreen: downloadPiclist: url: EXCEPT: %s' % (str(e)), 'err')
		filename, fullname = "", ""
		try:
			filename = url.rsplit('/', 1)[1]
		except Exception as e:
			LOG('YampScreen: downloadPiclist: filename: EXCEPT: %s' % (str(e)), 'err')
		try:
			fullname = join(self.pathArtistPic, filename)
		except Exception as e:
			LOG('YampScreen: downloadPiclist: fullname: EXCEPT: %s' % (str(e)), 'err')
		try:
			LOG("YampScreen: downloadPiclist: url: %s fullname: %s" % (url, fullname), 'all')
		except Exception as e:
			LOG('YampScreen: LOG downloadPiclist: url, filename: EXCEPT: %s' % (str(e)), 'err')
		try:
			LOG("YampScreen: downloadPiclist: getUrlData: url: %s fullname: %s" % (url, fullname), 'all')
		except Exception as e:
			LOG('YampScreen: downloadPiclist: LOG getUrlData: url: EXCEPT: %s' % (str(e)), 'err')
		self.showFanartNumberDl()
		try:
			LOG('YampScreen: downloadPiclist: fanartDlTimer start', 'all')
			self.fanartDlTimer.start(self.fanartDlTime, True)
			self.artistFanartDlFinished = False
			callback = boundFunction(self.artistartDownloadFinished, fullname)
			callInThread(getUrlData, url, fullname, callback=callback, fail=self.artistartDownloadFailed)
		except Exception as e:
			LOG('YampScreen: downloadPiclist: getUrlData: EXCEPT: %s' % (str(e)), 'err')

	def fanartDlOk(self):  # from fanartDlTimer
		LOG('YampScreen: fanartDlOk: DlFinished: %d' % (self.artistFanartDlFinished), 'all')
		if not self.artistFanartDlFinished:
			return
		self.downloadPiclist()

	def artistartDownloadFinished(self, fullname, result):
		self.artistFanartDlFinished = True
		self.fanartSuccessDl += 1
		try:
			LOG('YampScreen: artistartDownloadFinished: success: %d fullname: %s artist: %s' % (self.fanartSuccessDl, fullname, self.artistFanartDl), 'all')
			if len(self.artistBgPicsList) > 0:
				self.artistBgPicsList.remove(self.artistBgPicsList[0])
			self.newArtistBg = True
		except Exception as e:
			LOG('YampScreen: artistartDownloadFinished: remove: EXCEPT: %s' % (str(e)), 'err')
		try:
			if not self.fanartDlTimer.isActive():
				self.downloadPiclist()
		except Exception as e:
			LOG('YampScreen: artistartDownloadFinished: downloadPiclist: EXCEPT: %s' % (str(e)), 'err')

	def artistartDownloadFailed(self, result):
		artist = self.artistFanartDl
		LOG("YampScreen: artistartDownloadFailed: DlTimerActive: %d artist: %s" % (self.fanartDlTimer.isActive(), self.artistFanartDl), 'all')
		self.artistFanartDlFinished = True
		if len(self.artistBgPicsList) > 0:
			try:
				actDownload = self.artistBgPicsList[0]
				self.artistBgPicsList.remove(actDownload)
			except Exception as e:
				LOG('YampScreen: artistartDownloadFailed: remove: EXCEPT: %s' % (str(e)), 'err')
		if not self.fanartDlTimer.isActive():
			if len(self.artistBgPicsList) > 0:
				self.fanartDlTimer.start(self.fanartDlTime, True)
			self.downloadPiclist()

	def writePicsloadedToDb(self):
		con, result = ConnectDatabase()
		if con:
			try:
				cursor = con.cursor()
			except Exception as e:
				LOG('YampScreen: writePicsloadedToDb: cursor: EXCEPT: %s' % (str(e)), 'err')
				con.close()
				return
			try:
				date = datetime.now().date()
				cursor.execute("UPDATE Artists SET picsLoadedDate = '%s' WHERE artist_id=%d" % (date, self.artistIdFanart))
				LOG('YampScreen: writePicsloadedToDb: write picsLoadedDate: %s artistId: %d' % (date, self.artistIdFanart), 'all')
			except Exception as e:
				LOG('YampScreen: writePicsloadedToDb: write picsLoadedDate: EXCEPT: %s' % (str(e)), 'err')
			try:
				con.commit()
			except Exception as e:
				LOG('YampScreen: writePicsloadedToDb: commit: EXCEPT: %s' % (str(e)), 'err')
			try:
				cursor.close()
			except Exception:
				pass
			try:
				con.close()
			except Exception as e:
				LOG('YampScreen: writePicsloadedToDb: close: EXCEPT: %s' % (str(e)), 'err')

	def getUnixErrorString(self, s):
		# unicode error fix dirty....
		try:
			s = s.replace('\xe9', 'e')
		except Exception as e:
			LOG('YampScreen: getUnixErrorString: EXCEPT: %s' % (str(e)), 'err')
		return s

	def showArtistSelection(self, artistlist, artistId):  # select artist, if several with same name
		try:
			if len(artistlist) > 1:
				self.hideScreenSaver()
				menu = []
				textLen = []
				idx = 0
				try:
					for artis in artistlist:
						text = ', '.join(artis[:6]).rstrip(', ')  # .encode("utf-8", 'ignore')
						text = sub(r'(, )+', ', ', text)
						LOG('YampScreen: showArtistSelection: len: %d text: %s' % (len(text), text), 'all')
						menu.append((text, str(idx)))
						textLen.append(len(text) + 10)
						idx += 1
				except Exception as e:
					LOG('YampScreen: showArtistSelection: menu append: EXCEPT: %s' % (str(e)), 'err')
				self.par1 = artistlist
				self.par2 = artistId
				title = _('Several Artists %s found at musicbrainz.org, please select Artist') % (self.artistFanartDl)
				LOG('YampScreen: showArtistSelection: len: %d title: %s' % (len(title), title), 'all')
				textLen.append(len(title))
				title = title.ljust(max(textLen)) + '.'
				try:
					self.session.openWithCallback(self.showArtistSelectionCB, ChoiceBox, title=title, list=menu)
				except Exception as e:
					LOG('YampScreen: showArtistSelection: ChoiceBox: EXCEPT: %s' % (str(e)), 'err')
					self.getArtistPicsCB(artistId, None)
			elif len(artistlist) == 1:
				mbid = artistlist[0][6]
				self.writeMbidToDb(mbid, artistId)
				self.getArtistPicsCB(artistId, mbid)
			else:
				self.getArtistPicsCB(artistId, None)
		except Exception as e:
			LOG('YampScreen: showArtistSelection: : EXCEPT: %s' % (str(e)), 'err')
			self.getArtistPicsCB(artistId, None)

	def showArtistSelectionCB(self, choice):
		artistlist = self.par1
		artistId = self.par2
		if choice is None:
			mbid = None
		else:
			mbid = artistlist[int(choice[1])][6]
			self.writeMbidToDb(mbid, artistId)
		self.getArtistPicsCB(artistId, mbid)
		if not self.currentIsVideo or self.videoStartMode != "manual":
			self.resetScreenSaverTimer()


# Database actions own thread
# Possibly blocking database actions use their own thread and are called from their own screen (YampDatabaseScreen)
class ThreadQueue:
	def __init__(self):
		self.__list = []
		self.__lock = Lock()

	def push(self, val):
		lock = self.__lock
		lock.acquire()
		self.__list.append(val)
		lock.release()

	def pop(self):
		lock = self.__lock
		lock.acquire()
		ret = self.__list.pop()
		lock.release()
		return ret


class YampDbActions(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.__running = False
		self.__cancel = False
		self.__path = None
		self.__messages = ThreadQueue()
		self.__messagePump = ePythonMessagePump()

	def __getMessagePump(self):
		return self.__messagePump
	MessagePump = property(__getMessagePump)

	def __getMessageQueue(self):
		return self.__messages
	Message = property(__getMessageQueue)

	def __getRunning(self):
		return self.__running
	isRunning = property(__getRunning)

	def Cancel(self):
		self.__cancel = True

	def Start(self, func, dir, recursive):
		if not self.__running:
			self.__running = True
			self.__func = func
			self.__path = dir
			self.__recursive = recursive
			self.start()

	def run(self):
		self.mp = self.__messagePump
		self.__running = True
		self.__cancel = False
		con, result = ConnectDatabase()
		if con:
			con.text_factory = str
			cursor = con.cursor()
			self.counterAdded = 0
			self.counterActualized = 0
			self.counterSkipped = 0
			self.checkTime = time()
			if self.__func == "add":
				self.__messages.push((THREAD_WORKING, _("searching ... "), ""))
				self.mp.send(0)
				self.addDirToDatabase(con, cursor, self.__path, self.__recursive)
				if not self.__cancel:
					con.commit()
				cursor.close()
				con.close()
				msgAdded = _('%d files added to database\n\n') % (self.counterAdded)
				msgActualized = _('%d files actualized\n\n') % (self.counterActualized)
				msgSkipped = _('%d files skipped\n\n\n') % (self.counterSkipped)
				msgClose = _('Press OK to close.')
				msg1 = ''
				if self.__cancel:
					msg1 = _('Process aborted.')
				else:
					msg1 = _('Process finished.')
				self.__messages.push((THREAD_FINISHED, msg1, msgAdded + msgActualized + msgSkipped + msgClose))
		else:
			self.__messages.push((THREAD_FINISHED, _("Error!\nCan not open database!\nCheck if database path is correct and writeable!\n\nPress OK to close."), ""))
		self.mp.send(0)
		self.__running = False
		Thread.__init__(self)

	def addDirToDatabase(self, con, cursor, dir, recursive=True):
		global selectedDirExcludeValue, dirExcludeOptions
		filelist = YampFileList(dir, matchingPattern=r"(?i)^.*\.(mp2|mp3|wav|flac|ogg|m4a|m3u|pls|e2pls|mp4|avi|mpg|flv|m2ts|m4v|mkv|mov|mpeg|ts|wmv|divx)", useServiceRef=True, showMountpoints=False, isTop=True, additionalExtensions="4098:m3u 4098:e2pls 4098:pls")
		for x in filelist.getFileList():
			if self.__cancel:
				break
			if x[0][1] is True:  # isDir
				if recursive and x[0][0] != dir:
					# check Exclusions
					if selectedDirExcludeValue == 0:  # no excludes
						self.addDirToDatabase(con, cursor, x[0][0])
					elif selectedDirExcludeValue == 3:  # both excludes
						if (not x[1][7].startswith(dirExcludeOptions[0])) and (not x[1][7].startswith(dirExcludeOptions[1])):
							self.addDirToDatabase(con, cursor, x[0][0])
					else:  # one exclude
						if not x[1][7].startswith(dirExcludeOptions[selectedDirExcludeValue - 1]):
							self.addDirToDatabase(con, cursor, x[0][0])
					con.commit()
			else:  # isFile
				f = x[0][0].getPath()
				if f.lower().endswith(".m3u") or f.lower().endswith(".pls") or f.lower().endswith(".e2pls"):
					result = dbInsert(con, cursor, x[0][0], table="playlists", update=False)
				else:
					result = dbInsert(con, cursor, x[0][0], table="titles", update=False)
				if result == 1:
					self.counterAdded += 1
				elif result == 2:
					self.counterActualized += 1
				else:
					self.counterSkipped += 1
				if time() - self.checkTime >= 0.15:  # update interval for GUI
					msg = _("added to database (%d)\n\nactualized in database (%d)\n\nalready exists in database (%d)") % (self.counterAdded, self.counterActualized, self.counterSkipped)
					try:
						self.__messages.push((THREAD_WORKING, f, msg))
					except Exception as e:
						LOG('YampDbActions: ++ simPump added: push: EXCEPT: ' + str(e), 'err')
					self.mp.send(0)
					self.checkTime = time()


databaseActions = YampDbActions()  # Build instance of YampDbActions class


# More screens - Database Screen
class YampDatabaseScreenV33(Screen):
	def __init__(self, session, func, dir, recursive=False):
		Screen.__init__(self, session)
		xmlfile = join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampDatabase.xml")
		if not exists(xmlfile):
			LOG('YampDatabaseScreenV33: __init__: File not found: "%s"' % xmlfile, 'err')
			return
		with open(xmlfile, 'r') as f:
			self.skin = f.read()
		self.func = func
		self.dir = dir
		self.recursive = recursive
		self.finished = False
		self.LcdText = ''
		self.runningUpdate = True
		if self.func == "add":
			if self.recursive:
				self["title"] = Label(_("YAMP Music Player - Add directory incl. Subdirs to Database"))
			else:
				self["title"] = Label(_("YAMP Music Player - Add directory to Database"))
		else:
			self["title"] = Label(_("YAMP Music Player - Database Actions"))
		self["key_red"] = Label(_("Cancel"))
		self["key_green"] = Label("")
		self["message1"] = Label()
		self["message2"] = Label()
#		self["message3"] = Label()
		self["actions"] = ActionMap(["YampActions", "YampOtherActions"],
		{
			"exit": self.keyCancel,
			"red": self.keyCancel,
			"green": self.keyClose,
			"ok": self.keyClose,
		}, -1)
		self.onClose.append(self.__onClose)
		self["key_green"].setText('')
		databaseActions.MessagePump.recv_msg.get().append(self.gotThreadMsg)
		if not databaseActions.isRunning:
			databaseActions.Start(func, dir, recursive)
		self.startupTimer = eTimer()
		self.startupTimer.callback.append(self.startupChecks)
		self.runningTimer = eTimer()
		self.runningTimer.callback.append(self.runningTimerCb)
		self.onLayoutFinish.append(self.layoutFinished)

	def keyCancel(self):
		try:
			if databaseActions.isRunning:
				databaseActions.Cancel()
		except Exception as e:
			LOG('YampDatabaseScreen: keyCancel: EXCEPT: ' + str(e), 'err')

	def keyClose(self):
		try:
			if self["key_green"].getText():
				self.close()
		except Exception as e:
			LOG('YampDatabaseScreen: keyClose: EXCEPT: ' + str(e), 'err')

	def layoutFinished(self):
		self.startupTimer.start(1000, True)

	def startupChecks(self):
		self.summaries.showHideLcdCover(False)
		self.runningTimer.start(4000, False)

	def runningTimerCb(self):
		self.runningUpdate = True

	def gotThreadMsg(self, msg=""):
		msg = msg or databaseActions.Message.pop()
		if self.finished is False:
			self["message1"].setText(msg[1])
			self["message2"].setText(msg[2])
			textList = msg[2].split('\n')
			text1 = text2 = text3 = ''
			nrIns = nrAct = nrSki = '0'
			try:
				if len(textList) == 5:
					nrIns = textList[0].split()[0]
					nrAct = textList[2].split()[0]
					nrSki = textList[4].split()[0]
					text1 = nrIns + _(' inserted')
					text2 = nrAct + _(' actualized')
					text3 = nrSki + _(' skipped')
			except Exception as e:
				LOG('YampDatabaseScreen: gotThreadMsg: EXCEPT: ' + str(e), 'err')
			lcdMode = config.plugins.yampmusicplayer.yampLcdMode.value
			if lcdMode == 'running':
				if self.runningUpdate:
					self.updateLCDText(nrIns + '-' + nrAct + '-' + nrSki, 1)
					self.runningUpdate = False
			elif lcdMode == 'oneline' or lcdMode == 'cover1':
				self.updateLCDText(_("DB Insert:") + nrIns + '-' + nrAct + '-' + nrSki, 1)
			else:  # threelines or = cover3
				self.updateLCDText(text1, 1)
				self.updateLCDText(text2, 2)
				self.updateLCDText(text3, 3)
		if msg[0] == THREAD_FINISHED:
			self.finished = True
			self.updateLCDText(_('DB insert finished'), 1)
			self["key_red"].setText('')
			self["key_green"].setText(_('OK'))

	def __onClose(self):
		databaseActions.MessagePump.recv_msg.get().remove(self.gotThreadMsg)
		self.startupTimer.stop()
		self.runningTimer.stop()
		del self.startupTimer
		del self.runningTimer

	def updateLCDText(self, text, line):
		if config.plugins.yampmusicplayer.yampLcdMode.value == 'running':
			self.LcdText = text
		else:
			self.summaries.setText(text, line)

	def getLcdText(self):  # for LCD Running Text
		return (self.LcdText)

	def createSummary(self):
		confLcd = config.plugins.yampmusicplayer.yampLcdMode.value
		if confLcd == 'off':
			return
		elif confLcd == 'running':
			return YampLCDRunningScreenV33
		else:
			return YampLCDScreenV33

# General routines - Database actions


def ConnectDatabase():
	dbPath = join(config.plugins.yampmusicplayer.databasePath.value, "yamp.db")
	try:
		con = connect(dbPath)
		try:
			LOG('ConnectDatabase: dbPath: %s con: %s ' % (dbPath, con), 'all')
		except Exception as e:
			LOG('ConnectDatabase: dbPath: con : EXCEPT: ' + str(e), 'err')
		if not access(dbPath, W_OK):
			LOG('ConnectDatabase: dbPath: no write access %s' % (dbPath), 'err')
			con.close()
			return None, 2
	except Exception as e:
		LOG('ConnectDatabase: cannot open database dbPath: %s : %s' % (dbPath, str(e)), 'err')
		return None, 1
	return con, 0


def checkIfDbexists():
	dbPath = join(config.plugins.yampmusicplayer.databasePath.value, "yamp.db")
	return (exists(dbPath))


def checkDatabaseHasData():
	result = 0
	con, result = ConnectDatabase()
	if result > 0:
		return 0
	count = 0
	try:
		if con:
			cur = con.cursor()
			cur.execute("SELECT COUNT (*) FROM Titles;")
			row = cur.fetchone()
			count = row[0]
			cur.close()
	except Exception:  # Db probably has wrong/no structure
		try:
			clearDatabase()  # delete DB and build new one
			count = 0
		except Exception as e:
			LOG('Yamp.py: checkDatabaseHasData: clearDatabase: EXCEPT: %s' % (str(e)), 'err')
	return count


def clearDatabase():
	try:
		remove(join(config.plugins.yampmusicplayer.databasePath.value, "yamp.db"))
	except Exception as e:
		LOG('YampScreen: clearDatabase: delete Database: EXCEPT: %s' % (str(e)), 'err')
	try:
		con, result = createDatabase()  # create new DB
		if con:
			con.close()
	except Exception as e:
		LOG('YampScreen: clearDatabase: build new Database: EXCEPT: %s' % (str(e)), 'err')


def createDatabase():
	dbPath = join(config.plugins.yampmusicplayer.databasePath.value, "yamp.db")
	try:
		con = connect(dbPath)
		try:
			LOG('createDatabase: dbPath: %s con: %s ' % (dbPath, con), 'all')
		except Exception:
			LOG('createDatabase: dbPath: con : EXCEPT', 'err')  # Test
		if not access(dbPath, W_OK):
			LOG('createDatabase: dbPath: no write access %s' % (dbPath), 'err')
			con.close()
			return None, 2
	except Exception as e:
		LOG('createDatabase: cannot open database dbPath: %s : %s' % (dbPath, str(e)), 'err')
		return None, 1
	cur = con.cursor()  # !!!
	cur.execute('CREATE TABLE IF NOT EXISTS Playlists (playlist_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, playlist_filename TEXT NOT NULL UNIQUE, playlist_title TEXT);')
	cur.execute('CREATE TABLE IF NOT EXISTS Titles (title_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL UNIQUE, title TEXT, artist_id INTEGER, album_id INTEGER, genre_id INTEGER, date_id INTEGER, date TEXT, length TEXT, tracknr INTEGER, sref TEXT, albumartist_id INTEGER DEFAULT 0);')
	cur.execute('CREATE TABLE IF NOT EXISTS Artists (artist_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, artist TEXT NOT NULL UNIQUE, mbid TEXT, picsLoadedDate TEXT DEFAULT "2000-01-01", artistShort TEXT);')
	cur.execute('CREATE TABLE IF NOT EXISTS Albums (album_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, album TEXT NOT NULL );')
	cur.execute('CREATE TABLE IF NOT EXISTS Genres (genre_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, genre TEXT NOT NULL UNIQUE);')
	cur.execute('CREATE TABLE IF NOT EXISTS Dates (date_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL UNIQUE);')
	cur.close()
	return con, 0


def dbUpgradeV33():
	if not checkIfDbexists():
		createDatabase()
		return 0
	if checkDatabaseHasData() == 0:
		clearDatabase()  # empty  -> delete and create new
		return 0

	con, result = ConnectDatabase()
	if con:
		try:
			con.row_factory = Row
		except Exception:
			LOG('dbUpgradeV33: row_factory: EXCEPT', 'err')
		cursor = con.cursor()
		try:
			cursor.execute("SELECT * FROM Artists")
		except Exception:
			LOG('dbUpgradeV33: SELECT: EXCEPT', 'err')
		rows = cursor.fetchone()
		try:
			a = rows['artist_id']
		except Exception:
			LOG('dbUpgradeV33: a=rows[artist_id]: EXCEPT: most likely empty database', 'err')
			try:
				cursor.close()
				con.close()
			except Exception as e:
				LOG('dbUpgradeV33: close1: EXCEPT: ' + str(e), 'err')
			return 1
		try:
			b = rows['artist']
		except Exception:
			LOG('dbUpgradeV33: b=rows[artist]: EXCEPT: most likely empty database', 'err')
			return 2
		try:
			c = rows['mbid']
			LOG('dbUpgradeV33: c=rows[mbid] exists: already upgraded to V33', 'all')
			return 0
		except Exception:
			LOG('dbUpgradeV33: c=rows[mbid]: EXCEPT: must be upgraded to V33', 'all')
		upgradeerror = 0
		try:
			cursor.execute("ALTER TABLE Artists ADD COLUMN 'mbid' TEXT")
		except Exception as e:
			LOG('dbUpgradeV33: ALTER TABLE: mbid: EXCEPT: ' + str(e), 'err')
			upgradeerror = 3
		try:
			con.commit()
		except Exception as e:
			LOG('dbUpgradeV33: commit: EXCEPT: ' + str(e), 'err')
			upgradeerror = 5
		try:
			cursor.close()
			con.close()
		except Exception as e:
			LOG('dbUpgradeV33: close: EXCEPT: ' + str(e), 'err')
		return upgradeerror


def dbUpgradeV331():
	if not checkIfDbexists():
		return 0
	if checkDatabaseHasData() == 0:
		return 999  # empty database
	con, result = ConnectDatabase()
	upgradeInfo = 0
	if con:
		cursor = None
		try:
			con.row_factory = Row
		except Exception:
			LOG('dbUpgradeV331: row_factory: EXCEPT', 'err')
		try:
			cursor = con.cursor()
		except Exception:
			LOG('dbUpgradeV331: cursor: EXCEPT', 'err')
		if cursor:
			try:
				cursor.execute("SELECT * FROM Artists")
			except Exception:
				LOG('dbUpgradeV331: SELECT: EXCEPT', 'err')
			rows = cursor.fetchone()
			try:
				a = rows['artist_id']
			except Exception:
				LOG('dbUpgradeV331: a=rows[artist_id]: EXCEPT: most likely empty database', 'err')
				upgradeInfo = -1
			try:
				b = rows['artist']
			except Exception:
				LOG('dbUpgradeV331: b=rows[artist]: EXCEPT: most likely empty database', 'err')
				upgradeInfo -= 1
			try:
				c = rows['artistShort']
				LOG('dbUpgradeV331: c=rows[artistShort] exists: already upgraded to V331', 'all')
				return 0
			except Exception:
				LOG('dbUpgradeV331: c=rows[artistShort]: Database will be upgraded to V331', 'all')
			try:
				# remove picsloaded, add picsLoadedDate, artistShort for Artists
				cursor.execute("ALTER TABLE Artists RENAME TO ArtistsOld")
				cursor.execute("CREATE TABLE Artists (artist_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, artist TEXT NOT NULL UNIQUE, mbid TEXT, picsLoadedDate TEXT DEFAULT '2000-01-01', artistShort TEXT)")
				cursor.execute("INSERT INTO Artists (artist_id, artist, mbid) SELECT artist_id, artist, mbid FROM ArtistsOld")
				cursor.execute("DROP TABLE ArtistsOld")
			except Exception as e:
				upgradeInfo -= 1
				LOG('dbUpgradeV331: remove picsloaded, add -Date + artistShort : EXCEPT: ' + str(e), 'err')
			try:
				makeArtistsShort(cursor)
			except Exception as e:
				upgradeInfo -= 1
				LOG('dbUpgradeV331: makeArtistsShort: EXCEPT: ' + str(e), 'err')
			try:
				# remove UNIQUE for album
				cursor.execute("ALTER TABLE Albums RENAME TO AlbumsOld")
				cursor.execute("CREATE TABLE Albums (album_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, album TEXT NOT NULL)")
				cursor.execute("INSERT INTO Albums (album_id, album) SELECT album_id, album FROM AlbumsOld")
				cursor.execute("DROP TABLE AlbumsOld")
			except Exception as e:
				upgradeInfo -= 1
				LOG('dbUpgradeV331: remove UNIQUE from album: EXCEPT: ' + str(e), 'err')
			try:
				con.commit()
			except Exception as e:
				LOG('dbUpgradeV331: commit: EXCEPT: ' + str(e), 'err')
				upgradeInfo -= 1
			try:
				if upgradeInfo == 0:
					newTitles = updateSpecialAlbums(con, cursor)
					upgradeInfo = 1000 + newTitles
			except Exception as e:
				LOG('Yamp.py: dbUpgradeV331: updateSpecialAlbums: EXCEPT: ' + str(e), 'err')
			try:
				cursor.close()
				con.close()
			except Exception as e:
				LOG('dbUpgradeV331: close: EXCEPT: ' + str(e), 'err')
			if upgradeInfo == 0:
				upgradeInfo = 1  # upgrade succesful
			return upgradeInfo
	return 0


def dbUpgradeV332():
	if not checkIfDbexists():
		return 0
	if checkDatabaseHasData() == 0:
		return 999  # empty database
	con, result = ConnectDatabase()
	upgradeInfo = 0
	if con:
		try:
			con.row_factory = Row
		except Exception:
			LOG('dbUpgradeV332: row_factory: EXCEPT', 'err')
		cursor = con.cursor()
		try:
			cursor.execute("SELECT * FROM Titles")
		except Exception:
			LOG('dbUpgradeV332: SELECT: EXCEPT', 'err')
		rows = cursor.fetchone()
		try:
			a = rows['title_id']
		except Exception:
			LOG('dbUpgradeV332: a=rows[title_id]: EXCEPT: most likely empty database', 'err')
			upgradeInfo = -1
		try:
			b = rows['filename']
		except Exception:
			LOG('dbUpgradeV332: b=rows[filename]: EXCEPT: most likely empty database', 'err')
			upgradeInfo -= 1
		try:
			c = rows['albumartist_id']
			LOG('dbUpgradeV332: c=rows[albumartist_id] exists: already upgraded to V332', 'all')
			return 0
		except Exception as e:
			LOG('dbUpgradeV332: c=rows[albumartist_id]: Database will be upgraded to V332', 'all')
		try:
			cursor.execute("ALTER TABLE Titles ADD COLUMN 'albumartist_id' INTEGER DEFAULT 0")
		except Exception as e:
			LOG('dbUpgradeV332: ALTER TABLE: albumartist_id: EXCEPT: ' + str(e), 'err')
			upgradeInfo = -1
		try:
			if upgradeInfo == 0:
				updated = updateAlbumArtists(con, cursor)
		except Exception as e:
			LOG('Yamp.py: dbUpgradeV332: updateAlbumArtists: EXCEPT: ' + str(e), 'err')
		try:
			con.commit()
		except Exception as e:
			LOG('dbUpgradeV33: commit: EXCEPT: ' + str(e), 'err')
			upgradeInfo = -1
		try:
			cursor.close()
			con.close()
		except Exception as e:
			LOG('dbUpgradeV332: close: EXCEPT: ' + str(e), 'err')
		if upgradeInfo == 0:
			upgradeInfo = 1  # upgrade succesful
		return upgradeInfo
	return 0


def updateAlbumArtists(con, cursor):
	retVal = 0
	try:
		cursor.execute("SELECT title_id, artist_id, albumartist_id FROM Titles")
		rows = cursor.fetchall()
		if len(rows) == 0:
			return 0
		for title in rows:
			if title[2] == 0:
				try:
					cursor.execute("UPDATE Titles SET albumartist_id = %d WHERE title_id = %d" % (title[1], title[0]))
					retVal += 1
				except Exception as e:
					LOG('dbUpgradeV332: updateAlbumArtists: write albumartist: EXCEPT: ' + str(e), 'err')
		con.commit()
	except Exception as e:
		LOG('dbUpgradeV332: updateAlbumArtists: EXCEPT: ' + str(e), 'err')
	return retVal


def updateSpecialAlbums(con, cursor):
	try:
		# AlbumID 0, Artist 1, ArtistID 2, Album 3 , TitleID 4
		cursor.execute("SELECT Albums.album_id, Artists.artist, Artists.artist_id, Albums.album, Titles.title_id FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id INNER JOIN Albums ON Titles.album_id = Albums.album_id WHERE Albums.album LIKE 'GREATEST HITS' ORDER BY Artists.artist_id")
	except Exception as e:
		LOG('Yamp.py: updateSpecialAlbums: exec SQL: EXCEPT: ' + str(e), 'err')
	rows = []
	albIdArtId, actIDs = [], []
	try:
		rows = cursor.fetchall()
		if len(rows) == 0:
			return 0  # no 'Greatest HitS'
		albIdArtId = []
		actIDs = []
	except Exception as e:
		LOG('Yamp.py: updateSpecialAlbums: setValues: EXCEPT: ' + str(e), 'err')
	try:
		newAlbumsTitles = []
		newAlbumID = oldAlbumID = 0
		for row in rows:
			found = False
			actIDs = [row[0], row[2]]
			oldAlbumID = row[0]
			# find existing AlbumID AND ArtistID in list
			for exist in albIdArtId:
				if exist[0] == row[0] and exist[1] == row[2]:
					found = True
					newalbTit = [newAlbumID, row[4]]
					newAlbumsTitles.append(newalbTit)
					break
			if not found:  # new album or new artist
				# make new album
				cursor.execute('INSERT INTO Albums (album) VALUES("%s");' % ("Greatest Hits"))
				newAlbumID = cursor.lastrowid
				albIdArtId.append(actIDs)
				newalbTit = [newAlbumID, row[4]]
				newAlbumsTitles.append(newalbTit)
		retVal = len(newAlbumsTitles)
		for albumTitle in newAlbumsTitles:
			cursor.execute("UPDATE Titles SET album_id = %d WHERE title_id = %d" % (albumTitle[0], albumTitle[1]))
		# delete old common album Greatest Hits
		if oldAlbumID > 0:
			cursor.execute('DELETE FROM Albums WHERE album_id = %d;' % oldAlbumID)
		con.commit()
	except Exception as e:
		LOG('Yamp.py: updateSpecialAlbums: execute: EXCEPT: ' + str(e), 'err')
		retVal = -1
	return retVal


def makeArtistsShort(cursor):  # if DB is upgraded...
	row = ["", ""]
	try:
		cursor.execute("SELECT * FROM Artists")
		rows = cursor.fetchall()
		for row in rows:
			artistShort = sub('(?i)( +feat)(.*)', '', row[1]).strip()  # remove Featuring
			cursor.execute("UPDATE Artists SET artistShort = \"%s\" WHERE artist_id = %d" % (artistShort, row[0]))
	except Exception as e:
		LOG('Yamp.py: dbUpgradeV331: makeArtistsShort: EXCEPT: ' + row[1] + ': ' + str(e), 'err')


def dbInsert(con, cursor, ref, table="titles", update=False):  # Return: 0: skipped, 1: added 2: actualized
	res = 0
	f = ref.getPath()
	sref = str(ServiceReference(ref))
	if table == "titles":
		try:
			cursor.execute('SELECT title_id FROM Titles WHERE filename = "%s";' % f)
		except Exception as e:
			LOG('YampDbActions: dbInsert: SELECT title_id: EXCEPT: ' + str(e), 'err')
		rowFile = cursor.fetchone()
		title, album, genre, artist, albumartist, date, length, tracknr = "", "", "", "", "", "", "", ""
		try:
			title, album, genre, artist, albumartist, date, length, tracknr, strBitrate = readID3Infos(f)
		except Exception as e:
			LOG('YampDbActions: dbInsert: readID3Infos: EXCEPT: ' + str(e), 'err')
		artistShort = sub('(?i)( +feat)(.*)', '', artist).strip()  #  remove Featuring
		if config.plugins.yampmusicplayer.capitalizeTitleAndArtist.value:
			title = titlecase(title)
			artist = titlecase(artist).replace('"', '""')
			albumartist = titlecase(albumartist).replace('"', '""')
		try:
			LOG('YampDbActions: dbInsert: title: %s album: %s genre: %s artist: %s albumartist: %s date: %s length: %s tracknr: %d' % (title, album, genre, artist, albumartist, date, length, tracknr), 'all')
		except Exception as e:
			LOG('YampDbActions: dbInsert: Log Id3Infos: EXCEPT: ' + str(e), 'err')
		# get New Values of title, add or get artist, album, genre, date
		# 1a. Artist
#		artistShort = sub('(?i)( +feat)(.*)', '', artist).strip()  # remove Featuring
		cursor.execute('SELECT artist_id FROM Artists WHERE artist = "%s";' % (artist))
		row = cursor.fetchone()
		if row is None:
			cursor.execute('INSERT INTO Artists (artist, artistShort) VALUES("%s","%s");' % (artist, artistShort))
			artistID = cursor.lastrowid
		else:
			artistID = row[0]
		# 1b. Albumartist
		albumartistShort = sub('(?i)( +feat)(.*)', '', albumartist).strip()  #  remove Featuring
		cursor.execute('SELECT artist_id FROM Artists WHERE artist = "%s";' % (albumartist))
		row = cursor.fetchone()
		if row is None:
			cursor.execute('INSERT INTO Artists (artist, artistShort) VALUES("%s","%s");' % (albumartist, albumartistShort))
			albumartistID = cursor.lastrowid
		else:
			albumartistID = row[0]
		# 2. Album
		# albumSpecial: check artist also to get multiple entries for example "Greatest Hits"
		albumSpecial = False
		for specAlbum in ['greatest hits']:  # Albums, which need special treatment (incl. artist)
			albumSpecial = album.lower().startswith(specAlbum)
		album = album.replace('"', '""')
		if albumSpecial:
			params = (album, artist)
			cursor.execute('SELECT Albums.album_id, Artists.artist, Albums.album FROM Titles INNER JOIN Artists ON Titles.artist_id = Artists.artist_id INNER JOIN Albums ON Titles.album_id = Albums.album_id WHERE Albums.album LIKE ? AND Artists.artist LIKE ?', params)
		else:
			cursor.execute('SELECT album_id FROM Albums WHERE album = "%s";' % (album))
		row = cursor.fetchone()
		if row is None:
			cursor.execute('INSERT INTO Albums (album) VALUES("%s");' % (album))
			albumID = cursor.lastrowid
		else:
			albumID = row[0]
		# 3. Genre
		genre = genre.replace('"', '""')
		cursor.execute('SELECT genre_id FROM Genres WHERE genre = "%s";' % (genre))
		row = cursor.fetchone()
		if row is None:
			cursor.execute('INSERT INTO Genres (genre) VALUES("%s");' % (genre))
			genreID = cursor.lastrowid
		else:
			genreID = row[0]
		# 4. date (original) and year
		try:
			year = str(int(date.replace('"', '""')[:4]))
		except Exception:
			year = 'n/a'
		cursor.execute('SELECT date_id FROM Dates WHERE date = "%s";' % (year))
		row = cursor.fetchone()
		if row is None:
			cursor.execute('INSERT INTO Dates (date) VALUES("%s");' % (year))
			dateID = cursor.lastrowid
		else:
			dateID = row[0]
		if rowFile is None:  #new title: insert
			# 5. Titles
			try:
				cursor.execute("INSERT INTO Titles (filename,title,artist_id,album_id,genre_id,date_id, length,date,tracknr,sref,albumartist_id ) VALUES(?,?,?,?,?,?,?,?,?,?,?);", (f, title, artistID, albumID, genreID, dateID, length, date, tracknr, sref, albumartistID))
				res = 1
			except Exception as e:
				LOG('YampDbActions: dbInsert: 5.Titles: EXCEPT: ' + str(e), 'err')
		else:  # existing title: update, if necessary
			isActualized = False
			cursor.execute('SELECT  title_id, title, artist_id, album_id, genre_id, date_id, length, date, tracknr, albumartist_id FROM Titles WHERE filename = "%s";' % f)
			row = cursor.fetchone()
			try:
				if row[1] != title:  # new Title
					LOG('YampDbActions: dbInsert: actualize title:  new: *%s* old: %s ' % (title, row[0]), 'all')
					cursor.execute('UPDATE Titles SET title = "%s" WHERE title_id = %d' % (title, row[0]))
					isActualized = True
				if row[2] != artistID:  # new Artist
					LOG('YampDbActions: dbInsert: actualize artistID for title %s:  new: %d old: %d ' % (title, artistID, row[2]), 'all')
					cursor.execute("UPDATE Titles SET artist_id = %d WHERE title_id = %d" % (artistID, row[0]))
					isActualized = True
				if row[3] != albumID:  # new Album
					LOG('YampDbActions: dbInsert: actualize albumID for title %s:  new: %d old: %d ' % (title, albumID, row[3]), 'all')
					cursor.execute("UPDATE Titles SET album_id = %d WHERE title_id = %d" % (albumID, row[0]))
					isActualized = True
				if row[4] != genreID:  # new Genre
					LOG('YampDbActions: dbInsert: actualize genreID for title %s:  new: %d old: %d ' % (title, genreID, row[4]), 'all')
					cursor.execute("UPDATE Titles SET genre_id = %d WHERE title_id = %d" % (genreID, row[0]))
					isActualized = True
				if row[5] != dateID:  # new DateID (Year)
					LOG('YampDbActions: dbInsert: actualize dateID for title %s:  new: %d old: %d ' % (title, dateID, row[5]), 'all')
					cursor.execute("UPDATE Titles SET date_id = %d WHERE title_id = %d" % (dateID, row[0]))
					isActualized = True
				if row[6] != length:  # new Length
					LOG('YampDbActions: dbInsert: actualize length for title %s:  new: %s old: %s ' % (title, length, row[6]), 'all')
					cursor.execute("UPDATE Titles SET length = '%s' WHERE title_id = %d" % (length, row[0]))
					isActualized = True
				if row[7] != date:  # new Date (original)
					LOG('YampDbActions: dbInsert: actualize date for title %s:  new: %s old: %s ' % (title, date, row[7]), 'all')
					cursor.execute("UPDATE Titles SET date = '%s' WHERE title_id = %d" % (date, row[0]))
					isActualized = True
				if row[8] != tracknr:  # new Tracknr
					LOG('YampDbActions: dbInsert: actualize tracknr for title %s:  new: %d old: %d ' % (title, tracknr, row[8]), 'all')
					cursor.execute("UPDATE Titles SET tracknr = '%d' WHERE title_id = %d" % (tracknr, row[0]))
					isActualized = True
				if row[9] != albumartistID:  # new AlbumArtist
					LOG('YampDbActions: dbInsert: actualize albumartist for title %s:  new: %d old: %d ' % (title, albumartistID, row[9]), 'all')
					cursor.execute("UPDATE Titles SET albumartist_id = '%d' WHERE title_id = %d" % (albumartistID, row[0]))
					isActualized = True
			except Exception as e:
				LOG('YampDbActions: dbInsert: Actualize: EXCEPT: ' + str(title) + ': ' + str(e), 'err')
			if isActualized:
				res = 2
	elif table == "playlists":
		cursor.execute('SELECT playlist_id FROM Playlists WHERE playlist_filename = "%s";' % f)
		row = cursor.fetchone()
		if row is None:
			text = ref.getName() or basename(f)
			try:
				try:
					cursor.execute("INSERT INTO Playlists (playlist_filename,playlist_title) VALUES(?,?);", (f, text))
				except Exception as e:
					LOG('YampScreen: dbInsert: playlist: execute sql: EXCEPT: ' + str(e), 'err')
				res = 1
			except IntegrityError:
				pass
	return res


#######################################################################
#	titlecase()
#
#	Original Perl version by: John Gruber http://daringfireball.net/ 10 May 2008
#	Python version by Stuart Colville http://muffinresearch.co.uk
#	License: http://www.opensource.org/licenses/mit-license.php
# Adapted by AlfredENeumann, Jan. 2016, Jan 2023, Feb. 2024
#
#######################################################################

SMALL = r'a|an|and|as|at|but|by|en|for|if|in|of|on|or|the|to|v\.?|via|vs|der|die|das|dem|des|ein|eine|ist|mit|und|von\.?'
PUNCT = r"""!"#$%&'‘()*+,\-./:;?@[\\\]_`{|}~"""
SMALL_WORDS = compile(r'^(%s)$' % SMALL, I)
INLINE_PERIOD = compile(r'[a-z][.][a-z]', I)
UC_ELSEWHERE = compile(r'[%s]*?[a-zA-Z]+[A-Z]+?' % PUNCT)
CAPFIRST = compile(r"^[%s]*?([A-Za-z])" % PUNCT)
SMALL_FIRST = compile(r'^([%s]*)(%s)\b' % (PUNCT, SMALL), I)
SMALL_LAST = compile(r'\b(%s)[%s]?$' % (SMALL, PUNCT), I)
SUBPHRASE = compile(r'([:.;?!][ ])(%s)' % SMALL)
APOS_SECOND = compile(r"^[dol]{1}['‘]{1}[a-z]+$", I)
ALL_CAPS = compile(r'^[A-Z\s\d%s]+$' % PUNCT)
UC_INITIALS = compile(r"^(?:[A-Z]{1}\.{1}|[A-Z]{1}\.{1}[A-Z]{1})+$")
MAC_MC = compile(r"^([Mm]c)(\w.+)")


def set_small_word_list(small=SMALL):
	global SMALL_WORDS
	global SMALL_FIRST
	global SMALL_LAST
	global SUBPHRASE
	SMALL_WORDS = compile(r'^(%s)$' % small, I)
	SMALL_FIRST = compile(r'^([%s]*)(%s)\b' % (PUNCT, small), I)
	SMALL_LAST = compile(r'\b(%s)[%s]?$' % (small, PUNCT), I)
	SUBPHRASE = compile(r'([:.;?!][ ])(%s)' % small)


def titlecase(text, callback=None):
	"""
	Titlecases input text
	This filter changes all words to Title Caps, and attempts to be clever
	about *un*capitalizing SMALL words like a/an/the in the input.
	The list of "SMALL words" which are not capped comes from
	the New York Times Manual of Style, plus 'vs' and 'v'.

	AlfredENeumann: in <yampDir> No Titlecase, txt excludes may be defined
	"""
	global yampTitlecaseNochange
	for excl in yampTitlecaseNochange:
		if text.startswith(excl):
			return (text)

	lines = split('[\r\n]+', text)
	processed = []
	for line in lines:
		all_caps = ALL_CAPS.match(line)
		words = split('[\t ]', line)
		tc_line = []
		for word in words:
			if callback:
				new_word = callback(word, all_caps=all_caps)
				if new_word:
					tc_line.append(new_word)
					continue
			if all_caps and UC_INITIALS.match(word):
					tc_line.append(word)
					continue
			if APOS_SECOND.match(word):
				if len(word[0]) == 1 and word[0] not in 'aeiouAEIOU':
					word = word[0].lower() + word[1] + word[2].upper() + word[3:]
				else:
					word = word[0].upper() + word[1] + word[2].upper() + word[3:]
				tc_line.append(word)
				continue
			if INLINE_PERIOD.search(word) or (not all_caps and UC_ELSEWHERE.match(word)):
				tc_line.append(word)
				continue
			if SMALL_WORDS.match(word):
				tc_line.append(word.lower())
				continue
			match = MAC_MC.match(word)
			if match:
#				if word.lower() != 'machine' and word.lower() != 'machine,' and word.lower() != 'macy':
				tc_line.append("%s%s" % (match.group(1).capitalize(), match.group(2).capitalize()))
				continue
			if "/" in word and "//" not in word:
				slashed = map(lambda t: titlecase(t, callback), word.split('/'))
				tc_line.append("/".join(slashed))
				continue
			if '-' in word:
				hyphenated = map(lambda t: titlecase(t, callback), word.split('-'))
				tc_line.append("-".join(hyphenated))
				continue
			if all_caps:
				word = word.lower()
			# Just a normal word that needs to be capitalized
			tc_line.append(CAPFIRST.sub(lambda m: m.group(0).upper(), word))
		result = " ".join(tc_line)
		result = SMALL_FIRST.sub(lambda m: '%s%s' % (m.group(1), m.group(2).capitalize()), result)
		result = SMALL_LAST.sub(lambda m: m.group(0).capitalize(), result)
		result = SUBPHRASE.sub(lambda m: '%s%s' % (m.group(1), m.group(2).capitalize()), result)
		processed.append(result)
	return "\n".join(processed)
