import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.helpers.selector import (
    selector
)

from typing import (
    Final, 
    Optional, 
    Dict, 
    Any, 
    Mapping 
)

from asyncio import gather

from homeassistant.config_entries import (
    ConfigType, 
    ConfigEntry, 
    ConfigFlow, 
    OptionsFlow, 
    SOURCE_IMPORT
)

from homeassistant.core import (
    callback
)

from homeassistant.const import ( 
    CONF_API_KEY, 
    CONF_NAME
)

from .const import (
    DOMAIN,
    FLOW_VERSION,
    CONF_API_SECRET,
    CONF_DOMAIN,
    CONF_BALANCES,
    CONF_EXCHANGES,
    CONF_NATIVE_CURRENCY,
    CONF_MINING,
    DEFAULT_NAME,
    DEFAULT_DOMAIN,
    DEFAULT_BALANCES,
    DEFAULT_EXCHANGES,
    DEFAULT_CURRENCY
)

class BinancePoolConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION: Final[int] = FLOW_VERSION
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.save_data = {}
        self.api_data = False
        self.coins = []    
        self.asstets = []
    
    def _check_entry_exists(self, name: str):
        current_entries = self._async_current_entries()

        for config_entry in current_entries:
            if config_entry.data.get(CONF_NAME) == name:
                return True

        return False  
    
    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        errors = ()
        
        if user_input:
            try:
                name = user_input[CONF_NAME]
            except (TypeError, ValueError, LookupError):
                errors[CONF_NAME] = "invalid_credentials"
            
            else:
                await self.async_set_unique_id(name)
                self._abort_if_unique_id_configured()
                
                api_key = user_input[CONF_API_KEY]
                api_secret = user_input[CONF_API_SECRET]
                tld = user_input[CONF_DOMAIN]

                from .client import BinancePoolClient, BinanceAPIException, BinanceRequestException
                client = BinancePoolClient(api_key, api_secret, tld=tld)
                                    
                try: 
                    tasks = [
                        client.async_get_capital_balances(),
                        client.get_all_tickers()
                    ]

                    res = await gather(*tasks, return_exceptions=True)
                    for r in res:
                        if isinstance(r, Exception):
                            await client.close_connection()
                            raise r
                        
                except (BinanceAPIException, BinanceRequestException): 
                    errors['base'] = 'api_error'

                else:
                    coins, tickers = res   
            
                    self.coins = [ x['coin'] for x in list(coins) ]
                    self.coins.sort()
                    
                    self.assets = [ x['symbol'] for x in list(tickers) ]
                    self.assets.sort()
                    
                finally:
                    await client.close_connection()
                
            if not errors:
                self.save_data.update({
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_API_KEY: user_input[CONF_API_KEY],
                    CONF_API_SECRET: user_input[CONF_API_SECRET],
                    CONF_DOMAIN: user_input[CONF_DOMAIN],
                    CONF_BALANCES: DEFAULT_BALANCES,
                    CONF_EXCHANGES: DEFAULT_EXCHANGES,
                    CONF_NATIVE_CURRENCY: DEFAULT_CURRENCY,
                    CONF_MINING: []
                })                
                
                return self.async_show_form(
                    step_id = 'options',
                    data_schema = vol.Schema({
                        vol.Optional(CONF_BALANCES, default=self.save_data.get(CONF_BALANCES, DEFAULT_BALANCES)): selector({ 
                            'select': {
                                'options': self.coins,
                                'multiple': True,
                                'mode': 'dropdown'
                            }
                        }),
                        vol.Optional(CONF_EXCHANGES, default=self.save_data.get(CONF_EXCHANGES, DEFAULT_EXCHANGES)): selector({ 
                            'select': {
                                'options': self.assets,
                                'multiple': True,
                                'mode': 'dropdown'
                            }            
                        }),
                        vol.Optional(CONF_NATIVE_CURRENCY, default=self.save_data.get(CONF_NATIVE_CURRENCY, DEFAULT_CURRENCY)): selector({ 
                            'select': {
                                'options': self.coins,
                                'multiple': True,
                                'mode': 'dropdown'
                            }            
                        }),
                        vol.Optional(CONF_MINING, default=', '.join(self.save_data.get(CONF_MINING, []))): cv.string
                    }),
                    errors = errors,
                )   
    
        else:
            user_input = {}
            
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Required(CONF_DOMAIN, default=DEFAULT_DOMAIN): vol.In({'com': 'binance.com', 'us': 'binance.us'}),        
                vol.Required(CONF_API_KEY): cv.string,
                vol.Required(CONF_API_SECRET): cv.string    
            }),
            errors=errors
        )
                
    async def async_step_options(self, user_input: Optional[ConfigType] = None) -> Dict[str, Any]:
        errors = {}

        if user_input:    
            import re
            
            self.save_data.update({
                CONF_BALANCES: user_input.get(CONF_BALANCES, DEFAULT_BALANCES),
                CONF_EXCHANGES: user_input.get(CONF_EXCHANGES, DEFAULT_EXCHANGES),
                CONF_NATIVE_CURRENCY: user_input.get(CONF_NATIVE_CURRENCY, DEFAULT_CURRENCY),
                CONF_MINING: re.split(r'[\s\,]+', user_input.get(CONF_MINING, []))
            })
                
            return self._save_config(self.save_data)
    
        else:
            user_input = {}
            
        return self.async_show_form(
            step_id = 'options',
            data_schema = vol.Schema({
                vol.Optional(CONF_BALANCES, default=self.save_data.get(CONF_BALANCES, DEFAULT_BALANCES)): selector({ 
                    'select': {
                        'options': self.coins,
                        'multiple': True,
                        'mode': 'dropdown'
                    }
                }),
                vol.Optional(CONF_EXCHANGES, default=self.save_data.get(CONF_EXCHANGES, DEFAULT_EXCHANGES)): selector({ 
                    'select': {
                        'options': self.assets,
                        'multiple': True,
                        'mode': 'dropdown'
                    }            
                }),
                vol.Optional(CONF_NATIVE_CURRENCY, default=self.save_data.get(CONF_NATIVE_CURRENCY, DEFAULT_CURRENCY)): selector({ 
                    'select': {
                        'options': self.coins,
                        'multiple': True,
                        'mode': 'dropdown'
                    }            
                }),
                vol.Optional(CONF_MINING, default=', '.join(self.save_data.get(CONF_MINING, []))): cv.string
            }),
            errors = errors,
        )  
                
    async def async_step_import(self, user_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not user_input:
            return self.async_abort(reason="empty_config")
        
        if not ( user_input[CONF_API_KEY] and user_input[CONF_API_SECRET]):
            return self.async_abort(reason="empty auth data")
        
        if not user_input[CONF_NAME]:
            user_input[CONF_NAME] = DEFAULT_NAME        
            
        if not user_input[CONF_DOMAIN]:
            user_input[CONF_DOMAIN] = DEFAULT_DOMAIN            
            
        if not user_input[CONF_BALANCES]:
            user_input[CONF_BALANCES] = DEFAULT_BALANCES
            
        if not user_input[CONF_EXCHANGES]:
            user_input[CONF_EXCHANGES] = DEFAULT_EXCHANGES            
            
        if not user_input[CONF_NATIVE_CURRENCY]:
            user_input[CONF_NATIVE_CURRENCY] = DEFAULT_CURRENCY            
                         
        await self.async_set_unique_id(user_input[CONF_NAME])
        self._abort_if_unique_id_configured()
        
        return self._save_config(user_input)


    def _save_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        if self._check_entry_exists(config[CONF_NAME]):
            return self.async_abort(reason="already_exists")


        return self.async_create_entry(title=config[CONF_NAME], data=config)
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return BinancePoolOptionsFlow(config_entry)    
    
    
class BinancePoolOptionsFlow(OptionsFlow):

    def __init__(self, config_entry: ConfigEntry) -> None:
        from .schemas import CONFIG_ENTRY_SCHEMA

        self._config_entry = config_entry
        self._filter_statuses: Optional[Mapping[str, bool]] = None
        self._base_config: Mapping[str, Any] = CONFIG_ENTRY_SCHEMA({**config_entry.data, **config_entry.options})    

        self.save_data: ConfigType = {**self._config_entry.data}
        self.api_data = False
        self.coins = []
        self.assets = []
        
        
    async def async_fetch_api_data(self, user_input: Optional[ConfigType] = None):
        if not self.api_data:
        
            from .client import BinancePoolClient
                            
            client = BinancePoolClient(user_input[CONF_API_KEY], user_input[CONF_API_SECRET], tld=user_input[CONF_DOMAIN])
     
            tasks = [
                client.async_get_capital_balances(),
                client.get_all_tickers()
            ]
                
            res = await gather(*tasks, return_exceptions=True)
            for r in res:
                if isinstance(r, Exception):
                    await client.close_connection()
                    raise r
                     
            coins, tickers = res   
            
            self.coins = [ x['coin'] for x in coins ]
            self.coins.sort()
            
            self.assets = [ x['symbol'] for x in tickers ]
            self.assets.sort()
            
            self.api_data = True


    async def async_step_init(self, user_input: Optional[ConfigType] = None) -> Dict[str, Any]:
        config_entry = self._config_entry
        if config_entry.source == SOURCE_IMPORT:
            return self.async_abort(reason="yaml_not_supported")

        errors = {}

        if user_input:    
            try:
                await self.async_fetch_api_data(user_input)
            except :
                errors['base'] = 'api_error' 
            else:
                self.save_data.update({
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_API_KEY: user_input[CONF_API_KEY],
                    CONF_API_SECRET: user_input[CONF_API_SECRET],
                    CONF_DOMAIN: user_input[CONF_DOMAIN]
                })
    
                return self.async_show_form(
                    step_id = "options",
                    data_schema = vol.Schema({
                        vol.Optional(CONF_BALANCES, default=self.save_data.get(CONF_BALANCES, DEFAULT_BALANCES)): selector({ 
                            'select': {
                                'options': self.coins,
                                'multiple': True,
                                'mode': 'dropdown'
                            }
                        }),
                        vol.Optional(CONF_EXCHANGES, default=self.save_data.get(CONF_EXCHANGES, DEFAULT_EXCHANGES)): selector({ 
                            'select': {
                                'options': self.assets,
                                'multiple': True,
                                'mode': 'dropdown'
                            }            
                        }),
                        vol.Optional(CONF_NATIVE_CURRENCY, default=self.save_data.get(CONF_NATIVE_CURRENCY, DEFAULT_CURRENCY)): selector({ 
                            'select': {
                                'options': self.coins,
                                'multiple': True,
                                'mode': 'dropdown'
                            }            
                        }),
                        vol.Optional(CONF_MINING, default=', '.join(self.save_data.get(CONF_MINING, []))): cv.string
                    }),
                    errors=errors
                )
    
        else:
            user_input = {}
            
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_NAME, default=self.save_data.get(CONF_NAME, DEFAULT_NAME)): cv.string,
                vol.Required(CONF_DOMAIN, default=self.save_data.get(CONF_DOMAIN, DEFAULT_DOMAIN)): vol.In({'com': 'binance.com', 'us': 'binance.us'}),        
                vol.Required(CONF_API_KEY, default=self.save_data.get(CONF_API_KEY, '')): cv.string,
                vol.Required(CONF_API_SECRET, ''): cv.string    
            }),
            errors=errors,
        )

    async def async_step_options(self, user_input: Optional[ConfigType] = None) -> Dict[str, Any]:
        config_entry = self._config_entry
        if config_entry.source == SOURCE_IMPORT:
            return self.async_abort(reason="yaml_not_supported")
        
        errors = {}

        if user_input:    
            import re
            
            self.save_data.update({
                CONF_BALANCES: user_input.get(CONF_BALANCES, DEFAULT_BALANCES),
                CONF_EXCHANGES: user_input.get(CONF_EXCHANGES, DEFAULT_EXCHANGES),
                CONF_NATIVE_CURRENCY: user_input.get(CONF_NATIVE_CURRENCY, DEFAULT_CURRENCY),
                CONF_MINING: re.split(r'[\s\,]+', user_input.get(CONF_MINING, []))
            })
            
            self.hass.config_entries.async_update_entry(config_entry, unique_id=self.save_data[CONF_NAME], data=self.save_data)
            return self.async_create_entry(title='', data=self.save_data)
    
        else:
            user_input = {}
            
        return self.async_show_form(
            step_id = 'options',
            data_schema = vol.Schema({
                vol.Optional(CONF_BALANCES, default=self.save_data.get(CONF_BALANCES, DEFAULT_BALANCES)): selector({ 
                    'select': {
                        'options': self.coins,
                        'multiple': True,
                        'mode': 'dropdown'
                    }
                }),
                vol.Optional(CONF_EXCHANGES, default=self.save_data.get(CONF_EXCHANGES, DEFAULT_EXCHANGES)): selector({ 
                    'select': {
                        'options': self.assets,
                        'multiple': True,
                        'mode': 'dropdown'
                    }            
                }),
                vol.Optional(CONF_NATIVE_CURRENCY, default=self.save_data.get(CONF_NATIVE_CURRENCY, DEFAULT_CURRENCY)): selector({ 
                    'select': {
                        'options': self.coins,
                        'multiple': True,
                        'mode': 'dropdown'
                    }            
                }),
                vol.Optional(CONF_MINING, default=', '.join(self.save_data.get(CONF_MINING, []))): cv.string
            }),
            errors = errors,
        )        
    