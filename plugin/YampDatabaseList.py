#######################################################################
#
#    YAMP - Yet Another Music Player - DatabaseList
#    Version 3.3.2 2024-03-10
#    Coded by JohnHenry (c)2013 (up to V2.6.5)
#    Extended by AlfredENeumann (c)2016-2024
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
#######################################################################

from enigma import eListboxPythonMultiContent, eListbox, fontRenderClass, getDesktop, RT_VALIGN_TOP, RT_VALIGN_CENTER, RT_VALIGN_BOTTOM, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER
from Components.GUIComponent import GUIComponent
from Components.MultiContent import MultiContentEntryText
from skin import parseFont, parsePosition, parseSize, parseColor
from .myLogger import LOG


class YampDatabaseList(GUIComponent):
	def __init__(self, enableWrapAround=True):
		GUIComponent.__init__(self)
		try:   #!!!evtl. noch andere Vorgaben fuer FHD
			self.itemFont0 = parseFont("Regular;18", ((1, 1), (1, 1)))
			self.itemFont1 = parseFont("Regular;16", ((1, 1), (1, 1)))
			self.myItemHeight = 23
		except Exception:
			LOG('YampDatabaseList: init: setDefaults:  EXCEPT', 'err')
		self.list = []
		self.mode = 0
		self.lines = 1
		self.title = ""
		self.onSelectionChanged = []
		self.enableWrapAround = enableWrapAround
		self.l = eListboxPythonMultiContent()
		try:
			self.l.setBuildFunc(self.buildEntry)
		except Exception as e:
			LOG('YampDatabaseList:__init__:setBuildFunc: EXCEPT: ' + str(e), 'err')

		#skinning parameters
		self.parItemSizeLine1exist = False  # itemSizeLine1
		self.parHeightLine2exist = False  # itemHeightLine2

		self.parItemPosLine1exist = False  # itemPosLine1
		self.parItemPosLine2exist = False  # itemPosLine2
											#itemWidthLine1R
											#itemWidthLine2R

											#itemVAlignLine1
											#itemVAlignLine2

		self.parItemCol1exist = False		#itemColorLine1
		self.parItemCol2exist = False		#itemColorLine2
		self.parItemColSel1exist = False  # itemColorSelLine1
		self.parItemColSel2exist = False  # itemColorSelLine2

		#set default values, if not skinned
		if getDesktop(0).size().width() > 1280:  # FHD
			font0 = "Regular;28"
			font1 = "Regular;21"
			height = 30.0
		else:  # HD
			font0 = "Regular;18"
			font1 = "Regular;16"
			height = 23.0
		try:
			self.itemFont0 = parseFont(font0, ((1, 1), (1, 1)))
			self.itemFont1 = parseFont(font1, ((1, 1), (1, 1)))
			self.myItemHeightF = height
		except Exception as e:
			LOG('YampDatabaseList: init: setDefaults: EXCEPT: ' + str(e), 'err')
		self.line1sizeX = 0
		self.line2sizeX = 0
		self.line1sizeY = 0
		self.line2sizeY = 0
		self.line1PosX = 0
		self.line1PosY = 0
		self.line2PosX = 40
		self.line2PosY = 0
		self.widthLine1Right = 80
		self.widthLine2Right = 150
		self.posXline1Right = 0
		self.posXline2Right = 0
		self.alignVertLine1 = RT_VALIGN_TOP
		self.alignVertLine2 = RT_VALIGN_TOP
		self.colorLine1 = 0xFFFFFF
		self.colorLine2 = 0x777777
		self.colorSelLine1 = 0xFFFFFF
		self.colorSelLine2 = 0xAAAAAA
	GUI_WIDGET = eListbox

	def buildEntry(self, item):
		res = [None]
		if not self.parItemSizeLine1exist:
			self.line1sizeX = self.l.getItemSize().width()
			self.posXline1Right = self.line1sizeX - self.widthLine1Right
			self.posXline2Right = self.line1sizeX - self.widthLine2Right
		align1 = RT_HALIGN_CENTER | self.alignVertLine1 if item.nav else RT_HALIGN_LEFT | self.alignVertLine1
		if self.lines == 1:
			if self.parItemCol1exist and self.parItemColSel1exist:
				res.append(MultiContentEntryText(pos=(self.line1PosX, self.line1PosY), size=(self.line1sizeX, self.line1sizeY), font=0, color=self.colorLine1, color_sel=self.colorSelLine1, flags=align1, text="%s" % item.text))
			else:
				res.append(MultiContentEntryText(pos=(self.line1PosX, self.line1PosY), size=(self.line1sizeX, self.line1sizeY), font=0, flags=align1, text="%s" % item.text))
		else:  # 2 lines
			if self.parItemCol1exist and self.parItemColSel1exist:
				#line 1 with color
				if item.nav:
					res.append(MultiContentEntryText(pos=(self.line1PosX, self.line1PosY), size=(self.line1sizeX, self.line1sizeY), font=0, color=self.colorLine1, color_sel=self.colorSelLine1, flags=align1, text="%s" % item.text))
				else:
					res.append(MultiContentEntryText(pos=(self.line1PosX, self.line1PosY), size=(self.line1sizeX - self.line1PosX - self.widthLine1Right, self.line1sizeY), font=0, color=self.colorLine1, color_sel=self.colorSelLine1, flags=align1, text="%s%s  -  %s" % (item.text, item.title, item.artist)))
					#length, 1st line right
					res.append(MultiContentEntryText(pos=(self.posXline1Right, self.line1PosY), size=(self.widthLine1Right, self.line1sizeY), font=0, color=self.colorLine1, color_sel=self.colorSelLine1, flags=RT_HALIGN_RIGHT | self.alignVertLine1, text="%s" % item.length))
			else:  # line 1 no color
				if item.nav:
					res.append(MultiContentEntryText(pos=(self.line1PosX, self.line1PosY), size=(self.line1sizeX, self.line1sizeY), font=0, flags=align1, text="%s" % item.text))
				else:
					res.append(MultiContentEntryText(pos=(self.line1PosX, self.line1PosY), size=(self.line1sizeX - self.line1PosX - self.widthLine1Right, self.line1sizeY), font=0, flags=align1, text="%s%s  -  %s" % (item.text, item.title, item.artist)))
					#length, 1st line right
					res.append(MultiContentEntryText(pos=(self.posXline1Right, self.line1PosY), size=(self.widthLine1Right, self.line1sizeY), font=0, flags=RT_HALIGN_RIGHT | self.alignVertLine1, text="%s" % item.length))
			if not item.nav:  # line 2
				res.append(MultiContentEntryText(pos=(self.line2PosX, self.line2PosY), size=(self.line1sizeX - self.line2PosX - self.widthLine2Right, self.line2sizeY), font=1, color=self.colorLine2, color_sel=self.colorSelLine2, flags=RT_HALIGN_LEFT | self.alignVertLine2, text="%s  (%s)" % (item.album, item.date)))
				#genre, line 2 right
				res.append(MultiContentEntryText(pos=(self.posXline2Right, self.line2PosY), size=(self.widthLine2Right, self.line2sizeY), font=1, color=self.colorLine2, color_sel=self.colorSelLine2, flags=RT_HALIGN_RIGHT | self.alignVertLine2, text="%s" % item.genre))
		return res

	def applySkin(self, desktop, parent):
		attribs = []
		if self.skinAttributes is not None:
			try:
				for (attrib, value) in self.skinAttributes:
					if attrib == "itemFont0":
						self.itemFont0 = parseFont(value, ((1, 1), (1, 1)))
					elif attrib == "itemFont1":
						self.itemFont1 = parseFont(value, ((1, 1), (1, 1)))
					elif attrib == "itemSizeLine1":
						self.parItemSizeLine1exist = True
						size = parseSize(value, ((1, 1), (1, 1)))
						self.line1sizeX = size.width()
						self.line1sizeY = size.height()
					elif attrib == "itemHeightLine2":
						self.parHeightLine2exist = True
						self.line2sizeY = int(value)
					elif attrib == "itemPosLine1":
						self.parItemPosLine1exist = True
						pos = parsePosition(value, ((1, 1), (1, 1)))
						self.line1PosX = pos.x()
						self.line1PosY = pos.y()
					elif attrib == "itemPosLine2":
						self.parItemPosLine2exist = True
						pos = parsePosition(value, ((1, 1), (1, 1)))
						self.line2PosX = pos.x()
						self.line2PosY = pos.y()
					elif attrib == "itemWidthLine1R":
						self.widthLine1Right = int(value)
					elif attrib == "itemWidthLine2R":
						self.widthLine2Right = int(value)
					elif attrib == "itemVAlignLine1":
						if value.lower() == 'top':
							self.alignVertLine1 = RT_VALIGN_TOP
						elif value.lower() == 'bottom':
							self.alignVertLine1 = RT_VALIGN_BOTTOM
						else:
							self.alignVertLine1 = RT_VALIGN_CENTER
					elif attrib == "itemVAlignLine2":
						if value.lower() == 'top':
							self.alignVertLine2 = RT_VALIGN_TOP
						elif value.lower() == 'bottom':
							self.alignVertLine2 = RT_VALIGN_BOTTOM
						else:
							self.alignVertLine2 = RT_VALIGN_CENTER
					elif attrib == "itemColorLine1":
						self.colorLine1 = self.getColor(value)
						self.parItemCol1exist = True
					elif attrib == "itemColorLine2":
						self.colorLine2 = self.getColor(value)
						self.parItemCol2exist = True
					elif attrib == "itemColorSelLine1":
						self.colorSelLine1 = self.getColor(value)
						self.parItemColSel1exist = True
					elif attrib == "itemColorSelLine2":
						self.colorSelLine2 = self.getColor(value)
						self.parItemColSel2exist = True
					else:
						attribs.append((attrib, value))
			except Exception as e:
				LOG('YampDatabaseList: applySkin: attribs: EXCEPT: ' + str(e), 'err')
		try:
			self.l.setFont(0, self.itemFont0)
		except Exception as e:
			LOG('YampDatabaseList: applySkin: setFont0: EXCEPT: ' + str(e), 'err')
		try:
			self.l.setFont(1, self.itemFont1)
		except Exception as e:
			LOG('YampDatabaseList: applySkin: setFont1: EXCEPT: ' + str(e), 'err')
		try:
			self.skinAttributes = attribs
		except Exception as e:
			LOG('YampDatabaseList: applySkin: SetskinAttributes: EXCEPT: ' + str(e), 'err')
		self.font0h = int(fontRenderClass.getInstance().getLineHeight(self.itemFont0))
		self.font1h = int(fontRenderClass.getInstance().getLineHeight(self.itemFont1))
		if not self.parItemPosLine1exist:
			self.line1PosY = int(self.font0h * 0.01) + 1
		if not self.parItemPosLine2exist:
			self.line2PosY = int(self.font0h * 1.05 + self.font1h * 0.05) + 1
		if not self.parHeightLine2exist:
			self.line2sizeY = int(self.font1h * 1.05)
		self.posXline1Right = self.line1sizeX - self.widthLine1Right
		self.posXline2Right = self.line1sizeX - self.widthLine2Right
		return GUIComponent.applySkin(self, desktop, parent)

	def postWidgetCreate(self, instance):
		instance.setContent(self.l)
		instance.selectionChanged.get().append(self.selectionChanged)
		if self.enableWrapAround:
			self.instance.setWrapAround(True)

	def preWidgetRemove(self, instance):
		instance.setContent(None)
		instance.selectionChanged.get().remove(self.selectionChanged)

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
		if self.parItemSizeLine1exist:
			self.myItemHeightF = self.line1sizeY
		else:
			self.myItemHeightF = self.font0h * 1.1
			self.line1sizeY = int(self.font0h * 1.05)
		if self.lines == 2:
			self.myItemHeightF += self.line2sizeY if self.parHeightLine2exist else self.font1h * 1.1
		self.l.setItemHeight(int(self.myItemHeightF))

	def setTitle(self, title):
		self.title = title

	def __len__(self):
		return len(self.list)

	def getColor(self, colString):
		try:
			return parseColor(colString).argb()
		except Exception:
			return 0xFF0000


class DblistStackEntry:
	def __init__(self, mode=0, query=-1, selIndex=0, menutitle="", queryString=""):
		self.mode = mode
		self.query = query
		self.selIndex = selIndex
		self.menutitle = menutitle
		self.queryString = queryString


class DblistEntryComponent:
	def __init__(self, text="", nav=False, title="", artist="", albmartist="", album="", genre="", filename="", length="", date="", tracknr=-1, titleID=0, artistID=0, albumID=0, genreID=0, dateID=0, ref=""):
		self.text = text
		self.nav = nav
		self.title = title
		self.artist = artist
		self.album = album
		self.genre = genre
		self.filename = filename
		self.length = length
		self.date = "%s" % date if date is not None else ""
		self.tracknr = tracknr
		self.titleID = titleID
		self.artistID = artistID
		self.albumID = albumID
		self.genreID = genreID
		self.dateID = dateID
		self.ref = ref
