from itertools import groupby

def transcriptWithSpacesAndEllipses(transcriptList):
    """ Add a space between each word, and add ellipses before/after """
    assert transcriptList
    withSpaces = addSpaceToTranscriptList(transcriptList)
    withEllipses = ["..."]
    withEllipses.extend(withSpaces)
    withEllipses.append("...")
    return withEllipses

def addSpaceToTranscriptList(transcriptList):
    """ Append a space between every word for punctuation """
    spacedtranscript = [' ']*(2*len(transcriptList))
    spacedtranscript[0::2] = transcriptList
    del spacedtranscript[-1] # space before last ellipses

    # Note: the order of these deletions is important. Don't throw off indexing.
    # del spacedtranscript[-3] # space before last ellipses
    # del spacedtranscript[-1] # space after last ellipses
    # del spacedtranscript[1] # space after first ellipses

    return spacedtranscript

def combineConsecutiveDuplicates(transcriptList, isCorrectList):
    # Combine consecutive duplicates
    combinedTranscript = []
    combinedStatus = []
    for group in groupby(zip(transcriptList, isCorrectList),
            lambda f: f[1]): # lambda to sort by the bools in isCorrectList
        combinedStatus.append(group[0])
        combinedTranscript.append(" ".join([tuple[0] for tuple in group[1]]))
    return combinedTranscript, combinedStatus
