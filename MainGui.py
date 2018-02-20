import importlib
import OpenBCIHardwareInterface as BciHwInter
import CCDLUtil.EEGInterface.EEG_INDEX
import CCDLUtil.EEGInterface.EEGInterface
from CCDLUtil.Utility.Decorators import threaded
import wx
import os
import time
import threading
import NFT
import sys
import scipy as sp
import numpy as np
import scipy.signal as sig
from scipy.stats import linregress
import random
import numpy.random as rnd
import matplotlib.pyplot as plt
import serial
from scipy.signal import butter, lfilter

fs = 250.0  #Sampling rate
lowcut = 0.5 #The lowest frequency you want in Hz
highcut = 50.0 #The highest frequency you want in Hz
order  = 2  #The order of the filter

Values = np.genfromtxt(r'\\CCDL-RESOURCEPC\Users\CCDL\Documents\CCDL Experiment Resources\Experiment Resources\RAIN_SubjControlFile\ThetaRatio.csv', delimiter=',')
ValuesIndex = Values[:,0]


def ask(parent=None, message='', default_value=''):
        dlg = wx.TextEntryDialog(parent, message, defaultValue=default_value)
        dlg.ShowModal()
        result = dlg.GetValue()
        dlg.Destroy()
        return result


wildcard = "EEG raw data (*.eeg)|*.eeg|"    \
           "Comma Separated Values File (*.csv)|*.csv|"       \
           "All files (*.*)|*.*"



class OpenBCIStreamer(CCDLUtil.EEGInterface.EEGInterface.EEGInterfaceParent):

    def __init__(self, channels_for_live='All', channels_for_save='All', live=True, save_data=True,
                 include_aux_in_save_file=True, subject_name=None, subject_tracking_number=None, experiment_number=None,
                 channel_names=None, port=None, baud=115200):
        """
        Inherits from CCDLUtil.EEGInterface.EEGInterfaceParent.EEGInterfaceParent

        :param channels_for_live: List of channel Indexes (Only!! -- channel names has not been implemented for OpenBCI) to put on the out_buffer_queue.
                                    If [], no channels will be put on the out_buffer_queue.
                                  If 'All', all channels will be placed on the out_buffer_queue.
        :param channels_for_save: List of channel Indexes (Only!! -- channel names has not been implemented for OpenBCI) to put on the data_save_queue.
                                    If [], no channels will be put on the out_buffer_queue.
                                    If 'All', all channels will be placed on the out_buffer_queue.
        :param include_aux_in_save_file: If True, we'll pass our AUX channels (along with the channels specified in channels_for_save) to our data_save_queue
        :param data_save_queue: queue to put data to save.  If None, data will not be saved.
        :param out_buffer_queue: The channel listed in the channels_for_live parameter will be placed on this queue. This is intended for live data analysis.
                                 If None, no data will be put on the queue.
                                 Items put on the out buffer queue will be a numpy array (though this can be either a 2D or a 1D numpy array)
        :param subject_name: Optional -- Name of the subject. Defaults to 'None'
        :param subject_tracking_number: Optional -- Subject Tracking Number (AKA TMS group experiment number tracker). Defaults to 'None'
        :param experiment_number: Optional -- Experimental number. Defaults to 'None'
        """

        super(OpenBCIStreamer, self).__init__(
            channels_for_live=channels_for_live, live=live, save_data=save_data, subject_name=subject_name,
            subject_tracking_number=subject_tracking_number, experiment_number=experiment_number)
        # in super, self.data_index is set to 0
        self.channel_names = str(channel_names)
        self.channels_for_save = channels_for_save
        self.include_aux_in_save_file = include_aux_in_save_file
        self.channels_for_live = channels_for_live
        # Set our port to default if a port isn't passed
        if port is None:
            raise ValueError("port cannot be None!")
        self.port = port
        self.baud = baud
        # create board object from hardware interface
        self.board = BciHwInter.OpenBCIBoard(port=self.port, baud=self.baud, scaled_output=False, log=True)
                                                    

    def callback_fn(self, data_packet):
        """
        This is a callback from our OpenBCI board.  A data packet is passed (a list of the data points)

        :param data_packet:  Data as taken from the OpenBCI board.  This is generally an OpenBCI sample object.
        """
        try:
            # List of data points
            data = data_packet.channel_data
            # starts at -1, our data is always indexed >= 0 by incrementing here instead of at the end of the method.
            self.data_index += 1
            # List of AUX data. note that this is sampled at a fraction of the rate of the data.
            # Each packet will have this field
            aux_data = data_packet.aux_data
            # but packets that don't have aux data will have a list of zeros.
            id_val = data_packet.id

        except Exception as e:
            # If we throw an error in this portion of the code, exit everything
            print e.message, e
            # continue to run, ignore the incomplete packet

        # Put on Out Buffer for live data analysis.
        if self.live:
            # Get our channels from channels for live:
            if type(self.channels_for_live) is str and self.channels_for_live.lower() == 'all':
                self.out_buffer_queue.put(data)
            elif type(self.channels_for_live) is list:
                # Get only the indexes contained in the channels for live list.
                trimmed_data = OpenBCIStreamer.trim_channels_with_channel_index_list(data, self.channels_for_live)
                self.out_buffer_queue.put(trimmed_data)
            else:
                if self.channels_for_live is not None:
                    raise ValueError('Invalid channels_for_live value.')
        # Save data
        if self.save_data:
            data_to_put_on_queue = None
            if type(self.channels_for_save) is str and self.channels_for_save.lower() == 'all':
                data_to_put_on_queue = data
            elif type(self.channels_for_live) is list:
                data_to_put_on_queue = OpenBCIStreamer.trim_channels_with_channel_index_list(data, self.channels_for_save)
            else:
                if self.channels_for_save is not None:
                    raise ValueError('Invalid channels_for_live value.')

            if data_to_put_on_queue is not None:

                data_str = str(id_val)+','+str(time.time())+','+','.join([str(xx) for xx in data_to_put_on_queue])

                if self.include_aux_in_save_file:
                    data_str += ',' + ','.join([str(yy) for yy in aux_data])

                # Data put on the data save queue is a len three tuple.
                self.data_save_queue.put((None, None, data_str + '\n'))

        # Set our two EEG INDEX parameters.
        CCDLUtil.EEGInterface.EEG_INDEX.CURR_EEG_INDEX = self.data_index
        CCDLUtil.EEGInterface.EEG_INDEX.CURR_EEG_INDEX_2 = self.data_index
        CCDLUtil.EEGInterface.EEG_INDEX.EEG_ID_VAL = id_val

    @threaded(False)
    def start_recording(self):
        """
        Starts the open BciHwInter streamer. Called in a new thread
        """

        #board = BciHwInter.OpenBCIBoard(port=self.port, baud=self.baud, scaled_output=False, log=True)
        print 'start recording'
        try:
            NFT.startflag = True
            self.board.start_streaming(self.callback_fn)
        except serial.SerialException:
            pass
def butter_bandpass(lowcut, highcut, fs, order):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(data, lowcut, highcut, fs, order):
    b, a = butter_bandpass(lowcut, highcut, fs, order)
    y = lfilter(b, a, data)
    return y        


def worker():
    """thread worker function"""
    obs = OpenBCIStreamer(live=True, save_data=True, port=NFT.com)
    obs.start_recording()
    second = []
    packetindex = 0
    
    f = open(NFT.filename, 'w')
    while NFT.startflag == False:
        g = obs.out_buffer_queue.get()
        second = second + g
        if len(second) > 4000:
            second = second[-4000:]
    print 'Main Loop Initializing--Start Next Round at will'
    #obs.start_saving_data(save_data_file_path='RestingStateMay24.csv', header="Sample Header")
    tick = time.time()
    total = 0
    while True:
        if NFT.resetflag and (NFT.FileWrite or NFT.FiveFlag) :
            print 'new file'
            NFT.resetflag = False
            
            if NFT.Type == 'NFT':
                f.close()
                f = open(NFT.filename[:-6] + '_' + str(NFT.stage) + '.csv', 'w')
            tick = time.time()
            total = 0
            packetindex = 0
            
            
        if NFT.FileWrite or NFT.FiveFlag:
            total = time.time()-tick
            
        if NFT.pausetime == False or NFT.stage == 0:
            print 'tick ', total, float(packetindex)/250 
        #tick = time.time()
        for i in range(0,250):
            g = obs.out_buffer_queue.get()
            second = second + g
            if NFT.FileWrite or NFT.FiveFlag:
                packetindex = packetindex+1
                if i == 125:
                    if NFT.pausetime == False or NFT.stage == 0 or NFT.FiveFlag:
                        print 'tock'
                for j in g:
                    f.write(str(j) + ',')                
                f.write(str(float(packetindex)/250) + ',' + str(total + time.time() - tick))
                f.write('\n')
                NFT.RecTime     = total
                NFT.PacketCount = float(packetindex)/250
            
            if NFT.FiveFlag:
                if time.time() > NFT.FiveFlag:
                    NFT.FiveFlag = 0
                    print '5 minutes are over'
            if len(second) > 4000:
                second = second[-4000:]
                

        #print len(second), 'second length'
        #print len(second[0::8]), 'channel length)'
        SMRTimeSeries = second[0::8]
        SMRTimeSeries2 = second[1::8]
        
        
        
        #SMRBase =  np.mean(SMRTimeSeries)
        #SMRTimeSeries = SMRTimeSeries - SMRBase
        #print 'values:', (g[0] - SMRBase), g[0], np.mean(SMRTimeSeries), SMRBase
        #print SMRTimeSeries[0:20]
        # Generate the timeseries
        T = 500
        t = np.array(list(range(T)))
        
        #if len(SMRTimeSeries) == 500: 
        #    lmod = linregress(t, SMRTimeSeries)
        #    predicted = lmod[1] + lmod[0]*t  #lmod.intercept, lmod.slope
        #    SMRTimeSeries = SMRTimeSeries - predicted
            #print SMRTimeSeries[0:8], SMRTimeSeries[-8:]
        if len(SMRTimeSeries) < 500:
            continue
        SMRTimeSeries = SMRTimeSeries - np.mean(SMRTimeSeries)
        SMRTimeSeries = butter_bandpass_filter(SMRTimeSeries, lowcut, highcut, fs, order)

        freq, density = sig.welch(SMRTimeSeries, fs=250, nperseg=500, scaling='density')

        NFT.SMRTimeSeries = SMRTimeSeries
        #freq2, density2 = sig.welch(SMRTimeSeries2, fs=250, nperseg=250, scaling='density')
        #print freq

        NFT.VoltMax = np.amax(SMRTimeSeries)
        NFT.VoltMedian = np.median(SMRTimeSeries)
        NFT.VoltMin = np.amin(SMRTimeSeries)
        # density = sp.log(density)[1:]
        # freq = freq[1:]
        #sub_data = [np.average([density[i], density[i + 1]]) for i in np.arange(0, 64, 2)]
        #self.meter.SetData(sp.log(sub_data), offset=0, size=32)
        #SPFreqs = freq
        # print("TESTING")
        # print SPFreqs[7:15]
        # print SPFreqs[22:38]
        SPVals = density[1:]
        
        #NFT.SPTruVal = (np.average(SPVals[4:8]) / np.average(SPVals[12:20]))  # 4-8 and 12-20 (Only adding +1 to each value)
        #NFT.Theta = np.average(SPVals[4:8])  # it's our theta, which is kind of messed up??
        #NFT.Beta = np.average(SPVals[12:20])  # same as above, but for beta?
        #NFT.LoNoise = SPVals[1]  # 1 Hz
        #NFT.HiNoise = np.average(SPVals[40:59])  # 40-59 Hz
        
        freq = freq[1:]
        
        
        if NFT.ThetaFlag:
            #print 'theta', freq[7:15]
            NFT.SPTruVal = np.average(SPVals[7:15]) #Theta only!
        else:
            #print 'ratio', freq[7:15], freq[22:38]
            NFT.SPTruVal = (np.average(SPVals[7:15])/np.average(SPVals[22:38])) #4-8 and 12-20 (Only adding +1 to each value)
        NFT.Theta = np.average(SPVals[7:15]) #it's our theta, which is kind of messed up??
        NFT.Beta = np.average(SPVals[22:38]) #same as above, but for beta?
        NFT.LoNoise = SPVals[1] #1 Hz
        NFT.HiNoise = np.average(SPVals[79:116]) #40-59 Hz




class testGUI(wx.Frame):
    def __init__(self):
        self.firstflag = True
        wx.Frame.__init__(self, None, -1, "OpenBCI Data Control Panel", size=(530, 500))
        panel = wx.Panel(self, -1)
        
               
        Numbers = ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15']
    

        ExTypes = ['NFT', 'Resting', 'Reading']
    
        wx.StaticBox(panel, -1, 'Subject Info', (20, 30), size=(480, 240))

        self.NumberText = wx.StaticText(panel, label="Trial Number:  ", pos=(60, 123))
        self.TypeText = wx.StaticText(panel, label="Data Type:  ", pos=(60, 163))
        #wx.CallAfter(self.pollServer)
        self.FileText = wx.StaticText(panel, label="", pos=(60, 30))
        self.buttonFilename = wx.Button(panel, -1, label="Subject Number", pos=(90, 80))
        self.ExNumber   = wx.ComboBox(panel, -1, pos=(170, 120), size=(80, -1), choices=Numbers, style=wx.CB_READONLY)
        self.ExType     = wx.ComboBox(panel, -1, pos=(170, 160), size=(80, -1), choices=ExTypes, style=wx.CB_READONLY)
        self.buttonPath = wx.Button(panel, -1, label="Confirm Subject", pos=(90, 200))
        self.pathtext = wx.StaticText(panel, label="", pos=(30, 240))
        self.buttonCOM = wx.Button(panel, -1, label="Specify COM", pos=(30, 300))
        self.buttonConnect = wx.Button(panel, -1, label="Connect to Board", pos=(30, 330))
        #self.buttonNFT = wx.Button(panel, -1, label="Create Window", pos=(30, 400))
        #self.buttonRest = wx.Button(panel, -1, label="Initialize 5 Minute Resting", pos=(30, 270))
        self.buttonNextRound = wx.Button(panel, -1, label="Start Recording", pos=(30, 400))


        panel.Bind(wx.EVT_COMBOBOX, self.Number, id=self.ExNumber.GetId())
        panel.Bind(wx.EVT_COMBOBOX, self.Type, id = self.ExType.GetId())
        
        panel.Bind(wx.EVT_BUTTON, self.Filename, id=self.buttonFilename.GetId())
        panel.Bind(wx.EVT_BUTTON, self.Connect, id=self.buttonConnect.GetId())
        panel.Bind(wx.EVT_BUTTON, self.COM, id=self.buttonCOM.GetId())
        panel.Bind(wx.EVT_BUTTON, self.NextRound, id=self.buttonNextRound.GetId())
        #panel.Bind(wx.EVT_BUTTON, self.NFT, id=self.buttonNFT.GetId())
        panel.Bind(wx.EVT_BUTTON, self.Path, id=self.buttonPath.GetId())
        #panel.Bind(wx.EVT_BUTTON, self.Rest, id=self.buttonRest.GetId())
        #panel.Bind(wx.EVT_BUTTON, self.Invisibility, id=self.buttonToggleInvisibility.GetId())

        # panel.Bind(wx.EVT_BUTTON, self.Tally, id=self.buttonTally.GetId())

        self.buttonConnect.Disable()
        self.buttonCOM.Disable()
        self.buttonNextRound.Disable()
        #self.buttonNFT.Disable()
        self.ExNumber.Disable()
        self.ExType.Disable()  
       # self.buttonFilename.Disable()
        self.buttonPath.Disable()

        self.sizer = wx.BoxSizer()
        self.sizer.Add(self.FileText, 1)
        # self.sizer.Add(self.button)
        
        
    def Number(self,event):
        item = event.GetSelection()
        print 'num', item+1
        NFT.Session = str(item+1)
        self.ExType.Enable()  
        
        
    def Type(self,event):         
        print 'type', event.GetSelection()
        selection = event.GetSelection()
        if selection == 0:
            NFT.Type = 'NFT'
        elif selection == 1:
            NFT.Type = 'Rest'
        elif selection == 2:
            NFT.Type = 'Read'
        print NFT.Type
        self.buttonPath.Enable()  
        
            
    def Path(self,event):
        """

        Opens up a file saving dialog when the "File" button is pressed.
        """
        global filename
        
        if NFT.Type == 'NFT':
            filename = 'C:\Users\Experimenter\Desktop\Experiment Data\RAIN\EEG Data\NFT\\' + str(NFT.Number) + '_s' + str(NFT.Session) + '_' + NFT.Type + '_1.csv'
        if NFT.Type == 'Read':
            filename = 'C:\Users\Experimenter\Desktop\Experiment Data\RAIN\EEG Data\Reading\\' + str(NFT.Number) + '_s' + str(NFT.Session) + '_' + NFT.Type + '.csv'
        if NFT.Type == 'Rest':
            filename = 'C:\Users\Experimenter\Desktop\Experiment Data\RAIN\EEG Data\Resting\\' + str(NFT.Number) + '_s' + str(NFT.Session) + '_' + NFT.Type + '.csv'        
        #filename = 'C:/Users/Experimenter/Desktop/TEST/' + str(NFT.Number) + '_s' + str(NFT.Session) + '_' + NFT.Type + '.csv'
        print filename
        fname = filename
        
        # If the filename exists, ask for confirmation
        if os.path.exists(fname):
            dlg = wx.MessageDialog(self, "A file for this subject at this trial exists. Overwrite?",
                                   "Potential problem with file",
                                   wx.YES_NO | wx.NO_DEFAULT | wx.ICON_INFORMATION
                                   )

            response = dlg.ShowModal()
            if response == wx.ID_YES:
                filename = fname

            elif response == wx.ID_NO:
                filename = None
                return

        else:
            # If the file does not exists, we can proceed
            filename = fname
        if filename != None:
            filestring = "Filename: " + str(fname)
            self.FileText.SetLabel(filestring)
            self.sizer.Layout()
            print(["Filename: " + fname])
            #interface.filename = fname
            #self.buttonToggleTMS.Enable()
            self.buttonCOM.Enable()
            # self.buttonConnect.Enable()
            self.Refresh()
            self.Update()
        NFT.filename = fname
        NFT.OutputFilename = fname[:-6] + '_MetaData.csv'
        NFT.ExperimentOutputName = fname[:-6] + '_ContRec.csv'
        # self.update_interface()
        
        
        self.pathtext.SetLabel(fname)
        self.sizer.Layout()
        self.Refresh()
        self.Update() 

        self.ExNumber.Disable()
        self.ExType.Disable()  
        self.buttonFilename.Disable()
        self.buttonPath.Disable()        
        
        NFT.CustomName = True
        
    def Filename(self,event):
        x = ask(message = 'What is this subject experiment number?')
        x = int(x)
        try: 
            print x
            SubjectIndex = np.where(ValuesIndex == x)
            SubjectIndex = int(SubjectIndex[0])
            print SubjectIndex
            ControlValue = Values[SubjectIndex, 1]
            print 'Subject ID is ', str(x)
            if ControlValue == 0:
                dlg = wx.MessageDialog(self,'You have entered experiment # ' + str(x) + '. \n\n This is THETA NFT subject.  \n\nDouble check the number you have entered.  \n\nIf it is correct, press OK.  Otherwise, CANCEL.', 'Info', wx.OK|wx.CANCEL|wx.ICON_INFORMATION)
                result = dlg.ShowModal() 
                NFT.ThetaFlag =  True
                if result == wx.ID_CANCEL: 
                    return
            if ControlValue != 0:
                dlg = wx.MessageDialog(self,'You have entered experiment # ' + str(x) + '. \n\n This experiment is a THETA-BETA RATIO subject.  \n\nDouble check the number you have entered.  \n\nIf it is not correct, press CANCEL. \n\nIf it is correct, hit OK and select a control file.', 'Info', wx.OK|wx.CANCEL|wx.ICON_INFORMATION)
                result = dlg.ShowModal() 
                NFT.ThetaFlag = False
                if result == wx.ID_CANCEL: 
                    return 
        except TypeError:
            wx.MessageBox('This number is not in the subject database. Try again or contact Justin.', 'Info', wx.OK | wx.ICON_INFORMATION)
        else: 
            NFT.Number = str(x)
            self.buttonFilename.SetLabel(str(x))
            self.sizer.Layout()
            self.Refresh()
            self.Update()
            self.ExNumber.Enable()

  


    def pollServer(self):
        self.Tally()
        wx.CallLater(10, self.pollServer)


    def Tally(self):
        self.sizer.Layout()
        self.Refresh()
        self.Update()
        
    
    def Path2(self, event):
        NFT.ThetaFlag = not NFT.ThetaFlag
        if NFT.ThetaFlag:
            self.buttonPath.SetLabel("Theta!")
        else:
            self.buttonPath.SetLabel("Ratio!")
        self.sizer.Layout()
        self.Refresh()
        self.Update()
        #self.buttonNFT.Enable()
    

    def COM(self, event):
        dlg = wx.TextEntryDialog(frame, 'Specify the COM port, i.e. COM6', 'COM Specification')
        dlg.SetValue("COM6")
        if dlg.ShowModal() == wx.ID_OK:
            NFT.com = dlg.GetValue()
            self.buttonConnect.Enable()
        dlg.Destroy()

        self.buttonCOM.SetLabel(NFT.com)
        self.sizer.Layout()
        self.Refresh()
        self.Update()

    def Connect(self, event):
        self.buttonPath.Enable()
        self.buttonConnect.Disable()
        self.buttonCOM.Disable()
        #self.buttonRest.Enable()
        self.buttonFilename.Disable()
        self.buttonNextRound.Enable()
        #self.buttonNFT.Enable()
        #self.buttonRest.Enable()
        t = threading.Thread(target=worker)
        t.start()
        self.buttonNextRound.Enable()
        #self.buttonNFT.Disable()
        #self.buttonRest.Disable()
        self.buttonPath.Disable()
        if NFT.Type == 'NFT':
            print'paradigm started'        
            NFT.main()
        


    def NFT(self, event):
        self.buttonNextRound.Enable()
        self.buttonNFT.Disable()
        #self.buttonRest.Disable()
        self.buttonPath.Disable()
        NFT.main()
        print'paradigm started'

    def Rest(self, event):
        self.buttonNextRound.Enable()
        NFT.FiveMin = True
        NFT.FixationInterval = 300
        #self.buttonNFT.Disable()
        #self.buttonRest.Disable()
        self.buttonPath.Disable()
        NFT.main()
        print'paradigm complete'


    def NextRound(self, event):
        # print('check')
        # self.ser = serial.Serial('COM1', 9600)
        # self.ser.write('0')
        # self.ser.close()
        if NFT.Type == 'NFT':
            if NFT.pausetime:
                NFT.resetflag = True
                NFT.FileWrite = True
            NFT.NEXT = True
            if NFT.startflag:
                NFT.RecordBypass = True
            else:
                'Wait for connection'
            self.buttonNextRound.SetLabel('Next Round')
            self.sizer.Layout()
            self.Refresh()
            self.Update() 
        else:
            self.buttonNextRound.Disable()
            NFT.FiveFlag = time.time() + 300


if __name__ == '__main__':
    app = wx.App(redirect=False)
    frame = testGUI()
    frame.Show(True)
    app.MainLoop()

