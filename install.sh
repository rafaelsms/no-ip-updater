mkdir /opt/No-IP-Updater
cp noip-updater.py /opt/No-IP-Updater/noip-updater.py
echo "Installed executable on /opt/No-IP-Updater"
cp noip-updater.service /etc/systemd/system/noip-updater.service
systemctl enable noip-updater.service
echo "Installed system service"

echo
echo "You should now install python's pip"
echo "On pip, install apscheduler and sqlalchemy, run on the command line:"
echo "$ sudo pip install apscheduler sqlalchemy"
echo
echo "After installing it, run:"
echo "$ cd /opt/No-IP-Updater/"
echo "$ sudo python3 noip-updater.py"
echo "So you can configure the application."
echo "Restart the computer or use:"
echo "$ sudo systemctl start noip-updater.service"
echo "To start the service."
