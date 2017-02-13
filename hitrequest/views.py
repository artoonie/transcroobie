import os
from urlparse import urlparse

from boto.exception import GSResponseError
from celery.utils.log import get_task_logger
from django.template import loader
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.core.files.base import File
from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.auth.decorators import login_required

from hitrequest.models import Document, AudioSnippet
from hitrequest.forms import DocumentForm
from hitrequest.splitAudio import splitAudioIntoParts
from hitrequest.createHits import HitCreator
from hitrequest.speechrec import getTranscriptionFromURL
from transcroobie.celery import app

logger = get_task_logger(__name__)

@csrf_exempt
@login_required
def index(request):
    # Handle file upload
    request.upload_handlers.pop(0)
    return _list(request)

@csrf_protect
def _list(request):
    """ This is the trigger to take an uploaded file and create a HIT """
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            uploadedFile = request.FILES['uploadedFile']
            newdoc = Document(docfile = uploadedFile)
            newdoc.save()

            usersFilename = uploadedFile.name
            _, extension = os.path.splitext(usersFilename)

            # Delay processing so we can return a file soon
            _processUploadedDocument.delay(newdoc.id, extension)

            # Redirect to the document list after POST
            return HttpResponseRedirect('index.html')
    else:
        # Spawn a processHitTask every refresh
        _processHitsTask(doSpawn=False)

        form = DocumentForm() # A empty, unbound form

    # Load documents for the list page
    documents = Document.objects.all()

    render_data = {'documents': documents,
                   'form': form}
    template = loader.get_template('hitrequest/list.html')
    response = template.render(render_data, request)

    return HttpResponse(response)

@app.task(name="_processUploadedDocument")
def _processUploadedDocument(docId, extension):
    # Extension should include leading '.'
    import tempfile

    newdoc = get_object_or_404(Document, pk = docId)
    logger.info("Processing document: " + newdoc.docfile.url)


    tmpFile = tempfile.NamedTemporaryFile(suffix=extension)
    uploadedFile = newdoc.docfile
    with open(tmpFile.name, 'wb+') as dest:
        dest.write(uploadedFile.read())

    hitCreator = HitCreator()

    # Get the paths of each of the split fileparts
    i = 0
    for (tmpFileObject, sampleRate) in splitAudioIntoParts(tmpFile.name,
            extension, basedir = settings.MEDIA_ROOT):
        logger.info("   Processing part {}".format(i))
        relPath = os.path.relpath(tmpFileObject, settings.MEDIA_ROOT)

        # Open the file, copy into to the database's storage.
        # TODO - inefficient copying - how can splitAudioIntoParts
        # write directly into the correct location?
        with open(tmpFileObject) as fileObj:
            fileCopy = File(file=fileObj, name=relPath)

            audioModel = AudioSnippet(audio = fileCopy,
                                      hasBeenValidated = False,
                                      predictions = [])

            # Get the transcript
            audioModel.save() # upload fileCopy
            url = "gs://"+settings.GS_BUCKET_NAME+urlparse(audioModel.audio.url).path
            text, confidence = getTranscriptionFromURL(url, sampleRate)
            audioModel.predictions.append(text)
            if float(confidence) > .99:
                audioModel.hasBeenValidated = True

            # Create a hit from this document
            hitCreator.createHitFrom(audioModel, 'check')
            newdoc.audioSnippets.add(audioModel) # this saves audioModel
        logger.info("   Completed part  {}".format(i))
        i += 1

    newdoc.save()
    _processHitsTask.apply_async([True, 10],countdown=60) # wait a minute before processing

def _deleteDocument(docToDel):
    hitCreator = None
    for audioSnippet in docToDel.audioSnippets.all():
        audioSnippet.audio.delete()
        if audioSnippet.activeHITId:
            if not hitCreator:
                # delay creation - I think this tries to connect to AMT on init
                hitCreator = HitCreator()
            hitCreator.deleteHit(audioSnippet.activeHITId)
        audioSnippet.delete()
    try:
        # The file may have been deleted remotely or not successfully uploaded
        docToDel.docfile.delete()
    except GSResponseError:
        pass

    docToDel.delete()

@login_required
def delete(request):
    """ Delete one uploaded file """
    if request.method != 'POST':
        raise Http404

    docId = request.POST.get('selectedDoc', None)
    docToDel = get_object_or_404(Document, pk = docId)
    _deleteDocument(docToDel)

    return redirectToIndex()

@login_required
def deleteAll(request):
    """ Delete all uploaded files """
    documents = Document.objects.all()
    for docToDel in documents:
        _deleteDocument(docToDel)

    audioSnippets = AudioSnippet.objects.all()
    for audioSnippet in audioSnippets:
        audioSnippets.delete()

    return redirectToIndex()

@login_required
def deleteAllHits(request):
    hitCreator = HitCreator()
    hitCreator.deleteAllHits()

    return redirectToIndex()

@app.task(name="_processHitsTask")
def _processHitsTask(doSpawn, spawnTimeout=None):
    """ doSpawn: if there are unprocessed HITs, spawn more tasks?
                 be careful not to recursively spawn a zillion jobs. """
    docs = Document.objects.order_by('id')
    hitCreator = HitCreator()
    hasAnyHITCompleted = False
    areAllHITsDone = True
    for doc in docs:
        if doc.completeTranscript:
            continue

        newHITCompleted = hitCreator.processHits(doc)
        hasAnyHITCompleted |= newHITCompleted

        if doc.completeTranscript:
            # Check again after processing
            areAllHITsDone = False

    if doSpawn and not areAllHITsDone:
        assert spawnTimeout
        # If a HIT completes, halve the countdown time.
        # Else, double it.
        nextCountdownMult = 2 if not hasAnyHITCompleted else 0.5
        nextCountdown = spawnTimeout * nextCountdownMult
        if spawnTimeout > 60 * 60 * 24: # one day
            logger.info("Waiting {} seconds before looking for more HITs.".format(
                    nextCountdown))
            _processHitsTask.apply_async([True, nextCountdown], countdown=spawnTimeout)
        else:
            logger.error("Waited a day and still no HITs ready")

@login_required
def approveAllHits(request):
    hitCreator = HitCreator()
    hitCreator.approveAllHits()

    return redirectToIndex()

def redirectToIndex():
    return HttpResponseRedirect('../index.html')
