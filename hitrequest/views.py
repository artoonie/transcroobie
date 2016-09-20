import os

from django.template import loader
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.core.files.base import File
from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404

from hitrequest.models import Document
from hitrequest.forms import DocumentForm
from hitrequest.splitAudio import splitAudioIntoParts
from hitrequest.createHits import HitCreator

def list(request):
    # Handle file upload
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            hitCreator = HitCreator()
            newdoc = Document(docfile = request.FILES['docfile'])
            newdoc.save()
            # Get the fullpath of the uploaded file
            fullpath = os.path.join(settings.MEDIA_ROOT, newdoc.docfile.name)

            # Get the paths of each of the split fileparts
            for tmpFileObject in splitAudioIntoParts(fullpath,
                    basedir = settings.MEDIA_ROOT):
                relPath = os.path.relpath(tmpFileObject, settings.MEDIA_ROOT)

                # Open the file, copy into to the database's storage.
                # TODO - inefficient copying - how can splitAudioIntoParts
                # write directly into the correct location?
                with open(tmpFileObject) as fileObj:
                    fileCopy = File(file=fileObj, name=relPath)
                    currdoc = Document(docfile = fileCopy)
                    currdoc.save()

                    # Create a hit from this document
                    hitCreator.createHitFromDocument(currdoc)

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
    docToDel.docfile.delete()
    docToDel.delete()

def delete(request):
    """ Delete one uploaded file """
    if request.method != 'POST':
        raise Http404

    docId = request.POST.get('docfile', None)
    docToDel = get_object_or_404(Document, pk = docId)
    _deleteDocument(docToDel)

    return HttpResponseRedirect(reverse('list'))

def deleteAll(request):
    """ Delete all uploaded files """
    documents = Document.objects.all()
    for docToDel in documents:
        _deleteDocument(docToDel)

    return HttpResponseRedirect(reverse('list'))
