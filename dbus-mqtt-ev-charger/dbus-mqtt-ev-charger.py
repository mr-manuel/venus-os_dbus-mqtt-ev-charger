#!/usr/bin/env python

from gi.repository import GLib  # pyright: ignore[reportMissingImports]
import platform
import logging
import sys
import os
from time import sleep, time
import json
import paho.mqtt.client as mqtt
import configparser  # for config/ini file
import _thread

# import Victron Energy packages
sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'ext', 'velib_python'))
from vedbus import VeDbusService


# get values from config.ini file
try:
    config_file = (os.path.dirname(os.path.realpath(__file__))) + "/config.ini"
    if os.path.exists(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)
        if (config['MQTT']['broker_address'] == "IP_ADDR_OR_FQDN"):
            print("ERROR:The \"config.ini\" is using invalid default values like IP_ADDR_OR_FQDN. The driver restarts in 60 seconds.")
            sleep(60)
            sys.exit()
    else:
        print("ERROR:The \"" + config_file + "\" is not found. Did you copy or rename the \"config.sample.ini\" to \"config.ini\"? The driver restarts in 60 seconds.")
        sleep(60)
        sys.exit()

except Exception:
    exception_type, exception_object, exception_traceback = sys.exc_info()
    file = exception_traceback.tb_frame.f_code.co_filename
    line = exception_traceback.tb_lineno
    print(f"Exception occurred: {repr(exception_object)} of type {exception_type} in {file} line #{line}")
    print("ERROR:The driver restarts in 60 seconds.")
    sleep(60)
    sys.exit()


# Get logging level from config.ini
# ERROR = shows errors only
# WARNING = shows ERROR and warnings
# INFO = shows WARNING and running functions
# DEBUG = shows INFO and data/values
if 'DEFAULT' in config and 'logging' in config['DEFAULT']:
    if config['DEFAULT']['logging'] == 'DEBUG':
        logging.basicConfig(level=logging.DEBUG)
    elif config['DEFAULT']['logging'] == 'INFO':
        logging.basicConfig(level=logging.INFO)
    elif config['DEFAULT']['logging'] == 'ERROR':
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.WARNING)
else:
    logging.basicConfig(level=logging.WARNING)


# get timeout
if 'DEFAULT' in config and 'timeout' in config['DEFAULT']:
    timeout = int(config['DEFAULT']['timeout'])
else:
    timeout = 60


# set variables
connected = 0
last_changed = 0
last_updated = 0
charging_time = {
    "start": None,
    "calculate": False,
    "stopped_since": 0
}
STOP_CHARGING_COUNTER_AFTER = 300  # seconds


# formatting
def _a(p, v): return (str("%.1f" % v) + "A")
def _n(p, v): return (str("%i" % v))
def _s(p, v): return (str("%s" % v))
def _w(p, v): return (str("%i" % v) + "W")
def _kwh(p, v): return (str("%.2f" % v) + "kWh")


ev_charger_dict = {

    # general data
    '/Ac/Power':                            {'value': None, 'textformat': _w},
    '/Ac/L1/Power':                         {'value': None, 'textformat': _w},
    '/Ac/L2/Power':                         {'value': None, 'textformat': _w},
    '/Ac/L3/Power':                         {'value': None, 'textformat': _w},
    '/Ac/Energy/Forward':                   {'value': None, 'textformat': _kwh},

    '/Current':                             {'value': None, 'textformat': _a},
    '/MaxCurrent':                          {'value': None, 'textformat': _a},
    '/SetCurrent':                          {'value': None, 'textformat': _a},

    '/AutoStart':                           {'value': 0, 'textformat': _n},
    '/ChargingTime':                        {'value': None, 'textformat': _n},
    '/EnableDisplay':                       {'value': 1, 'textformat': _n},
    '/Mode':                                {'value': 1, 'textformat': _n},
    '/Model':                               {'value': None, 'textformat': _s},
    '/Role':                                {'value': None, 'textformat': _n},
    '/StartStop':                           {'value': 1, 'textformat': _n},

    '/Status':                              {'value': None, 'textformat': _n},

}


"""
com.victronenergy.evcharger

/Ac/Power                  --> Write: AC Power (W)
/Ac/L1/Power               --> Write: L1 Power used (W)
/Ac/L2/Power               --> Write: L2 Power used (W)
/Ac/L3/Power               --> Write: L3 Power used (W)
/Ac/Energy/Forward         --> Write: Charged Energy (kWh)

/Current                   --> Write: Actual charging current (A)
/MaxCurrent                --> Read/Write: Max charging current (A)
/SetCurrent                --> Read/Write: Charging current (A)

/AutoStart                 --> Read/Write: Start automatically (number)
    0 = Charger autostart disabled
    1 = Charger autostart enabled
/ChargingTime              --> Write: Total charging time (seconds)
/EnableDisplay             --> Read/Write: Lock charger display (number)
    0 = Control disabled
    1 = Control enabled
/Mode                      --> Read/Write: Charge mode (number)
    0 = Manual
    1 = Automatic
    2 = Scheduled
/Model                     --> Model, e.g. AC22E or AC22NS (for No Screen)
/Position                  --> Write: Charger position (number)
    0 = AC Output
    1 = AC Input
/Role                      --> Unknown usage
/StartStop                 --> Read/Write: Enable charging (number)
    0 = Enable charging: False
    1 = Enable charging: True
/Status                    --> Write: Status (number)
    0 = EV disconnected
    1 = Connected
    2 = Charging
    3 = Charged
    4 = Waiting for sun
    5 = Waiting for RFID
    6 = Waiting for enable
    7 = Low SOC
    8 = Ground error
    9 = Welded contacts error
    10 = CP input test error
    11 = Residual current detected
    12 = Undervoltage detected
    13 = Overvoltage detected
    14 = Overheating detected
    21 = Start charging
    22 = Switching to 3-phase
    23 = Switching to single phase
"""


# MQTT requests
def on_disconnect(client, userdata, rc):
    global connected
    logging.warning("MQTT client: Got disconnected")
    if rc != 0:
        logging.warning('MQTT client: Unexpected MQTT disconnection. Will auto-reconnect')
    else:
        logging.warning('MQTT client: rc value:' + str(rc))

    while connected == 0:
        try:
            logging.warning("MQTT client: Trying to reconnect")
            client.connect(config['MQTT']['broker_address'])
            connected = 1
        except Exception as err:
            logging.error(f"MQTT client: Error in retrying to connect with broker ({config['MQTT']['broker_address']}:{config['MQTT']['broker_port']}): {err}")
            logging.error("MQTT client: Retrying in 15 seconds")
            connected = 0
            sleep(15)


def on_connect(client, userdata, flags, rc):
    global connected
    if rc == 0:
        logging.info("MQTT client: Connected to MQTT broker!")
        connected = 1
        client.subscribe(config['MQTT']['topic'])
    else:
        logging.error("MQTT client: Failed to connect, return code %d\n", rc)


def on_message(client, userdata, msg):
    try:

        global \
            ev_charger_dict, last_changed

        # get JSON from topic
        if msg.topic == config['MQTT']['topic']:
            if msg.payload != '' and msg.payload != b'':
                jsonpayload = json.loads(msg.payload)

                last_changed = int(time())

                if (
                    'Ac' in jsonpayload
                    and 'Power' in jsonpayload['Ac']
                ):

                    # save JSON data into ev_charger_dict
                    for key_1, data_1 in jsonpayload.items():

                        key = '/' + key_1

                        if type(data_1) is dict:

                            for key_2, data_2 in data_1.items():

                                key = '/' + key_1 + '/' + key_2

                                if type(data_2) is dict:

                                    for key_3, data_3 in data_2.items():

                                        key = '/' + key_1 + '/' + key_2 + '/' + key_3

                                        if (
                                            key in ev_charger_dict
                                            and
                                            (
                                                type(data_3) is str
                                                or
                                                type(data_3) is int
                                                or
                                                type(data_3) is float
                                            )
                                        ):
                                            ev_charger_dict[key]['value'] = data_3
                                        else:
                                            logging.warning("Received key \"" + str(key) + "\" with value \"" + str(data_3) + "\" is not valid")

                                else:

                                    if (
                                        key in ev_charger_dict
                                        and
                                        (
                                            type(data_2) is str
                                            or
                                            type(data_2) is int
                                            or
                                            type(data_2) is float
                                        )
                                    ):
                                        ev_charger_dict[key]['value'] = data_2
                                    else:
                                        logging.warning("Received key \"" + str(key) + "\" with value \"" + str(data_2) + "\" is not valid")

                        else:

                            if (
                                key in ev_charger_dict
                                and
                                (
                                    type(data_1) is str
                                    or
                                    type(data_1) is int
                                    or
                                    type(data_1) is float
                                )
                            ):
                                ev_charger_dict[key]['value'] = data_1
                            else:
                                logging.warning("Received key \"" + str(key) + "\" with value \"" + str(data_1) + "\" is not valid")

                    # ------ calculate possible values if missing -----
                    # Current
                    if 'Current' not in jsonpayload:
                        if 'L1' in jsonpayload['Ac'] and 'L2' in jsonpayload['Ac'] and 'L3' in jsonpayload['Ac']:
                            ev_charger_dict['/Current']['value'] = round(
                                (
                                    ev_charger_dict['/Ac/Power']['value']
                                    / int(config['DEFAULT']['voltage'])
                                ) / 3,
                                3
                            ) if ev_charger_dict['/Ac/Power']['value'] != 0 else 0

                        elif 'L1' in jsonpayload['Ac'] and 'L2' in jsonpayload['Ac'] or 'L1' in jsonpayload['Ac'] and 'L3' in jsonpayload['Ac'] or 'L2' in jsonpayload['Ac'] and 'L3' in jsonpayload['Ac']:
                            ev_charger_dict['/Current']['value'] = round(
                                (
                                    ev_charger_dict['/Ac/Power']['value']
                                    / int(config['DEFAULT']['voltage'])
                                ) / 2,
                                3
                            ) if ev_charger_dict['/Ac/Power']['value'] != 0 else 0

                        else:
                            ev_charger_dict['/Current']['value'] = round(
                                (
                                    ev_charger_dict['/Ac/Power']['value']
                                    / int(config['DEFAULT']['voltage'])
                                ),
                                3
                            ) if ev_charger_dict['/Ac/Power']['value'] != 0 else 0

                    # ChargingTime
                    if 'ChargingTime' in jsonpayload:
                        charging_time["calculate"] = False
                    else:
                        charging_time["calculate"] = True

                else:
                    logging.warning("Received JSON doesn't contain minimum required values")
                    logging.warning("Example: {\"Ac\":{\"Power\":321.6} }")
                    logging.debug("MQTT payload: " + str(msg.payload)[1:])

            else:
                logging.warning("Received message was empty and therefore it was ignored")
                logging.debug("MQTT payload: " + str(msg.payload)[1:])

    except ValueError as e:
        logging.error("Received message is not a valid JSON. %s" % e)
        logging.debug("MQTT payload: " + str(msg.payload)[1:])

    except Exception:
        exception_type, exception_object, exception_traceback = sys.exc_info()
        file = exception_traceback.tb_frame.f_code.co_filename
        line = exception_traceback.tb_lineno
        logging.error(f"Exception occurred: {repr(exception_object)} of type {exception_type} in {file} line #{line}")
        logging.debug("MQTT payload: " + str(msg.payload)[1:])


class DbusMqttEvChargerService:
    def __init__(
        self,
        servicename,
        deviceinstance,
        paths,
        productname='MQTT EV Charger',
        customname='MQTT EV Charger',
        connection='MQTT EV Charger service'
    ):

        self._dbusservice = VeDbusService(servicename)
        self._paths = paths

        logging.debug("%s /DeviceInstance = %d" % (servicename, deviceinstance))

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
        self._dbusservice.add_path('/Mgmt/ProcessVersion', 'Unkown version, and running on Python ' + platform.python_version())
        self._dbusservice.add_path('/Mgmt/Connection', connection)

        # Create the mandatory objects
        self._dbusservice.add_path('/DeviceInstance', deviceinstance)
        self._dbusservice.add_path('/ProductId', 0xFFFF)
        self._dbusservice.add_path('/ProductName', productname)
        self._dbusservice.add_path('/CustomName', customname)
        self._dbusservice.add_path('/FirmwareVersion', '0.0.1 (20231226)')
        # self._dbusservice.add_path('/HardwareVersion', '')
        self._dbusservice.add_path('/Connected', 1)

        self._dbusservice.add_path('/Position', int(config['DEFAULT']['position']))

        self._dbusservice.add_path('/Latency', None)

        for path, settings in self._paths.items():
            self._dbusservice.add_path(
                path, settings['value'], gettextcallback=settings['textformat'], writeable=True, onchangecallback=self._handlechangedvalue
                )

        GLib.timeout_add(1000, self._update)  # pause 1000ms before the next request

    def _update(self):

        global \
            ev_charger_dict, last_changed, last_updated

        now = int(time())

        if last_changed != last_updated:

            for setting, data in ev_charger_dict.items():

                try:
                    self._dbusservice[setting] = data['value']

                except TypeError as e:
                    logging.error("Received key \"" + setting + "\" with value \"" + str(data['value']) + "\" is not valid: " + str(e))
                    sys.exit()

                except Exception:
                    exception_type, exception_object, exception_traceback = sys.exc_info()
                    file = exception_traceback.tb_frame.f_code.co_filename
                    line = exception_traceback.tb_lineno
                    logging.error(f"Exception occurred: {repr(exception_object)} of type {exception_type} in {file} line #{line}")

            logging.info("Data: {:.2f} W".format(ev_charger_dict['/Ac/Power']['value']))

            last_updated = last_changed

        # calculate charging time
        if charging_time["calculate"]:

            # set charging time start
            if charging_time["start"] is None and ev_charger_dict['/Ac/Power']['value'] > 0:
                charging_time["start"] = now

            # calculate charging time if charging started
            if charging_time["start"] is not None:
                ev_charger_dict['/ChargingTime']['value'] = now - charging_time["start"]

                if ev_charger_dict['/Ac/Power']['value'] == 0 and charging_time["stopped_since"] is None:
                    charging_time["stopped_since"] = now
                elif ev_charger_dict['/Ac/Power']['value'] > 0 and charging_time["stopped_since"] is not None:
                    charging_time["stopped_since"] = None

                if charging_time["stopped_since"] is not None and STOP_CHARGING_COUNTER_AFTER < now - charging_time["stopped_since"]:
                    charging_time["start"] = None
                    charging_time["stopped_since"] = None
                    ev_charger_dict['/ChargingTime']['value'] = None

        # quit driver if timeout is exceeded
        if timeout != 0 and (now - last_changed) > timeout:
            logging.error("Driver stopped. Timeout of %i seconds exceeded, since no new MQTT message was received in this time." % timeout)
            sys.exit()

        # increment UpdateIndex - to show that new data is available
        index = self._dbusservice['/UpdateIndex'] + 1  # increment index
        if index > 255:   # maximum value of the index
            index = 0       # overflow from 255 to 0
        self._dbusservice['/UpdateIndex'] = index
        return True

    def _handlechangedvalue(self, path, value):
        logging.debug("someone else updated %s to %s" % (path, value))
        return True  # accept the change


def main():
    _thread.daemon = True  # allow the program to quit

    from dbus.mainloop.glib import DBusGMainLoop  # pyright: ignore[reportMissingImports]
    # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
    DBusGMainLoop(set_as_default=True)

    # MQTT setup
    client = mqtt.Client("MqttEvCharger_" + str(config['MQTT']['device_instance']))
    client.on_disconnect = on_disconnect
    client.on_connect = on_connect
    client.on_message = on_message

    # check tls and use settings, if provided
    if 'tls_enabled' in config['MQTT'] and config['MQTT']['tls_enabled'] == '1':
        logging.info("MQTT client: TLS is enabled")

        if 'tls_path_to_ca' in config['MQTT'] and config['MQTT']['tls_path_to_ca'] != '':
            logging.info("MQTT client: TLS: custom ca \"%s\" used" % config['MQTT']['tls_path_to_ca'])
            client.tls_set(config['MQTT']['tls_path_to_ca'], tls_version=2)
        else:
            client.tls_set(tls_version=2)

        if 'tls_insecure' in config['MQTT'] and config['MQTT']['tls_insecure'] != '':
            logging.info("MQTT client: TLS certificate server hostname verification disabled")
            client.tls_insecure_set(True)

    # check if username and password are set
    if 'username' in config['MQTT'] and 'password' in config['MQTT'] and config['MQTT']['username'] != '' and config['MQTT']['password'] != '':
        logging.info("MQTT client: Using username \"%s\" and password to connect" % config['MQTT']['username'])
        client.username_pw_set(username=config['MQTT']['username'], password=config['MQTT']['password'])

    # connect to broker
    logging.info(f"MQTT client: Connecting to broker {config['MQTT']['broker_address']} on port {config['MQTT']['broker_port']}")
    client.connect(
        host=config['MQTT']['broker_address'],
        port=int(config['MQTT']['broker_port'])
    )
    client.loop_start()

    # wait to receive first data, else the JSON is empty and phase setup won't work
    i = 0
    while ev_charger_dict['/Ac/Power']['value'] is None:
        if i % 12 != 0 or i == 0:
            logging.info("Waiting 5 seconds for receiving first data...")
        else:
            logging.warning("Waiting since %s seconds for receiving first data..." % str(i * 5))

        # check if timeout was exceeded
        if timeout <= (i * 5):
            logging.error(
                "Driver stopped. Timeout of %i seconds exceeded, since no new MQTT message was received in this time."
                % timeout
            )
            sys.exit()

        sleep(5)
        i += 1

    paths_dbus = {
        '/UpdateIndex': {'value': 0, 'textformat': _n},
    }
    paths_dbus.update(ev_charger_dict)

    DbusMqttEvChargerService(
        servicename='com.victronenergy.evcharger.mqtt_ev_charger_' + str(config['MQTT']['device_instance']),
        deviceinstance=int(config['MQTT']['device_instance']),
        customname=config['MQTT']['device_name'],
        paths=paths_dbus
        )

    logging.info('Connected to dbus and switching over to GLib.MainLoop() (= event based)')
    mainloop = GLib.MainLoop()
    mainloop.run()


if __name__ == "__main__":
    main()
