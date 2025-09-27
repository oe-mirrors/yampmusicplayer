#######################################################################
#
#   Yamp LogFile  2021-02-21
#	last change: 2025-09-19 by Mr.Servo @OpenATV
#
#   Coded by AlfredENeumann (c) 2016-2024
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

from Components.config import config
from datetime import datetime


def LOG(s, logtype):
	if logtype == "all":
		if config.plugins.yampmusicplayer.yampDebugMode.value == "all":
			writeLog(s)
	elif logtype == "err":
		if config.plugins.yampmusicplayer.yampDebugMode.value != "off":
			writeLog(s)
	elif logtype == "spe":
		if config.plugins.yampmusicplayer.yampDebugMode.value == "special":
			writeLog(s)
	elif logtype == "spe2":
		if config.plugins.yampmusicplayer.yampDebugMode.value == "special2":
			writeLog(s)
	elif logtype == "spe3":
		if config.plugins.yampmusicplayer.yampDebugMode.value == "special3":
			writeLog(s)
	elif logtype == "spe4":
		if config.plugins.yampmusicplayer.yampDebugMode.value == "special4":
			writeLog(s)


def writeLog(text):
	try:
		t = timestamp()
		with open(config.plugins.yampmusicplayer.debugFile.value, 'a') as f:
			f.write('%s' '%s\n' % (t, text))
	except OSError:
		pass


def timestamp():
	return datetime.now().strftime("%Y.%m.%d-%H:%M:%S.%f")
