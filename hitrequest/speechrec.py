from googleapiclient.discovery import build
from oauth2client.client import GoogleCredentials

def getTranscriptionFromURL(url, sampleRate):
    credentials = GoogleCredentials.get_application_default()
    service = build('speech', 'v1beta1', credentials=credentials)

    data = {
      "config": {
          "encoding":"LINEAR16",
          "sampleRate": sampleRate,
          "languageCode": "en-US"
      },
      "audio": {
          "uri":url
      }
    }

    request = service.speech().syncrecognize(body=data)
    response = request.execute()
    result = response['results'][0]['alternatives'][0]
    return result['transcript'], result['confidence']
