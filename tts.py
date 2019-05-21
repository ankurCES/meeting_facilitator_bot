import boto3
import os
from playsound import playsound
import calendar
import time

def utter_text(text):
    voice_id = 'Amy'
    polly_client = boto3.Session(
                    aws_access_key_id='<access_key_here>',
        aws_secret_access_key='<secret_here>',
        region_name='<region_here>').client('polly')

    response = polly_client.synthesize_speech(VoiceId=voice_id,
                    OutputFormat='mp3',
                    Text = text)
    timestamp = calendar.timegm(time.gmtime())
    file_name = 'speech_data/speech_{}.mp3'.format(timestamp)
    file = open(file_name, 'wb')
    file.write(response['AudioStream'].read())
    file.close()
    playsound(file_name)

if __name__ == '__main__':
    utter_text('Hello I am Sally! Your personal assistant.', 'Joanna')
