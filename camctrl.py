import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, GObject
from galicaster.core import context
from galicaster.classui import get_ui_path
from galicaster.classui import get_image_path
import galicaster.utils.pysca as pysca
import galicaster.utils.camctrl_onvif_interface as camera 


#DEFAULTS
# This is the default Visca device this plugin talks to
DEFAULT_DEVICE = 1

# This is the default preset to set when the camera is recording
DEFAULT_RECORD_PRESET = "record"
DEFAULT_RECORD_PRESET_INT = 0

# This is the default preset to set when the camera is switching off
DEFAULT_IDLE_PRESET = "idle"
DEFAULT_IDLE_PRESET_INT = 5

# This is the key containing the preset to use when recording
RECORD_PRESET_KEY = 'record-preset'

# This is the key containing the preset to set the camera to just after switching it off
IDLE_PRESET_KEY= 'idle-preset'

# This is the key containing the port (path to the device) to use when recording
PORT_KEY = "port"

# This is the key specifying the backend (visca or onvif)
BACKEND = 'backend'

# This is the name of this plugin's section in the configuration file
CONFIG_SECTION = "camctrl"



def init():
    global recorder, dispatcher, logger, config, repo

    config = context.get_conf().get_section(CONFIG_SECTION) or {}
    dispatcher = context.get_dispatcher()
    repo = context.get_repository()
    logger = context.get_logger()

    backend = config.get(BACKEND)

    if backend == "onvif":
        global cam
        # connect to the camera
        ip = '134.95.128.120'
        username = "root"
        password = "opencast"

        cam = camera.AXIS_V5915()
        cam.connect(ip, username, password)

        # initiate the onvif user interface
        dispatcher.connect("init", init_onvif_ui)
        dispatcher.connect("recorder-starting", onvif_interface.on_start_recording)
        dispatcher.connect("recorder-stopped", onvif_interface.on_stop_recording)
    
    if backend == "visca":
        
        # If port is not defined, a None value will make this method fail
        pysca.connect(config.get(PORT_KEY))
        
        # initiate the visca user interface
        dispatcher.connect("init", init_visca_ui)
        dispatcher.connect('recorder-starting', visca_interface.on_start_recording)
        dispatcher.connect('recorder-stopped', visca_interface.on_stop_recording)

    logger.info("Cam connected")


# VISCA USER INTERFACE
def init_visca_ui(element):
    global recorder_ui, brightscale, movescale, zoomscale, presetbutton, flybutton, builder, onoffbutton, prefbutton

    visca = visca_interface()

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
    builder.add_from_file(get_ui_path("camctrl-visca.glade"))

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

    upimg.show()
    downimg.show()
    rightimg.show()
    rightupimg.show()
    rightdownimg.show()
    leftimg.show()
    leftupimg.show()
    leftdownimg.show()

    # buttons
    # movement
    button = builder.get_object("left")
    button.add(leftimg)
    button.connect("pressed", visca.move_left)
    button.connect("released", visca.stop_move)

    button = builder.get_object("leftup")
    button.add(leftupimg)
    button.connect("pressed", visca.move_leftup)
    button.connect("released", visca.stop_move)

    button = builder.get_object("leftdown")
    button.add(leftdownimg)
    button.connect("pressed", visca.move_leftdown)
    button.connect("released", visca.stop_move)

    button = builder.get_object("right")
    button.add(rightimg)
    button.connect("pressed", visca.move_right)
    button.connect("released", visca.stop_move)

    button = builder.get_object("rightup")
    button.add(rightupimg)
    button.connect("pressed", visca.move_rightup)
    button.connect("released", visca.stop_move)

    button = builder.get_object("rightdown")
    button.add(rightdownimg)
    button.connect("pressed", visca.move_rightdown)
    button.connect("released", visca.stop_move)

    button = builder.get_object("up")
    button.add(upimg)
    button.connect("pressed", visca.move_up)
    button.connect("released", visca.stop_move)

    button = builder.get_object("down")
    button.add(downimg)
    button.connect("pressed", visca.move_down)
    button.connect("released", visca.stop_move)

    button = builder.get_object("home")
    button.connect("clicked", visca.move_home)

    # zoom
    button = builder.get_object("zoomin")
    button.connect("pressed", visca.zoom_in)
    button.connect("released", visca.stop_zoom)

    button = builder.get_object("zoomout")
    button.connect("pressed", visca.zoom_out)
    button.connect("released", visca.stop_zoom)

    # presets
    button = builder.get_object("1")
    button.connect("clicked", visca.preset1)

    button = builder.get_object("2")
    button.connect("clicked", visca.preset2)

    button = builder.get_object("3")
    button.connect("clicked", visca.preset3)

    button = builder.get_object("4")
    button.connect("clicked", visca.preset4)

    button = builder.get_object("5")
    button.connect("clicked", visca.preset5)

    button = builder.get_object("6")
    button.connect("clicked", visca.preset6)

    # to set a new preset
    presetbutton = builder.get_object("preset")

    # fly-mode for camera-movement
    flybutton = builder.get_object("fly")
    flybutton.connect("clicked", visca.fly_mode)

    # on-off button
    onoffbutton = builder.get_object("on-off")
    onoffbutton.connect("state-set", visca.turn_on_off)

    # reset all settings
    button = builder.get_object("reset")
    button.connect("clicked", visca.reset)

    # show/hide preferences
    prefbutton = builder.get_object("pref")
    prefbutton.connect("clicked", visca.show_pref)

    # scales
    brightscale = builder.get_object("brightscale")
    brightscale.connect("value-changed", visca.set_bright)
    movescale = builder.get_object("movescale")
    zoomscale = builder.get_object("zoomscale")


# ONVIF USER INTERFACE       
def init_onvif_ui(element):
    global recorder_ui, brightscale, movescale, zoomscale, presetlist, presetdelbutton, flybutton, builder, prefbutton, newpreset

    onvif = onvif_interface()

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
    button.connect("pressed", onvif.move_left)
    button.connect("released", onvif.stop_move)

    button = builder.get_object("leftup")
    button.add(leftupimg)
    button.connect("pressed", onvif.move_leftup)
    button.connect("released", onvif.stop_move)

    button = builder.get_object("leftdown")
    button.add(leftdownimg)
    button.connect("pressed", onvif.move_leftdown)
    button.connect("released", onvif.stop_move)

    button = builder.get_object("right")
    button.add(rightimg)
    button.connect("pressed", onvif.move_right)
    button.connect("released", onvif.stop_move)

    button = builder.get_object("rightup")
    button.add(rightupimg)
    button.connect("pressed", onvif.move_rightup)
    button.connect("released", onvif.stop_move)

    button = builder.get_object("rightdown")
    button.add(rightdownimg)
    button.connect("pressed", onvif.move_rightdown)
    button.connect("released", onvif.stop_move)

    button = builder.get_object("up")
    button.add(upimg)
    button.connect("pressed", onvif.move_up)
    button.connect("released", onvif.stop_move)

    button = builder.get_object("down")
    button.add(downimg)
    button.connect("pressed", onvif.move_down)
    button.connect("released", onvif.stop_move)

    button = builder.get_object("home")
    #  button.add(homeimg)
    button.connect("clicked", onvif.move_home)

# zoom
    button = builder.get_object("zoomin")
    button.connect("pressed", onvif.zoom_in)
    button.connect("released", onvif.stop_move)

    button = builder.get_object("zoomout")
    button.connect("pressed", onvif.zoom_out)
    button.connect("released", onvif.stop_move)

# presets
    presetlist = builder.get_object("preset_list")
    # add home position to list
    presetlist.insert(0,"home","home")
    # fill the list with current presets
    for preset in cam.getPresets():
        presetlist.append(preset.Name, preset.Name)
    presetlist.connect("changed", onvif.change_preset)

# to set a new preset
    newpreset = builder.get_object("newpreset")
    newpreset.connect("activate", onvif.save_preset)
    newpreset.connect("icon-press", onvif.save_preset_icon)


# to delete a preset
    presetdelbutton = builder.get_object("presetdel")
    presetdelbutton.connect("clicked", onvif.empty_entry)

# fly-mode for camera-movement
    flybutton = builder.get_object("fly")
    flybutton.connect("clicked", onvif.fly_mode)

# reset all settings
    button = builder.get_object("reset")
    button.connect("clicked", onvif.reset)

# show/hide preferences
    prefbutton = builder.get_object("pref")
    prefbutton.connect("clicked", onvif.show_pref)

# scales
    #  brightscale = builder.get_object("brightscale")
    #  brightscale.connect("value-changed", set_bright)
    movescale = builder.get_object("movescale")
    zoomscale = builder.get_object("zoomscale")
    

# visca function interface
class visca_interface():
    # movement functions
    def move_left(self, button):
        print ("I move left")
        pysca.pan_tilt(DEFAULT_DEVICE, pan=-movescale.get_value())


    def move_leftup(self, button):
        print ("I move leftup")
        pysca.pan_tilt(DEFAULT_DEVICE, pan=-movescale.get_value(), tilt=movescale.get_value())


    def move_leftdown(self, button):
        print ("I move leftdown")
        pysca.pan_tilt(DEFAULT_DEVICE, pan=-movescale.get_value(), tilt=-movescale.get_value())


    def move_right(self, button):
        print ("I move right")
        pysca.pan_tilt(DEFAULT_DEVICE, pan=movescale.get_value())


    def move_rightup(self, button):
        print ("I move rightup")
        pysca.pan_tilt(DEFAULT_DEVICE, pan=movescale.get_value(), tilt=movescale.get_value())


    def move_rightdown(self, button):
        print ("I move rightdown")
        pysca.pan_tilt(DEFAULT_DEVICE, pan=movescale.get_value(), tilt=-movescale.get_value())


    def move_up(self, button):
        print ("I move up")
        pysca.pan_tilt(DEFAULT_DEVICE, tilt=movescale.get_value())


    def move_down(self, button):
        print ("I move down")
        pysca.pan_tilt(DEFAULT_DEVICE, tilt=-movescale.get_value())


    def stop_move(self, button):
        print ("I make a break")
        pysca.pan_tilt(DEFAULT_DEVICE, pan=0, tilt=0)


    def move_home(self, button):
        print ("I move home")
        pysca.pan_tilt_home(DEFAULT_DEVICE)


# zoom functions
    def zoom_in(self, button):
        print ("zoom in")
        pysca.zoom(DEFAULT_DEVICE, pysca.ZOOM_ACTION_TELE, speed=zoomscale.get_value())


    def zoom_out(self, button):
        print ("zoom out")
        pysca.zoom(DEFAULT_DEVICE, pysca.ZOOM_ACTION_WIDE, speed=zoomscale.get_value())


    def stop_zoom(self, button):
        print ("stop zoom")
        pysca.zoom(DEFAULT_DEVICE, pysca.ZOOM_ACTION_STOP)


# preset functions
    def preset1(self, button):
        if presetbutton.get_active():
            pysca.set_memory(DEFAULT_DEVICE, 0)
            presetbutton.set_active(False)
        else:
            pysca.recall_memory(DEFAULT_DEVICE, 0)


    def preset2(self, button):
        if presetbutton.get_active():
            pysca.set_memory(DEFAULT_DEVICE, 1)
            presetbutton.set_active(False)
        else:
            pysca.recall_memory(DEFAULT_DEVICE, 1)


    def preset3(self, button):
        if presetbutton.get_active():
            pysca.set_memory(DEFAULT_DEVICE, 2)
            presetbutton.set_active(False)
        else:
            pysca.recall_memory(DEFAULT_DEVICE, 2)


    def preset4(self, button):
        if presetbutton.get_active():
            pysca.set_memory(DEFAULT_DEVICE, 3)
            presetbutton.set_active(False)
        else:
            pysca.recall_memory(DEFAULT_DEVICE, 3)


    def preset5(self, button):
        if presetbutton.get_active():
            pysca.set_memory(DEFAULT_DEVICE, 4)
            presetbutton.set_active(False)
        else:
            pysca.recall_memory(DEFAULT_DEVICE, 4)


    def preset6(self, button):
        if presetbutton.get_active():
            pysca.set_memory(DEFAULT_DEVICE, 5)
            presetbutton.set_active(False)
        else:
            pysca.recall_memory(DEFAULT_DEVICE, 5)


# brightness scale
    def set_bright(self, brightscale):
        pysca.set_ae_mode(DEFAULT_DEVICE, pysca.AUTO_EXPOSURE_BRIGHT_MODE)
        pysca.set_brightness(DEFAULT_DEVICE, brightscale.get_value() + 15)


# reset all settings
    def reset(self, button):
        # reset brightness
        pysca.set_ae_mode(DEFAULT_DEVICE, pysca.AUTO_EXPOSURE_BRIGHT_MODE)
        pysca.set_brightness(DEFAULT_DEVICE, 15)
        brightscale.set_value(0)
        movescale.set_value(7)
        zoomscale.set_value(3.5)
        # reset zoom
        pysca.set_zoom(DEFAULT_DEVICE, 0000)
        # reset location
        pysca.pan_tilt_home(DEFAULT_DEVICE)


# turns the camera on/off
    def turn_on_off(self, onoffbutton, state):
        if onoffbutton.get_active():
            pysca.set_power_on(DEFAULT_DEVICE, True)
        else:
            pysca.set_power_on(DEFAULT_DEVICE, False)


# hides/shows the advanced preferences
    def show_pref(self, prefbutton):
        scalebox1 = builder.get_object("scales1")
        scalebox2 = builder.get_object("scales2")
        scalebox3 = builder.get_object("scales3")
        # settings button activated
        if scalebox1.get_property("visible"):
            print ("hide advanced settings")
            scalebox1.hide()
            scalebox2.hide()
            scalebox3.hide()
        # settings button deactivated
        else:
            print ("show advanced settings")
            scalebox1.show()
            scalebox2.show()
            scalebox3.show()



# flymode activation connects clicked signal and disconnects
# pressed/released to keep the movement
    def fly_mode(self, flybutton):
        # fly mode turned on
        if flybutton.get_active():
            print ("fly mode turned on")
            button = builder.get_object("left")
            GObject.signal_handlers_destroy(button)
            button.connect("clicked", self.move_left)

            button = builder.get_object("leftup")
            GObject.signal_handlers_destroy(button)
            button.connect("clicked", self.move_leftup)

            button = builder.get_object("leftdown")
            GObject.signal_handlers_destroy(button)
            button.connect("clicked", self.move_leftdown)

            button = builder.get_object("right")
            GObject.signal_handlers_destroy(button)
            button.connect("clicked", self.move_right)

            button = builder.get_object("rightup")
            GObject.signal_handlers_destroy(button)
            button.connect("clicked", self.move_rightup)

            button = builder.get_object("rightdown")
            GObject.signal_handlers_destroy(button)
            button.connect("clicked", self.move_rightdown)

            button = builder.get_object("up")
            GObject.signal_handlers_destroy(button)
            button.connect("clicked", self.move_up)

            button = builder.get_object("down")
            GObject.signal_handlers_destroy(button)
            button.connect("clicked", self.move_down)

            button = builder.get_object("home")
            img = builder.get_object("stopimg")
            GObject.signal_handlers_destroy(button)
            button.set_image(img)
            button.connect("clicked", self.stop_move)


        # fly mode turned off
        else:
            print("fly mode turned off")

            button = builder.get_object("left")
            GObject.signal_handlers_destroy(button)
            button.connect("pressed", self.move_left)
            button.connect("released", self.stop_move)

            button = builder.get_object("leftup")
            GObject.signal_handlers_destroy(button)
            button.connect("pressed", self.move_leftup)
            button.connect("released", self.stop_move)

            button = builder.get_object("leftdown")
            GObject.signal_handlers_destroy(button)
            button.connect("pressed", self.move_leftdown)
            button.connect("released", self.stop_move)

            button = builder.get_object("right")
            GObject.signal_handlers_destroy(button)
            button.connect("pressed", self.move_right)
            button.connect("released", self.stop_move)

            button = builder.get_object("rightup")
            GObject.signal_handlers_destroy(button)
            button.connect("pressed", self.move_rightup)
            button.connect("released", self.stop_move)

            button = builder.get_object("rightdown")
            GObject.signal_handlers_destroy(button)
            button.connect("pressed", self.move_rightdown)
            button.connect("released", self.stop_move)

            button = builder.get_object("up")
            GObject.signal_handlers_destroy(button)
            button.connect("pressed", self.move_up)
            button.connect("released", self.stop_move)

            button = builder.get_object("down")
            GObject.signal_handlers_destroy(button)
            button.connect("pressed", self.move_down)
            button.connect("released", self.stop_move)

            button = builder.get_object("home")
            img = builder.get_object("homeimg")
            GObject.signal_handlers_destroy(button)
            button.set_image(img)
            button.connect("clicked", self.move_home)


    def on_start_recording(self, elem):

        preset = config.get(RECORD_PRESET_KEY, DEFAULT_RECORD_PRESET_INT)
        mp = repo.get_next_mediapackage()

        if mp is not None:
            properties = mp.getOCCaptureAgentProperties()
            preset = int(properties['org.opencastproject.workflow.config.cameraPreset'])

        try:
            pysca.set_power_on(DEFAULT_DEVICE, True, ) 
            onoffbutton.set_active(True)
            pysca.recall_memory(DEFAULT_DEVICE, (preset))

        except Exception as e:
            logger.warn("Error accessing the Visca device %u on recording start. The recording may be incorrect! Error: %s" % (DEFAULT_DEVICE, e))


    def on_stop_recording(self, elem, elem2):

        try:
            pysca.recall_memory(DEFAULT_DEVICE, config.get(IDLE_PRESET_KEY, DEFAULT_IDLE_PRESET_INT))
            pysca.set_power_on(DEFAULT_DEVICE, False)
            onoffbutton.set_active(False)

        except Exception as e:
            logger.warn("Error accessing the Visca device %u on recording end. The recording may be incorrect! Error: %s" % (DEFAULT_DEVICE, e))


# onvif function interface
class onvif_interface():

    # movement functions
    def move_left(self, button):
        print ("I move left")
        cam.goLeft(movescale.get_value())
        presetlist.set_active(-1)


    def move_leftup(self, button):
        print ("I move leftup")
        cam.goLeftUp(movescale.get_value())
        presetlist.set_active(-1)


    def move_leftdown(self, button):
        print ("I move leftdown")
        cam.goLeftDown(movescale.get_value())
        presetlist.set_active(-1)


    def move_right(self, button):
        print ("I move right")
        cam.goRight(movescale.get_value())
        presetlist.set_active(-1)


    def move_rightup(self, button):
        print ("I move rightup")
        cam.goRightUp(movescale.get_value())
        presetlist.set_active(-1)


    def move_rightdown(self, button):
        print ("I move rightdown")
        cam.goRightDown(movescale.get_value())
        presetlist.set_active(-1)


    def move_up(self, button):
        print ("I move up")
        cam.goUp(movescale.get_value())
        presetlist.set_active(-1)


    def move_down(self, button):
        print ("I move down")
        cam.goDown(movescale.get_value())
        presetlist.set_active(-1)


    def stop_move(self, button):
        print ("I make a break")
        cam.stop()


    def move_home(self, button):
        print ("I move home")
        presetlist.set_active_id("home")


# zoom functions
    def zoom_in(self, button):
        print ("zoom in")
        cam.zoom_in(zoomscale.get_value())
        presetlist.set_active(-1)


    def zoom_out(self, button):
        print ("zoom out")
        cam.zoom_out(zoomscale.get_value())
        presetlist.set_active(-1)


# preset functions
    def change_preset(self, presetlist):
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


    def empty_entry(self, presetdelbutton):
        if presetdelbutton.get_active():
            presetlist.set_active(-1)
            presetlist.remove(0)
        elif not presetdelbutton.get_active():
            presetlist.insert(0,"home","home")


    def save_preset_icon(self, newpreset, pos, event):
        if newpreset.get_text() == "home":
            cam.setHome()
            presetlist.set_active_id(newpreset.get_text())
            newpreset.set_text("")
        else:
            cam.setPreset(newpreset.get_text())
            presetlist.append(newpreset.get_text(), newpreset.get_text())
            presetlist.set_active_id(newpreset.get_text())
            newpreset.set_text("")


    def save_preset(self, newpreset):
        if newpreset.get_text() == "home":
            cam.setHome()
            presetlist.set_active_id(newpreset.get_text())
            newpreset.set_text("")
        else:
            cam.setPreset(newpreset.get_text())
            presetlist.append(newpreset.get_text(), newpreset.get_text())
            presetlist.set_active_id(newpreset.get_text())
            newpreset.set_text("")


# reset all settings
    def reset(self, button):
        movescale.set_value(0.5)
        zoomscale.set_value(0.5)
        # reset location
        cam.goHome()


# hides/shows the advanced preferences
    def show_pref(self, prefbutton):
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
    def fly_mode(self, flybutton):
        # fly mode turned on
        if flybutton.get_active():
            print ("fly mode turned on")
            button = builder.get_object("left")
            GObject.signal_handlers_destroy(button)
            button.connect("clicked", self.move_left)

            button = builder.get_object("leftup")
            GObject.signal_handlers_destroy(button)
            button.connect("clicked", self.move_leftup)

            button = builder.get_object("leftdown")
            GObject.signal_handlers_destroy(button)
            button.connect("clicked", self.move_leftdown)

            button = builder.get_object("right")
            GObject.signal_handlers_destroy(button)
            button.connect("clicked", self.move_right)

            button = builder.get_object("rightup")
            GObject.signal_handlers_destroy(button)
            button.connect("clicked", self.move_rightup)

            button = builder.get_object("rightdown")
            GObject.signal_handlers_destroy(button)
            button.connect("clicked", self.move_rightdown)

            button = builder.get_object("up")
            GObject.signal_handlers_destroy(button)
            button.connect("clicked", self.move_up)

            button = builder.get_object("down")
            GObject.signal_handlers_destroy(button)
            button.connect("clicked", self.move_down)

            button = builder.get_object("home")
            img = builder.get_object("stopimg")
            GObject.signal_handlers_destroy(button)
            button.set_image(img)
            button.connect("clicked", self.stop_move)

        # fly mode turned off
        else:
            print("fly mode turned off")

            button = builder.get_object("left")
            GObject.signal_handlers_destroy(button)
            button.connect("pressed", self.move_left)
            button.connect("released", self.stop_move)

            button = builder.get_object("leftup")
            GObject.signal_handlers_destroy(button)
            button.connect("pressed", self.move_leftup)
            button.connect("released", self.stop_move)

            button = builder.get_object("leftdown")
            GObject.signal_handlers_destroy(button)
            button.connect("pressed", self.move_leftdown)
            button.connect("released", self.stop_move)

            button = builder.get_object("right")
            GObject.signal_handlers_destroy(button)
            button.connect("pressed", self.move_right)
            button.connect("released", self.stop_move)

            button = builder.get_object("rightup")
            GObject.signal_handlers_destroy(button)
            button.connect("pressed", self.move_rightup)
            button.connect("released", self.stop_move)

            button = builder.get_object("rightdown")
            GObject.signal_handlers_destroy(button)
            button.connect("pressed", self.move_rightdown)
            button.connect("released", self.stop_move)

            button = builder.get_object("up")
            GObject.signal_handlers_destroy(button)
            button.connect("pressed", self.move_up)
            button.connect("released", self.stop_move)

            button = builder.get_object("down")
            GObject.signal_handlers_destroy(button)
            button.connect("pressed", self.move_down)
            button.connect("released", self.stop_move)

            button = builder.get_object("home")
            img = builder.get_object("homeimg")
            GObject.signal_handlers_destroy(button)
            button.set_image(img)
            button.connect("clicked", self.move_home)


    def on_start_recording(self, elem):
        
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


    def on_stop_recording(self, elem, elem2):

        try:
            presetlist.set_active_id(config.get(IDLE_PRESET_KEY, DEFAULT_IDLE_PRESET))
            #  cam.goToPreset(cam.identifyPreset(config.get(IDLE_PRESET_KEY, DEFAULT_IDLE_PRESET)))

        except Exception as e:
            logger.warn("Error accessing the IP camera on recording end. The recording may be incorrect! Error: ", e)
