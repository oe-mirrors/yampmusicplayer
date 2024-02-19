#######################################################################
#
#    YAMP - Yet Another Music Player
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
#    Thanks to the authors of Merlin Music Player and OpenPli Media
#    Player for ideas and code snippets
#
#######################################################################

from Components.config import config, ConfigSubsection, ConfigYesNo
from enigma import getDesktop
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox

from __init__ import _

from YampGlobals import *
import os
import Yamp

pname = _("YAMP Music Player")
pdesc = _("Music Player with Artist-Art Background")


def main(session, **kwargs):
	display_width = getDesktop(0).size().width()
	if display_width < 1280: # minimum 1280x720 skin
		session.open(MessageBox, _("This plugin needs a HD or FHD skin"), type = MessageBox.TYPE_ERROR,timeout = 10 )
		return
	MOUNTPOINT = "/media"

	try:
		mountpoints = os.listdir(MOUNTPOINT)
		msgtext = _("Cannot open mountpoint %s") %(MOUNTPOINT)
	except:
		session.open(MessageBox, msgtext, type = MessageBox.TYPE_ERROR,timeout = 15)
		return

	reload(Yamp)
	try:
		session.openWithCallback(closePlayer, Yamp.YampScreenV33)
	except:
		import traceback
		traceback.print_exc()
		
def closePlayer(session, service=None):
	if service:
		session.nav.playService(service)

def menu(menuid, **kwargs):
	if menuid == "mainmenu":
		return [(pname, main, "yamp_music_player", 47)]
	return []

	
def Plugins(**kwargs):
	list = [PluginDescriptor(name=pname, description=pdesc, where = [PluginDescriptor.WHERE_PLUGINMENU], icon = "yamp.png", needsRestart = True, fnc=main)]
	if config.plugins.yampmusicplayer.yampInExtendedPluginlist.value:
		list.append(PluginDescriptor(name=pname, description=pdesc, where = [PluginDescriptor.WHERE_EXTENSIONSMENU], needsRestart = True, fnc=main))
	if config.plugins.yampmusicplayer.yampInMainMenu.value:
		list.append(PluginDescriptor(name=pname, description=pdesc, where = [PluginDescriptor.WHERE_MENU], needsRestart = True, fnc=menu))
	return list
