import math
import os
import tempfile

from pydub import AudioSegment

def basenameNoExt(filename):
    """ e.g. /foo/bar/baz.txt returns baz """
    return os.path.splitext(os.path.basename(filename))[0]

def splitAudioIntoParts(uploadedFilepath, extension, basedir):
    """ Yields the filename of a namedTemporaryFile,
        which is deleted at the next iteration. """
    assert os.path.exists(uploadedFilepath)

    track = AudioSegment.from_file(uploadedFilepath, extension[1:])
    sampleRate = track.frame_rate

    tracklen = len(track)
    overlap = 2*1000 # 2 seconds
    chunkBaseLength = 30*1000 # 30 seconds
    num_segments = int(math.ceil(tracklen / chunkBaseLength))
    basename = basenameNoExt(uploadedFilepath)

    # Iterate over every chunkBaseLength segment
    for i in range(0, num_segments):
        start_time = i*chunkBaseLength
        end_time = min((i+1)*chunkBaseLength+overlap, tracklen)
        curr_track = track[start_time:end_time]

        # Save the segment to a NamedTemporaryFile in basedir,
        # named after both the original filename and the part of the track.
        # Once the with completes, the file is deleted.
        with tempfile.NamedTemporaryFile(
                prefix = basename+"_",
                suffix = "_part%02d.wav"%i,
                dir = basedir) as currFilename:
            curr_track.export(currFilename.name, format="wav", bitrate="192k")
            yield (currFilename.name, sampleRate)
            return
