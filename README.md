# README #

Galicaster plugins to control cameras of visca and onvif protocol.

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
* Set up a working Datapath profile
* clone the git repository to a desired location on your machine:

```
cd ~/path/to/your/location
git clone https://svnset@bitbucket.org/svnset/cameracontrol.git
cd cameracontrol
```
* Now follow the steps below depending on which plugin you want to install (or both)
### camctrl-visca ###
* Copy all relevant files to your Galicaster install like below:
```
cp -r img/ ~/path/to/Galicaster/resources/images/.
cp cmctrl.css ~/path/to/Galicaster/resources/ui/.
cd cmctrl-visca
cp camctrl-visca.glade ~/path/to/Galicaster/resources/ui/.
cp camctrl-visca.py ~/path/to/Galicaster/galicaster/plugins/.

```
* We need to edit our conf.ini to activate the plugin at Galicaster startup:
* add the following lines to do so:
```
[plugins]
cameractrl-visca = True
[cameractrl-visca]
port = /dev/ttyS0
```
* Note that we need to define the port where the camera is connected (default port is S0 like above)
### camctrl-onvif ###
* Copy all relevant files to your Galicaster install like below:
```
cp -r img/ ~/path/to/Galicaster/resources/images/.
cp cmctrl.css ~/path/to/Galicaster/resources/ui/.
cd cmctrl-onvif
cp camctrl-onvif.glade ~/path/to/Galicaster/resources/ui/.
cp camctrl-onvif.py ~/path/to/Galicaster/galicaster/plugins/.
cp camctrl_onvif_interface.py ~/path/to/Galicaster/galicaster/utils/.

```
* We need to edit our conf.ini to activate the plugin at Galicaster startup:
* add the following lines to do so:
```
[plugins]
cameractrl-visca = True
```
## Plugin Features ##
### camctrl-visca ###
* Workflow integration: If you schedule a recording, you are now able 
### camctrl-onvif ###