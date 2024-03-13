# dbus-mqtt-ev-charger - Emulates a EV charger from MQTT data

<small>GitHub repository: [mr-manuel/venus-os_dbus-mqtt-ev-charger](https://github.com/mr-manuel/venus-os_dbus-mqtt-ev-charger)</small>

### Disclaimer

I wrote this script for myself. I'm not responsible, if you damage something using my script.


## Supporting/Sponsoring this project

You like the project and you want to support me?

[<img src="https://github.md0.eu/uploads/donate-button.svg" height="50">](https://www.paypal.com/donate/?hosted_button_id=3NEVZBDM5KABW)


### Purpose

The script emulates a EV charger in Venus OS. It gets the MQTT data from a subscribed topic and publishes the information on the dbus as the service `com.victronenergy.evcharger.mqtt_ev_charger` with the VRM instance `11`.


### Config

Copy or rename the `config.sample.ini` to `config.ini` in the `dbus-mqtt-ev-charger` folder and change it as you need it.


### JSON structure

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

#### Payload

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
    "Status": 1,
}
```

#### Description

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
```
</details>


# Read settings

Changed settings can be found on this MQTT path of the Venus OS broker:

```
N/<vrm_id>/evcharger/11/...
```


### Install / Update

1. Login to your Venus OS device via SSH. See [Venus OS:Root Access](https://www.victronenergy.com/live/ccgx:root_access#root_access) for more details.

2. Execute this commands to download and extract the files:

    ```bash
    # change to temp folder
    cd /tmp

    # download driver
    wget -O /tmp/venus-os_dbus-mqtt-ev-charger.zip https://github.com/mr-manuel/venus-os_dbus-mqtt-ev-charger/archive/refs/heads/master.zip

    # If updating: cleanup old folder
    rm -rf /tmp/venus-os_dbus-mqtt-ev-charger-master

    # unzip folder
    unzip venus-os_dbus-mqtt-ev-charger.zip

    # If updating: backup existing config file
    mv /data/etc/dbus-mqtt-ev-charger/config.ini /data/etc/dbus-mqtt-ev-charger_config.ini

    # If updating: cleanup existing driver
    rm -rf /data/etc/dbus-mqtt-ev-charger

    # copy files
    cp -R /tmp/venus-os_dbus-mqtt-ev-charger-master/dbus-mqtt-ev-charger/ /data/etc/

    # If updating: restore existing config file
    mv /data/etc/dbus-mqtt-ev-charger_config.ini /data/etc/dbus-mqtt-ev-charger/config.ini
    ```

3. Copy the sample config file, if you are installing the driver for the first time and edit it to your needs.

    ```bash
    # copy default config file
    cp /data/etc/dbus-mqtt-ev-charger/config.sample.ini /data/etc/dbus-mqtt-ev-charger/config.ini

    # edit the config file with nano
    nano /data/etc/dbus-mqtt-ev-charger/config.ini
    ```

4. Run `bash /data/etc/dbus-mqtt-ev-charger/install.sh` to install the driver as service.

   The daemon-tools should start this service automatically within seconds.


### Uninstall

Run `/data/etc/dbus-mqtt-ev-charger/uninstall.sh`


### Restart

Run `/data/etc/dbus-mqtt-ev-charger/restart.sh`


### Debugging

The logs can be checked with `tail -n 100 -F /data/log/dbus-mqtt-ev-charger/current | tai64nlocal`

The service status can be checked with svstat `svstat /service/dbus-mqtt-ev-charger`

This will output somethink like `/service/dbus-mqtt-ev-charger: up (pid 5845) 185 seconds`

If the seconds are under 5 then the service crashes and gets restarted all the time. If you do not see anything in the logs you can increase the log level in `/data/etc/dbus-mqtt-ev-charger/dbus-mqtt-ev-charger.py` by changing `level=logging.WARNING` to `level=logging.INFO` or `level=logging.DEBUG`

If the script stops with the message `dbus.exceptions.NameExistsException: Bus name already exists: com.victronenergy.evcharger.mqtt_ev_charger"` it means that the service is still running or another service is using that bus name.


### Multiple instances

It's possible to have multiple instances, but it's not automated. Follow these steps to achieve this:

1. Save the new name to a variable `driverclone=dbus-mqtt-ev-charger-2`

2. Copy current folder `cp -r /data/etc/dbus-mqtt-ev-charger/ /data/etc/$driverclone/`

3. Rename the main script `mv /data/etc/$driverclone/dbus-mqtt-ev-charger.py /data/etc/$driverclone/$driverclone.py`

4. Fix the script references for service and log
    ```
    sed -i 's:dbus-mqtt-ev-charger:'$driverclone':g' /data/etc/$driverclone/service/run
    sed -i 's:dbus-mqtt-ev-charger:'$driverclone':g' /data/etc/$driverclone/service/log/run
    ```

5. Change the `device_name` and increase the `device_instance` in the `config.ini`

Now you can install and run the cloned driver. Should you need another instance just increase the number in step 1 and repeat all steps.


### Compatibility

It was tested on following devices:

* RaspberryPi 4b
* MultiPlus II (GX Version)


### Screenshots

<details><summary>MQTT EV Charger</summary>

![MQTT EV Charger - device list](/screenshots/ev-charger_device_list.png)
![MQTT EV Charger - device list - mqtt ev charger](/screenshots/ev-charger_device_list_ev-charger_1.png)
![MQTT EV Charger - device list - mqtt ev charger](/screenshots/ev-charger_device_list_ev-charger_2.png)
![MQTT EV Charger - device list - mqtt ev charger](/screenshots/ev-charger_device_list_ev-charger_setup_1.png)
![MQTT EV Charger - device list - mqtt ev charger](/screenshots/ev-charger_device_list_ev-charger_device_1.png)
![MQTT EV Charger - device list - mqtt ev charger](/screenshots/ev-charger_device_list_ev-charger_device_2.png)

</details>
