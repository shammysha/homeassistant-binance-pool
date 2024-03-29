import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.const import (
    CONF_API_KEY, 
    CONF_NAME
)

from .const import (
    DOMAIN,
    DEFAULT_NAME,
    DEFAULT_DOMAIN,
    DEFAULT_CURRENCY,
    DEFAULT_BALANCES,
    DEFAULT_EXCHANGES,
    CONF_API_SECRET,
    CONF_BALANCES,
    CONF_EXCHANGES,
    CONF_MINING,
    CONF_DOMAIN,
    CONF_NATIVE_CURRENCY   
)

CONFIG_ENTRY_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_DOMAIN, default=DEFAULT_DOMAIN): vol.In({'com': 'binance.com', 'us': 'binance.us'}),
        vol.Optional(CONF_NATIVE_CURRENCY, default=DEFAULT_CURRENCY): vol.All(
            cv.ensure_list, [cv.string]
        ),
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_API_SECRET): cv.string,
        vol.Optional(CONF_BALANCES, default=DEFAULT_BALANCES): vol.All(
            cv.ensure_list, [cv.string]
        ),
        vol.Optional(CONF_EXCHANGES, default=DEFAULT_EXCHANGES): vol.All(
            cv.ensure_list, [cv.string]
        ),
        vol.Optional(CONF_MINING, default=[]): vol.All(
            cv.ensure_list, [cv.string]
        )
    },
    extra=vol.ALLOW_EXTRA
)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional(DOMAIN): vol.Any(
            vol.Equal({}),
            vol.Equal(CONFIG_ENTRY_SCHEMA),
            vol.All(
               cv.ensure_list,
               [CONFIG_ENTRY_SCHEMA]         
            )
        )
    },
    extra=vol.ALLOW_EXTRA
)

