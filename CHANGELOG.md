# Changelog

## 0.0.5-dev
* Changed: Fix restart issue

## 0.0.4
⚠️ This version is required for Venus OS v3.60~27 or later, but it is also compatible with older versions.
* Added: paho-mqtt module to driver
* Changed: Broker port missing on reconnect
* Changed: Default device instance is now `100`
* Changed: Fixed service not starting sometimes

## v0.0.3
* Changed: Add VRM ID to MQTT client name
* Changed: Fix registration to dbus https://github.com/victronenergy/velib_python/commit/494f9aef38f46d6cfcddd8b1242336a0a3a79563

## v0.0.2
* Changed: Fixed problems when timeout was set to `0`.
* Changed: Fixed units for forwarded energy.
* Changed: Other smaller fixes.

## v0.0.1
Initial release
