# Home Assistant ViCare component

Home Assistant component for Viessmann Vitodata service. This is work in progress!

## Links/Credits:
* [Original feature request in HA community](https://community.home-assistant.io/t/viessmann-component/77873)
* [PyViCare](https://github.com/somm15/PyViCare) Python API for accessing the ViCare API used by this project 

## How to set it up:

Copy the sensor component to .homeassistant/custom_components/vicare/sensor.py
Copy the climate component to .homeassistant/custom_components/vicare/climate.py

Add the following config to your Home assistant configuration.yaml
```
sensor:
  - platform: vicare
    username: [VICARE_EMAIL]
    password: [VICARE_PASSWORD]
    
climate:
  - platform: vicare
    username: [VICARE_EMAIL]
    password: [VICARE_PASSWORD]
```

Restart home assistant

### Example lovelace config:
![Lovelace Example](/doc/lovelace_example.jpg)
```
type: entities
entities:
  - entity: climate.vicare_heating
  - entity: climate.vicare_water
  
type: thermostat
entity: climate.vicare_heating

type: thermostat
entity: climate.vicare_water

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

## Consumption data
Note that the consumption sensors (sensor.vicare_consumption*) are only reporting data for Vitodens 200 with Vitotronic 200 (Typ HO1B/HO2B) as well as Vitodens 300-W (HO2B), Vitodens 333-F (HO2B) and Vitodens 343-F (HO2B).
