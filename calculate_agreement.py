#TODO wow it highlighted it

from pympi import Praat
import tgt
import re


class CohenKappaCalculator:
    def __init__(self):
        # is this too long? we just don't know 
        self.yes_both=0
        self.no_both=0
        self.yes_a=0
        self.yes_b=0
        
    
    
    
    
    
    
    
def main():
    yes_both=0
    no_both=0
    yes_a=0
    yes_b=0
    print "Let's calculate Cohen's Kappa, kids. Does anybody want to do this No. Nobody wants to do this."
    byhand=["/home/ksb/Documents/dreu/analysis/python_scripts/american_audio/TextGrids/American_2_Naming_Stephanie.TextGrid"]
    bymachine=["/home/ksb/Documents/dreu/analysis/python_scripts/dragonbot-listen/annotations_higher_rms/American_2_A_3NamingTask.TextGrid"]
    idx=0 # later stick in for loop
    tg_a=tgt.io.read_textgrid(filename=byhand[idx], encoding='utf-8', include_empty_intervals=False)
    tg_b=tgt.io.read_textgrid(filename=bymachine[idx], encoding='utf-8', include_empty_intervals=False)
    start=0
    ANNOTATION_CHUNK_TIME=1 # milliseconds
    end=tg_a.end_time
    for tier in tg_a.get_tier_names():
        tiersearch=re.search("\(A\)",tier,re.IGNORECASE)
        if tiersearch!=None:
            a_name=tier
            break
            
    speech_A=tg_a.get_tier_by_name(a_name)
    speech_B=tg_b.get_tier_by_name("default_speech")
    while start<end:
        
        annotation_A=speech_A.get_annotations_between_timepoints(start,start+ANNOTATION_CHUNK_TIME,left_overlap=True,right_overlap=True)
        annotation_B=speech_B.get_annotations_between_timepoints(start,start+ANNOTATION_CHUNK_TIME,left_overlap=True,right_overlap=True)        
        # determine whether or not they match
        if len(annotation_A)>0 and len(annotation_B)>0:
            # they agree on yes
            yes_both+=1
        elif len(annotation_A)>0:
            yes_a+=1
        elif len(annotation_B)>0:
            yes_b+=1
        else:
            no_both+=1
        
        start+=ANNOTATION_CHUNK_TIME
        
    print "number of times they both agree: ",yes_both
    print "just A said yes: ",yes_a
    print "just B said yes: ",yes_b
    print "both agreed no: ",no_both
    kap_array=[yes_both,yes_a,yes_b,no_both]
    print "kappa: ",calculate_kappa(kap_array)
        
def calculate_kappa(agree):
    total=0
    for x in agree:
        total+=x
    a=agree[0]
    b=agree[1]
    c=agree[2]
    d=agree[3]
    Pa  = float(a + d)/total
    PA1 = float(a + b)/total
    PA2 = 1.0- PA1
    PB1 = float(a + c) /total
    PB2 = 1.0 -PB1
    Pe  = PA1 *PB1 + PA2*PB2
    #print Pa, PA1, PB1, PA2, PB2
    return (Pa -Pe)/ (1.0 -Pe)

        
main()









