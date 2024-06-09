# **Robot Movement Control**
![Screenshot](https://github.com/MikhailKapirusov/ROS_GUI/blob/main/APP/Logo.PNG)
# ROS_GUI
Graphical interface of the software system for controlling the movement of a mobile robot named ***Robot Movement Control***.

## Background

The main purpose of a software system for controlling the movement of a mobile robot is to provide the average user with the opportunity to control a mobile robot, both within the same local network and remotely.
The main feature of the software system is the previously taken developments of the autonomous navigation algorithm of the mobile robot and an early prototype of the client application, which need to be implemented into the software system. 
The requirement for the system was to provide the ability to control the robot from a remote device in NAT conditions. 
In view of these features, it was determined that the software system should consist of three parts: a client application, a protocol conversion module as part of the built-in software of the mobile robot and a server.

***The client application is provided here, offline navigation for the mobile robot is provided, and the server installer is provided in other repositories.***
![Screenshot](https://github.com/MikhailKapirusov/ROS_GUI/blob/main/Pic1.JPG)
ROBOT: *Coming soon*
SERVER: *Coming soon*

## Installation
***!Before executing the script, you must create the /usr/local/lib/ros-gui/ directory. You need to move the files ROS_GUI.py and logo.png (program shortcut) to the previously created directory!***

*1* To install the ***"ROS GUI"*** client application, use the bash installer ***"install_gui.sh"***

*1.1* Make the installation file ***"install_gui.sh"*** executable with the command: `chmod +x ./install_gui.sh`

*1.2* Run the installer with the command: `install_gui.sh`

As a result, the application shortcut ***"ROS GUI"*** will appear on the desktop:

![Screenshot](https://github.com/MikhailKapirusov/ROS_GUI/blob/main/Pic2.png)

## Results 

***!Before starting the graphical interface, you must enable the mobile robot and server!***

*1* Click on the application shortcut

*2* Enter the username and password for the Ejabberd server

*3* Enter the IP address of a mobile robot available on the network

*4* Click on the "Connect to robot" button

*5* You can control the mobile robot using keys or by starting autonomous navigation (“Start autonomous navigation”)

***Below is the result of the client application:***

![](https://github.com/MikhailKapirusov/ROS_GUI/blob/main/ros_gui.gif)
