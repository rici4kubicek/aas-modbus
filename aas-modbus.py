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
import subprocess

__author__ = "Richard Kubicek"
__copyright__ = "Copyright 2020, FEEC BUT Brno"
__credits__ = ["Richard Kubicek"]
__license__ = "Proprietary"
__version__ = "1.0.1"
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

DATA_DELIMETER = 0xfffe
DATA_NONE = 0xffff


class DefaultSlavesID(Enum):
    SLAVE_ID_READER_DATA_READ = 0
    SLAVE_ID_READER_DATA_WRITE = 1
    SLAVE_ID_READER_STATUS = 2
    SLAVE_ID_BUTTONS = 3
    SLAVE_ID_DISPLAY = 4
    SLAVE_ID_LED = 5


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
    default_values = [DATA_NONE] * 254
    try:
        if obj.config["use_registers"]:
            raw = json.loads(msg.payload.decode("utf-8"))
            values = list()
            values.append(raw["button"])
        elif obj.config["use_msgpack"]:
            raw = json.loads(msg.payload.decode("utf-8"))
            packed = msgpack.packb(raw)

            values = [v for v in packed]
        else:  # if msgpack or registers are not allow use bare json in ascii
            values = [ord(v) for v in msg.payload.decode("utf-8")]
        aas.logger_debug("Buttons: new values: " + str(values))
        # setup default values and then set received values
        obj.context[aas.config["slave_id"]["buttons"]].setValues(3, 0, default_values)
        obj.context[aas.config["slave_id"]["buttons"]].setValues(4, 0, default_values)
        obj.context[aas.config["slave_id"]["buttons"]].setValues(3, 0, values)
        obj.context[aas.config["slave_id"]["buttons"]].setValues(4, 0, values)
    except:
        obj.logger_error("MQTT: received msq cannot be processed")


def on_reader_read(moqs, obj, msg):
    """
    Reader data read MQTT callback
    :param moqs:
    :param obj:
    :param msg:
    :return:
    """
    obj.logger_debug("MQTT: topic: {}, data: {}".format(msg.topic, msg.payload.decode("utf-8")))
    default_values = [DATA_NONE] * 254
    try:
        if obj.config["use_registers"]:
            raw = json.loads(msg.payload.decode("utf-8"))
            values = list()
            for i in range(0, len(raw["uid"])):
                values.append(raw["uid"][i])  # add uid to registers 0 - 6
            values.append(DATA_DELIMETER)  # add 65534 as delimiter
            values.append(raw["tag"]["tag_protocol"])  # add tag protocol to address 10
            values.append(raw["tag"]["tag_size"])  # add tag size to address 11
            values.append(DATA_DELIMETER)  # add 65534 as delimiter
            for page in range(0, len(raw["data"])):
                for val in range(0, 4):
                    values.append(raw["data"][page][val])
                values.append(DATA_DELIMETER)  # add 65534 as delimiter between pages
        elif obj.config["use_msgpack"]:
            raw = json.loads(msg.payload.decode("utf-8"))
            packed = msgpack.packb(raw)

            values = [v for v in packed]
        else:  # if msgpack or registers are not allow use bare json in ascii
            values = [ord(v) for v in msg.payload.decode("utf-8")]
        aas.logger_debug("Reader data read: new values: " + str(values))
        # setup default values and then set received values
        obj.context[aas.config["slave_id"]["reader_data_read"]].setValues(3, 0, default_values)
        obj.context[aas.config["slave_id"]["reader_data_read"]].setValues(4, 0, default_values)
        obj.context[aas.config["slave_id"]["reader_data_read"]].setValues(3, 0, values)
        obj.context[aas.config["slave_id"]["reader_data_read"]].setValues(4, 0, values)
    except:
        obj.logger_error("MQTT: received msq cannot be processed")


def on_reader_status(moqs, obj, msg):
    """
    Reader status MQTT callback
    :param moqs:
    :param obj:
    :param msg:
    :return:
    """
    obj.logger_debug("MQTT: topic: {}, data: {}".format(msg.topic, msg.payload.decode("utf-8")))
    default_values = [DATA_NONE] * 254
    try:
        if obj.config["use_registers"]:
            raw = json.loads(msg.payload.decode("utf-8"))
            values = list()
            values.append(raw["write"]["sector"])
            if raw["write"]["status"] == "OK":
                values.append(1)
            elif raw["write"]["status"] == "NOK":
                values.append(0)
            else:
                values.append(DATA_NONE)
        elif obj.config["use_msgpack"]:
            raw = json.loads(msg.payload.decode("utf-8"))
            packed = msgpack.packb(raw)

            values = [v for v in packed]
        else:  # if msgpack or registers are not allow use bare json in ascii
            values = [ord(v) for v in msg.payload.decode("utf-8")]
        aas.logger_debug("Reader status: new values: " + str(values))
        # setup default values and then set received values
        obj.context[aas.config["slave_id"]["reader_status"]].setValues(3, 0, default_values)
        obj.context[aas.config["slave_id"]["reader_status"]].setValues(4, 0, default_values)
        obj.context[aas.config["slave_id"]["reader_status"]].setValues(3, 0, values)
        obj.context[aas.config["slave_id"]["reader_status"]].setValues(4, 0, values)
    except:
        obj.logger_error("MQTT: received msq cannot be processed")


def on_connect(mosq, obj, flags, rc):
    if rc == 0:
        obj.mqtt_ready = True
        obj.mqtt().subscribe(LL_TOUCH_TOPIC)
        obj.mqtt().subscribe(LL_READER_STATUS_TOPIC)
        obj.mqtt().subscribe(LL_READER_DATA_READ_TOPIC)
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


def check_parse_and_send_values_led(aas_, topic, values_, default_val):
    diff = False
    if values_ != default_val:  # compare values in data space with default values
        dta = bytearray()
        # place values into bytearray
        for i in values_:
            if i != DATA_NONE:
                dta.append(i & 0xff)
            if dta[len(dta) - 1] == 0:
                dta.pop(len(dta) - 1)

        # unpack data or get raw data
        if aas_.config["use_registers"]:
            if len(dta) != 4 * 4:  # 4 bytes per LED
                aas_.logger_error("LED registers: lack of data")
            else:
                data = {}
                for led in range(0, 4):
                    led_str = "led_{}".format(led)
                    data[led_str]["red"] = dta[0 + 4 * led]
                    data[led_str]["green"] = dta[1 + 4 * led]
                    data[led_str]["blue"] = dta[2 + 4 * led]
                    data[led_str]["brightness"] = dta[3 + 4 * led]
        elif aas_.config["use_msgpack"]:
            try:
                data = msgpack.unpackb(dta)
            except:
                data = ""
                aas_.logger_error("MessagePack: received msq cannot be processed")
                diff = False
        else:
            data = dta.decode("utf-8")
        aas_.mqtt().publish(topic, "{}".format(data))
        diff = True
        return diff
    else:
        return diff


def check_parse_and_send_values_display(aas_, topic, values_, default_val):
    diff = False
    if values_ != default_val:  # compare values in data space with default values
        dta = bytearray()
        # place values into bytearray
        for i in values_:
            if i != DATA_NONE:
                dta.append(i & 0xff)
            if dta[len(dta) - 1] == DATA_NONE:
                dta.pop(len(dta) - 1)

        # unpack data or get raw data
        if aas_.config["use_registers"]:
            data = {}

            if dta[0] == 0:
                data["cmd"] = "clear"
            elif dta[0] == 1 or dta[0] == 2:
                if dta[0] == 1:
                    data["cmd"] = "write"
                if dta[0] == 2:
                    data["cmd"] = "scroll"
                data["pos_x"] = dta[1]
                data["pos_y"] = dta[2]
                tmp = bytearray()
                font_end = 0
                for i in range(3, len(dta)):
                    if dta[i] != (DATA_DELIMETER & 0xff):
                        tmp.append(dta[i])
                    else:
                        font_end = i
                        break
                data["font"] = tmp[:].decode("utf-8")
                tmp = bytearray()
                for i in range(font_end + 1, len(dta)):
                    if dta[i] != DATA_NONE:
                        tmp.append(dta[i])
                data["text"] = tmp[:].decode("utf-8")

            else:
                aas_.logger_error("Display registers: unknown command")
        elif aas_.config["use_msgpack"]:
            try:
                data = msgpack.unpackb(dta)
            except:
                data = ""
                aas_.logger_error("MessagePack: received msq cannot be processed")
                diff = False
        else:
            data = dta.decode("utf-8")
        aas_.mqtt().publish(topic, "{}".format(data))
        diff = True
        return diff
    else:
        return diff


def check_parse_and_send_values_reader_write(aas_, topic, values_, default_val):
    diff = False
    if values_ != default_val:  # compare values in data space with default values
        dta = list()
        # place values into list
        for i in values_:
            if i != DATA_NONE:
                dta.append(i)
            if dta[len(dta) - 1] == DATA_NONE:
                dta.pop(len(dta) - 1)

        # unpack data or get raw data
        if aas_.config["use_registers"]:
            data = {}
            sector_cnt = len(dta)/6
            if int(len(dta)) % 6 != 0:
                aas_.logger_error("Registers: received msq cannot be processed")
            else:
                if sector_cnt == 1:
                    tmp_act = list()
                    dta_act = dict()
                    tmp_act.append(dta[0])
                    tmp_act.append(dta[1])
                    tmp_act.append(dta[2])
                    tmp_act.append(dta[3])
                    dta_act["sector"] = dta[4]
                    dta_act["data"] = tmp_act
                    data["write"] = dta_act
                else:
                    wl = list()
                    for i in range(0, int(sector_cnt)):
                        tmp_act = list()
                        dta_act = dict()
                        tmp_act.append(dta[0 + 6 * i])
                        tmp_act.append(dta[1 + 6 * i])
                        tmp_act.append(dta[2 + 6 * i])
                        tmp_act.append(dta[3 + 6 * i])
                        dta_act["sector"] = dta[4 + 6 * i]
                        dta_act["data"] = tmp_act
                        wl.append(dta_act)
                    data["write_multi"] = wl
        elif aas_.config["use_msgpack"]:
            try:
                data = msgpack.unpackb(dta)
            except:
                data = ""
                aas_.logger_error("MessagePack: received msq cannot be processed")
                diff = False
        else:
            data = dta.decode("utf-8")
        
        aas_.mqtt().publish(topic, "{}".format(data))
        diff = True
        return diff
    else:
        return diff


def get_written_values(aas_):
    default_values = [0xffff] * 254
    while True:
        # led control
        values = aas_.context[aas_.config["slave_id"]["led"]].getValues(0x10, 0, 254)
        if check_parse_and_send_values_led(aas_, LL_LED_TOPIC, values, default_values):
            aas_.context[aas_.config["slave_id"]["led"]].setValues(0x10, 0, default_values)

        # display control
        values = aas_.context[aas_.config["slave_id"]["display"]].getValues(0x10, 0, 254)
        if check_parse_and_send_values_display(aas_, LL_DISPLAY_TOPIC, values, default_values):
            aas_.context[aas_.config["slave_id"]["display"]].setValues(0x10, 0, default_values)

        # rfid reader write commands
        values = aas_.context[aas_.config["slave_id"]["reader_data_write"]].getValues(0x10, 0, 254)
        if check_parse_and_send_values_reader_write(aas_, LL_READER_DATA_WRITE_TOPIC, values, default_values):
            aas_.context[aas_.config["slave_id"]["reader_data_write"]].setValues(0x10, 0, default_values)

        time.sleep(1)


def prepare_and_run_server(aas_):
    # prepare data context
    store = {}
    for key, value in aas.config["slave_id"].items():
        store[value] = ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [0xffff] * 255),
            co=ModbusSequentialDataBlock(0, [0xffff] * 255),
            hr=ModbusSequentialDataBlock(0, [0xffff] * 255),
            ir=ModbusSequentialDataBlock(0, [0xffff] * 255))

    aas_.context = ModbusServerContext(slaves=store, single=False)

    # prepare server identity
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'FEKT VUTBR'
    identity.ProductCode = 'AAS'
    identity.VendorUrl = 'https://www.fekt.vut.cz/'
    identity.ProductName = 'AAS modbus server'
    identity.ModelName = 'AAS module'
    identity.MajorMinorRevision = "{}".format(__version__)

    thread = Thread(target=get_written_values, args=(aas_,))
    thread.start()

    # get IP address for communication over network
    cmd = "hostname -I | cut -d\' \' -f1"
    ip = subprocess.check_output(cmd, shell=True)
    ip = str(ip, "ascii")

    StartTcpServer(aas_.context, identity=identity, address=(ip, aas_.config["port"]))


if __name__ == "__main__":
    aas = Aas()
    # setup logger
    aas.logger().setLevel(logging.DEBUG)
    fh = logging.FileHandler("var/log/aas-modbus.txt")
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

    # prepare configuration
    if os.path.isfile("config.json"):
        cfg = open("config.json", "r")
        aas.config = json.load(cfg)
        aas.logger().info("Core: successful read configuration: {}".format(aas.config))

        if aas.config["use_msgpack"] and aas.config["use_registers"]:
            aas.logger().error("Core: only once from \"use_msgpack\" and \"use_registers\" can be set to true")
            aas.logger().error("Core: program exit")
            quit()
    else:
        aas.config["port"] = 5020
        aas.config["use_msgpack"] = True
        aas.config["use_registers"] = False
        aas.config["slave_id"] = dict()
        aas.config["slave_id"]["reader_data_read"] = DefaultSlavesID.SLAVE_ID_READER_DATA_READ.value
        aas.config["slave_id"]["reader_data_write"] = DefaultSlavesID.SLAVE_ID_READER_DATA_WRITE.value
        aas.config["slave_id"]["reader_status"] = DefaultSlavesID.SLAVE_ID_READER_STATUS.value
        aas.config["slave_id"]["buttons"] = DefaultSlavesID.SLAVE_ID_BUTTONS.value
        aas.config["slave_id"]["display"] = DefaultSlavesID.SLAVE_ID_DISPLAY.value
        aas.config["slave_id"]["led"] = DefaultSlavesID.SLAVE_ID_LED.value
        aas.logger().error("Core: Set default configuration: {}".format(aas.config))

    # connect to MQTT broker
    aas.mqtt().connect("localhost")
    aas.mqtt().on_connect = on_connect
    aas.mqtt().user_data_set(aas)
    aas.mqtt().message_callback_add(LL_TOUCH_TOPIC, on_touch)
    aas.mqtt().message_callback_add(LL_READER_DATA_READ_TOPIC, on_reader_read)
    aas.mqtt().message_callback_add(LL_READER_STATUS_TOPIC, on_reader_status)

    aas.mqtt().loop_start()

    prepare_and_run_server(aas)
