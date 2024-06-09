import sys
import os
import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLineEdit, QFormLayout, QFrame, QDialog, QDialogButtonBox, QErrorMessage
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
import numpy as np
from geometry_msgs.msg import Twist
import subprocess
import threading
from nav_msgs.msg import OccupancyGrid, Odometry
import sleekxmpp

#Turn ON Ejabberd-server
class LoginDialog(QDialog):
    def __init__(self):
        super(LoginDialog, self).__init__()
        self.setWindowTitle("Login")
        self.setModal(True)
        
        self.layout = QVBoxLayout(self)
        
        self.username_label = QLabel("Username:")
        self.layout.addWidget(self.username_label)
        self.username_input = QLineEdit(self)
        self.layout.addWidget(self.username_input)
        
        self.password_label = QLabel("Password:")
        self.layout.addWidget(self.password_label)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(self.password_input)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)
        
    def get_credentials(self):
        return self.username_input.text(), self.password_input.text()

class XMPPClient(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password):
        super(XMPPClient, self).__init__(jid, password)
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("failed_auth", self.failed_auth)
        self.auth_success = False

    def start(self, event):
        self.auth_success = True
        self.disconnect()

    def failed_auth(self, event):
        self.auth_success = False
        self.disconnect()

    def authenticate(self):
        self.connect()
        self.process(block=True)
        return self.auth_success

class ROSInterface:
    def __init__(self):
        rospy.init_node('ros_interface', anonymous=True)
        self.bridge = CvBridge()
        self.image = None
        self.map_image = None
        self.robot_x = 0.0
        self.robot_y = 0.0
        self.robot_orientation = 0.0
        self.robot_linear_velocity = 0.0
        self.robot_angular_velocity = 0.0
        self.cmd_vel_publisher = rospy.Publisher('/cmd_vel', Twist, queue_size=10)
        self.subscriber = rospy.Subscriber('/camera/rgb/image_raw', Image, self.image_callback) #Change your camera topic name
        self.map_subscriber = rospy.Subscriber('/map', OccupancyGrid, self.map_callback)
        self.odom_subscriber = rospy.Subscriber('/odom', Odometry, self.odom_callback)

    def image_callback(self, msg):
        rospy.loginfo("Received image from camera") #Comment out if you want to stop writing the log to the console 
        self.image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        rospy.loginfo("Image shape: {}".format(self.image.shape)) #Comment out if you want to stop writing the log to the console

    def map_callback(self, msg):
        rospy.loginfo("Received SLAM map") #Comment out if you want to stop writing the log to the console
        map_data = np.array(msg.data).reshape((msg.info.height, msg.info.width))
        map_image = (255 * map_data).astype(np.uint8)
        self.map_image = cv2.cvtColor(map_image, cv2.COLOR_GRAY2BGR)
        rospy.loginfo("Map shape: {}".format(self.map_image.shape)) #Comment out if you want to stop writing the log to the console

    def odom_callback(self, msg):
        self.robot_x = msg.pose.pose.position.x
        self.robot_y = msg.pose.pose.position.y
        self.robot_orientation = msg.pose.pose.orientation.z
        self.robot_linear_velocity = msg.twist.twist.linear.x
        self.robot_angular_velocity = msg.twist.twist.angular.z

    def move_robot(self, linear, angular):
        twist_msg = Twist()
        twist_msg.linear.x = linear
        twist_msg.angular.z = angular
        self.cmd_vel_publisher.publish(twist_msg)

class ConnectingThread(QThread):
    ping_finished = pyqtSignal(bool)

    def __init__(self, ip):
        super(ConnectingThread, self).__init__()
        self.ip = ip

    def run(self):
        response = os.system('ping -c 1 ' + self.ip)
        self.ping_finished.emit(response == 0)

class GUI(QMainWindow):
    def __init__(self):
        super(GUI, self).__init__()
        self.ros_interface = None
        self.navigation_process = None
        self.setWindowTitle("ROS Robot Interface")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.ip_input = QLineEdit(self)
        self.ip_input.setPlaceholderText("Enter Robot IP Address")
        self.layout.addWidget(self.ip_input)

        self.connect_button = QPushButton('Connect to robot')
        self.connect_button.clicked.connect(self.check_robot_availability)
        self.layout.addWidget(self.connect_button)

        self.explore_button = QPushButton('Begin autonomous navigation')
        self.explore_button.setEnabled(False)
        self.explore_button.clicked.connect(self.start_autonomous_navigation)
        self.layout.addWidget(self.explore_button)

        self.stop_explore_button = QPushButton('Stop autonomous navigation')
        self.stop_explore_button.setEnabled(False)
        self.stop_explore_button.clicked.connect(self.stop_autonomous_navigation)
        self.layout.addWidget(self.stop_explore_button)

        self.ping_status = QLabel("Status: Not Connected")
        self.layout.addWidget(self.ping_status)

        self.image_layout = QHBoxLayout()
        self.layout.addLayout(self.image_layout)

        self.label_camera = QLabel()
        self.label_camera.setMinimumSize(320, 240)
        self.image_layout.addWidget(self.label_camera)
        
        self.label_map = QLabel()
        self.label_map.setMinimumSize(320, 240)
        self.image_layout.addWidget(self.label_map)

        self.info_layout = QFormLayout()
        self.layout.addLayout(self.info_layout)

        self.position_x_label = QLineEdit(self)
        self.position_x_label.setReadOnly(True)
        self.info_layout.addRow("Position X:", self.position_x_label)

        self.position_y_label = QLineEdit(self)
        self.position_y_label.setReadOnly(True)
        self.info_layout.addRow("Position Y:", self.position_y_label)

        self.orientation_label = QLineEdit(self)
        self.orientation_label.setReadOnly(True)
        self.info_layout.addRow("Orientation:", self.orientation_label)

        self.linear_velocity_label = QLineEdit(self)
        self.linear_velocity_label.setReadOnly(True)
        self.info_layout.addRow("Linear Velocity:", self.linear_velocity_label)

        self.angular_velocity_label = QLineEdit(self)
        self.angular_velocity_label.setReadOnly(True)
        self.info_layout.addRow("Angular Velocity:", self.angular_velocity_label)

        self.controls_info = QLabel("Robot control: W - forward, S - backward, A - left, D - right, E - stop")
        self.layout.addWidget(self.controls_info)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_image)
        self.timer.start(100)

    def show_image(self):
        if self.ros_interface and self.ros_interface.image is not None:
            image = cv2.cvtColor(self.ros_interface.image, cv2.COLOR_BGR2RGB)
            h, w, ch = image.shape
            bytes_per_line = ch * w
            q_image = QImage(image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            self.label_camera.setPixmap(pixmap.scaled(self.label_camera.size(), Qt.KeepAspectRatio))

        if self.ros_interface and self.ros_interface.map_image is not None:
            map_image = cv2.cvtColor(self.ros_interface.map_image, cv2.COLOR_BGR2RGB)
            h, w, ch = map_image.shape
            bytes_per_line = ch * w
            q_map_image = QImage(map_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_map_image)
            self.label_map.setPixmap(pixmap.scaled(self.label_map.size(), Qt.KeepAspectRatio))

        if self.ros_interface:
            self.position_x_label.setText("{:.2f}".format(self.ros_interface.robot_x))
            self.position_y_label.setText("{:.2f}".format(self.ros_interface.robot_y))
            self.orientation_label.setText("{:.2f}".format(self.ros_interface.robot_orientation))
            self.linear_velocity_label.setText("{:.2f}".format(self.ros_interface.robot_linear_velocity))
            self.angular_velocity_label.setText("{:.2f}".format(self.ros_interface.robot_angular_velocity))

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_W:
            self.ros_interface.move_robot(0.5, 0.0)
        elif key == Qt.Key_S:
            self.ros_interface.move_robot(-0.5, 0.0)
        elif key == Qt.Key_A:
            self.ros_interface.move_robot(0.0, 0.5)
        elif key == Qt.Key_D:
            self.ros_interface.move_robot(0.0, -0.5)
        elif key == Qt.Key_E:
            self.ros_interface.move_robot(0.0, 0.0)

    def check_robot_availability(self):
        ip = self.ip_input.text()
        self.ping_thread = ConnectingThread(ip)
        self.ping_thread.ping_finished.connect(self.handle_ping_result)
        self.ping_thread.start()

    def handle_ping_result(self, success):
        if success:
            self.ping_status.setText("Status: Connected")
            self.ros_interface = ROSInterface()
            self.explore_button.setEnabled(True)
            self.stop_explore_button.setEnabled(True)
        else:
            self.ping_status.setText("Status: Not Connected")
            self.explore_button.setEnabled(False)
            self.stop_explore_button.setEnabled(False)

    def start_autonomous_navigation(self):
        self.navigation_process = subprocess.Popen(['roslaunch', 'my_robot_navigation', 'explore.launch']) #Change dirr to m-explore-2

    def stop_autonomous_navigation(self):
        if self.navigation_process:
            self.navigation_process.terminate()
            self.navigation_process = None

    def authenticate_xmpp(self):
        dialog = LoginDialog()
        if dialog.exec_() == QDialog.Accepted:
            username, password = dialog.get_credentials()
            self.xmpp_client = XMPPClient(username, password)
            if self.xmpp_client.authenticate():
                print("Authenticated successfully")
            else:
                print("Authentication failed")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = GUI()
    gui.show()
    gui.authenticate_xmpp()
    sys.exit(app.exec_())
