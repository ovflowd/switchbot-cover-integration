import asyncio
import logging

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_DOWN_SWITCH,
    CONF_MOVEMENT_TIMEOUT,
    CONF_SENSOR,
    CONF_UP_SWITCH,
    DEFAULT_MOVEMENT_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = {**entry.data, **entry.options}
    async_add_entities(
        [SwitchBotCoverEntity(hass, entry.entry_id, entry.title, data)]
    )


class SwitchBotCoverEntity(CoverEntity):

    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        name: str,
        data: dict,
    ) -> None:
        self._hass = hass
        self._attr_unique_id = entry_id
        self._attr_name = name
        self._up_switch = data[CONF_UP_SWITCH]
        self._down_switch = data[CONF_DOWN_SWITCH]
        self._sensor = data.get(CONF_SENSOR)
        self._timeout = data.get(CONF_MOVEMENT_TIMEOUT, DEFAULT_MOVEMENT_TIMEOUT)
        self._moving = False
        self._lock = asyncio.Lock()
        self._is_closed: bool | None = None
        self._position: int | None = None
        self._unsub_sensor = None

    @property
    def supported_features(self) -> CoverEntityFeature:
        flags = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
        )
        if self._sensor:
            flags |= CoverEntityFeature.SET_POSITION
        return flags

    @property
    def is_closed(self) -> bool | None:
        return self._is_closed

    @property
    def current_cover_position(self) -> int | None:
        return self._position

    @property
    def is_opening(self) -> bool:
        return self._moving and self._last_direction == "up"

    @property
    def is_closing(self) -> bool:
        return self._moving and self._last_direction == "down"

    async def async_added_to_hass(self) -> None:
        self._last_direction: str | None = None
        if self._sensor:
            state = self._hass.states.get(self._sensor)
            if state:
                self._update_from_sensor(state.state)
            self._unsub_sensor = async_track_state_change_event(
                self._hass, [self._sensor], self._sensor_changed
            )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_sensor:
            self._unsub_sensor()

    @callback
    def _sensor_changed(self, event) -> None:
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        self._update_from_sensor(new_state.state)
        self.async_write_ha_state()

    def _update_from_sensor(self, state: str) -> None:
        is_open = state == STATE_ON
        self._is_closed = not is_open
        self._position = 100 if is_open else 0

    async def _toggle_direction(self, direction: str) -> None:
        if self._lock.locked():
            _LOGGER.debug("Movement in progress, ignoring %s command", direction)
            return

        async with self._lock:
            switch = self._up_switch if direction == "up" else self._down_switch
            self._moving = True
            self._last_direction = direction
            self.async_write_ha_state()

            await self._hass.services.async_call(
                "switch", "turn_on", {"entity_id": switch}, blocking=True
            )

            if self._sensor:
                target = STATE_ON if direction == "up" else "off"
                try:
                    await self._wait_for_sensor(target)
                except asyncio.TimeoutError:
                    _LOGGER.debug("Timeout waiting for sensor, assuming complete")
            else:
                await asyncio.sleep(self._timeout)

            self._moving = False
            if not self._sensor:
                self._is_closed = direction == "down"
                self._position = 0 if direction == "down" else 100
            self.async_write_ha_state()

    async def _wait_for_sensor(self, target_state: str) -> None:
        event = asyncio.Event()

        @callback
        def _check(ev):
            new = ev.data.get("new_state")
            if new and new.state == target_state:
                event.set()

        current = self._hass.states.get(self._sensor)
        if current and current.state == target_state:
            return

        unsub = async_track_state_change_event(
            self._hass, [self._sensor], _check
        )
        try:
            await asyncio.wait_for(event.wait(), timeout=self._timeout)
        finally:
            unsub()

    async def async_open_cover(self, **kwargs) -> None:
        await self._toggle_direction("up")

    async def async_close_cover(self, **kwargs) -> None:
        await self._toggle_direction("down")

    async def async_stop_cover(self, **kwargs) -> None:
        if self._moving:
            switch = (
                self._up_switch
                if self._last_direction == "up"
                else self._down_switch
            )
            await self._hass.services.async_call(
                "switch", "turn_on", {"entity_id": switch}, blocking=True
            )
            self._moving = False
            self.async_write_ha_state()

    async def async_set_cover_position(self, **kwargs) -> None:
        position = kwargs.get("position", 0)
        if position > 50:
            await self.async_open_cover()
        else:
            await self.async_close_cover()
