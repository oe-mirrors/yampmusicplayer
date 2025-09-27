#######################################################################
#  Yamp File Functions
#    Version 3.3.1 2024-01-02
#  Coded by AlfredENeumann (c) 2022-2024
#  Last change: 2025-09-26 by Mr.Servo @OpenATV
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

from os.path import join, exists
from Components.config import config
from .YampGlobals import yampDir
from .myLogger import LOG

OFFSETCOMMENT = 1700


def writeLcdRunning():
	try:
		xmlfile = join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampLcdRunning.xml")
		if not exists(xmlfile):
			LOG('YampFileFunctions: writeLcdRunning: File not found: "%s"' % xmlfile, 'err')
			return
		with open(xmlfile, 'r') as f:
			data = f.read()
		LcdWidth, LcdHeight, posLcdsize, lastPos = getSize(data, OFFSETCOMMENT)
		positionX, positionY, posPosition, lastPos = getPosition(data, lastPos)
		WidthRText, HeightRText, posSizeRText, lastPos = getSize(data, lastPos)
		fontSize, posFont, lastPos = getFont(data, lastPos)
		newLcdWidth = config.plugins.yampmusicplayer.lcdSize.value.split('x')[0]
		newLcdHeight = config.plugins.yampmusicplayer.lcdSize.value.split('x')[1]
		rep = data[posLcdsize:].replace(LcdWidth + ',', newLcdWidth + ',', 1)
		rep = rep.replace(',' + LcdHeight, ',' + newLcdHeight, 1)
		data = data[:posLcdsize] + rep
		posTop = posPosition + data[posPosition:].find(',') + 1
		rep = data[posTop:]
		rep = rep.replace(WidthRText + ',', newLcdWidth + ',', 1)
		rep = rep.replace(',' + HeightRText, ',' + newLcdHeight, 1)
		data = data[:posTop] + rep
		rep = data[posFont:].replace(';' + fontSize, ';' + str(config.plugins.yampmusicplayer.lcdRunningFontSize.value), 1)
		data = data[:posFont] + rep
		with open(join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampLcdRunning.xml"), 'w') as f:
			f.write(data)
		return 0
	except Exception:
		return -1


def writeLcd():
	try:
		xmlfile = join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampLCD.xml")
		if not exists(xmlfile):
			LOG('YampFileFunctions: writeLcd: File not found: "%s"' % xmlfile, 'err')
			return
		with open(xmlfile, 'r') as f:
			data = f.read()
		LcdWidth, LcdHeight, posLcdsize, lastPos = getSize(data, OFFSETCOMMENT)
		positionXText1, positionYText1, posPositionText1, lastPos = getPosition(data, lastPos)
		WidthText1, HeightText1, posSizeText1, lastPos = getSize(data, lastPos)
		fontSizeText1, posFontText1, lastPos = getFont(data, lastPos)
		alignText1, posalignText1, lastPos = getAlign(data, lastPos)
		colorText1, posColorText1, lastPos = getForeColor(data, lastPos)
		positionXText2, positionYText2, posPositionText2, lastPos = getPosition(data, lastPos)
		WidthText2, HeightText2, posSizeText2, lastPos = getSize(data, lastPos)
		fontSizeText2, posFontText2, lastPos = getFont(data, lastPos)
		alignText2, posalignText2, lastPos = getAlign(data, lastPos)
		colorText2, posColorText2, lastPos = getForeColor(data, lastPos)
		positionXText3, positionYText3, posPositionText3, lastPos = getPosition(data, lastPos)
		WidthText3, HeightText3, posSizeText3, lastPos = getSize(data, lastPos)
		fontSizeText3, posFontText3, lastPos = getFont(data, lastPos)
		alignText3, posalignText3, lastPos = getAlign(data, lastPos)
		colorText3, posColorText3, lastPos = getForeColor(data, lastPos)
		positionXCover, positionYCover, posPositionCover, lastPos = getPosition(data, lastPos)
		WidthCover, HeightCover, posSizeCover, lastPos = getSize(data, lastPos)
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
			newTextHeight1 = (int(newLcdHeight) - 2 * textMinTop)
			newTextHeight2 = newTextHeight3 = 0
			newText2PosY = newText3PosY = str(int(newLcdHeight) - 1)
		else:
			newTextHeight1 = newTextHeight2 = newTextHeight3 = (int(newLcdHeight) - 2 * textMinTop) / 3
			newText2PosY = str(newTextHeight1 + textMinTop)
			newText3PosY = str(newTextHeight1 * 2 + textMinTop)
		newTextHeight1 = str(newTextHeight1)
		newTextHeight2 = str(newTextHeight2)
		newTextHeight3 = str(newTextHeight3)
		newFontSize = str(config.plugins.yampmusicplayer.lcdFontSize.value)
		newColorText1 = config.plugins.yampmusicplayer.lcdColorLine1.value
		newColorText2 = config.plugins.yampmusicplayer.lcdColorLine2.value
		newColorText3 = config.plugins.yampmusicplayer.lcdColorLine3.value
		rep = data[posLcdsize:].replace(LcdWidth + ',', newLcdWidth + ',', 1)
		rep = rep.replace(',' + LcdHeight, ',' + newLcdHeight, 1)
		data = data[:posLcdsize] + rep
		rep = data[posPositionText1:].replace(positionXText1 + ',', newTextPosX + ',', 1)
		rep = rep.replace(',' + positionYText1, ',' + str(textMinTop), 1)
		data = data[:posPositionText1] + rep
		rep = data[posSizeText1:].replace(WidthText1 + ',', newTextWidth + ',', 1)
		rep = rep.replace(',' + HeightText1, ',' + newTextHeight1, 1)
		rep = rep.replace(';' + fontSizeText1, ';' + newFontSize, 1)
		rep = rep.replace(alignText1, newTextAlign, 1)
		rep = rep.replace(colorText1, newColorText1, 1)
		data = data[:posSizeText1] + rep
		rep = data[posPositionText2:].replace(positionXText2 + ',', newTextPosX + ',', 1)
		rep = rep.replace(',' + positionYText2, ',' + newText2PosY, 1)
		data = data[:posPositionText2] + rep
		rep = data[posSizeText2:].replace(WidthText2 + ',', newTextWidth + ',', 1)
		rep = rep.replace(',' + HeightText2, ',' + newTextHeight2, 1)
		rep = rep.replace(';' + fontSizeText2, ';' + newFontSize, 1)
		rep = rep.replace(alignText2, newTextAlign, 1)
		rep = rep.replace(colorText2, newColorText2, 1)
		data = data[:posSizeText2] + rep
		rep = data[posPositionText3:].replace(positionXText3 + ',', newTextPosX + ',', 1)
		rep = rep.replace(',' + positionYText3, ',' + newText3PosY, 1)
		data = data[:posPositionText3] + rep
		rep = data[posSizeText3:].replace(WidthText3 + ',', newTextWidth + ',', 1)
		rep = rep.replace(',' + HeightText3, ',' + newTextHeight3, 1)
		rep = rep.replace(';' + fontSizeText3, ';' + newFontSize, 1)
		rep = rep.replace(alignText3, newTextAlign, 1)
		rep = rep.replace(colorText3, newColorText3, 1)
		data = data[:posSizeText3] + rep
		rep = data[posPositionCover:].replace(positionXCover + ',', newCoverPosX + ',', 1)
		rep = rep.replace(',' + positionYCover, ',' + newCoverPosY, 1)
		data = data[:posPositionCover] + rep
		rep = data[posSizeCover:].replace(WidthCover + ',', newCoverSize + ',', 1)
		rep = rep.replace(',' + HeightCover, ',' + newCoverSize, 1)
		data = data[:posSizeCover] + rep
		with open(join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampLCD.xml"), 'w') as f:
			f.write(data)
		return 0
	except Exception as e:
		print(f'=== writeLcd: EXCEPT writeLcd: {e}')
		return -1


def writeVTIRunningRenderer():
	try:
		xmlfile = join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampLcdRunning.xml")
		if not exists(xmlfile):
			LOG('YampFileFunctions: writeVTIRunningRenderer: File not found: "%s"' % xmlfile, 'err')
			return
		with open(xmlfile, 'r') as f:
			data = f.read()
		posRender = data.find('render=', OFFSETCOMMENT)
		rep = data[posRender:].replace('="VRunningText"', '="RunningText"', 1)
		data = data[:posRender] + rep
		with open(join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampLcdRunning.xml"), 'w') as f:
			f.write(data)
		return 0
	except OSError:
		return -1


def readCustomCoverSize():
	try:
		xmlfile = join(yampDir, "skins", config.plugins.yampmusicplayer.yampSkin.value, "YampLCD.xml")
		if not exists(xmlfile):
			LOG('YampFileFunctions: readCustomCoverSize: File not found: "%s"' % xmlfile, 'err')
			return
		with open(xmlfile, 'r') as f:
			data = f.read()
		posCover = data.find('coverArt', OFFSETCOMMENT)
		WidthCover, HeightCover, posSizeCover, lastPos = getSize(data, posCover)
		return (int(WidthCover))
	except OSError:
		return -1


def getPosition(data, startIdx):
	posPosition = data.find('position=', startIdx)
	posComma = data.find(',', posPosition)
	posEnd = data.find('"', posComma)
	positionX = data[posPosition + 10:posComma]
	positionY = data[posComma + 1:posEnd]
	return positionX, positionY, posPosition, posEnd


def getSize(data, startIdx):
	posSize = data.find('size=', startIdx)
	posComma = data.find(',', posSize)
	posEnd = data.find('"', posComma)
	Width = data[posSize + 6:posComma]
	Height = data[posComma + 1:posEnd]
	return Width, Height, posSize, posEnd


def getFont(data, startIdx):
	posFont = data.find('font=', startIdx)
	posSemik = data.find(';', posFont)
	posEnd = data.find('"', posSemik)
	font = data[posFont + 6:posSemik]
	fontSize = data[posSemik + 1:posEnd]
	return fontSize, posFont, posEnd


def getForeColor(data, startIdx):
	posForeColor = data.find('foregroundColor=', startIdx)
	posEnd = data.find('"', posForeColor + 22)
	color = data[posForeColor + 17:posEnd]
	return color, posForeColor, posEnd


def getAlign(data, startIdx, horiz=True):
	if horiz:
		posAlign = data.find('halign=', startIdx)
	else:
		posAlign = data.find('align=', startIdx)
	posEnd = data.find('"', posAlign + 10)
	align = data[posAlign + 8:posEnd]
	return align, posAlign, posEnd


def readRcButtonTexts():
	return ("EPG(L)", "VIDEO", "CHANNEL + -")  # textInfo INFO(L) EPG(L), textSaver PVR VIDEO, textBouquet BOUQET+- CHANNEL+-
