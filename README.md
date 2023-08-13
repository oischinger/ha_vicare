# Unofficial Home Assistant custom component for Viessmann ViCare API

[![GitHub contributors](https://img.shields.io/github/contributors/oischinger/ha_vicare)](https://github.com/thebino/vicare/graphs/contributors)
![Version](https://img.shields.io/github/v/release/oischinger/ha_vicare)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

The `vicare` component is a Home Assistant custom component for monitoring and controlling [Viessmann](https://www.viessmann.family) devices through their cloud-based [ViCare API](https://developer.viessmann.com/start.html).

⚠️ **This custom component contains some experimental commits. Use at your own risk**

Please check out the [Official Home Assistant ViCare integration](https://www.home-assistant.io/integrations/vicare) before installing this custom component.

## Why an unofficial integration?

⚠️ As the only maintainer of this integration did not allow me to maintain it up to the [standards of a Home Assistant Core](https://developers.home-assistant.io/docs/integration_quality_scale_index). The interest in this integration grew rapidly and I could not keep up with it.

Nevertheless I decided to still publish my work as a custom integration. Feel free to use it but please understand that I have very little time to work on it.

Please refer to the [Changelog](CHANGELOG.md) to see what changed compared to the [Official Home Assistant ViCare integration](https://www.home-assistant.io/integrations/vicare).

## Installation

### Install with HACS (recommended)

1. Ensure that [HACS](https://community.home-assistant.io/t/custom-component-hacs) is installed.
2. In HACS [add a custom repositories](https://hacs.xyz/docs/faq/custom_repositories/) and use this URL: `https://github.com/oischinger/ha_vicare`
3. Search for and install the "ViCare" integration.
4. Configure the `vicare` integration.
5. Restart Home Assistant.

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

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for how to set up a development environment and contribute.

## Links/Credits:

- [Original feature request in HA community](https://community.home-assistant.io/t/viessmann-component/77873)
- [PyViCare](https://github.com/somm15/PyViCare) Python API for accessing the ViCare API used by this project
