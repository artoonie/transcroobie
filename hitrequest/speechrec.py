from celery.utils.log import get_task_logger
from googleapiclient.discovery import build
from oauth2client.client import GoogleCredentials

logger = get_task_logger(__name__)

def getTranscriptionFromURL(url, sampleRate):
    credentials = GoogleCredentials.get_application_default()
    service = build('speech', 'v1', credentials=credentials)

    data = {
      "config": {
          "encoding":"LINEAR16",
          "sampleRateHertz": sampleRate,
          "languageCode": "en-US"
      },
      "audio": {
          "uri":url
      }
    }

    request = service.speech().recognize(body=data)
    try:
        response = request.execute()
    except Exception as e:
        logger.error(str(e))
        raise e

    transcript = ""
    confidence = 0

    if 'results' in response and response['results']:
        results = response['results'][0]
        if results['alternatives']:
            result = results['alternatives'][0]
            transcript = result['transcript']
            try:
                confidence = result['confidence']
            except KeyError:
                # From the Google Speech API Documentation:
                # Your code should not require the confidence field as it is not
                # guaranteed to be accurate, or even set, in any of the results.
                confidence = 0.0

    return transcript, confidence
