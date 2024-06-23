# -*- coding: utf-8 -*-
#######################################################################
#
#	YAMP - Yet Another Music Player - PlayList
#	Version 3.3.2 2024-03-17
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

from YampGlobals import *

from Components.MenuList import MenuList
from Components.config import config
from Components.GUIComponent import GUIComponent
from Components.MultiContent import MultiContentEntryText

from enigma import eListboxPythonMultiContent, RT_VALIGN_TOP, RT_VALIGN_CENTER, RT_VALIGN_BOTTOM, gFont
import enigma
from enigma import getDesktop

from random import shuffle

from Tools.Directories import SCOPE_CURRENT_SKIN, resolveFilename
from Tools.LoadPixmap import LoadPixmap

from skin import parseFont, parsePosition, parseSize


class YampPlayList(MenuList):
	def __init__(self, enableWrapAround = True):
		MenuList.__init__(self, [], enableWrapAround, eListboxPythonMultiContent)

		self.currentPngPath=yampDir + 'skins/' + config.plugins.yampmusicplayer.yampSkin.value + '/filelist/'

		if getDesktop(0).size().width() > 1280:	#FHD
			self.itemFont=parseFont("Regular;28", ((1,1),(1,1)))
			self.myItemWidth = 795
			self.myItemHeight = 45
			self.myItemPosX = 85
			self.myItemPosY = 0
			self.itemPosXno = 45
			self.myItemWidthNo = 835
			self.alignVert = RT_VALIGN_CENTER
			self.iconPosX = 40
			self.iconPosY = 7
			self.iconSizeX = 30
			self.iconSizeY = 30
			self.iconPlayPosX = 6
			self.iconPlayPosY = 10
			self.iconPlaySizeX = 25
			self.iconPlaySizeY = 25
		else:	
			self.itemFont=parseFont("Regular;18", ((1,1),(1,1)))
			self.myItemWidth = 520
			self.myItemHeight = 25
			self.myItemPosX = 45
			self.myItemPosY = 1
			self.itemPosXno = 25
			self.myItemWidthNo = 560
			self.alignVert = RT_VALIGN_CENTER
			self.iconPosX = 5
			self.iconPosY = 3
			self.iconSizeX = 16
			self.iconSizeY = 16
			self.iconPlayPosX = 2
			self.iconPlayPosY = 4
			self.iconPlaySizeX = 16
			self.iconPlaySizeY = 16

		self.currPlaying = -1
		self.oldCurrPlaying = -1		#!!!lokale Icons??	
		self.iconsPlayState = [
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

		if self.skinAttributes is not None:
			try:
				for (attrib, value) in self.skinAttributes:
					if attrib == "itemPos":
						pos = parsePosition(value, ((1,1),(1,1)))
						self.myItemPosX = pos.x()
						self.myItemPosY = pos.y()
					elif attrib == "itemPosXNoIcon":
						self.itemPosXno = int(value)
					elif attrib == "itemHeight":	#for compatibility with old versions
						self.myItemHeight = int(value)
					elif attrib == "itemSize":
						size = parseSize(value, ((1,1),(1,1)))
						self.myItemWidth = size.width()
						self.myItemHeight = size.height()
					elif attrib == "itemWidthNoIcon":
						self.myItemWidthNo = int(value)

					elif attrib == "itemVAlign":
						if value.lower() == 'top': self.alignVert = RT_VALIGN_TOP
						elif value.lower() == 'bottom': self.alignVert = RT_VALIGN_BOTTOM
						else: self.alignVert = RT_VALIGN_CENTER
					elif attrib == "iconSize":
						size = parseSize(value, ((1,1),(1,1)))
						self.iconSizeX = size.width()
						self.iconSizeY = size.height()
					elif attrib == "iconFilePos":	#forcompatibility with old version
						pos = parsePosition(value, ((1,1),(1,1)))
						self.iconPosX = pos.x()
						self.iconPosY = pos.y()
					elif attrib == "iconPos":
						pos = parsePosition(value, ((1,1),(1,1)))
						self.iconPosX = pos.x()
						self.iconPosY = pos.y()
					elif attrib == "iconPlaySize":
						size = parseSize(value, ((1,1),(1,1)))
						self.iconPlaySizeX = size.width()
						self.iconPlaySizeY = size.height()
					elif attrib == "iconPlayPos":
						pos = parsePosition(value, ((1,1),(1,1)))
						self.iconPlayPosX = pos.x()
						self.iconPlayPosY = pos.y()
					elif attrib == "itemFont":
						self.itemFont = parseFont(value, ((1,1),(1,1)))
					else:
						attribs.append((attrib, value))
			except Exception as e:		
				LOG('\nYampPlayList: applySkin: EXCEPT: ' + str(e), 'err')
					
		try:
			self.l.setFont(0, self.itemFont)
		except Exception as e:		
			LOG('YampPlayList: applySkin: setFont: EXCEPT: ' + str(e), 'err') 
		try:
			self.l.setItemHeight(self.myItemHeight)
		except Exception as e:		
			LOG('YampPlayList: applySkin: setHeight: EXCEPT: ' + str(e), 'err') 
		try:
			self.skinAttributes = attribs
		except Exception as e:		
			LOG('YampPlayList: applySkin: SetskinAttributes EXCEPT: ' + str(e), 'err') 

		return GUIComponent.applySkin(self, desktop, parent)


	def PlaylistEntryComponent(self, serviceref, state):
		noBT_SCALE = False
		try: from enigma import BT_SCALE
		except: noBT_SCALE = True

		res = [ serviceref ]
		text = serviceref.getName()

		if text == "":
			text = os.path.splitext(os.path.basename(serviceref.getPath()))[0]
		try:
			path = serviceref.getPath()
		except Exception as e:		
			LOG('YampPlayList: PlaylistEntryComponent: path: EXCEPT: ' + str(e), 'err')

		notAvailableColor = 0xFF0000 
		if not config.plugins.yampmusicplayer.playListIcons.value:
			try:
				if os.path.isfile(path):
					res.append((eListboxPythonMultiContent.TYPE_TEXT, self.itemPosXno, self.myItemPosY, self.myItemWidthNo, self.myItemHeight, 0, self.alignVert, text))
				else:
					res.append((eListboxPythonMultiContent.TYPE_TEXT, self.itemPosXno, self.myItemPosY, self.myItemWidthNo, self.myItemHeight, 0, self.alignVert, text, notAvailableColor))
			except Exception as e:		
				LOG('YampPlayList: PlaylistEntryComponent: append with color: EXCEPT: + str(e)', 'err')
		else:	#with icons
			try:
				if os.path.isfile(path):
					res.append((eListboxPythonMultiContent.TYPE_TEXT, self.myItemPosX, self.myItemPosY, self.myItemWidth, self.myItemHeight, 0, self.alignVert, text))
				else:
					res.append((eListboxPythonMultiContent.TYPE_TEXT, self.myItemPosX, self.myItemPosY, self.myItemWidth, self.myItemHeight, 0, self.alignVert, text, notAvailableColor))
			except Exception as e:		
				LOG('YampPlayList: PlaylistEntryComponent: append with color, icon: EXCEPT' + str(e), 'err')
		
			png = None
			extension = path.rsplit('.',1)[-1].lower()
			if EXTENSIONS.has_key(extension):
				png = LoadPixmap(self.currentPngPath + EXTENSIONS[extension] + '.png')
			if png is not None:
				if noBT_SCALE: #TYPE_PIXMAP_ALPHATEST?
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, self.iconPosX, self.iconPosY, self.iconSizeX, self.iconSizeY, png))
				else:
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, self.iconPosX, self.iconPosY, self.iconSizeX, self.iconSizeY, png, None, None, BT_SCALE))
		#play, pause, stop icon
		try:
			if state == STATE_NONE: return res 

			png = self.iconsPlayState[state]
			if noBT_SCALE:  #TYPE_PIXMAP_ALPHATEST?
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, self.iconPlayPosX, self.iconPlayPosY, self.iconPlaySizeX, self.iconPlaySizeY, png))
			else:
				res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, self.iconPlayPosX, self.iconPlayPosY, self.iconPlaySizeX, self.iconPlaySizeY, png, None, None, BT_SCALE))
		except Exception as e:		
			LOG('YampPlayList: PlaylistEntryComponent: PlayIcon: EXCEPT' + str(e), 'err')
		return res


	def clear(self):
		del self.list[:]
		del self.shadowList[:]
		self.updateList()
		self.currPlaying = -1
		self.oldCurrPlaying = -1
		self.isShuffeled = False
		self.sortMode = 0

	def getName(self, index):
		try:
			try:
				return self.list[index][1][7]
			except:
				return ''
		except Exception as e:		
			LOG('YampPlayList: getName: EXCEPT' + str(e), 'err')

		
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
#		currEntry = self.list[self.currPlaying]
		currRef = self.getServiceRefList()[self.currPlaying]
		currPath = currRef.getPath()
		del self.shadowList [self.getShadowIndex(index)]
		del self.list[index] # this must be done AFTER deleting the shadowList entry, because the service to be deleted is searched for there!
		if self.currPlaying >= index:
			self.currPlaying -= 1

	def setCurrentPlaying(self, index):
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

	def getCurrentIndex(self):
		return self.currPlaying

	def setCurrentIndex(self, index):
		try:
			self.oldCurrPlaying = self.currPlaying
			self.currPlaying = index
		except:
			LOG('setCurrentIndex: EXCEPT', 'err')
			
	def getServiceRefList(self):
		return [ x[0] for x in self.list ]

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
		
	def sortList(self, mode):	#0: unsorted, 1: A-Z, 2: Z-A
		from operator import itemgetter
		try:
			if self.currPlaying >= len(self.list): self.currPlaying = len(self.list) - 1
			if self.currPlaying < 0: self.currPlaying = 0
			currEntry = self.list[self.currPlaying]
			currRef = self.getServiceRefList()[self.currPlaying]
			currPath = currRef.getPath()
			self.lastSearchSuccess = 0
		except:
			LOG('YampPlayList: EXCEPT: currPlaying: %d  len(list): %d \r\n' %(self.currPlaying, len(self.list)), 'err' )
			return
		try:
			if mode == 0:			
				self.isShuffeled = True	#restore shadow list
				self.shuffleList()
			elif mode == 1: 
				try:
					self.list.sort(key=itemgetter(1))
				except:
					LOG('\nYampPlayList: sortList itemgetter1: EXCEPT', 'err')
				self.isShuffeled = False
			elif mode == 2: 
				try:
					self.list.sort(key=itemgetter(1),reverse = True)
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
			if self.lastSearch != text: self.lastSearchSuccess = 0
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
		return [ x[0] for x in self.shadowList ]

	def moveEntryUpMul(self, index, number, wrap):
		for i in xrange(0,number):
			index=self.moveEntryUp(index,wrap)

	def moveEntryUp(self, index, wrap):
		lastIndex = len(self.list) - 1 
		if index == 0:											# first entry
			if wrap: newIndex = lastIndex
			else: newIndex = index
		else: newIndex = index-1

		elem = self.list.pop(index)
		self.list.insert(newIndex, elem)
		self.moveToIndex(newIndex)
		if self.currPlaying == index:					#move current playing
			self.currPlaying = newIndex
		elif self.currPlaying == index-1:			#move across current playing
			if wrap and newIndex == lastIndex: self.currPlaying -= 1
			else: self.currPlaying += 1
		elif newIndex == lastIndex:						#title was wrapped
			self.currPlaying -=1
		if self.currPlaying < -1: self.currPlaying = -1	

		if not self.isShuffeled:
			elem = self.shadowList.pop(index)
			self.shadowList.insert(index-1, elem)
		return newIndex	

	def moveEntryDownMul(self, index, number, wrap):
		for i in xrange(0,number):
			index=self.moveEntryDown(index,wrap)
		
	def moveEntryDown(self, index, wrap):
		if index == len(self.list) - 1:				# last entry
			if wrap: newIndex = 0
			else: newIndex = index
		else: newIndex = index+1
		
		elem = self.list.pop(index)
		self.list.insert(newIndex, elem)
		self.moveToIndex(newIndex)
		if self.currPlaying == index:					#move current playing
			self.currPlaying = newIndex
		elif self.currPlaying == index+1:			#move across current playing
			if wrap and newIndex == 0: self.currPlaying += 1
			else: self.currPlaying -= 1
		elif newIndex == 0:										#title was wrapped
			self.currPlaying +=1

		if not self.isShuffeled:
			elem = self.shadowList.pop(index)
			self.shadowList.insert(index+1, elem)
		return newIndex	
