"""
Binance sensor
"""
from datetime import datetime, timezone

from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.components.sensor import SensorEntity

CURRENCY_ICONS = {
    "BTC": "mdi:currency-btc",
    "BSV": "mdi:bitcoin",
    "BCH": "mdi:bitcoin",    
    "ETH": "mdi:currency-eth",
    "EUR": "mdi:currency-eur",
    "LTC": "mdi:litecoin",
    "USD": "mdi:currency-usd",
    "USDT": "mdi:currency-usd",
    "RUB": "mdi:currency-rub"
}

QUOTE_ASSETS = ["USD", "BTC", "USDT", "BUSD", "USDC", "RUB"]

DEFAULT_COIN_ICON = "mdi:currency-usd-circle"

ATTRIBUTION = "Data provided by Binance"
ATTR_FREE = "free"
ATTR_LOCKED = "locked"
ATTR_FREEZE = "freeze"
ATTR_TOTAL = "total"
ATTR_NATIVE_BALANCE = "native balance"

ATTR_WORKER_STATUS = "status"
ATTR_WORKER_HRATE = "hashrate"
ATTR_WORKER_HRATE_DAILY = "daily_hashrate"
ATTR_WORKER_REJECT = "reject_rate"
ATTR_WORKER_WORKER = "worker_name"
ATTR_WORKER_UPDATE = "updated"

ATTR_STATUS_HRATE15M = "average hashrate (15 mins)"
ATTR_STATUS_HRATE24H = "average hashrate (24 hours)"
ATTR_STATUS_VALID_WORKERS = "valid workers"
ATTR_STATUS_INVALID_WORKERS = "invalid workers"

ATTR_PROFIT_ESTIMATE = "estimated profit"
ATTR_PROFIT_EARNINGS = "yesterday's earnings"

ATTR_ACCOUNT = "account"
ATTR_ALGO = "algorithm"
ATTR_COIN = "coin"

DATA_BINANCE = "binance_pool_cache"

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the Binance sensors."""

    if discovery_info is None:
        return
    
    elif all(i in discovery_info for i in ["name", "coin", "free", "locked", "freeze", "native"]):
        name = discovery_info["name"]
        coin = discovery_info["coin"]
        free = discovery_info["free"]
        locked = discovery_info["locked"]
        freeze = discovery_info["freeze"]
        native = discovery_info["native"]

        sensor = BinanceSensor(
            hass.data[DATA_BINANCE], name, coin, free, locked, freeze, native
        )

    elif all(i in discovery_info for i in ["name", "symbol", "price"]):
        name = discovery_info["name"]
        symbol = discovery_info["symbol"]
        price = discovery_info["price"]

        sensor = BinanceExchangeSensor(hass.data[DATA_BINANCE], name, symbol, price)


    elif all(i in discovery_info for i in ["name", "account", "algorithm", "workerName", "status", "hashRate", "dayHashRate", "rejectRate", "lastShareTime"]):
        name = discovery_info["name"]
        account = discovery_info["account"]
        algorithm = discovery_info["algorithm"]
        worker = discovery_info["workerName"]
        status = discovery_info["status"]
        hrate = discovery_info["hashRate"]
        hrate_daily = discovery_info["dayHashRate"]
        reject = discovery_info["rejectRate"]
        update = discovery_info["lastShareTime"]

        sensor = BinanceWorkerSensor(hass.data[DATA_BINANCE], name, account, algorithm, worker, status, hrate, hrate_daily, reject, update)

    elif all(i in discovery_info for i in ["name", "account", "algorithm", "fifteenMinHashRate", "dayHashRate", "validNum", "invalidNum"]):
        name = discovery_info["name"]
        account = discovery_info["account"]
        algorithm = discovery_info["algorithm"]
        hrate_15min = discovery_info["fifteenMinHashRate"]
        hrate_day = discovery_info["dayHashRate"]
        validNum = discovery_info["validNum"]
        invalidNum = discovery_info["invalidNum"]

        sensor = BinanceStatusSensor(hass.data[DATA_BINANCE], name, account, algorithm, hrate_15min, hrate_day, validNum, invalidNum)
        
    elif all(i in discovery_info for i in ["name", "account", "algorithm", "coin", "profitToday", "profitYesterday"]):
        name = discovery_info["name"]
        account = discovery_info["account"]
        algorithm = discovery_info["algorithm"]
        coin = discovery_info["coin"]
        estimate = discovery_info["profitToday"]
        earnings = discovery_info["profitYesterday"]
        
        sensor = BinanceProfitSensor(hass.data[DATA_BINANCE], name, account, algorithm, coin, estimate, earnings)        

    add_entities([sensor], True)

class BinanceSensor(SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, binance_data, name, coin, free, locked, freeze, native = []):
        """Initialize the sensor."""
        self._binance_data = binance_data
        self._name = f"{name} {coin} Balance"
        self._coin = coin
        self._free = free
        self._locked = locked
        self._freeze = freeze
        self._native = native
        self._unit_of_measurement = coin
        self._total = float(free) + float(locked) + float(freeze)
        self._state = None
        self._native_balance = { "total" : {}, "free": {}, "freeze": {}, "locked": {} }

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""

        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement this sensor expresses itself in."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""

        return CURRENCY_ICONS.get(self._coin, "mdi:currency-" + self._coin.lower())

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""

        data = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_FREE: "{:.8f}".format(float(self._free)) + f" {self._unit_of_measurement}",
            ATTR_LOCKED: "{:.8f}".format(float(self._locked)) + f" {self._unit_of_measurement}",
            ATTR_FREEZE: "{:.8f}".format(float(self._freeze)) + f" {self._unit_of_measurement}",            
            ATTR_TOTAL: "{:.8f}".format(float(self._total)) + f" {self._unit_of_measurement}",
        }
        
        for type, native in self._native_balance.items():
            for asset, exchange in type.items(): 
                data[f"Native {type} balance in {asset}"] = "{:.8f}".format(exchange) + f" {asset}"
         
        return data

    def update(self):
        """Update current values."""
        self._binance_data.update()
        for balance in self._binance_data.balances:
            if balance["coin"] == self._coin:
                
                self._total = float(balance["free"]) + float(balance["locked"]) + float(balance["freeze"])
                self._free = balance["free"]
                self._locked = balance["locked"]
                self._freeze = balance["freeze"]
                self._state = self._total
                
                if self._native:
                    for native in self._native:
                        for ticker in self._binance_data.tickers:
                    
                            if ticker["symbol"] == self._coin + native.upper():
                                self._native_balance["total"][native] = float(ticker["price"]) * float(self._total)
                                self._native_balance["free"][native] = float(ticker["price"]) * float(self._free)
                                self._native_balance["locked"][native] = float(ticker["price"]) * float(self._free)
                                self._native_balance["freeze"][native] = float(ticker["price"]) * float(self._freeze)
                            
                                break
                            
                            if ticker["symbol"] == native.upper() + self._coin:      
                                self._native_balance["total"][native] = float(self._total) / float(ticker["price"])
                                self._native_balance["free"][native] = float(self._free) / float(ticker["price"])
                                self._native_balance["locked"][native] = float(self._locked) / float(ticker["price"])
                                self._native_balance["freeze"][native] = float(self._freeze) / float(ticker["price"])                                                  
                            
                                break
                break


class BinanceExchangeSensor(SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, binance_data, name, symbol, price):
        """Initialize the sensor."""
        self._binance_data = binance_data
        self._name = f"{name} {symbol} Exchange"
        self._symbol = symbol
        self._price = price
        self._unit_of_measurement = None
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement this sensor expresses itself in."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return CURRENCY_ICONS.get(self._symbol, "mdi:currency-" + self._symbol.lower())

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""

        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }

    def update(self):
        """Update current values."""
        self._binance_data.update()
        for ticker in self._binance_data.tickers:
            if ticker["symbol"] == self._symbol:
                self._state = ticker["price"]
                if ticker["symbol"][-4:] in QUOTE_ASSETS[2:5]:
                    self._unit_of_measurement = ticker["symbol"][-4:]
                elif ticker["symbol"][-3:] in QUOTE_ASSETS[:2]:
                    self._unit_of_measurement = ticker["symbol"][-3:]
                break

   
             
class BinanceWorkerSensor(SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, binance_data, name, account, algorithm, worker, status, hrate, hrate_daily, reject, update):
        """Initialize the sensor."""
        self._binance_data = binance_data
        self._name = f"{name} {account}.{worker} ({algorithm}) worker"
        self._account = account
        self._algorithm = algorithm
        self._worker = worker
        self._status = status
        self._hrate = hrate
        self._hrate_daily = hrate_daily
        self._reject = reject
        self._update = update
        self._unit_of_measurement = 'TH/s'        
        self._state = None
        
        self._status_vars = ["unknown", "valid", "invalid", "inactive"]
        self._status_icons = ["mdi:sync-off", "mdi:server-network", "mdi:server-network-off", "mdi:power-plug-off"]

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""

        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement this sensor expresses itself in."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        
        try:
            return self._status_icons[self._status]
        except KeyError as e:
            return self._status_icons[0]

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""

        data = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_WORKER_HRATE: f"{self._hrate}",
            ATTR_WORKER_HRATE_DAILY: f"{self._hrate_daily}",
            ATTR_WORKER_REJECT: f"{self._reject}",
            ATTR_WORKER_WORKER: f"{self._worker}",
            ATTR_WORKER_UPDATE: datetime.fromtimestamp(self._update / 1000).strftime("%Y-%m-%d %H:%M:%S"),
            ATTR_ACCOUNT: f"{self._account}",
            ATTR_ALGO: f"{self._algorithm}",
        }
        
        try:
            data[ATTR_WORKER_STATUS] = self._status_vars[self._status]
        except KeyError as e:
            data[ATTR_WORKER_STATUS] = "unknown"
        
        return data
        
        
    def update(self):
        """Update current values."""
        self._binance_data.update_mining()

        exists = False
                
        for account, algos in self._binance_data.mining["accounts"].items():
            if account != self._account:
                continue
                
            for algo, type in algos.items():
                if algo != self._algorithm or "workers" not in type:
                    continue
                
                for worker in type["workers"]:
                    if worker["workerName"] != self._worker:
                        continue
                    
                    exists = True
                        
                    self._status = worker["status"]
                    self._hrate = worker["hashRate"]
                    self._hrate_daily = worker["dayHashRate"]
                    self._reject = worker["rejectRate"]
                    self._update = worker["lastShareTime"]

                    self._state = float("{:.2f}".format(float(worker["hashRate"]) / 10 ** 12))
    
                    break                
                if exists:
                    break
        
            if exists:
                break
                            
        if not exists:
            self._state = None 
            
class BinanceStatusSensor(SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, binance_data, name, account, algorithm, hrate_15min, hrate_day, validNum, invalidNum):
        """Initialize the sensor."""
        self._binance_data = binance_data
        self._name = f"{name} {account} ({algorithm}) status"
        self._account = account
        self._algorithm = algorithm
        self._hrate15m = hrate_15min
        self._hrate24h = hrate_day
        self._valid_workers = validNum
        self._invalid_workers = invalidNum
        self._unit_of_measurement = None        
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""

        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement this sensor expresses itself in."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return 'mdi::finance'

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""

        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_STATUS_HRATE15M: f"{self._hrate15m}",
            ATTR_STATUS_HRATE24H: f"{self._hrate24h}",
            ATTR_STATUS_VALID_WORKERS: f"{self._valid_workers}",
            ATTR_STATUS_INVALID_WORKERS: f"{self._invalid_workers}",    
            ATTR_ACCOUNT: f"{self._account}",
            ATTR_ALGO: f"{self._algorithm}",
        }
        
        
    def update(self):
        """Update current values."""
        self._binance_data.update_mining()

        exists = False

        for account, algos in self._binance_data.mining["accounts"].items():
            if account != self._account:
                continue
                
            for algo, type in algos.items():
                if algo != self._algorithm or "status" not in type:
                    continue
                
                exists = True
                
                self._hrate15m = type["status"].get("fifteenMinHashRate", 0)
                self._hrate24h = type["status"].get("dayHashRate", 0)
                self._valid_workers = type["status"]["validNum"]
                self._invalid_workers = type["status"]["invalidNum"]
                
                self._state = float("{:.2f}".format(float(self._hrate15m) / 10 ** 12))

                break
            
            if exists:
                break
                
        if not exists:
            self._state = 0
            
class BinanceProfitSensor(SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, binance_data, name, account, algorithm, coin, estimate, earnings):
        """Initialize the sensor."""
        self._binance_data = binance_data
        self._name = f"{name} {account} ({algorithm}) {coin} profit"
        self._account = account
        self._algorithm = algorithm
        self._coin = coin
        self._estimate = estimate
        self._earnings = earnings
        self._unit_of_measurement = f"{coin}"        
        self._state = None
        
    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""

        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement this sensor expresses itself in."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return CURRENCY_ICONS.get(self._coin, "mdi:currency-" + self._coin.lower())

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""

        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_PROFIT_ESTIMATE: f"{self._estimate}",
            ATTR_PROFIT_EARNINGS: f"{self._earnings}",
            ATTR_COIN: f"{self._coin}",
            ATTR_ACCOUNT: f"{self._account}",
            ATTR_ALGO: f"{self._algorithm}",
        }
        
        
    def update(self):
        """Update current values."""
        self._binance_data.update_mining()

        exists = False
                
        for account, algos in self._binance_data.mining["accounts"].items():
            if account != self._account:
                continue
                
            for algo, type in algos.items():
                if algo != self._algorithm or "status" not in type:
                    continue
                
                for coindata in self._binance_data.coins:
                    coin = coindata["coinName"]
                    
                    if coin != self._coin:
                        continue

                    estimate = type["status"].get("profitToday", {})
                    earnings = type["status"].get("profitYesterday", {})
                        
                    exists = True
                                            
                    if coin in estimate:
                        self._estimate = estimate[coin]
                    else:
                        self._estimate = 0.00
                    
                    if coin in earnings:
                        self._earnings = earnings[coin]
                        self._state = earnings[coin]
                    else:
                        self._earnings = 0.00
                        self._state = 0.00

                    break   
                
                if exists:
                    break
        
            if exists:
                break
                            
        if not exists:
            self._state = None             