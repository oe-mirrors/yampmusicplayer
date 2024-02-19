#######################################################################
#
#  Yamp Lyrics Functions
#  Version 3.3.1 2023-12-06
#  Coded by AlfredENeumann (c) 2021-2023
#  Support: www.vuplus-support.org, board.newnigma2.to
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

from .YampGlobals import *
import re
import os

import mutagen
from mutagen.flac import FLAC
from mutagen.id3 import ID3


from Components.config import config
from .myLogger import LOG

from .YampCommonFunctions import getEncodedString, readID3Infos


def searchLyricsfromFiles(songFilename, foundPrio):
	lyricsFileActive = lyrics = ''
	if config.plugins.yampmusicplayer.prioLyrics1.value == 'lyricsFile':
		prio = 1
	elif config.plugins.yampmusicplayer.prioLyrics2.value == 'lyricsFile':
		prio = 2
	elif config.plugins.yampmusicplayer.prioLyrics3.value == 'lyricsFile':
		prio = 3
	elif config.plugins.yampmusicplayer.prioLyrics4.value == 'lyricsFile':
		prio = 4
	else:
		return '', '', foundPrio

	if foundPrio < prio:
		return '', '', foundPrio  # already found with higher priority

	lyricsFileName, lyricsFileNameLong, lyricsFileNameLrc, lyricsFileNameLrcLong = getLyricsFileNames(songFilename)

	try:
		file = open(lyricsFileNameLong, "r")
		lyrics = file.read()
		file.close()
		lyricsFileActive = lyricsFileNameLong
	except:
		try:
			file = open(lyricsFileName, "r")
			lyrics = file.read()
			file.close()
			lyricsFileActive = lyricsFileName
		except:
			try:
				file = open(lyricsFileNameLrcLong, "r")
				lyrics = file.read()
				file.close()
				lyricsFileActive = lyricsFileNameLrcLong
			except:
				try:
					file = open(lyricsFileNameLrc, "r")
					lyrics = file.read()
					file.close()
					lyricsFileActive = lyricsFileNameLrc
				except:
					pass
	if len(lyrics):
		foundPrio = prio
	return lyrics, lyricsFileActive, foundPrio


#get Lyrics from ID3 (mp3, flac, m4a, mp4)

def getLyricsID3(songFilename, foundPrio):
	if config.plugins.yampmusicplayer.prioLyrics1.value == 'lyricsID3':
		prio = 1
	elif config.plugins.yampmusicplayer.prioLyrics2.value == 'lyricsID3':
		prio = 2
	elif config.plugins.yampmusicplayer.prioLyrics3.value == 'lyricsID3':
		prio = 3
	elif config.plugins.yampmusicplayer.prioLyrics4.value == 'lyricsID3':
		prio = 4
	else:
		return '', LYRICSS_NO, foundPrio

	lyrics = ''
	pixNumLyrics = LYRICSS_NO

	if foundPrio < prio:
		return '', LYRICSS_NO, foundPrio  # already found with higher priority

	if songFilename.lower().endswith(".mp3"):
		#Lyrics search mp3
		try:
			audio = ID3(songFilename)
		except:
			audio = None
		if audio:
			for frame in audio.values():
				if frame.FrameID == "USLT":
					try:
						lyrics = getEncodedString(frame.text).replace("\r\n", "\n").replace("\r", "\n")
					except Exception as e:
						LOG('\nYampLyricsFunctions:getLyricsID3mp3: lyrics getEncodedString: EXCEPT: ' + str(e), 'err')
					pixNumLyrics = LYRICSS_MP3
					foundPrio = prio
					break

			return lyrics, pixNumLyrics, foundPrio

	elif songFilename.lower().endswith(".m4a") or songFilename.lower().endswith(".mp4"):
		try:
			f = mutagen.File(songFilename)
		except Exception as e:
			LOG('\nYampLyricsScreen:searchId3_m4a: mutagen: EXCEPT: ' + str(e), 'err')
		try:
			for key in f.keys():
				if key.endswith('lyr'):
					lyrics = getEncodedString(f[key][0]).replace("\r\n", "\n").replace("\r", "\n")
					if songFilename.lower().endswith(".mp4"):
						pixNumLyrics = LYRICSS_MP4
					else:
						pixNumLyrics = LYRICSS_M4A
					foundPrio = prio
		except Exception as e:
			LOG('\nYampLyricsScreen:searchId3mp4m4a: key: EXCEPT: ' + str(e), 'err')
		return lyrics, pixNumLyrics, foundPrio

	elif songFilename.lower().endswith(".flac"):
		#Lyrics search flac
		try:
			flacInfo = FLAC(songFilename)
		except:
			flacInfo = None
		try:
			if flacInfo:
				if 'lyrics' not in flacInfo:
					pass
				else:
					try:
						text = flacInfo['lyrics']
					except Exception as e:
						LOG('YampLyricsFunctions: getLyricsID3: FLAC: text: EXCEPT: ' + str(e), 'err')
					try:
						lyrics = text[0]
					except Exception as e:
						LOG('YampLyricsFunctions: getLyricsID3: FLAC: lyrics 1: EXCEPT: ' + str(e), 'err')
					try:
						lyrics = getEncodedString(lyrics).replace("\r\n", "\n").replace("\r", "\n")
					except Exception as e:
						LOG('YampLyricsFunctions: getLyricsID3: FLAC: lyrics encode: EXCEPT: ' + str(e), 'err')
					try:
						pixNumLyrics = LYRICSS_FLAC
						foundPrio = prio
					except Exception as e:
						LOG('YampLyricsFunctions: getLyricsID3: FLAC: lyrics 5: EXCEPT: ' + str(e), 'err')
		except Exception as e:
			LOG('YampLyricsFunctions: getLyricsID3: FLAC: FlacInfo EXCEPT: ' + str(e), 'err')
	return lyrics, pixNumLyrics, foundPrio


def textToList(text):
	textLines = []
	tStamp = []
	tStampmsecs90 = []
	tStampMin = -1
	lyrics = ''
	try:
		textLines = text.split('\n')
	except Exception as e:
		LOG('YampLyricsFunctions: textToList: text.split: EXCEPT: ' + str(e), 'err')
	try:
		for line in textLines:
			tx = ''
			timeStamp = re.findall(r'\[[0-9]+:[0-9]+.?[0-9]*\]', line)
			if len(timeStamp):
				tx = timeStamp[len(timeStamp) - 1]
			else:
				tx = '[00:00.00]'
			if len(tx) == 7 and tx[6] == ']':  # assuming milliseconds missing: [xx:yy]
				tx = tx[:6] + '.00]'
			tStamp.append(tx)
			minutes = int(tx[1:3])
			seconds = float(tx[4:9])
			posMsec90 = int(((minutes * 60.0 + seconds) * 1000.0) * 90.0)
			tStampmsecs90.append(posMsec90)
			if posMsec90 > 0:
				if posMsec90 < tStampMin or tStampMin == -1:
					tStampMin = posMsec90
	except Exception as e:
		LOG('YampLyricsFunctions: textToList: timeStamp: EXCEPT: ' + str(e), 'err')
	try:
		textLines = re.sub(r'\[[0-9]+:[0-9]+.?[0-9]*\]', '', text)  # remove leading timecode [00:00.00]
		textLines = textLines.split('\n')
	except Exception as e:
		LOG('YampLyricsFunctions: textToList: re.sub: EXCEPT: ' + str(e), 'err')
	return tStamp, tStampmsecs90, textLines, tStampMin


def getLyricsFileNames(songFilepathExt):

	title, album, genre, artist, date, length, tracknr, strBitrate = readID3Infos(songFilepathExt)

	songFilepath = os.path.splitext(songFilepathExt)[0]
	songFilepathSplit = songFilepath.split('/')
	titleFromFileName = songFilepathSplit[-1].replace('/', '_')

	artist = artist.replace('/', '_').upper()
	artist = artist.replace(':', '_').upper()
	album = album.replace('/', '_').upper()
	album = album.replace(':', '_').upper()

	lyricsFileName = titleFromFileName + '.txt'
	lyricsFileNameLrc = titleFromFileName + '.lrc'
	lyricsFileNameLong = artist + ' - ' + album + ' - ' + titleFromFileName + '.txt'
	lyricsFileNameLrcLong = artist + ' - ' + album + ' - ' + titleFromFileName + '.lrc'

	if config.plugins.yampmusicplayer.useSingleLyricsPath.value:
		lyricsFileName = os.path.join(config.plugins.yampmusicplayer.lyricsPath.value, lyricsFileName)
		lyricsFileNameLong = os.path.join(config.plugins.yampmusicplayer.lyricsPath.value, lyricsFileNameLong)
		lyricsFileNameLrc = os.path.join(config.plugins.yampmusicplayer.lyricsPath.value, lyricsFileNameLrc)
		lyricsFileNameLrcLong = os.path.join(config.plugins.yampmusicplayer.lyricsPath.value, lyricsFileNameLrcLong)
	else:
		lyricsFileName = os.path.splitext(songFilepathExt)[0] + ".txt"
		lyricsFileNameLong = os.path.dirname(songFilepathExt) + '/' + lyricsFileNameLong
		lyricsFileNameLrc = os.path.splitext(songFilepathExt)[0] + ".lrc"
		lyricsFileNameLrcLong = os.path.dirname(songFilepathExt) + '/' + lyricsFileNameLrcLong
	return (lyricsFileName, lyricsFileNameLong, lyricsFileNameLrc, lyricsFileNameLrcLong)


def delLyricsLine(idx, tiStampMsec90, tiStamp, txtLines):
	try:
		tiStampMsec90.pop(idx)
		tiStamp.pop(idx)
		txtLines.pop(idx)
	except Exception as e:
		LOG('YampLyricsFunctions: delLyricsLine: EXCEPT: ' + str(e), 'err')


def addTimeOffset(offsetMsec, tiStampMsec90, tiStamp):
	try:
		offsetMsec90 = offsetMsec * 90

		for idx in range(len(tiStampMsec90)):
			if tiStampMsec90[idx] > 0:
				tiStampMsec90[idx] = tiStampMsec90[idx] + offsetMsec90
				if tiStampMsec90[idx] < 0:
					tiStampMsec90[idx] = 90

				milliseconds = (tiStampMsec90[idx] / 90)
				if milliseconds < 0:
					milliseconds = 0
				minutes = milliseconds / 60000
				seconds = (milliseconds % 60000) / 1000.0

				tiStamp[idx] = '[%02d:%05.2f]' % (minutes, seconds)
	except Exception as e:
		LOG('YampLyricsFunctions: addTimeOffset: EXCEPT: ' + str(e), 'err')


def lyricsClean(text):
	try:
		text = re.sub(r'\[ar:.*\]', '', text)								#remove artist string [ar:xxx]
		text = re.sub(r'\[ti:.*\]', '', text)								#remove title string [ti:xxx]
		text = re.sub(r'\[offset:.*\]', '', text)							#remove offset string [ofset:xxx]
		text = re.sub(r'\[Offset:.*\]', '', text)							#remove offset string [ofset:xxx]
		text = re.sub(r'\[ap:.*\]', '', text)								#remove ap string [ap:xxx]
		text = re.sub(r'\[al:.*\]', '', text)								#remove al string [al:xxx]
		text = re.sub(r'\[by:.*\]', '', text)								#remove by string [by:xxx]
		text = re.sub(r'<!--.*-->', '', text)								#remove xml comment
		text = re.sub(r'<script.*/script>', '', text)						#remove xml script
		text = re.sub(r'</em>', '', text)									#remove xml em class end
		text = re.sub(r'<em class=.*>', '', text)							#remove xml em class

		text = text.strip()		#remove empty lines at beginning / end

	except Exception as e:
		LOG('YampLyricsFunctions: LyricsClean: text: EXCEPT: ' + str(e), 'err')
	return text
