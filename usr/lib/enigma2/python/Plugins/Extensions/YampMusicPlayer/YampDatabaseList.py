# -*- coding: utf-8 -*-
#######################################################################
#
#    YAMP - Yet Another Music Player - DatabaseList
#    Version 3.3.1 2024-01-02
#    Coded by JohnHenry (c)2013 (up to V2.6.5)
#    Extended by AlfredENeumann (c)2016-2024
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
#######################################################################

from YampGlobals import *

from Components.GUIComponent import GUIComponent
from Components.MultiContent import MultiContentEntryText

from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_VALIGN_CENTER, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER

from skin import parseFont, parsePosition, parseSize
from enigma import fontRenderClass


class YampDatabaseList(GUIComponent):
	def __init__(self, enableWrapAround=True):   #!!!!
		GUIComponent.__init__(self)

		try:   #!!!evtl. noch andere Vorgaben fuer FHD
			self.itemFont0 = parseFont("Regular;18", ((1,1),(1,1)))
			self.itemFont1 = parseFont("Regular;16", ((1,1),(1,1)))
			self.myItemHeight = 23
		except:
			LOG('YampDatabaseList: init: setDefaults:  EXCEPT', 'err') 

		self.isDreamOS = os.path.exists("/var/lib/dpkg/status")
			
		self.list = []
		self.mode = 0
		self.lines = 1
		self.title = ""
		self.onSelectionChanged = [ ]
		self.enableWrapAround = enableWrapAround
		self.l = eListboxPythonMultiContent()
		try:
			self.l.setBuildFunc(self.buildEntry)
		except:
			LOG('YampDatabaseList:__init__:set self.l.setBuildFunc:   EXCEPT', 'err') 
		
	GUI_WIDGET = eListbox

	def buildEntry(self, item):
		self.w = self.l.getItemSize().width()
		self.h = self.myItemHeight
		res = [ None ]

		line1y = int(self.font0h * 0.01) + 1
		line2y = int(self.font0h * 1.05 + self.font1h * 0.05) + 1
		line1h = int(self.font0h * 1.05)
		line2h = int(self.font1h * 1.05)

		if self.lines == 1:
			if item.nav:
				res.append (MultiContentEntryText(pos=(0, line1y), size=(self.w, line1h), font = 0, flags = RT_HALIGN_CENTER|RT_VALIGN_CENTER, text = "%s" % item.text))
			else:
				res.append (MultiContentEntryText(pos=(0, line1y), size=(self.w, line1h), font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = "%s" % item.text))
		else:
			if item.nav:
				res.append (MultiContentEntryText(pos=(0, line1y), size=(self.w, line1h), font = 0, flags = RT_HALIGN_CENTER|RT_VALIGN_CENTER, text = "%s" % item.text))
			else:
				res.append (MultiContentEntryText(pos=(0, line1y), size=(self.w-80, line1h), font = 0, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = "%s%s  -  %s" % (item.text, item.title, item.artist)))
				res.append (MultiContentEntryText(pos=(self.w-80, line1y), size=(80, line1h), font = 1, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text = "%s" % item.length))
				res.append (MultiContentEntryText(pos=(0, line2y), size=(self.w-150, line2h), font = 1, color = 0x777777, color_sel = 0xAAAAAA, flags = RT_HALIGN_LEFT|RT_VALIGN_CENTER, text = "     %s%s" % (item.album, item.date)))
				res.append (MultiContentEntryText(pos=(self.w-150, line2y), size=(150, line2h), font = 1, color = 0x777777, color_sel = 0xAAAAAA, flags = RT_HALIGN_RIGHT|RT_VALIGN_CENTER, text = "%s" % item.genre))
		return res

	def applySkin(self, desktop, parent):
		attribs = []
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "itemFont0":
					self.itemFont0 = parseFont(value, ((1,1),(1,1)))
				elif attrib == "itemFont1":
					self.itemFont1 = parseFont(value, ((1,1),(1,1)))
				else:
					attribs.append((attrib, value))
		self.font0h = int(fontRenderClass.getInstance().getLineHeight(self.itemFont0))
		self.font1h = int(fontRenderClass.getInstance().getLineHeight(self.itemFont1))

		try:
			self.l.setFont(0, self.itemFont0)
		except:
			LOG('YampDatabaseList: applySkin: setFont0   EXCEPT', 'err') 
		try:
			self.l.setFont(1, self.itemFont1)
		except:
			LOG('YampDatabaseList: applySkin: setFont1   EXCEPT', 'err') 
		try:
			self.skinAttributes = attribs
		except:
			LOG('YampDatabaseList: applySkin: SetskinAttributes   EXCEPT', 'err') 
		return GUIComponent.applySkin(self, desktop, parent)
	
	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		if self.isDreamOS: instance.selectionChanged_conn=instance.selectionChanged.connect(self.selectionChanged)
		else:	instance.selectionChanged.get().append(self.selectionChanged)
		if self.enableWrapAround:
			self.instance.setWrapAround(True)

	def preWidgetRemove(self, instance):
		instance.setContent(None)
		if self.isDreamOS: instance.selectionChanged_conn = None
		else:	instance.selectionChanged.get().remove(self.selectionChanged)

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

	def getDatabaseList(self):
		return self.list

	def setMode(self, mode):
		self.mode = mode
		
	def setLines(self, lines):
		self.lines = lines
		if self.lines == 1:
			self.myItemHeight = int(self.font0h * 1.1)
			self.l.setItemHeight(self.myItemHeight)
		else:
			self.myItemHeight = int((self.font0h + self.font1h) * 1.1)
			self.l.setItemHeight(self.myItemHeight)

	def setTitle(self, title):
		self.title = title

	def __len__(self):
		return len(self.list)

class DblistStackEntry:
	def __init__(self, mode = 0, query = -1, selIndex = 0, menutitle = "", queryString = ""):
		self.mode = mode
		self.query = query
		self.selIndex = selIndex
		self.menutitle = menutitle
		self.queryString = queryString
		
class DblistEntryComponent:
	def __init__(self, text = "", nav = False, title = "", artist = "", album = "", genre = "", filename = "", length = "", date = "", tracknr = -1, titleID = 0, artistID = 0, albumID = 0, genreID = 0, dateID = 0, ref = ""):
		self.text = text
		self.nav = nav
		self.title = title
		self.artist = artist
		self.album = album
		self.genre = genre
		self.filename = filename
		self.length = length
		if date is not None:
			self.date = " (%s)" % date
		else:
			self.date = ""
		self.tracknr = tracknr
		self.titleID = titleID
		self.artistID = artistID
		self.albumID = albumID
		self.genreID = genreID
		self.dateID = dateID
		self.ref = ref
