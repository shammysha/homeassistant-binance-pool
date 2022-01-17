from datetime import timedelta
import logging

from binance.client import Client, MARGIN_API_URL
from binance.exceptions import BinanceAPIException, BinanceRequestException
import voluptuous as vol

from homeassistant.const import CONF_API_KEY, CONF_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import load_platform
from homeassistant.util import Throttle

__version__ = "1.0.1"
REQUIREMENTS = ["python-binance==1.0.10"]

DOMAIN = "binance_pool"

DEFAULT_NAME = "Binance"
DEFAULT_DOMAIN = "us"
DEFAULT_CURRENCY = "USD"
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
                vol.Optional(CONF_NATIVE_CURRENCY, default=DEFAULT_CURRENCY): cv.string,
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


def setup(hass, config):
    api_key = config[DOMAIN][CONF_API_KEY]
    api_secret = config[DOMAIN][CONF_API_SECRET]
    name = config[DOMAIN].get(CONF_NAME)
    balances = config[DOMAIN].get(CONF_BALANCES)
    tickers = config[DOMAIN].get(CONF_EXCHANGES)
    miners = config[DOMAIN].get(CONF_MINING)
    native_currency = config[DOMAIN].get(CONF_NATIVE_CURRENCY).upper()
    tld = config[DOMAIN].get(CONF_DOMAIN)

    hass.data[DATA_BINANCE] = binance_data = BinanceData(api_key, api_secret, tld, miners)

    if not hasattr(binance_data, "balances"):
        pass
    else:
        for balance in binance_data.balances:
            if not balances or balance["coin"] in balances:
                balance["name"] = name
                balance.pop("networkList", None)
                load_platform(hass, "sensor", DOMAIN, balance, config)

    if not hasattr(binance_data, "tickers"):
        pass
    else:
        for ticker in binance_data.tickers:
            if not tickers or ticker["symbol"] in tickers:
                ticker["name"] = name
                load_platform(hass, "sensor", DOMAIN, ticker, config)

    if not hasattr(binance_data, "mining") or "accounts" not in binance_data.mining:
        pass
    else:
        for account, algos in binance_data.mining["accounts"].items():
            for algo, type in algos.items():
                if "workers" in type:
                    for worker in type["workers"]:
                        worker["name"] = name
                        worker["algorithm"] = algo
                        worker["account"] = account
                        load_platform(hass, "sensor", DOMAIN, worker, config)
                        
                if "status" in type:
                    status = type["status"]
                    status["name"] = name
                    status["algorithm"] = algo
                    status["account"] = account
                    
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
                            "coin": coin
                        }
                        
                        if coin in estimate:
                            profit["profitToday"] = estimate[coin]
                        else:
                            profit["profitToday"] = 0
                        
                        if coin in earnings:
                            profit["profitYesterday"] = earnings[coin]
                        else:
                            profit["profitYesterday"] = 0
                            
                        load_platform(hass, "sensor", DOMAIN, profit, config)                        
                    
                    status.pop("profitToday", None)
                    status.pop("profitYesterday", None)
                    
                    load_platform(hass, "sensor", DOMAIN, status, config)                                        
    return True


class BinanceData:
    def __init__(self, api_key, api_secret, tld, miners = []):
        """Initialize."""
        self.client = BinancePoolClient(api_key, api_secret, tld=tld)
        self.coins = {}
        self.balances = []
        self.tickers = {}
        self.mining = {}
        self.tld = tld

        self.update()
        
        if miners: 
            self.mining = { "accounts": {} }
            for account in miners:
                self.mining["accounts"] = { account: {} }
                
            self.update_mining()                
        

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        _LOGGER.debug(f"Fetching data from binance.{self.tld}")
        try:
            balances = self.client.get_capital_balances()
            if balances:
                self.balances = balances
                _LOGGER.debug(f"Balances updated from binance.{self.tld}")

            prices = self.client.get_all_tickers()
            if prices:
                self.tickers = prices
                _LOGGER.debug(f"Exchange rates updated from binance.{self.tld}")
            
        except (BinanceAPIException, BinanceRequestException) as e:
            _LOGGER.error(f"Error fetching data from binance.{self.tld}: {e.message}")
            return False


    @Throttle(MIN_TIME_BETWEEN_MINING_UPDATES)
    def update_mining(self):
        _LOGGER.debug(f"Fetching mining data from binance.{self.tld}")
        try:        
            if "accounts" in self.mining:
                coins = self.client.get_mining_coinlist();
                if coins:
                    self.coins = coins

                    algos = self.client.get_mining_algolist();
                    if algos:
                        for algo in algos:
                            algoname = algo["algoName"].lower()
                                                    
                            for account, algorithm in self.mining["accounts"].items():
                                if algoname not in algorithm:
                                    self.mining["accounts"][account][algoname] = {}
                                
                                miner_list = self.client.get_mining_worker_list(algo=algoname, userName=account)
                                workers_list = miner_list.get("workerDatas", [])
                                if workers_list:
                                    self.mining["accounts"][account][algoname].update({ "workers": workers_list })
                                    _LOGGER.debug(f"Mining workers updated for {account} ({algoname}) from binance.{self.tld}")
    
                                status_info = self.client.get_mining_status(algo=algoname, userName=account)
                                if status_info:
                                    self.mining["accounts"][account][algoname].update({ "status": status_info })
                                    _LOGGER.debug(f"Mining status updated for {account} ({algoname}) from binance.{self.tld}")                               
                    
                                      
        except (BinanceAPIException, BinanceRequestException) as e:
            _LOGGER.error(f"Error fetching mining data from binance.{self.tld}: {e.message}")
            return False                                       
            
class BinancePoolClient(Client):

    def _create_mining_api_url(self, path: str, version: str = MARGIN_API_URL ) -> str:
        return self.MARGIN_API_URL.format(self.tld) + '/' + MARGIN_API_VERSION + '/mining/' + path        

    def _create_capital_api_url(self, path: str, version: str = MARGIN_API_URL ) -> str:
        return self.MARGIN_API_URL.format(self.tld) + '/' + self.MARGIN_API_VERSION + '/capital/' + path
      
    def _request_mining_api(self, method, path, signed=False, **kwargs):
        uri = self._create_mining_api_url(path)
        
        answer = self._request(method, uri, signed, True, **kwargs)
        
        if answer["code"] != 0 or "data" not in answer:
            _LOGGER.error(f"Error fetching mining data from binance.{self.tld}: {answer}")
            return False   
             
        return answer["data"]

    def _request_capital_api(self, method, path, signed=False, **kwargs):
        uri = self._create_capital_api_url(path)
        
        return self._request(method, uri, signed, True, **kwargs)
        
    def get_mining_algolist(self):
        """ Acquiring Algorithm (MARKET_DATA)
        
            https://binance-docs.github.io/apidocs/spot/en/#acquiring-algorithm-market_data
            
        """
        return self._request_mining_api('get', 'pub/algoList')


    def get_mining_coinlist(self):
        """ Acquiring CoinName (MARKET_DATA)
        
            https://binance-docs.github.io/apidocs/spot/en/#acquiring-coinname-market_data
        """
        return self._request_mining_api('get', 'pub/coinList')        


    def get_mining_worker_detail(self, **params):
        """ Request for Detail Miner List (USER_DATA)

            https://binance-docs.github.io/apidocs/spot/en/#request-for-detail-miner-list-user_data
        """
        return self._request_mining_api('get', 'worker/detail', True, data=params)        
        

    def get_mining_worker_list(self, **params):
        """ Request for Miner List (USER_DATA)

            https://binance-docs.github.io/apidocs/spot/en/#earnings-list-user_data
        """
        return self._request_mining_api('get', 'worker/list', True, data=params)        
        
    
    def get_mining_earning_history(self, **params):
        """ Earnings List(USER_DATA)

            https://binance-docs.github.io/apidocs/spot/en/#earnings-list-user_data
        """
        return self._request_mining_api('get', 'payment/list', True, data=params)      


    def get_mining_bonus_history(self, **params):
        """ Extra Bonus List (USER_DATA)

            https://binance-docs.github.io/apidocs/spot/en/#extra-bonus-list-user_data
        """
        return self._request_mining_api('get', 'payment/other', True, data=params) 


    def get_mining_status(self, **params):
        """ Statistic List (USER_DATA)

            https://binance-docs.github.io/apidocs/spot/en/#statistic-list-user_data
        """
        return self._request_mining_api('get', 'statistics/user/status', True, data=params) 

        
    def get_mining_history(self, **params):
        """ Account List (USER_DATA)

            https://binance-docs.github.io/apidocs/spot/en/#account-list-user_data
        """
        return self._request_mining_api('get', 'statistics/user/list', True, data=params)           

    def get_capital_balances(self, **params):
        """ All Coins' Information (USER_DATA)

            https://binance-docs.github.io/apidocs/spot/en/#all-coins-39-information-user_data
        """
        return self._request_capital_api('get', 'config/getall', True, data=params) 