sudo cp service/aas-modbus.service /lib/systemd/system/aas-modbus.service
sudo systemctl enable aas-modbus.service
sudo systemctl start aas-modbus.service