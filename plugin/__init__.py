from gettext import bindtextdomain, dgettext, gettext
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

PluginLanguageDomain = "YampMusicPlayer"
PluginLanguagePath = "Extensions/YampMusicPlayer/locale"


def localeInit():
	bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	t = dgettext(PluginLanguageDomain, txt)
	if t == txt:
		print(f"[Yamp] Fallback to default Enigma2 Translation for '{txt}'")
		t = gettext(txt)
	return t


localeInit()
language.addCallback(localeInit)
