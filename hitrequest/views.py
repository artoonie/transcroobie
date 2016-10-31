import os
from urlparse import urlparse

from django.template import loader
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.core.files.base import File
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from hitrequest.models import Document, AudioSnippet
from hitrequest.forms import DocumentForm
from hitrequest.splitAudio import splitAudioIntoParts
from hitrequest.createHits import HitCreator
from hitrequest.speechrec import getTranscriptionFromURL

@csrf_exempt
def list(request):
    # Handle file upload
    request.upload_handlers.pop(0)
    return _list(request)

@csrf_protect
def _list(request):
    """ This is the trigger to take an uploaded file and create a HIT """
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            hitCreator = HitCreator()
            localFilename = request.FILES['uploadedFile']
            newdoc = Document(docfile = localFilename)
            newdoc.save() # TODO is this redundant?

            # Get the paths of each of the split fileparts
            for (tmpFileObject, sampleRate) in splitAudioIntoParts(localFilename,
                    basedir = settings.MEDIA_ROOT):
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

                    audioModel.save()
                    newdoc.audioSnippets.add(audioModel)

                    # Create a hit from this document
                    hitCreator.createHitFromAudioSnippet(audioModel)

            newdoc.save()

            # Redirect to the document list after POST
            return HttpResponseRedirect(reverse('list'))
    else:
        form = DocumentForm() # A empty, unbound form

    # Load documents for the list page
    documents = Document.objects.all()

    render_data = {'documents': documents,
                   'form': form}
    template = loader.get_template('hitrequest/list.html')
    response = template.render(render_data, request)

    return HttpResponse(response)

def _deleteDocument(docToDel):
    for audioSnippet in docToDel.audioSnippets.all():
        audioSnippet.audio.delete()
        audioSnippet.delete()
    docToDel.docfile.delete()
    docToDel.delete()

def delete(request):
    """ Delete one uploaded file """
    if request.method != 'POST':
        raise Http404

    docId = request.POST.get('selectedDoc', None)
    docToDel = get_object_or_404(Document, pk = docId)
    _deleteDocument(docToDel)

    return HttpResponseRedirect(reverse('list'))

def deleteAll(request):
    """ Delete all uploaded files """
    documents = Document.objects.all()
    for docToDel in documents:
        _deleteDocument(docToDel)

    return HttpResponseRedirect(reverse('list'))

def deleteAllHits(request):
    hitCreator = HitCreator()
    hitCreator.deleteAllHits()

    return HttpResponseRedirect(reverse('list'))

def processHits(request):
    hitCreator = HitCreator()
    text = hitCreator.processHits()

    render_data = {'processedHitText': text}
    template = loader.get_template('hitrequest/text.html')
    response = template.render(render_data, request)

    return HttpResponse(response)

def approveAllHits(request):
    hitCreator = HitCreator()
    hitCreator.approveAllHits()

    return HttpResponseRedirect(reverse('list'))
