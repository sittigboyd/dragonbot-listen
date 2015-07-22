import pyaudio as pya
import numpy 
from scipy.stats.mstats import gmean
import sys
import struct
import math
import wave
import time
from pympi import Elan,Praat
import os

class SoundDetector:
    def __init__(self,filename):
        #self.RMS_THRESHOLD=0.013 # adjust as necessary       
        self.ENERGY_THRESHOLD=35 # drawn from M. H. Moattar and M. M. Homayounpour 2009
        self.F_THRESHOLD=185 # also drawn from above, in Hz      
        self.SF_THRESHOLD=5 # drawn from Moattar and Homayounpour
        self.pa=pya.PyAudio()
        self.e_min=40 # ridiculously high number for more accurate thresholding
        self.f_min=185
        self.sfm_min=5
        self.rms_min=400 # I BELIEVE, adjust as necessary
        
        self.most_recent=0 # the duration of the most recent speaking sound
        self.cont_sounds=0 # no continuous sounds so far
        self.silence=0 # start from 0 everywhere
        self.current=0 # keeps track of the current time. still gotta figure this out. 
        self.sound_start=0
        
        self.CHANNELS=1        
        self.CHUNK=1024
        self.RATE=44100
        self.FORMAT = pya.paInt16 
        self.INPUT_BLOCK_TIME=0.01 # 20 ms chunks?
        self.INPUT_FRAMES_PER_BLOCK=int(self.RATE*self.INPUT_BLOCK_TIME)
        self.wf=wave.open(filename,'rb')
        
        print "there are %d frames per block"%self.INPUT_FRAMES_PER_BLOCK
        self.annotator=ElanAnnotator(filename=filename)
        self.stream=self.start_stream(self.wf)   
        
    def is_sound(self,amp):
        return amp>self.RMS_THRESHOLD
        
    def get_features(self,frame):
        """
        MOVE
        Nice algorithm taken from Moattar and Homayounpour, 2009 
        ("A Simple but Efficient Real-Time Voice Activity Detection Algorithm")
        Friendly. Plays well with others. 
        
        Calculates energy, dominant frequency, and spectral flatness measure of a frame;
        returns whether or not it seems like speech 
        """
        energy=self.calc_frame_energy(frame)
        f,sfm=self.apply_fft(frame)
        return energy,f,sfm

    def apply_fft(self,frame):
        ### THIS IS THE PROBLEM CHILD
        "Returns both the frequency and sfm"
        data=numpy.array(frame)
        w=numpy.fft.fft(data)
        #mad_max_freq=w[numpy.argmax(w)]
        freqs_and_geeks=numpy.fft.fftfreq(len(w))
        idx=numpy.argmax(numpy.abs(w))
        freq=freqs_and_geeks[idx]
        freq_hz=abs(freq)*44100
        arith_mean=numpy.mean(frame)
        geo_mean=gmean(frame)
        try:
            sfm=10*(geo_mean/arith_mean)
        except:
            sfm=0
        return freq_hz,sfm
       
    def calc_frame_energy_ignore(self,frame):
        energy=0
        for f in frame:
            energy+=f*f        
        return energy
        
    def calc_frame_energy(self,frame):
        "Returns a numpy array of the energy associated with ? ? ? each single sample in a frame ? ? ? "
        return numpy.sum(numpy.square(frame))
        
    def set_thresh(self,e,f,sf):
        e=self.ENERGY_THRESHOLD*math.log(e)
        #f=self.F_THRESHOLD
        sf=self.SF_THRESHOLD
        return e,f,sf        
    
    def start_new_files(self,filename):
        self.e_min=40 # ridiculously high number for more accurate thresholding
        self.f_min=185
        self.sfm_min=5
        self.rms_min=200 # I BELIEVE, adjust as necessary
        
        self.most_recent=0 # the duration of the most recent speaking sound
        self.cont_sounds=0 # no continuous sounds so far
        self.silence=0 # start from 0 everywhere
        self.current=0 # keeps track of the current time. still gotta figure this out. 
        self.sound_start=0
        self.wf=wave.open(filename,'rb')
        efile=filename.split("/")[-1]
        efile=efile.split(".")[0]
        self.annotator=ElanAnnotator(filename=efile)
    
    def start_stream(self,wf):
        strm=self.pa.open(format=self.pa.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        input=True)
        print "****** RECORDING ******"                         
        return strm
        
    def detect_sounds(self):
        sound_frames=0
        silence_frames=0
        # uncomment later just testing silence_threshold=30
        silence_threshold=10
        fmt="%dh"%self.INPUT_FRAMES_PER_BLOCK
        still_reading=True
        total_sounds=0
        frames=0
        while still_reading:
            try:
                counter=0
                sound=False
                d=self.wf.readframes(self.INPUT_FRAMES_PER_BLOCK)
                d=struct.unpack(fmt,d)
                frames+=1
                e,f,sfm=self.get_features(d)
                rms=self.get_rms(d)
                te,tf,tsfm=self.set_thresh(self.e_min,self.f_min,self.sfm_min)
                if frames<30:
                    self.e_min=((silence_frames*self.e_min)+e)/(silence_frames+1)
                    #if f<self.f_min and f!=0:
                        #self.f_min=f
                    if sfm<self.sfm_min:
                        self.sfm_min=sfm
                if e-self.e_min>=te:
                    #print "e met"
                    counter+=1
                if sfm-self.sfm_min>=tsfm:
                    #print "sfm met"
                    counter+=1
                if f-self.f_min>=tf:
                    #print "frequency met"
                    counter+=1
                if rms>self.rms_min:
                    if counter>1:
                        sound=True
#                print "counter: %d"%counter
                if sound:
                    silence_frames=0
                    self.cont_sounds+=0.01
                    sound_frames+=1
                    # Then, check to see how many sound frames there have been. if there are more than five, sound
                    # is occurring, so we'll set this so that the silence threshold is higher
                    #if sound_frames>15:
                        # sound has definitely started
                        #silence_threshold=50 # a reasonable half a second of silence
                    #else:
                        #silence_threshold=10 # .1 seconds of silence
                    if self.sound_start==0:
                        self.sound_start=self.current
                else:
                    silence_frames+=1
                    if silence_frames>silence_threshold:
                        # check to see if there's any speech we need to write to the file:
                        if sound_frames>10: # WAS 30 change back for original comparison
                            total_sounds+=1
                            #print "we got %f seconds in a row dingle dangle"%(1000*self.cont_sounds)
                            #print "We've got sound, ladies and gents! it lasts from %f to %f"%((self.current-0.1-self.cont_sounds),(self.current-0.1))
                            start=self.current-(silence_threshold*0.01)-self.cont_sounds
                            end=self.current-(silence_threshold*0.01)
                            ann_text="speaking"
                            self.annotator.create_annotation("default_speech",start,end,ann_text)
                            #self.annotator.create_annotation("default_speech",(self.current-0.2)-self.cont_sounds,(self.current-0.2),"speaking")
                        sound_frames=0
                        self.cont_sounds=0
                        sound_frames=0
                    #else:
                    #    self.e_min=((silence_frames*self.e_min)+e)/(silence_frames+1)
                self.current+=0.01
                #still_reading=False # comment; just for testing
            except IOError, e:
                print e
                print "*** ERROR ***"
                still_reading=False
            except:
                print "Error, idk what"
                still_reading=False
        print "at the end, there were %d annotations created"%total_sounds
        self.finish()
    
    def read_stream(self):
        
        fmt="%dh"%self.INPUT_FRAMES_PER_BLOCK
        try:
            d=self.wf.readframes(self.INPUT_FRAMES_PER_BLOCK)
            d=struct.unpack(fmt,d)
            if self.is_speech(d):
                self.cont_sounds+=0.01
#                self.silence=0
                if self.sound_start==0:
                    self.sound_start=self.current
            else:
                self.silence+=0.01
                if self.silence>1: # 1 second of silence
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
        self.wf.close()
        #self.pa.terminate()
  
    def set_length(self, dur):
        self.most_recent=dur
        
    def get_length(self):
        return self.most_recent
        
    def get_rms(self,block):
        # where block is a numpy array
        #rms=0
        block=numpy.array(block)
        squares=numpy.square(block)
        sum_sq=numpy.sum(squares)
        sq_mean=sum_sq/block.size
        sqroot=numpy.sqrt(sq_mean)
        #print "rms is %f"%sqroot
        return sqroot
        
#        print numpy.sqrt(numpy.mean(numpy.square(block)))
#        return numpy.sqrt(numpy.mean([8,4,15]))
        
    def current_time(self):
        return self.current
        
    def is_silent(self):
        return silence!=0
    
    def end_stream(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()
        print "*** STREAM CLOSED ***"
    
    def read_from_file(self,fn):
        w = wave.open(fn, 'rb')
        return w   
            
class ElanAnnotator:
    def __init__(self,tier_names=["default_speech"],filename=None):
        self.total=0
        if contains(filename,"/"):
            filename=filename.split("/")[-1]
            filename=filename.split(".")[0]
        self.efile=filename
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
        self.total+=1
        
    def write_annotation_file(self):
        Elan.to_eaf("annotations_higher_rms/%s.eaf"%(self.efile),self.eaf)
        tg=self.eaf.to_textgrid()
        tg.to_file("annotations_higher_rms/%s.TextGrid"%(self.efile))   
        print "in write_annotation_file: there were %d total annotations added."%self.total
        
def contains(string,char):
    for s in string:
        if s==char:
            return True
    
def annotate_american_data():
#    filepath="/home/ksb/Documents/dreu/analysis/python_scripts/american_audio/American_4/American_4_A_3NamingTask.wav"
#    sound_detect=SoundDetector(filepath)
#    sound_detect.detect_sounds()
#    filepath="/home/ksb/Documents/dreu/analysis/python_scripts/american_audio/American_4/American_4_A_4StoryTask.wav"
#    sound_detect.start_new_files(filepath)
#    sound_detect.detect_sounds()
    audiopath="/home/ksb/Documents/dreu/analysis/python_scripts/american_audio"
    dirs=['American_2','American_3','American_4']
    files=[
        ['American_2_A_4StoryTask.wav','American_2_B_4StoryTask.wav','American_2_C_4StoryTask.wav','American_2_D_4StoryTask.wav','American_2_A_3NamingTask.wav','American_2_B_3NamingTask.wav','American_2_C_3NamingTask.wav','American_2_D_3NamingTask.wav'],\
        ['American_3_A_4StoryTask.wav','American_3_B_4StoryTask.wav','American_3_C_4StoryTask.wav','American_3_D_4StoryTask.wav','American_3_A_3NamingTask.wav','American_3_B_3NamingTask.wav','American_3_C_3NamingTask.wav','American_3_D_3NamingTask.wav'],\
        ['American_4_A_4StoryTask.wav','American_4_B_4StoryTask.wav','American_4_C_4StoryTask.wav','American_4_D_4StoryTask.wav','American_4_A_3NamingTask.wav','American_4_B_3NamingTask.wav','American_4_C_3NamingTask.wav','American_4_D_3NamingTask.wav'],\
        ]
    not_created=True
    for idx in range(len(dirs)):
        direc=dirs[idx]
        for filename in files[idx]:
            filepath="%s/%s/%s"%(audiopath,direc,filename)
            print "annotating %s"%filepath
            if not_created:
                sound_detect=SoundDetector(filepath)
                not_created=False
            sound_detect.start_new_files(filepath)
            sound_detect.detect_sounds()
    sound_detect.end_stream()
        
def annotate_mexican_data():
    audiopath="/home/ksb/Documents/dreu/analysis/utep_ict_audio" 
    dirs=['Mexican_1','Mexican_2']
    files=[
          ['Mexican_1_A_4Story.wav','Mexican_1_B_4Story.wav','Mexican_1_C_4Story.wav','Mexican_1_D_4Story.wav','Mexican_1_A_3Naming.wav','Mexican_1_B_3Naming.wav','Mexican_1_C_3Naming.wav','Mexican_1_D_3Naming.wav'],\
          ['Mexican_2_A_4StoryTask.wav','Mexican_2_B_4StoryTask.wav','Mexican_2_C_4StoryTask.wav','Mexican_2_D_4StoryTask.wav','Mexican_2_A_3NamingTask.wav','Mexican_2_B_3NamingTask.wav','Mexican_2_C_3NamingTask.wav','Mexican_2_D_3NamingTask.wav'],\
        ]
    not_created=True
    for idx in range(len(dirs)):
        direc=dirs[idx]
        for filename in files[idx]:
            filepath="%s/%s/%s"%(audiopath,direc,filename)
            print "annotating %s"%filepath
            if not_created:
                sound_detect=SoundDetector(filepath)
                not_created=False
            sound_detect.start_new_files(filepath)
            sound_detect.detect_sounds()
    sound_detect.end_stream()
    
    
def annotate_arabic_data():
    audiopath="/home/ksb/Documents/dreu/analysis/utep_ict_audio" 
    dirs=['Arabic_1','Arabic_4']
    files=[
          ['Arabic_1_A_4Story.wav','Arabic_1_B_4Story.wav','Arabic_1_C_4Story.wav','Arabic_1_D_4Story.wav','Arabic_1_A_3Naming.wav','Arabic_1_B_3Naming.wav','Arabic_1_C_3Naming.wav','Arabic_1_D_3Naming.wav'],\
          ['Arabic_4_A_4Story.wav','Arabic_4_B_4Story.wav','Arabic_4_C_4Story.wav','Arabic_4_D_4Story.wav','Arabic_4_A_3Naming.wav','Arabic_4_B_3Naming.wav','Arabic_4_C_3Naming.wav','Arabic_4_D_3Naming.wav']
        ]
    not_created=True
    for idx in range(len(dirs)):
        direc=dirs[idx]
        for filename in files[idx]:
            filepath="%s/%s/%s"%(audiopath,direc,filename)
            print "annotating %s"%filepath
            if not_created:
                sound_detect=SoundDetector(filepath)
                not_created=False
            sound_detect.start_new_files(filepath)
            sound_detect.detect_sounds()
    sound_detect.end_stream()
    
    
if __name__=="__main__":
    print "**** Gonna analyze some 'mericans ****"
    print "**** About to annotate the Mexican speech data ****"
    annotate_mexican_data()
    print "**** Finished with Mexican speech data, about to annotate Arabic speech data ****"
    annotate_arabic_data()
    print "**** Finished with everything!! ****"
    