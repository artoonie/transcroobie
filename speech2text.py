import math
from pydub import AudioSegment
import sys

if len(sys.argv) != 2:
    print 'usage speech2text.py filename'
    exit(1)

track = AudioSegment.from_mp3(sys.argv[1])
tracklen = len(track)
ten_seconds = 10*1000
num_segments = math.ceil(tracklen / ten_seconds)
for i in range(0, ten_seconds):
    start_time = i*ten_seconds
    end_time = min((i+1)*ten_seconds, tracklen)
    curr_track = track[start_time:end_time]
    print "track%02d.mp3"%i
    curr_track.export("tracks/track%02d.mp3"%i, format="mp3")
