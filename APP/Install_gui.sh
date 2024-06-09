#!/bin/bash

echo "Installing libraries..."
pip install sleekxmpp pyqt5

if [ $? -ne 0 ]; then
    echo "Error installing libraries. Please check your pip settings and internet connection."
    exit 1
fi

DESKTOP_DIR="$HOME/Desktop"
SHORTCUT_FILE="$DESKTOP_DIR/ROS-GUI.desktop"
EXECUTABLE_PATH="/usr/local/lib/ros-gui/ros_gui.py"
ICON_PATH="/usr/local/lib/ros-gui/ros_gui.png"
PYTHON_PATH=$(which python2.7)

echo "Create a shortcut on the desktop..."
cat <<EOL > $SHORTCUT_FILE
[Desktop Entry]
Version=1.0
Type=Application
Name=ROS GUI
Comment=Запуск ROS GUI
Exec=sh -c 'source ~/.bashrc && $PYTHON_PATH $EXECUTABLE_PATH; exec bash'
Icon=$ICON_PATH
Terminal=true
EOL

chmod +x $SHORTCUT_FILE

if [ -f "$SHORTCUT_FILE" ]; then
    echo "The shortcut has been successfully created on the desktop."
else
    echo "Failed to create shortcut. Check your desktop permissions."
    exit 1
fi

echo "ROS GUI installation completed successfully!"
