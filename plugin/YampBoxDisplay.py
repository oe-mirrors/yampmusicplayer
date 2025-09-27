#######################################################################
#
# YAMP - Yet Another Music Player - Box Display
# Version 3.3.1 2023-01-01
# Coded by  by AlfredENeumann (c)2016-2024
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
# Thanks to the authors of Merlin Music Player and OpenPli Media
# Player for ideas and code snippets
#
#######################################################################

from os.path import join, exists
from enigma import eTimer
from Components.config import config
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.Label import Label
from Screens.Screen import Screen
from Tools.LoadPixmap import LoadPixmap
from .YampGlobals import yampDir
from .myLogger import LOG
from . import _


class YampLCDRunningScreenV33(Screen):  # for LCD 'Running Text'
	def __init__(self, session, parent):
		Screen.__init__(self, session, parent=parent)
		xmlfile = join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampLcdRunning.xml")
		if not exists(xmlfile):
			LOG('YampLCDRunningScreenV33: __init__: File not found: "%s"' % xmlfile, 'err')
			return
		with open(xmlfile, 'r') as f:
			self.skin = f.read()
		self["lcdRunningText"] = StaticText("")
		self.onShow.append(self.__onShow)
		self.onHide.append(self.__onHide)
		self.lcdGetTextTimer = eTimer()
		self.lcdGetTextTimer.callback.append(self.selectionChanged)

	def __onShow(self):
		self.selectionChanged()

	def __onHide(self):
		self.selectionChanged()

	def selectionChanged(self):
		lcdRunningText = self.parent.getLcdText()
		if lcdRunningText != self["lcdRunningText"].text:
			self["lcdRunningText"].text = lcdRunningText
		self.lcdGetTextTimer.start(1000)

	def setText(self, text, line):  # only for campatibility with standard LCD
		pass

	def showHideLcdCover(self, show):
		return


class YampLCDScreenV33(Screen):  # for Standard LCD 1 or 3 lines
	def __init__(self, session, parent):
		Screen.__init__(self, session, parent=parent)
		xmlfile = join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampLCD.xml")
		if not exists(xmlfile):
			LOG('YampLCDScreenV33: __init__: File not found: "%s"' % xmlfile, 'err')
			return
		with open(xmlfile, 'r') as f:
			self.skin = f.read()
		self["text1"] = Label("")
		self["text2"] = Label("")
		self["text3"] = Label("")
		self["coverArt"] = Pixmap()

	def setText(self, text, line):
		lcdMode = config.plugins.yampmusicplayer.yampLcdMode.value
		if lcdMode == 'cover':
			self["text1"].setText("")
			self["text2"].setText("")
			self["text3"].setText("")
			return
		if line == 1:
			self["text1"].setText(text)
		if lcdMode == 'threelines' or lcdMode == 'cover3':
			if line == 2:
				self["text2"].setText(text)
			elif line == 3:
				self["text3"].setText(text)
		else:
			self["text2"].setText('')
			self["text3"].setText('')

	def setCover(self):
		lcdCoverPixmap = None
		try:
			if 'cover' not in config.plugins.yampmusicplayer.yampLcdMode.value:
				self["coverArt"].hide()
				return
		except Exception:
			LOG('YampLCDScreen: setCover: hide: EXCEPT', 'err')
		try:
			lcdCoverPixmap = LoadPixmap('/tmp/coverlcd.png', cached=False)
		except Exception as e:
			LOG('YampBoxDisplay: setCover: LoadPixmap: EXCEPT', 'err')
		try:
			self["coverArt"].instance.setPixmap(lcdCoverPixmap)
		except Exception as e:
			LOG('YampBoxDisplay: setCover: setPixmap: EXCEPT: ' + str(e), 'err')
		try:
			self["coverArt"].show()
		except Exception as e:
			LOG('YampBoxDisplay: setCover: coverart show: EXCEPT: ' + str(e), 'err')

	def showHideLcdCover(self, show):
		if 'cover' in config.plugins.yampmusicplayer.yampLcdMode.value:
			if show:
				self["coverArt"].instance.show()
			else:
				self["coverArt"].instance.hide()
