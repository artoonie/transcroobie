from difflib import SequenceMatcher

class DidNotConvergeError(Exception): pass

def combine(a, b):
    def compare(x):
        ai, bi = int(x[0]), int(x[1])
        # print "Comparing ({}, {})".format(ai, bi)
        currRatio = SequenceMatcher(None, a[ai:].lower(), b[0:bi].lower()).ratio()
        length = (len(a) - ai) + bi
        currScore = length*currRatio*currRatio
        return currScore

    def visualize(x):
        import matplotlib.pyplot as plt

        fig = plt.figure(figsize=(6, 3.2))

        ax = fig.add_subplot(111)
        plt.imshow(x)
        ax.set_aspect('equal')
        plt.show()

    def bruteForce():
        x = []
        for aii in range(0, len(a)):
            x.append([])
            for bii in range(0, len(b)):
                x[aii].append(compare((aii, bii)))
        visualize(x)

    def sign(x):
        return 1 if x >= 0 else -1

    def gradAt(x):
        # Push x in bounds, at least 1 from boundary
        s = (a, b)
        x = [max(x[i], 1) for i in (0,1)]
        x = [min(x[i], len(s[i])) for i in (0,1)]

        curr = compare(x)
        ai = max(x[0], 1)
        bi = max(x[1], 1)

        # surroundX[0] = x-1, surroundX[1] = x+1
        surroundX = []
        for i in (-1, 1):
            surroundX.append([compare((ai+i, bi)), compare((ai, bi+i))])

        grad = [0,0]
        for dim in (0, 1):
            diffBack = curr - surroundX[0][dim]
            diffFore = surroundX[1][dim] - curr
            if sign(diffBack) != sign(diffFore):
                grad[dim] = 0
            else:
                grad[dim] = (diffFore + diffBack) / 2

        return grad

    beenHereBeforeList = {}
    def binarySearch(x, stepSize, numIters):
        x = (x[0], x[1])
        if x in beenHereBeforeList:
            return x
        else:
            beenHereBeforeList[x] = True

        if numIters > 100: raise DidNotConvergeError()

        g = gradAt(x)
        # print "{}: {}:   X = {},  grad = {}".format(numIters, stepSize, x, g)
        currStepMult = [1 if g[i] > 0 else -1 for i in (0,1)]
        currX = [x[i] + currStepMult[i]*stepSize[i] for i in (0,1)]

        if all([gv == 0 for gv in g]):
            return currX
        else:
            s = (a, b)
            currX = [min(max(0, currX[i]), len(s[i])) for i in (0,1)]
            currStepSize = [max(stepSize[i] / 2, 1) for i in (0,1)]
            return binarySearch(currX, currStepSize, numIters+1)

    x = binarySearch((5,5), (len(a)/2, len(b)/2), 0)

    ai = int(x[0])
    bi = int(x[1])

    # bruteForce()

    # Accept the version with more characters
    alen = len(a)-ai
    blen = bi
    if alen > blen:
        return bi, "B"
        # output = a + b[bi+1:]
    else:
        return ai, "A"
        # output = a[:ai] + b
    # print "A:", alen, a + b[bi:]
    # print "B:", blen, a[:ai] + b

    # print
    # print
    # print a
    # print ' '*ai + "^"

    # print
    # print b
    # print ' '*bi + "^"
    return output

def combineSeveral(listOfStrings):
    results = []
    for i in range(len(listOfStrings)-1):
        results.append(combine(listOfStrings[i], listOfStrings[i+1]))

    for i in range(len(results)):
        index, whichString = results[i]
        if whichString == "A":
            # Truncate the first string, removing the end
            listOfStrings[i] = listOfStrings[i][:index]
        else:
            # Truncate the second string, removing the beginning
            listOfStrings[i+1] = listOfStrings[i+1][index+1:]

    return '\n'.join(listOfStrings)

if __name__ == "__main__":
    a = "is not a problem today, screens are everywhere, but when you were a START younger sibling back when you FIX FIX"
    b = "younger sibling, back when you FIX FIX pretty much had one television in the house, you either complained a lot"
    c = "complained a lot or decided it was time to eat some cheese"
    d = "some cheetos is what you need at times"
    try:
        print combineSeveral([a, b, c, d])
        output = combine(b, c)
    except DidNotConvergeError:
        print "Failed to converge."
