# README #

Galicaster plugin to control PTZ cameras compatible with VISCA and ONVIF protocols.

## Requirements ##
### camctrl-visca ###
* pysca
* python-serial
* Galicaster 2.0.x
### camctrl-onvif ###
* python-onvif
* Galicaster 2.0.x


## Installation ##
### General ###
* Make sure you have a working Galicaster 2.0.x installed with all required dependencies (Gstreamer, GTK, etc.).
* Clone the git repository to a desired location on your machine:

        :::sh
        git clone https://bitbucket.org/uni-koeln/cameracontrol.git
        cd cameracontrol

* Copy all relevant files to your Galicaster install like below:

        :::sh
        cp -r camctrl-images/ $GALICASTER/resources/images/.
        cp camctrl.py $GALICASTER/galicaster/plugins/.
        cp camctrl.css $GALICASTER/resources/ui/.
        cp camctrl-visca.glade $GALICASTER/resources/ui/.
        cp camctrl-onvif.glade $GALICASTER/resources/ui/.
        cp camctrl_onvif_interface.py $GALICASTER/galicaster/utils/.

    , where `$GALICASTER` represents the location Galicaster within the system. If you used the official packages, that should be in `/usr/share/galicaster`

* Edit your `conf.ini` file (`/etc/galicaster/conf.ini` if installed from the official .deb package) to activate the plugin:

        [plugins]
        camctrl = True

* Now we need to choose what backend we want to use:

        [camctrl]
        backend = visca

    or:

        [camctrl]
        backend = onvif

* To use the VISCA backend, note that we also need to define the port where our VISCA camera is connected (default port is S0 like below)

        [camctrl]
        backend = visca
        port = /dev/ttyS0

* To use the ONVIF backend, it is important that we also define the credentials to connect to the SOAP-Service. Port is optional, if none set it will default to 80. (IMPORTANT: Galicaster will freeze if you set the wrong port, you will get no feedback or error message due to an internal bug in the python-onvif implementation. So make sure the port you provide is not blocked.)

        [camctrl]
        ip = <yourcameraip>
        username = <yourusername>
        password = <yourpass> 
        port = 80

## Plugin Features ##
### camctrl-visca ###
* You can configure the plugin to call a certain preset before recording (`record-preset`) and also after finishing a recording (`idle-preset`). Presets go from 0 to 5, which correspond to the presets 1-6 defined by VISCA. A sample configuration in Galicaster's `conf.ini` file is:

        [camctrl]
        backend = visca
        serial-port = /dev/ttyS0
        record-preset = 0
        idle-preset = 5

### camctrl-onvif ###
* Infinite number of presets with full names like "record", "idle", "desk", etc. 
    * Preset names may consist of alphanumerical characters only. Punctuation characters (like "-" or ".") and non-English characters (like "ä", "é" or "ñ") are not yet allowed.
* You can configure the plugin to call a certain preset before recording (`record-preset`) and also after finishing a recording (`idle-preset`). For instance:

        [camctrl]
        backend = onvif
        record-preset = record
        idle-preset = idle
