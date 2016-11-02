from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template import loader
from django.views.decorators.clickjacking import xframe_options_exempt
from hitrequest.models import AudioSnippet
from transcroobie import settings


if settings.IS_DEV_ENV or settings.USE_AMT_SANDBOX:
    AMAZON_HOST = "https://workersandbox.mturk.com/mturk/externalSubmit"
else:
    AMAZON_HOST = "https://www.mturk.com/mturk/externalSubmit"

def getRenderDataFor(request):
    disabledText = "" # To be placed at the end of the submit <input> tag
    if request.GET.get("assignmentId") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        # worker hasn't accepted the HIT (task) yet
        disabledText = "disabled"

    fileId = request.GET.get("docId", "")
    audioSnippet = get_object_or_404(AudioSnippet, pk = fileId)
    # For testing: get the last upload
    # audioSnippet = AudioSnippet.objects.order_by('id').reverse()[0]

    if len(audioSnippet.predictions) > 0:
        lastTranscription = audioSnippet.predictions[-1].split(' ')
    else:
        lastTranscription = ""

    withEllipses = ["..."]
    withEllipses.extend(lastTranscription)
    withEllipses.append("...")

    renderData = {
        "worker_id": request.GET.get("workerId", ""),
        "assignment_id": request.GET.get("assignmentId", ""),
        "amazon_host": AMAZON_HOST,
        "hit_id": request.GET.get("hitId", ""),
        "as_file_id": fileId,
        "audioSnippet": audioSnippet,
        "lastTranscription": withEllipses,
        "isDisabled": disabledText
    }
    return renderData


@xframe_options_exempt
def fixHIT(request):
    renderData = getRenderDataFor(request)
    template= loader.get_template('hit/fixHIT.html')
    audioSnippet = renderData['audioSnippet']
    incorrectWords = audioSnippet.incorrectWords['bools'][-1]

    txt = ""
    for i, t in enumerate(renderData['lastTranscription']):
        if incorrectWords[i]:
            txt += "WRONG" + t + "\n"
        else:
            txt += "RIGHT" + t + "\n"
    lt = renderData['lastTranscription']
    renderData['lastTranscription'] = zip(lt, incorrectWords)

    response = template.render(renderData, request)

    return HttpResponse(response)

@xframe_options_exempt
def checkHIT(request):
    renderData = getRenderDataFor(request)
    template= loader.get_template('hit/checkHIT.html')
    response = template.render(renderData, request)

    return HttpResponse(response)
