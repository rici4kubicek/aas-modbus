#!/usr/bin/python3
# -*- coding: utf-8 -*-
from pymodbus.server.asynchronous import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer
from threading import Thread
import paho.mqtt.client as mqtt_client
import logging
import time

__author__ = "Richard Kubicek"
__copyright__ = "Copyright 2019, FEEC BUT Brno"
__credits__ = ["Richard Kubicek"]
__license__ = "Proprietary"
__version__ = "1.0.0"
__maintainer__ = "Richard Kubicek"
__email__ = "xkubic35@vutbr.cz"
__status__ = "Private Beta"

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)


def updating_writer(a):
    while True:
        log.debug("updating the context")
        context = a._slaves
        register = 3
        slave_id = 0x00
        address = 0x10
        values = context[slave_id].getValues(register, address, count=5)
        values = [v + 1 for v in values]
        log.debug("new values: " + str(values))
        context[slave_id].setValues(register, address, values)
        time.sleep(5)


def run_updating_server():
    st = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [17] * 100),
        co=ModbusSequentialDataBlock(0, [17] * 100),
        hr=ModbusSequentialDataBlock(0, [17] * 100),
        ir=ModbusSequentialDataBlock(0, [17] * 100))
    st2 = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [18] * 100),
        co=ModbusSequentialDataBlock(0, [18] * 100),
        hr=ModbusSequentialDataBlock(0, [18] * 100),
        ir=ModbusSequentialDataBlock(0, [18] * 100))
    store = {}
    store[0] = st
    store[1] = st2
    context = ModbusServerContext(slaves=store, single=False)

    identity = ModbusDeviceIdentification()
    identity.VendorName = 'FEKT VUTBR'
    identity.ProductCode = 'AAS'
    identity.VendorUrl = 'https://www.fekt.vut.cz/'
    identity.ProductName = 'AAS modbus server'
    identity.ModelName = 'AAS module'
    identity.MajorMinorRevision = '1.0.0'

    thread = Thread(target=updating_writer, args=(context,))
    thread.start()
    StartTcpServer(context, identity=identity, address=("localhost", 5020))


if __name__ == "__main__":
    run_updating_server()
