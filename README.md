# PiSecure By AlanL0 <img src="logo2.png" width="100" height="100">
This is a project mainly for utilizing my RaspberryPi 3B and a camera module as a responsive Security Camera. 
Thanks to different Guides from [PyImageSearch](pyimagesearch.com) and from [Hackster.io](https://www.hackster.io/KennyHo2911/camera-alert-application-with-raspberry-pi-3-ios-android-881bb4),
I implemented a Security Camera that communicates with Pushbullet API and uploads images straight to Dropbox.

Things I used:
Raspberry Pi 3B w/ Wifi access
Raspberry Pi Camera Module V2-8 with correct settings on your RasPi

How it Works:
- This Security Camera Utilizes OpenCV to detect changes frame by frame and will Highlight/Mark the object that caused the change.
- Example; OpenCV will take an initial image and compare it with the next frame/image and if there are any significant changes, the Raspberry Pi will upload and image to your Dropbox.
- [More Info Here](https://www.pyimagesearch.com/2015/06/01/home-surveillance-and-motion-detection-with-the-raspberry-pi-python-and-opencv/)


Here's How to Set it Up:
- To Set this all up, you'll need to get access tokens from [Pushbullet API](https://www.pushbullet.com/) by creating an acount and Dropbox API by creating a account 
for [Dropbox developers](https://www.dropbox.com/developers/reference/getting-started#overview) and creating an app.
- With dropbox you'll need to create a folder/directory where you want to store images
- Using Pushbullet API you'll need to link a desired devices where you'll want to be notified and/or check on your security camera

How to Use:
- When your Security Camera is Active, Pushbullet should send a message that "PiSecure app is starting"
- You can send commands like:
<br />@check -- checks on your Raspberry Pi's device's Temperature, RAM, and CPU usage<br /> 
@reboot -- reboots your Raspberry Pi<br />
@status -- Sends back a message if the Camera detected any motion or changes<br />
@end    -- Shutsdown the Raspberry Pi<br />
@snap   -- When sent; it will upload a LIVE Image from your Security Camera to your Dropbox Account<br />
-- You can add more custom commands if desired. 
- Currently I am only able to start it manually by starting the script 'on_reboot.sh', but auto-start up is possible.



