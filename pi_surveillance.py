#!/usr/bin/python
# import the necessary packages
from pysearch.tempimage import TempImage
from picamera.array import PiRGBArray
from picamera import PiCamera
import argparse
import warnings
import datetime
import dropbox
import imutils
import json
import time
import cv2
import subprocess
import os
from pushbullet import Pushbullet
from push import NotificationHandler

# construct the argument parser and parse the arguments
PUSHBULLET_KEY = '<Key/Token to access Pushbullet>'
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--conf", required=True,
	help="path to the JSON configuration file")
args = vars(ap.parse_args())
 
# filter warnings, load the configuration and initialize the Dropbox
# client
warnings.filterwarnings("ignore")
conf = json.load(open(args["conf"]))
client = None
# check to see if the Dropbox should be used
if conf["use_dropbox"]:
	# connect to dropbox and start the session authorization process
	client = dropbox.Dropbox(conf["dropbox_access_token"])
	print("[SUCCESS] dropbox account linked")

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = tuple(conf["resolution"])
camera.framerate = conf["fps"]
rawCapture = PiRGBArray(camera, size=tuple(conf["resolution"]))
 
# allow the camera to warmup, then initialize the average frame, last
# uploaded timestamp, and frame motion counter
print("[INFO] warming up...")
time.sleep(conf["camera_warmup_time"])
avg = None
lastUploaded = datetime.datetime.now()
motionCounter = 0
presence = 0

# Pushbullet status check
WORKING_DIR="/home/pi/Desktop/PiSecure/"

def file_update():
        f = open("/home/pi/Desktop/PiSecure/test.txt","r")
        read=f.readlines()
        num = -1
        for i in read:
                num = int(i)
        f.close()
        if num == 1337:
                result = 1
        else:
                result = 0
        
        return result

def didReceiveCommand(command):
	global notificationHandler
	global presence
	global lastUploaded
	if command == "@check":
		process = subprocess.Popen([ WORKING_DIR + 'systemInfo.sh'], stdout=subprocess.PIPE)
		out, err = process.communicate()
		pushData = {'type': 'TEXT_MESSAGE', 'text': out}
		notificationHandler.pushToMobile(pushData)
	if command == "@reboot":
                os.system("sudo reboot")
        if command == "@status":
                out = "Securing Perimeter [Occupied Counter is = " + str(presence) +" ]"
                pushData = {'type': 'TEXT_MESSAGE', 'text': out}
		notificationHandler.pushToMobile(pushData)
		presence = 0
	if command == "@end":
                os.system("sudo shutdown -h now")
        if command == "@snap":
                out = "Sending a current Picture to DropBox at " + str(lastUploaded)
                f=open("/home/pi/Desktop/PiSecure/test.txt","w")
                f.write("1337")
                f.close()
                pushData = {'type': 'TEXT_MESSAGE', 'text': out}
		notificationHandler.pushToMobile(pushData)
        else: 
                out = "Typical commands are @status and @check"
                pushData = {'type': 'TEXT_MESSAGE', 'text': out}
		notificationHandler.pushToMobile(pushData)
notificationHandler = NotificationHandler(PUSHBULLET_KEY, didReceiveCommand)      

# capture frames from the camera
for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	# grab the raw NumPy array representing the image and initialize
	# the timestamp and occupied/unoccupied text
	frame = f.array
	timestamp = datetime.datetime.now()
	text = "Unoccupied"
        snap = file_update()
	# resize the frame, convert it to grayscale, and blur it
	frame = imutils.resize(frame, width=500)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	gray = cv2.GaussianBlur(gray, (21, 21), 0)
 
	# if the average frame is None, initialize it
	if avg is None:
		print("[INFO] starting background model...")
		avg = gray.copy().astype("float")
		rawCapture.truncate(0)
		global notificationHandler
		pushData = {'type': 'TEXT_MESSAGE', 'text': 'PiSecure app starts !'}
                notificationHandler.pushToMobile(pushData)
		continue
                
	# accumulate the weighted average between the current frame and
	# previous frames, then compute the difference between the current
	# frame and running average
	cv2.accumulateWeighted(gray, avg, 0.5)
	frameDelta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))
	# threshold the delta image, dilate the thresholded image to fill
	# in holes, then find contours on thresholded image
	thresh = cv2.threshold(frameDelta, conf["delta_thresh"], 255,
		cv2.THRESH_BINARY)[1]
	thresh = cv2.dilate(thresh, None, iterations=2)
	cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
		cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)
 
	# loop over the contours
	for c in cnts:
		# if the contour is too small, ignore it
		if cv2.contourArea(c) < conf["min_area"]:
                        continue
 
		# compute the bounding box for the contour, draw it on the frame,
		# and update the text
		(x, y, w, h) = cv2.boundingRect(c)
		cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
		text = "Occupied"
 
	# draw the text and timestamp on the frame
	ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
	cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
		cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
	cv2.putText(frame, ts, (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
		0.35, (0, 0, 255), 1)
	# check to see if the room is occupied
	if text == "Occupied":
		# check to see if enough time has passed between uploads
		if (timestamp - lastUploaded).seconds >= conf["min_upload_seconds"]:
			# increment the motion counter
			motionCounter += 1
                        presence += 1
			# check to see if the number of frames with consistent motion is
			# high enough
			if motionCounter >= conf["min_motion_frames"]:
				# check to see if dropbox sohuld be used
				if conf["use_dropbox"]:
					# write the image to temporary file
					t = TempImage()
					cv2.imwrite(t.path, frame)
                                        # upload the image to Dropbox and cleanup the tempory image
					print("[UPLOAD] {}".format(ts))
					path = "/{base_path}/{timestamp}.jpg".format(
					    base_path=conf["dropbox_base_path"], timestamp=ts)
					client.files_upload(open(t.path, "rb").read(), path)
					t.cleanup()
 
				# update the last uploaded timestamp and reset the motion
				# counter
				lastUploaded = timestamp
				motionCounter = 0
        # check if user wants to snap a pic
        elif snap == 1:
                if conf["use_dropbox"]:
                        # write the image to temporary file
			n = TempImage()
			cv2.imwrite(n.path, frame)
                        # upload the image to Dropbox and cleanup the tempory image
			print("[UPLOAD] {}".format(ts))
			path = "/{base_path}/{timestamp}.jpg".format(base_path=conf["dropbox_base_path"], timestamp=ts)
			client.files_upload(open(n.path, "rb").read(), path)
			n.cleanup()
		f=open("/home/pi/Desktop/PiSecure/test.txt","w")
                f.write("0")
                f.close()
 
	# otherwise, the room is not occupied
	else:
                motionCounter = 0
	# check to see if the frames should be displayed to screen
	if conf["show_video"]:
		# display the security feed
		cv2.imshow("Security Feed", frame)
		key = cv2.waitKey(1) & 0xFF
 
		# if the `q` key is pressed, break from the loop
		if key == ord("q"):
			break
 
	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)
