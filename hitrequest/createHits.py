from enum import IntEnum

from boto.mturk.connection import MTurkRequestError
from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
from boto.mturk.price import Price
from django.shortcuts import get_object_or_404

from . import overlap
from hitrequest.models import AudioSnippet
from transcroobie import settings
from hit.transcriptProcessUtils import transcriptWithSpacesAndEllipses,\
                                       combineConsecutiveDuplicates
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

class CompletionStatus(IntEnum):
    incomplete = 0,
    correct = 1,
    givenup = 2,

class HitCreator():
    def __init__(self):
        if settings.IS_DEV_ENV or settings.USE_AMT_SANDBOX:
            HOST = 'mechanicalturk.sandbox.amazonaws.com'
        else:
            HOST = 'mechanicalturk.amazonaws.com'

        self.connection = MTurkConnection(
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                host=HOST)

    def createHitFrom(self, audioSnippet, hitType, numIncorrectWords=None):
        if hitType == "fix":
            suffix = "fixHIT"
            # half cent per incorrect word, up to eight words
            assert isinstance(numIncorrectWords, int)
            amount = max(min(.05, numIncorrectWords*.005), .02)
        elif hitType == "check":
            suffix = "checkHIT"
            amount = 0.05
        else:
            assert False

        if settings.IS_DEV_ENV:
            baseurl = 'https://localhost:5000/hit/' + suffix
        else:
            baseurl = "https://transcroobie.herokuapp.com/hit/" + suffix
        title = "Transcribe a short audio clip."
        description = "Transcribe the audio. Words may be cut off at the beginning"\
                      " or end of the segment. Do not worry about correctly"\
                      " transcribing these words."
        keywords = ["transcription"]
        frame_height = 800

        thisDocUrl = baseurl + "?docId=" + str(audioSnippet.pk)
        questionform = ExternalQuestion(thisDocUrl, frame_height)

        resultSet = self.connection.create_hit(
            title=title,
            description=description,
            keywords=keywords,
            max_assignments=1,
            question=questionform,
            reward=Price(amount=amount),
            response_groups=('Minimal', 'HITDetail'),  # I don't know what response groups are
        )
        assert len(resultSet) == 1
        audioSnippet.activeHITId = resultSet[0].HITId
        audioSnippet.save()

    def deleteHit(self, hitID):
        try:
            self.connection.disable_hit(hitID)
        except MTurkRequestError as e:
            print "HIT already deleted", e

    def deleteAllHits(self):
        allHits = [hit for hit in self.connection.get_all_hits()]
        for hit in allHits:
            print "Disabling hit ", hit.HITId
            self.deleteHit(hit.HITId)

    def processHit(self, questionFormAnswers):
        # Process each HIT only once. This function will set activeHITId to ""
        # to let you know that the HIT is completed and processed.
        hitType = None
        response = None
        audioSnippet = None
        fixWords = {}
        for questionFormAnswer in questionFormAnswers:
            if questionFormAnswer.qid == "asFileId":
                asFileId = questionFormAnswer.fields[0]
                audioSnippet = get_object_or_404(AudioSnippet, pk = asFileId)
            elif questionFormAnswer.qid == "fixedHITResult":
                hitType = "fix"
                response = None # need to look at word_%d based on audiosnippet
            elif questionFormAnswer.qid.startswith("word_"):
                fixWords[questionFormAnswer.qid] = questionFormAnswer.fields[0]
            elif questionFormAnswer.qid == "checkedHITResult":
                hitType = "check"
                responseStr = questionFormAnswer.fields[0]
                response = [val == 'true' for val in responseStr.split(',')]

        numIncorrectWords = 0
        if hitType == "fix":
            # Get the list of words marked incorrect, and count them
            incorrectWords = audioSnippet.incorrectWords['bools'][-1]
            numIncorrectWords = len(incorrectWords)-sum(incorrectWords)

            # Get the last prediction to interpret incorrectWords
            prediction = audioSnippet.predictions[-1].split()

            # Convert the last prediction to what was actually sent to
            # the user
            predictionSpaced = transcriptWithSpacesAndEllipses(prediction)
            assert len(incorrectWords) == len(predictionSpaced)
            words, isCorrect = combineConsecutiveDuplicates(predictionSpaced,
                    incorrectWords)

            response = ""
            for i in xrange(len(words)):
                if not isCorrect[i]:
                    response += fixWords["word_" + str(i)] + " "
                else:
                    # Only add punctuation (" ") and ellipses if marked incorrect
                    word = words[i]
                    if word.isspace() or word == "":
                        continue
                    elif i == 0 and word.startswith("..."):
                        word = word[3:] # remove initial ellipses
                    elif i == len(words)-1 and word.endswith("..."):
                        word = word[:-3] # remove trailing ellipses
                    response += word.strip() + " "
            audioSnippet.predictions.append(response)

            # Always do a check after a fix
            completionStatus = CompletionStatus.incomplete
        else:
            audioSnippet.incorrectWords['bools'].append(response)
            completionStatus = self.getCompletionStatus(audioSnippet, response)
            if completionStatus == CompletionStatus.correct:
                audioSnippet.hasBeenValidated = True
                audioSnippet.isComplete = True
            elif completionStatus == CompletionStatus.givenup:
                audioSnippet.hasBeenValidated = False
                audioSnippet.isComplete = True
        audioSnippet.activeHITId = ""

        if completionStatus == CompletionStatus.incomplete:
            if hitType == "check":
                # CHECK task complete. Create a FIX task (since not # hasBeenValidated)
                self.createHitFrom(audioSnippet, 'fix', numIncorrectWords)
            elif hitType == "fix":
                # FIX task complete. Create a CHECK task.
                self.createHitFrom(audioSnippet, 'check')

        audioSnippet.save()

    def getCompletionStatus(self, audioSnippet, response):
        # only callwhen all hitTypes == "check"
        # returns a CompletionStatus
        MAX_NUM_PREDICTIONS = 0 # TODO test what if we just did google?

        completionStatus = CompletionStatus.incomplete
        if all(response):
            completionStatus = CompletionStatus.correct
        elif len(audioSnippet.predictions) > MAX_NUM_PREDICTIONS:
            completionStatus = CompletionStatus.givenup
        return completionStatus

    def processHits(self, doc):
        """ Returns whether or not the doc had a newly-completed HIT
            which was processed. """
        assert not doc.completeTranscript
        audioSnippets = doc.audioSnippets.order_by('id')

        newHITCompleted = False
        assignments = []
        for audioSnippet in audioSnippets:
            hitID = audioSnippet.activeHITId
            if not hitID: continue
            hit = self.connection.get_hit(hitID)
            asgnForHit = self.connection.get_assignments(hit[0].HITId)
            if asgnForHit:
                # Hit is ready. Get the data.
                for asgn in asgnForHit:
                    assignments.append(asgn)
                    questionFormAnswers = asgn.answers[0]
                    self.processHit(questionFormAnswers)
                    newHITCompleted = True

        responses = [a.predictions[-1] for a in audioSnippets]
        statuses = [a.isComplete for a in audioSnippets]
        if all([a.hasBeenValidated for s in statuses]) or \
                all([a.isComplete for a in audioSnippets]):
            # All tasks complete for first time
            totalString = overlap.combineSeveral(responses)
            doc.completeTranscript = totalString
            doc.save()

        return newHITCompleted

    def isTaskReady(self, hitID):
        return len(self.connection.get_assignments(hitID)) > 0

    def approveAllHits(self):
        # Approve hits:
        for assignment in self.getAllAssignments():
            try:
                self.connection.approve_assignment(assignment.AssignmentId)
            except MTurkRequestError as e:
                # Maybe already approved?
                logger.error("MTurk Request Error: " + str(e))

    def checkIfHitsReady(self):
        return True

    def getAllAssignments(self):
        allHits = [hit for hit in self.connection.get_all_hits()]

        # Approve hits:
        for hit in allHits:
            assignments = self.connection.get_assignments(hit.HITId)
            for assignment in assignments:
                yield assignment
