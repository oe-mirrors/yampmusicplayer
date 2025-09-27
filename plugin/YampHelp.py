#######################################################################
#
#  Yamp Help Screen
#  Version 3.3.1 2024-01-07
#  Coded by AlfredENeumann (c) 2023-2024
#  Last change: 2025-09-27 by Mr.Servo @OpenATV
#  Support: www.vuplus-support.org, board.newnigma2.to
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
#######################################################################

from json import load
from os.path import join, exists
from Components.ActionMap import ActionMap, HelpableActionMap
from Components.config import config
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Pixmap import Pixmap
from Tools.LoadPixmap import LoadPixmap
from Screens.Screen import Screen
from .myLogger import LOG
from .YampFileFunctions import readRcButtonTexts
from .YampGlobals import yampDir
from . import _


class YampHelpScreenV33(Screen):
	IS_DIALOG = True

	def __init__(self, session):
		Screen.__init__(self, session)
		self.actpage = 1
		self.baseDir = join(yampDir, "common/help/")
		xmlfile = join(self.baseDir, "help.xml")
		if not exists(xmlfile):
			LOG('YampHelpScreenV33: __init__: File not found: "%s"' % xmlfile, 'err')
			return
		with open(xmlfile, 'r') as file:
			self.skin = file.read()
		jsonfile = join(self.baseDir, "helpPages.json")
		if not exists(jsonfile):
			LOG('YampHelpScreenV33: __init__: File not found: "%s"' % jsonfile, 'err')
			return
		with open(jsonfile, 'r') as file:
			helpPagesDict = load(file)
		self.HELPPAGENEWS = 3
		self.HELPPAGEFIRSTSTEPS = 7
		self.HELPPAGEOPERATION = 9
		self.HELPPAGEHINTS = 13
		self.HELPPAGENEWS = helpPagesDict["Red"]
		self.HELPPAGEFIRSTSTEPS = helpPagesDict["Green"]
		self.HELPPAGEOPERATION = helpPagesDict["Yellow"]
		self.HELPPAGEHINTS = helpPagesDict["Blue"]
		self["title"] = Label()
		self["topText"] = Label()
		self["headLine"] = Label()
		self["helpText"] = ScrollLabel()
		self["helpPic"] = Pixmap()
		self["button_red"] = Label()
		self["button_green"] = Label()
		self["button_yellow"] = Label()
		self["button_blue"] = Label()
		self["key_red"] = Label(_("Version News\nLONG: First Page"))
		self["key_green"] = Label(_("Yamp First Steps"))
		self["key_yellow"] = Label(_("Basic Operation"))
		self["key_blue"] = Label(_("Hints"))
		self.redLongActive = False
		self.textInfo, self.txtPvrVideo, self.txtBouq = readRcButtonTexts()
		self.textInfo = self.textInfo.replace('(L)', '')
		self["Actions"] = HelpableActionMap(self, "YampActions",
		{
			"right": (self.right, _("next page")),
			"left": (self.left, _("previous page")),
			"exit": (self.exit, _("Close")),
			"redLong": (self.redLong, _("first page")),
		}, -2)
		self["OtherActions"] = ActionMap(["YampOtherActions"],
		{
			"up": self.scrollUp,
			"down": self.scrollDown,
			"red": self.red,
			"green": self.green,
			"yellow": self.yellow,
			"blue": self.blue,
		}, -2)
		try:
			self.getHelpData()
		except Exception as e:
			LOG('YampHelpScreenV33: getHelpData: EXCEPT %s' % (str(e)), 'err')
		try:
			self.onLayoutFinish.append(self.setScreenValues)
		except Exception as e:
			LOG('YampHelpScreenV33: onLayoutFinish: EXCEPT %s' % (str(e)), 'err')

	def scrollUp(self):
		self["helpText"].pageUp()

	def scrollDown(self):
		self["helpText"].pageDown()

	def getHelpData(self):
		print("getHelpData")
		currentLanguage = 'en'  # default
		try:
			currentLanguage = config.osd.language.getValue().split("_")[0]
		except Exception as e:
			LOG('YampHelpScreenV33: getHelpData: language: EXCEPT %s' % (str(e)), 'err')
		print("currentLanguage", currentLanguage)
		helpFile = self.baseDir + "help.json"
		print("helpFile", helpFile)
		jsonDict = {}
		try:
			jsonDict = load(open(helpFile, 'r', encoding='utf-8'))
			print("jsonDict", jsonDict)
		except Exception as e:
			print("jsonDict", e)
			LOG('YampHelpScreenV33: getHelpData: load: EXCEPT %s' % (str(e)), 'err')
		try:
			for lang, data in jsonDict.items():
				if lang == currentLanguage:
					self.helpData = data
					break
		except Exception as e:
			LOG('YampHelpScreenV33: getHelpData: helpData: EXCEPT %s' % (str(e)), 'err')
		print("self.helpData", self.helpData)

	def setScreenValues(self):
		print("setScreenValues")
		if self.actpage < 1:
			self.actpage = 1
		elif self.actpage > len(self.helpData):
			self.actpage = len(self.helpData)
		self["title"].setText(_('YAMP Help Page ') + str(self.actpage) + '/' + str(len(self.helpData)))
		dataPage = self.helpData['page%s' % self.actpage]
		try:
			topText = str(dataPage['topText']).replace('INFO/EPG', self.textInfo).replace('PVR/VIDEO', self.txtPvrVideo).replace('BOUQET/CHANNEL', self.txtBouq)
			self["topText"].setText(topText)
			headLine = str(dataPage['headLine']).replace('INFO/EPG', self.textInfo).replace('PVR/VIDEO', self.txtPvrVideo).replace('BOUQET/CHANNEL', self.txtBouq)
			self["headLine"].setText(headLine)
			helpText = str(dataPage['text']).replace('INFO/EPG', self.textInfo).replace('PVR/VIDEO', self.txtPvrVideo).replace('BOUQET/CHANNEL', self.txtBouq)
			self["helpText"].setText(str(helpText))
		except Exception as e:
			LOG('YampHelpScreenV33: setScreenValues: setText: EXCEPT %s' % (str(e)), 'err')
		try:
			if len(dataPage['pic']):
				picFile = self.baseDir + str(dataPage['pic'])
				ptr = LoadPixmap(picFile)
				self["helpPic"].instance.setPixmap(ptr)
		except Exception as e:
			LOG('YampHelpScreenV33: setScreenValues: setPixmap: EXCEPT %s' % (str(e)), 'err')
		try:
			topTextPosSize = dataPage['ttPosSize']
			headLinePosSize = dataPage['hlPosSize']
			helpTextPosSize = dataPage['textPosSize']
			picPosSize = dataPage['picPosSize']
			self["topText"].setPosition(topTextPosSize[0], topTextPosSize[1])
			self["topText"].resize(topTextPosSize[2], topTextPosSize[3])
			self["headLine"].setPosition(headLinePosSize[0], headLinePosSize[1])
			self["headLine"].resize(headLinePosSize[2], headLinePosSize[3])
			self["helpText"].setPosition(helpTextPosSize[0], helpTextPosSize[1])
			self["helpText"].resize(helpTextPosSize[2], helpTextPosSize[3])
		except Exception as e:
			LOG('YampHelpScreenV33: setScreenValues: setPosition/resize: EXCEPT %s' % (str(e)), 'err')
		try:
			self["helpPic"].setPosition(picPosSize[0], picPosSize[1])
		except Exception as e:
			LOG('YampHelpScreenV33: setScreenValues: setPosition pic: EXCEPT %s' % (str(e)), 'err')
		try:
			self["helpPic"].resize(picPosSize[2], picPosSize[3])
		except Exception as e:
			LOG('YampHelpScreenV33: setScreenValues: resize pic: EXCEPT %s' % (str(e)), 'err')

	def right(self):
		self.actpage += 1
		self.setScreenValues()

	def left(self):
		self.actpage -= 1
		self.setScreenValues()

	def red(self):
		if self.redLongActive:
			self.redLongActive = False
		else:
			self.actpage = self.HELPPAGENEWS
			self.setScreenValues()

	def redLong(self):
		self.redLongActive = True
		self.actpage = 1
		self.setScreenValues()

	def green(self):
		self.actpage = self.HELPPAGEFIRSTSTEPS
		self.setScreenValues()

	def yellow(self):
		self.actpage = self.HELPPAGEOPERATION
		self.setScreenValues()

	def blue(self):
		self.actpage = self.HELPPAGEHINTS
		self.setScreenValues()

	def exit(self):
		self.close()
