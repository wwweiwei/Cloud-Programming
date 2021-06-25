import json
from datetime import datetime as dt
import boto3
from PIL import Image

###These are temporary path saved in the function####
IMG_PATH = '/tmp/image.png'
RESIZED_IMG_PATH = '/tmp/resized_image.png'


def operate_s3(download_bucket, file_name, upload_bucket):
    '''
    Downloads the image from the S3 bucket, resizes the image, and uploads it to
    another S3 bucket.

    download_bucket: Name of the S3 bucket to download images from
    file_name      : Name of the image file in the S3 bucket
    upload_bucket  : Name of the S3 bucket to upload images to
    '''
    s3 = boto3.resource('s3')
    s3.Bucket(download_bucket).download_file(file_name, IMG_PATH)

    img = Image.open(IMG_PATH)
    resized_img = img.resize([d // 2 for d in img.size])
    resized_img.save(RESIZED_IMG_PATH)

    timestamp = dt.isoformat(dt.now())
    s3.Bucket(upload_bucket).upload_file(RESIZED_IMG_PATH, f'{timestamp}.png')


def lambda_handler(event, context):
    ### parsing json style msg sending from sqs
    ### bucketNameOri >>>>>>> the bucket where we put the original pictures
    ### bucketNameResized >>>>>> where we upload the resized pictures
    '''
    please send json sqs like this:
    {"bucketNameOri": 'name of the bucket', "bucketNameResized": "name of the bucket", "fileName": "the picture name"}
    '''
    try :
        for rec in event['Records']:
            msgBody = json.loads(rec['body'])
            bucketNameOri = msgBody['bucketNameOri']
            bucketNameResized = msgBody['bucketNameResized']
            fileName = msgBody['fileName']
            operate_s3(bucketNameOri, fileName, bucketNameResized)
    except Exception as err:
        raise err


    return {
        'statusCode': 200,
        'body': json.dumps('Test succeeded.')
    }
