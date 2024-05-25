# -*- coding: utf-8 -*-

from setuptools import setup
import setup_translate

pkg = 'Extensions.YampMusicPlayer'
setup(name='enigma2-plugin-extensions-yampmusicplayer',
	description='Music Player with Artist-Art Background',
	cmdclass=setup_translate.cmdclass,
	# explicitly declare packages so setuptools does not attempt auto discovery
	packages=[],
)
