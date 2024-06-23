# -*- coding: UTF-8 -*-
#######################################################################
#
#  Yamp Common Functions  
#  Version 3.3.2 2024-02-27
#  Coded by AlfredENeumann (c) 2021-2024
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

from YampGlobals import *

import mutagen
from mutagen.apev2 import APEv2
from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4
from mutagen.flac import Picture, FLAC, StreamInfo
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis

from datetime import timedelta as datetime_timedelta

from urllib import quote, quote_plus, unquote

from Components.config import config

from YampFileFunctions import *
from myLogger import LOG


def readID3Infos(path):

	audio = None
	title = ""
	genre = artist = album = date = albumartist = length = strBitrate = "n/a"
	tracknr = -1
	discNr = 0
	bitrate = 0.0
	if path.lower().endswith(".wma"):

		#TinyTag:{"album": "Rockferry", "albumartist": "Duffy", "artist": "Duffy", "audio_offset": null, "bitrate": 128.01599999999999, "channels": null, "comment": "", "composer": null, "disc": "1", "disc_total": "1", "duration": 222.07499999999999, "filesize": 3598326, "genre": "R&B/Soul", "samplerate": 44100, "title": "Mercy", "track": "07", "track_total": "10", "year": "2008"}
		tag = TinyTag.get(path)
		try:
			tracknr=int(tag.track)
			discNr = int(tag.disc)
			if discNr > 1: tracknr = discNr * 1000 + tracknr
		except: pass	
		if tag.duration>0:length=str(int(tag.duration/60))+':'+str(int(tag.duration%60))
		return str(tag.title), str(tag.album), str(tag.genre), str(tag.artist), str(tag.year), length, int(tag.track), str(tag.bitrate)
	
	elif path.lower().endswith(".mp3"):
		#{'musicbrainz_albumstatus': [u'official'], 'releasecountry': [u'NO'], 'date': [u'1996'], 'albumartist': [u'Toto'], 'musicbrainz_albumartistid': [u'aab5c954-cabe-432e-899e-1c4f99757327'], 'composer': [u'David Paich'], 'catalognumber': [u'485 122 2'], 'tracknumber': [u'5/15'], 'musicbrainz_trackid': [u'5bfbc273-73f4-42df-971b-8075b0414aae'], 'album': [u'Greatest Hits'], 'musicbrainz_artistid': [u'aab5c954-cabe-432e-899e-1c4f99757327'], 'title': [u'Rosanna'], 'media': [u'CD'], 'artistsort': [u'Toto'], 'acoustid_id': [u'41a25f1c-c3f2-4b15-8217-850ad13f1287'], 'musicbrainz_releasegroupid': [u'e1645597-bb35-3dc5-8a19-22510ef85971'], 'barcode': [u'5099748512222'], 'musicbrainz_albumtype': [u'album/compilation'], 'genre': [u'Rock'], 'isrc': [u'USSM18200245/USSM19801976'], 'discnumber': [u'1/1'], 'originaldate': [u'1996'], 'artist': [u'Toto'], 'musicbrainz_albumid': [u'd426efc6-00ce-48fa-9f26-b304938961c6'], 'organization': [u'Columbia'], 'musicbrainz_releasetrackid': [u'3b1f7257-9a10-3736-a251-db36f90ca085']}	
		try: audio = MP3(path, ID3 = EasyID3)
		except: audio = None

	elif path.lower().endswith(".flac"):
		#{'albumartistsort': [u'Various Artists'], 'disctotal': [u'4'], 'catalognumber': [u'88875085792'], 'releasecountry': [u'DE'], 'totaldiscs': [u'4'], 'date': [u'2015-09-25'], 'originalyear': [u'2015'], 'albumartist': [u'Various Artists'], 'musicbrainz_albumartistid': [u'89ad4ac3-39f7-470e-963a-56509c546377'], 'artists': [u'Patti Smith Group'], 'tracknumber': [u'1'], 'tracktotal': [u'19'], 'album': [u'Ultimate Rock'], 'asin': [u'B00TY9FGR0'], 'musicbrainz_artistid': [u'26638df8-ef34-40d1-8d93-616836b72878'], 'script': [u'Latn'], 'media': [u'CD'], 'musicbrainz_trackid': [u'f6655c59-8b0f-475e-8962-516ee897e7bb'], 'label': [u'Sony Music'], 'artistsort': [u'Smith, Patti, Group'], 'acoustid_id': [u'34a3aff6-61fb-463a-8db0-c01484a14665'], 'musicbrainz_releasegroupid': [u'591ee08d-4ad8-4445-a860-6deef34a5a7b'], 'compilation': [u'1'], 'barcode': [u'888750857927'], 'releasestatus': [u'official'], 'genre': [u'Rock'], 'isrc': [u'USAR17800008', u'USAR17800224', u'USAR18700224', u'USSM10002053'], 'discnumber': [u'3'], 'originaldate': [u'2015-09-25'], 'artist': [u'Patti Smith Group'], 'title': [u'Because the Night'], 'releasetype': [u'album', u'compilation'], 'musicbrainz_albumid': [u'5943b41a-c858-4d1c-93d6-35199b0efe4c'], 'totaltracks': [u'19'], 'musicbrainz_releasetrackid': [u'b9d87317-e868-49ac-8cab-9238210fee88']}
		try: 
			audio = FLAC(path)
			LOG('readID3Infos: FLAC', 'all')
			try:
				filesize = os.path.getsize(path)
				duration = audio.info.length
				if duration > 0: bitrate = filesize / duration * 8.0 / 1000.0
			except: LOG('readID3Infos: getFlacBitrate: EXCEPT', 'err')
		except: audio = None
 
	elif path.lower().endswith(".m4a") or path.lower().endswith(".mp4"):
		#{'album': [u'Zeig Dich!'], 'albumartistsort': [u'BRDigung'], 'musicbrainz_artistid': [u'6926d482-159b-40cd-9603-1d18bc28c734'], 'musicbrainz_albumstatus': [u'official'], 'title': [u'Nur einen Sommer lang'], 'artist': [u'BRDigung'], 'musicbrainz_trackid': [u'f26bf366-8288-42e1-bd98-3aa8120aa8b2'], 'genre': [u'Deutsch Rock'], 'albumartist': [u'BRDigung'], 'musicbrainz_albumartistid': [u'6926d482-159b-40cd-9603-1d18bc28c734'], 'artistsort': [u'BRDigung'], 'musicbrainz_albumtype': [u'album'], 'date': [u'2020-01-31'], 'tracknumber': [u'13/14'], 'discnumber': [u'1/1'], 'musicbrainz_albumid': [u'67660d8a-8a57-48b0-8550-b7b529b44920']}
		try: audio = EasyMP4(path)		#old method
		except: 
			audio = None
			try: audio = mutagen.File(path, easy=True)		#new method
			except: audio = None

	elif path.lower().endswith(".ogg"):
		#{'albumartistsort': [u'Anastacia'], 'lyrics': [u""], 'date': [u'2003'], 'albumartist': [u'Anastacia'], 'musicbrainz_albumartistid': [u'd3b2bec4-b70e-460e-b433-a865ceac2de8'], 'tracknumber': [u'01'], 'musicbrainz_albumid': [u'ea9fba23-896b-4847-96ce-8c16d0c05c0f'], 'album': [u'Not That Kind'], 'musicbrainz_artistid': [u'd3b2bec4-b70e-460e-b433-a865ceac2de8'], 'disctotal': [u'1'], 'title': [u'Not That Kind'], 'tracktotal': [u'12'], 'artistsort': [u'Anastacia'], 'metadata_block_picture': [''], 'musicbrainz_releasegroupid': [u'bf780e6d-0ad3-3517-977a-a2be9b81ae3e'], 'mediatype': [u'CD'], 'encoder': [u'Lavc59.1.100 libvorbis'], 'genre': [u'Pop'], 'isrc': [u'USSM19928913'], 'discnumber': [u'1'], 'artist': [u'Anastacia'], 'country': [u'GB'], 'musicbrainz_trackid': [u'aa80e7d9-22e2-4443-aec4-a6555f0bb9d4'], 'musicbrainz_releasetrackid': [u'c5ffb4f8-78eb-33db-8512-c9b4352985cd']}
		try: audio = OggVorbis(path)
		except: audio = None

	filename = os.path.splitext(os.path.basename(path))[0]
	if audio:
		try: title = getEncodedString(audio.get('title', [filename])[0])
		except: LOG('readID3Infos: get title: EXCEPT', 'err')
		try: album = getEncodedString(audio.get('album', ['n/a'])[0])
		except: LOG('readID3Infos: title: %s: get album: EXCEPT' %(title), 'err')
		try: artist = getEncodedString(audio.get('artist', ['n/a'])[0])
		except: LOG('readID3Infos: title: %s album: %s: get artist: EXCEPT' %(title, album), 'err')
		try: albumartist = getEncodedString(audio.get('albumartist', [''])[0])
		except Exception as e:
			albumartist = ''
			LOG('readID3Infos: title: %s album: %s: get albumartist: EXCEPT:' + str(e) %(title, album), 'err')
		if albumartist == '': albumartist = artist
		try: genre = getEncodedString(audio.get('genre', ['n/a'])[0])
		except: LOG('readID3Infos: title: %s artist: %s: get genre: EXCEPT' %(title, artist), 'err')
		try: date = getEncodedString(audio.get('date', ['n/a'])[0])
		except: LOG('readID3Infos: title: %s artist: %s: get date: EXCEPT' %(title, artist), 'err')
		try: 
			tracknr = searchTrackAndDiscNumber(audio)
		except Exception as e:
			LOG('readID3Infos: filename: %s tracknr: EXCEPT' %(filename, str(e)), 'err')
		if bitrate == 0.0:
			try: bitrate = audio.info.bitrate / 1000.0
			except: pass
		try:
			len = int(audio.info.length)
			length = str(datetime_timedelta(seconds=len)).encode("utf-8", 'ignore')
			if len < 3600: length = length[-5:]
		except Exception as e:
			length = "n/a"
			LOG('readID3Infos: filename: %s length: EXCEPT' %(filename, str(e)), 'err')
	else:
		title = filename
	if bitrate > 0.0: strBitrate = str(round(bitrate,1)) + ' kBit/s' 	
	
	return title, album, genre, artist, albumartist, date, length, tracknr, strBitrate

def searchTrackAndDiscNumber(audio):
	tracknr = -1
	discTotal = 0
	discNr = 1
	discNrkomplett = ''
	try: 
		tracknr = int(audio.get('tracknumber', ['-1'])[0].split("/")[0])
	except: pass	
	#option1: disctotal out of discnumber  (3/4)
	discNrkomplett = audio.get('discnumber',['1'])
	discNrSplit = discNrkomplett[0].split("/")
	discNr = int(discNrSplit[0])
	if len(discNrSplit) > 1: discTotal = int(discNrSplit[1])
	#option2: disctotal out of direct tag
	if discTotal == 0: discTotal = int(audio.get('disctotal', ['0'])[0])

	if discTotal > 1: tracknr = discNr * 1000 + tracknr	
	return tracknr
