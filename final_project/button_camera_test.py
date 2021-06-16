from gpiozero import Button
from time import sleep
from picamera import PiCamera

# button
button = Button(17) # GPIO17
button_is_pressed = 0 # init to not pressed

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
        camera.capture('image.jpg')
        # button
        button_is_pressed = 0 # reset to not pressed
