# -*- coding: UTF-8 -*-
#######################################################################
#  Yamp File Functions  
#    Version 3.3.1 2024-01-02
#  Coded by AlfredENeumann (c) 2022-2024
#  Support: www.vuplus-support.org, board.newnigma2.to
#
#  All Files of this Software are licensed under the Creative Commons
#  Attribution-NonCommercial-ShareAlike 3.0 Unported
#  License if not stated otherwise in a Files Head. To view a copy of this license, visit
#  http://creativecommons.org/licenses/by-nc-sa/3.0/ or send a letter to Creative
#  Commons, 559 Nathan Abbott Way, Stanford, California 94305, USA.
#
#  This plugin is NOT free software. It is open source, you are allowed to
#  modify it (if you keep the license), but it may not be commercially
#  distributed other than under the conditions noted above.
#  This applies to the source code as a whole as well as to parts of it, unless
#  explicitely stated otherwise.
#######################################################################

from YampGlobals import *
from myLogger import LOG

from Components.config import config
import os

OFFSETCOMMENT = 1700

def getEncodedString(value):
	returnValue = ""
	try:
		returnValue = value.encode("utf-8", 'ignore')
	except UnicodeDecodeError:
		try:
			returnValue = value.encode("iso8859-1", 'ignore')
		except UnicodeDecodeError:
			try:
				returnValue = value.decode("cp1252").encode("utf-8")
			except UnicodeDecodeError:
				returnValue = "n/a"
	return returnValue



def htmlUnescape(text):		#replace html strings like German 'umlauts' and others
		replDict = {'&Auml;':'Ä','&auml;':'ä','&Ouml;':'Ö','&ouml;':'ö','&Uuml;':'Ü','&uuml;':'ü','&szlig;':'ß','&auml;':'ä','&auml;':'ä','&auml;':'ä','&auml;':'ä'}
		for key,val in replDict.iteritems():
			text = text.replace(key,val)
		return text


def writeLcdRunning():
	try:
		f=open(os.path.join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampLcdRunning.xml"), 'r')
		data = f.read()
		f.close()

		LcdWidth,LcdHeight, posLcdsize, lastPos = getSize(data, OFFSETCOMMENT) 
		positionX,positionY, posPosition, lastPos = getPosition(data, lastPos) 

		WidthRText,HeightRText, posSizeRText, lastPos = getSize(data, lastPos) 
		fontSize, posFont, lastPos = getFont(data, lastPos) 

		newLcdWidth=config.plugins.yampmusicplayer.lcdSize.value.split('x')[0]
		newLcdHeight=config.plugins.yampmusicplayer.lcdSize.value.split('x')[1]

		rep=data[posLcdsize:].replace(LcdWidth+',',newLcdWidth+',',1)
		rep=rep.replace(','+LcdHeight,','+newLcdHeight,1)
		data=data[:posLcdsize] + rep

		posTop=posPosition+data[posPosition:].find(',')+1

		rep=data[posTop:]
		rep=rep.replace(WidthRText+',',newLcdWidth+',',1)
		rep=rep.replace(','+HeightRText,','+newLcdHeight,1)
		data=data[:posTop] + rep

		rep=data[posFont:].replace(';'+fontSize,';'+str(config.plugins.yampmusicplayer.lcdRunningFontSize.value),1)
		data=data[:posFont] + rep

		f=open(os.path.join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampLcdRunning.xml"), 'w')
		f.write(data)
		f.close()
		return 0
	except:
		return -1
		

def writeLcd():
	try:
		f=open(os.path.join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampLCD.xml"), 'r')
		data = f.read()
		f.close()

		LcdWidth,LcdHeight, posLcdsize, lastPos = getSize(data, OFFSETCOMMENT) 
		
		positionXText1,positionYText1, posPositionText1, lastPos = getPosition(data, lastPos) 

		WidthText1,HeightText1, posSizeText1, lastPos = getSize(data, lastPos) 
		fontSizeText1, posFontText1, lastPos = getFont(data, lastPos) 

		alignText1, posalignText1, lastPos = getAlign(data, lastPos) 
		colorText1, posColorText1, lastPos = getForeColor(data, lastPos) 

		positionXText2,positionYText2, posPositionText2, lastPos = getPosition(data, lastPos) 

		WidthText2,HeightText2, posSizeText2, lastPos = getSize(data, lastPos) 

		fontSizeText2, posFontText2, lastPos = getFont(data, lastPos) 

		alignText2, posalignText2, lastPos = getAlign(data, lastPos) 

		colorText2, posColorText2, lastPos = getForeColor(data, lastPos) 

		positionXText3,positionYText3, posPositionText3, lastPos = getPosition(data, lastPos) 

		WidthText3,HeightText3, posSizeText3, lastPos = getSize(data, lastPos) 

		fontSizeText3, posFontText3, lastPos = getFont(data, lastPos) 

		alignText3, posalignText3, lastPos = getAlign(data, lastPos) 

		colorText3, posColorText3, lastPos = getForeColor(data, lastPos) 

		positionXCover,positionYCover, posPositionCover, lastPos = getPosition(data, lastPos) 

		WidthCover,HeightCover, posSizeCover, lastPos = getSize(data, lastPos) 

		lcdMode = config.plugins.yampmusicplayer.yampLcdMode.value
		newLcdWidth = config.plugins.yampmusicplayer.lcdSize.value.split('x')[0]
		newLcdHeight = config.plugins.yampmusicplayer.lcdSize.value.split('x')[1]

		newTextWidth = str(config.plugins.yampmusicplayer.lcdTextLen.value)
		newTextAlign = config.plugins.yampmusicplayer.lcdTextHoriz.value 
		newTextPosX = str(config.plugins.yampmusicplayer.lcdTextPosX.value)
		newCoverSize = str(config.plugins.yampmusicplayer.lcdCoverSize.value)
		newCoverPosX = str(config.plugins.yampmusicplayer.lcdCoverPosX.value)
		newCoverPosY = str(config.plugins.yampmusicplayer.lcdCoverPosY.value)


		textMinTop = config.plugins.yampmusicplayer.lcdTextTopMin.value		

		if lcdMode == 'oneline' or lcdMode == 'cover1':
			newTextHeight1 = (int(newLcdHeight) - 2*textMinTop)
			newTextHeight2 = newTextHeight3 = 0
			newText2PosY = newText3PosY = str(int(newLcdHeight) - 1)
		else:	
			newTextHeight1 = newTextHeight2 = newTextHeight3 = (int(newLcdHeight) - 2*textMinTop) / 3
			newText2PosY = str(newTextHeight1 + textMinTop)
			newText3PosY = str(newTextHeight1*2 + textMinTop)
		newTextHeight1 = str(newTextHeight1)
		newTextHeight2 = str(newTextHeight2)
		newTextHeight3 = str(newTextHeight3)
			
		newFontSize=str(config.plugins.yampmusicplayer.lcdFontSize.value)
	
		newColorText1 = config.plugins.yampmusicplayer.lcdColorLine1.value
		newColorText2 = config.plugins.yampmusicplayer.lcdColorLine2.value
		newColorText3 = config.plugins.yampmusicplayer.lcdColorLine3.value


		rep=data[posLcdsize:].replace(LcdWidth+',',newLcdWidth+',',1)
		rep=rep.replace(','+LcdHeight,','+newLcdHeight,1)
		data=data[:posLcdsize] + rep

		rep=data[posPositionText1:].replace(positionXText1+',',newTextPosX+',',1)
		rep=rep.replace(','+positionYText1,','+str(textMinTop),1)
		data=data[:posPositionText1] + rep

		rep=data[posSizeText1:].replace(WidthText1+',',newTextWidth+',',1)
		rep=rep.replace(','+HeightText1,','+newTextHeight1,1)
		rep=rep.replace(';'+fontSizeText1,';'+newFontSize,1)
		rep=rep.replace(alignText1,newTextAlign,1)
		rep=rep.replace(colorText1,newColorText1,1)
		data=data[:posSizeText1] + rep

		rep=data[posPositionText2:].replace(positionXText2+',',newTextPosX+',',1)
		rep=rep.replace(','+positionYText2,','+newText2PosY,1)
		data=data[:posPositionText2] + rep

		rep=data[posSizeText2:].replace(WidthText2+',',newTextWidth+',',1)
		rep=rep.replace(','+HeightText2,','+newTextHeight2,1)
		rep=rep.replace(';'+fontSizeText2,';'+newFontSize,1)
		rep=rep.replace(alignText2,newTextAlign,1)
		rep=rep.replace(colorText2,newColorText2,1)
		data=data[:posSizeText2] + rep

		rep=data[posPositionText3:].replace(positionXText3+',',newTextPosX+',',1)
		rep=rep.replace(','+positionYText3,','+newText3PosY,1)
		data=data[:posPositionText3] + rep

		rep=data[posSizeText3:].replace(WidthText3+',',newTextWidth+',',1)
		rep=rep.replace(','+HeightText3,','+newTextHeight3,1)
		rep=rep.replace(';'+fontSizeText3,';'+newFontSize,1)
		rep=rep.replace(alignText3,newTextAlign,1)
		rep=rep.replace(colorText3,newColorText3,1)
		data=data[:posSizeText3] + rep

		rep=data[posPositionCover:].replace(positionXCover+',',newCoverPosX+',',1)
		rep=rep.replace(','+positionYCover,','+newCoverPosY,1)
		data=data[:posPositionCover] + rep
		
		rep=data[posSizeCover:].replace(WidthCover+',',newCoverSize+',',1)
		rep=rep.replace(','+HeightCover,','+newCoverSize,1)
		data=data[:posSizeCover] + rep

		f=open(os.path.join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampLCD.xml"), 'w')
		f.write(data)
		f.close()
		return 0
	except Exception as e:
		print '=== writeLcd: EXCEPT writeLcd:', str(e) 
		return -1

def writeVTIRunningRenderer():
	VTi = checkVTi() and (os.path.exists('/usr/lib/enigma2/python/Components/Renderer/VRunningText.py') or os.path.exists('/usr/lib/enigma2/python/Components/Renderer/VRunningText.pyo'))
	try:
		f=open(os.path.join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampLcdRunning.xml"), 'r')
		data = f.read()
		f.close()

		posRender=data.find('render=',OFFSETCOMMENT)
		if VTi:
			rep=data[posRender:].replace('="RunningText"','="VRunningText"',1)
		else:
			rep=data[posRender:].replace('="VRunningText"','="RunningText"',1)
		data=data[:posRender] + rep

		f=open(os.path.join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampLcdRunning.xml"), 'w')
		f.write(data)
		f.close()
		return 0
	except:
		return -1


def readCustomCoverSize():
	try:
		f=open(os.path.join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampLCD.xml"), 'r')
		data = f.read()
		f.close()
		posCover = data.find('coverArt',OFFSETCOMMENT)
		WidthCover,HeightCover, posSizeCover, lastPos = getSize(data, posCover) 
	
		return(int(WidthCover))
	except:
		return -1

def getPosition(data,startIdx):
	posPosition=data.find('position=',startIdx)
	posComma = data.find(',',posPosition)
	posEnd = data.find('"',posComma)
	positionX = data[posPosition+10:posComma]
	positionY = data[posComma+1:posEnd]
	return positionX, positionY, posPosition, posEnd

def getSize(data,startIdx):
	posSize=data.find('size=',startIdx)
	posComma = data.find(',',posSize)
	posEnd = data.find('"',posComma)
	Width = data[posSize+6:posComma]	
	Height = data[posComma+1:posEnd]
	return Width, Height, posSize, posEnd
	
def getFont(data,startIdx):
	posFont = data.find('font=',startIdx)
	posSemik = data.find(';',posFont)
	posEnd=data.find('"',posSemik)
	font = data[posFont+6:posSemik]
	fontSize = data[posSemik+1:posEnd]
	return fontSize, posFont, posEnd

def getForeColor(data,startIdx):
	posForeColor = data.find('foregroundColor=',startIdx)
	posEnd=data.find('"',posForeColor+22)
	color = data[posForeColor+17:posEnd]
	return color, posForeColor, posEnd

def getAlign(data,startIdx, horiz=True):
	if horiz: posAlign = data.find('halign=',startIdx)
	else: posAlign = data.find('align=',startIdx)
	posEnd=data.find('"',posAlign+10)
	align = data[posAlign+8:posEnd]
	return align, posAlign, posEnd


def checkVTi():
	isVTi = True
	if os.path.exists('/etc/image-version'):
		fm = open('/etc/image-version','r')
		lines = fm.read()
		isVTi = 'vti' in lines.lower()	
		fm.close()
	return(isVTi)	

def readRcButtonTexts(isVTi):
	try:
		f=open(os.path.join(yampDir, 'DreamVuRcText.txt'), 'r')
		lines=f.readlines()
		f.close()

		txtInfo=txtSaver=txtBouquet=''
		if isVTi: idx=2
		else: idx=1
		txtInfo = lines[2].split('\t')[idx].strip()
		txtSaver= lines[3].split('\t')[idx].strip()
		txtBouquet = lines[4].split('\t')[idx].strip()
	except:
		pass
	return(txtInfo,txtSaver,txtBouquet)
