from onvif import ONVIFCamera
import os
# For testing purposes
ip = '134.95.128.120'
username = "root"
password = "opencast"


'''
Before using make sure onvif is installed and set the path from #1 to the correct wsdl folder
Now you can test the class and move the camera in cameratest.py
If connection gets bad request, check cameras date and time settings and make sure it has the same time as
the operating machine.
'''

class AXIS_V5915():
    # Connection to the onvif protocol with credentials
    def connect(self, ip, username, password):
        global ptz, img
        # Connect to ONVIF camera
        print ('IP camera initialization...')
        if os.path.exists('/etc/onvif/wsdl'):
            path = '/etc/onvif/wsdl'
        else:
            path = '/home/rl/.local/wsdl'
        mycam = ONVIFCamera(ip, 80, username, password, path) #1
        host = mycam.devicemgmt.GetHostname()
        print ('  Connected to ONVIF camera ' + str(host.Name))
        #print(mycam.devicemgmt.GetCapabilities())
        #print(mycam.devicemgmt.GetServices())
     
        
        # Create media service object
        print ('  Creating media service...')
        media = mycam.create_media_service()
        print ('  Creating media service... Done.')
        # IMPORTANT!
        # Get media profile (first element if we don't have multiple profiles)
        media_profiles = media.GetProfiles()
        #print(media_profiles)
        media_profile_h264 = media_profiles[0]
        media_profile_jpg = media_profiles[1]

        # Get video sources
        video_source = media.GetVideoSources()[0]
        
        #print(media.GetVideoSourceConfigurations())
        #print(media.GetVideoSources())
        #print(media.GetVideoSourceConfigurationOptions())
        
        # We need the profile token
        token = media_profile_h264._token

        # PTZ
        # Create ptz service object
        print ('  Creating PTZ service...')
        ptz = mycam.create_ptz_service()
        #  print(ptz.GetConfigurations())
        #  print(ptz.GetServiceCapabilities())
        print ('  Creating PTZ service... Done.')

        #return
        # Next we want to automatically define all functions, in requesting those from the ptz-service
        self.define_requests(token)

    def define_requests(self, token):
        print('  Defining requests...')
        global req_move, req_stop, req_set_preset, req_remove_preset, \
            req_get_presets, req_goto_preset, req_set_home, req_goto_home

        req_move = ptz.create_type('ContinuousMove')
        req_move.ProfileToken = token

        req_stop = ptz.create_type('Stop')
        req_stop.ProfileToken = token

        req_set_preset = ptz.create_type('SetPreset')
        req_set_preset.ProfileToken = token

        req_remove_preset = ptz.create_type("RemovePreset")
        req_remove_preset.ProfileToken = token

        req_get_presets = ptz.create_type("GetPresets")
        req_get_presets.ProfileToken = token

        req_goto_preset = ptz.create_type('GotoPreset')
        req_goto_preset.ProfileToken = token

        req_set_home = ptz.create_type('SetHomePosition')
        req_set_home.ProfileToken = token

        req_goto_home = ptz.create_type('GotoHomePosition')
        req_goto_home.ProfileToken = token

        # req_focus = img.create_type('Move')
        # req_focus.ProfileToken = token
        #
        # req_imaging = img.create_type('SetImagingSettings')
        # req_imaging.ProfileToken = token
        #
        # req_stopfocus = img.create_type('Stop')
        # req_stopfocus.ProfileToken = token
        print('  Defining requests... Done.')
        print('Ip camera initialization... Done.')
    # ptz functionality

    # stop all current and pending ptz actions
    def stop(self):
        req_stop.PanTilt = True
        req_stop.Zoom = True
        ptz.Stop(req_stop)

    # Absolute and relative movment cannot be implemented, so all movement is done with continuous movement

    # Continuous movement for x seconds
    def goLeft(self, speed):
        self.stop()
        req_move.Velocity.Zoom._x = 0.0
        req_move.Velocity.PanTilt._x = -speed
        req_move.Velocity.PanTilt._y = 0.0
        ptz.ContinuousMove(req_move)

    def goRight(self, speed):
        self.stop()
        req_move.Velocity.Zoom._x = 0.0
        req_move.Velocity.PanTilt._x = speed
        req_move.Velocity.PanTilt._y = 0.0
        ptz.ContinuousMove(req_move)

    def goDown(self, speed):
        self.stop()
        req_move.Velocity.Zoom._x = 0.0
        req_move.Velocity.PanTilt._x = 0.0
        req_move.Velocity.PanTilt._y = -speed
        ptz.ContinuousMove(req_move)

    def goUp(self, speed):
        self.stop()
        req_move.Velocity.Zoom._x = 0.0
        req_move.Velocity.PanTilt._x = 0.0
        req_move.Velocity.PanTilt._y = speed
        ptz.ContinuousMove(req_move)

    def goRightUp(self, speed):
        self.stop()
        req_move.Velocity.Zoom._x = 0.0
        req_move.Velocity.PanTilt._x = speed
        req_move.Velocity.PanTilt._y = speed
        ptz.ContinuousMove(req_move)

    def goLeftUp(self, speed):
        self.stop()
        req_move.Velocity.Zoom._x = 0.0
        req_move.Velocity.PanTilt._x = -speed
        req_move.Velocity.PanTilt._y = speed
        ptz.ContinuousMove(req_move)

    def goRightDown(self, speed):
        self.stop()
        req_move.Velocity.Zoom._x = 0.0
        req_move.Velocity.PanTilt._x = speed
        req_move.Velocity.PanTilt._y = -speed
        ptz.ContinuousMove(req_move)

    def goLeftDown(self, speed):
        self.stop()
        req_move.Velocity.Zoom._x = 0.0
        req_move.Velocity.PanTilt._x = -speed
        req_move.Velocity.PanTilt._y = -speed
        ptz.ContinuousMove(req_move)


    # presets and home
    # Go to home preset
    def goHome(self):
        ptz.GotoHomePosition(req_goto_home)

    #Sets current Position to the new home preset
    def setHome(self):
        ptz.SetHomePosition(req_set_home)

    # Changes current Camera Position to a preset by its number (use identifyPreset to go by name)
    def goToPreset(self, number):
        req_goto_preset.PresetToken = number
        ptz.GotoPreset(req_goto_preset)
        print ('Going to Preset ', number)

    # Sets the current Camera Position to a new Preset, with the "name" attribute
    # setPreset takes the next free available number, starting with "2"
    def setPreset(self, name):
        self.stop()
        req_set_preset.PresetName = name
        preset = ptz.SetPreset(req_set_preset)
        print ('Current Position set to Preset ', preset)

    # Remove a preset by its number (use identifyPreset to delete by name)
    def removePreset(self, number):
        req_remove_preset.PresetToken = number
        ptz.RemovePreset(req_remove_preset)
        print ('Removed Preset ', number)

    # Get a list of all present presets except for preset number 1 which is home
    def getPresets(self):
        PresetList = ptz.GetPresets(req_get_presets)
        return PresetList

    # Identify a preset by it's "name" or "number" (not both)
    # returns either the presets name or number, returns none if both or none is given
    def identifyPreset(self, name=None, number=None):
        if (name is None and number is None) or (name and number is not None):
            print("Name or number must be given to identify a preset.")
            return None
        else:
            if name is not None:
                for preset in ptz.GetPresets(req_get_presets):
                    if preset.Name == name:
                        number = preset._token
                        return number
            else:
                for preset in ptz.GetPresets(req_get_presets):
                    if preset._token == number:
                        name = preset.Name
                        return name

    # zoom
    def zoom_in(self, speed):
        self.stop()
        req_move.Velocity.PanTilt._x = 0.0
        req_move.Velocity.PanTilt._y = 0.0
        req_move.Velocity.Zoom._x = speed
        ptz.ContinuousMove(req_move)

    def zoom_out(self, speed):
        self.stop()
        req_move.Velocity.PanTilt._x = 0.0
        req_move.Velocity.PanTilt._y = 0.0
        req_move.Velocity.Zoom._x = -speed
        ptz.ContinuousMove(req_move)


