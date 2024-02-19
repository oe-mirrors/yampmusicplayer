#######################################################################
#
#    YAMP - Yet Another Music Player
#    Version 3.1.1 2023-07-25
#    Coded by JohnHenry (c)2013
#    Extended by AlfredENeumann (c)2016-2023
#    Support: www.vuplus-support.org
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

#from .YampGlobals import *
import os

from ServiceReference import ServiceReference
from enigma import eServiceReference

from .myLogger import LOG


class YampParsers:
	MOUNTPOINT = "/media"
	OK = 0
	ERROR = 3
	REMOTE_PROTOS = ["http", "https", "udp", "rtsp", "rtp", "mmp"]

	def __init__(self):
		self.list = []
		self.mountpoints = os.listdir(self.MOUNTPOINT)

	def clear(self):
		del self.list[:]

	def addService(self, service):
		self.list.append(service)

	def getRef(self, filename, entry):
		for proto in self.REMOTE_PROTOS:
			if entry.startswith(proto):
				return None  # no support for streams!
		if entry[0] == "/":
			path = entry
		else:
			path = os.path.join(os.path.dirname(filename), entry)
		if not os.path.exists(path):
			path = self.tryMountpoints(path)
		return path and ServiceReference(eServiceReference(4097, 0, path))

	def tryMountpoints(self, abspath):
		newpath = None
		for p in self.mountpoints:
			x = os.path.join(self.MOUNTPOINT, p, abspath[1:])  # ignore leading '/'!
			if os.path.exists(x):
				newpath = x
				break
		return newpath


class YampParserE2pls(YampParsers):
	def __init__(self):
		YampParsers.__init__(self)

	def open(self, filename):
		self.clear()
		try:
			file = open(filename, "r")
		except OSError:
			return None
		while True:
			entry = file.readline().strip()
			if entry == "":
				break
			self.addService(ServiceReference(entry))
		file.close()
		return self.list

	def save(self, filename=None):
		file = open(filename, "w")
		for x in self.list:
			file.write(str(x) + "\n")
		file.close()
		return self.OK


class YampParserM3u(YampParsers):
	def __init__(self):
		YampParsers.__init__(self)

	def open(self, filename):
		self.clear()
		try:
			file = open(filename, "r")
		except OSError:
			return None
		self.displayname = None
		while True:
			entry = file.readline()
			if entry == "":
				break
			entry = entry.strip().replace('\\', '/')
			if entry.startswith("#EXTINF:"):
				extinf = entry.split(',', 1)
				if len(extinf) > 1:
					self.displayname = extinf[1]
			elif entry != "" and not entry.startswith("#"):
				sref = YampParsers.getRef(self, filename, entry)
				if sref:
					if self.displayname:
						sref.ref.setName(self.displayname)
					self.addService(sref)
				self.displayname = None
		file.close()
		return self.list

	def save(self, filename=None):
		import re
		file = open(filename, "w")
		file.write('#EXTM3U\n')
		for x in self.list:
			try:
				x = re.sub(r'^4097:', '', str(x))  # remove leading 4097:
				x = re.sub(r'^([0-9]+:)+', '', x)  # remove all leading xyz:  xyz = 1 or more numbers
				pos = x.rfind('-')
				title = x[pos + 1:].strip()
				x = x[:pos].strip()
				pos = x.rfind(':')
				artist = x[pos + 1:].strip()
				x = x[:pos].strip()
				lenght = -1
				file.write('#EXTINF:' + str(lenght) + ',' + artist + ' - ' + title + '\n')
			except Exception as e:
				LOG('YampParserM3u: save: EXCEPT: %s' % (str(e)), 'err')
			file.write(str(x) + "\n")
		file.close()
		return self.OK


class YampParserPls(YampParsers):
	def __init__(self):
		YampParsers.__init__(self)

	def open(self, filename):
		self.clear()
		try:
			file = open(filename, "r")
		except OSError:
			return None
		entry = file.readline().strip().replace('\\', '/')
		if entry == "[playlist]":  # extended pls
			while True:
				entry = file.readline()
				if entry == "":
					break
				entry = entry.strip().replace('\\', '/')
				if entry.startswith("File"):
					pos = entry.find('=') + 1
					newentry = entry[pos:]
					sref = YampParsers.getRef(self, filename, newentry)
					if sref:
						self.addService(sref)
				if entry.startswith("Title"):
					pos = entry.find('=') + 1
					self.displayname = entry[pos:]
					if sref:  # last file entry was ok??
						self.list[-1].ref.setName(self.displayname)
		else:
			playlist = YampParserM3u()
			file.close()
			return playlist.open(filename)
		file.close()
		return self.list

	def save(self, filename=None):
		return self.ERROR
