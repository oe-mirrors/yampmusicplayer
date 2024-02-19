#!/usr/bin/env python
# -*- coding: utf-8 -*-
#######################################################################
#
#	YAMP - Yet Another Music Player - YampPixmaps
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

from myLogger import LOG
from YampGlobals import *

from Components.AVSwitch import AVSwitch
from Components.Pixmap import Pixmap

from enigma import ePicLoad, gPixmapPtr
from Screens.MessageBox import MessageBox
from random import shuffle
from timer import TimerEntry

#
# The following class provides methods for showing coverart pictures
#
class YampCoverArtPixmap(Pixmap):
	def __init__(self):
		Pixmap.__init__(self)
		self.coverArtFilename = ""
		self.picload = ePicLoad()
		if os.path.exists("/var/lib/dpkg/status"): self.picload_conn=self.picload.PictureData.connect(self.paintCoverArtPixmapCB)
		else:	self.picload.PictureData.get().append(self.paintCoverArtPixmapCB)

	def applySkin(self, desktop, screen):
		from Tools.LoadPixmap import LoadPixmap
		self.noCoverFile = None
		if self.skinAttributes is not None:
			for (attrib, value) in self.skinAttributes:
				if attrib == "pixmap":
					self.noCoverFile = value
					break
		if self.noCoverFile is None:
			self.noCoverFile = yampDir + "common/no_coverArt.png" #!!images
		self.noCoverPixmap = LoadPixmap(self.noCoverFile)
		return Pixmap.applySkin(self, desktop, screen)

	def onShow(self):
		Pixmap.onShow(self)
		sc = AVSwitch().getFramebufferScale()
		#0=Width 1=Height 2=Aspect 3=use_cache 4=resize_type 5=Background(#AARRGGBB)
		self.picload.setPara((self.instance.size().width(), self.instance.size().height(), sc[0], sc[1], False, 1, "#00000000"))

	def paintCoverArtPixmapCB(self, picInfo=None):
		ptr = self.picload.getData()
		if ptr != None:
			LOG('YampCoverArtPixmap: paintCoverArtPixmapCB: ptr = ok', 'all')
			self.instance.setPixmap(ptr)
		else:
			try:
				self.instance.setPixmap(self.noCoverPixmap)
				LOG('YampCoverArtPixmap: paintCoverArtPixmapCB: ptr = None -> noCoverPixmap', 'all')
			except:
				LOG('YampCoverArtPixmap: paintCoverArtPixmapCB: ptr = None EXCEPT', 'err')
				
	def showDefaultCover(self):
		self.coverArtFilename = self.noCoverFile
		self.instance.setPixmap(self.noCoverPixmap)
		self.copyCover()

	def showCoverArt(self, filename):
		LOG('YampCoverArtPixmap: showCoverArt: Start: filename: %s' %(filename) , 'all')
		self.coverArtFilename = filename
		self.picload.startDecode(self.coverArtFilename)
		LOG('YampCoverArtPixmap: showCoverArt: after startDecode: filename: %s' %(filename) , 'all')
		self.copyCover()
		LOG('YampCoverArtPixmap: showCoverArt: End: filename: %s' %(filename) , 'all')
		
	def getFileName(self):
		return self.coverArtFilename
		
	def copyCover(self):
		# copy cover to unique location for third party apps, use 8192 byte chunks
		fn = self.coverArtFilename
		if fn == "":
			fn = yampDir + "common/no_coverArt.png"		#!!images
		with open(fn, 'rb') as fsrc:
			with open("/tmp/.cover", 'wb') as fdst:
				buf = fsrc.read(8192)
				while len(buf) > 0:
					fdst.write(buf)
					buf = fsrc.read(8192)

					
#
# The following class provides methods for showing screen saver slides
#
class YampScreenSaver(Pixmap):
	def __init__(self):
		Pixmap.__init__(self)
		self.picload = ePicLoad()
		self.isDreamOS = os.path.exists("/var/lib/dpkg/status")
		if not self.isDreamOS: #DreamOS: sync sonst async
			self.picload.PictureData.get().append(self.finish_decode)
		self.checkDecodeTimer = eTimer()
		if not self.isDreamOS: #DreamOS: sync sonst async
			self.checkDecodeTimer.callback.append(self.decodeTimerTimout)

		self.decodeFinished = True
		self.slideList = []
		self.slideIndex = self.displayIndex = 9
		self.currPic = self.currPicSav = []
		self.displayPtr = None

	def setList(self, slideList, slideIndex, showImmediate):
#		try:
#			pass
#			LOG('\n\nYampScreenSaver setList: len(slideList): %d' %(len(slideList)), 'spe2') 
#			LOG('YampScreenSaver setList: slideList: %s' %(slideList), 'spe2') 
#		except:
#			LOG('YampScreenSaver setList: EXCEPT', 'err')
		self.slideList = slideList
		self.slideIndex = slideIndex
		if self.slideIndex > len(self.slideList)-1: self.slideIndex = len(self.slideList)-1
		if self.slideIndex < 0: self.slideIndex = 0
		self.currPic = []
		self.currPicSav = []
		self.shownow = showImmediate
		self.displayIndex = slideIndex
		try:
			sc = AVSwitch().getFramebufferScale()
		except:
			LOG('YampScreenSaver setList: getFramebufferScale: EXCEPT', 'err')
		#0=Width 1=Height 2=Aspect 3=use_cache 4=resize_type 5=Background(#AARRGGBB)
		try:
			self.picload.setPara((self.instance.size().width(), self.instance.size().height(), sc[0], sc[1], False, 0, "#00222222"))
		except:
			LOG('YampScreenSaver setList: setPara: EXCEPT', 'err')
		self.decodeFinished = True
		self.displayPtr = None 
#		LOG('YampScreenSaver setList end: lenList %d: ' %(len(self.slideList)), 'spe2')
		if len(self.slideList) > 0:
#			LOG('YampScreenSaver setList end: slideList: %s' %(self.slideList), 'spe2')
			self.start_decode()

	def start_decode(self):
#		try:
#			LOG('\n\n\nYampScreenSaver: start_decode:slideIndex: %d slide: %s' %(self.slideIndex,self.slideList), 'spe2')
#		except:
#			LOG('\nYampScreenSaver: start_decode: newtryxx: EXCEPT 1' , 'err')
		
		if not self.decodeFinished: return
		self.decodeFinished = False
		self.currPic = []
		if len(self.slideList) < 1: 
			self.checkAddSlide()
			return
		res=0
		if self.isDreamOS:
			res = self.picload.startDecode(self.slideList[self.slideIndex], False)
			try:
				if not res: #startDecode ok
					self.checkSlide()
				else:  #startDecode error
					LOG('YampScreenSaver: start decode res<>0 corrupt slide: slide: %s ' %(self.slideList[self.slideIndex]), 'err')
					try:
						os.rename(self.slideList[self.slideIndex], self.slideList[self.slideIndex] + '_corrupt2')  
					except:
						LOG('YampScreenSaver start_decode DreamOS: rename: EXCEPT', 'err') 
					try:
						self.slideList.pop(self.slideIndex)
						self.next() #correction slideIndex only
						self.next()	#correction slideindex only
						self.decodeFinished = True
					except:
						LOG('YampScreenSaver start_decode DreamOS: pop/nextPic: EXCEPT', 'err') 

					LOG('YampScreenSaver: start_decode DreamOS: END: slide: %s ' %(self.slideList[self.slideIndex]), 'all')
			except:
				LOG('YampScreenSaver: start decode DreamOS END: EXCEPT: slide: %s' %(self.slideList[self.slideIndex]), 'err')

		else: #non DreamOS
			try:
				self.picload.startDecode(self.slideList[self.slideIndex])
				self.checkDecodeTimer.start(9000, True)
			except:
				LOG('YampScreenSaver: start decode END: EXCEPT: self.slideIndex: %d ' %(self.slideIndex), 'err')

	def decodeTimerTimout(self):
#		if self.slideIndex > (len(self.slideList) -1):
#			LOG('YampScreenSaver: decodeTimerTimout: slideIndex: %d len(slideList): %d' %(self.slideIndex,len(self.slideList)) , 'spe2')
#		else:
#			LOG('YampScreenSaver: decodeTimerTimout: slide: %s' %(self.slideList[self.slideIndex]) , 'spe2')
		try:
#			LOG('YampScreenSaver decodeTimerTimout: vor pop: %d  %s' %(len(self.slideList),self.slideList[self.slideIndex]), 'spe2') 
			self.slideList.pop(self.slideIndex)
#			LOG('YampScreenSaver decodeTimerTimout: nach pop: %d' %(len(self.slideList)), 'spe2') 
			self.next() #correction slideindex only
			self.showNextPic()
			self.decodeFinished = True
		except:
			print "=== decodeTimerTimoutEXCEPT " 
			LOG('YampScreenSaver decodeTimerTimout: pop/nextPic: EXCEPT', 'err') 
	

	def finish_decode(self, picInfo=""):
#		try:
#			LOG('YampScreenSaver: finish_decode: Start. %d slide: %s' %(self.decodeFinished, self.slideList[self.slideIndex]), 'spe2')
#		except:
#			pass
		if self.checkDecodeTimer.isActive(): self.checkDecodeTimer.stop()
		try:
			LOG('YampScreenSaver: finish_decode: self.slideIndex: %d' %(self.slideIndex), 'all')
		except:
			LOG('YampScreenSaver finish_decode: EXCEPT', 'err')
		self.checkSlide()	
		self.decodeFinished = True
			

	def showPic(self):
		if self.shownow and len(self.currPic):
			self.instance.setPixmap(self.currPic[0])
			self.displayPtr = self.currPic[0] 
			self.displayIndex = self.currPic[1]
			self.shownow = False
			self.next()
			self.start_decode()

	def refreshPic(self, test = False):
		try:
			pass
		except: LOG('PixMaps: refreshPic: decodeFinished: EXCEPT','err')	
		if self.displayPtr != None:
			if not test: self.instance.setPixmap(self.displayPtr)
			return 1
		return 0	
			
	def next(self):
		self.slideIndex += 1
		if self.slideIndex > len(self.slideList) -1:
			self.slideIndex = 0

	def prev(self):
		self.slideIndex -= 1
		if self.slideIndex < 0:
			self.slideIndex = len(self.slideList) -1

	def showNextPic(self):
		self.shownow = True
		if len(self.currPic):
			self.showPic()
		else:
			self.start_decode()

	def showPrevPic(self):
		self.slideIndex = self.displayIndex
		self.prev()
		self.shownow = True
		self.start_decode()
		
	def getCurrentSlide(self):
		if len(self.slideList):
			try:
				return self.slideList[self.displayIndex]
			except:	
				return ''
		else:
			return ''

	def removeCurrentSlide(self):		
		if len(self.slideList) > 1:
			try:
				index=self.displayIndex	
				self.showNextPic()
				self.slideList.pop(index)
			except:
				pass

	def removeSlide(self, slidepath):
		try:
			if len(self.slideList) > 1:
				self.showNextPic()
				self.slideList.remove(slidepath)
		except:		
			LOG('PixMaps removeSlide: EXCEPT' , 'err')
			
	def getLen(self):
		return len(self.slideList)
			
	def __len__(self):
		try:
			return len(self.slideList)
		except:
			return 0

	def checkAddSlide(self):
#		try:
#			LOG('YampScreenSaver checkAddSlide: len(slideList): %d slidelist: %s' %(len(self.slideList),self.slideList), 'spe2')
#		except:		
#			LOG('YampScreenSaver checkAddSlide: EXCEPT', 'err')
		if len(self.slideList) < 2:
			addPath=''
			conf=config.plugins.yampmusicplayer.screenSaverMode.value
			if conf == 'artwork':
				addPath = config.plugins.yampmusicplayer.screenSaverArtworkPath.value + 'Default/'
				if not os.path.exists(addPath):	
					addPath = yampDir + "saver/"	# 
			elif conf == 'custom':
 				addPath =  yampDir + "saver/"				

			addList = []
			if os.path.exists(addPath):	
				for filename in os.listdir(addPath):
					addList.append(addPath + filename) 
#			LOG('------YampScreenSaver checkAddSlide: addList: %s' %(addList), 'spe2')
			lenAdd = len(addList)
			if lenAdd > 1:	
				shuffle(addList)
				if addList[0] in self.slideList: self.slideList.append(addList[1])
				else: self.slideList.append(addList[0])	
				if len(self.slideList) < 2:
					if addList[0] in self.slideList: self.slideList.append(addList[1])
					else: self.slideList.append(addList[0])	
			elif lenAdd > 0: 
				if not addList[0] in self.slideList: self.slideList.append(addList[0])
			if len(self.slideList) < 2:
				self.slideList.append(yampDir + "saverblank/black.png")
#			LOG('YampScreenSaver checkAddSlide end : slidelist: %s' %(self.slideList), 'spe2')


	def checkSlide(self):
#		LOG('YampScreenSaver checkSlide: len(slideList): %d slidelist: %s' %(len(self.slideList),self.slideList), 'spe2')
		if len(self.slideList) == 0:
			self.checkAddSlide()
			return
		ptr = self.picload.getData()
		if ptr != None:
			self.currPic.append(ptr)
			self.currPic.append(self.slideIndex)
#			try:
#				LOG('YampScreenSaver checkSlide ptrOk: len(currpic): %d slide: %s' %(len(self.currPic), self.slideList[self.currPic[1]]), 'spe2')
#			except:
#				LOG('YampScreenSaver checkSlide ptrOk: Log EXCEPT)', 'spe2')
			
			self.currPicSav = self.currPic
		else:
#			LOG('YampScreenSaver checkSlide ptrNOTok: pic: %s' %(self.slideList[self.slideIndex]), 'spe2')
			#error on load pixmap
			self.currPic = self.currPicSav
			os.rename(self.slideList[self.slideIndex], self.slideList[self.slideIndex] + '_corrupt')  
			self.slideList.pop(self.slideIndex)
#			LOG('YampScreenSaver checkSlide ERROR: currpic(sav): index: %d slide: %s '%(self.currPic[1],self.slideList[self.currPic[1]] ), 'spe2')
#			LOG('YampScreenSaver checkSlide ERROR: list: %s' %(self.slideList), 'spe2')
		self.decodeFinished = True
		try:
			if len(self.slideList) < 2:
				try:
					self.checkAddSlide()
				except:
					LOG('YampScreenSaver checkSlide: checkAddSlide: EXCEPText1', 'err')
		except:
			LOG('YampScreenSaver checkSlide: add black: EXCEPT2', 'err')
		try:
			self.showPic()
		except:
			LOG('YampScreenSaver finish_decode: show pic: EXCEPT', 'err')

