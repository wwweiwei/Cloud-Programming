import json
import boto3
import AWSIoTPythonSDK
import time
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient


S3_METADATA = {
    'Bucket': 'hw4image',  # Bucket name
    'Name': 'image.png'      # Filename
}


def detect_faces():
    client = boto3.client('rekognition')
    response = client.detect_faces(Image={'S3Object': S3_METADATA})

    face = response['FaceDetails']
    has_face = (len(face) != 0 and face[0]['Confidence'] > 50.0)
    print("lambda")
    return has_face
    
    
def LED(isOn):
    client = boto3.client('iot-data')
    if isOn==True:
        response = client.update_thing_shadow(
            thingName='hw4_LED',
            #shadowName='Classic Shadow',
            payload=json.dumps({"state":{"desired":{"isLEDOn":"true"}}})
        )
    else:
        response = client.update_thing_shadow(
            thingName='hw4_LED',
            #shadowName='Classic Shadow',
            payload=json.dumps({"state":{"desired":{"isLEDOn":"false"}}})
        )

def lambda_handler(event, context):
    try:
        response = detect_faces()
        LED(response)
    except Exception as e:
        raise e
    
    return {'statusCode': 200, 'hasFace': response}
