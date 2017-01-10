import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, GObject
from galicaster.core import context
from galicaster.classui import get_ui_path
from galicaster.classui import get_image_path
import galicaster.utils.camctrl_onvif_interface as camera


#DEFAULTS
# This is the default preset to set when the camera is recording
DEFAULT_RECORD_PRESET = "record" 

# This is the default preset to set when the camera is switching off
DEFAULT_IDLE_PRESET = "idle" 

# This is the key containing the preset to use when recording
RECORD_PRESET_KEY = 'record-preset'

# This is the key containing the preset to set the camera to just after switching it off
IDLE_PRESET_KEY= 'idle-preset'

# This is the name of this plugin's section in the configuration file
CONFIG_SECTION = "ipui"

def init():
    global cam, recorder, dispatcher, logger, config, repo

# connect to the camera
    ip = '134.95.128.120'
    username = "root"
    password = "opencast"
    
    cam = camera.AXIS_V5915()
    cam.connect(ip, username, password)


    dispatcher = context.get_dispatcher()
    repo = context.get_repository()
    #  repo = repository.Repository()
    logger = context.get_logger()
    config = context.get_conf().get_section(CONFIG_SECTION) or {}


    dispatcher.connect("init", init_ui)
    dispatcher.connect("recorder-starting", on_start_recording)
    dispatcher.connect("recorder-stopped", on_stop_recording)
    logger.info("Cam connected")


def init_ui(element):
    global recorder_ui, brightscale, movescale, zoomscale, presetlist, presetdelbutton, flybutton, builder, prefbutton, newpreset

    recorder_ui = context.get_mainwindow().nbox.get_nth_page(0).gui

# load css file
    css = Gtk.CssProvider()
    css.load_from_path(get_ui_path("camctrl.css"))

    Gtk.StyleContext.reset_widgets(Gdk.Screen.get_default())
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        css,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    # load glade file
    builder = Gtk.Builder()
    builder.add_from_file(get_ui_path("camctrl-onvif.glade"))
    
    # add new settings tab to the notebook
    notebook = recorder_ui.get_object("data_panel")
    mainbox = builder.get_object("mainbox")
    label = builder.get_object("notebooklabel")
    mainbox.show_all()
    notebook.append_page(mainbox, label)
    notebook.show_all()

    # images
    upimg = Gtk.Image.new_from_file(get_image_path("img/up.svg"))
    downimg = Gtk.Image.new_from_file(get_image_path("img/down.svg"))
    rightimg = Gtk.Image.new_from_file(get_image_path("img/right.svg"))
    rightupimg = Gtk.Image.new_from_file(get_image_path("img/rightup.svg"))
    rightdownimg = Gtk.Image.new_from_file(get_image_path("img/rightdown.svg"))
    leftimg = Gtk.Image.new_from_file(get_image_path("img/left.svg"))
    leftupimg = Gtk.Image.new_from_file(get_image_path("img/leftup.svg"))
    leftdownimg = Gtk.Image.new_from_file(get_image_path("img/leftdown.svg"))
    #  homeimg = Gtk.Image.new_from_file(get_image_path("img/home.svg")) 

    upimg.show()
    downimg.show()
    rightimg.show()
    rightupimg.show()
    rightdownimg.show()
    leftimg.show()
    leftupimg.show()
    leftdownimg.show()
    #  homeimg.show()

    # buttons
    # movement
    button = builder.get_object("left")
    button.add(leftimg)
    button.connect("pressed", move_left)
    button.connect("released", stop_move)

    button = builder.get_object("leftup")
    button.add(leftupimg)
    button.connect("pressed", move_leftup)
    button.connect("released", stop_move)

    button = builder.get_object("leftdown")
    button.add(leftdownimg)
    button.connect("pressed", move_leftdown)
    button.connect("released", stop_move)

    button = builder.get_object("right")
    button.add(rightimg)
    button.connect("pressed", move_right)
    button.connect("released", stop_move)

    button = builder.get_object("rightup")
    button.add(rightupimg)
    button.connect("pressed", move_rightup)
    button.connect("released", stop_move)

    button = builder.get_object("rightdown")
    button.add(rightdownimg)
    button.connect("pressed", move_rightdown)
    button.connect("released", stop_move)

    button = builder.get_object("up")
    button.add(upimg)
    button.connect("pressed", move_up)
    button.connect("released", stop_move)

    button = builder.get_object("down")
    button.add(downimg)
    button.connect("pressed", move_down)
    button.connect("released", stop_move)

    button = builder.get_object("home")
    #  button.add(homeimg)
    button.connect("clicked", move_home)

# zoom
    button = builder.get_object("zoomin")
    button.connect("pressed", zoom_in)
    button.connect("released", stop_move)

    button = builder.get_object("zoomout")
    button.connect("pressed", zoom_out)
    button.connect("released", stop_move)

# presets
    presetlist = builder.get_object("preset_list")
    # add home position to list
    presetlist.insert(0,"home","home")
    # fill the list with current presets
    for preset in cam.getPresets():
        presetlist.append(preset.Name, preset.Name)
    presetlist.connect("changed", change_preset)

# to set a new preset
    newpreset = builder.get_object("newpreset")
    newpreset.connect("activate", save_preset)
    newpreset.connect("icon-press", save_preset_icon)


# to delete a preset
    presetdelbutton = builder.get_object("presetdel")
    presetdelbutton.connect("clicked", empty_entry)

# fly-mode for camera-movement
    flybutton = builder.get_object("fly")
    flybutton.connect("clicked", fly_mode)

# reset all settings
    button = builder.get_object("reset")
    button.connect("clicked", reset)

# show/hide preferences
    prefbutton = builder.get_object("pref")
    prefbutton.connect("clicked", show_pref)

# scales
    #  brightscale = builder.get_object("brightscale")
    #  brightscale.connect("value-changed", set_bright)
    movescale = builder.get_object("movescale")
    zoomscale = builder.get_object("zoomscale")
    

# camera functions

# movement functions
def move_left(button):
    print ("I move left")
    cam.goLeft(movescale.get_value())
    presetlist.set_active(-1)


def move_leftup(button):
    print ("I move leftup")
    cam.goLeftUp(movescale.get_value())
    presetlist.set_active(-1)


def move_leftdown(button):
    print ("I move leftdown")
    cam.goLeftDown(movescale.get_value())
    presetlist.set_active(-1)


def move_right(button):
    print ("I move right")
    cam.goRight(movescale.get_value())
    presetlist.set_active(-1)


def move_rightup(button):
    print ("I move rightup")
    cam.goRightUp(movescale.get_value())
    presetlist.set_active(-1)


def move_rightdown(button):
    print ("I move rightdown")
    cam.goRightDown(movescale.get_value())
    presetlist.set_active(-1)


def move_up(button):
    print ("I move up")
    cam.goUp(movescale.get_value())
    presetlist.set_active(-1)


def move_down(button):
    print ("I move down")
    cam.goDown(movescale.get_value())
    presetlist.set_active(-1)


def stop_move(button):
    print ("I make a break")
    cam.stop()


def move_home(button):
    print ("I move home")
    presetlist.set_active_id("home")


# zoom functions
def zoom_in(button):
    print ("zoom in")
    cam.zoom_in(zoomscale.get_value())
    presetlist.set_active(-1)


def zoom_out(button):
    print ("zoom out")
    cam.zoom_out(zoomscale.get_value())
    presetlist.set_active(-1)


# preset functions
def change_preset(presetlist):
    if len(newpreset.get_text()) > 0:
        if newpreset.get_text() == "home":
            print ("New Home set to current position.")
        else:
            print("New Preset saved: ", newpreset.get_text())
    elif presetlist.get_active_text() == "home":
        print("Going Home")
        cam.goHome()        
    else:
        if presetdelbutton.get_active() and not presetlist.get_active_text() is None:
            cam.removePreset(cam.identifyPreset(presetlist.get_active_text()))
            presetdelbutton.set_active(False)
            presetlist.remove(presetlist.get_active())
            
        else:
            if not presetlist.get_active_text() is None:
                print("Going to: " + presetlist.get_active_text())
                cam.goToPreset(cam.identifyPreset(presetlist.get_active_text()))


def empty_entry(presetdelbutton):
    if presetdelbutton.get_active():
        presetlist.set_active(-1)
        presetlist.remove(0)
    elif not presetdelbutton.get_active():
        presetlist.insert(0,"home","home")


def save_preset_icon(newpreset, pos, event):
    if newpreset.get_text() == "home":
        cam.setHome()
        presetlist.set_active_id(newpreset.get_text())
        newpreset.set_text("")
    else:
        cam.setPreset(newpreset.get_text())
        presetlist.append(newpreset.get_text(), newpreset.get_text())
        presetlist.set_active_id(newpreset.get_text())
        newpreset.set_text("")


def save_preset(newpreset):
    if newpreset.get_text() == "home":
        cam.setHome()
        presetlist.set_active_id(newpreset.get_text())
        newpreset.set_text("")
    else:
        cam.setPreset(newpreset.get_text())
        presetlist.append(newpreset.get_text(), newpreset.get_text())
        presetlist.set_active_id(newpreset.get_text())
        newpreset.set_text("")


# brightness scale
def set_bright(brightscale):
    return None

# reset all settings
def reset(button):
    movescale.set_value(0.5)
    zoomscale.set_value(0.5)
    # reset location
    cam.goHome()


# hides/shows the advanced preferences
def show_pref(prefbutton):
    scalebox1 = builder.get_object("scales1")
    scalebox2 = builder.get_object("scales2")
    # settings button activated
    if scalebox1.get_property("visible"):
        print ("hide advanced settings")
        scalebox1.hide()
        scalebox2.hide()
    # settings button deactivated
    else:
        print ("show advanced settings")
        scalebox1.show()
        scalebox2.show()


# flymode activation connects clicked signal and disconnects
# pressed/released to keep the movement
def fly_mode(flybutton):
    # fly mode turned on
    if flybutton.get_active():
        print ("fly mode turned on")
        button = builder.get_object("left")
        GObject.signal_handlers_destroy(button)
        button.connect("clicked", move_left)

        button = builder.get_object("leftup")
        GObject.signal_handlers_destroy(button)
        button.connect("clicked", move_leftup)

        button = builder.get_object("leftdown")
        GObject.signal_handlers_destroy(button)
        button.connect("clicked", move_leftdown)

        button = builder.get_object("right")
        GObject.signal_handlers_destroy(button)
        button.connect("clicked", move_right)

        button = builder.get_object("rightup")
        GObject.signal_handlers_destroy(button)
        button.connect("clicked", move_rightup)

        button = builder.get_object("rightdown")
        GObject.signal_handlers_destroy(button)
        button.connect("clicked", move_rightdown)

        button = builder.get_object("up")
        GObject.signal_handlers_destroy(button)
        button.connect("clicked", move_up)

        button = builder.get_object("down")
        GObject.signal_handlers_destroy(button)
        button.connect("clicked", move_down)

        button = builder.get_object("home")
        img = builder.get_object("stopimg")
        GObject.signal_handlers_destroy(button)
        button.set_image(img)
        button.connect("clicked", stop_move)

    # fly mode turned off
    else:
        print("fly mode turned off")

        button = builder.get_object("left")
        GObject.signal_handlers_destroy(button)
        button.connect("pressed", move_left)
        button.connect("released", stop_move)

        button = builder.get_object("leftup")
        GObject.signal_handlers_destroy(button)
        button.connect("pressed", move_leftup)
        button.connect("released", stop_move)

        button = builder.get_object("leftdown")
        GObject.signal_handlers_destroy(button)
        button.connect("pressed", move_leftdown)
        button.connect("released", stop_move)

        button = builder.get_object("right")
        GObject.signal_handlers_destroy(button)
        button.connect("pressed", move_right)
        button.connect("released", stop_move)

        button = builder.get_object("rightup")
        GObject.signal_handlers_destroy(button)
        button.connect("pressed", move_rightup)
        button.connect("released", stop_move)

        button = builder.get_object("rightdown")
        GObject.signal_handlers_destroy(button)
        button.connect("pressed", move_rightdown)
        button.connect("released", stop_move)

        button = builder.get_object("up")
        GObject.signal_handlers_destroy(button)
        button.connect("pressed", move_up)
        button.connect("released", stop_move)

        button = builder.get_object("down")
        GObject.signal_handlers_destroy(button)
        button.connect("pressed", move_down)
        button.connect("released", stop_move)

        button = builder.get_object("home")
        img = builder.get_object("homeimg")
        GObject.signal_handlers_destroy(button)
        button.set_image(img)
        button.connect("clicked", move_home)


def on_start_recording(elem):
    
    preset = config.get(RECORD_PRESET_KEY, DEFAULT_RECORD_PRESET)
    mp = repo.get_next_mediapackage()

    if mp is not None:
        properties = mp.getOCCaptureAgentProperties()
        preset = properties['org.opencastproject.workflow.config.cameraPreset']

    try:
        presetlist.set_active_id(preset)
        #  cam.goToPreset(cam.identifyPreset(preset))

    except Exception as e:
        logger.warn("Error accessing the IP camera on recording start. The recording may be incorrect! Error:", e)


def on_stop_recording(elem, elem2):

    try:
        presetlist.set_active_id(config.get(IDLE_PRESET_KEY, DEFAULT_IDLE_PRESET))
        #  cam.goToPreset(cam.identifyPreset(config.get(IDLE_PRESET_KEY, DEFAULT_IDLE_PRESET)))

    except Exception as e:
        logger.warn("Error accessing the IP camera on recording end. The recording may be incorrect! Error: ", e)
