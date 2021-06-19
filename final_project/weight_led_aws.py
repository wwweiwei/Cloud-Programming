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
global need_update
global user_id
count = 0
item_id = "item_0"
need_update = "False"
user_id = "null"

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

def weight(cur_weight,item_id,count,need_update):
    val = hx.get_weight(5)
    print("current weight: "+str(val))
    hx.power_down()
    hx.power_up()
    time.sleep(0.1)

    # global cur_weight
    # global count
    # global item_id
    # global need_update

    if int(cur_weight) < 10000:
        print("Turn on red light, no stock!")
        setColor(255, 0, 0) # red
    else:
        red_pwm.ChangeDutyCycle(100-int(0/255*100)) # close red light

    # add stock:+, take away stock:-
    delta = cur_weight - val
    cur_weight = val

    if int(delta)>10000 and int(delta)<20000:
        print("Buy! item_id = item_1, count = 1")
        item_id = 'item_1'
        count = -1
        need_update = "True"
    elif int(delta)>20000 and int(delta)<30000:
        print("Buy! item_id = item_1, count = 2")
        item_id = 'item_1'
        count = -2
        need_update = "True"
    elif int(delta)>30000 and int(delta)<40000:
        print("Buy! item_id = item_1, count = 3")
        item_id = 'item_1'
        count = -3
        need_update = "True"
    elif int(delta)>40000 and int(delta)<50000:
        print("Buy! item_id = item_1, count = 4")
        item_id = 'item_1'
        count = -4
        need_update = "True"
    elif int(delta)>50000 and int(delta)<60000:
        print("Buy! item_id = item_1, count = 5")
        item_id = 'item_1'
        count = -5
    elif int(delta)>60000:
        print("Buy! You buy too much!")
        item_id = 'item_1'
        count = -6
        need_update = "True"
    elif int(delta)>-20000 and int(delta)<-10000:
        print("New stock arrive! item_id = item_1, count = 1")
        item_id = 'item_1'
        count = 1
        need_update = "True"
    elif int(delta)>-30000 and int(delta)<-20000:
        print("New stock arrive! item_id = item_1, count = 2")
        item_id = 'item_1'
        count = 2
        need_update = "True"
    elif int(delta)>-40000 and int(delta)<-30000:
        print("New stock arrive! item_id = item_1, count = 3")
        item_id = 'item_1'
        count = 3
        need_update = "True"
    elif int(delta)>-50000 and int(delta)<-40000:
        print("New stock arrive! item_id = item_1, count = 4")
        item_id = 'item_1'
        count = 4
        need_update = "True"
    elif int(delta)>-60000 and int(delta)<-50000:
        print("New stock arrive! item_id = item_1, count = 5")
        item_id = 'item_1'
        count = 5
        need_update = "True"
    elif int(delta)<-60000:
        print("New stock arrive! You add too much stock!")
        item_id = 'item_1'
        count = 6
        need_update = "True"
    else: ## 10000 > delta > -10000
        count = 0

    # send item_id and count to aws dynamoDB
    return cur_weight, item_id, count, need_update

class shadowCallbackContainer:
    def __init__(self, deviceShadowInstance):
        self.deviceShadowInstance = deviceShadowInstance

    # # Custom Shadow callback
    # def customShadowCallback_Update(self, payload, responseStatus, token):
        
    #     print("Update")
    #     global count
    #     global item_id
    #     global need_update

    #     ## update item_id and count
    #     if need_update == "True":
    #         need_update = "False"
    #         print("Update DynamoDB!")
    #         msg = '"item_id":' + str(item_id) + ' ,"count":' + str(count)
    #         desiredMessage = json.dumps(msg)
    #         newPayload = '{"state":{"desired":' + desiredMessage + '}}'
    #         self.deviceShadowInstance.shadowUpdate(newPayload, None, 5)


    def customShadowCallback_Delta(self, payload, responseStatus, token):

        print("** Delta from aws")

        user_id = 'null'

        payloadDict = json.loads(payload)
        print("payloadDict:"+str(payloadDict))

        if 'item_id' in payloadDict["state"]:
            item_id = payloadDict["state"]["item_id"]
        if 'count' in payloadDict["state"]:
            count = payloadDict["state"]["count"]

        if 'user_id' in payloadDict["state"]:
            user_id = payloadDict["state"]["user_id"] #null       
        if 'user_led' in payloadDict["state"]:
            user_led = payloadDict["state"]["user_led"]        
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
            elif user_led == "off":
                print("Turn off the light")
                setColor(0, 0, 0)

        deltaMessage = json.dumps(payloadDict["state"])
        newPayload = '{"state":{"reported":' + deltaMessage + '}}'
        # print("newPayload: " + str(newPayload))
        
        self.deviceShadowInstance.shadowUpdate(newPayload, None, 5)

        return user_id

clientId="mypythoncodefinal"
thingName="final"
# shadow name

try:
    # Configure logging
    # logger = logging.getLogger("AWSIoTPythonSDK.core")
    # logger.setLevel(logging.INFO)
    # streamHandler = logging.StreamHandler()
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # streamHandler.setFormatter(formatter)
    # logger.addHandler(streamHandler)

    # AWS
    myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(clientId)
    myAWSIoTMQTTShadowClient.configureEndpoint("a245gozh31fmt8-ats.iot.us-east-1.amazonaws.com", 8883)
    myAWSIoTMQTTShadowClient.configureCredentials("./root-CA.pem", "./final-private.pem.key", "./final-certificate.pem.crt")

    # Connect to AWS IoT
    myAWSIoTMQTTShadowClient.connect()

    deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(thingName, True)
    shadowCallbackContainer_Bot = shadowCallbackContainer(deviceShadowHandler)
    user_id = deviceShadowHandler.shadowRegisterDeltaCallback(shadowCallbackContainer_Bot.customShadowCallback_Delta)
except:
    print("AWS Error")


while True:
    try:
        cur_weight, item_id, count, need_update = weight(cur_weight,item_id,count,need_update)

        ## update count, item and user_id
        if need_update == "True":
            need_update = "False"
            print("Update DynamoDB!")
            msg = '"item_id":"' + str(item_id) + '" ,"count":"' + str(count) + '" ,"user_id":"' + str(user_id) + '"'
            # msg = '"item_id":"' + str(item_id) + '" ,"count":"' + str(count) + '"'
            # desiredMessage = json.dumps(msg)
            print("msg: "+str(msg))
            JSONPayload = '{"state":{"desired":{' + msg + '}}}'
            deviceShadowHandler.shadowUpdate(JSONPayload, None, 5)

        # deviceShadowHandler.shadowRegisterUpdateCallback(shadowCallbackContainer_Bot.customShadowCallback_Update)

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