#######################################################################
#
# Yamp Lyrics Functions
# Version 3.3.2 2024-02-27
# Coded by AlfredENeumann (c) 2021-2024
# Last change: 2025-09-27 by Mr.Servo @OpenATV
# Support: www.vuplus-support.org, board.newnigma2.to
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
#######################################################################

from os.path import join, exists, splitext, dirname
from re import findall, sub
from mutagen import File
from mutagen.flac import FLAC
from mutagen.id3 import ID3
from Components.config import config
from .YampGlobals import LYRICSS_NO, LYRICSS_MP3, LYRICSS_MP4, LYRICSS_M4A, LYRICSS_FLAC
from .YampCommonFunctions import readID3Infos
from .myLogger import LOG


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
	if exists(lyricsFileNameLong):
		with open(lyricsFileNameLong, "r") as file:
			lyrics = file.read()
		lyricsFileActive = lyricsFileNameLong
	else:  # first fallback
		if exists(lyricsFileName):
			with open(lyricsFileName, "r") as file:
				lyrics = file.read()
			lyricsFileActive = lyricsFileName
		else:  # and second fallback
			if exists(lyricsFileNameLrcLong):
				with open(lyricsFileNameLrcLong, "r") as file:
					lyrics = file.read()
				lyricsFileActive = lyricsFileNameLrcLong
			else:  # final fallback
				if exists(lyricsFileNameLrc):
					with open(lyricsFileNameLrc, "r") as file:
						lyrics = file.read()
					lyricsFileActive = lyricsFileNameLrc
				else:
					LOG('YampLyricsFunctions: searchLyricsfromFiles: None of the files found: "%s", "%s", "%s", "%s"' % (lyricsFileNameLong, lyricsFileName, lyricsFileNameLrcLong, lyricsFileNameLrc), 'err')
	if len(lyrics):
		foundPrio = prio
	return lyrics, lyricsFileActive, foundPrio

# get Lyrics from ID3 (mp3, flac, m4a, mp4)


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
		# Lyrics search mp3
		try:
			audio = ID3(songFilename)
		except Exception:
			audio = None
		if audio:
			for frame in audio.values():
				if frame.FrameID == "USLT":
					lyrics = frame.text.replace("\r\n", "\n").replace("\r", "\n")
					pixNumLyrics = LYRICSS_MP3
					foundPrio = prio
					break
			return lyrics, pixNumLyrics, foundPrio
	elif songFilename.lower().endswith(".m4a") or songFilename.lower().endswith(".mp4"):
		f = {}
		try:
			f = File(songFilename)
		except Exception as e:
			LOG('YampLyricsScreen:searchId3_m4a: mutagen: EXCEPT: ' + str(e), 'err')
		try:
			for key in f.keys():
				if key.endswith('lyr'):
					lyrics = f[key][0].replace("\r\n", "\n").replace("\r", "\n")
					if songFilename.lower().endswith(".mp4"):
						pixNumLyrics = LYRICSS_MP4
					else:
						pixNumLyrics = LYRICSS_M4A
					foundPrio = prio
		except Exception as e:
			LOG('YampLyricsScreen:searchId3mp4m4a: key: EXCEPT: ' + str(e), 'err')
		return lyrics, pixNumLyrics, foundPrio
	elif songFilename.lower().endswith(".flac"):
		# Lyrics search flac
		try:
			flacInfo = FLAC(songFilename)
		except Exception:
			flacInfo = None
		try:
			if flacInfo:
				text = ""
				if 'lyrics' in flacInfo:
					text = flacInfo['lyrics']
					lyrics = text[0]
					lyrics = lyrics.replace("\r\n", "\n").replace("\r", "\n")
					pixNumLyrics = LYRICSS_FLAC
					foundPrio = prio
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
			timeStamp = findall(r'\[\d+:\d+.?\d*\]', line)
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
			if posMsec90 > 0 and posMsec90 < tStampMin or tStampMin == -1:
				tStampMin = posMsec90
	except Exception as e:
		LOG('YampLyricsFunctions: textToList: timeStamp: EXCEPT: ' + str(e), 'err')
	try:
		textLines = sub(r'\[\d+:\d+.?\d*\]', '', text)  # remove leading timecode [00:00.00]
		textLines = textLines.split('\n')
	except Exception as e:
		LOG('YampLyricsFunctions: textToList: sub: EXCEPT: ' + str(e), 'err')
	return tStamp, tStampmsecs90, textLines, tStampMin


def getLyricsFileNames(songFilepathExt):
	title, album, genre, artist, albumartist, date, length, tracknr, strBitrate = readID3Infos(songFilepathExt)
	songFilepath = splitext(songFilepathExt)[0]
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
		lyricsFileName = join(config.plugins.yampmusicplayer.lyricsPath.value, lyricsFileName)
		lyricsFileNameLong = join(config.plugins.yampmusicplayer.lyricsPath.value, lyricsFileNameLong)
		lyricsFileNameLrc = join(config.plugins.yampmusicplayer.lyricsPath.value, lyricsFileNameLrc)
		lyricsFileNameLrcLong = join(config.plugins.yampmusicplayer.lyricsPath.value, lyricsFileNameLrcLong)
	else:
		lyricsFileName = splitext(songFilepathExt)[0] + ".txt"
		lyricsFileNameLong = dirname(songFilepathExt) + '/' + lyricsFileNameLong
		lyricsFileNameLrc = splitext(songFilepathExt)[0] + ".lrc"
		lyricsFileNameLrcLong = dirname(songFilepathExt) + '/' + lyricsFileNameLrcLong
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
		text = sub(r'\[ar:.*\]', '', text)  # remove artist string [ar:xxx]
		text = sub(r'\[ti:.*\]', '', text)  # remove title string [ti:xxx]
		text = sub(r'\[offset:.*\]', '', text)  # remove offset string [ofset:xxx]
		text = sub(r'\[Offset:.*\]', '', text)  # remove offset string [ofset:xxx]
		text = sub(r'\[ap:.*\]', '', text)  # remove ap string [ap:xxx]
		text = sub(r'\[al:.*\]', '', text)  # remove al string [al:xxx]
		text = sub(r'\[by:.*\]', '', text)  # remove by string [by:xxx]
		text = sub(r'<!--.*-->', '', text)  # remove xml comment
		text = sub(r'<script.*/script>', '', text)  # remove xml script
		text = text.replace('</em>', '')  # remove xml em class end
		text = sub(r'<em class=.*>', '', text)  # remove xml em class
		text = text.strip()  # remove empty lines at beginning / end
	except Exception as e:
		LOG('YampLyricsFunctions: LyricsClean: text: EXCEPT: ' + str(e), 'err')
	return text
