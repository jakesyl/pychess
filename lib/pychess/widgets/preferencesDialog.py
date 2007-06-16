import sys, os

import gtk, gobject

from pychess.System import myconf
from pychess.System import gstreamer
from pychess.Utils.const import *
from pychess.Players.engineNest import discoverer

firstRun = True
def run(widgets):
    global firstRun
    if firstRun:
        initialize(widgets)
        firstRun = False
    widgets["preferences"].show()

def initialize(widgets):
    
    def delete_event (widget, *args):
        widgets["preferences"].hide()
        return True
    
    GeneralTab(widgets)
    EngineTab(widgets)
    SoundTab(widgets)
    
    widgets["preferences"].connect("delete-event", delete_event)
    widgets["preferences_close_button"].connect("clicked", delete_event)

################################################################################
# Gui functions                                                                #
################################################################################

def createCombo (combo, data):
    ls = gtk.ListStore(gtk.gdk.Pixbuf, str)
    for icon, label in data:
        ls.append([icon, label])
    combo.clear()
    
    combo.set_model(ls)
    crp = gtk.CellRendererPixbuf()
    crp.set_property('xalign',0)
    crp.set_property('xpad', 2)
    combo.pack_start(crp, False)
    combo.add_attribute(crp, 'pixbuf', 0)
    
    crt = gtk.CellRendererText()
    crt.set_property('xalign',0)
    crt.set_property('xpad', 4)
    combo.pack_start(crt, True)
    combo.add_attribute(crt, 'text', 1)

methodDict = {
    gtk.CheckButton: ("get_active", "set_active", "toggled"),
    gtk.Entry: ("get_text", "set_text", "changed"),
    gtk.ComboBox: ("get_active", "set_active", "changed"),
    gtk.RadioButton: ("get_active", "set_active", "toggled")
}

def keep (widgets, key, get_value_=None, set_value_=None):
    widget = widgets[key]
    if widget == None:
        raise AttributeError, "key '%s' isn't in widgets" % key
    
    if get_value_:
        get_value = lambda: get_value_(widget)
    else:
        get_value = getattr(widget, methodDict[type(widget)][0])
    
    if set_value_:
        set_value = lambda v: set_value_(widget, v)
    else:
        set_value = getattr(widget, methodDict[type(widget)][1])
    
    set_value(myconf.get(key))
    
    signal = methodDict[type(widget)][2]
    widget.connect(signal, lambda *args: myconf.set(key, get_value()))
    myconf.notify_add(key, lambda *args: set_value(myconf.get(key)))

################################################################################
# General initing                                                              #
################################################################################

class GeneralTab:
    
    def __init__ (self, widgets):
        firstName = myconf.get("firstName")
        if not firstName:
            from pwd import getpwuid
            from os import getuid
            userdata = getpwuid(getuid())
            firstName = userdata.pw_gecos
            if not firstName:
                firstName = userdata.pw_name
            myconf.set("firstName", firstName)
        
        secondName = myconf.get("secondName")
        if not secondName:
            myconf.set("secondName", _("Guest"))
        
        # Give to keeper
        
        for key in ("firstName", "secondName",
                    "hideTabs", "autoRotate", "showCords", "figuresInNotation",  
                    "fullAnimation", "moveAnimation", "noAnimation"):
            keep(widgets, key)

################################################################################
# Engine initing                                                               #
################################################################################

class EngineTab:
    
    def __init__ (self, widgets):
        
        # Put engines in trees and combos
        
        engines = discoverer.getEngines()
        allstore = gtk.ListStore(gtk.gdk.Pixbuf, str)
        for engine in engines.values():
            c = discoverer.getCountry(engine)
            if c:
                flag = "flags/%s.png" % c
            else: flag = "flags/unknown.png"
            flag_icon = gtk.gdk.pixbuf_new_from_file(prefix(flag))
            allstore.append((flag_icon, discoverer.getName(engine)))
        
        tv = widgets["engines_treeview"]
        tv.set_model(allstore)
        tv.append_column(gtk.TreeViewColumn(
                "Flag", gtk.CellRendererPixbuf(), pixbuf=0))
        tv.append_column(gtk.TreeViewColumn(
                "Name", gtk.CellRendererText(), text=1))
        
        analyzers = discoverer.getAnalyzers()
        ana_data = []
        invana_data = []
        for engine in analyzers:
            name = discoverer.getName(engine)
            c = discoverer.getCountry(engine)
            if c:
                flag = "flags/%s.png" % c
            else: flag = "flags/unknown.png"
            flag_icon = gtk.gdk.pixbuf_new_from_file(prefix(flag))
            ana_data.append((flag_icon, name))
            invana_data.append((flag_icon, name))
        
        createCombo(widgets["ana_combobox"], ana_data)
        createCombo(widgets["inv_ana_combobox"], invana_data)
        
        # Save, load and make analyze combos active
    
        def on_analyzer_check_toggled (check):
            widgets["analyzers_vbox"].set_sensitive(check.get_active())
            widgets["hint_mode"].set_active(check.get_active())
            from pychess.Main import gameDic
            if gameDic:
                widgets["hint_mode"].set_sensitive(check.get_active())
        widgets["analyzer_check"].connect("toggled", on_analyzer_check_toggled)
        
        def on_analyzer_check_toggled (check):
            widgets["inv_analyzers_vbox"].set_sensitive(check.get_active())
            widgets["spy_mode"].set_active(check.get_active())
            from pychess.Main import gameDic
            if gameDic:
                widgets["spy_mode"].set_sensitive(check.get_active())
        widgets["inv_analyzer_check"].connect("toggled", on_analyzer_check_toggled)
        
        # Put options in trees in add/edit dialog
        
        tv = widgets["optionview"]
        tv.append_column(gtk.TreeViewColumn(
            "Option", gtk.CellRendererText(), text=0))
        tv.append_column(gtk.TreeViewColumn(
            "Value", gtk.CellRendererText(), text=1))
        
        def edit (button):
            
            iter = widgets["engines_treeview"].get_selection().get_selected()[1]
            if iter: row = allstore.get_path(iter)[0]
            else: return
            
            engine = discoverer.getEngineN(row)
            optionstags = engine.getElementsByTagName("options")
            if not optionstags:
                widgets["engine_options_expander"].hide()
            else:
                widgets["engine_options_expander"].show()
                widgets["engine_options_expander"].set_expanded(False)
                
                optionsstore = gtk.ListStore(str, str)
                tv = widgets["optionview"]
                tv.set_model(optionsstore)
                
                for option in optionstags[0].childNodes:
                    if option.nodeType != option.ELEMENT_NODE: continue
                    optionsstore.append( [option.getAttribute("name"),
                                          option.getAttribute("default")] )
                
            widgets["engine_path_chooser"].set_title(_("Locate Engine"))
            widgets["engine_path_chooser"].set_uri("file:///usr/bin/gnuchess")
            
            dialog = widgets["addconfig_engine"]
            answer = dialog.run()
            dialog.hide()
        widgets["edit_engine_button"].connect("clicked", edit)
        #widgets["remove_engine_button"].connect("clicked", remove)
        #widgets["add_engine_button"].connect("clicked", add)
        
        # Give widgets to kepper
        
        for combo in ("ana_combobox", "inv_ana_combobox"):
            
            def get_value (combobox):
                engine = discoverer.getAnalyzers()[combobox.get_active()]
                md5s = engine.getElementsByTagName("md5")
                if md5s:
                    return md5s[0].childNodes[0].data.strip()
            
            def set_value (combobox, value):
                engine = discoverer.getEngineByMd5(value)
                if not engine:
                    combobox.set_active(0)
                else:
                    index = discoverer.getAnalyzers().index(engine)
                    combobox.set_active(index)
            
            keep (widgets, combo, get_value, set_value)
        
################################################################################
# Sound initing                                                                #
################################################################################

class SoundTab:
    
    SOUND_DIRS = ("/usr/share/sounds", "/usr/local/share/sounds",
                  os.environ["HOME"])
    
    COUNT_OF_SOUNDS = 9
    
    actionToKeyNo = {
        "aPlayerMoves": 0,
        "aPlayerChecks": 1,
        "aPlayerCaptures": 2,
        "gameIsSetup": 3,
        "gameIsWon": 4,
        "gameIsLost": 5,
        "gameIsDrawn": 6,
        "observedMoves": 7,
        "oberservedEnds": 8
    }
    
    @classmethod
    def playAction (cls, action):
        no = cls.actionToKeyNo[action]
        type = myconf.get("soundcombo%d" % no)
        if type == SOUND_BEEP:
            sys.stdout.write("\a")
            sys.stdout.flush()
        elif type == SOUND_URI:
            uri = myconf.get("sounduri%d" % no)
            gstreamer.playSound(uri)
    
    def __init__ (self, widgets):
        
        # Init open dialog
        
        opendialog = gtk.FileChooserDialog (
                _("Open Sound File"), None, gtk.FILE_CHOOSER_ACTION_OPEN,
                 (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN,
                  gtk.RESPONSE_ACCEPT))
        
        for dir in self.SOUND_DIRS:
            if os.path.isdir(dir):
                opendialog.set_current_folder(dir)
                break
        
        soundfilter = gtk.FileFilter()
        soundfilter.add_custom(soundfilter.get_needed(),
                               lambda data: data[3].startswith("audio/"))
        opendialog.add_filter(soundfilter)
        opendialog.set_filter(soundfilter)
        
        # Get combo icons
        
        icons = ((_("No sound"), "audio-volume-muted", "audio-volume-muted"),
                 (_("Beep"), "stock_bell", "audio-x-generic"), 
                 (_("Select sound file..."), "gtk-open", "document-open"))
        
        it = gtk.icon_theme_get_default()
        items = []
        for level, stock, altstock in icons:
            try:
                image = it.load_icon(stock, 16, gtk.ICON_LOOKUP_USE_BUILTIN)
            except gobject.GError:
                image = it.load_icon(altstock, 16, gtk.ICON_LOOKUP_USE_BUILTIN)
            items += [(image, level)]
        
        audioIco = it.load_icon("audio-x-generic", 16,
                                gtk.ICON_LOOKUP_USE_BUILTIN)
        
        # Set-up combos
        
        def callback (combobox, index):
            if combobox.get_active() == SOUND_SELECT:
                if opendialog.run() == gtk.RESPONSE_ACCEPT:
                    uri = opendialog.get_uri()
                    model = combobox.get_model()
                    myconf.set("sounduri%d"%index, uri)
                    label = os.path.split(uri)[1]
                    if len(model) == 3:
                        model.append([audioIco, label])
                    else:
                        model.set(model.get_iter((3,)), 1, label)
                    combobox.set_active(3)
                else:
                    combobox.set_active(myconf.get("soundcombo%d"%index))
                opendialog.hide()
        
        for i in xrange(self.COUNT_OF_SOUNDS):
            combo = widgets["soundcombo%d"%i]
            createCombo (combo, items)
            combo.set_active(2)
            combo.connect("changed", callback, i)
            
            label = widgets["soundlabel%d"%i]
            label.props.mnemonic_widget = combo
            
            uri = myconf.get("sounduri%d"%i)
            if uri:
                model = combo.get_model()
                model.append([audioIco, os.path.split(uri)[1]])
                combo.set_active(3)
        
        # Init play button
        
        def playCallback (button, index):
            value = myconf.get("soundcombo%d"%index)
            if value == SOUND_BEEP:
                sys.stdout.write("\a")
                sys.stdout.flush()
            elif value == SOUND_URI:
                uri = myconf.get("sounduri%d"%index)
                gstreamer.playSound(uri)
        
        for i in range (self.COUNT_OF_SOUNDS):
            button = widgets["soundbutton%d"%i]
            button.connect("clicked", playCallback, i)
        
        # Init 'use sound" checkbutton
        
        def checkCallBack (*args):
            checkbox = widgets["useSounds"]
            widgets["frame23"].set_property("sensitive", checkbox.get_active())
        myconf.notify_add("useSounds", checkCallBack)
        
        # Give widgets to auto connecter
        
        keep(widgets, "useSounds")
        for i in xrange(self.COUNT_OF_SOUNDS):
            keep(widgets, "soundcombo%d" % i)