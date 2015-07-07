import pyaudio as pya 
import sys
import struct
import math
import wave
import time
from pympi import Elan,Praat

class SoundDetector:
    def __init__(self):
        self.THRESHOLD=.02 # adjust as necessary       
        
    def is_sound(self,amp):
        return amp>self.THRESHOLD
    
    def _identify_speech(self):
        return ""
        
        
class ElanAnnotator:
    def __init__(self,tier_names=["default_speech"]):
        try:
            self.eaf=Elan.Eaf(author="A Group of Americans")
            for tier in tier_names:
                self.eaf.add_tier(tier)
        except KeyError, ke:
            print ke
            print "NO HOPE NOW"
            sys.exit(-1)
        except ValueError, ve:
            print ve
            print "NO HOPE NOW"
            sys.exit(-1)
            
            
    def create_annotation(self,tier,start,end,text):
        self.eaf.add_annotation(tier, start, end, value=text)
        
    def write_annotation_file(self):
        self.eaf.to_file("test_1.eaf")
        
        
        
class WavFileReader:
    def __init__(self,stream=None,filepath=""):
        self.pa=pya.PyAudio()
        self.most_recent=0 # the duration of the most recent speaking sound
        self.cont_sounds=0 # no continuous sounds so far
        self.silence=0 # start from 0 everywhere
        self.current=0 # keeps track of the current time. still gotta figure this out. 
        self.sound_start=0
        self.sd=SoundDetector()
        self.CHANNELS=1        
        self.CHUNK=1024
        self.RATE=44100
        self.FORMAT = pya.paInt16 
        self.INPUT_BLOCK_TIME=0.2 # 20 ms chunks?
        self.INPUT_FRAMES_PER_BLOCK=int(self.RATE*self.INPUT_BLOCK_TIME)
        self.annotator=ElanAnnotator()
        self.wf=None
        self.stream=self.start_stream(self.read_from_file(filepath))      
        
         
    def start_stream(self,wf):
        strm=self.pa.open(format=self.pa.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        input=True)
        self.wf=wf
        print "****** RECORDING ******"                         
        return strm
        
    def read_stream(self):
        fmt="%dh"%self.INPUT_FRAMES_PER_BLOCK
        try:
            d=self.wf.readframes(self.INPUT_FRAMES_PER_BLOCK)
            d=struct.unpack(fmt,d)
            if self.sd.is_sound(self.calc_rms(d)):
                if self.sound_start==0:
                    self.sound_start=self.current
                self.cont_sounds+=0.2
                self.silence=0
            else:
                self.silence+=0.2
                if self.silence>5:# 2 seconds roughly 
                    self.sound_start=0 # reset 
                    # now that this is done, see if we should add to the elan file at all! whoooo
                    self.set_length(self.cont_sounds)
                    if self.get_length()>0:
                        self.cont_sounds=0
                        print "tier: %s,start time: %f,end time: %f, annotation: %s"%("default_speech",self.current-self.most_recent,self.current,"speaking")
                        #self.annotator.create_annotation("default_speech",self.current-self.most_recent,self.current,"speaking")
            self.current+=0.2 # move ahead a little ? ? ? ????? I HOPE?
            return d
        except:
            #print e
            print "*** ERROR ***"
            
            
    def finish(self):
        self.annotator.write_annotation_file()
  
    def set_length(self, dur):
        self.most_recent=dur
        
    def get_length(self):
        return self.most_recent
        
    def current_time(self):
        return self.current
        
    def is_silent(self):
        return silence!=0
    
    def end_stream(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()
        print "*** STREAM CLOSED ***"
        
    def _identify_pitch(self,data):
        # this will do something cool in the future
        return None
        
    def calc_rms(self,block):
        rms=0
        n=len(block)
        for b in block:
            b = b / (2.**15)
            square=b*b
            rms+=square
        rms=math.sqrt(rms/n)
        return rms
    
    def read_from_file(self,filename):
        w = wave.open(sys.argv[1], 'rb')
        return w   
    

    
if __name__=="__main__":
    wfr=WavFileReader(filepath="/home/ksb/Documents/dreu/analysis/python_scripts/american_audio/American_2/American_2_A_3NamingTask.wav")
    data=True
    while data:
        try:
            wfr.read_stream()
        except:
            data=False
            wfr.finish()
        
        
        
        
        
        
        
        
        
        
        
        
