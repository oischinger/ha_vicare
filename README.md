# Unofficial Home Assistant custom component for Viessmann ViCare API

[![GitHub contributors](https://img.shields.io/github/contributors/oischinger/ha_vicare)](https://github.com/thebino/vicare/graphs/contributors)
![Version](https://img.shields.io/github/v/release/oischinger/ha_vicare)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

The `vicare` component is a Home Assistant custom component for monitoring and controlling [Viessmann](https://www.viessmann.family) devices through their cloud-based [ViCare API](https://developer.viessmann.com/start.html).

⚠️ **This custom component contains some experimental commits. Use at your own risk**

Please check out the [Official Home Assistant ViCare integration](https://www.home-assistant.io/integrations/vicare) before installing this custom component.

## Why an unofficial integration?

This repo is used for early development purposes and may contain some changes that are not (yet) contributed to Home Assistant Core.

## Installation

### Install with HACS (recommended)

1. Ensure that [HACS](https://community.home-assistant.io/t/custom-component-hacs) is installed.
2. Search for and install the "ViCare" integration.
3. Configure the `vicare` integration.
4. Restart Home Assistant.

#### Install manually

1. Download the [latest release](https://github.com/oischinger/ha_vicare/releases/latest).
2. Unpack the release and copy the `custom_components/vicare` directory
   into the `<config dir>/custom_components` directory of your Home Assistant installation.
3. Configure the `vicare` sensor.
4. Restart Home Assistant.

## Configuration

#### User interface

Open the `Configuration` of your Home-Assistant instance and select `Integrations`.
Add a new integration, search and select `vicare`.
A dialog appears to enter your [ViCare API](https://developer.viessmann.com/start.html) credentials. Please see the documentation of the [official Home Assistant ViCare integration](https://www.home-assistant.io/integrations/vicare) for further details.

## Links/Credits:

- [Original feature request in HA community](https://community.home-assistant.io/t/viessmann-component/77873)
- [PyViCare](https://github.com/somm15/PyViCare) Python API for accessing the ViCare API used by this project
