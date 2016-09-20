import os
from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
from boto.mturk.price import Price

class HitCreator():
    def __init__(self):
        AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
        AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

        if os.environ.get("I_AM_IN_DEV_ENV") or os.environ.get("USE_AMT_SANDBOX"):
            HOST = 'mechanicalturk.sandbox.amazonaws.com'
        else:
            HOST = 'mechanicalturk.amazonaws.com'

        self.connection = MTurkConnection(
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                host=HOST)

    def createHitFromDocument(self, document):
        if os.environ.get("I_AM_IN_DEV_ENV"):
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
