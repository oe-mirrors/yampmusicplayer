

# -*- coding: utf-8 -*-
#######################################################################
#
#    YAMP - Yet Another Music Player - Box Display
#    Version 3.3.1 2023-01-01 
#    Coded by  by AlfredENeumann (c)2016-2024
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

from YampGlobals import *
from Components.Pixmap import Pixmap, MultiPixmap

class YampLCDRunningScreenV33(Screen):	  #for LCD 'Running Text'
	def __init__(self, session, parent):
		Screen.__init__(self, session, parent = parent)

		filePathName=os.path.join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampLcdRunning.xml")
		try:
			with open(filePathName, 'r') as f:
				self.skin = f.read()
		except:
			LOG(_('YampLCDRunningScreenV33: Failed to open/read %s') %(filePathName), 'err')

		self["lcdRunningText"] = StaticText("")
		self.onShow.append(self.__onShow)
		self.onHide.append(self.__onHide)
		self.lcdGetTextTimer = eTimer()
		if os.path.exists("/var/lib/dpkg/status"):
			self.lcdGetTextTimer_conn=self.lcdGetTextTimer.timeout.connect(self.selectionChanged)
		else:
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

	def setText(self, text, line):		#only for campatibility with standard LCD
		text = text

	def showHideLcdCover(self, show):
		return

class YampLCDScreenV33(Screen):	#for Standard LCD 1 or 3 lines
	def __init__(self, session, parent):
		Screen.__init__(self, session, parent = parent)
		filePathName=os.path.join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampLCD.xml")
		try:
			with open(filePathName, 'r') as f:
				self.skin = f.read()
		except:
			LOG(_('YampLCDScreenV33: Failed to open/read %s') %(filePathName), 'err')

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
		try:
			if not ('cover' in config.plugins.yampmusicplayer.yampLcdMode.value):
				self["coverArt"].hide()
				return
		except: LOG('YampLCDScreen: setCover: hide: EXCEPT', 'err')
		try:
			from Tools.LoadPixmap import LoadPixmap
		except: LOG('YampBoxDisplay: setCover: import: EXCEPT', 'err')
		try: lcdCoverPixmap = LoadPixmap('/tmp/coverlcd.png',cached=False)
		except Exception as e:
			LOG('YampBoxDisplay: setCover: LoadPixmap: EXCEPT', 'err')

		try: self["coverArt"].instance.setPixmap(lcdCoverPixmap )
		except Exception as e:
			LOG('YampBoxDisplay: setCover: setPixmap: EXCEPT: ' + str(e), 'err')
		try: self["coverArt"].show()
		except Exception as e:
			LOG('YampBoxDisplay: setCover: coverart show: EXCEPT: ' + str(e), 'err')

	def showHideLcdCover(self, show):
		if 'cover' in config.plugins.yampmusicplayer.yampLcdMode.value:
			if show: 
				self["coverArt"].instance.show()
			else: 
				self["coverArt"].instance.hide()
