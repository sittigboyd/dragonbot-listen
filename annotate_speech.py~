import pyaudio as pya
import numpy 
import sys
import struct
import math
import wave
import time
from pympi import Elan,Praat

class SoundDetector:
    def __init__(self):
        self.RMS_THRESHOLD=0.013 # adjust as necessary       
        self.ENERGY_THRESHOLD=40 # drawn from M. H. Moattar and M. M. Homayounpour 2009
        self.F_THRESHOLD=185 # also drawn from above, in Hz
        self.SF_THRESHOLD=5 # drawn from Moattar and Homayounpour
        
    def is_sound(self,amp):
        return amp>self.RMS_THRESHOLD
        
    def is_speech(self,frame):
        """
        Nice algorithm taken from Moattar and Homayounpour, 2009 
        ("A Simple but Efficient Real-Time Voice Activity Detection Algorithm")
        Friendly. Plays well with others. 
        
        Calculates energy, dominant frequency, and spectral flatness measure of a frame;
        returns whether or not it seems like speech 
        """
        counter=0
        energy=self.calc_frame_energy(frame)
        f,sfm=self.apply_fft(frame)
        min_e=min(energy)
        min_f=min(f)
        min_sf=min(sfm)
        
        te,tf,tsfm=self.set_thresh(min_e,min_f,min_sf)
        
        if energy-min_e>=te:
            counter+=1
        if f-min_f>=tf:
            counter+=1
        if sf-min_sf>=tsfm:
            counter+=1
        if counter>1:
            return True
        return False

    def apply_fft(frame):
        "Returns both the frequency and sfm"
        frame=numpy.array(frame)
        w=fft.fft(frame)
        freqs_and_geeks=fft.fftfreq(len(w))
        mad_max_freq=freqs_and_geeks.max()
        
        # Next step: return sfm(frame)
        # find the arithmetic mean of the speech spectrum, nbd
        arith_mean=mean(frame)
        geo_mean=gmean(frame)
        sfm=10*(geo_mean/arith_mean)
        return mad_max_freq,sfm
       
    def calc_frame_energy(frame):
        energy=0
        for f in frame:
            energy+=f*f
        return energy
            

    def set_thresh(e,f,sf):
        e=self.ENERGY_THRESHOLD*math.log(e)
        f=self.F_THRESHOLD
        sf=self.SF_THRESHOLD
        return e,f,sf
    
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
        self.eaf.add_annotation(tier, 1000*(start), 1000*(end), value=text)
        
    def write_annotation_file(self):
        Elan.to_eaf("test_2.eaf",self.eaf)
        tg=self.eaf.to_textgrid()
        tg.to_file("test_2.TextGrid")
        
        
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
        self.INPUT_BLOCK_TIME=0.01 # 20 ms chunks?
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
                self.cont_sounds+=0.01
                self.silence=0
            else:
                self.silence+=0.01
                if self.silence>1:
                    self.sound_start=0 # reset 
                    # now that this is done, see if we should add to the elan file at all! whoooo
                    self.set_length(self.cont_sounds)
                    if self.get_length()>0:
                        self.cont_sounds=0
                        #print "tier: %s,start time: %f,end time: %f, annotation: %s"%("default_speech",self.current-self.most_recent,self.current,"speaking")
                        self.annotator.create_annotation("default_speech",self.current-self.most_recent,self.current,"speaking")
            self.current+=0.01 # move ahead a little ? ? ? ????? I HOPE?
            return d
        except IOError, e:
            print e
            print "*** ERROR ***"
        except:
            print "Error, idk what"
    
    def detect_sounds(self):
        
        fmt="%dh"%self.INPUT_FRAMES_PER_BLOCK
        try:
            d=self.wf.readframes(self.INPUT_FRAMES_PER_BLOCK)
            d=struct.unpack(fmt,d)
            if self.sd.is_speech(d):
                self.cont_sounds+=0.01
#                self.silence=0
                if self.sound_start==0:
                    self.sound_start=self.current
            else:
                self.silence+=0.01
                if self.silence>1: # 10 consecutive frames of silence
                    self.sound_start=0 # reset 
                    # now that this is done, see if we should add to the elan file at all! whoooo
                    self.set_length(self.cont_sounds)
                    if self.get_length()>0:
                        self.cont_sounds=0
                        #print "tier: %s,start time: %f,end time: %f, annotation: %s"%("default_speech",self.current-self.most_recent,self.current,"speaking")
                        self.annotator.create_annotation("default_speech",self.current-self.most_recent,self.current,"speaking")
            self.current+=0.01 # move ahead a little ? ? ? ????? I HOPE?
            return d
        except IOError, e:
            print e
            print "*** ERROR ***"
            return False
        except:
            print "Error, idk what"
            return False
    
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
            data=wfr.read_stream()
        except:
            data=False
# RECOMMENT     wfr.finish()
