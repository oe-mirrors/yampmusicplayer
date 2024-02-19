# -*- coding: utf-8 -*-
#######################################################################
#
#    YAMP - Yet Another Music Player - YampFileList
#    Version 3.3.1 2024-01-02
#    Coded by JohnHenry (c)2013
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

from enigma import eServiceReference
from myFileList import *


class YampFileList(FileList):
	def __init__(self, directory, showDirectories = True, showFiles = True, showMountpoints = True, matchingPattern = None, useServiceRef = False, inhibitDirs = False, inhibitMounts = False, isTop = False, enableWrapAround = False, additionalExtensions = None):
		FileList.__init__(self, directory, showDirectories, showFiles, showMountpoints, matchingPattern, useServiceRef, inhibitDirs, inhibitMounts, isTop, enableWrapAround, additionalExtensions)
		try:   #!!!evtl. noch andere Vorgaben fuer FHD
			self.itemFont0 = parseFont("Regular;40", ((1,1),(1,1)))
			self.itemFont1 = parseFont("Regular;30", ((1,1),(1,1)))
		except:
			LOG('YampFileList: init: setDefaults:  EXCEPT', 'err') 
		
	def getName(self):
		index = self.getSelectionIndex()
		if index < 0 or index > len (self.list)-1: # should not happen
			return ""
		return self.list[index][1][7]
	
	def searchFile(self, choice):
		self.search(choice, "File")
	
	def searchPath(self, choice):
		self.search(choice, "Path")
	
	def search(self, choice, mode):
		if choice is not None:
			self.list = []
			pattern = re.compile("(?i)^.*%s.*\.(mp2|mp3|ogg|ts|wav|m3u|pls|e2pls|mpg|vob|avi|divx|m4v|mkv|mp4|m4a|dat|flac|mov|m2ts)" % choice)
			self.list.append(FileEntryComponent(name = "<" +_("Parent Directory") + ">", absolute = self.getCurrentDirectory(), isDir = True))
			for root, folders, files in os.walk(self.getCurrentDirectory()):
				files.sort()
				for file in files:
					if mode == "Path":
						path = os.path.join(root,file)
						if pattern.search(path):
							self.list.append(FileEntryComponent(name = file, absolute = eServiceReference(4097,0,path), isDir = False))
					else:
						if pattern.search(file):
							path = os.path.join(root,file)
							self.list.append(FileEntryComponent(name = file, absolute = eServiceReference(4097,0,path), isDir = False))
			self.l.setList(self.list)
			self.moveToIndex(0)

	def __len__(self):
		return len(self.list)

