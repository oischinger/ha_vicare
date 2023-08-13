"""Viessmann ViCare sensor device."""
from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
import logging

from PyViCare.PyViCareDevice import Device
from PyViCare.PyViCareUtils import (
    PyViCareInternalServerError,
    PyViCareInvalidDataError,
    PyViCareNotSupportedFeatureError,
    PyViCareRateLimitError,
)
import requests

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ViCareRequiredKeysMixin
from .const import (
    DOMAIN,
    VICARE_CUBIC_METER,
    VICARE_DEVICE_CONFIG,
    VICARE_KWH,
    VICARE_NAME,
    VICARE_UNIT_TO_UNIT_OF_MEASUREMENT,
)
from .helpers import (
    get_burners,
    get_circuits,
    get_compressors,
    get_device_name,
    get_unique_device_id,
    get_unique_id,
)

_LOGGER = logging.getLogger(__name__)

VICARE_UNIT_TO_DEVICE_CLASS = {
    VICARE_KWH: SensorDeviceClass.ENERGY,
    VICARE_CUBIC_METER: SensorDeviceClass.GAS,
}


@dataclass
class ViCareSensorEntityDescription(SensorEntityDescription, ViCareRequiredKeysMixin):
    """Describes ViCare sensor entity."""

    unit_getter: Callable[[Device], str | None] | None = None


GLOBAL_SENSORS: tuple[ViCareSensorEntityDescription, ...] = (
    ViCareSensorEntityDescription(
        key="outside_temperature",
        name="Outside Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_getter=lambda api: api.getOutsideTemperature(),
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ViCareSensorEntityDescription(
        key="return_temperature",
        name="Return Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_getter=lambda api: api.getReturnTemperature(),
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ViCareSensorEntityDescription(
        key="boiler_temperature",
        name="Boiler Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_getter=lambda api: api.getBoilerTemperature(),
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ViCareSensorEntityDescription(
        key="boiler_supply_temperature",
        name="Boiler Supply Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_getter=lambda api: api.getBoilerCommonSupplyTemperature(),
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ViCareSensorEntityDescription(
        key="primary_circuit_supply_temperature",
        name="Primary Circuit Supply Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_getter=lambda api: api.getSupplyTemperaturePrimaryCircuit(),
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ViCareSensorEntityDescription(
        key="primary_circuit_return_temperature",
        name="Primary Circuit  Return Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_getter=lambda api: api.getReturnTemperaturePrimaryCircuit(),
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ViCareSensorEntityDescription(
        key="secondary_circuit_supply_temperature",
        name="Secondary Circuit Supply Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_getter=lambda api: api.getSupplyTemperatureSecondaryCircuit(),
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ViCareSensorEntityDescription(
        key="secondary_circuit_return_temperature",
        name="Secondary Circuit Return Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_getter=lambda api: api.getReturnTemperatureSecondaryCircuit(),
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ViCareSensorEntityDescription(
        key="hotwater_out_temperature",
        name="Hot Water Out Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_getter=lambda api: api.getDomesticHotWaterOutletTemperature(),
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ViCareSensorEntityDescription(
        key="hotwater_max_temperature",
        name="Hot Water Max Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_getter=lambda api: api.getDomesticHotWaterMaxTemperature(),
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ViCareSensorEntityDescription(
        key="hotwater_min_temperature",
        name="Hot Water Min Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_getter=lambda api: api.getDomesticHotWaterMinTemperature(),
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ViCareSensorEntityDescription(
        key="hotwater_gas_consumption_today",
        name="Hot water gas consumption today",
        value_getter=lambda api: api.getGasConsumptionDomesticHotWaterToday(),
        unit_getter=lambda api: api.getGasConsumptionDomesticHotWaterUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="hotwater_gas_consumption_heating_this_week",
        name="Hot water gas consumption this week",
        value_getter=lambda api: api.getGasConsumptionDomesticHotWaterThisWeek(),
        unit_getter=lambda api: api.getGasConsumptionDomesticHotWaterUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="hotwater_gas_consumption_heating_this_month",
        name="Hot water gas consumption this month",
        value_getter=lambda api: api.getGasConsumptionDomesticHotWaterThisMonth(),
        unit_getter=lambda api: api.getGasConsumptionDomesticHotWaterUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="hotwater_gas_consumption_heating_this_year",
        name="Hot water gas consumption this year",
        value_getter=lambda api: api.getGasConsumptionDomesticHotWaterThisYear(),
        unit_getter=lambda api: api.getGasConsumptionDomesticHotWaterUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="gas_consumption_heating_today",
        name="Heating gas consumption today",
        value_getter=lambda api: api.getGasConsumptionHeatingToday(),
        unit_getter=lambda api: api.getGasConsumptionHeatingUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="gas_consumption_heating_this_week",
        name="Heating gas consumption this week",
        value_getter=lambda api: api.getGasConsumptionHeatingThisWeek(),
        unit_getter=lambda api: api.getGasConsumptionHeatingUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="gas_consumption_heating_this_month",
        name="Heating gas consumption this month",
        value_getter=lambda api: api.getGasConsumptionHeatingThisMonth(),
        unit_getter=lambda api: api.getGasConsumptionHeatingUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="gas_consumption_heating_this_year",
        name="Heating gas consumption this year",
        value_getter=lambda api: api.getGasConsumptionHeatingThisYear(),
        unit_getter=lambda api: api.getGasConsumptionHeatingUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="gas_summary_consumption_heating_currentday",
        name="Heating gas consumption current day",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        value_getter=lambda api: api.getGasSummaryConsumptionHeatingCurrentDay(),
        unit_getter=lambda api: api.getGasSummaryConsumptionHeatingUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="gas_summary_consumption_heating_currentmonth",
        name="Heating gas consumption current month",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        value_getter=lambda api: api.getGasSummaryConsumptionHeatingCurrentMonth(),
        unit_getter=lambda api: api.getGasSummaryConsumptionHeatingUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="gas_summary_consumption_heating_currentyear",
        name="Heating gas consumption current year",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        value_getter=lambda api: api.getGasSummaryConsumptionHeatingCurrentYear(),
        unit_getter=lambda api: api.getGasSummaryConsumptionHeatingUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="hotwater_gas_summary_consumption_heating_currentday",
        name="Hot water gas consumption current day",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        value_getter=lambda api: api.getGasSummaryConsumptionDomesticHotWaterCurrentDay(),
        unit_getter=lambda api: api.getGasSummaryConsumptionDomesticHotWaterUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="hotwater_gas_summary_consumption_heating_currentmonth",
        name="Hot water gas consumption current month",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        value_getter=lambda api: api.getGasSummaryConsumptionDomesticHotWaterCurrentMonth(),
        unit_getter=lambda api: api.getGasSummaryConsumptionDomesticHotWaterUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="hotwater_gas_summary_consumption_heating_currentyear",
        name="Hot water gas consumption current year",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        value_getter=lambda api: api.getGasSummaryConsumptionDomesticHotWaterCurrentYear(),
        unit_getter=lambda api: api.getGasSummaryConsumptionDomesticHotWaterUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="hotwater_gas_summary_consumption_heating_lastsevendays",
        name="Hot water gas consumption last seven days",
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        value_getter=lambda api: api.getGasSummaryConsumptionDomesticHotWaterLastSevenDays(),
        unit_getter=lambda api: api.getGasSummaryConsumptionDomesticHotWaterUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="energy_summary_consumption_heating_currentday",
        name="Energy consumption of heating current day",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerSummaryConsumptionHeatingCurrentDay(),
        unit_getter=lambda api: api.getPowerSummaryConsumptionHeatingUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="energy_summary_consumption_heating_currentmonth",
        name="Energy consumption of heating current month",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerSummaryConsumptionHeatingCurrentMonth(),
        unit_getter=lambda api: api.getPowerSummaryConsumptionHeatingUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="energy_summary_consumption_heating_currentyear",
        name="Energy consumption of heating current year",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerSummaryConsumptionHeatingCurrentYear(),
        unit_getter=lambda api: api.getPowerSummaryConsumptionHeatingUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="energy_summary_consumption_heating_lastsevendays",
        name="Energy consumption of heating last seven days",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerSummaryConsumptionHeatingLastSevenDays(),
        unit_getter=lambda api: api.getPowerSummaryConsumptionHeatingUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="energy_dhw_summary_consumption_heating_currentday",
        name="Energy consumption of hot water heating current day",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerSummaryConsumptionDomesticHotWaterCurrentDay(),
        unit_getter=lambda api: api.getPowerSummaryConsumptionDomesticHotWaterUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="energy_dhw_summary_consumption_heating_currentmonth",
        name="Energy consumption of hot water heating current month",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerSummaryConsumptionDomesticHotWaterCurrentMonth(),
        unit_getter=lambda api: api.getPowerSummaryConsumptionDomesticHotWaterUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="energy_dhw_summary_consumption_heating_currentyear",
        name="Energy consumption of hot water heating current year",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerSummaryConsumptionDomesticHotWaterCurrentYear(),
        unit_getter=lambda api: api.getPowerSummaryConsumptionDomesticHotWaterUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="energy_summary_dhw_consumption_heating_lastsevendays",
        name="Energy consumption of hot water heating last seven days",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerSummaryConsumptionDomesticHotWaterLastSevenDays(),
        unit_getter=lambda api: api.getPowerSummaryConsumptionDomesticHotWaterUnit(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="power_production_current",
        name="Power production current",
        native_unit_of_measurement=UnitOfPower.WATT,
        value_getter=lambda api: api.getPowerProductionCurrent(),
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ViCareSensorEntityDescription(
        key="power_production_today",
        name="Energy production today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerProductionToday(),
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="power_production_this_week",
        name="Energy production this week",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerProductionThisWeek(),
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="power_production_this_month",
        name="Energy production this month",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerProductionThisMonth(),
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="power_production_this_year",
        name="Energy production this year",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerProductionThisYear(),
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="solar storage temperature",
        name="Solar Storage Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_getter=lambda api: api.getSolarStorageTemperature(),
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ViCareSensorEntityDescription(
        key="collector temperature",
        name="Solar Collector Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_getter=lambda api: api.getSolarCollectorTemperature(),
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ViCareSensorEntityDescription(
        key="solar power production today",
        name="Solar energy production today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getSolarPowerProductionToday(),
        unit_getter=lambda api: api.getSolarPowerProductionUnit(),
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="solar power production this week",
        name="Solar energy production this week",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getSolarPowerProductionThisWeek(),
        unit_getter=lambda api: api.getSolarPowerProductionUnit(),
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="solar power production this month",
        name="Solar energy production this month",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getSolarPowerProductionThisMonth(),
        unit_getter=lambda api: api.getSolarPowerProductionUnit(),
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="solar power production this year",
        name="Solar energy production this year",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getSolarPowerProductionThisYear(),
        unit_getter=lambda api: api.getSolarPowerProductionUnit(),
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="power consumption today",
        name="Energy consumption today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerConsumptionToday(),
        unit_getter=lambda api: api.getPowerConsumptionUnit(),
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="power consumption this week",
        name="Power consumption this week",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerConsumptionThisWeek(),
        unit_getter=lambda api: api.getPowerConsumptionUnit(),
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="power consumption this month",
        name="Energy consumption this month",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerConsumptionThisMonth(),
        unit_getter=lambda api: api.getPowerConsumptionUnit(),
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="power consumption this year",
        name="Energy consumption this year",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerConsumptionThisYear(),
        unit_getter=lambda api: api.getPowerConsumptionUnit(),
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="power consumption dhw today",
        name="Energy consumption of hot water heating today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_getter=lambda api: api.getPowerConsumptionDomesticHotWaterToday(),
        unit_getter=lambda api: api.getPowerConsumptionUnit(),
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="buffer main temperature",
        name="Buffer Main Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_getter=lambda api: api.getBufferMainTemperature(),
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ViCareSensorEntityDescription(
        key="buffer top temperature",
        name="Buffer Top Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_getter=lambda api: api.getBufferTopTemperature(),
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ViCareSensorEntityDescription(
        key="room_temperature",
        name="Room Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_getter=lambda api: api.getTemperature(),
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ViCareSensorEntityDescription(
        key="room_humidity",
        name="Room Humidity",
        icon="mdi:percent",
        native_unit_of_measurement=PERCENTAGE,
        value_getter=lambda api: api.getHumidity(),
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

CIRCUIT_SENSORS: tuple[ViCareSensorEntityDescription, ...] = (
    ViCareSensorEntityDescription(
        key="supply_temperature",
        name="Supply Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_getter=lambda api: api.getSupplyTemperature(),
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

BURNER_SENSORS: tuple[ViCareSensorEntityDescription, ...] = (
    ViCareSensorEntityDescription(
        key="burner_starts",
        name="Burner Starts",
        icon="mdi:counter",
        value_getter=lambda api: api.getStarts(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="burner_hours",
        name="Burner Hours",
        icon="mdi:counter",
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_getter=lambda api: api.getHours(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="burner_modulation",
        name="Burner Modulation",
        icon="mdi:percent",
        native_unit_of_measurement=PERCENTAGE,
        value_getter=lambda api: api.getModulation(),
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

COMPRESSOR_SENSORS: tuple[ViCareSensorEntityDescription, ...] = (
    ViCareSensorEntityDescription(
        key="compressor_starts",
        name="Compressor Starts",
        icon="mdi:counter",
        value_getter=lambda api: api.getStarts(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="compressor_hours",
        name="Compressor Hours",
        icon="mdi:counter",
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_getter=lambda api: api.getHours(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="compressor_hours_loadclass1",
        name="Compressor Hours Load Class 1",
        icon="mdi:counter",
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_getter=lambda api: api.getHoursLoadClass1(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="compressor_hours_loadclass2",
        name="Compressor Hours Load Class 2",
        icon="mdi:counter",
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_getter=lambda api: api.getHoursLoadClass2(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="compressor_hours_loadclass3",
        name="Compressor Hours Load Class 3",
        icon="mdi:counter",
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_getter=lambda api: api.getHoursLoadClass3(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="compressor_hours_loadclass4",
        name="Compressor Hours Load Class 4",
        icon="mdi:counter",
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_getter=lambda api: api.getHoursLoadClass4(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ViCareSensorEntityDescription(
        key="compressor_hours_loadclass5",
        name="Compressor Hours Load Class 5",
        icon="mdi:counter",
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_getter=lambda api: api.getHoursLoadClass5(),
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
)


def _build_entity(name, vicare_api, device_config, sensor):
    """Create a ViCare sensor entity."""
    try:
        sensor.value_getter(vicare_api)
        _LOGGER.debug("Found entity %s", name)
    except PyViCareInternalServerError as server_error:
        _LOGGER.info(
            "Server error ( %s): Not creating entity %s", server_error.message, name
        )
        return None
    except PyViCareNotSupportedFeatureError:
        _LOGGER.debug("Feature not supported %s", name)
        return None
    except AttributeError:
        _LOGGER.debug("Attribute Error %s", name)
        return None

    return ViCareSensor(
        name,
        vicare_api,
        device_config,
        sensor,
    )


def _entities_from_descriptions(
    hass, name, entities, sensor_descriptions, iterables, config_entry, device
):
    """Create entities from descriptions and list of burners/circuits."""
    for description in sensor_descriptions:
        for current in iterables:
            suffix = ""
            if len(iterables) > 1:
                suffix = f" {current.id}"
            entity = _build_entity(
                f"{name} {description.name}{suffix}",
                current,
                device,
                description,
            )
            if entity is not None:
                entities.append(entity)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the ViCare sensor devices."""
    entities = await hass.async_add_executor_job(
        create_all_entities, hass, config_entry
    )
    async_add_entities(entities)


def create_all_entities(hass: HomeAssistant, config_entry: ConfigEntry):
    """Create entities for all devices and their circuits, burners or compressors if applicable."""
    name = VICARE_NAME
    entities: list[ViCareSensor] = []

    for device in hass.data[DOMAIN][config_entry.entry_id][VICARE_DEVICE_CONFIG]:
        api = device.asAutoDetectDevice()

        _entities_from_descriptions(
            hass, name, entities, GLOBAL_SENSORS, [api], config_entry, device
        )

        try:
            _entities_from_descriptions(
                hass,
                name,
                entities,
                CIRCUIT_SENSORS,
                get_circuits(api),
                config_entry,
                device,
            )
        except PyViCareNotSupportedFeatureError:
            _LOGGER.info("No circuits found")

        try:
            _entities_from_descriptions(
                hass, name, entities, BURNER_SENSORS, get_burners(api), config_entry, device
            )
        except PyViCareNotSupportedFeatureError:
            _LOGGER.info("No burners found")

        try:
            _entities_from_descriptions(
                hass,
                name,
                entities,
                COMPRESSOR_SENSORS,
                get_compressors(api),
                config_entry,
                device,
            )
        except PyViCareNotSupportedFeatureError:
            _LOGGER.info("No compressors found")

    return entities


class ViCareSensor(SensorEntity):
    """Representation of a ViCare sensor."""

    entity_description: ViCareSensorEntityDescription

    def __init__(
        self, name, api, device_config, description: ViCareSensorEntityDescription
    ) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        self._attr_name = name
        self._api = api
        self._device_config = device_config
        self.update()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this device."""
        return DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    get_unique_device_id(self._device_config),
                )
            },
            name=get_device_name(self._device_config),
            manufacturer="Viessmann",
            model=self._device_config.getModel(),
            configuration_url="https://developer.viessmann.com/",
        )

    @property
    def available(self):
        """Return True if entity is available."""
        return self._state is not None

    @property
    def unique_id(self) -> str:
        """Return unique ID for this device."""
        return get_unique_id(
            self._api, self._device_config, self.entity_description.key
        )

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    def update(self):
        """Update state of sensor."""
        try:
            with suppress(PyViCareNotSupportedFeatureError):
                self._state = self.entity_description.value_getter(self._api)

                if self.entity_description.unit_getter:
                    vicare_unit = self.entity_description.unit_getter(self._api)
                    if vicare_unit is not None:
                        self._attr_device_class = VICARE_UNIT_TO_DEVICE_CLASS.get(
                            vicare_unit
                        )
                        self._attr_native_unit_of_measurement = (
                            VICARE_UNIT_TO_UNIT_OF_MEASUREMENT.get(vicare_unit)
                        )
        except requests.exceptions.ConnectionError:
            _LOGGER.error("Unable to retrieve data from ViCare server")
        except ValueError:
            _LOGGER.error("Unable to decode data from ViCare server")
        except PyViCareRateLimitError as limit_exception:
            _LOGGER.error("Vicare API rate limit exceeded: %s", limit_exception)
        except PyViCareInvalidDataError as invalid_data_exception:
            _LOGGER.error("Invalid data from Vicare server: %s", invalid_data_exception)
