#!/usr/bin/env python

## --------------------------------------------------------------- ##
## RECORDING.py
## --------------------------------------------------------------- ##
## Defines a few widgets that record EEG data during a session.
## --------------------------------------------------------------- ##
## TODOs
##
## --------------------------------------------------------------- ##

from .gui import ManagerPanel
import core.ccdl as ccdl
import core.variables as var
import os
import time
import threading 
import wx
import traceback
import numpy as np
import NFT

wildcard = "EEG raw data (*.eeg)|*.eeg|"    \
           "Text File (*.txt)|*.txt|"       \
           "All files (*.*)|*.*"

class TimedSessionRecorder(ManagerPanel):
    """A simple object that just records the data"""
    
    SET_FILENAME = 2001      # ID of the Filename button
    START_RECORDING = 2002   # ID of the Recording button
    ABORT_RECORDING = 2003   # ID of the abort recording button
    EMOSTATE_FIELDS = ("Blink", "LeftWink", "RightWink",
                       "EyesOpen", "LeftEyeLid","RightEyelid")
    
    def __init__(self, parent, manager):
        """Inits a new Timed Session Recoding Panel"""
        ManagerPanel.__init__(self, parent, manager,
                              manager_state=True,
                              monitored_events=(ccdl.HEADSET_FOUND_EVENT,))
        self.manager.add_listener(ccdl.SAMPLING_EVENT,
                                  self.save_sensor_data)
        self.manager.add_listener(ccdl.SENSOR_QUALITY_EVENT,
                                  self.save_sensor_quality_data)
        self.manager.add_listener(ccdl.EMOSTATE_EVENT,
                                  self.save_emostate_data)
        
    def refresh(self, param):
        """Updates the interface when the user is updated"""
        self.update_interface()
    
    
    def create_objects(self):
        """Creates the objects"""
        self.file_open = False
        self._filename = None
        self.file = None
        self.session_duration = 180
        self._time_left = self.session_duration
        self.samples_collected = 0
        self.recording = False
        self.sensor_quality = dict(zip(var.COMPLETE_SENSORS,
                                   [0] * len(var.COMPLETE_SENSORS)))
        self.emostate_data = np.array((0, 6))    
        
        self._filename_lbl = wx.StaticText(self, wx.ID_ANY, "Data file:")
        
        self._file_lbl = wx.StaticText(self, wx.ID_ANY, "[No file]", size=(100, 25), 
                                           style=wx.ALIGN_LEFT|wx.ST_ELLIPSIZE_START|wx.BORDER)
        
        self._file_btn = wx.Button(self, TimedSessionRecorder.SET_FILENAME,
                                   "Set File")

        self._timer_lbl = wx.StaticText(self, wx.ID_ANY, "Session Duration (Mins):",
                                        size=(150, 25))
        
        self._timer_spn = wx.SpinCtrl(self, -1, size=(50,25),
                                        style=wx.SP_VERTICAL)
        
        self._start_btn = wx.Button(self, TimedSessionRecorder.START_RECORDING,
                                    "Start")
        
        self._abort_btn = wx.Button(self, TimedSessionRecorder.ABORT_RECORDING,
                                    "Abort")
        
        self._timeleft_lbl = wx.StaticText(self, wx.ID_ANY, "00:00:00",
                                           size=(200, 80), style=wx.ALIGN_CENTER)
        
        self._timeleft_lbl.SetFont( wx.Font(40, family=wx.FONTFAMILY_DEFAULT,
                                            style=wx.FONTSTYLE_NORMAL, weight=wx.BOLD))
        self._timer_spn.SetRange(1, 100)
        self._timer_spn.SetValue(3)
        
        self.Bind(wx.EVT_SPINCTRL, self.on_spin, self._timer_spn)
        self.Bind(wx.EVT_BUTTON, self.on_start_button, self._start_btn)
        self.Bind(wx.EVT_BUTTON, self.on_abort_button, self._abort_btn)
        self.Bind(wx.EVT_BUTTON, self.on_file_button, self._file_btn)
        
        
    def do_layout(self):
        """Lays out the components"""
        param = wx.StaticBox(self, -1, "Session Parameters")
        parambox= wx.StaticBoxSizer(param, wx.VERTICAL)
        row1 = wx.BoxSizer(wx.HORIZONTAL)
        
        row1.Add(self._filename_lbl, 0, wx.ALL|wx.LEFT, 2)
        row1.Add(self._file_lbl, 1, wx.ALL|wx.CENTER, 2)
        row1.Add(self._file_btn, 0, wx.ALL|wx.RIGHT, 2)
        
        row2 = wx.BoxSizer(wx.HORIZONTAL)
        row2.Add(self._timer_lbl, 0, wx.ALL|wx.LEFT, 2)
        row2.Add(self._timer_spn, 1, wx.ALL|wx.CENTER, 2)
        row2.Add(self._start_btn, 0, wx.ALL|wx.RIGHT, 2)
        
        row3 = wx.BoxSizer(wx.HORIZONTAL)
        row3.Add(self._timeleft_lbl, 1, wx.ALL|wx.EXPAND, 2)
        row3.Add(self._abort_btn, 0, wx.ALL|wx.LEFT, 2)
        
        box1 = wx.BoxSizer(wx.VERTICAL)
        box1.Add(row1, 1, wx.ALL | wx.EXPAND, 10)
        box1.Add(row2, 1, wx.ALL | wx.EXPAND, 10)
  
        parambox.Add(box1, 1, wx.ALL | wx.EXPAND, 2)
        
        box2 = wx.BoxSizer(wx.VERTICAL)
        box2.Add(parambox, 1, wx.ALL | wx.EXPAND, 10)
        box2.Add(row3, 1, wx.ALL|wx.EXPAND, 10)
    
        self.SetSizerAndFit(box2)
        self.update_interface()
    
    def on_spin(self, event):
        """
        Updates the session duration after a user event
        originated from the Spin Control
        """
        self.session_duration = self._timer_spn.GetValue() * 60
        self.time_left = self.session_duration
        
        # Updates the label
        self._timeleft_lbl.SetLabel(self.sec2str(self.time_left))
    
    
    def sec2str(self, num):
        """
        Simple function to transform a number of seconds into
        an equivalent string in the format HH:MM:SS
        """
        h = int(num / (60*60))
        m = int(num / 60)
        s = num % 60
        return "%02d:%02d:%02d" % (h, m, s)
        
    
    def update_interface(self):
        """Updates the interface based on the internal model"""
        self.on_spin(None)
        if self.manager.has_user :  # 'or True' for testing purposes
            self._filename_lbl.Enable()
            self._file_lbl.Enable()
            self._timer_lbl.Enable()
            self._timeleft_lbl.Enable()
            self._timeleft_lbl.Disable()
 
            if self.file_open:
                if self.recording:
                    self._file_btn.Disable()
                    self._timer_spn.Disable()
                    self._start_btn.Disable()
                    self._abort_btn.Enable()
                    self._timeleft_lbl.Enable()
                else:
                    self._file_btn.Enable()
                    self._timer_spn.Enable()
                    self._start_btn.Enable()
                    self._abort_btn.Disable()
                    self._timeleft_lbl.Disable()
            else:
                self._file_btn.Enable()
                self._timer_spn.Enable()
                self._start_btn.Disable()
                self._abort_btn.Disable()
                self._timeleft_lbl.Disable()
        else:
            self._filename_lbl.Disable()
            self._file_lbl.Disable()
            self._file_btn.Disable()
            self._timer_lbl.Disable()
            self._timer_spn.Disable()
            self._start_btn.Disable()
            self._timeleft_lbl.Disable()
            self._abort_btn.Disable()
        
        
    def timer(self):
        """Runs a simple timer that collects data for given time"""
        while self.recording and self.time_left > 0:
            time.sleep(1)   # Sleeps one second
            self.time_left -= 1

        # Stops recording
        self.recording = False

        # When the loop ends, warn the user
        # that session has terminated
        dlg = wx.MessageDialog(self,
                               """%d Samples were saved on file %s""" % (self.samples_collected, self.filename),
                               "Recording Session Terminated",
                               wx.OK | wx.ICON_INFORMATION
                               )
        dlg.ShowModal()
        dlg.Destroy()
        
        # When the user finally responds, updates the interface,
        # resets the counter, closes the files,
        # blocks recording, and resets the samples
        
        self.time_left = self.session_duration
        self.file.close()
        self.file_open = False
        self.filename = None
        self.samples_collected = 0
        self.update_interface()
    
    def on_start_button(self, event):
        """Starts the recording thread"""
        if self.file_open and not self.recording:
            thread = threading.Thread(group=None, target=self.timer)
            self.recording = True
            thread.start()
            NFT.RecordBypass = True
        
            # Updates the interface to reflect current changes in the model
            self.update_interface()
    
    def on_file_button(self, event):
        """
        Opens up a file saving dialog when the "File" button is pressed.
        """
        if NFT.EEGFilename == '':
            dlg = wx.MessageDialog(self,'You have not entered the experiment information yet.  \n\nAre you sure you want to begin a recording anyways?  \n\nPress CANCEL if this was an accidental oversight. \n\nThen, press the ''Start'' button to enter experiment information.  \n\nOtherwise, press ''Ok'' to enter a recording filename.', 'Info', wx.OK|wx.CANCEL|wx.ICON_INFORMATION)
            result = dlg.ShowModal() 
            if result == wx.ID_CANCEL: 
                return
        else: 
            wx.MessageBox('\nThe Experiment Number will automatically be entered into the filename slot.  \n\nAdd the session number to it.', 'Info', wx.OK | wx.ICON_INFORMATION)
        dlg = wx.FileDialog(self, message="Save EEG data as ...",
                            defaultDir=r'\\CCDL_168_01\CCDL Questionnaire Database\RAIN_NFT', defaultFile=NFT.EEGFilename + '_S',
                            wildcard=wildcard, style=wx.SAVE)

        dlg.SetFilterIndex(1)

        # Show the dialog and retrieve the user response. If it is the OK response, 
        # process the data.
        if dlg.ShowModal() == wx.ID_OK:
            fname = dlg.GetPath()
        dlg.Destroy()
        
        # If the filename exists, ask for confirmation
        if os.path.exists( fname ):
            dlg = wx.MessageDialog(self, "File already exists. Overwrite?",
                                   "Potential problem with file",
                                   wx.YES_NO | wx.NO_DEFAULT | wx.ICON_INFORMATION
                                   )

            response = dlg.ShowModal()
            if response == wx.ID_YES:
                self.filename = fname
            elif response == wx.ID_NO:
                self.filename = None
            
        else:
            # If the file does not exists, we can proceed
            self.filename = fname
        NFT.OutputFilename = fname[:-4] + 'MetaData.csv'
        NFT.ExperimentOutputName = fname[:-4] + 'ContRec.csv'
        self.update_interface()
        NFT.CustomName = True
    
    def on_abort_button(self, event):
        """Aborts a recording session by setting the recording flag to false"""
        if self.recording:
            self.recording = False
            
    
    @property
    def filename(self):
        """
        Returns the path of the current file (where data is going
        to be saved)
        """
        return self._filename 
        
        
    @filename.setter
    def filename(self, name):
        """
        Sets the filename propertye
        @param  name  the new path where data is saved
        """
        if name is not None:
            try:
                self.init_file( name )
                self._filename = name
                self._file_lbl.SetLabel(name)
                
            except Exception as e:
                dlg = wx.MessageDialog(self, "%s" % traceback.format_exc(),
                               'Cannot save on file',
                               wx.OK | wx.ICON_INFORMATION
                               #wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION
                               )
                dlg.ShowModal()
                dlg.Destroy()
                
        else:
            self._filename = None
            self.file_open = False
            self._file_lbl.SetLabel("[No file]")
        
            
    @property
    def time_left(self):
        """Returns the amount of time left in this session"""
        return self._time_left
        
    @time_left.setter
    def time_left(self, val):
        """Sets the amount of time left in the current session"""
        self._time_left = val
        self._timeleft_lbl.SetLabel( self.sec2str(self._time_left) )
        
    def init_file(self, name):
        """Inits the file sink"""
        self.file = file(name, "w")
        self.file_open = True
        for channel in var.CHANNELS:
            self.file.write( "%s\t" % var.CHANNEL_NAMES[channel] )
        for sensor in var.COMPLETE_SENSORS:
            self.file.write( "%s_Q\t" % var.SENSOR_NAMES[sensor] )
        for field in self.EMOSTATE_FIELDS[:-1]:
            self.file.write( "%s\t" % field)
        self.file.write( "%s\n" % self.EMOSTATE_FIELDS[-1] )
        
    
    def save_sensor_data(self, data):
        """
        Saves sensory data on a file
        @param data A NumPy SxC array of S samples and C channels
        """
        if self.file_open and self.recording:
            n_samples, n_channels = data.shape
            for s in xrange(n_samples):
                for c in xrange(n_channels):
                    self.file.write("%f\t" % data[s, c])
                for sensor in var.COMPLETE_SENSORS:
                    self.file.write("%d\t" % self.sensor_quality[sensor])
                for field in self.EMOSTATE_FIELDS[0:4]:
                    self.file.write("%d\t" % self.emostate_data[field])
                for field in self.EMOSTATE_FIELDS[4:-1]:
                    self.file.write("%0.3f\t" % self.emostate_data[field].value)
                self.file.write("%0.3f\n" % self.emostate_data[self.EMOSTATE_FIELDS[-1]].value)
            self.samples_collected += n_samples
        
    def save_sensor_quality_data(self, qdata):
        """
        Saves sensor quality data on an inner dictionary
        (the data will be saved by the 'save_sensor_data' loop)
        @param  qdata  the sensor quality data dictionary
        """
        if self.recording:
            self.sensor_quality = qdata
    
    def save_emostate_data(self, edata):
        """Saves emostate data"""
        if self.recording:
            self.emostate_data = edata