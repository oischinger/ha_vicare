
# Development

This custom component repository is unrelated to the [Home Assistant Core](https://github.com/home-assistant/core) repository.

Most of the times it is some commits ahead of the core repository.

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

