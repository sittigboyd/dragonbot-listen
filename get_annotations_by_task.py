import pympi
from pympi import Praat
import re
import os
#import aifc 
from pydub import AudioSegment as audseg
import tgt
from tgt import TextGrid

elan_path="/media/UTEP-ICT/Completed Annotations/Speech Type - Rhianna/"
data_path="/media/UTEP-ICT/Data/UTEP-ICT_audio/"
test_path="/media/UTEP-ICT/"
task_path="/media/UTEP-ICT/Data/interaction_lab_version/american_split_by_task/audio/"

def main():
    # a dictionary of the form filename: {tier_name:[annotations]}
    annotation_dicts={} 
    # a dictionary for the audio files of the form {AudioSegment:TextGrid}
    audio_dict={}
    praat_textgrids={} # a dictionary of the form filename: TextGrid object
    for filename in get_all_files(elan_path):
        files_added=0 # start fresh
        print "Adding information for %s"%filename
        # note: the filename is actually just the name of the file
#        print "Filepath: %s"%filename
        elan_file=pympi.Elan.Eaf((elan_path+filename),author="")
        tiernames=elan_file.get_tier_names()
        
        # for a single file
        all_annotations={} 
        """
        # this loop walks through each tier in the singular .eaf file, finds all of the annotations, and stores them in the dictionary
        for tn in tiernames: 
            # find tiers that have to do with speech
            speech=re.search("Speech",tn,re.IGNORECASE) 
            if speech!=None:                
                # if there's a match, add to the annotations dictionary for the file
                all_annotations[tn]=elan_file.get_annotation_data_for_tier(tn) 
        # add the dictionary of the tier names and annotations to the dictionary of file:{tn:{[annotations]}}
        annotation_dicts[filename]=all_annotations 
        Comment back if useful
        """
        
        # returns the name of a directory and a list of the files associated with it
        aud_directory,audio_files=find_corresponding_audio(filename) 
        #print "aud directory: %s"%aud_directory
#        ttadd=conv_to_tg(elan_file,annotation_dicts[filename].keys())
# ADD BACK IN?        praat_textgrids[(elan_path+filename)]=ttadd
# ADD BACK IN?        for fn in praat_textgrids.keys():
        fpath=filename[:len(filename)-3]+"TextGrid"
        ttadd=tgt.io.read_textgrid((elan_path+fpath),encoding="utf-8")
        # NOW, get the tiers
        audio_dict[filename]={}
        for t in ttadd.get_tier_names():
            for f in audio_files:
                letter=re.search("\(([ABCD])\)",t)
                
                if letter!=None:
                    letter=letter.group(1)
                    # then, find the corresponding audio!!
                    #print " Found the letter, line 50: %s"%letter
                    #print "Currently in directory %s"%aud_directory
                # NOW find the naming/story AND the letter and we'll be good
                    fmatch=re.search("(Naming|Story)",f,re.IGNORECASE)
                    if fmatch!=None:
                        ns=fmatch.group(1) # either Naming or Story depending
                        tns=re.search("(Naming|Story)",filename,re.IGNORECASE)
                        if tns!=None:
                            tns=tns.group(1)

                            if tns==ns:
                                reg="_(%s)_"%letter
            #                   print "regular expression=%s"%reg
                                aud_letter=re.search(reg,f)
                                if aud_letter!=None and aud_letter.group(1)==letter:
#                                    print "found it in if at %s on line 70"%f
            #                        print "YEAH"
                                    #print "Found file %s to match %s from %s"%(f,t,fn)
                                    tofile=aud_directory+f
                            #print " Great, going to turn this into an audioseg: %s"%tofile
                                    next_chunk=audseg.from_file(tofile,format="wav") 
                                    # Cool, now we have to get the corresponding tier from the text grid, aka ttadd
                                    # We already have the name, that is, t! So, now we just have to get that tier_name
                                    right_tier=ttadd.get_tier_by_name(t) # returns a tier
                                    audio_dict[filename][right_tier]=next_chunk # so this will set the appropriate TextGrid as the key to a Tier, which is the key for an AudioSegment
                                    files_added+=1
                                
                                #print "Just checking that the dictionary works. Here's the first tier type: "
                                #print audio_dict[ttadd].keys()[0].tier_type()
                                #print " And here's a count of frames from the audiosegment associated with that tier: "
                                #print str(audio_dict[ttadd][right_tier].frame_count())
                        # once all of the files hav been walked through, we'll have a full dictionary of TextGrid objects and lists of AudioSegment objects
        print "For %s, %d files were added (should be approx 4-8)"%(filename,files_added)
        #break
    sound_to_annotation_dict=get_sound_and_tier_dict(audio_dict)
    print "That's all for today, folks"

#            all_clips=get_all_clips(next_chunk)
def conv_to_tg(elan_file,tiers):
    # accepts a SINGLE file handle and a list of the tiers to include and converts it to praat textgrid form
    # just make sure the tiers match in terms of
    return elan_file.to_textgrid(filtin=tiers) # includes only the speech related tiers
    
def get_sound_and_tier_dict(adict):
    """
    Accepts: A horrible brainchild of the form:
    {TextGrid:{Tier:AudioSegment}} (actually it isn't that bad)
    
    Two ideas: one, store them in a list of tuples (chronologically); two, store them in two parallel lists (aka a tuple of lists)
    
    I like the tuple idea better, but I also think that it needs to be another dictionary (by textgrid, aka narrative task).
    idea: return {TextGrid:{tier:[(sound,annotation),(sound,annotation),etc.]}}
    """

    # first, get the dictionary ready!!!! 
    
    print " about to make some sick tuples"
    tuple_dict={} # key: textgrid, value: dictionary (key: tier, value: a list of tuples in chronological order of 200ms chunks of sound and annotations)
    
    # ok great so let's start with the keys, aka the TextGrids (which map to tiers, which map to the audio)
#    tkey=adict.keys()[0] # FOR STARTERS so I don't have to test on all of them, ha ha. gets first TextGrid.
#    tier=adict[tkey].keys()[0] # same thing, gets the first tier + audio. DOES NOT MATTER if the tiers are in order A,B,C,D bc they are arbitrary anyway
    total_tiers=0
    for tkey in adict.keys():
        for tier in adict[tkey].keys():
            total_tiers+=1
            audio=adict[tkey][tier]
            # So, now that I have the tier and the according audio, I can start getting the small chunks :)
            sound_ann=[] # list, soon to be filled with tuples
            start=0
            total_seg=0
            while len(audio)>200: # in ms
                clip=get_next_clip(audio,start,200)
                seg=get_next_annotation_chunk(tier,start,200) 
                start+=200
                audio=audio[start:]
                tuple_dict[tkey]={tier:""}
                tuple_dict[tkey][tier]= (clip,seg) # basic. next step: lists of tuples of all of those sounds and annotations. (sound, annotation)
                total_seg+=1
    #        print "For that tier, there were %d annotation and sound chunks"%total_seg
    #print "There were %d total tiers"%total_tiers
    return tuple_dict

def process_audio(audio_clip):
    # do some sick rad meme things
    
    # Okay, this is what I need to do today. There are a few versions of this: first, look into like... sound levels or sth?
    # Or look at the words 
    # etc
    
    return None
    

def get_next_clip(sound,start_pos,interval):
    clip=sound[start_pos:start_pos+interval]
    return clip
   
def get_next_annotation_chunk(tier,start_pos,interval):
    ann=tier.get_annotations_between_timepoints(start_pos,(start_pos+interval),left_overlap=True,right_overlap=True)
    return ann
  

def find_start_pos(ptg): # where ptg is a text grid
    tg=tgt.io.read_textgrid(filename=ptg)
    print "COOL BEANS"
    return tg.start_time
    
    
def get_all_files(direc):
    # returns all files associated with a single group, ie, American 1 <-- returns multiple files from the same directory
    files=[]
    for dirs,subdirs,fnames in (os.walk(direc)):
        for f in fnames:
            if f.startswith("._"):
                pass
            elif f.endswith(".eaf"):
                files.append(f)
                print f
    return files
    
def find_corresponding_audio(efile):
#    print "Looking for the directory associated with %s"%efile
    direc=""
    files=[]
    nationalities=["american","mexican","arab"]
    for n in nationalities:
        n=re.search(n,efile,re.IGNORECASE)
        if n!=None:
            nat=n.group(0)
    number=re.search("[0-9]",efile)
    number=number.group(0)
    for dirs,subdirs,fnames in (os.walk(task_path)):
        for d in subdirs:
            if re.search(nat,d,re.IGNORECASE)!=None and re.search(number,d)!=None:
                direc=d
            if direc==d:
                break
        if direc!="":
            print "The directory is: %s"%direc
            break
    direc=(task_path+direc+"/")
    #print direc
    #print "so far so good"
    # great, next step: find all four audio files (A.aiff, B.aiff, C.aiff, D.aiff)
    for dirs,subdirs,fnames in (os.walk(direc)):
        for fname in fnames:
            if fname.endswith(".wav"):
                fmatch=re.search("(Naming|Story)",fname,re.IGNORECASE)
                if fmatch!=None:
#                    print "Found file %s -- check it out"%fname
                    files.append(fname)
    return direc,files

def get_slice(sound):
    return sound[:200],sound[200:]
    
def get_all_clips(afile):
    allclips=[]
    clips_processed=0
    while len(afile)>200:
        clip=afile[:200]
        allclips.append(clip)
        afile=afile[200:]
        clips_processed+=1
    print "Total clips: "+str(clips_processed)
    return allclips

def get_length(sound):
    # returns the length of the audio clip in milliseconds
    return len(sound)    
# next step: break up text grids in praat into 200 ms chunks as well
def read_tg(tgpath):
    all_segs=[]
    tgrid=tgt.io.read_textgrid(filename=tgpath,encoding="utf-8",include_empty_intervals=True)
    all_tiers=tgrid.tiers
    start=0
    print "End time: " + str(tgrid.end_time)
    for tier in all_tiers:
        while (start+.200) < tgrid.end_time:
            seg=tier.get_annotations_between_timepoints(start,(start+.200),left_overlap=True,right_overlap=True)
            all_segs.append(seg)
            start+=.200
            print str(start)
            print str(seg)
        print "There are " + str(len(all_segs)) + " segments"
    return all_segs
    
def process_annotations(ann):
    print "figure out"

main()
