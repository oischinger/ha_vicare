# Home Assistant ViCare component

Home Assistant component for Viessmann Vitodata service. This is work in progress!

## Links/Credits:
* [Original feature request in HA community](https://community.home-assistant.io/t/viessmann-component/77873)
* [PyViCare](https://github.com/somm15/PyViCare) Python API for accessing the ViCare API used by this project 
* [Homeassistant Viessmann integration](https://github.com/geertmeersman/homeassistant) An integration using mqtt. The code for the Viessmann cloud communication is taken from that repo


## How to set it up:

Put the sensor in your .homeassistant/custom_components directory, e.g. .homeassistant/custom_components/sensor/vicare.py

Add the following sensor to your Home assistant configuration.yaml
```
sensor:
  - platform: vicare
    user: [VICARE_EMAIL]
    password: [VICARE_PASSWORD]
    client_id: '79742319e39245de5f91d15ff4cac2a8'
    client_secret: '8ad97aceb92c5892e102b093c7c083fa'
```

Restart home assistant
