"""Copyright (C) 2017  Robin Lachmann

This file is part of the camctrl plugin for Galicaster.

The camctrl plugin is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

The camctrl plugin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with the camctrl plugin. If not, see <http://www.gnu.org/licenses/>."""


import gi

gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, GdkPixbuf, GObject, Pango
from galicaster.core import context
from galicaster.classui import get_ui_path
from galicaster.classui import get_image_path


# DEFAULTS
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
PORT_KEY = "serial-port"

# This is the key specifying the backend (visca or onvif)
BACKEND = 'backend'

# This is the name of this plugin's section in the configuration file
CONFIG_SECTION = "camctrl"

# This are the credentials, which have to be set in the configuration file
IPADDRESS = "ip"
USERNAME = "username"
PASSWORD = "password"
PORT = "port"

# DEFAULt VALUES
DEFAULT_PORT = 80

# VISCA
DEFAULT_MOVESCALE = 7
DEFAULT_BRIGHTNESS = 15
DEFAULT_BRIGHTSCALE = 0
DEFAULT_ZOOM = 0
DEFAULT_ZOOMSCALE = 3.5

# ONVIF
DEFAULT_ZOOMSCALE_ONVIF = 0.5
DEFAULT_MOVESCALE_0NVIF = 0.5


def init():
    global recorder, dispatcher, logger, config, repo

    config = context.get_conf().get_section(CONFIG_SECTION) or {}
    dispatcher = context.get_dispatcher()
    repo = context.get_repository()
    logger = context.get_logger()

    backend = config.get(BACKEND)

    if backend == "onvif":
        global cam
        import galicaster.utils.camctrl_onvif_interface as camera
        # connect to the camera
        ip = config.get(IPADDRESS)
        username = config.get(USERNAME)
        password = config.get(PASSWORD)
        if config.get(PORT) is None:
            port = DEFAULT_PORT
        else:
            port = config.get(PORT)
        cam = camera.AXIS_V5915()
        cam.connect(ip, port, username, password)
        # initiate the onvif user interface
        dispatcher.connect("init", init_onvif_ui)

    elif backend == "visca":
        global pysca 
        import galicaster.utils.pysca as pysca
        # If port is not defined, a None value will make this method fail
        pysca.connect(config.get(PORT_KEY))
        # initiate the visca user interface
        dispatcher.connect("init", init_visca_ui)
    else:
        logger.warn("WARNING: You have to choose a backend in the config file before starting Galicaster, otherwise the cameracontrol plugin does not work.")
        raise RuntimeError("No backend for the cameracontrol plugin defined.") 
    logger.info("Camera connected.")


# VISCA USER INTERFACE
def init_visca_ui(element):
    global recorder_ui, builder

    # init function classes
    visca = visca_interface()

    dispatcher.connect('recorder-starting', visca.on_start_recording)
    dispatcher.connect('recorder-stopped', visca.on_stop_recording)

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

    # scaling of images/labels that do not get called at all
    # scale images
    imgs = ["ctrl", "zoom", "bright", "dummy", "settings"]
    for i in imgs:
        get_stock_icon(i)

    # scale label
    labels = ["control", "settings", "1", "2", "3", "4", "5", "6", "on", "off"]
    for i in labels:
        get_label(i)

    # add new settings tab to the notebook
    notebook = recorder_ui.get_object("data_panel")
    mainbox = builder.get_object("mainbox")
    notebook.append_page(mainbox, get_label("notebook"))

    # object lists
    movement = ["left", "leftup", "leftdown", "right", "rightup", "rightdown", "up", "down", "fly_mode"]
    zoom = ["zoom_in", "zoom_out"]
    scales = ["bright", "move", "zoom"]
    others = ["on", "off", "reset", "show_pref", "home"]
    
    # object initialisation
    # preset buttons
    presetbutton = builder.get_object("preset")
    presetbutton.add(get_stock_icon("preset"))
    for i in [ str(x) for x in range(1,7)]:
        button = builder.get_object(i)
        button.connect("clicked", str_to_module("visca_interface", "preset" + i), presetbutton)

    # scales and movement/zoom buttons
    for i in scales:
        scale = builder.get_object(i + "scale")
        scalelabel = get_label(i)
        scalelabel.set_text(str(int(scale.get_value())))

        if i == "bright":
            scale.connect("value-changed", visca.set_bright, scalelabel)
        else:
            scale.connect("value-changed", visca.set_scale, scalelabel)
            if i == "move":
                # movement buttons
                for i in movement:
                    button = builder.get_object(i)
                    if i == "fly_mode":
                        button.add(get_stock_icon(i))
                        button.connect("clicked", str_to_module("visca_interface", i), scale)
                    else:
                        button.add(get_icon(i))
                        button.connect("pressed", str_to_module("visca_interface", "move_" + i), scale)
                        button.connect("released", visca.stop_move)
            elif i == "zoom":
                # zoom buttons
                for i in zoom:
                    button = builder.get_object(i)
                    button.add(get_stock_icon(i))
                    button.connect("pressed", str_to_module("visca_interface", i), scale)
                    button.connect("released", visca.stop_zoom)

    # other buttons
    for i in others:
        button = builder.get_object(i)
        if i == "home":
            button.add(get_icon(i))
            button.connect("clicked", str_to_module("visca_interface", "move_" + i))
        elif i == "on" or i == "off":
            button.connect("clicked", str_to_module("visca_interface", "turn_" + i))
        elif i == "show_pref":
            button.connect("clicked", str_to_module("visca_interface", i))
        else:
            button.add(get_stock_icon(i))
            button.connect("clicked", str_to_module("visca_interface", i))


# ONVIF USER INTERFACE
def init_onvif_ui(element):
    global recorder_ui, builder
    
    # init function classes
    onvif = onvif_interface()

    dispatcher.connect("recorder-starting", onvif.on_start_recording)
    dispatcher.connect("recorder-stopped", onvif.on_stop_recording)

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

    # scaling of images/labels which do not get called at all
    # scale images
    imgs = ["ctrl", "zoom", "dummy", "settings"]
    for i in imgs:
        get_stock_icon(i)
    # scale label
    labels = ["control", "settings"]
    for i in labels:
        get_label(i)

    # add new settings tab to the notebook
    notebook = recorder_ui.get_object("data_panel")
    mainbox = builder.get_object("mainbox")
    notebook.append_page(mainbox, get_label("notebook"))

    # object lists
    movement = ["left", "leftup", "leftdown", "right", "rightup", "rightdown", "up", "down", "fly_mode"]
    zoom = ["zoom_in", "zoom_out"]
    scales = ["move", "zoom"]
    others = ["reset", "show_pref", "home"]
    
    # object initialisation
    # presets
    # note: preset objects have to be initialized individually
    # preset list
    presetlist = builder.get_object("preset_list")
    # add home position to list
    presetlist.insert(0, "home", "home")
    # fill the list with current presets
    for preset in cam.get_presets():
        presetlist.append(preset.Name, preset.Name)

    # preset buttons
    # to set a new preset
    newpreset = builder.get_object("newpreset")

    # to delete a preset
    presetdelbutton = builder.get_object("presetdel")
    presetdelbutton.add(get_stock_icon("presetdel"))

    # connect preset functions
    presetlist.connect("changed", onvif.change_preset, newpreset, presetdelbutton)
    newpreset.connect("activate", onvif.save_preset, presetlist)
    newpreset.connect("icon-press", onvif.save_preset_icon, presetlist)
    presetdelbutton.connect("clicked", onvif.empty_entry, presetlist)

    # scales and movement/zoom buttons
    for i in scales:
        scale = builder.get_object(i + "scale")
        scalelabel = get_label(i)
        scalelabel.set_text("{0:.1f}".format(scale.get_value()))
        scale.connect("value-changed", onvif.set_scale, scalelabel)
        if i == "move":
            # movement buttons
            for i in movement:
                button = builder.get_object(i)
                if i == "fly_mode":
                    button.add(get_stock_icon(i))
                    button.connect("clicked", str_to_module("onvif_interface", i), scale, presetlist)
                else:
                    button.add(get_icon(i))
                    button.connect("pressed", str_to_module("onvif_interface", "move_" + i), scale, presetlist)
                    button.connect("released", onvif.stop_move)
                    button.connect("released", onvif.stop_move)

        elif i == "zoom":
            # zoom buttons
            for i in zoom:
                button = builder.get_object(i)
                button.add(get_stock_icon(i))
                button.connect("pressed", str_to_module("onvif_interface", i), scale, presetlist)
                button.connect("released", onvif.stop_move)

    # other buttons
    for i in others:
        button = builder.get_object(i)
        if i == "home":
            button.add(get_icon(i))
            button.connect("clicked", str_to_module("onvif_interface", "move_" + i), presetlist)
        elif i == "show_pref":
            button.connect("clicked", str_to_module("onvif_interface", i))
        else:
            button.add(get_stock_icon(i))
            button.connect("clicked", str_to_module("onvif_interface", i))


# visca function interface
class visca_interface():
    #  import galicaster.utils.pysca as pysca
    # movement functions
    def move_left(self, button, scale):
        logger.debug("I move left")
        pysca.pan_tilt(DEFAULT_DEVICE, pan=-int(scale.get_value()))

    def move_leftup(self, button, scale):
        logger.debug("I move leftup")
        pysca.pan_tilt(DEFAULT_DEVICE, pan=-int(scale.get_value()), tilt=int(scale.get_value()))

    def move_leftdown(self, button, scale):
        logger.debug("I move leftdown")
        pysca.pan_tilt(DEFAULT_DEVICE, pan=-int(scale.get_value()), tilt=-int(scale.get_value()))

    def move_right(self, button, scale):
        logger.debug("I move right")
        pysca.pan_tilt(DEFAULT_DEVICE, pan=int(scale.get_value()))

    def move_rightup(self, button, scale):
        logger.debug("I move rightup")
        pysca.pan_tilt(DEFAULT_DEVICE, pan=int(scale.get_value()), tilt=int(scale.get_value()))

    def move_rightdown(self, button, scale):
        logger.debug("I move rightdown")
        pysca.pan_tilt(DEFAULT_DEVICE, pan=int(scale.get_value()), tilt=-int(scale.get_value()))

    def move_up(self, button, scale):
        logger.debug("I move up")
        pysca.pan_tilt(DEFAULT_DEVICE, tilt=int(scale.get_value()))

    def move_down(self, button, scale):
        logger.debug("I move down")
        pysca.pan_tilt(DEFAULT_DEVICE, tilt=-int(scale.get_value()))

    def stop_move(self, button):
        logger.debug("I make a break")
        pysca.pan_tilt(DEFAULT_DEVICE, pan=0, tilt=0)

    def move_home(self, button):
        logger.debug("I move home")
        pysca.pan_tilt_home(DEFAULT_DEVICE)

    # zoom functions
    def zoom_in(self, button, scale):
        logger.debug("zoom in")
        pysca.zoom(DEFAULT_DEVICE, pysca.ZOOM_ACTION_TELE, speed=int(scale.get_value()))

    def zoom_out(self, button, scale):
        logger.debug("zoom out")
        pysca.zoom(DEFAULT_DEVICE, pysca.ZOOM_ACTION_WIDE, speed=int(scale.get_value()))

    def stop_zoom(self, button):
        logger.debug("stop zoom")
        pysca.zoom(DEFAULT_DEVICE, pysca.ZOOM_ACTION_STOP)

    # preset functions
    def preset1(self, button, presetbutton):
        if presetbutton.get_active():
            pysca.set_memory(DEFAULT_DEVICE, 0)
            presetbutton.set_active(False)
        else:
            pysca.recall_memory(DEFAULT_DEVICE, 0)

    def preset2(self, button, presetbutton):
        if presetbutton.get_active():
            pysca.set_memory(DEFAULT_DEVICE, 1)
            presetbutton.set_active(False)
        else:
            pysca.recall_memory(DEFAULT_DEVICE, 1)

    def preset3(self, button, presetbutton):
        if presetbutton.get_active():
            pysca.set_memory(DEFAULT_DEVICE, 2)
            presetbutton.set_active(False)
        else:
            pysca.recall_memory(DEFAULT_DEVICE, 2)

    def preset4(self, button, presetbutton):
        if presetbutton.get_active():
            pysca.set_memory(DEFAULT_DEVICE, 3)
            presetbutton.set_active(False)
        else:
            pysca.recall_memory(DEFAULT_DEVICE, 3)

    def preset5(self, button, presetbutton):
        if presetbutton.get_active():
            pysca.set_memory(DEFAULT_DEVICE, 4)
            presetbutton.set_active(False)
        else:
            pysca.recall_memory(DEFAULT_DEVICE, 4)

    def preset6(self, button, presetbutton):
        if presetbutton.get_active():
            pysca.set_memory(DEFAULT_DEVICE, 5)
            presetbutton.set_active(False)
        else:
            pysca.recall_memory(DEFAULT_DEVICE, 5)

    # brightness scale
    def set_bright(self, scale, scalelabel):
        scalelabel.set_text(str(int(scale.get_value())))
        pysca.set_ae_mode(DEFAULT_DEVICE, pysca.AUTO_EXPOSURE_BRIGHT_MODE)
        pysca.set_brightness(DEFAULT_DEVICE, int(scale.get_value()) + DEFAULT_BRIGHTNESS)

    def set_scale(self, scale, scalelabel):
        scalelabel.set_text(str(int(scale.get_value())))

    # reset all settings
    def reset(self, button):
        # reset brightness
        pysca.set_ae_mode(DEFAULT_DEVICE, pysca.AUTO_EXPOSURE_BRIGHT_MODE)
        pysca.set_brightness(DEFAULT_DEVICE, DEFAULT_BRIGHTNESS)
        # reset zoom
        pysca.set_zoom(DEFAULT_DEVICE, DEFAULT_ZOOM)
        # reset location
        pysca.pan_tilt_home(DEFAULT_DEVICE)
        # reset scales
        builder.get_object("brightscale").set_value(DEFAULT_BRIGHTSCALE)
        builder.get_object("movescale").set_value(DEFAULT_MOVESCALE)
        builder.get_object("zoomscale").set_value(DEFAULT_ZOOMSCALE)

    # turns the camera on/off
    def turn_on(self, button):
        pysca.set_power_on(DEFAULT_DEVICE, True)

    def turn_off(self, button):
        pysca.set_power_on(DEFAULT_DEVICE, False)

    # hides/shows the advanced preferences
    def show_pref(self, button):
        scaleboxes = ["scales1", "scales2", "scales3"]
        for i in scaleboxes:
            scalebox = builder.get_object(i)
            if scalebox.get_property("visible"):
                scalebox.hide()
            else:
                scalebox.show()

    # flymode activation connects clicked signal and disconnects
    # pressed/released to enable continuous movement
    def fly_mode(self, button, scale):
        # objects relevant for fly mode
        tochange = ["left", "leftup", "leftdown", "right", "rightup", "rightdown", "up", "down", "home"]

        # fly mode turned on
        if button.get_active():
            logger.debug("fly mode turned on")
            

            for i in tochange:
                button = builder.get_object(i)
                GObject.signal_handlers_destroy(button)
                if i == "home":
                    button.set_image(get_stock_icon("stop"))
                    button.connect("clicked", self.stop_move)
                else:
                    button.connect("clicked", str_to_module("visca_interface", "move_" + i), scale)
        # fly mode turned off
        else:
            logger.debug("fly mode turned off")

            for i in tochange:
                button = builder.get_object(i)
                GObject.signal_handlers_destroy(button)
                if i == "home":
                    button.set_image(get_icon("home"))
                    button.connect("clicked", self.move_home)
                else:
                    button.connect("pressed", str_to_module("visca_interface", "move_" + i), scale)
                    button.connect("released", self.stop_move)

    def on_start_recording(self, elem):

        preset = config.get(RECORD_PRESET_KEY, DEFAULT_RECORD_PRESET_INT)
        mp = repo.get_next_mediapackage()

        if mp is not None:
            try:
                properties = mp.getOCCaptureAgentProperties()
                preset = int(properties['org.opencastproject.workflow.config.cameraPreset'])
            except Exception as e:
                logger.warn("Error loading the preset from the OC properties! Error:", e)

        try:
            pysca.set_power_on(DEFAULT_DEVICE, True, )
            builder.get_object("on-off").set_active(True)
            pysca.recall_memory(DEFAULT_DEVICE, (preset))

        except Exception as e:
            logger.warn("Error accessing the Visca device %u on recording start. The recording may be incorrect! Error: %s" % (DEFAULT_DEVICE, e))

    def on_stop_recording(self, elem, elem2):

        try:
            pysca.recall_memory(DEFAULT_DEVICE, config.get(IDLE_PRESET_KEY, DEFAULT_IDLE_PRESET_INT))
            pysca.set_power_on(DEFAULT_DEVICE, False)
            builder.get_object("on-off").set_active(False)

        except Exception as e:
            logger.warn("Error accessing the Visca device %u on recording end. The recording may be incorrect! Error: %s" % (DEFAULT_DEVICE, e))


# onvif function interface
class onvif_interface():

    # movement functions
    def move_left(self, button, scale, presetlist):
        logger.debug("I move left")
        cam.go_left(float("{0:.1f}".format(scale.get_value())))
        presetlist.set_active(-1)

    def move_leftup(self, button, scale, presetlist):
        logger.debug("I move leftup")
        cam.go_left_up(float("{0:.1f}".format(scale.get_value())))
        presetlist.set_active(-1)

    def move_leftdown(self, button, scale, presetlist):
        logger.debug("I move leftdown")
        cam.go_left_down(float("{0:.1f}".format(scale.get_value())))
        presetlist.set_active(-1)

    def move_right(self, button, scale, presetlist):
        logger.debug("I move right")
        cam.go_right(float("{0:.1f}".format(scale.get_value())))
        presetlist.set_active(-1)

    def move_rightup(self, button, scale, presetlist):
        logger.debug("I move rightup")
        cam.go_right_up(float("{0:.1f}".format(scale.get_value())))
        presetlist.set_active(-1)

    def move_rightdown(self, button, scale, presetlist):
        logger.debug("I move rightdown")
        cam.go_right_down(float("{0:.1f}".format(scale.get_value())))
        presetlist.set_active(-1)

    def move_up(self, button, scale, presetlist):
        logger.debug("I move up")
        cam.go_up(float("{0:.1f}".format(scale.get_value())))
        presetlist.set_active(-1)

    def move_down(self, button, scale, presetlist):
        logger.debug("I move down")
        cam.go_down(float("{0:.1f}".format(scale.get_value())))
        presetlist.set_active(-1)

    def stop_move(self, button):
        logger.debug("I make a break")
        cam.stop()

    def move_home(self, button, presetlist):
        logger.debug("I move home")
        presetlist.set_active_id("home")

    # zoom functions
    def zoom_in(self, button, scale, presetlist):
        logger.debug("zoom in")
        cam.zoom_in(float("{0:.1f}".format(scale.get_value())))
        presetlist.set_active(-1)

    def zoom_out(self, button, scale, presetlist):
        logger.debug("zoom out")
        cam.zoom_out(float("{0:.1f}".format(scale.get_value())))
        presetlist.set_active(-1)

    # preset functions
    def change_preset(self, presetlist, newpreset, presetdelbutton):
        if len(newpreset.get_text()) > 0:
            if newpreset.get_text() == "home":
                logger.debug("New Home set to current position.")
            else:
                logger.debug("New Preset saved: %s", newpreset.get_text())
        elif presetlist.get_active_text() == "home":
            logger.debug("Going Home")
            cam.go_home()
        else:
            if presetdelbutton.get_active() and not presetlist.get_active_text() is None:
                cam.remove_preset(cam.identify_preset(presetlist.get_active_text()))
                presetdelbutton.set_active(False)
                presetlist.remove(presetlist.get_active())
                
            else:
                if not presetlist.get_active_text() is None:
                    logger.debug("Going to: " + presetlist.get_active_text())
                    cam.go_to_preset(cam.identify_preset(presetlist.get_active_text()))

    def empty_entry(self, presetdelbutton, presetlist):
        if presetdelbutton.get_active():
            presetlist.set_active(-1)
            presetlist.remove(0)
        elif not presetdelbutton.get_active():
            presetlist.insert(0, "home", "home")

    def save_preset_icon(self, newpreset, pos, event, presetlist):
        if newpreset.get_text() == "home":
            cam.set_home()
            presetlist.set_active_id(newpreset.get_text())
            newpreset.set_text("")
        else:
            cam.set_preset(newpreset.get_text())
            presetlist.append(newpreset.get_text(), newpreset.get_text())
            presetlist.set_active_id(newpreset.get_text())
            newpreset.set_text("")

    def save_preset(self, newpreset, presetlist):
        if newpreset.get_text() == "home":
            cam.set_home()
            presetlist.set_active_id(newpreset.get_text())
            newpreset.set_text("")
        else:
            cam.set_preset(newpreset.get_text())
            presetlist.append(newpreset.get_text(), newpreset.get_text())
            presetlist.set_active_id(newpreset.get_text())
            newpreset.set_text("")

    # reset all settings
    def reset(self, button):
        # reset scales
        builder.get_object("movescale").set_value(DEFAULT_MOVESCALE_0NVIF)
        builder.get_object("zoomscale").set_value(DEFAULT_ZOOMSCALE_ONVIF)
        # reset location
        cam.go_home()

    def set_scale(self, scale, scalelabel):
        scalelabel.set_text("{0:.1f}".format(scale.get_value()))

    # hides/shows the advanced preferences
    def show_pref(self, button):
        scaleboxes = ["scales1", "scales2"]
        for i in scaleboxes:
            scalebox = builder.get_object(i)
            if scalebox.get_property("visible"):
                scalebox.hide()
            else:
                scalebox.show()

    # flymode activation connects clicked signal and disconnects
    # pressed/released to enable continuous movement
    def fly_mode(self, button, scale, presetlist):
        # objects relevant for fly mode
        tochange = ["left", "leftup", "leftdown", "right", "rightup", "rightdown", "up", "down", "home"]

        # fly mode turned on
        if button.get_active():
            logger.debug("fly mode turned on")

            for i in tochange:
                button = builder.get_object(i)
                GObject.signal_handlers_destroy(button)
                if i == "home":
                    button.set_image(get_stock_icon("stop"))
                    button.connect("clicked", self.stop_move)
                else:
                    button.connect("clicked", str_to_module("onvif_interface", "move_" + i), scale, presetlist)

        # fly mode turned off
        else:
            logger.debug("fly mode turned off")

            for i in tochange:
                button = builder.get_object(i)
                GObject.signal_handlers_destroy(button)
                if i == "home":
                    button.set_image(get_icon("home"))
                    button.connect("clicked", self.move_home)
                else:
                    button.connect("pressed", str_to_module("onvif_interface", "move_" + i), scale, presetlist)
                    button.connect("released", self.stop_move)

    def on_start_recording(self, elem):
        preset = config.get(RECORD_PRESET_KEY, DEFAULT_RECORD_PRESET)
        mp = repo.get_next_mediapackage()

        if mp is not None:
                try:
                    properties = mp.getOCCaptureAgentProperties()
                    preset = properties['org.opencastproject.workflow.config.cameraPreset']
                except Exception as e:
                    logger.warn("Error loading a preset from the OC properties! Error:", e)

        try:
            builder.get_object("presetlist").set_active_id(preset)
            #  cam.goToPreset(cam.identifyPreset(preset))

        except Exception as e:
            logger.warn("Error accessing the IP camera on recording start. The recording may be incorrect! Error:", e)

    def on_stop_recording(self, elem, elem2):

        try:
            builder.get_object("presetlist").set_active_id(config.get(IDLE_PRESET_KEY, DEFAULT_IDLE_PRESET))
            #  cam.goToPreset(cam.identifyPreset(config.get(IDLE_PRESET_KEY, DEFAULT_IDLE_PRESET)))

        except Exception as e:
            logger.warn("Error accessing the IP camera on recording end. The recording may be incorrect! Error: ", e)


# utility functions for scaling and other advanced funtionality
# get the current window resolution
def get_res():
    # calculate resolution for scaling
    window_size = context.get_mainwindow().get_size()
    res = window_size[0]/1920.0
    return res

# get custom icons and scale them
def get_icon(imgname):
    size = get_res() * 56
    pix = GdkPixbuf.Pixbuf.new_from_file_at_size(get_image_path("camctrl-images/"+imgname+".svg"), size, size)
    img = Gtk.Image.new_from_pixbuf(pix)
    img.show()
    return img

# get stock icons and scale them
def get_stock_icon(imgname):
    size = get_res() * 28
    if imgname == "stop":
        size = get_res() * 56
    img = builder.get_object(imgname+"img")
    img.set_pixel_size(size)
    img.show()
    return img
# get labels and scale them
def get_label(labelname):
    label = builder.get_object(labelname+"_label")
    size = get_res() * 18
    if labelname == "settings" \
       or labelname == "control":
        size = get_res() * 20
    elif labelname == "notebook":
        size = get_res() * 20
        label.set_property("ypad",10)
        #  label.set_property("xpad",5)
        #  label.set_property("vexpand-set",True)
        #  label.set_property("vexpand",True)
    elif labelname == "bright" or \
            labelname == "move" or \
            labelname == "zoom":
        size = get_res() * 14
    label.set_use_markup(True)
    label.modify_font(Pango.FontDescription(str(size)))
    return label

# to refer a function by string
# to call the object use str_to_module(module, func)()
def str_to_module(module, func):
    return getattr(globals()[module](), func)
