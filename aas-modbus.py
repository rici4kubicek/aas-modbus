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
import json

__author__ = "Richard Kubicek"
__copyright__ = "Copyright 2019, FEEC BUT Brno"
__credits__ = ["Richard Kubicek"]
__license__ = "Proprietary"
__version__ = "1.0.0"
__maintainer__ = "Richard Kubicek"
__email__ = "xkubic35@vutbr.cz"
__status__ = "Private Beta"

LL_I2C_TOPIC = "i2c"
LL_DISPLAY_TOPIC = LL_I2C_TOPIC + "/display"
LL_I2C_MSG_TOPIC = LL_I2C_TOPIC + "/msg"
LL_TOUCH_TOPIC = LL_I2C_TOPIC + "/touch"
LL_SPI_TOPIC = "spi"
LL_READER_TOPIC = LL_SPI_TOPIC + "/reader"
LL_READER_DATA_TOPIC = LL_READER_TOPIC + "/data"
LL_READER_DATA_READ_TOPIC = LL_READER_TOPIC + "/data/read"
LL_READER_DATA_WRITE_TOPIC = LL_READER_TOPIC + "/data/write"
LL_READER_STATUS_TOPIC = LL_READER_TOPIC + "/state"
LL_SPI_MSG_TOPIC = LL_SPI_TOPIC + "/msg"
LL_LED_TOPIC = LL_SPI_TOPIC + "/led"


class Aas:
    _mqtt = mqtt_client.Client()
    _logger = logging.getLogger()

    def __init__(self):
        self.mqtt_ready = False

    def publish(self, topic, data):
        self._mqtt.publish(topic, data)

    def mqtt(self):
        return self._mqtt

    def logger(self):
        return self._logger

    def logger_debug(self, _str):
        self._logger.debug(_str)

    def logger_error(self, _str):
        self._logger.error(_str)


def on_touch(moqs, obj, msg):
    obj.logger_debug("MQTT: topic: {}, data: {}".format(msg.topic, msg.payload.decode("utf-8")))

    try:
        data = json.loads(msg.payload.decode("utf-8"))
        obj.spi.led.prepare_data(data["led_0"]["red"], data["led_0"]["green"], data["led_0"]["blue"],
                                 data["led_0"]["brightness"], 0)
        obj.spi.led.prepare_data(data["led_1"]["red"], data["led_1"]["green"], data["led_1"]["blue"],
                                 data["led_1"]["brightness"], 1)
        obj.spi.led.prepare_data(data["led_2"]["red"], data["led_2"]["green"], data["led_2"]["blue"],
                                 data["led_2"]["brightness"], 2)
        obj.spi.led.prepare_data(data["led_3"]["red"], data["led_3"]["green"], data["led_3"]["blue"],
                                 data["led_3"]["brightness"], 3)
        obj.spi.send_led = True
    except json.JSONDecodeError:
        obj.logger_error("MQTT: received msq is not json with expected information")


def on_connect(mqtt_client, obj, flags, rc):
    if rc == 0:
        obj.mqtt_ready = True
        obj.mqtt().subscribe(LL_DISPLAY_TOPIC)
        obj.mqtt().subscribe(LL_LED_TOPIC)
        obj.mqtt().subscribe(LL_READER_DATA_WRITE_TOPIC)
    else:
        obj.mqtt_ready = 0
        retry_time = 2
        while rc != 0:
            time.sleep(retry_time)
            try:
                rc = mqtt_client.reconnect()
            except Exception as e:
                rc = 1
                retry_time = 5

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
    aas = Aas()
    aas.logger().setLevel(logging.DEBUG)
    fh = logging.FileHandler("/var/log/aas-modbus.txt")
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    aas.logger().addHandler(fh)
    aas.logger().addHandler(ch)

    aas.logger().info("Core: ===================== Application start ========================")
    aas.logger().info("Script version: {}".format(__version__))

    aas.mqtt().connect("localhost")
    aas.mqtt().publish(LL_I2C_MSG_TOPIC, "I2C: prepared")
    aas.mqtt().on_connect = on_connect
    aas.mqtt().user_data_set(aas)
    aas.mqtt().message_callback_add(LL_TOUCH_TOPIC, on_touch)

    run_updating_server()
