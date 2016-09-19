import os
from django.http import HttpResponse
from django.template import loader

if os.environ.get("I_AM_IN_DEV_ENV"):
    AMAZON_HOST = "https://workersandbox.mturk.com/mturk/externalSubmit"
else:
    AMAZON_HOST = "https://www.mturk.com/mturk/externalSubmit"

def index(request):
    if request.GET.get("assignmentId") == "ASSIGNMENT_ID_NOT_AVAILABLE":
        # worker hasn't accepted the HIT (task) yet
        pass
    else:
        # worked accepted the task
        pass

    render_data = {
        "worker_id": request.GET.get("workerId", ""),
        "assignment_id": request.GET.get("assignmentId", ""),
        "amazon_host": AMAZON_HOST,
        "hit_id": request.GET.get("hitId", ""),
    }

    template= loader.get_template('hit/client.html')
    response = template.render(render_data, request)
    # without this header, your iFrame will not render in Amazon
    # response['x-frame-options'] = 'this_can_be_anything'

    return HttpResponse(response)

