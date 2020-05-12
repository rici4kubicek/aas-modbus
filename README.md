# aas-modbus

## Installation
**Note** This is applicable only if you place `aas-modbus` project to path `/home/pi/aas-modbus/`

* run command `sh install.sh` in directory `/home/pi/aas-modbus/`
* run command `sh start_service.sh` in directory `/home/pi/aas-modbus/`

**Note** If you have project `aas-modbus` placed on another path, you must make some changes in `aas-modbus.service` file
* change _WorkingDirectory_ to path, where is your project placed
* change _ExecStartPre_ if you want another conditions, or your device is not in network, which is routed to the internet
* change _ExecStart_ to path, where is your project main file, `aas-modbus.py`
* run command `sh install.sh` in directory `/home/pi/aas-modbus/`
* run command `sh start_service.sh` in directory `/home/pi/aas-modbus/`
