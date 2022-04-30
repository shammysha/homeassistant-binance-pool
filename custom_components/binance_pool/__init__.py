from datetime import timedelta
import logging
import asyncio
import copy

from binance.client import AsyncClient
from binance.exceptions import BinanceAPIException, BinanceRequestException
import voluptuous as vol

from homeassistant.const import CONF_API_KEY, CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.util import Throttle

__version__ = "1.4.6"
REQUIREMENTS = ["python-binance==1.0.10"]

DOMAIN = "binance_pool"

DEFAULT_NAME = "Binance"
DEFAULT_DOMAIN = "us"
DEFAULT_CURRENCY = [ "USD" ]
CONF_API_SECRET = "api_secret"
CONF_BALANCES = "balances"
CONF_EXCHANGES = "exchanges"
CONF_MINING = "miners"
CONF_DOMAIN = "domain"
CONF_NATIVE_CURRENCY = "native_currency"

SCAN_INTERVAL = timedelta(minutes=1)
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)
MIN_TIME_BETWEEN_MINING_UPDATES = timedelta(minutes=5)

DATA_BINANCE = "binance_pool_cache"

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Optional(CONF_DOMAIN, default=DEFAULT_DOMAIN): cv.string,
                vol.Optional(CONF_NATIVE_CURRENCY, default=DEFAULT_CURRENCY): vol.All(
                    cv.ensure_list, [cv.string]
                ),
                vol.Required(CONF_API_KEY): cv.string,
                vol.Required(CONF_API_SECRET): cv.string,
                vol.Optional(CONF_BALANCES, default=[]): vol.All(
                    cv.ensure_list, [cv.string]
                ),
                vol.Optional(CONF_EXCHANGES, default=[]): vol.All(
                    cv.ensure_list, [cv.string]
                ),
                vol.Optional(CONF_MINING, default=[]): vol.All(
                    cv.ensure_list, [cv.string]
                ),                
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    api_key = config[DOMAIN][CONF_API_KEY]
    api_secret = config[DOMAIN][CONF_API_SECRET]
    name = config[DOMAIN].get(CONF_NAME)
    balances = config[DOMAIN].get(CONF_BALANCES)
    tickers = config[DOMAIN].get(CONF_EXCHANGES)
    miners = config[DOMAIN].get(CONF_MINING)
    native_currency = config[DOMAIN].get(CONF_NATIVE_CURRENCY)
    tld = config[DOMAIN].get(CONF_DOMAIN)

    binance_data = BinanceData(api_key, api_secret, tld, miners)
    
    upddata = [ binance_data.async_update() ]
    if miners:
        upddata.append(
            binance_data.async_update_mining()
        )
    res = await asyncio.gather(*upddata, return_exceptions=True)
    
    hass.data[DATA_BINANCE] = binance_data
     
    if hasattr(binance_data, "balances"):
        for balance in binance_data.balances:
            if not balances or balance["coin"] in balances:
                balance["name"] = name
                balance["native"] = native_currency
                balance.pop("networkList", None)
                
                hass.async_create_task(
                    async_load_platform(hass, "sensor", DOMAIN, balance, config)
                )

                fundExists = False
                
                for funding in binance_data.funding:
                    if funding["asset"] == balance["coin"]:
                        fundExists = True
                        
                        funding["name"] = name
                        funding["native"] = native_currency                
                        funding.pop("btcValuation", None)
                        
                        hass.async_create_task(
                            async_load_platform(hass, "sensor", DOMAIN, funding, config)
                        )
                        
                        break

                if not fundExists:
                    funding = {
                        "name": name,
                        "native": native_currency,
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
            'native': native_currency,
            'coin': 'USDT',
            'total': binance_data.savings['totalAmountInUSDT'],
            'fixed': binance_data.savings['totalFixedAmountInUSDT'],
            'flexible': binance_data.savings['totalFlexibleInUSDT'],
        }
            
        hass.async_create_task(
            async_load_platform(hass, "sensor", DOMAIN, saving, config)
        )                    

        saving = {
            'name': name,
            'native': native_currency,
            'coin': 'BTC',
            'total': binance_data.savings['totalAmountInBTC'],
            'fixed': binance_data.savings['totalFixedAmountInBTC'],
            'flexible': binance_data.savings['totalFlexibleInBTC'],
        }
         
        hass.async_create_task(   
            async_load_platform(hass, "sensor", DOMAIN, saving, config)
        )
                    

    if hasattr(binance_data, "tickers"):
        for ticker in binance_data.tickers:
            if not tickers or ticker["symbol"] in tickers:
                ticker["name"] = name
                
                hass.async_create_task(
                    async_load_platform(hass, "sensor", DOMAIN, ticker, config)
                )                

    if hasattr(binance_data, "mining") and "accounts" in binance_data.mining:
        for account, algos in binance_data.mining["accounts"].items():
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

                    for coindata in binance_data.coins:
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
                            "native": native_currency,
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


class BinanceData:
    def __init__(self, api_key, api_secret, tld, miners = []):
        """Initialize."""
        self.client = BinancePoolClient(api_key, api_secret, tld=tld)
        self.coins = {}
        self.balances = []
        self.funding = []
        self.savings = {}
        self.tickers = {}
        self.mining = {}
        self.tld = tld
        
        if miners: 
            self.mining = { "accounts": {} }
            for account in miners:
                self.mining["accounts"] = { account: {} }
        
        
    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        _LOGGER.debug(f"Fetching data from binance.{self.tld}")
        try:

            tasks = [
                self.client.async_get_capital_balances(),
                self.client.async_get_funding_balances(),
                self.client.get_lending_account(),
                self.client.get_all_tickers()
            ]
            
            res = await asyncio.gather(*tasks, return_exceptions=True)
            
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
            _LOGGER.error(f"Error fetching data from binance.{self.tld}: {e.message}")
            return False


    @Throttle(MIN_TIME_BETWEEN_MINING_UPDATES)
    async def async_update_mining(self):
        _LOGGER.debug(f"Fetching mining data from binance.{self.tld}")
        try:        
            if "accounts" in self.mining:
                common_queries = [
                    self.client.async_get_mining_coinlist(),
                    self.client.async_get_mining_algolist()
                ] 
                
                res = await asyncio.gather(*common_queries, return_exceptions=True)
                
                coins, algos = res
                
                if coins:
                    self.coins = coins

                    if algos:
                        for algo in algos:
                            algoname = algo["algoName"].lower()
                            
                            for account, algorithm in self.mining["accounts"].items():
                                if algoname not in algorithm:
                                    self.mining["accounts"][account][algoname] = {}
                                
                                miner_list = await self.client.async_get_mining_worker_list(algo=algoname, userName=account)
                                if miner_list:
                                    workers_list = miner_list.get("workerDatas", [])
                                    if workers_list:
                                        self.mining["accounts"][account][algoname].update({ "workers": workers_list })
                                        _LOGGER.debug(f"Mining workers updated for {account} ({algoname}) from binance.{self.tld}")
        
                                    status_info = await self.client.async_get_mining_status(algo=algoname, userName=account)
                                    if status_info:
                                        self.mining["accounts"][account][algoname].update({ "status": status_info })
                                        _LOGGER.debug(f"Mining status updated for {account} ({algoname}) from binance.{self.tld}")                               
                    
            return True

        except (BinanceAPIException, BinanceRequestException) as e:
            _LOGGER.error(f"Error fetching mining data from binance.{self.tld}: {e.message}")
            return False                                       
            
class BinancePoolClient(AsyncClient):
    MINING_API_URL = 'https://api.binance.{}/sapi'
    BALANCES_API_URL = 'https://api.binance.{}/sapi'
    MINING_API_VERSION = 'v1'
    BALANCES_API_VERSION = 'v1'
    RECV_WINDOW = 50000
    
    def _get_request_kwargs(self, method, signed: bool, force_params: bool = False, **kwargs):
        if signed:
            kwargs['data']['recvWindow'] = self.RECV_WINDOW
            
        return super()._get_request_kwargs(method, signed, force_params, **kwargs)
    
    def _create_mining_api_url(self, path: str, version: str = MINING_API_URL ) -> str:
        return self.MINING_API_URL.format(self.tld) + '/' + self.MINING_API_VERSION + '/mining/' + path        

    def _create_capital_api_url(self, path: str, version: str = BALANCES_API_URL ) -> str:
        return self.BALANCES_API_URL.format(self.tld) + '/' + self.BALANCES_API_VERSION + '/capital/' + path
        
    async def async_request_mining_api(self, method, path, signed=False, **kwargs):
        uri = self._create_mining_api_url(path)
        
        answer = await self._request(method, uri, signed, True, **kwargs)
        
        if answer["code"] != 0 or "data" not in answer:
            _LOGGER.error(f"Error fetching mining data from binance.{self.tld}: {answer}")
            return False   
             
        return answer["data"]

    async def async_request_capital_api(self, method, path, signed=False, **kwargs):
        uri = self._create_capital_api_url(path)
        
        return await self._request(method, uri, signed, True, **kwargs)
        
    async def async_get_mining_algolist(self):
        """ Acquiring Algorithm (MARKET_DATA)
        
            https://binance-docs.github.io/apidocs/spot/en/#acquiring-algorithm-market_data
            
        """
        return await self.async_request_mining_api('get', 'pub/algoList')


    async def async_get_mining_coinlist(self):
        """ Acquiring CoinName (MARKET_DATA)
        
            https://binance-docs.github.io/apidocs/spot/en/#acquiring-coinname-market_data
        """
        return await self.async_request_mining_api('get', 'pub/coinList')        


    async def async_get_mining_worker_detail(self, **params):
        """ Request for Detail Miner List (USER_DATA)

            https://binance-docs.github.io/apidocs/spot/en/#request-for-detail-miner-list-user_data
        """
        return await self.async_request_mining_api('get', 'worker/detail', True, data=params)        
        

    async def async_get_mining_worker_list(self, **params):
        """ Request for Miner List (USER_DATA)

            https://binance-docs.github.io/apidocs/spot/en/#earnings-list-user_data
        """
        return await self.async_request_mining_api('get', 'worker/list', True, data=params)        
        
    
    async def async_get_mining_earning_history(self, **params):
        """ Earnings List(USER_DATA)

            https://binance-docs.github.io/apidocs/spot/en/#earnings-list-user_data
        """
        return await self.async_request_mining_api('get', 'payment/list', True, data=params)      


    async def async_get_mining_bonus_history(self, **params):
        """ Extra Bonus List (USER_DATA)

            https://binance-docs.github.io/apidocs/spot/en/#extra-bonus-list-user_data
        """
        return await self.async_request_mining_api('get', 'payment/other', True, data=params) 


    async def async_get_mining_status(self, **params):
        """ Statistic List (USER_DATA)

            https://binance-docs.github.io/apidocs/spot/en/#statistic-list-user_data
        """
        return await self.async_request_mining_api('get', 'statistics/user/status', True, data=params) 

        
    async def async_get_mining_history(self, **params):
        """ Account List (USER_DATA)

            https://binance-docs.github.io/apidocs/spot/en/#account-list-user_data
        """
        return await self.async_request_mining_api('get', 'statistics/user/list', True, data=params)           

    async def async_get_capital_balances(self, **params):
        """ All Coins' Information (USER_DATA)

            https://binance-docs.github.io/apidocs/spot/en/#all-coins-39-information-user_data
        """
        return await self.async_request_capital_api('get', 'config/getall', True, data=params) 
        
    async def async_get_funding_balances(self, **params):
        """ Funding Wallet (USER_DATA)
        
            https://binance-docs.github.io/apidocs/spot/en/#funding-wallet-user_data
        """
        return await self._request_margin_api('post', 'asset/get-funding-asset', True, data=params) 
        
