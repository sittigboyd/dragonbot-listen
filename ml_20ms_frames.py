# IN CASE I HECKED UP /usr/lib/python2.7/lib-dynload/parser.so

import sys,os
from scipy.io import wavfile as wf
import numpy as np
#from matplotlib import pyplot 
import tgt
import re
from sklearn import svm
import librosa

def main():
    audpath="audiofiles/American_4_A_3NamingTask.wav"
    tgpath="audiofiles/eaf/American_4_Naming_Joyce.TextGrid" 
    full_tg=get_textgrid(tgpath)
    right_tier=get_individual_tier(full_tg,"Speech (A)")
    
    # then get the annotations
    anns=get_next_annotation_chunk(right_tier,0,.2) # get 200 ms of annotations
    #process_annotations(anns)
    
    aud_nump=get_numpy_from_file(audpath)
#    assess_numpy(aud_nump)
#    aud_seg=get_xms(aud_nump,100)
#    assess_numpy(aud_nump,right_tier)
    
#    X,y=form_learning_array(right_tier,aud_nump)
    X,y=get_training_data(aud_nump,right_tier)
    X=extract_features(X)   
    machine_learn(X,y)
    
    
def get_all_tiers(tgpath,letter):
    tiers=[]
    # returns an array of TextGrid objects
    for dirs,subdirs,fnames in (os.walk(tgpath)):
        for f in fnames:
            if f.startswith("._"):
                pass
            elif f.endswith(".TextGrid"):
                # turn it into an actual textgrid object
                tg=get_textgrid(tgpath+f)
                tiers.append(tg.get_tier_by_name("Speech (%s)"%(letter.upper()))
    return tiers
    
    

def form_learning_array(tiers,audio_array):
    X=[] # new array of input
    y=[] # the output
    # so, get chunks of input and then output
    total=0
    start=0
    zeroes=0
    ones=0
    twos=0
    for idx in range(len(tiers)):
        audio=audio_array[idx]
        tier=tiers[idx]
        while len(audio) >8820:
            next_audio=get_xms(audio,200)
            audio=audio[8820:]
            outcome=process_annotations(get_next_annotation_chunk(tier, start, (start+.20)))
            if outcome==0:
                zeroes+=1
            elif outcome==1:
                ones+=1
            elif outcome==2:
                twos+=1
            #print " The outcome was %d"%outcome
            start+=.20
            total+=1
            X.append(next_audio)
            y.append(outcome)
    print "There are %d samples of this person NOT speaking, %d samples of this person laughing, and %d samples of this person speaking"%(zeroes,twos,ones)
    X=np.array(X,dtype="int16")
    y=np.array(y)
    return X,y

def extract_features(audio):
    """
    Given a numpy array of audio data (200 ms long), return the following:
    1. The pitch
    2. The intensity
    3. The mfcc thingy
    Returns: a numpy array. 
    """
    # let's start by doing some basic feature extraction on the audio array with mfcc
    all_feat=[]
    idx=0
    audsamp=audio[idx]
    while idx<len(audio):
        try:
            f = librosa.feature.mfcc(y=audsamp,sr=44100,n_mfcc=13)
            f=f.reshape(f.shape[1])
            rms = librosa.feature.rmse(y=audsamp)
            rms=rms.reshape(rms.shape[1])
            f=np.concatenate((f,rms))
            zc=librosa.feature.zero_crossing_rate(y=audsamp)
            zc=zc.reshape(zc.shape[1])
            f=np.concatenate((f,zc))
            all_feat.append(f)
        except RuntimeWarning as e:
            print "DANG"
            print e
        idx+=1
    all_feat=np.array(all_feat)
    print "Shape of all_features: " + str(all_feat.shape)
    print "Size of all_features: " + str(all_feat.size)
    print all_feat
#    print "shape: " + str(all_feat.shape[0])
    #np.reshape(all_feat,all_feat.shape[0])
    #print "I will regret this"
    #print all_feat
    return all_feat #nonepy ha ha
    
def machine_learn(X,y):
    learner=svm.SVC(kernel="poly")    
    learner.fit(X[:-1],y[:-1])
    correct=0
    wrong=0
#    for idx in range(499):
    oc=learner.predict(X[-1])
     #   print "X: %s"%str(X[idx])
#        print "y: %s"%str(y[idx])
#        print oc
   # print "X: %s"%str(X[-1])
    print "y: %s"%str(y[-1])
    print oc
def get_xms(audio,dur):
    if dur%10!=0:
        print "The duration must be a multiple of 10 ms"
        return None
    dur=dur*44.1
    return audio[:dur]

def get_next_annotation_chunk(tier,start_pos,end_pos):
    #ann=tier.get_annotations_between_timepoints(start_pos,end_pos)
    ann=tier.get_annotations_by_time(start_pos)
    #if start_pos<100:
    #    print "start_pos: %d, annotation: %s"%(start_pos,ann[0].text)
    return ann
    
def get_textgrid(pth):
    tgrid=tgt.io.read_textgrid(filename=pth,encoding="utf-8",include_empty_intervals=True)
    return tgrid
    

def process_annotations(a): # where a is for the annotations
    # print "in process_annotations"
    # this is dealing with an Interval 
    # pretty simple: if there are annotations, determine that they are NOT laughter; return values accordingly
    # 0 for not speaking, 1 for speaking
    # print "in process_annotations"
    # print a
    if len(a)<1:
        #print "No annotation, aka no speaking"
        return 0
    for ann in a:
        #print "looking at annotations: "
#        print ann.text
        if re.search("laughter",ann.text,re.I) !=None:
            #print "found laughter, returning 0"
            return 2 # it's just laughter not speaking
        elif ann.text =="":
            return 0
        return 1 

def get_individual_tier(tg,tname):
    return tg.get_tier_by_name(tname)

def get_numpy_from_file(fpath):
    return wf.read(fpath)[1] # just the data; the rate is 44100 as per usual 
    
 
def highest_freq_speaker(tiers,end_length):
    speech=[]
    for tier in tiers:
        ones=0
        twos=0
        zeroes=0
        start=0
        while start<end_length:
            outcome=process_annotations(get_next_annotation_chunk(tier, start, (start+.20)))
            if outcome==0:
                zeroes+=1
            elif outcome==1:
                ones+=1
            elif outcome==2:
                twos+=1
            start+=.20
        speech.append(ones)
    highest=0
    for s in range(len(speech)):
        if speech[s]>highest:
            highest=speech[s]
            idx=s
    return tiers[idx]
    
def get_training_data(audio,tier):
    X=[] # new array of input
    y=[] # the output
    # so, get chunks of input and then output
    total=0
    start=0
    zeroes=0
    ones=0
    twos=0
    speaking=0
    silence=0
    while len(audio) >882:
        next_audio=get_xms(audio,20)
        audio=audio[882:]
        outcome=process_annotations(get_next_annotation_chunk(tier, start, (start+.20)))
        if outcome==0:
            zeroes+=1
            if silence<500:
                silence+=1
                X.append(next_audio)
                y.append(outcome)
            else:
                pass
        elif outcome==1:
            ones+=1
            if speaking<500:
                speaking+=1
                X.append(next_audio)
                y.append(outcome)
            else:
                pass
        elif outcome==2:
            twos+=1
        #print " The outcome was %d"%outcome
        start+=.20
        total+=1
    print "There are %d speaking and %d silence examples"%(speaking,silence)
    X=np.array(X,dtype="int16")
    y=np.array(y)
    return X,y 
    
    
def get_all_audiofiles(fpath,letter):
    # since there are only two kinds that are actually annotated, the Naming and Story tasks: 
    files=[]
    for dirs,subdirs,fnames in (os.walk(fpath)):
        for f in fnames:
            if f.startswith("._"):
                pass
            elif f.endswith(".wav"):
                # then it's the right kind of file. next step: make sure it's the right task 
                ns=re.search("(Naming|Story)",f,re.IGNORECASE)
                if ns!=None:
                    #ns=ns.group(1)
                    lm=re.search("_%s_"%letter,f,re.IGNORECASE)
                    if lm!=None:
                        #lm=lm.group(0)
                        files.append(f)
    return files
    
main()