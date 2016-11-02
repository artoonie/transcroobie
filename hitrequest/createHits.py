from enum import IntEnum

from boto.mturk.connection import MTurkConnection
from boto.mturk.connection import MTurkRequestError
from boto.mturk.question import ExternalQuestion
from boto.mturk.price import Price
from django.shortcuts import get_object_or_404

from . import overlap
from hitrequest.models import AudioSnippet
from transcroobie import settings

class AudioSnippetCompletionStatus(IntEnum):
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

    def createHitFrom(self, audioSnippet, hitType):
        if hitType == "fix":
            suffix = "fixHIT"
        elif hitType == "check":
            suffix = "checkHIT"
        else:
            assert False

        if settings.IS_DEV_ENV:
            baseurl = 'https://localhost:5000/hit/' + suffix
        else:
            baseurl = "https://transcroobie.herokuapp.com/hit/" + suffix
        title = "Transcribe the audio as best you can."
        description = "Transcribe the audio. Words may be cut off at the beginning"\
                      " or end of the segment. Do not worry about correctly"\
                      " transcribing these words."
        keywords = ["transcription"]
        frame_height = 800
        amount = 0.05

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

    def deleteAllHits(self):
        allHits = [hit for hit in self.connection.get_all_hits()]
        for hit in allHits:
            print "Disabling hit ", hit.HITId
            self.connection.disable_hit(hit.HITId)

    def processHit(self, questionFormAnswers):
        hitType = None
        response = None
        audioSnippet = None
        ans = []
        resp = []
        for questionFormAnswer in questionFormAnswers:
            ans.append(questionFormAnswer.qid)
            resp.append(questionFormAnswer.fields)
        for questionFormAnswer in questionFormAnswers:
            if questionFormAnswer.qid == "asFileId":
                asFileId = questionFormAnswer.fields[0]
                audioSnippet = get_object_or_404(AudioSnippet, pk = asFileId)
            elif questionFormAnswer.qid == "fixedHITResult":
                hitType = "fix"
                response = questionFormAnswer.fields[0]
            elif questionFormAnswer.qid == "checkedHITResult":
                hitType = "check"
                responseStr = questionFormAnswer.fields[0]
                response = [val == 'true' for val in responseStr.split(',')]

        assert response
        assert audioSnippet
        assert hitType
        return {
            'hitType': hitType,
            'response': response,
            'audioSnippet': audioSnippet
        }

    def getCompletionStatus(self, responseStruct):
        # only callwhen all hitTypes == "check"
        # returns an AudioSnippetCompletionStatus
        assert responseStruct['hitType'] == "check"
        MAX_NUM_PREDICTIONS = 2

        completionStatus = AudioSnippetCompletionStatus.incomplete
        audioSnippet = responseStruct['audioSnippet']
        if all(responseStruct['response']):
            completionStatus = AudioSnippetCompletionStatus.correct
            audioSnippet.hasBeenValidated = True
            audioSnippet.save()
        elif len(audioSnippet.predictions) > MAX_NUM_PREDICTIONS:
            completionStatus = AudioSnippetCompletionStatus.givenup
            audioSnippet.hasBeenValidated = True
            audioSnippet.save()
        return completionStatus

    def processHits(self):
        responseStructs = []

        audioSnippets = AudioSnippet.objects.order_by('id')
        responses = [a.predictions[-1] for a in audioSnippets]
        eachString = '\n'.join(responses)

        assignments = []
        for audioSnippet in audioSnippets:
            hitID = audioSnippet.activeHITId
            hit = self.connection.get_hit(hitID)
            asgnForHit = self.connection.get_assignments(hit[0].HITId)
            for asgn in asgnForHit:
                assignments.append(asgn)

        for assignment in assignments:
            questionFormAnswers = assignment.answers[0]
            responseStruct = self.processHit(questionFormAnswers)
            responseStructs.append(responseStruct)


        if all([x['hitType'] == 'check' for x in responseStructs]):
            statuses = [self.getCompletionStatus(x) for x in responseStructs]
            if all([s == AudioSnippetCompletionStatus.correct for s in statuses]):
                totalString = overlap.combineSeveral(responses)

                res = "Correct transcript:\n" + totalString
                res += "\n\n\nEach:\n" + eachString
                return res
            elif all([s == AudioSnippetCompletionStatus.correct or
                    s == AudioSnippetCompletionStatus.givenup for x in statuses]):
                totalString = overlap.combineSeveral(responses)
                res = "Potentially incorrect transcript. Our best guess is:\n"
                res += totalString
                res += "\n\n Unconfirmed strings marked with (*):\n"
                for i, s in enumerate(responses):
                    if statuses[i] == AudioSnippetCompletionStatus.givenup:
                        res += "* "
                    res += s + "\n"
                return res

        res = "Some AMT tasks still pending. HIT status: \n"

        for r in responseStructs:
            if r['audioSnippet'].hasBeenValidated:
                status = self.getCompletionStatus(r)
                if status == AudioSnippetCompletionStatus.correct:
                    res += "\n COMPLETE"
                elif status == AudioSnippetCompletionStatus.givenup:
                    res += "\n GIVEN UP"
                assert status != AudioSnippetCompletionStatus.incomplete
            elif r['hitType'] == "check" and self.isTaskReady(r['audioSnippet'].activeHITId):
                # CHECK task complete. Create a FIX task (since not # hasBeenValidated)
                self.createHitFrom(r['audioSnippet'], 'fix')
                res += "\n FIXIN UP"
            elif r['hitType'] == "fix" and self.isTaskReady(r['audioSnippet'].activeHITId):
                # FIX task complete. Create a CHECK task.
                self.createHitFrom(r['audioSnippet'], 'check')
                res += "\n VERIFYIN"
            res += str(r['audioSnippet'].id) + ":"
            res += " (" + r['audioSnippet'].predictions[-1] + ")"

        return res

    def isTaskReady(self, hitID):
        return len(self.connection.get_assignments(hitID)) > 0

    def approveAllHits(self):
        # Approve hits:
        for assignment in self.getAllAssignments():
            self.connection.approve_assignment(assignment.AssignmentId)

    def checkIfHitsReady(self):
        return True

    def getAllAssignments(self):
        allHits = [hit for hit in self.connection.get_all_hits()]

        # Approve hits:
        for hit in allHits:
            assignments = self.connection.get_assignments(hit.HITId)
            for assignment in assignments:
                yield assignment
