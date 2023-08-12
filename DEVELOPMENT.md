# Development

This custom component repository is unrelated to the [Home Assistant Core](https://github.com/home-assistant/core) repository.

Most of the times it is some commits ahead of the core repository.

## Development environment

### Install core dependencies:

Make sure your system has an up to date python version (ideally the same as required [here](https://developers.home-assistant.io/docs/development_environment)).

```
sudo apt-get update
sudo apt-get install python3-pip python3-dev python3-venv
```

### Create a venv

In the root directory of this repository create a venv initially:

```
python3 -m venv venv
```

Change to the venv:

```
source venv/bin/activate
```

### Install development and test dependencies

```
python3 -m pip install -r requirements_dev.txt
python3 -m pip install -r requirements_test.txt
```

### Run tests

Just run `pytest`

# Creating a PR

To create a PR to this repository please install this commit hook:

```
python3 -m pip install pre-commit
pre-commit install
```

# HA Core development

Make sure to setup the development environment like as described [here](https://developers.home-assistant.io/docs/development_environment).

# Howto apply patches from this repo to HA Core

Create a patch from a given commit e.g. with `git format-patch HEAD~1` and apply it on the HA Core repo with this command:

`git am -p2 --directory=homeassistant/components path_to_ha_vicare/custom_components/vicare/0001-some.patch`
