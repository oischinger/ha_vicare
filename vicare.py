# The domain of your component. Equal to the filename of your component.
import logging
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity

import requests
import json

ATTR_JSON_DATA = 'json_data'

def getToken(client_id, client_secret, user, password):
    global vToken
    global URL

    authorizeURL = 'https://iam.viessmann.com/idp/v1/authorize';
    token_url = 'https://iam.viessmann.com/idp/v1/token';
    apiURLBase = 'https://api.viessmann-platform.io';
    callback_uri = "vicare://oauth-callback/everest";

    #Settings to request Autorization Code
    url = authorizeURL + "?client_id=" + client_id + "&scope=openid&redirect_uri=" + callback_uri + "&response_type=code";
    _LOGGER.info("ViCare URL is " + str(url))

    header = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    #Try to get a response, but the requests library does not allow a request URL that does not start with http (ours is: "vicare://oauth-callback/everest")
    codestring = ''
    try:
        response = requests.post(url, headers=header, auth=(user, password))
    except Exception as e:
        _LOGGER.warn("ViCare response is " + str(e.args[0]))
        #capture the error, which contains the code the authorization code and put this in to codestring
        codestring = "{0}".format(str(e.args[0])).encode("utf-8");
        codestring = str(codestring)
        codestring = codestring[codestring.find("?code=")+6:len(codestring)-2]

    #Use autorization code to request access_token
    header = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
    }
    data = {
      'client_id':client_id,
      'code':codestring,
      'redirect_uri':callback_uri,
      'grant_type':'authorization_code',
    }
    _LOGGER.warn("ViCare is" + str(data) + " user: " + user + " password: " + password)
    response = requests.post(token_url, headers=header, data=data, auth=(client_id, client_secret))
    data = response.json()
    _LOGGER.warn("ViCare response is " + str(data))
    vToken = data["access_token"]

    apiURL = apiURLBase + '/general-management/installations?expanded=true&'
    data = GetData(apiURL, vToken, '')
    ID = data["entities"][0]["properties"]["id"] #ID of the installation
    SERIAL = data["entities"][0]["entities"][0]["properties"]["serial"] #Serial of installation
    URL = apiURLBase + '/operational-data/installations/' + str(ID) + '/gateways/' + str(SERIAL) + '/devices/0/features/'

def SetData(ReqURL, Token, feature, action, data):
    #Define Request header
    header = {
     'Authorization':'Bearer ' + Token,
     'Content-Type':'application/json'
     }
    response = requests.post(ReqURL+'heating.circuits.0.'+feature+'/'+action, headers=header, data=json.dumps(data))
    return response

#SubRoutine for requests
def GetData(ReqURL, Token, returnValue):
    #Define Request header
    header = {
     'Authorization':'Bearer ' + Token,
     'Cache-Control': 'no-cache'
     }
    #Get RequestURL with header

    response = requests.get(ReqURL+returnValue, headers=header)
    data = response.json()
    if not returnValue:
        return data
    ret = {}
    if "message" in data and data["message"] == "FEATURE_NOT_FOUND":
        return
    if not any(data["properties"]):
        return
    if "value" in data["properties"]:
        ret['value'] = data["properties"]["value"]["value"]
    if "status" in data["properties"]:
        ret['status'] = data["properties"]["status"]["value"]
    if "active" in data["properties"]:
        ret['active'] = data["properties"]["active"]["value"]
    if "slope" in data["properties"]:
        ret['slope'] = data["properties"]["slope"]["value"]
    if "enabled" in data["properties"]:
        ret['enabled'] = data["properties"]["enabled"]["value"]
    if "entries" in data["properties"]:
        ret['entries'] = data["properties"]["entries"]["value"]
    if "temperature" in data["properties"]:
        ret['temperature'] = data["properties"]["temperature"]["value"]
    if not any(ret):
        return
    #Return response as JSON
    return ret;

def GetVData(feature):
    return GetData(URL, vToken, feature)

def SetVData(feature, action, data):
    return SetData(URL, vToken, feature, action, data);

_LOGGER = logging.getLogger(__name__)

DOMAIN = "vcare"
DEPENDENCIES = []

CONF_USER = 'user'
CONF_PASSWORD = 'password'
CONF_CLIENT_ID = 'client_id'
CONF_CLIENT_SECRET = 'client_secret'

def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the ViCare component."""
    add_devices([ViCareSensor(config, "heating.boiler.sensors.temperature.main", TEMP_CELSIUS, "value"),
                 ViCareSensor(config, "heating.circuits.0.operating.programs.active", "", "value"), # "comfort","eco","external","holiday","normal","reduced", "standby"
                 ViCareSensor(config, "heating.sensors.temperature.outside", TEMP_CELSIUS, "value"),
                 ViCareSensor(config, "heating.burner.current.power", "kW", "value"),
                 ViCareSensor(config, "heating.circuits.0.operating.modes.active", "", "value"), # "standby","dhw","dhwAndHeating","forcedReduced","forcedNormal"
                 ViCareSensor(config, "heating.dhw.sensors.temperature.hotWaterStorage", TEMP_CELSIUS, "value"),
                 ViCareSensor(config, "heating.gas.consumption.dhw", "", "day"),
                 ViCareSensor(config, "heating.gas.consumption.heating", "", "day"),
                 ViCareSensor(config, "heating.burner.statistics", ""),
                 ViCareSensor(config, "heating.burner.modulation", "", None),
                 ViCareSensor(config, "heating.circuits.0.heating.curve", "", "slope"),
                 ViCareSensor(config, "heating.circuits.0.heating.curve", "", "shift"),
                 ViCareSensor(config, "heating.dhw.temperature", TEMP_CELSIUS, "value")])
    return True

class ViCareSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, config, sensorName, unit, keyName=None):
        """Initialize the sensor."""
        self._user = config.get(CONF_USER)
        self._password = config.get(CONF_PASSWORD)
        self._client_id = config.get(CONF_CLIENT_ID)
        self._client_secret = config.get(CONF_CLIENT_SECRET)
        self._state = None
        self._json_data = None
        self._unit = unit
        self._keyName = keyName
        self._device_state_attributes = {}
        self.sensorName = sensorName

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.sensorName

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def json_data(self):
        """Return the json data of the sensor."""
        return self._json_data

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def device_state_attributes(self):
        """Return the state attributes of the generic device."""
        attr = self._device_state_attributes
        attr.update({
            ATTR_JSON_DATA: self._json_data
        })
        return attr

    def refreshToken(self):
        self._api = getToken(self._client_id, self._client_secret, self._user, self._password)

    def update(self):
        try:
            data = GetVData(self.sensorName)
        except Exception as e:
            self.refreshToken()
            data = GetVData(self.sensorName)

        self._json_data = data

        if data is None:
            self._state = None
        else:
            self._state = data[self._keyName]

