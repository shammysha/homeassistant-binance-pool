import logging

from aiohttp import (
    ClientSession
)

from binance.client import (
    AsyncClient
)

from binance.exceptions import *

_LOGGER = logging.getLogger(__name__)

class BinancePoolClient(AsyncClient):
    MINING_API_URL = 'https://api.binance.{}/sapi'
    BALANCES_API_URL = 'https://api.binance.{}/sapi'
    MINING_API_VERSION = 'v1'
    BALANCES_API_VERSION = 'v1'
    RECV_WINDOW = 50000
    
    def _init_session(self) -> ClientSession:
        return ClientSession(
            loop=self.loop,
            headers=self._get_headers()
        )
    
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
            raise BinanceRequestException(f'Invalid Response: {answer}')        
        
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

            https://binance-docs.github.io/apidocs/spot/en/#request-for-miner-list-user_data
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
        

    async def async_get_simple_earn_account(self, **params):
        """ Get Simple Earn Locked Product List (USER_DATA)
        
            https://binance-docs.github.io/apidocs/spot/en/#simple-account-user_data
        """
        return await self._request_margin_api('post', 'simple-earn/account', True, data=params)
