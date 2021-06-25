# Cloud-Programming

* HW3: Cloud Backend Mobile App
  * Part1: launch the app => sign-in by email
  * Part2: operate on the app interface for creating and deleting bucket/queue
  * Part3: camera activity
    * step1: take a picture from the camera=>upload the picture to a S3 bucket 
    * step2: retrieve the url of the S3 object
    * step3: send a message with the url to a SQS queue
    * step4: automatically trigger a lambda function
    * step5: execute lambda function to upload resize images  
* HW4: IoT, Machine Learning
  *  Implement an end-to-end cloud application which can take a picture and then use AWS service to detect whether there are any faces in the picture or not. If any face is detected, turn on the light on the raspberry pi. If not, turn off the light on the raspberry pi.
*  Final Project: Auto-check
  *  A cloud cashier-free convenience store system
