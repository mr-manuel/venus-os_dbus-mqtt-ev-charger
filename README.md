# dbus-mqtt-ev-charger - Emulates a EV charger from MQTT data

<small>GitHub repository: [mr-manuel/venus-os_dbus-mqtt-ev-charger](https://github.com/mr-manuel/venus-os_dbus-mqtt-ev-charger)</small>

## Index

1. [Disclaimer](#disclaimer)
1. [Supporting/Sponsoring this project](#supportingsponsoring-this-project)
1. [Purpose](#purpose)
1. [Config](#config)
1. [JSON structure](#json-structure)
1. [Install / Update](#install--update)
1. [Uninstall](#uninstall)
1. [Restart](#restart)
1. [Debugging](#debugging)
1. [Compatibility](#compatibility)
1. [Screenshots](#screenshots)


## Disclaimer

I wrote this script for myself. I'm not responsible, if you damage something using my script.


## Supporting/Sponsoring this project

You like the project and you want to support me?

[<img src="https://github.md0.eu/uploads/donate-button.svg" height="50">](https://www.paypal.com/donate/?hosted_button_id=3NEVZBDM5KABW)


## Purpose

The script emulates a EV charger in Venus OS. It gets the MQTT data from a subscribed topic and publishes the information on the dbus as the service `com.victronenergy.evcharger.mqtt_ev_charger` with the VRM instance `11`.


## Config

Copy or rename the `config.sample.ini` to `config.ini` in the `dbus-mqtt-ev-charger` folder and change it as you need it.


## JSON structure

<details><summary>Minimum required to start the driver</summary>

```json
{
    "Ac": {
        "Power": 321.6
    }
}
```
</details>

<details><summary>Full (with descriptions)</summary>

### Payload

```json
{
    "Ac": {
        "Power": 12000.0,
        "L1": {
            "Power": 4000.0
        },
        "L2": {
            "Power": 4000.0
        },
        "L3": {
            "Power": 4000.0
        },
        "Energy": {
            "Forward": 342.4
        }
    },
    "Current": 17.39,
    "MaxCurrent": 32,
    "SetCurrent": 16,
    "AutoStart": 1,
    "ChargingTime": 63,
    "EnableDisplay": 1,
    "Mode": 1,
    "StartStop": 1,
    "Status": 1
}
```

### Description

```
/Ac/Power                  --> Write: AC Power (W)
/Ac/L1/Power               --> Write: L1 Power used (W)
/Ac/L2/Power               --> Write: L2 Power used (W)
/Ac/L3/Power               --> Write: L3 Power used (W)
/Ac/Energy/Forward         --> Write: Total Charged Energy (kWh)

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
/Position                  --> Write: Charger position (number)
    0 = AC Input
    1 = AC Output
/StartStop                 --> Read/Write: Enable charging (number)
    0 = Enable charging: False
    1 = Enable charging: True
/Status                    --> Write: Status (number)
    0 = Disconnected
    1 = Connected
    2 = Charging
    3 = Charged
    4 = Waiting for sun
    5 = Waiting for RFID
    6 = Waiting for start
    7 = Low SOC
    8 = Ground test error
    9 = Welded contacts test error
    10 = CP input test error (shorted)
    11 = Residual current detected
    12 = Undervoltage detected
    13 = Overvoltage detected
    14 = Overheating detected
    15 = Reserved
    16 = Reserved
    17 = Reserved
    18 = Reserved
    19 = Reserved
    20 = Charging limit
    21 = Start charging
    22 = Switching to 3-phase
    23 = Switching to 1-phase
    24 = Stop charging
```
</details>


# Read settings

Changed settings can be found on this MQTT path of the Venus OS broker:

```
N/<vrm_id>/evcharger/11/...
```


## Install / Update

1. Login to your Venus OS device via SSH. See [Venus OS:Root Access](https://www.victronenergy.com/live/ccgx:root_access#root_access) for more details.

2. Execute this commands to download and copy the files:

    ```bash
    wget -O /tmp/download_dbus-mqtt-ev-charger.sh https://raw.githubusercontent.com/mr-manuel/venus-os_dbus-mqtt-ev-charger/master/download.sh

    bash /tmp/download_dbus-mqtt-ev-charger.sh
    ```

3. Select the version you want to install.

4. Press enter for a single instance. For multiple instances, enter a number and press enter.

    Example:

    - Pressing enter or entering `1` will install the driver to `/data/etc/dbus-mqtt-ev-charger`.
    - Entering `2` will install the driver to `/data/etc/dbus-mqtt-ev-charger-2`.

### Extra steps for your first installation

5. Edit the config file to fit your needs. The correct command for your installation is shown after the installation.

    - If you pressed enter or entered `1` during installation:
    ```bash
    nano /data/etc/dbus-mqtt-ev-charger/config.ini
    ```

    - If you entered `2` during installation:
    ```bash
    nano /data/etc/dbus-mqtt-ev-charger-2/config.ini
    ```

6. Install the driver as a service. The correct command for your installation is shown after the installation.

    - If you pressed enter or entered `1` during installation:
    ```bash
    bash /data/etc/dbus-mqtt-ev-charger/install.sh
    ```

    - If you entered `2` during installation:
    ```bash
    bash /data/etc/dbus-mqtt-ev-charger-2/install.sh
    ```

    The daemon-tools should start this service automatically within seconds.

## Uninstall

⚠️ If you have multiple instances, ensure you choose the correct one. For example:

- To uninstall the default instance:
    ```bash
    bash /data/etc/dbus-mqtt-ev-charger/uninstall.sh
    ```

- To uninstall the second instance:
    ```bash
    bash /data/etc/dbus-mqtt-ev-charger-2/uninstall.sh
    ```

## Restart

⚠️ If you have multiple instances, ensure you choose the correct one. For example:

- To restart the default instance:
    ```bash
    bash /data/etc/dbus-mqtt-ev-charger/restart.sh
    ```

- To restart the second instance:
    ```bash
    bash /data/etc/dbus-mqtt-ev-charger-2/restart.sh
    ```

## Debugging

⚠️ If you have multiple instances, ensure you choose the correct one.

- To check the logs of the default instance:
    ```bash
    tail -n 100 -F /data/log/dbus-mqtt-ev-charger/current | tai64nlocal
    ```

- To check the logs of the second instance:
    ```bash
    tail -n 100 -F /data/log/dbus-mqtt-ev-charger-2/current | tai64nlocal
    ```

The service status can be checked with svstat `svstat /service/dbus-mqtt-ev-charger`

This will output somethink like `/service/dbus-mqtt-ev-charger: up (pid 5845) 185 seconds`

If the seconds are under 5 then the service crashes and gets restarted all the time. If you do not see anything in the logs you can increase the log level in `/data/etc/dbus-mqtt-ev-charger/dbus-mqtt-ev-charger.py` by changing `level=logging.WARNING` to `level=logging.INFO` or `level=logging.DEBUG`

If the script stops with the message `dbus.exceptions.NameExistsException: Bus name already exists: com.victronenergy.evcharger.mqtt_ev_charger"` it means that the service is still running or another service is using that bus name.


## Compatibility

This software supports the latest three stable versions of Venus OS. It may also work on older versions, but this is not guaranteed.

## Screenshots

<details><summary>MQTT EV Charger</summary>

![MQTT EV Charger - device list](/screenshots/ev-charger_device_list.png)
![MQTT EV Charger - device list - mqtt ev charger](/screenshots/ev-charger_device_list_ev-charger_1.png)
![MQTT EV Charger - device list - mqtt ev charger](/screenshots/ev-charger_device_list_ev-charger_2.png)
![MQTT EV Charger - device list - mqtt ev charger](/screenshots/ev-charger_device_list_ev-charger_setup_1.png)
![MQTT EV Charger - device list - mqtt ev charger](/screenshots/ev-charger_device_list_ev-charger_device_1.png)
![MQTT EV Charger - device list - mqtt ev charger](/screenshots/ev-charger_device_list_ev-charger_device_2.png)

</details>
