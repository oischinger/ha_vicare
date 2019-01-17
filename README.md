# Home Assistant ViCare component

Home Assistant component for Viessmann Vitodata service. This is work in progress!

## Links/Credits:
* [Original feature request in HA community](https://community.home-assistant.io/t/viessmann-component/77873)
* [PyViCare](https://github.com/somm15/PyViCare) Python API for accessing the ViCare API used by this project 

## How to set it up:

Put the sensor in your .homeassistant/custom_components directory, e.g. .homeassistant/custom_components/sensor/vicare.py

Add the following sensor to your Home assistant configuration.yaml
```
sensor:
  - platform: vicare
    user: [VICARE_EMAIL]
    password: [VICARE_PASSWORD]
    
climate:
  - platform: vicare
    user: [VICARE_EMAIL]
    password: [VICARE_PASSWORD]
```

Restart home assistant

### Example lovelace config:
```
type: entities
entities:
  - entity: climate.vicare

type: thermostat
entity: climate.vicare

type: history-graph
entities:
  - entity: sensor.vicare_gasconsumptionheatingthisyear
    name: Verbrauch Heizen
  - entity: sensor.vicare_gasconsumptiondomestichotwaterthisyear
    name: Verbrauch Wasser
  - entity: sensor.vicare_activeprogram
    name: Programm
  - entity: sensor.vicare_activemode
    name: Modus
  - entity: sensor.vicare_boilertemperature
    name: Kesseltemperatur
  - entity: sensor.vicare_currentdesiredtemperature
    name: Solltemp. Heizen
  - entity: sensor.vicare_domestichotwaterconfiguredtemperature
    name: Solltemp. Wasser
  - entity: sensor.vicare_domestichotwaterstoragetemperature
    name: Wassertemperatur
  - entity: sensor.vicare_outsidetemperature
    name: Aussenfühler


```
