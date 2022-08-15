from datetime import (
    timedelta
)

import logging
import copy

from typing import (
    Dict, 
    Final, 
    Mapping, 
    Optional, 
    TYPE_CHECKING, 
    Tuple, 
    Type
)

from asyncio import (
    gather
)

from homeassistant.config_entries import (
    ConfigEntry, 
    SOURCE_IMPORT
)

from homeassistant.const import (
    CONF_API_KEY, 
    CONF_NAME
)

from homeassistant.exceptions import (
    ConfigEntryAuthFailed
)

from homeassistant.helpers.discovery import (
    async_load_platform
)

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity, 
    DataUpdateCoordinator, 
    UpdateFailed
)

from homeassistant.util import (
    Throttle
)

from .schemas import (
    CONFIG_SCHEMA, 
    CONFIG_ENTRY_SCHEMA
)

from .const import (
    DOMAIN,
    CONF_API_SECRET,
    CONF_BALANCES,
    CONF_EXCHANGES,
    CONF_MINING,
    CONF_DOMAIN,
    CONF_NATIVE_CURRENCY,
    MIN_TIME_BETWEEN_UPDATES,
    MIN_TIME_BETWEEN_MINING_UPDATES,
    COORDINATOR_MINING,
    COORDINATOR_WALLET    
)

from .client import (
    BinancePoolClient, 
    BinanceAPIException, 
    BinanceRequestException
)

__version__ = "1.6.12"
REQUIREMENTS = ["python-binance==1.0.10"]

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    domain_config = config.get(DOMAIN)
    
    if not domain_config:
        return True
    
    yaml_config = {}
    hass.data[DOMAIN] = { 'yaml': yaml_config }
    
    for item in domain_config:
        name = item[CONF_NAME]
        
        _LOGGER.debug('Entry with name "%s" from YAML', name)
        
        existing_entry = find_existing_entry(hass, name)
        if existing_entry:
            if existing_entry.source == SOURCE_IMPORT:
                yaml_config[name] = item
                _LOGGER.debug('Skipping existing import binding for "%s"', name)
            else: 
                _LOGGER.warning("YAML config for %s is overridden by another config entry!", name)                
            
            continue
                
        yaml_config[name] = item        
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=item
            )
        )        
    
    if yaml_config:
        _LOGGER.debug("YAML names: %s", '"' + '", "'.join(yaml_config.keys()) + '"')
    else:
        _LOGGER.debug("No configuration added from YAML")

    return True
    
async def async_setup_entry(hass, config_entry: ConfigEntry) -> bool:
    entry_id = config_entry.entry_id
    name = config_entry.data[CONF_NAME]

    config = {}
    
    _LOGGER.debug("hass data is: %s", hass.data[DOMAIN])

    if config_entry.source == SOURCE_IMPORT:
        yaml_config = hass.data[DOMAIN].get('yaml')

        if not (yaml_config and name in yaml_config):
            _LOGGER.info(f"[{name}] Removing entry {entry_id} " f"after removal from YAML configuration")
            
            hass.async_create_task(hass.config_entries.async_remove(entry_id))
            return False
        else:
            config = CONFIG_ENTRY_SCHEMA({**config_entry.data, **config_entry.options})
        
    _LOGGER.debug(f"[{name}] Setting up config entry")

    binance_data_wallet = BinanceDataWallet(hass, config[CONF_API_KEY], config[CONF_API_SECRET], config[CONF_DOMAIN])
    binance_data_mining = BinanceDataMining(hass, config[CONF_API_KEY], config[CONF_API_SECRET], config[CONF_DOMAIN], config.get(CONF_MINING))

    hass.data[DOMAIN].update({
        'config': config,
        'coordinator': { 
            COORDINATOR_MINING: binance_data_mining,
            COORDINATOR_WALLET: binance_data_wallet
        }
    })
    
    upddata = [ binance_data_wallet.async_config_entry_first_refresh() ]
    if config[CONF_MINING]:
        upddata.append(
            binance_data_mining.async_config_entry_first_refresh()
        )
    
    res = await gather(*upddata, return_exceptions=True)
    
    for r in res:
        if isinstance(r, Exception): 
            await binance_data_wallet.client.close_connection()
            await binance_data_mining.client.close_connection()
            raise r
    
    if hasattr(binance_data_wallet, "balances"):
        for balance in binance_data_wallet.balances:
            if not config[CONF_BALANCES] or balance["coin"] in config[CONF_BALANCES]:
                balance["name"] = name
                balance["native"] = config[CONF_NATIVE_CURRENCY]
                balance.pop("networkList", None)
                
                hass.async_create_task(
                    async_load_platform(hass, "sensor", DOMAIN, balance, config)
                )

                fundExists = False
                
                for funding in binance_data_wallet.funding:
                    if funding["asset"] == balance["coin"]:
                        fundExists = True
                        
                        funding["name"] = name
                        funding["native"] = config[CONF_NATIVE_CURRENCY]                
                        funding.pop("btcValuation", None)
                        
                        hass.async_create_task(
                            async_load_platform(hass, "sensor", DOMAIN, funding, config)
                        )
                        
                        break

                if not fundExists:
                    funding = {
                        "name": name,
                        "native": config[CONF_NATIVE_CURRENCY],
                        "asset": balance["coin"],
                        "free": "0",
                        "locked": "0",
                        "freeze": "0",
                        "withdrawing": "0",
                    }
                    
                    hass.async_create_task(                        
                        async_load_platform(hass, "sensor", DOMAIN, funding, config)
                    )
                    
        saving = {
            'name': name,
            'native': config[CONF_NATIVE_CURRENCY],
            'coin': 'USDT',
            'total': binance_data_wallet.savings['totalAmountInUSDT'],
            'fixed': binance_data_wallet.savings['totalFixedAmountInUSDT'],
            'flexible': binance_data_wallet.savings['totalFlexibleInUSDT'],
        }
            
        hass.async_create_task(
            async_load_platform(hass, "sensor", DOMAIN, saving, config)
        )                    

        saving = {
            'name': name,
            'native': config[CONF_NATIVE_CURRENCY],
            'coin': 'BTC',
            'total': binance_data_wallet.savings['totalAmountInBTC'],
            'fixed': binance_data_wallet.savings['totalFixedAmountInBTC'],
            'flexible': binance_data_wallet.savings['totalFlexibleInBTC'],
        }
         
        hass.async_create_task(   
            async_load_platform(hass, "sensor", DOMAIN, saving, config)
        )
                    

    if hasattr(binance_data_wallet, "tickers"):
        for ticker in binance_data_wallet.tickers:
            if not config[CONF_EXCHANGES] or ticker["symbol"] in config[CONF_EXCHANGES]:
                ticker["name"] = name
                
                hass.async_create_task(
                    async_load_platform(hass, "sensor", DOMAIN, ticker, config)
                )                

    if hasattr(binance_data_mining, "mining"):
        for account, algos in binance_data_mining.mining.items():
            if not config[CONF_MINING] or account in config[CONF_MINING]:
                for algo, type in algos.items():
                    unknown = invalid = inactive = 0
                    
                    if "workers" in type:
                        for worker in type["workers"]:
                            worker["name"] = name
                            worker["algorithm"] = algo
                            worker["account"] = account
                            
                            hass.async_create_task(
                                async_load_platform(hass, "sensor", DOMAIN, worker, config)
                            )                        
                            
                            if worker["status"] == 0:
                                unknown += 1
                            elif worker["status"] == 2:
                                invalid += 1
                            elif worker["status"] == 3:
                                inactive += 1    
                            
                    if "status" in type:
                        status = copy.deepcopy(type["status"])
                        status["name"] = name
                        status["algorithm"] = algo
                        status["account"] = account
                        status["unknown"] = unknown
                        status["invalid"] = invalid
                        status["inactive"] = inactive
                        
                        if "fifteenMinHashRate" not in status:
                            status["fifteenMinHashRate"] = 0
                            
                        if "dayHashRate" not in status:
                            status["dayHashRate"] = 0                    
    
                        for coindata in binance_data_mining.coins:
                            if coindata["algoName"].lower() != algo:
                                continue
    
                            coin = coindata["coinName"]
                            
                            estimate = status.get("profitToday", {})
                            earnings = status.get("profitYesterday", {})
                            
                            profit = {
                                "name": name, 
                                "algorithm": algo,
                                "account": account,
                                "coin": coin,
                                "native": config[CONF_NATIVE_CURRENCY]
                            }
                            
                            if coin in estimate:
                                profit["profitToday"] = estimate[coin]
                            else:
                                profit["profitToday"] = 0
                            
                            if coin in earnings:
                                profit["profitYesterday"] = earnings[coin]
                            else:
                                profit["profitYesterday"] = 0
                              
                            hass.async_create_task(
                                async_load_platform(hass, "sensor", DOMAIN, profit, config)
                            )                            
                        
                        status.pop("profitToday", None)
                        status.pop("profitYesterday", None)
    
                        hass.async_create_task(
                            async_load_platform(hass, "sensor", DOMAIN, status, config)
                        )                  
                                     
    return True
   
   
def find_existing_entry(hass, name) -> Optional[ConfigEntry]:
    for config_entry in hass.config_entries.async_entries(DOMAIN):
        if config_entry.unique_id == name:
            return config_entry   
  
      
class BinanceDataMining(DataUpdateCoordinator):
    def __init__(self, hass, api_key, api_secret, tld, miners = []):
        """Initialize."""
        
        super().__init__(hass, _LOGGER, name="BinanceDataMining", update_interval=timedelta(minutes=MIN_TIME_BETWEEN_MINING_UPDATES))
        self.client = BinancePoolClient(api_key, api_secret, tld=tld)
        
        self.mining = {}
        self.coins = {}
        self.tld = tld
        
        for account in miners:
            self.mining[account] = {}

    async def _async_update_data(self):
        _LOGGER.debug(f"Fetching mining data from binance.{self.tld}")

        try:        
            if self.mining:
                common_queries = [
                    self.client.async_get_mining_coinlist(),
                    self.client.async_get_mining_algolist()
                ] 
                
                res = await gather(*common_queries, return_exceptions=True)
                for r in res:
                    if isinstance(r, Exception): 
                        await self.client.close_connection()
                        raise r
                                                        
                coins, algos = res
                
                if coins:
                    self.coins = coins

                    if algos:
                        for algo in algos:
                            algoname = algo["algoName"].lower()
                            
                            for account, algorithm in self.mining.items():
                                if algoname not in algorithm:
                                    self.mining[account][algoname] = {}
                                
                                miner_list = await self.client.async_get_mining_worker_list(algo=algoname, userName=account)
                                if miner_list:
                                    workers_list = miner_list.get("workerDatas", [])
                                    if workers_list:
                                        self.mining[account][algoname].update({ "workers": workers_list })
                                        _LOGGER.debug(f"Mining workers updated for {account} ({algoname}) from binance.{self.tld}")
        
                                    status_info = await self.client.async_get_mining_status(algo=algoname, userName=account)
                                    if status_info:
                                        self.mining[account][algoname].update({ "status": status_info })
                                        _LOGGER.debug(f"Mining status updated for {account} ({algoname}) from binance.{self.tld}")                               
                    
            return True

        except (BinanceAPIException, BinanceRequestException) as e:
            raise UpdateFailed from e

            
class BinanceDataWallet(DataUpdateCoordinator):
    
    def __init__(self, hass, api_key, api_secret, tld):
        """Initialize."""
        super().__init__(hass, _LOGGER, name="BinanceDataWallet", update_interval=timedelta(minutes=MIN_TIME_BETWEEN_UPDATES))
        
        self.client = BinancePoolClient(api_key, api_secret, tld=tld)
        self.hass = hass
        self.balances = []
        self.funding = []
        self.savings = {}
        self.tickers = {}
        self.tld = tld
        
    async def _async_update_data(self):
        _LOGGER.debug(f"Fetching wallet data from binance.{self.tld}")
        try:

            tasks = [
                self.client.async_get_capital_balances(),
                self.client.async_get_funding_balances(),
                self.client.get_lending_account(),
                self.client.get_all_tickers()
            ]
            
            res = await gather(*tasks, return_exceptions=True)
            for r in res:
                if isinstance(r, Exception):
                    await self.client.close_connection()
                    raise r
                
            balances, funding, savings, prices = res
            
            if balances:
                self.balances = balances
                _LOGGER.debug(f"Balances updated from binance.{self.tld}")

            if funding:
                self.funding = funding
                _LOGGER.debug(f"Funding data updated from binance.{self.tld}")


            if savings:
                savings.pop("positionAmountVos", None)
    
                self.savings = savings
                _LOGGER.debug(f"Savings data updated from binance.{self.tld}")

            if prices:
                self.tickers = prices
                _LOGGER.debug(f"Exchange rates updated from binance.{self.tld}")

            return True
        
        except (BinanceAPIException, BinanceRequestException) as e:
            raise UpdateFailed from e


                               
            
