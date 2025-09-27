#######################################################################
#
#    YAMP - Yet Another Music Player - Video Special
#    Version 3.3.1.2 2024-02-14
#    Coded by AlfredENeumann (c)2016-2024
#    Last change: 2025-09-26 by Mr.Servo @OpenATV
#    Support: www.vuplus-support.org, board.newnigma2.to
#
#    This program is free software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    Thanks to the authors of Merlin Music Player and OpenPli Media
#    Player for ideas and code snippets
#
#######################################################################

from os.path import join, exists
from enigma import eTimer
from Components.ActionMap import ActionMap
from Components.config import config
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.Sources.Boolean import Boolean
from Screens.Screen import Screen
from .YampGlobals import yampDir, STATE_STOP
from .YampPixmaps import YampCoverArtPixmap
from .YampBoxDisplay import YampLCDRunningScreenV33, YampLCDScreenV33
from .myLogger import LOG
from . import _


def checkAttributes(element, NameText, searchText):
	check = False
	if element.skinAttributes is not None:
		for (attrib, value) in element.skinAttributes:
			try:
				if attrib == NameText and value == searchText:
					check = True
			except Exception:
				LOG('YampScreen: checkAttributes: if ATTR:EXCEPT', 'err')
	return check


class YampVideoTitleV33(Screen):
	def __init__(self, session, parent, autoStartTime=0):
		Screen.__init__(self, session, parent=parent)
		xmlfile = join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampVideoTitle.xml")
		if not exists(xmlfile):
			self.skinOpenError = True
			self.close('')
			return
		with open(xmlfile, 'r') as f:
			self.skin = f.read()
		self.skinOpenError = False
		self.parent = parent
		self.autoStartTime = autoStartTime
		self.textLongActive = False
		self.jumpFwLongActive = False
		self.jumpBwLongActive = False
		self.elementClock = self.elementDate = None
		LOG('YampVideoTitle: START', 'all')
		self.updateTimer = eTimer()
		self.updateTimer.callback.append(self.updateInfoCyclic)
		self.startupTimer = eTimer()
		self.startupTimer.callback.append(self.startupTimerTimeout)
		self["songtitle"] = Label("")
		self["artist"] = Label("")
		self["album"] = Label("")
		self["year"] = Label("")
		self["genre"] = Label("")
		self["line1"] = Label(".")
		self["line2"] = Label(".")
		self["coverArt"] = YampCoverArtPixmap()
		self["nextsong"] = Label(_("Next Song"))
		self["nextsongtitle"] = Label("")
		self["bitrate"] = Label("")
		self["songInfoBg"] = Boolean(True)
		self["clockBackground"] = Pixmap()
		self["dateBackground"] = Pixmap()
		self["lyricsLine"] = Label("")
		self["lyricsLineBackground"] = Pixmap()
		self["lyricsLineBig"] = Label("")
		self["lyricsLineBackgroundBig"] = Pixmap()
		self["karaoke"] = Boolean(False)
		self["karaokeBig"] = Boolean(False)
		self["actions"] = ActionMap(["YampActions", "YampOtherActions"],
		{
			"exit": self.keyClose,
			"red": self.keyClose,
			"green": self.keyCloseOk,
			"ok": self.keyCloseOk,
			"up": self.keyCloseUp,
			"down": self.keyCloseDown,
			"moveTop": self.keyCloseMoveTop,
			"moveEnd": self.keyCloseMoveEnd,
			"menu": self.keyCloseMenu,
			"info": self.keyCloseInfo,
			"prevTitle": self.keyPrevious,
			"nextTitle": self.keyNext,
			"Audio": self.keyAudio,
			"Text": self.keyText,
			"TextLong": self.keyTextLong,
			"play": self.keyPlay,
			"pause": self.keyPause,
			"stop": self.keyStop,
			"keyPercentJumpFw": self.keyPercentJumpFwActions,
			"keyPercentJumpBw": self.keyPercentJumpBwActions,
			"keyPercentJumpFwLong": self.keyPercentJumpFwLActions,
			"keyPercentJumpBwLong": self.keyPercentJumpBwLActions
		}, -2)
		self["seekactions"] = ActionMap(["YampActions"],
		{
			"key1": self.key1,
			"key3": self.key3,
			"key4": self.key4,
			"key6": self.key6,
			"key7": self.key7,
			"key9": self.key9
		}, -2)
		self.LcdText = ''
		try:
			LOG('YampVideoTitle: init: autoStartTime: %d' % (autoStartTime), 'spe')
			LOG('YampVideoTitle: init: autoStartTime: %d' % (self.autoStartTime), 'spe')
		except Exception:
			LOG('YampVideoTitle: init: parameters: EXCEPT', 'err')
		LOG('YampVideoTitle: init: IsVideo: %d' % (self.parent.currentIsVideo), 'spe')
		self.actTitle = self.actArtist = self.actAlbum = ''
		self.onLayoutFinish.append(self.layoutFinished)
		self.onClose.append(self.cleanup)
		self.parent.videoScreenActive = True

	def layoutFinished(self):
		LOG('YampVideoTitle: layoutFinished: autoStartTime: %d  isVideo: %d' % (self.autoStartTime, self.parent.currentIsVideo), 'spe')
		bgMode = config.plugins.yampmusicplayer.karaokeBg.value
		self.findClockElement()
		self.showHideClock("Video")
		self["songInfoBg"].setBoolean(config.plugins.yampmusicplayer.showInfoBarBg.value)
		self["lyricsLine"].hide()
		self["lyricsLineBackground"].hide()
		self["lyricsLineBig"].hide()
		self["lyricsLineBackgroundBig"].hide()
		self.updateSongInfo()
		self.updateTimer.start(300, False)
		if self.autoStartTime > 0:
			self.startupTimer.start(self.autoStartTime * 1000, True)
		self.displayKaraoke()

	def displayKaraoke(self):
		try:
			lyrics = self.parent.oldLyricsText.strip()
			if self.parent.lyricsLineShow or self.parent.lyricsLineShowBig:
				bgMode = config.plugins.yampmusicplayer.karaokeBg.value
				showBgSmall = (bgMode == 'small' or bgMode == 'both') and len(lyrics) > 0
				showBgBig = (bgMode == 'big' or bgMode == 'both') and len(lyrics) > 0
				if self.parent.playerState < STATE_STOP:
					if self.parent.lyricsLineShow:
						self["lyricsLine"].setText(lyrics)
						self["lyricsLine"].show()
						self["lyricsLineBig"].hide()
						self["lyricsLineBackgroundBig"].hide()
						if showBgSmall:
							self["lyricsLineBackground"].show()
						else:
							self["lyricsLineBackground"].hide()
					else:
						self["lyricsLineBig"].setText(lyrics)
						self["lyricsLineBig"].show()
						self["lyricsLine"].hide()
						self["lyricsLineBackground"].hide()
						if showBgBig:
							self["lyricsLineBackgroundBig"].show()
						else:
							self["lyricsLineBackgroundBig"].hide()
			self["karaoke"].setBoolean(self.parent.lyricsLineShow)
			self["karaokeBig"].setBoolean(self.parent.lyricsLineShowBig)
		except Exception:
			LOG('YampVideoTitleV33: displayKaraoke: EXCEPT', 'err')

	def startupTimerTimeout(self):
		LOG('YampVideoTitle: startupTimerTimeout: close: IsVideo: %d' % (self.parent.currentIsVideo), 'spe')
		if not self.parent.currentIsVideo:
			self.updateTimer.stop()
		self.close('startupTimerTimeout')

	def updateSongInfo(self):
		if not self.parent.currentIsVideo:
			self.updateTimer.stop()
			self.close('updateSongInfo')
			return
		try:
			if self.parent.lyricsLineShow or self.parent.lyricsLineShowBig:
				self["lyricsLine"].setText(self.parent.displayLyricsText)
		except Exception:
			LOG('YampVideoTitle: updateSongInfo: lyricsLine SetText: EXCEPT', 'err')
		try:
			coverArtFile, PixNumCover = self.parent.getCoverArtFile()
			if PixNumCover > 0:
				self["coverArt"].showCoverArt(coverArtFile)
		except Exception:
			LOG('YampVideoTitle: updateSongInfo: cover: EXCEPT', 'err')
		replaceText = self.parent.infoBarNaReplace
		newTitle = self.parent.currTitle.replace('n/a', replaceText)
		newArtist = self.parent.currArtist.replace('n/a', replaceText)
		newAlbum = self.parent.currAlbum.replace('n/a', replaceText)
		if self.actTitle != newTitle or self.actArtist != newArtist or self.actAlbum != newAlbum:
			if self.autoStartTime > 0:
				if self.startupTimer.isActive():
					self.startupTimer.stop()
				self.startupTimer.start(self.autoStartTime * 1000, True)
			self.actTitle = newTitle
			self.actArtist = newArtist
			self.actAlbum = newAlbum
			self["songtitle"].setText(newTitle)
			self["artist"].setText(newArtist)
			self["album"].setText(newAlbum)
			self["year"].setText(self.parent.currYear.replace('n/a', replaceText))
			self["genre"].setText(self.parent.currGenre.replace('n/a', replaceText))
			self["nextsongtitle"].setText(self.parent.nextSongDisplay.replace('n/a', replaceText))
			self["bitrate"].setText(self.parent.currBitRate.replace('n/a', replaceText))
# self["line1"] = Label (".")
# self["line2"] = Label (".")

	def updateInfoCyclic(self):
		self.displayKaraoke()
		self.updateSongInfo()
		self.setLcdText()

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

	def keyAudio(self):
		self.close('keyAudio')

	def keyText(self):
		if self.textLongActive:
			self.textLongActive = False
		else:
			try:
				self.parent.lyricsLineShow = not self.parent.lyricsLineShow  # !!!noch Restzeit autostart
				self.parent.lyricsLineShowBig = False
				self.displayKaraoke()
			except Exception:
				LOG('YampVideoTitle: keyText: EXCEPT', 'err')

	def keyTextLong(self):
		self.textLongActive = True
		self.parent.lyricsLineShowBig = not self.parent.lyricsLineShowBig
		self.parent.lyricsLineShow = False
		self.displayKaraoke()

	def keyPercentJumpFwActions(self):
		if self.jumpFwLongActive:
			self.jumpFwLongActive = False
		else:
			self.parent.seekOwn(21)

	def keyPercentJumpBwActions(self):
		if self.jumpBwLongActive:
			self.jumpBwLongActive = False
		else:
			self.parent.seekOwn(22)

	def keyPercentJumpFwLActions(self):
		self.jumpFwLongActive = True
		self.parent.seekOwn(23)

	def keyPercentJumpBwLActions(self):
		self.jumpBwLongActive = True
		self.parent.seekOwn(24)

	def keyClose(self):
		self.close('keyClose')

	def keyCloseOk(self):
		self.close('keyOk')

	def keyCloseUp(self):
		self.close('keyUp')

	def keyCloseDown(self):
		self.close('keyDown')

	def keyCloseMoveTop(self):
		self.close('keyMoveTop')

	def keyCloseMoveEnd(self):
		self.close('keyMoveEnd')

	def keyCloseMenu(self):
		self.close('keyMenu')

	def keyCloseInfo(self):
		self.close('keyInfo')

	def keyPlay(self):
		try:
			self.parent.play()
		except Exception as e:
			LOG('YampVideoSpecial: YampVideoTitle: keyPlay: EXCEPT: %s' % (str(e)), 'err')

	def keyPause(self):
		try:
			self.parent.pause()
		except Exception as e:
			LOG('YampVideoSpecial: YampVideoTitle: keyPause: EXCEPT: %s' % (str(e)), 'err')

	def keyStop(self):
		try:
			self.parent.stopEntry()
		except Exception:
			LOG('YampVideoTitle: keyStop: EXCEPT', 'err')
		self.close('keyStop')

	def cleanup(self):
		LOG('YampVideoTitle: cleanup', 'spe')
		self.showHideClock()
		self.updateTimer.stop()
		self.startupTimer.stop()
		del self.updateTimer
		del self.startupTimer
		self["lyricsLine"].hide()
		self["lyricsLineBackground"].hide()
		self["lyricsLineBig"].hide()
		self["lyricsLineBackgroundBig"].hide()
		self.parent.videoScreenActive = False

	def setLcdText(self):
		if config.plugins.yampmusicplayer.yampLcdMode.value == 'off':
			return
		if config.plugins.yampmusicplayer.yampLcdMode.value == 'rolling':
			self.updateLCDText(self.actTitle + ' - ' + self.actArtist + ' - ' + self.actAlbum, 1)
		else:
			self.updateLCDText(self.actTitle, 1)
			self.updateLCDText(self.actArtist, 2)
			self.updateLCDText(self.actAlbum, 3)

	def updateLCDText(self, text, line):
		if config.plugins.yampmusicplayer.yampLcdMode.value == 'rolling':
			try:
				self.LcdText = text
			except Exception:
				pass
		else:
			self.summaries.setCover()
			self.summaries.setText(text, line)

	def getLcdText(self):  # for LCD Running Text
		if self.skinOpenError is True:
			return ('')
		return (self.LcdText)

	def createSummary(self):
		lcdMode = config.plugins.yampmusicplayer.yampLcdMode.value
		if lcdMode == 'off':
			return
		return YampLCDRunningScreenV33 if lcdMode == 'rolling' else YampLCDScreenV33

	def findClockElement(self):
		LOG('YampVideoTitle: findClockElement: Start', 'all')
		try:
			for element in self.renderer:
				if "Converter.ClockToText." in str(vars(element)):
					if checkAttributes(element, "text", "clockHide"):
						LOG('YampVideoTitle: findClockElement: FOUND clockHide!!!', 'all')
						self.elementClock = element
					elif checkAttributes(element, "text", "dateHide"):
						LOG('YampVideoTitle: findClockElement: FOUND dateHide!!!', 'all')
						self.elementDate = element
		except Exception:
			LOG('YampVideoTitle: findClockElement: EXCEPT', 'err')

	def showHideClock(self, Modus="Standard"):  # "Video"
		LOG('VideoTitleScreen: showHideClock START: Modus %s ' % (Modus), 'all')
		try:
			configVid = config.plugins.yampmusicplayer.showClockVideo.value
			LOG('VideoTitleScreen: showHideClock: configVid: %s' % (configVid), 'all')
			if self.elementClock is not None:
				if Modus == "Standard":
					self.elementClock.instance.hide()
					self["clockBackground"].hide()
					LOG('VideoTitleScreen: showHideClock: Clock & BG Hide 1', 'all')
				elif Modus == "Video":
					if configVid == "no" or configVid == "date" or configVid == "datebg":
						self.elementClock.instance.hide()
						self["clockBackground"].hide()
						LOG('VideoTitleScreen: showHideClock: Clock & BG Hide 2', 'all')
					elif configVid == "clock" or configVid == "clockdate":
						self.elementClock.instance.show()
						self["clockBackground"].hide()
						LOG('VideoTitleScreen: showHideClock: Clock Show, BG Hide', 'all')
					elif configVid == "clockbg" or configVid == "clockdatebg":
						self.elementClock.instance.show()
						self["clockBackground"].show()
						LOG('YampVideoSpecial: VideoTitleScreen: showHideClock: Clock & BG Show', 'all')
			if self.elementDate is not None:
				if Modus == "Standard":
					self.elementDate.instance.hide()
					self["dateBackground"].hide()
					LOG('YampVideoSpecial: VideoTitleScreen: showHideClock: Date & BG Hide 1', 'all')
				elif Modus == "Video":
					if configVid == "no" or configVid == "clock" or configVid == "clockbg":
						self.elementDate.instance.hide()
						self["dateBackground"].hide()
						LOG('YampVideoSpecial: VideoTitleScreen: showHideClock: Date & BG Hide 2', 'all')
					elif configVid == "date" or configVid == "clockdate":
						self.elementDate.instance.show()
						self["dateBackground"].hide()
						LOG('YampVideoSpecial: VideoTitleScreen: showHideClock: Date Show, BG Hide', 'all')
					elif configVid == "datebg" or configVid == "clockdatebg":
						self.elementDate.instance.show()
						self["dateBackground"].show()
						LOG('\nYampVideoSpecial: VideoTitleScreen: showHideClock: Date & BG Show', 'all')
		except Exception:
			LOG('VideoTitleScreen: showHideClock: EXCEPT', 'err')

	def lockShow(self):
		pass

	def unlockShow(self):
		pass


class YampVideoLyricsV33(Screen):
	def __init__(self, session, parent):
		Screen.__init__(self, session, parent=parent)
		try:
			with open(join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampVideoLyrics.xml"), 'r') as f:
				self.skin = f.read()
				self.skinOpenError = False
		except Exception as e:
			LOG('YampVideoSpecial: YampVideoLyrics: open xml: EXCEPT: %s' % (str(e)), 'err')
			self.skinOpenError = True
			self.close()
			return
		self.parent = parent
		self.textLongActive = False
		self.updateTimer = eTimer()
		self.elementClock = self.elementDate = None
		self.updateTimer.callback.append(self.updateInfoCyclic)
		self["lyricsLine"] = Label("")
		self["lyricsLineBackground"] = Pixmap()
		self["lyricsLineBig"] = Label("")
		self["lyricsLineBackgroundBig"] = Pixmap()
		self["karaoke"] = Boolean(False)
		self["karaokeBig"] = Boolean(False)
		self["clockBackground"] = Pixmap()
		self["dateBackground"] = Pixmap()
		self["actions"] = ActionMap(["YampActions", "YampOtherActions"],
		{
			"exit": self.keyClose,
			"red": self.keyClose,
			"green": self.keyCloseOk,
			"ok": self.keyCloseOk,
			"up": self.keyCloseUp,
			"down": self.keyCloseDown,
			"moveTop": self.keyCloseMoveTop,
			"moveEnd": self.keyCloseMoveEnd,
			"menu": self.keyCloseMenu,
			"info": self.keyCloseInfo,
			"prevTitle": self.keyPrevious,
			"nextTitle": self.keyNext,
			"Audio": self.keyAudio,
			"Text": self.keyText,
			"TextLong": self.keyTextLong,
			"play": self.keyPlay,
			"pause": self.keyPause,
			"stop": self.keyStop,
		}, -2)
		self["seekactions"] = ActionMap(["YampActions"],
		{
			"key1": self.key1,
			"key3": self.key3,
			"key4": self.key4,
			"key6": self.key6,
			"key7": self.key7,
			"key9": self.key9,
		}, -2)
		self.LcdText = ''
		self.actTitle = self.actArtist = self.actAlbum = ''
		self.onLayoutFinish.append(self.layoutFinished)
		self.onClose.append(self.cleanup)
		self.parent.videoScreenActive = True

	def layoutFinished(self):
		self.findClockElement()
		self.showHideClock("Video")
		self["lyricsLine"].hide()
		self["lyricsLineBackground"].hide()
		self["lyricsLineBig"].hide()
		self["lyricsLineBackgroundBig"].hide()
		self.updateSongInfo()
		self.updateTimer.start(300, False)
		self.displayKaraoke()

	def displayKaraoke(self):
		try:
			lyrics = self.parent.oldLyricsText.strip()
			if self.parent.lyricsLineShow or self.parent.lyricsLineShowBig:
				bgMode = config.plugins.yampmusicplayer.karaokeBg.value
				showBgSmall = (bgMode == 'small' or bgMode == 'both') and len(lyrics) > 0
				showBgBig = (bgMode == 'big' or bgMode == 'both') and len(lyrics) > 0
				if self.parent.playerState < STATE_STOP:
					if self.parent.lyricsLineShow:
						self["lyricsLine"].setText(lyrics)
						self["lyricsLine"].show()
						self["lyricsLineBig"].hide()
						self["lyricsLineBackgroundBig"].hide()
						if showBgSmall:
							self["lyricsLineBackground"].show()
						else:
							self["lyricsLineBackground"].hide()
					else:
						self["lyricsLineBig"].setText(lyrics)
						self["lyricsLineBig"].show()
						self["lyricsLine"].hide()
						self["lyricsLineBackground"].hide()
						if showBgBig:
							self["lyricsLineBackgroundBig"].show()
						else:
							self["lyricsLineBackgroundBig"].hide()
			self["karaoke"].setBoolean(self.parent.lyricsLineShow)
			self["karaokeBig"].setBoolean(self.parent.lyricsLineShowBig)
		except Exception:
			LOG('YampVideoSpecial: YampVideoLyrics: displayKaraoke: EXCEPT', 'err')

	def updateSongInfo(self):
		if not self.parent.currentIsVideo:
			LOG('YampVideoSpecial: YampVideoLyrics: updateSongInfo: close: IsVideo: %d' % (self.parent.currentIsVideo), 'spe')
			self.updateTimer.stop()
			self.close('updateSongInfo')
			return
		try:
			if self.parent.lyricsLineShow or self.parent.lyricsLineShowBig:
				self["lyricsLine"].setText(self.parent.displayLyricsText)
		except Exception:
			LOG('YampVideoSpecial: YampVideoLyrics: updateSongInfo: lyricsLine SetText: EXCEPT', 'err')
		replaceText = self.parent.infoBarNaReplace
		newTitle = self.parent.currTitle.replace('n/a', replaceText)
		newArtist = self.parent.currArtist.replace('n/a', replaceText)
		newAlbum = self.parent.currAlbum.replace('n/a', replaceText)
		if self.actTitle != newTitle or self.actArtist != newArtist or self.actAlbum != newAlbum:
			self.actTitle = newTitle
			self.actArtist = newArtist
			self.actAlbum = newAlbum

	def updateInfoCyclic(self):
		self.displayKaraoke()
		self.updateSongInfo()
		self.setLcdText()

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

	def keyAudio(self):
		self.close('keyAudio')

	def keyText(self):
		if self.textLongActive:
			self.textLongActive = False
		else:
			try:
				self.parent.lyricsLineShow = not self.parent.lyricsLineShow  # !!!noch Restzeit autostart
				self.parent.lyricsLineShowBig = False
				self.displayKaraoke()
			except Exception:
				LOG('YampVideoSpecial: YampVideoLyrics: keyText: EXCEPT', 'err')

	def keyTextLong(self):
		self.textLongActive = True
		self.parent.lyricsLineShowBig = not self.parent.lyricsLineShowBig
		self.parent.lyricsLineShow = False
		self.displayKaraoke()

	def keyClose(self):
		self.close('keyClose')

	def keyCloseOk(self):
		self.close('keyOk')

	def keyCloseUp(self):
		self.close('keyUp')

	def keyCloseDown(self):
		self.close('keyDown')

	def keyCloseMoveTop(self):
		self.close('keyMoveTop')

	def keyCloseMoveEnd(self):
		self.close('keyMoveEnd')

	def keyCloseMenu(self):
		self.close('keyMenu')

	def keyCloseInfo(self):
		self.close('keyInfo')

	def keyPlay(self):
		try:
			self.parent.play()
		except Exception:
			LOG('YampVideoSpecial: YampVideoLyrics: keyPlay: EXCEPT', 'err')

	def keyPause(self):
		try:
			self.parent.pause()
		except Exception:
			LOG('YampVideoSpecial: YampVideoLyrics: keyPause: EXCEPT', 'err')

	def keyStop(self):
		try:
			self.parent.stopEntry()
		except Exception:
			LOG('YampVideoSpecial: YampVideoLyrics: keyStop: EXCEPT', 'err')
		self.close('keyStop')

	def cleanup(self):
		LOG('YampVideoSpecial: YampVideoLyrics: cleanup', 'spe')
		self.showHideClock()
		self.updateTimer.stop()
		del self.updateTimer
		self["lyricsLine"].hide()
		self["lyricsLineBackground"].hide()
		self["lyricsLineBig"].hide()
		self["lyricsLineBackgroundBig"].hide()
		self.parent.videoScreenActive = False

	def setLcdText(self):
		if config.plugins.yampmusicplayer.yampLcdMode.value == 'off':
			return
		if config.plugins.yampmusicplayer.yampLcdMode.value == 'rolling':
			self.updateLCDText(self.actTitle + ' - ' + self.actArtist + ' - ' + self.actAlbum, 1)
		else:
			self.updateLCDText(self.actTitle, 1)
			self.updateLCDText(self.actArtist, 2)
			self.updateLCDText(self.actAlbum, 3)

	def updateLCDText(self, text, line):
		if config.plugins.yampmusicplayer.yampLcdMode.value == 'rolling':
			try:
				self.LcdText = text
			except Exception:
				pass
		else:
			self.summaries.setCover()
			self.summaries.setText(text, line)

	def getLcdText(self):  # for LCD Running Text
		if self.skinOpenError is True:
			return ('')
		return (self.LcdText)

	def createSummary(self):
		lcdMode = config.plugins.yampmusicplayer.yampLcdMode.value
		if lcdMode == 'off':
			return
		return YampLCDRunningScreenV33 if lcdMode == 'rolling' else YampLCDScreenV33

	def findClockElement(self):
		try:
			for element in self.renderer:
				if "Converter.ClockToText." in str(vars(element)):
					if checkAttributes(element, "text", "clockHide"):
						self.elementClock = element
					elif checkAttributes(element, "text", "dateHide"):
						self.elementDate = element
		except Exception:
			LOG('YampVideoLyrics: findClockElement: EXCEPT', 'err')

	def showHideClock(self, Modus="Standard"):  # "SS", "Video"
		LOG('VideoLyricsScreen: showHideClock: Modus %s ' % (Modus), 'all')
		try:
			configVid = config.plugins.yampmusicplayer.showClockVideo.value
			LOG('VideoLyricsScreen: showHideClock: configVid: %s' % (configVid), 'all')
			if self.elementClock is not None:
				if Modus == "Standard":
					self.elementClock.instance.hide()
					self["clockBackground"].hide()
					LOG('VideoLyricsScreen: showHideClock: Clock & BG Hide 1', 'all')
				elif Modus == "Video":
					if configVid == "no" or configVid == "date" or configVid == "datebg":
						self.elementClock.instance.hide()
						self["clockBackground"].hide()
						LOG('VideoLyricsScreen: showHideClock: Clock & BG Hide 2', 'all')
					elif configVid == "clock" or configVid == "clockdate":
						self.elementClock.instance.show()
						self["clockBackground"].hide()
						LOG('VideoLyricsScreen: showHideClock: Clock Show, BG Hide', 'all')
					elif configVid == "clockbg" or configVid == "clockdatebg":
						self.elementClock.instance.show()
						self["clockBackground"].show()
						LOG('\nVideoLyricsScreen: showHideClock: Clock & BG Show', 'all')
			if self.elementDate is not None:
				if Modus == "Standard":
					self.elementDate.instance.hide()
					self["dateBackground"].hide()
					LOG('VideoLyricsScreen: showHideClock: Date & BG Hide 1', 'all')
				elif Modus == "Video":
					if configVid == "no" or configVid == "clock" or configVid == "clockbg":
						self.elementDate.instance.hide()
						self["dateBackground"].hide()
						LOG('VideoLyricsScreen: showHideClock: Date & BG Hide 2', 'all')
					elif configVid == "date" or configVid == "clockdate":
						self.elementDate.instance.show()
						self["dateBackground"].hide()
						LOG('VideoLyricsScreen: showHideClock: Date Show, BG Hide', 'all')
					elif configVid == "datebg" or configVid == "clockdatebg":
						self.elementDate.instance.show()
						self["dateBackground"].show()
						LOG('\nVideoLyricsScreen: showHideClock: Date & BG Show', 'all')
		except Exception:
			LOG('VideoLyricsScreen: showHideClock: EXCEPT', 'err')

	def lockShow(self):
		pass

	def unlockShow(self):
		pass
