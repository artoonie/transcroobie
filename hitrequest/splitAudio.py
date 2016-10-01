import math
import os
import tempfile

from pydub import AudioSegment

def basenameNoExt(filename):
    """ e.g. /foo/bar/baz.txt returns baz """
    return os.path.splitext(os.path.basename(filename))[0]

def splitAudioIntoParts(uploadedFilename, basedir):
    """ Yields the filename of a namedTemporaryFile,
        which is deleted at the next iteration. """
    assert os.path.exists(uploadedFilename)
    track = AudioSegment.from_mp3(uploadedFilename)
    tracklen = len(track)
    two_seconds = 10*1000
    ten_seconds = 10*1000
    num_segments = int(math.ceil(tracklen / ten_seconds))
    basename = basenameNoExt(uploadedFilename)

    # Iterate over every ten-second segment
    overlap = two_seconds
    for i in range(0, num_segments):
        start_time = i*ten_seconds
        end_time = min((i+1)*ten_seconds+overlap, tracklen)
        curr_track = track[start_time:end_time]

        # Save the segment to a NamedTemporaryFile in basedir,
        # named after both the original filename and the part of the track.
        # Once the with completes, the file is deleted.
        with tempfile.NamedTemporaryFile(
                prefix = basename+"_",
                suffix = "_part%02d.mp3"%i,
                dir = basedir) as currFilename:
            curr_track.export(currFilename.name, format="mp3")
            yield currFilename.name
