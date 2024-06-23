# -*- coding: utf-8 -*-
#######################################################################
#
#    YAMP - Yet Another Music Player - Globals
#    Version 3.3.2 2024-02-28
#    Coded by AlfredENeumann (c)2016-2024
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


yampDir = "/usr/lib/enigma2/python/Plugins/Extensions/YampMusicPlayer/"
audioExtensions = (".mp2", ".mp3", ".wav", ".ogg", ".flac", ".m4a", ".wma")

yampTitlecaseNochange=[]
minList=[]
secList=[]

FANARTTVAPPAPIFILE = yampDir + '.YampFanarttvAppApi.key'
FANARTTVPERSAPIFILE = yampDir + 'YampFanarttvPersonalApi.key'

#
# Constants
#

STATE_PLAY = 0
STATE_PAUSE = 1
STATE_STOP = 2
STATE_NONE = 5

MENULIST = 0
ARTISTLIST = 1
ALBUMLIST = 2
GENRELIST = 3
DATELIST = 4
PLAYLISTLIST = 5
ARTISTALBUMLIST = 6
GENREALBUMLIST = 7
DATEALBUMLIST = 8
SEARCHPLAYLISTLIST = 9
SEARCHARTISTLIST = 10
SEARCHALBUMLIST = 11
SEARCHGENRELIST = 12
SEARCHDATELIST = 13
TITLELIST = 20
ARTISTTITLELIST = 21
ALBUMTITLELIST = 22
GENRETITLELIST = 23
DATETITLELIST = 24
SEARCHTITLELIST = 25
SEARCHFILELIST = 26
SEARCHARTISTTITLELIST = 27
SEARCHALBUMTITLELIST = 28

THREAD_WORKING = 1
THREAD_FINISHED = 2

COVER_EXTENSIONS = ['.jpg', '.jpeg','.png', '.gif']
COVER_MINSIZE = 500

#Cover Search
COVERS_NO = 10
COVERS_MP3 = 1
COVERS_FLAC = 2
COVERS_DIRANY = 3
COVERS_ALB = 4
COVERS_GOOGLE = 5
COVERS_MP4 = 6
COVERS_M4A = 7
COVERS_TITLE = 8
COVERS_OGG = 9

COVER_MAXINDEX = 10

#Lyrics_Search
LYRICSS_NO = 11
LYRICSS_MP3 = 1
LYRICSS_FLAC = 2
LYRICSS_FILE = 3
LYRICSS_CHARTL = 4
LYRICSS_GENIUS = 5
LYRICSS_MP4 = 6
LYRICSS_M4A = 7
LYRICSS_OGG = 8
LYRICSS_LYRDIR = 9
LYRICSS_AZ = 10

DOWNLOADBASETIME = 125
FANARTDLTIMEMUL = 48
FANARTDLTIMEPERSONALMUL = 4


EXTENSIONS = {
		"m4a": "music_m4a",
		"mp2": "music_mp2",
		"mp3": "music_mp3",
		"wav": "music_wav",
		"wma": "music_wma",
		"ogg": "music_ogg",
		"flac": "music_flac",
		"jpg": "picture_jpg",
		"jpeg": "picture_jpeg",
		"png": "picture_png",
		"bmp": "picture_bmp",
		"ts": "movie_ts",
		"avi": "movie_avi",
		"divx": "movie_divx",
		"m4v": "movie_m4v",
		"mpg": "movie_mpg",
		"mpeg": "movie_mpeg",
		"mkv": "movie_mkv",
		"mp4": "movie_mp4",
		"mov": "movie_mov",
		"m2ts": "movie_m2ts",
		"flv": "movie_flv",
		"wmv": "movie_mwv",
		"e2pls": "playl_e2pls",
		"m3u": "playl_m3u"
	}


import os
import re
from enigma import eTimer

from Components.ActionMap import ActionMap, HelpableActionMap
from Components.config import config, ConfigSubsection, ConfigDirectory, ConfigYesNo, ConfigSelection, ConfigInteger, ConfigText, ConfigBoolean, getConfigListEntry, configfile 
from Components.Label import Label
from Components.Sources.StaticText import StaticText

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

# own modules
from myLogger import LOG

