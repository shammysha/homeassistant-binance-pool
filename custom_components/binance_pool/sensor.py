"""
Binance sensor
"""
from datetime import (
    datetime
)

from homeassistant.const import (
    ATTR_ATTRIBUTION
)

from homeassistant.core import ( 
    callback
)

from homeassistant.components.sensor import (
    SensorEntity
)

from homeassistant.util import (
    slugify
)

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity
)

from .const import (
    DOMAIN,
    CURRENCY_ICONS,
    EXCHANGES_ICON,
    STATUS_ICON,

    ATTRIBUTION,
    ATTR_FREE,
    ATTR_LOCKED,
    ATTR_FREEZE,
    ATTR_WITHDRAW,
    ATTR_TOTAL,
    ATTR_FLEXIBLE,
    ATTR_FIXED,
    
    ATTR_WORKER_STATUS,
    ATTR_WORKER_HRATE,
    ATTR_WORKER_HRATE_DAILY,
    ATTR_WORKER_REJECT,
    ATTR_WORKER_WORKER,
    ATTR_WORKER_UPDATE,
    
    ATTR_STATUS_HRATE15M,
    ATTR_STATUS_HRATE24H,
    ATTR_STATUS_VALID_WORKERS,
    ATTR_STATUS_INVALID_WORKERS,
    ATTR_STATUS_INACTIVE_WORKERS,
    ATTR_STATUS_UNKNOWN_WORKERS,
    ATTR_STATUS_TOTAL_ALERTS,
    
    ATTR_PROFIT_ESTIMATE,
    ATTR_PROFIT_EARNINGS,
    
    ATTR_ACCOUNT,
    ATTR_ALGO,
    ATTR_COIN,

    COORDINATOR_MINING,
    COORDINATOR_WALLET
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    entry_id = config_entry.entry_id
    sensors = hass.data[DOMAIN][entry_id]['sensors']
    coordinators = hass.data[DOMAIN][entry_id]['coordinator']
    
    for sensor_data in sensors:
        sensor = False
        
        if sensor_data is None:
            continue
        
        elif all(i in sensor_data for i in ["name", "coin", "free", "locked", "freeze", "native"]):
            coordinator = coordinators[COORDINATOR_WALLET]        
            name = sensor_data["name"]
            coin = sensor_data["coin"]
            free = sensor_data["free"]
            locked = sensor_data["locked"]
            freeze = sensor_data["freeze"]
            native = sensor_data["native"]
    
            sensor = BinanceBalanceSensor(coordinator, name, coin, free, locked, freeze, native)
            
        elif all(i in sensor_data for i in ["name", "asset", "free", "locked", "freeze", "withdrawing", "native"]):
            coordinator = coordinators[COORDINATOR_WALLET]        
            name = sensor_data["name"]
            coin = sensor_data["asset"]
            free = sensor_data["free"]
            locked = sensor_data["locked"]
            freeze = sensor_data["freeze"]
            native = sensor_data["native"]
            withdrawing = sensor_data["withdrawing"]
    
            sensor = BinanceFundingSensor(coordinator, name, coin, free, locked, freeze, withdrawing, native)
            
        elif all(i in sensor_data for i in ["name", "coin", "total", "fixed", "flexible", "native"]):
            coordinator = coordinators[COORDINATOR_WALLET]        
            name = sensor_data["name"]
            coin = sensor_data["coin"]
            total = sensor_data["total"]
            fixed = sensor_data["fixed"]
            flexible = sensor_data["flexible"]
            native = sensor_data["native"]
    
            sensor = BinanceSavingsSensor(coordinator, name, coin, total, fixed, flexible, native)        
            
        elif all(i in sensor_data for i in ["name", "symbol", "price"]):
            coordinator = coordinators[COORDINATOR_WALLET]        
            name = sensor_data["name"]
            symbol = sensor_data["symbol"]
            price = sensor_data["price"]
    
            sensor = BinanceExchangeSensor(coordinator, name, symbol, price)
    
    
        elif all(i in sensor_data for i in ["name", "account", "algorithm", "workerName", "status", "hashRate", "dayHashRate", "rejectRate", "lastShareTime"]):
            coordinator = coordinators[COORDINATOR_MINING]        
            name = sensor_data["name"]
            account = sensor_data["account"]
            algorithm = sensor_data["algorithm"]
            worker = sensor_data["workerName"]
            status = sensor_data["status"]
            hrate = sensor_data["hashRate"]
            hrate_daily = sensor_data["dayHashRate"]
            reject = sensor_data["rejectRate"]
            update = sensor_data["lastShareTime"]
    
            sensor = BinanceWorkerSensor(coordinator, name, account, algorithm, worker, status, hrate, hrate_daily, reject, update)
    
        elif all(i in sensor_data for i in ["name", "account", "algorithm", "fifteenMinHashRate", "dayHashRate", "validNum", "invalidNum", "unknown", "invalid", "inactive"]):
            coordinator = coordinators[COORDINATOR_MINING]
            name = sensor_data["name"]
            account = sensor_data["account"]
            algorithm = sensor_data["algorithm"]
            hrate_15min = sensor_data["fifteenMinHashRate"]
            hrate_day = sensor_data["dayHashRate"]
            validNum = sensor_data["validNum"]
            invalidNum = sensor_data["invalidNum"]
            unknown = sensor_data["unknown"]
            invalid = sensor_data["invalid"]
            inactive = sensor_data["inactive"]
    
            sensor = BinanceStatusSensor(coordinator, name, account, algorithm, hrate_15min, hrate_day, validNum, invalidNum, unknown, invalid, inactive)
            
        elif all(i in sensor_data for i in ["name", "account", "algorithm", "coin", "profitToday", "profitYesterday", "native"]):
            coordinator = coordinators[COORDINATOR_MINING]
            wallet = coordinators[COORDINATOR_WALLET]
            name = sensor_data["name"]
            account = sensor_data["account"]
            algorithm = sensor_data["algorithm"]
            coin = sensor_data["coin"]
            estimate = sensor_data["profitToday"]
            earnings = sensor_data["profitYesterday"]
            native = sensor_data["native"]
            
            
            sensor = BinanceProfitSensor(coordinator, wallet, name, account, algorithm, coin, estimate, earnings, native)        
    
        if sensor:
            async_add_entities([sensor], False)

class BinanceSensorEntity(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator:CoordinatorEntity, name:str):
        super().__init__(coordinator = coordinator)
        
        self._name = name
        self._state = None
        
        
    @property
    def unique_id(self):
        return slugify(text = self._name, separator = '-')
    
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
        raise Exception('Unimplemented')

    @property
    def icon(self):
        raise Exception('Unimplemented')

    @property
    def extra_state_attributes(self):
        raise Exception('Unimplemented')
    
    async def async_added_to_hass(self):
        self._handle_coordinator_update()    
        
        self.async_on_remove(
            self.coordinator.async_add_listener(
                self._handle_coordinator_update, self.coordinator_context
            )
        )        
    
    @callback
    def _handle_coordinator_update(self) -> None:
        raise Exception('Unimplemented')

    
class BinanceBalanceSensor(BinanceSensorEntity):
    """Representation of a Sensor."""
    
    def __init__(self, coordinator, name, coin, free, locked, freeze, native = []):
        """Initialize the sensor."""
        self._coin = coin
        self._free = free
        self._locked = locked
        self._freeze = freeze
        self._native = native
        self._unit_of_measurement = coin
        self._total = float(free) + float(locked) + float(freeze)
        self._native_balance = { "total" : {}, "free": {}, "freeze": {}, "locked": {} }
        
        super().__init__(
            coordinator = coordinator, 
            name = f"{name} {coin} Balance"
        )

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
            ATTR_FREE: "{:.8f}".format(float(self._free)),
            ATTR_LOCKED: "{:.8f}".format(float(self._locked)),
            ATTR_FREEZE: "{:.8f}".format(float(self._freeze)),            
            ATTR_TOTAL: "{:.8f}".format(float(self._total)),
        }
        
        for typ, native in self._native_balance.items():
            for asset, exchange in native.items(): 
                data[f"Native {typ} balance in {asset}"] = exchange
         
        return data

    @callback
    def _handle_coordinator_update(self) -> None:
        for balance in self.coordinator.balances:
            if balance["coin"] == self._coin:
                
                self._total = float(balance["free"]) + float(balance["locked"]) + float(balance["freeze"])
                self._free = balance["free"]
                self._locked = balance["locked"]
                self._freeze = balance["freeze"]
                self._state = self._total
                
                if self._native:
                    for native in self._native:
                        for ticker in self.coordinator.tickers:
                            if ticker["symbol"] == self._coin + native.upper():
                                self._native_balance["total"][native] = "{:.2f}".format(float(ticker["price"]) * float(self._total))
                                self._native_balance["free"][native] = "{:.2f}".format(float(ticker["price"]) * float(self._free))
                                self._native_balance["locked"][native] = "{:.2f}".format(float(ticker["price"]) * float(self._locked))
                                self._native_balance["freeze"][native] = "{:.2f}".format(float(ticker["price"]) * float(self._freeze))

                                break
                            
                            if ticker["symbol"] == native.upper() + self._coin:      
                                self._native_balance["total"][native] = "{:.8f}".format(float(self._total) / float(ticker["price"]))
                                self._native_balance["free"][native] = "{:.8f}".format(float(self._free) / float(ticker["price"]))
                                self._native_balance["locked"][native] = "{:.8f}".format(float(self._locked) / float(ticker["price"]))
                                self._native_balance["freeze"][native] = "{:.8f}".format(float(self._freeze) / float(ticker["price"]))                                               
                            
                                break
                break

        self.async_write_ha_state()
        
class BinanceFundingSensor(BinanceSensorEntity):
    """Representation of a Sensor."""

    def __init__(self, coordinator, name, coin, free, locked, freeze, withdrawing, native = []):
        """Initialize the sensor."""
        self._coin = coin
        self._free = free
        self._locked = locked
        self._freeze = freeze
        self._withdrawing = withdrawing
        self._native = native
        self._unit_of_measurement = coin
        self._total = float(free) + float(locked) + float(freeze)
        self._native_balance = { "total" : {}, "free": {}, "freeze": {}, "locked": {}, "withdrawing": {} }
        
        super().__init__(
            coordinator = coordinator, 
            name = f"{name} {coin} Funding"
        )        

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
            ATTR_FREE: "{:.8f}".format(float(self._free)),
            ATTR_LOCKED: "{:.8f}".format(float(self._locked)),
            ATTR_FREEZE: "{:.8f}".format(float(self._freeze)),    
            ATTR_WITHDRAW: "{:.8f}".format(float(self._withdrawing)),                    
            ATTR_TOTAL: "{:.8f}".format(float(self._total)),
        }
        
        for typ, native in self._native_balance.items():
            for asset, exchange in native.items(): 
                data[f"Native {typ} funding in {asset}"] = exchange
         
        return data

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update current values."""
        
        fundExists = False
        
        for funding in self.coordinator.funding:
            if funding["asset"] == self._coin:
                fundExists = True
                
                self._total = float(funding["free"]) + float(funding["locked"]) + float(funding["freeze"]) + float(funding["withdrawing"])
                self._free = funding["free"]
                self._locked = funding["locked"]
                self._freeze = funding["freeze"]
                self._withdrawing = funding["withdrawing"]
                self._state = self._total

                break
        
        if not fundExists:
            self._total = 0.00
            self._free = 0.00
            self._locked = 0.00
            self._freeze = 0.00
            self._withdrawing = 0.00
            self._state = 0.00        
                
        if self._native:
            for native in self._native:
                for ticker in self.coordinator.tickers:
            
                    if ticker["symbol"] == self._coin + native.upper():
                        self._native_balance["total"][native] = "{:.2f}".format(float(ticker["price"]) * float(self._total))
                        self._native_balance["free"][native] = "{:.2f}".format(float(ticker["price"]) * float(self._free))
                        self._native_balance["locked"][native] = "{:.2f}".format(float(ticker["price"]) * float(self._locked))
                        self._native_balance["freeze"][native] = "{:.2f}".format(float(ticker["price"]) * float(self._freeze))
                        self._native_balance["withdrawing"][native] = "{:.2f}".format(float(ticker["price"]) * float(self._withdrawing))
                    
                        break
                    
                    if ticker["symbol"] == native.upper() + self._coin:      
                        self._native_balance["total"][native] = "{:.8f}".format(float(self._total) / float(ticker["price"]))
                        self._native_balance["free"][native] = "{:.8f}".format(float(self._free) / float(ticker["price"]))
                        self._native_balance["locked"][native] = "{:.8f}".format(float(self._locked) / float(ticker["price"]))
                        self._native_balance["freeze"][native] = "{:.8f}".format(float(self._freeze) / float(ticker["price"]))                                               
                        self._native_balance["withdrawing"][native] = "{:.8f}".format(float(self._withdrawing) / float(ticker["price"]))
                    
                        break

        self.async_write_ha_state()
        
class BinanceSavingsSensor(BinanceSensorEntity):
    """Representation of a Sensor."""

    def __init__(self, coordinator, name, coin, total, fixed, flexible, native = []):
        """Initialize the sensor."""
        self._coin = coin
        self._total = total
        self._fixed = fixed
        self._flexible = flexible
        self._native = native
        self._unit_of_measurement = coin
        self._native_balance = { "total" : {}, "fixed": {}, "flexible": {} }
        
        super().__init__(
            coordinator = coordinator, 
            name = f"{name} {coin} Savings"
        )        
        

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
            ATTR_FIXED: "{:.8f}".format(float(self._fixed)),
            ATTR_FLEXIBLE: "{:.8f}".format(float(self._flexible)),
            ATTR_TOTAL: "{:.8f}".format(float(self._total)),
        }
        
        for typ, native in self._native_balance.items():
            for asset, exchange in native.items(): 
                data[f"Native {typ} savings in {asset}"] = exchange
         
        return data

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update current values."""
        
        self._total = self.coordinator.savings[f"totalAmountIn{self._coin}"]
        self._fixed = self.coordinator.savings[f"totalFixedAmountIn{self._coin}"]
        self._flexible = self.coordinator.savings[f"totalFlexibleIn{self._coin}"]
        self._state = self._total
                        
        if self._native:
            for native in self._native:
                for ticker in self.coordinator.tickers:
            
                    if ticker["symbol"] == self._coin + native.upper():
                        self._native_balance["total"][native] = "{:.2f}".format(float(ticker["price"]) * float(self._total))
                        self._native_balance["fixed"][native] = "{:.2f}".format(float(ticker["price"]) * float(self._fixed))
                        self._native_balance["flexible"][native] = "{:.2f}".format(float(ticker["price"]) * float(self._flexible))
                    
                        break
                    
                    if ticker["symbol"] == native.upper() + self._coin:      
                        self._native_balance["total"][native] = "{:.8f}".format(float(self._total) / float(ticker["price"]))
                        self._native_balance["fixed"][native] = "{:.8f}".format(float(self._fixed) / float(ticker["price"]))
                        self._native_balance["flexible"][native] = "{:.8f}".format(float(self._flexible) / float(ticker["price"]))
                    
                        break

        self.async_write_ha_state()

class BinanceExchangeSensor(BinanceSensorEntity):
    """Representation of a Sensor."""

    def __init__(self, coordinator, name, symbol, price):
        """Initialize the sensor."""
        self._symbol = symbol
        self._price = price
        self._unit_of_measurement = None

        super().__init__(
            coordinator = coordinator, 
            name = f"{name} {symbol} Exchange"
        )

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement this sensor expresses itself in."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return EXCHANGES_ICON

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""

        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update current values."""
        
        symbols = {}
        for coin1 in self.coordinator.balances:
            for coin2 in self.coordinator.balances:
                if coin1["coin"] == coin2["coin"]: 
                    continue
                    
                symbol = "{}{}".format(coin1["coin"], coin2["coin"]).upper()
                
                if symbol not in symbols:
                    symbols[symbol] = coin2["coin"]
                
                
        for ticker in self.coordinator.tickers:
            if ticker["symbol"] == self._symbol:
                self._state = float(ticker["price"])
                
                symbol = ticker["symbol"].upper()
                if symbol in symbols:
                    self._unit_of_measurement = symbols[symbol]

                break

   
        self.async_write_ha_state()
        
class BinanceWorkerSensor(BinanceSensorEntity):
    """Representation of a Sensor."""

    def __init__(self, coordinator, name, account, algorithm, worker, status, hrate, hrate_daily, reject, update):
        """Initialize the sensor."""
        self._account = account
        self._algorithm = algorithm
        self._worker = worker
        self._status = status
        self._hrate = hrate
        self._hrate_daily = hrate_daily
        self._reject = reject
        self._update = update
        self._unit_of_measurement = "H/s"        
        
        self._status_vars = ["unknown", "valid", "invalid", "inactive"]
        self._status_icons = ["mdi:sync-off", "mdi:server-network", "mdi:server-network-off", "mdi:power-plug-off"]
        
        super().__init__(
            coordinator = coordinator, 
            name = f"{name} {account}.{worker} ({algorithm}) worker"
        )        

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement this sensor expresses itself in."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        
        try:
            return self._status_icons[self._status]
        except KeyError:
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
        except KeyError:
            data[ATTR_WORKER_STATUS] = "unknown"
        
        return data
        
    @callback        
    def _handle_coordinator_update(self) -> None:
        """Update current values."""

        exists = False
                
        for account, algos in self.coordinator.mining.items():
            if account != self._account:
                continue
                
            for algo, typ in algos.items():
                if algo != self._algorithm or "workers" not in typ:
                    continue
                
                for worker in typ["workers"]:
                    if worker["workerName"] != self._worker:
                        continue
                    
                    exists = True
                        
                    self._status = worker["status"]
                    self._hrate = worker["hashRate"]
                    self._hrate_daily = worker["dayHashRate"]
                    self._reject = worker["rejectRate"]
                    self._update = worker["lastShareTime"]

                    self._state = self._hrate
    
                    break                
                if exists:
                    break
        
            if exists:
                break
                            
        if not exists:
            self._state = None 
          
        self.async_write_ha_state()          
            
class BinanceStatusSensor(BinanceSensorEntity):
    """Representation of a Sensor."""

    def __init__(self, coordinator, name, account, algorithm, hrate_15min, hrate_day, validNum, invalidNum, unknown, invalid, inactive):
        """Initialize the sensor."""
        self._account = account
        self._algorithm = algorithm
        self._hrate15m = hrate_15min
        self._hrate24h = hrate_day
        self._valid_workers = validNum
        self._total_alerts = invalidNum
        self._unknown_workers = unknown
        self._invalid_workers = invalid
        self._inactive_workers = inactive
        self._unit_of_measurement = "H/s"        

        self._status_vars = ["unknown", "valid", "invalid", "inactive"]
        
        super().__init__(
            coordinator = coordinator, 
            name = f"{name} {account} ({algorithm}) status"
        )        

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement this sensor expresses itself in."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return STATUS_ICON
    
    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""

        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            ATTR_STATUS_HRATE15M: f"{self._hrate15m}",
            ATTR_STATUS_HRATE24H: f"{self._hrate24h}",
            ATTR_STATUS_VALID_WORKERS: f"{self._valid_workers}",
            ATTR_STATUS_TOTAL_ALERTS: f"{self._total_alerts}",    
            ATTR_STATUS_UNKNOWN_WORKERS: f"{self._unknown_workers}",
            ATTR_STATUS_INVALID_WORKERS: f"{self._invalid_workers}",
            ATTR_STATUS_INACTIVE_WORKERS: f"{self._inactive_workers}",
            ATTR_ACCOUNT: f"{self._account}",
            ATTR_ALGO: f"{self._algorithm}",
        }
        
    @callback        
    def _handle_coordinator_update(self) -> None:
        """Update current values."""
        exists = False

        for account, algos in self.coordinator.mining.items():
            if account != self._account:
                continue
                
            for algo, typ in algos.items():
                if algo != self._algorithm or "status" not in typ:
                    continue

                exists = True
                
                self._hrate15m = typ["status"].get("fifteenMinHashRate", 0)
                self._hrate24h = typ["status"].get("dayHashRate", 0)
                self._valid_workers = typ["status"]["validNum"]
                self._total_alerts = typ["status"]["invalidNum"]
                
                self._state = self._hrate15m
                
                unknown = invalid = inactive = 0 
                
                if "workers" in typ:
                    for worker in typ["workers"]:
                        if worker["status"] == 0:
                            unknown += 1
                        elif worker["status"] == 2:
                            invalid += 1
                        elif worker["status"] == 3:
                            inactive += 1

                    self._unknown_workers = unknown
                    self._invalid_workers = invalid
                    self._inactive_workers = inactive

                break
            
            if exists:
                break
                
        if not exists:
            self._state = 0
          
          
        self.async_write_ha_state()
                    
class BinanceProfitSensor(BinanceSensorEntity):
    """Representation of a Sensor."""

    def __init__(self, coordinator, wallet, name, account, algorithm, coin, estimate, earnings, native = []):
        """Initialize the sensor."""
        self._account = account
        self._algorithm = algorithm
        self._coin = coin
        self._estimate = estimate
        self._earnings = earnings
        self._unit_of_measurement = f"{coin}"        
        self._native = native
        self._native_earnings = {}
        self._native_estimate = {}
        self._wallet = wallet
        
        super().__init__(
            coordinator = coordinator, 
            name = f"{name} {account} ({algorithm}) {coin} profit"
        )        
        
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
            ATTR_PROFIT_ESTIMATE: f"{self._estimate}",
            ATTR_PROFIT_EARNINGS: f"{self._earnings}",
            ATTR_COIN: f"{self._coin}",
            ATTR_ACCOUNT: f"{self._account}",
            ATTR_ALGO: f"{self._algorithm}",
        }
        
        if self._native_earnings:
            for asset, exchange in self._native_earnings.items():
                data[f"Native earnings in {asset}"] = exchange        
                
        if self._native_estimate:                
            for asset, exchange in self._native_estimate.items():
                data[f"Native estimate in {asset}"] = exchange            
        
        return data
        
    @callback        
    def _handle_coordinator_update(self) -> None:
        """Update current values."""

        exists = False
                
        for account, algos in self.coordinator.mining.items():
            if account != self._account:
                continue
                
            for algo, typ in algos.items():
                if algo != self._algorithm or "status" not in typ:
                    continue
                
                
                for coindata in self.coordinator.coins:
                    coin = coindata["coinName"]
                    
                    if coin != self._coin:
                        continue

                    estimate = typ["status"].get("profitToday", {})
                    earnings = typ["status"].get("profitYesterday", {})

                    old_estimate = self._estimate
                    old_earnings = self._earnings
                    new_estimate = 0.00
                    new_earnings = 0.00
                                            
                    exists = True
                                            
                    if coin in estimate:
                        new_estimate = estimate[coin]
                    else:
                        new_estimate = 0.00

                    if coin in earnings:
                        new_earnings = earnings[coin]   
                    
                    elif float(old_earnings) > 0: 
                        new_earnings = old_earnings
                        
                        if float(old_estimate) > 0 and float(new_estimate) == 0:
                            new_earnings = old_estimate
                        
                    else:
                        new_earnings = 0.00
                       

                    self._estimate = new_estimate
                    self._earnings = new_earnings
                    self._state = float(self._earnings)

                    if self._native:
                        for native in self._native: 
                            for ticker in self._wallet.tickers:
                                if ticker["symbol"] == self._coin + native.upper():
                                    self._native_estimate[native] = float("{:.8f}".format(float(ticker["price"]) * float(self._estimate)))
                            
                                    break
                                
                                if ticker["symbol"] == native.upper() + self._coin:      
                                    self._native_estimate[native] = "{:.8f}".format(float(self._estimate) / float(ticker["price"]))
                            
                                    break 

                    if self._native:
                        for native in self._native: 
                            for ticker in self._wallet.tickers:
                                if ticker["symbol"] == self._coin + native.upper():
                                    self._native_earnings[native] = "{:.8f}".format(float(ticker["price"]) * float(self._earnings))
                            
                                    break
                                
                                if ticker["symbol"] == native.upper() + self._coin:      
                                    self._native_earnings[native] = "{:.8f}".format(float(self._earnings) / float(ticker["price"]))
                            
                                    break 

                    break   
                
                if exists:
                    break
        
            if exists:
                break
                            
        if not exists:
            self._state = None   
            
        self.async_write_ha_state()