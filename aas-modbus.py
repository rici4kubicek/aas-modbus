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
import msgpack
from enum import Enum
import os

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


class DefaultSlavesID(Enum):
    SLAVE_ID_READER_DATA_READ = 0
    SLAVE_ID_READER_DATA_WRITE = 1
    SLAVE_ID_BUTTONS = 2
    SLAVE_ID_DISPLAY = 3


class Aas:
    _mqtt = mqtt_client.Client()
    _logger = logging.getLogger()

    def __init__(self):
        self.mqtt_ready = False
        self.context = None
        self.config = {}

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
    """
    Button touch MQTT callback
    :param moqs:
    :param obj:
    :param msg:
    :return:
    """
    obj.logger_debug("MQTT: topic: {}, data: {}".format(msg.topic, msg.payload.decode("utf-8")))
    try:
        if obj.config["use_msgpack"]:
            raw = json.loads(msg.payload.decode("utf-8"))
            packed = msgpack.packb(raw)

            values = [v for v in packed]
            aas.logger_debug("new values: " + str(values))
            obj.context[aas.config["slave_id"]["buttons"]].setValues(3, 0, values)
        else:  # if msgpack is not allow save bare json
            values = [ord(v) for v in msg.payload.decode("utf-8")]
            aas.logger_debug("new values: " + str(values))
            obj.context[aas.config["slave_id"]["buttons"]].setValues(3, 0, values)
    except:
        obj.logger_error("MQTT: received msq cannot be processed")


def on_connect(mosq, obj, flags, rc):
    if rc == 0:
        obj.mqtt_ready = True
        obj.mqtt().subscribe(LL_TOUCH_TOPIC)
    else:
        obj.mqtt_ready = 0
        retry_time = 2
        while rc != 0:
            time.sleep(retry_time)
            try:
                rc = mosq.reconnect()
            except Exception as e:
                rc = 1
                retry_time = 5


def run_updating_server(aas_):
    # prepare data context
    store = {}
    for key, value in aas.config["slave_id"].items():
        store[value] = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [0xffff] * 100),
            co=ModbusSequentialDataBlock(0, [0xffff] * 100),
            hr=ModbusSequentialDataBlock(0, [0xffff] * 100),
            ir=ModbusSequentialDataBlock(0, [0xffff] * 100))

    aas_.context = ModbusServerContext(slaves=store, single=False)

    # prepare server identity
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'FEKT VUTBR'
    identity.ProductCode = 'AAS'
    identity.VendorUrl = 'https://www.fekt.vut.cz/'
    identity.ProductName = 'AAS modbus server'
    identity.ModelName = 'AAS module'
    identity.MajorMinorRevision = '1.0.0'

    StartTcpServer(aas_.context, identity=identity, address=("localhost", aas.config["port"]))


if __name__ == "__main__":
    aas = Aas()
    aas.logger().setLevel(logging.DEBUG)
    fh = logging.FileHandler("aas-modbus.txt")
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

    if os.path.isfile("config.json"):
        cfg = open("config.json", "r")
        aas.config = json.load(cfg)
        aas.logger().info("Core: successful read configuration: {}".format(aas.config))
    else:
        aas.config["port"] = 5020
        aas.config["use_msgpack"] = True
        aas.config["slave_id"] = dict()
        aas.config["slave_id"]["reader_data_read"] = DefaultSlavesID.SLAVE_ID_READER_DATA_READ.value
        aas.config["slave_id"]["reader_data_write"] = DefaultSlavesID.SLAVE_ID_READER_DATA_WRITE.value
        aas.config["slave_id"]["buttons"] = DefaultSlavesID.SLAVE_ID_BUTTONS.value
        aas.config["slave_id"]["display"] = DefaultSlavesID.SLAVE_ID_DISPLAY.value
        aas.logger().error("Core: Set default configuration: {}".format(aas.config))

    # connect to MQTT broker
    aas.mqtt().connect("localhost")
    aas.mqtt().on_connect = on_connect
    aas.mqtt().user_data_set(aas)
    aas.mqtt().message_callback_add(LL_TOUCH_TOPIC, on_touch)

    aas.mqtt().loop_start()

    run_updating_server(aas)
