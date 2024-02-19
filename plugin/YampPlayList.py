#######################################################################
#
#	YAMP - Yet Another Music Player - PlayList
#	Version 3.3.1 2024-01-02
#	Coded by JohnHenry (c)2013
#	Extended by AlfredENeumann (c)2016-2024
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

#from .YampGlobals import *

import os

from Components.MenuList import MenuList
from Components.config import config
from Components.GUIComponent import GUIComponent

from enigma import eListboxPythonMultiContent, RT_VALIGN_CENTER

from random import shuffle

from Tools.Directories import SCOPE_CURRENT_SKIN, resolveFilename
from Tools.LoadPixmap import LoadPixmap

from skin import parseFont, parsePosition, parseSize

from .myLogger import LOG
from .YampGlobals import yampDir, EXTENSIONS, STATE_STOP, STATE_NONE, STATE_PLAY, STATE_PAUSE


class YampPlayList(MenuList):
	def __init__(self, enableWrapAround=True):
		MenuList.__init__(self, [], enableWrapAround, eListboxPythonMultiContent)

		try:   #!!!noch andere Vorgaben fuer FHD
			self.itemFont = parseFont("Regular;18", ((1, 1), (1, 1)))
			self.myItemHeight = 23
			self.itemPos = parsePosition("25,1", ((1, 1), (1, 1)))
			self.itemSize = parseSize("470,22", ((1, 1), (1, 1)))
			self.iconPos = parsePosition("5,3", ((1, 1), (1, 1)))
			self.iconSize = parseSize("16,16", ((1, 1), (1, 1)))
		except:
			LOG('YampPlayList: init: setDefaults:  EXCEPT', 'err')

		self.currPlaying = -1
		self.oldCurrPlaying = -1			#!!!lokale Bilder
		self.icons = [
			LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/ico_mp_play.png")),
			LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/ico_mp_pause.png")),
			LoadPixmap(resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/ico_mp_stop.png")),
		]
		self.shadowList = []
		self.isShuffeled = False
		self.sortMode = 0
		self.lastSearch = ''
		self.lastSearchSuccess = 0

	def applySkin(self, desktop, parent):
		attribs = []
		self.iconFilePos = parsePosition("25,3", ((1, 1), (1, 1)))

		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "itemHeight":
					self.myItemHeight = int(value)
				elif attrib == "itemFont":
					self.itemFont = parseFont(value, ((1, 1), (1, 1)))
				elif attrib == "itemPos":
					self.itemPos = parsePosition(value, ((1, 1), (1, 1)))
				elif attrib == "itemSize":
					self.itemSize = parseSize(value, ((1, 1), (1, 1)))
				elif attrib == "iconPos":
					self.iconPos = parsePosition(value, ((1, 1), (1, 1)))
				elif attrib == "iconSize":
					self.iconSize = parseSize(value, ((1, 1), (1, 1)))
				elif attrib == "iconFilePos":
					self.iconFilePos = parsePosition(value, ((1, 1), (1, 1)))
				else:
					attribs.append((attrib, value))

		try:
			self.l.setFont(0, self.itemFont)
		except:
			LOG('YampPlayList: applySkin: setFont   EXCEPT', 'err')
		try:
			self.l.setItemHeight(self.myItemHeight)
		except:
			LOG('YampPlayList: applySkin: setHeight   EXCEPT', 'err')
		try:
			self.skinAttributes = attribs
		except:
			LOG('YampPlayList: applySkin: SetskinAttributes   EXCEPT', 'err')

		return GUIComponent.applySkin(self, desktop, parent)

	def PlaylistEntryComponent(self, serviceref, state):
		global currentPngPath
		res = [serviceref]
		text = serviceref.getName()
		currentSkinPath = yampDir + 'skins/' + config.plugins.yampmusicplayer.yampSkin.value + '/'
		currentPngPath = currentSkinPath + 'filelist/'

		if text == "":
			text = os.path.splitext(os.path.basename(serviceref.getPath()))[0]
		try:
			path = serviceref.getPath()
		except:
			LOG('PlaylistEntryComponent: path: EXCEPT', 'err')

		try:
			x = self.itemPos.x()
			y = self.itemPos.y()
		except:
			LOG('PlaylistEntryComponent: Read item x,y: EXCEPT', 'err')
		try:
			w = self.itemSize.width()
			h = self.itemSize.height()
		except:
			LOG('PlaylistEntryComponent: Read item w,h : EXCEPT', 'err')
		xi = self.iconPos.x()
		yi = self.iconPos.y()
		wi = self.iconSize.width()
		hi = self.iconSize.height()
		xi2 = self.iconFilePos.x()
		yi2 = self.iconFilePos.y()

		pngType = None
		if config.plugins.yampmusicplayer.playListIcons.value:
			extension = path.rsplit('.', 1)[-1].lower()
			if extension in EXTENSIONS:
				pngType = LoadPixmap(currentPngPath + EXTENSIONS[extension] + '.png')
		else:
			x = xi2

		notAvailableColor = 0xFF0000
		try:
			if os.path.isfile(path):
				res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, w, h, 0, RT_VALIGN_CENTER, text))
			else:
				res.append((eListboxPythonMultiContent.TYPE_TEXT, x, y, w, h, 0, RT_VALIGN_CENTER, text, notAvailableColor))
		except:
			LOG('PlaylistEntryComponent: append with color: EXCEPT', 'err')

		if pngType is not None:
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, xi2, yi2, 20, 20, pngType))

		try:
			png = self.icons[state]
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHATEST, xi, yi, wi, hi, png))
		except:
			pass
		return res

	def clear(self):
		del self.list[:]
		del self.shadowList[:]
		self.updateList()
		self.currPlaying = -1
		self.oldCurrPlaying = -1
		self.isShuffeled = False
		self.sortMode = 0

	def getSelection(self):
		return self.l.getCurrentSelection() and self.l.getCurrentSelection()[0]

	def addService(self, serviceref):
		self.list.append(self.PlaylistEntryComponent(serviceref, STATE_NONE))
		self.shadowList.append(self.PlaylistEntryComponent(serviceref, STATE_NONE))

	def addShadowService(self, serviceref):
		self.shadowList.append(self.PlaylistEntryComponent(serviceref, STATE_NONE))

	def insertService(self, index, serviceref):
		self.shadowList.insert(index, self.PlaylistEntryComponent(serviceref, STATE_NONE))
		self.list.insert(index, self.PlaylistEntryComponent(serviceref, STATE_NONE))

	def deleteService(self, index):
		currEntry = self.list[self.currPlaying]
		currRef = self.getServiceRefList()[self.currPlaying]
		currPath = currRef.getPath()

		del self.shadowList[self.getShadowIndex(index)]
		del self.list[index]  # this must be done AFTER deleting the shadowList entry, because the service to be deleted is searched for there!
		if self.currPlaying >= index:
			self.currPlaying -= 1

	def setCurrentPlaying(self, index):
#		print("YampPlayList setCurrentPlaying", index)
		self.oldCurrPlaying = self.currPlaying
		self.currPlaying = index
		self.moveToIndex(index)

	def updateState(self, state):
		if len(self.list) > self.oldCurrPlaying and self.oldCurrPlaying != -1:
			self.list[self.oldCurrPlaying] = self.PlaylistEntryComponent(self.list[self.oldCurrPlaying][0], STATE_NONE)
		if self.currPlaying != -1 and self.currPlaying < len(self.list):
			self.list[self.currPlaying] = self.PlaylistEntryComponent(self.list[self.currPlaying][0], state)
		self.updateList()

	def playService(self):
		self.updateState(STATE_PLAY)

	def pauseService(self):
		self.updateState(STATE_PAUSE)

	def stopService(self):
		self.updateState(STATE_STOP)

	def updateList(self):
		self.l.setList(self.list)

#	def getCurrentIndex(self):
#		print("YampPlayList getCurrentIndex", self.currPlaying)
#		return self.currPlaying

#	def setCurrentIndex(self, index):
#		print("YampPlayList setCurrentIndex", index)
#		try:
#			self.oldCurrPlaying = self.currPlaying
#			self.currPlaying = index
#		except:
#			LOG('setCurrentIndex: EXCEPT', 'err')

	def getServiceRefList(self):
		return [x[0] for x in self.list]

	def __len__(self):
		return len(self.list)

	def shuffleList(self):
		currEntry = self.list[self.currPlaying]
		currRef = self.getServiceRefList()[self.currPlaying]
		currPath = currRef.getPath()
		self.lastSearchSuccess = 0
		if self.isShuffeled:
			self.list = self.shadowList[:]
		else:
			shuffle(self.list)
			self.sortMode = 0
		index = 0
		for x in self.getServiceRefList():
			if x.getPath() == currPath:
				self.currPlaying = index
				self.oldCurrPlaying = -1
				self.list[index] = currEntry
				self.moveToIndex(index)
				break
			index += 1
		self.updateList()
		self.isShuffeled = not self.isShuffeled

	def sortList(self, mode):  # 0: unsorted, 1: A-Z, 2: Z-A
#		print("YampPlayList sortList", mode)
		from operator import itemgetter
		try:
			if self.currPlaying >= len(self.list):
				self.currPlaying = len(self.list) - 1
			if self.currPlaying < 0:
				self.currPlaying = 0
			currEntry = self.list[self.currPlaying]
			currRef = self.getServiceRefList()[self.currPlaying]
			currPath = currRef.getPath()
			self.lastSearchSuccess = 0
		except:
			LOG('YampPlayList: EXCEPT: currPlaying: %d  len(list): %d \r\n' % (self.currPlaying, len(self.list)), 'err')
			return
		try:
			if mode == 0:
				self.isShuffeled = True  # restore shadow list
				self.shuffleList()
			elif mode == 1:
				try:
					self.list.sort(key=itemgetter(1))
				except:
					LOG('\nYampPlayList: sortList itemgetter1: EXCEPT', 'err')
				self.isShuffeled = False
			elif mode == 2:
				try:
					self.list.sort(key=itemgetter(1), reverse=True)
				except:
					LOG('\nYampPlayList: sortList itemgetter2: EXCEPT', 'err')
				self.isShuffeled = False
			self.sortMode = mode
		except:
			LOG('\nYampPlayList: sortList: sort: EXCEPT', 'err')

		index = 0
		for x in self.getServiceRefList():
			if x.getPath() == currPath:
				self.currPlaying = index
				self.oldCurrPlaying = -1
				self.list[index] = currEntry
				self.moveToIndex(index)
				break
			index += 1
		self.updateList()

	def searchList(self, text):
		try:
			if self.lastSearch != text:
				self.lastSearchSuccess = 0
			self.lastSearch = text

			index = found = 0
			for x in self.list:
				if text in x[1][-1].lower():
					found = found + 1
					if found > self.lastSearchSuccess:
						self.lastSearchSuccess = found
						self.moveToIndex(index)
						break
				index = index + 1
				if index == len(self.list):
					self.lastSearchSuccess = 0
		except:
			LOG('YampPlayList: search: EXCEPT', 'err')

	def getSortMode(self):
		return self.sortMode

	def getShadowIndex(self, index):
		shadowIndex = index
		if self.isShuffeled or self.sortMode > 0:
			currRef = self.getServiceRefList()[index]
			currPath = currRef.getPath()
			shadowIndex = 0
			for x in self.getShadowRefList():
				if x.getPath() == currPath:
					break
				shadowIndex += 1
		return shadowIndex

	def getShadowRefList(self):
		return [x[0] for x in self.shadowList]

	def moveEntryUpMul(self, index, number, wrap):
		for i in range(0, number):
			index = self.moveEntryUp(index, wrap)

	def moveEntryUp(self, index, wrap):
#		print("YampPlayList moveEntryUp", index)
		lastIndex = len(self.list) - 1
		if index == 0:											# first entry
			if wrap:
				newIndex = lastIndex
			else:
				newIndex = index
		else:
			newIndex = index - 1

		elem = self.list.pop(index)
		self.list.insert(newIndex, elem)
		self.moveToIndex(newIndex)
		if self.currPlaying == index:					#move current playing
			self.currPlaying = newIndex
		elif self.currPlaying == index - 1:			#move across current playing
			if wrap and newIndex == lastIndex:
				self.currPlaying -= 1
			else:
				self.currPlaying += 1
		elif newIndex == lastIndex:						#title was wrapped
			self.currPlaying -= 1

		if not self.isShuffeled:
			elem = self.shadowList.pop(index)
			self.shadowList.insert(index - 1, elem)
		return newIndex

	def moveEntryDownMul(self, index, number, wrap):
		for i in range(0, number):
			index = self.moveEntryDown(index, wrap)

	def moveEntryDown(self, index, wrap):
#		print("YampPlayList moveEntryDown", index)
		if index == len(self.list) - 1:				# last entry
			if wrap:
				newIndex = 0
			else:
				newIndex = index
		else:
			newIndex = index + 1

		elem = self.list.pop(index)
		self.list.insert(newIndex, elem)
		self.moveToIndex(newIndex)
		if self.currPlaying == index:					#move current playing
			self.currPlaying = newIndex
		elif self.currPlaying == index + 1:			#move across current playing
			if wrap and newIndex == 0:
				self.currPlaying += 1
			else:
				self.currPlaying -= 1
		elif newIndex == 0:										#title was wrapped
			self.currPlaying += 1

		if not self.isShuffeled:
			elem = self.shadowList.pop(index)
			self.shadowList.insert(index + 1, elem)
		return newIndex
