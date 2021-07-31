"""Constants for the ViCare integration."""
import enum

DOMAIN = "vicare"

CONF_CIRCUIT = "circuit"
CONF_HEATING_TYPE = "heating_type"
DEFAULT_SCAN_INTERVAL = 60
DEFAULT_HEATING_TYPE = "generic"


class HeatingType(enum.Enum):
    """Possible options for heating type."""

    generic = "generic"
    gas = "gas"
    heatpump = "heatpump"
    fuelcell = "fuelcell"
