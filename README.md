# README #

Galicaster plugin to control cameras of visca and onvif protocol.

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
* Make sure you have a working 2.0.x Galicaster installed with all required dependencies (gstreamer, gtk etc.).
* Set up a working Datapath/RTP profile
* clone the git repository to a desired location on your machine:

```
cd ~/path/to/your/location
git clone https://svnset@bitbucket.org/svnset/cameracontrol.git
cd cameracontrol
```
* Copy all relevant files to your Galicaster install like below:
```
cp -r img/ ~/path/to/Galicaster/resources/images/.
cp camctrl.py ~/path/to/Galicaster/galicaster/plugins/.
cp camctrl.css ~/path/to/Galicaster/resources/ui/.
cp camctrl-visca.glade ~/path/to/Galicaster/resources/ui/.
cp camctrl-onvif.glade ~/path/to/Galicaster/resources/ui/.
cp camctrl_onvif_interface.py ~/path/to/Galicaster/galicaster/utils/.

```
* We need to edit our conf.ini to activate the plugin at Galicaster startup, add the following lines to do so:
```
[plugins]
camctrl = True
```
* Now we need to further choose what backend we want to use:
```
[camctrl]
backend = visca
```
* or:
```
[camctrl]
backend = onvif
```
* To use the visca backend, note that we also need to define the port where our visca camera is connected(default port is S0 like below)
```
[camctrl]
port = /dev/ttyS0
```

## Plugin Features ##
### camctrl-visca ###
* 6 programmable presets
* Workflow integration: If you schedule a recording, you are now able to set a desired starting preset (0-5) and the plugin will start recording from it.
* You can also set a preset (0-5) for start and stop in your conf.ini e.g. :
```
[camctrl]
record-preset = 0
idle-preset = 5
```
### camctrl-onvif ###
* infinite number of presets (with proper names like record, idle, desk etc.)
* Workflow integration: If you schedule a recording, you are now able to set a desired starting preset (only normal characters for now, no äöü-_. etc.)
* You can also set a preset (only normal characters for now, no äöü-_. etc.)) for start and stop in your conf.ini e.g. :
```
[camctrl]
record-preset = record
idle-preset = idle
```