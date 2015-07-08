import pyaudio as pya 
import struct
import math
import wave
import time

class SoundDetector:
    def __init__(self,threshold=0.5):
        self.THRESHOLD=threshold # adjust as necessary       
        
    def is_sound(self,amp):
        return amp>self.THRESHOLD
        
    def is_onset(self,sound):
        onset=False
        return onset
    
    def _identify_speech(self):
        return ""
        
class MicStream:
    def __init__(self,stream=None):
        self.pa=pya.PyAudio()
        self.cont_sounds=0 # no continuous sounds so far
        self.silence=0 # start from 0 everywhere
        self.sd=SoundDetector()
        self.CHANNELS=1        
        self.CHUNK=1024
        self.RATE=44100
        self.FORMAT = pya.paInt16 
        self.INPUT_BLOCK_TIME=0.2 # 20 ms chunks?
        self.INPUT_FRAMES_PER_BLOCK=int(self.RATE*self.INPUT_BLOCK_TIME)
        self.stream=self.start_stream()        
         
    def start_stream(self):
        strm=self.pa.open(format=self.FORMAT,
                                 channels=self.CHANNELS,
                                 rate=self.RATE,
                                 input=True,
                                 frames_per_buffer=self.INPUT_FRAMES_PER_BLOCK)
        print "****** STARTED PROCESSING ******"                         
        return strm
        
    def read_stream(self):
        fmt="%dh"%self.INPUT_FRAMES_PER_BLOCK
        try:
            d=self.stream.read(self.INPUT_FRAMES_PER_BLOCK)
            d=struct.unpack(fmt,d)
            # maybe is_onset goes somewhere here??
            if sd.is_sound(self.calc_rms(d)):
                print "detected sound"
                self.cont_sounds+=0.2
                self.silence=0
            else:
                print "no dice"
                self.silence+=0.2
                if self.silence>5:# 2 seconds roughly 
                    print "too long without speaking"
                    self.cont_sounds=0
#            print sum(d)/len(d)
#            print "\n\n"
        except IOError, e:
            print e
            print "*** ERROR ***"
        #print (max(self.stream.read(self.CHUNK)))
        
        #sd.determine_sound(self.stream.read(self.CHUNK))
#        return self.stream.read(self.CHUNK)    
        
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
    
    def write_to_file(self,data):
        wf = wave.open('test_wav.wav', 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.pa.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(data))
        wf.close()
    
    
if __name__=="__main__":
    sd=SoundDetector()
    mc=MicStream()
    print "doing some stuff in the future"
    rec_time=10
    # let's try listening to say 10 seconds of data
    start=0
    recording=True
    all_data=[]
    while recording: # record 10 seconds
#        print start
#        start+=1
        mc.read_stream()
        #all_data.append(data)
    mc.end_stream()
    print "*** END OF STREAMING ***"
    
        