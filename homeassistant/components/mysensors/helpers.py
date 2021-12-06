"""Helper functions for mysensors package."""
import logging
from collections import defaultdict
from enum import IntEnum
from typing import Callable
from typing import DefaultDict
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Union

import voluptuous as vol
from mysensors import BaseAsyncGateway
from mysensors import Message
from mysensors.sensor import ChildSensor

import homeassistant.helpers.config_validation as cv
from .const import ATTR_DEVICES
from .const import ATTR_GATEWAY_ID
from .const import DevId
from .const import DOMAIN
from .const import FLAT_PLATFORM_TYPES
from .const import GatewayId
from .const import MYSENSORS_DISCOVERY
from .const import MYSENSORS_ON_UNLOAD
from .const import SensorType
from .const import TYPE_TO_PLATFORMS
from .const import ValueType
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.util.decorator import Registry

_LOGGER = logging.getLogger(__name__)
SCHEMAS = Registry()


async def on_unload(hass: HomeAssistantType, entry: Union[ConfigEntry,
                                                          GatewayId],
                    fnct: Callable) -> None:
    """Register a callback to be called when entry is unloaded.

    This function is used by platforms to cleanup after themselves.
    """
    if isinstance(entry, GatewayId):
        uniqueid = entry
    else:
        uniqueid = entry.entry_id
    key = MYSENSORS_ON_UNLOAD.format(uniqueid)
    if key not in hass.data[DOMAIN]:
        hass.data[DOMAIN][key] = []
    hass.data[DOMAIN][key].append(fnct)


@callback
def discover_mysensors_platform(hass: HomeAssistant, gateway_id: GatewayId,
                                platform: str,
                                new_devices: List[DevId]) -> None:
    """Discover a MySensors platform."""
    _LOGGER.debug("Discovering platform %s with devIds: %s", platform,
                  new_devices)
    async_dispatcher_send(
        hass,
        MYSENSORS_DISCOVERY.format(gateway_id, platform),
        {
            ATTR_DEVICES: new_devices,
            CONF_NAME: DOMAIN,
            ATTR_GATEWAY_ID: gateway_id,
        },
    )


def default_schema(gateway: BaseAsyncGateway, child: ChildSensor,
                   value_type_name: ValueType) -> vol.Schema:
    """Return a default validation schema for value types."""
    schema = {value_type_name: cv.string}
    return get_child_schema(gateway, child, value_type_name, schema)


@SCHEMAS.register(("light", "V_DIMMER"))
def light_dimmer_schema(gateway: BaseAsyncGateway, child: ChildSensor,
                        value_type_name: ValueType) -> vol.Schema:
    """Return a validation schema for V_DIMMER."""
    schema = {"V_DIMMER": cv.string, "V_LIGHT": cv.string}
    return get_child_schema(gateway, child, value_type_name, schema)


@SCHEMAS.register(("light", "V_PERCENTAGE"))
def light_percentage_schema(gateway: BaseAsyncGateway, child: ChildSensor,
                            value_type_name: ValueType) -> vol.Schema:
    """Return a validation schema for V_PERCENTAGE."""
    schema = {"V_PERCENTAGE": cv.string, "V_STATUS": cv.string}
    return get_child_schema(gateway, child, value_type_name, schema)


@SCHEMAS.register(("light", "V_RGB"))
def light_rgb_schema(gateway: BaseAsyncGateway, child: ChildSensor,
                     value_type_name: ValueType) -> vol.Schema:
    """Return a validation schema for V_RGB."""
    schema = {"V_RGB": cv.string, "V_STATUS": cv.string}
    return get_child_schema(gateway, child, value_type_name, schema)


@SCHEMAS.register(("light", "V_RGBW"))
def light_rgbw_schema(gateway: BaseAsyncGateway, child: ChildSensor,
                      value_type_name: ValueType) -> vol.Schema:
    """Return a validation schema for V_RGBW."""
    schema = {"V_RGBW": cv.string, "V_STATUS": cv.string}
    return get_child_schema(gateway, child, value_type_name, schema)


@SCHEMAS.register(("switch", "V_IR_SEND"))
def switch_ir_send_schema(gateway: BaseAsyncGateway, child: ChildSensor,
                          value_type_name: ValueType) -> vol.Schema:
    """Return a validation schema for V_IR_SEND."""
    schema = {"V_IR_SEND": cv.string, "V_LIGHT": cv.string}
    return get_child_schema(gateway, child, value_type_name, schema)


def get_child_schema(gateway: BaseAsyncGateway, child: ChildSensor,
                     value_type_name: ValueType, schema) -> vol.Schema:
    """Return a child schema."""
    set_req = gateway.const.SetReq
    child_schema = child.get_schema(gateway.protocol_version)
    schema = child_schema.extend(
        {
            vol.Required(set_req[name].value,
                         msg=invalid_msg(gateway, child, name)):
            child_schema.schema.get(set_req[name].value, valid)
            for name, valid in schema.items()
        },
        extra=vol.ALLOW_EXTRA,
    )
    return schema


def invalid_msg(gateway: BaseAsyncGateway, child: ChildSensor,
                value_type_name: ValueType):
    """Return a message for an invalid child during schema validation."""
    pres = gateway.const.Presentation
    set_req = gateway.const.SetReq
    return (
        f"{pres(child.type).name} requires value_type {set_req[value_type_name].name}"
    )


def validate_set_msg(gateway_id: GatewayId,
                     msg: Message) -> Dict[str, List[DevId]]:
    """Validate a set message."""
    if not validate_node(msg.gateway, msg.node_id):
        return {}
    child = msg.gateway.sensors[msg.node_id].children[msg.child_id]
    return validate_child(gateway_id, msg.gateway, msg.node_id, child,
                          msg.sub_type)


def validate_node(gateway: BaseAsyncGateway, node_id: int) -> bool:
    """Validate a node."""
    if gateway.sensors[node_id].sketch_name is None:
        _LOGGER.debug("Node %s is missing sketch name", node_id)
        return False
    return True


def validate_child(
    gateway_id: GatewayId,
    gateway: BaseAsyncGateway,
    node_id: int,
    child: ChildSensor,
    value_type: Optional[int] = None,
) -> DefaultDict[str, List[DevId]]:
    """Validate a child. Returns a dict mapping hass platform names to list of DevId."""
    validated: DefaultDict[str, List[DevId]] = defaultdict(list)
    pres: IntEnum = gateway.const.Presentation
    set_req: IntEnum = gateway.const.SetReq
    child_type_name: Optional[SensorType] = next(
        (member.name for member in pres if member.value == child.type), None)
    value_types: Set[int] = {value_type} if value_type else {*child.values}
    value_type_names: Set[ValueType] = {
        member.name
        for member in set_req if member.value in value_types
    }
    platforms: List[str] = TYPE_TO_PLATFORMS.get(child_type_name, [])
    if not platforms:
        _LOGGER.warning("Child type %s is not supported", child.type)
        return validated

    for platform in platforms:
        platform_v_names: Set[ValueType] = FLAT_PLATFORM_TYPES[platform,
                                                               child_type_name]
        v_names: Set[ValueType] = platform_v_names & value_type_names
        if not v_names:
            child_value_names: Set[ValueType] = {
                member.name
                for member in set_req if member.value in child.values
            }
            v_names: Set[ValueType] = platform_v_names & child_value_names

        for v_name in v_names:
            child_schema_gen = SCHEMAS.get((platform, v_name), default_schema)
            child_schema = child_schema_gen(gateway, child, v_name)
            try:
                child_schema(child.values)
            except vol.Invalid as exc:
                _LOGGER.warning(
                    "Invalid %s on node %s, %s platform: %s",
                    child,
                    node_id,
                    platform,
                    exc,
                )
                continue
            dev_id: DevId = (
                gateway_id,
                node_id,
                child.id,
                set_req[v_name].value,
            )
            validated[platform].append(dev_id)

    return validated
