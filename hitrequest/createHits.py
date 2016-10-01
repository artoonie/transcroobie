from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
from boto.mturk.price import Price
from transcroobie import settings

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

    def createHitFromDocument(self, document):
        if settings.IS_DEV_ENV:
            baseurl = 'https://localhost:5000/hit/'
        else:
            baseurl = "https://transcroobie.herokuapp.com/hit/"
        title = "Transcribe the audio as best you can."
        description = "Transcribe the audio. Words may be cut off at the beginning"\
                      " or end of the segment. Do not worry about correctly"\
                      " transcribing these words."
        keywords = ["transcription"]
        frame_height = 800
        amount = 0.05

        thisDocUrl = baseurl + "?docId=" + str(document.pk)
        questionform = ExternalQuestion(thisDocUrl, frame_height)

        create_hit_result = self.connection.create_hit(
            title=title,
            description=description,
            keywords=keywords,
            max_assignments=1,
            question=questionform,
            reward=Price(amount=amount),
            response_groups=('Minimal', 'HITDetail'),  # I don't know what response groups are
        )
        print "Created hit", create_hit_result

    def deleteAllHits(self):
        allHits = [hit for hit in self.connection.get_all_hits()]
        for hit in allHits:
            print "Disabling hit ", hit.HITId
            self.connection.disable_hit(hit.HITId)

    def processHits(self):
        allHits = [hit for hit in self.connection.get_all_hits()]
        responses = []

        # Approve hits:
        for hit in allHits:
            assignments = self.connection.get_assignments(hit.HITId)
            for assignment in assignments:
                # don't ask me why this is a 2D list
                question_form_answers = assignment.answers[0]
                for question_form_answer in question_form_answers:
                    # "user-input" is the field I created and the only one I care about
                    if question_form_answer.qid == "user-input":
                        user_response = question_form_answer.fields[0]
                        responses.append(user_response)
                #self.connection.approve_assignment(assignment.AssignmentId)
        return '\n'.join(responses)
