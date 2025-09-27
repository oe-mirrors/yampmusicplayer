#######################################################################
#
#    YAMP - Yet Another Music Player - YampFileList
#    Version 3.3.2 2024-03-08
#    Coded by JohnHenry (c)2013
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

from re import compile
from os import walk, listdir
from os.path import join, realpath, dirname, isdir, basename
from enigma import eListboxPythonMultiContent, eServiceCenter, eServiceReference, getDesktop, gFont, RT_VALIGN_TOP, RT_VALIGN_CENTER, RT_VALIGN_BOTTOM, RT_HALIGN_LEFT
from Components.config import config
from Components.FileList import FileList
from Components.GUIComponent import GUIComponent
from Components.MenuList import MenuList
from Components.Harddisk import harddiskmanager
from Tools.Directories import fileExists, resolveFilename, SCOPE_CURRENT_SKIN
from Tools.LoadPixmap import LoadPixmap
from skin import parseFont, parsePosition, parseSize
from .YampGlobals import yampDir, EXTENSIONS
from .myLogger import LOG
from . import _
noBT_SCALE = False
try:
	from enigma import BT_SCALE  # for images that don't support this flag
except ImportError:
	noBT_SCALE = True


class YampFileList(MenuList):
	def __init__(self, directory, showDirectories=True, showFiles=True, showMountpoints=True, matchingPattern=None, useServiceRef=False, inhibitDirs=None, inhibitMounts=None, isTop=False, enableWrapAround=False, additionalExtensions=None):
		self.currentPngPath = yampDir + 'skins/' + config.plugins.yampmusicplayer.yampSkin.value + '/filelist/'
		MenuList.__init__(self, list, enableWrapAround, eListboxPythonMultiContent)
		self.additional_extensions = additionalExtensions
		self.mountpoints = []
		self.current_directory = None
		self.current_mountpoint = None
		self.useServiceRef = useServiceRef
		self.showDirectories = showDirectories
		self.showMountpoints = showMountpoints
		self.showFiles = showFiles
		self.isTop = isTop
		# example: matching .nfi and .ts files: r"^.*\.(nfi|ts)"
		self.matchingPattern = matchingPattern
		self.inhibitDirs = inhibitDirs or []
		self.inhibitMounts = inhibitMounts or []
		if getDesktop(0).size().width() > 1280:  # FHD
			self.itemFont = parseFont("Regular;27", ((1, 1), (1, 1)))
			self.myItemWidth, self.myItemHeight = 810, 45
			self.myItemPosX, self.myItemPosY = 70, 0
			self.itemPosXno, self.myItemWidthNo = 20, 860
			self.iconPosX, self.iconPosY = 15, 7
			self.iconSizeX, self.iconSizeY = 30, 30
		else:
			self.itemFont = parseFont("Regular;18", ((1, 1), (1, 1)))
			self.myItemWidth, self.myItemHeight = 470, 22
			self.myItemPosX, self.myItemPosY = 25, 1
			self.itemPosXno, self.myItemWidthNo = 25, 520
			self.iconPosX, self.iconPosY = 5, 3
			self.iconSizeX, self.iconSizeY = 16, 16
		self.alignVert = RT_VALIGN_CENTER
		self.refreshMountpoints()
		self.changeDir(directory)
		self.directory = directory
		self.l.setFont(0, gFont("Regular", 18))
		self.l.setItemHeight(23)
		self.serviceHandler = eServiceCenter.getInstance()

	def FileEntryComponent(self, name, absolute=None, isDir=False):
		res = [(absolute, isDir)]
		if not config.plugins.yampmusicplayer.fileListIcons.value:
			res.append((eListboxPythonMultiContent.TYPE_TEXT, self.itemPosXno, self.myItemPosY, self.myItemWidthNo, self.myItemHeight, 0, RT_HALIGN_LEFT + self.alignVert, name))
		else:  # with icons
			res.append((eListboxPythonMultiContent.TYPE_TEXT, self.myItemPosX, self.myItemPosY, self.myItemWidth, self.myItemHeight, 0, RT_HALIGN_LEFT + self.alignVert, name))
			png = None
			if isDir:
				png = LoadPixmap(cached=True, path=self.currentPngPath + 'dir.png')
			else:
				extension = name.split('.')
				extension = extension[-1].lower()
				if extension in EXTENSIONS:
					png = LoadPixmap(self.currentPngPath + EXTENSIONS[extension] + '.png')
			if png is not None:
				# alphablending is really a performance killer, we should use it only with small graphics
				if noBT_SCALE:
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, self.iconPosX, self.iconPosY, self.iconSizeX, self.iconSizeY, png))
				else:
					res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, self.iconPosX, self.iconPosY, self.iconSizeX, self.iconSizeY, png, None, None, BT_SCALE))
		return res

	def applySkin(self, desktop, parent):
		attribs = []
		scale = ((1, 1), (1, 1))
		if self.skinAttributes is not None:
			try:
				for (attrib, value) in self.skinAttributes:
					if attrib == "itemPos":
						pos = parsePosition(value, ((1, 1), (1, 1)))
						self.myItemPosX = pos.x()
						self.myItemPosY = pos.y()
					elif attrib == "itemPosXNoIcon":
						self.itemPosXno = int(value)
					elif attrib == "itemHeight":  # for compatibility with old versions
						self.myItemHeight = int(value)
					elif attrib == "itemSize":
						size = parseSize(value, ((1, 1), (1, 1)))
						self.myItemWidth = size.width()
						self.myItemHeight = size.height()
					elif attrib == "itemWidthNoIcon":
						self.myItemWidthNo = int(value)
					elif attrib == "itemVAlign":
						if value.lower() == 'top':
							self.alignVert = RT_VALIGN_TOP
						elif value.lower() == 'bottom':
							self.alignVert = RT_VALIGN_BOTTOM
						else:
							self.alignVert = RT_VALIGN_CENTER
					elif attrib == "iconSize":
						size = parseSize(value, ((1, 1), (1, 1)))
						self.iconSizeX = size.width()
						self.iconSizeY = size.height()
					elif attrib == "iconPos":
						pos = parsePosition(value, ((1, 1), (1, 1)))
						self.iconPosX = pos.x()
						self.iconPosY = pos.y()
					elif attrib == "itemFont":
						self.itemFont = parseFont(value, ((1, 1), (1, 1)))
					else:
						attribs.append((attrib, value))
			except Exception as e:
				LOG('YampFileList: applySkin: EXCEPT: ' + str(e), 'err')
		try:
			self.l.setFont(0, self.itemFont)
		except Exception:
			LOG('YampFileList: applySkin: setFont0   EXCEPT', 'err')
		try:
			self.l.setItemHeight(self.myItemHeight)
		except Exception:
			LOG('YampPlayList: applySkin: setHeight   EXCEPT', 'err')
		try:
			self.skinAttributes = attribs
		except Exception:
			LOG('YampFileList: applySkin: SetskinAttributes   EXCEPT', 'err')
		return GUIComponent.applySkin(self, desktop, parent)

	def refreshMountpoints(self):
		self.mountpoints = [join(p.mountpoint, "") for p in harddiskmanager.getMountedPartitions()]
		self.mountpoints.sort(reverse=True)

	def getMountpoint(self, file):
		file = join(realpath(file), "")
		for m in self.mountpoints:
			if file.startswith(m):
				return m
		return False

	def getMountpointLink(self, file):
		if realpath(file) == file:
			return self.getMountpoint(file)
		else:
			if file[-1] == "/":
				file = file[:-1]
			mp = self.getMountpoint(file)
			last = file
			file = dirname(file)
			while last != "/" and mp == self.getMountpoint(file):
				last = file
				file = dirname(file)
			return join(last, "")

	def getSelection(self):
		if self.l.getCurrentSelection():
			return self.l.getCurrentSelection()[0]
		return []

	def getCurrentEvent(self):
		l = self.l.getCurrentSelection()
		return self.serviceHandler.info(l[0][0]).getEvent(l[0][0]) if l or l[0][1] == True else None

	def getFileList(self):
		return self.list

	def inParentDirs(self, dir, parents):
		rdir = realpath(dir)
		for p in parents:
			if rdir.startswith(p):
				return True
		return False

	def changeDir(self, directory, select=None):
		self.list = []
		# if we are just entering from the list of mount points:
		if self.current_directory is None:
			self.current_mountpoint = self.getMountpointLink(directory) if directory and self.showMountpoints else None
		self.current_directory = directory
		directories = []
		files = []
		if directory is None and self.showMountpoints:  # present available mountpoints
			for p in harddiskmanager.getMountedPartitions():
				path = join(p.mountpoint, "")
				if path not in self.inhibitMounts and not self.inParentDirs(path, self.inhibitDirs):
					self.list.append(self.FileEntryComponent(name=p.description, absolute=path, isDir=True))
			files = []
			directories = []
		elif directory is None:
			files = []
			directories = []
		elif self.useServiceRef:
			root = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + directory)
			if self.additional_extensions:
				root.setName(self.additional_extensions)
			serviceHandler = eServiceCenter.getInstance()
			hlist = serviceHandler.list(root)
			while True:
				s = hlist.getNext()
				if not s.valid():
					del hlist
					break
				if s.flags & s.mustDescent:
					directories.append(s.getPath())
				else:
					files.append(s)
			directories.sort()
			files.sort()
		else:
			if fileExists(directory):
				try:
					files = listdir(directory)
				except Exception:
					files = []
				files.sort()
				tmpfiles = files[:]
				for x in tmpfiles:
					if isdir(directory + x):
						directories.append(directory + x + "/")
						files.remove(x)
		if directory is not None and self.showDirectories and not self.isTop:
			if directory == self.current_mountpoint and self.showMountpoints:
				self.list.append(self.FileEntryComponent(name="<" + _("List of Storage Devices") + ">", absolute=None, isDir=True))
			elif (directory != "/") and not (self.inhibitMounts and self.getMountpoint(directory) in self.inhibitMounts):
				self.list.append(self.FileEntryComponent(name="<" + _("Parent Directory") + ">", absolute='/'.join(directory.split('/')[:-2]) + '/', isDir=True))
		if self.showDirectories:
			for x in directories:
				if not (self.inhibitMounts and self.getMountpoint(x) in self.inhibitMounts) and not self.inParentDirs(x, self.inhibitDirs):
					name = x.split('/')[-2]
					self.list.append(self.FileEntryComponent(name=name, absolute=x, isDir=True))
		if self.showFiles:
			for x in files:
				if self.useServiceRef:
					path = x.getPath()
					name = path.split('/')[-1]
				else:
					path = directory + x
					name = x
				if (self.matchingPattern is None) or compile(self.matchingPattern).search(path):
					self.list.append(self.FileEntryComponent(name=name, absolute=x, isDir=False))
		if self.showMountpoints and len(self.list) == 0:
			self.list.append(self.FileEntryComponent(name=_("nothing connected"), absolute=None, isDir=False))
		self.l.setList(self.list)
		if select is not None:
			i = 0
			self.moveToIndex(0)
			for x in self.list:
				p = x[0][0]
				if isinstance(p, eServiceReference):
					p = p.getPath()
				if p == select:
					self.moveToIndex(i)
				i += 1

	def getCurrentDirectory(self):
		return self.current_directory

	def canDescent(self):
		if self.getSelection():
			return self.getSelection()[1]
		return False

	def descent(self):
		if self.getSelection():
			self.changeDir(self.getSelection()[0], select=self.current_directory)

	def getFilename(self):
		if self.getSelection():
			x = self.getSelection()[0]
			if isinstance(x, eServiceReference):
				x = x.getPath()
			return x or ""
		return ""

	def getServiceRef(self):
		if self.getSelection():
			x = self.getSelection()[0]
			if isinstance(x, eServiceReference):
				return x

	def execBegin(self):
		harddiskmanager.on_partition_list_change.append(self.partitionListChanged)
		self.changeDir(self.directory)

	def execEnd(self):
		harddiskmanager.on_partition_list_change.remove(self.partitionListChanged)

	def refresh(self):
		self.changeDir(self.current_directory, self.getFilename())

	def partitionListChanged(self, action, device):
		self.refreshMountpoints()
		if self.current_directory is None:
			self.refresh()

	def getName(self):
		try:
			index = self.getSelectionIndex()
			try:
				return self.list[index][1][7]
			except Exception:
				return ''
		except Exception as e:
			LOG('YampFileList: getName: EXCEPT: ' + str(e), 'err')
		return ''

	def searchFile(self, choice):
		self.search(choice, "File")

	def searchPath(self, choice):
		self.search(choice, "Path")

	def search(self, choice, mode):
		if choice is not None:
			self.list = []
			pattern = compile(r"(?i)^.*%s.*\.(mp2|mp3|ogg|ts|wav|m3u|pls|e2pls|mpg|vob|avi|divx|m4v|mkv|mp4|m4a|dat|flac|mov|m2ts)" % choice)
			getCurrDir = self.getCurrentDirectory()
			self.list.append(self.FileEntryComponent(name="<" + _("Parent Directory") + ">", absolute=getCurrDir, isDir=True))
			if getCurrDir:
				for root, folders, files in walk(getCurrDir):
					files.sort()
					for file in files:
						if mode == "Path":
							path = join(root, file)
							if pattern.search(path):
								self.list.append(self.FileEntryComponent(name=file, absolute=eServiceReference(4097, 0, path), isDir=False))
						else:
							if pattern.search(file):
								path = join(root, file)
								self.list.append(self.FileEntryComponent(name=file, absolute=eServiceReference(4097, 0, path), isDir=False))
			self.l.setList(self.list)
			self.moveToIndex(0)

	def __len__(self):
		return len(self.list)


def MultiFileSelectEntryComponent(name, absolute=None, isDir=False, selected=False):
	res = [(absolute, isDir, selected, name)]
	res.append((eListboxPythonMultiContent.TYPE_TEXT, 55, 1, 1000, 20, 0, RT_HALIGN_LEFT, name))
	png = None
	if config.plugins.yampmusicplayer.fileListIcons.value:
		currentPngPath = yampDir + 'skins/' + config.plugins.yampmusicplayer.yampSkin.value + '/filelist/'
		if isDir:
			png = LoadPixmap(cached=True, path=currentPngPath + 'dir.png')
		else:
			extension = name.split('.')
			extension = extension[-1].lower()
			if extension in EXTENSIONS:
				png = LoadPixmap(currentPngPath + EXTENSIONS[extension] + '.png')
	if png is not None:
		res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 30, 2, 20, 20, png))
	if not name.startswith('<'):
		if selected is False:
			icon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/lock_off.png"))
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 2, 0, 25, 25, icon))
		else:
			icon = LoadPixmap(cached=True, path=resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/icons/lock_on.png"))
			res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 2, 0, 25, 25, icon))
	return res


class MultiFileSelectList(FileList):
	def __init__(self, preselectedFiles, directory, showMountpoints=False, matchingPattern=None, showDirectories=True, showFiles=True, useServiceRef=False, inhibitDirs=False, inhibitMounts=False, isTop=False, enableWrapAround=False, additionalExtensions=None):
		self.selectedFiles = preselectedFiles
		if self.selectedFiles is None:
			self.selectedFiles = []
		FileList.__init__(self, directory, showMountpoints=showMountpoints, matchingPattern=matchingPattern, showDirectories=showDirectories, showFiles=showFiles, useServiceRef=useServiceRef, inhibitDirs=inhibitDirs, inhibitMounts=inhibitMounts, isTop=isTop, enableWrapAround=enableWrapAround, additionalExtensions=additionalExtensions)
		self.changeDir(directory)
		self.l.setItemHeight(self.myItemHeight)
		self.l.setFont(0, gFont("Regular", 20))
		self.onSelectionChanged = []

	def selectionChanged(self):
		for f in self.onSelectionChanged:
			f()

	def changeSelectionState(self):
		idx = self.l.getCurrentSelectionIndex()
		count = 0
		newList = []
		for x in self.list:
			if idx == count:
				if x[0][3].startswith('<'):
					newList.append(x)
				else:
					if x[0][1] is True:
						realPathname = x[0][0]
					else:
						realPathname = self.current_directory + x[0][0]
					if x[0][2] == True:
						SelectState = False
						for entry in self.selectedFiles:
							if entry == realPathname:
								self.selectedFiles.remove(entry)
					else:
						SelectState = True
						alreadyinList = False
						for entry in self.selectedFiles:
							if entry == realPathname:
								alreadyinList = True
						if not alreadyinList:
							self.selectedFiles.append(realPathname)
					newList.append(MultiFileSelectEntryComponent(name=x[0][3], absolute=x[0][0], isDir=x[0][1], selected=SelectState))
			else:
				newList.append(x)
			count += 1
		self.list = newList
		self.l.setList(self.list)

	def getSelectedList(self):
		return self.selectedFiles

	def changeDir(self, directory, select=None):
		self.list = []
		# if we are just entering from the list of mount points:
		if self.current_directory is None:
			if directory and self.showMountpoints:
				self.current_mountpoint = self.getMountpointLink(directory)
			else:
				self.current_mountpoint = None
		self.current_directory = directory
		directories = []
		files = []
		if directory is None and self.showMountpoints:  # present available mountpoints
			for p in harddiskmanager.getMountedPartitions():
				path = join(p.mountpoint, "")
				if path not in self.inhibitMounts and not self.inParentDirs(path, self.inhibitDirs):
					self.list.append(MultiFileSelectEntryComponent(name=p.description, absolute=path, isDir=True))
			files = []
			directories = []
		elif directory is None:
			files = []
			directories = []
		elif self.useServiceRef:
			root = eServiceReference("2:0:1:0:0:0:0:0:0:0:" + directory)
			if self.additional_extensions:
				root.setName(self.additional_extensions)
			serviceHandler = eServiceCenter.getInstance()
			slist = serviceHandler.list(root)
			while 1:
				s = slist.getNext()
				if not s.valid():
					del slist
					break
				if s.flags & s.mustDescent:
					directories.append(s.getPath())
				else:
					files.append(s)
			directories.sort()
			files.sort()
		else:
			if fileExists(directory):
				try:
					files = listdir(directory)
				except OSError:
					files = []
				files.sort()
				tmpfiles = files[:]
				for x in tmpfiles:
					if isdir(directory + x):
						directories.append(directory + x + "/")
						files.remove(x)
		if directory is not None and self.showDirectories and not self.isTop:
			if directory == self.current_mountpoint and self.showMountpoints:
				self.list.append(MultiFileSelectEntryComponent(name="<" + _("List of Storage Devices") + ">", absolute=None, isDir=True))
			elif (directory != "/") and not (self.inhibitMounts and self.getMountpoint(directory) in self.inhibitMounts):
				self.list.append(MultiFileSelectEntryComponent(name="<" + _("Parent Directory") + ">", absolute='/'.join(directory.split('/')[:-2]) + '/', isDir=True))

		if self.showDirectories:
			for x in directories:
				if not (self.inhibitMounts and self.getMountpoint(x) in self.inhibitMounts) and not self.inParentDirs(x, self.inhibitDirs):
					name = x.split('/')[-2]
					alreadySelected = False
					for entry in self.selectedFiles:
						if entry == x:
							alreadySelected = True
					if alreadySelected:
						self.list.append(MultiFileSelectEntryComponent(name=name, absolute=x, isDir=True, selected=True))
					else:
						self.list.append(MultiFileSelectEntryComponent(name=name, absolute=x, isDir=True, selected=False))
		if self.showFiles:
			for x in files:
				if self.useServiceRef:
					path = x.getPath()
					name = path.split('/')[-1]
				else:
					path = directory + x
					name = x
				if (self.matchingPattern is None) or compile(self.matchingPattern).search(path):
					alreadySelected = False
					for entry in self.selectedFiles:
						if basename(entry) == x:
							alreadySelected = True
					if alreadySelected:
						self.list.append(MultiFileSelectEntryComponent(name=name, absolute=x, isDir=False, selected=True))
					else:
						self.list.append(MultiFileSelectEntryComponent(name=name, absolute=x, isDir=False, selected=False))
		self.l.setList(self.list)
		if select is not None:
			i = 0
			self.moveToIndex(0)
			for x in self.list:
				p = x[0][0]
				if isinstance(p, eServiceReference):
					p = p.getPath()
				if p == select:
					self.moveToIndex(i)
				i += 1
