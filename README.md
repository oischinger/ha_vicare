# Home Assistant ViCare component

Home Assistant component for Viessmann Vitodata service. This is work in progress!

Official integration into Home Assistant is currently in progress.

## Links/Credits:
* [Original feature request in HA community](https://community.home-assistant.io/t/viessmann-component/77873)
* [PyViCare](https://github.com/somm15/PyViCare) Python API for accessing the ViCare API used by this project 

## How to set it up:

Copy the contents of the vicare directory to your Home Assistant configuration directory (e.g. ~/.homeassistant or /config on Hass.io) into a subfolder named custom_components/vicare

Add the following config to your Home assistant configuration.yaml
```
vicare:
  username: [VICARE_EMAIL]
  password: [VICARE_PASSWORD]
```

Restart home assistant

More documentation can be found on the [docs pull request to Home Assistant](https://github.com/home-assistant/home-assistant.io/blob/f1887c713a07e4acdf261c37c855b758e6703dd3/source/_components/vicare.markdown)
