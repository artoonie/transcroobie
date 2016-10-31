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

@xframe_options_exempt
def index(request):
    disabledText = "" # To be placed at the end of the submit <input> tag
    if request.GET.get("assignmentId") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        # worker hasn't accepted the HIT (task) yet
        disabledText = "disabled"

    fileId = request.GET.get("docId", "")
    audioSnippet = get_object_or_404(AudioSnippet, pk = fileId)

    if len(audioSnippet.predictions) > 0:
        lastTranscription = audioSnippet.predictions[-1]
    else:
        lastTranscription = ""

    render_data = {
        "worker_id": request.GET.get("workerId", ""),
        "assignment_id": request.GET.get("assignmentId", ""),
        "amazon_host": AMAZON_HOST,
        "hit_id": request.GET.get("hitId", ""),
        "audioSnippet": audioSnippet,
        "lastTranscription": lastTranscription,
        "isDisabled": disabledText
    }

    template= loader.get_template('hit/client.html')
    response = template.render(render_data, request)

    return HttpResponse(response)

