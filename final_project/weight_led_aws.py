from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import logging
import time
import json
import RPi.GPIO as GPIO
from picamera import PiCamera
import boto3
from botocore.exceptions import ClientError
from hx711 import HX711

# hx711
EMULATE_HX711=False
referenceUnit = 1
hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(referenceUnit)
hx.reset()
hx.tare()
print("Tare done! Add weight now...")

## R:16, G:20, B:25, +3.3V
RED_LED_PIN = 16
BLUE_LED_PIN = 20
GREEN_LED_PIN = 25
PWM_FREQ = 200
 
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False) 
GPIO.setup(RED_LED_PIN, GPIO.OUT)
GPIO.setup(BLUE_LED_PIN, GPIO.OUT)
GPIO.setup(GREEN_LED_PIN, GPIO.OUT)
 
red_pwm = GPIO.PWM(RED_LED_PIN, PWM_FREQ)
red_pwm.start(0)
blue_pwm = GPIO.PWM(BLUE_LED_PIN, PWM_FREQ)
blue_pwm.start(0)
green_pwm = GPIO.PWM(GREEN_LED_PIN, PWM_FREQ)
green_pwm.start(0)

def setColor(r=0, g=0, b=0):
    red_pwm.ChangeDutyCycle(100-int(r/255*100))
    blue_pwm.ChangeDutyCycle(100-int(b/255*100))
    green_pwm.ChangeDutyCycle(100-int(g/255*100))

setColor(0, 0, 0)

global count
global item_id
global cur_weight

cur_weight = hx.get_weight(5)
print("initial weight: "+str(cur_weight))
hx.power_down()
hx.power_up()
time.sleep(0.1)

if cur_weight < 10000:
    print("Turn on red light, no stock!")
    setColor(255, 0, 0) # red
else:
    setColor(0, 0, 0)

def weight():
    val = hx.get_weight(5)
    print("current weight: "+str(val))
    hx.power_down()
    hx.power_up()
    time.sleep(0.1)

    global cur_weight

    if int(cur_weight) < 10000:
        print("Turn on red light, no stock!")
        setColor(255, 0, 0) # red
    else:
        red_pwm.ChangeDutyCycle(100-int(0/255*100)) # close red light

    # add stock:+, take away stock:-
    delta = cur_weight - val
    cur_weight = val

    if int(delta)>10000 and int(delta)<20000:
        print("item_id = item_1, count = 1")
        item_id = 'item_1'
        count = -1
    elif int(delta)>20000 and int(delta)<30000:
        print("item_id = item_1, count = 2")
        item_id = 'item_1'
        count = -2
    elif int(delta)>30000 and int(delta)<40000:
        print("item_id = item_1, count = 3")
        item_id = 'item_1'
        count = -3
    elif int(delta)>40000 and int(delta)<50000:
        print("item_id = item_1, count = 4")
        item_id = 'item_1'
        count = -4
    elif int(delta)>50000 and int(delta)<60000:
        print("item_id = item_1, count = 5")
        item_id = 'item_1'
        count = -5
    elif int(delta)>60000:
        print("You buy too much!")
        count = -6
    elif int(delta)>-20000 and int(delta)<-10000:
        print("New stock arrive! item_id = item_1, count = 1")
        item_id = 'item_1'
        count = 1
    elif int(delta)>-30000 and int(delta)<-20000:
        print("New stock arrive! item_id = item_1, count = 2")
        item_id = 'item_1'
        count = 2
    elif int(delta)>-40000 and int(delta)<-30000:
        print("New stock arrive! item_id = item_1, count = 3")
        item_id = 'item_1'
        count = 3
    elif int(delta)>-50000 and int(delta)<-40000:
        print("New stock arrive! item_id = item_1, count = 4")
        item_id = 'item_1'
        count = 4
    elif int(delta)>-60000 and int(delta)<-50000:
        print("New stock arrive! item_id = item_1, count = 5")
        item_id = 'item_1'
        count = 5
    elif int(delta)<-60000:
        print("New stock arrive! You add too much stock!")
        count = 6
    else: ## 10000 > delta > -10000
        count = 0

    # send item_id and count to aws dynamoDB

class shadowCallbackContainer:
    def __init__(self, deviceShadowInstance):
        self.deviceShadowInstance = deviceShadowInstance

    # Custom Shadow callback
    def customShadowCallback_Delta(self, payload, responseStatus, token):

        print("Get")

        payloadDict = json.loads(payload)
        # isLEDOn = payloadDict["state"]["isLEDOn"]
        user_led = payloadDict["state"]["user_led"]
        # item_id = payloadDict["state"]["item_id"]
        # count = payloadDict["state"]["count"]

        ## update item_id and count

        deltaMessage = json.dumps(payloadDict["state"])

        # user_led: pass, fail, off
        if user_led == "pass":
            print("Turn on green light, face recognition correct!")
            setColor(0, 255, 0) # green
            time.sleep(5) # 5 sec
            setColor(0, 0, 0)
            time.sleep(0.5)
        elif user_led == "fail":
            print("Turn on blue light, you are not our member!")
            setColor(0, 0, 255) # blue
            time.sleep(5)
            setColor(0, 0, 0)
            time.sleep(0.5)
        # elif user_led == "off":
        #     print("Turn off the light")
        #     setColor(0, 0, 0)


        newPayload = '{"state":{"reported":' + deltaMessage + '}}'
        self.deviceShadowInstance.shadowUpdate(newPayload, None, 5)


clientId="mypythoncodefinal"
thingName="final"

try:
    # Configure logging
    logger = logging.getLogger("AWSIoTPythonSDK.core")
    logger.setLevel(logging.INFO)
    streamHandler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)

    # AWS
    myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(clientId)
    myAWSIoTMQTTShadowClient.configureEndpoint("a245gozh31fmt8-ats.iot.us-east-1.amazonaws.com", 8883)
    myAWSIoTMQTTShadowClient.configureCredentials("./root-CA.pem", "./final-private.pem.key", "./final-certificate.pem.crt")

    # Connect to AWS IoT
    myAWSIoTMQTTShadowClient.connect()

    deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(thingName, True)
    shadowCallbackContainer_Bot = shadowCallbackContainer(deviceShadowHandler)
    deviceShadowHandler.shadowRegisterDeltaCallback(shadowCallbackContainer_Bot.customShadowCallback_Delta)
except:
    print("AWS Error")


while True:
    try:
        weight()
        # val = hx.get_weight(5)
        # print("get_weight: "+str(val))
        # hx.power_down()
        # hx.power_up()
        # time.sleep(0.1)
        
    except (KeyboardInterrupt, SystemExit):
        print("Weight Error")

# Loop forever
while True:
    time.sleep(1)