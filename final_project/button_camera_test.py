from gpiozero import Button
from time import sleep
from picamera import PiCamera
import boto3
from botocore.exceptions import ClientError

# button
button = Button(17) # GPIO17
button_is_pressed = 0 # init to not pressed


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    object_name = "image.jpg"

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


while True:
    if button.is_pressed:
        print("Button is pressed!")
        button_is_pressed = 1
    else:
        print("Button is not pressed!")

    if button_is_pressed:
        # camera
        camera = PiCamera()
        camera.resolution = (1024, 768)
        camera.start_preview()
        sleep(2)
        camera.capture("image.jpg")

        # button
        button_is_pressed = 0 # reset to not pressed

        # upload image to s3
        upload_file("./image.jpg", "finalprojectbuffer")
