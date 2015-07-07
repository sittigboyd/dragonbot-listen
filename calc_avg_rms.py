from pyaudio import PyAudio
import struct
import math
import wave




def calc_rms(block):
    rms=0
    n=len(block)
    for b in block:
        b = b / (2.**15)
        square=b*b
        rms+=square
        
    rms=math.sqrt(rms/n)
    return rms
    
def main():
    # read in some block data from pyaudio
    pa=PyAudio()
    wf=wave.open("/home/ksb/Documents/dreu/analysis/python_scripts/american_audio/American_2/American_2_A_4StoryTask.wav",'rb')
    strm=pa.open(format=pa.get_format_from_width(wf.getsampwidth()),
         channels=wf.getnchannels(),
         rate=wf.getframerate(),
         input=True)
         
    data=True
    fmt="%dh"%INPUT_FRAMES_PER_BLOCK
    while data:
        try:
            d=wf.readframes(INPUT_FRAMES_PER_BLOCK)
            d=struct.unpack(fmt,d)
            total_rms+=calc_rms(d)
        except:
            print "*** ERROR ***"
            data=False
    
    

main()    