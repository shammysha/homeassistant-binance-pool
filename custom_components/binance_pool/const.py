DOMAIN = "binance_pool"

DEFAULT_NAME = "Binance"
DEFAULT_DOMAIN = "us"
DEFAULT_CURRENCY = [ "USDT" ]
DEFAULT_EXCHANGES = [ "BTCUSDT", "ETHUSDT" ]
DEFAULT_BALANCES = [ "BTC", "ETH" ]
CONF_API_SECRET = "api_secret"
CONF_BALANCES = "balances"
CONF_EXCHANGES = "exchanges"
CONF_MINING = "miners"
CONF_DOMAIN = "domain"
CONF_NATIVE_CURRENCY = "native_currency"

FLOW_VERSION = 5

MIN_TIME_BETWEEN_UPDATES = 1
MIN_TIME_BETWEEN_MINING_UPDATES = 5

COORDINATOR_MINING = f'mining'
COORDINATOR_WALLET = f'wallet'

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

DEFAULT_COIN_ICON = "mdi:currency-usd-circle"

ATTRIBUTION = "Data provided by Binance"
ATTR_FREE = "free"
ATTR_LOCKED = "locked"
ATTR_FREEZE = "freeze"
ATTR_WITHDRAW = "withdrawing"
ATTR_TOTAL = "total"
ATTR_NATIVE_BALANCE = "native balance"
ATTR_FLEXIBLE = "flexible"
ATTR_FIXED = "fixed"

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
ATTR_STATUS_INACTIVE_WORKERS = "inactive workers"
ATTR_STATUS_UNKNOWN_WORKERS = "unknown workers"
ATTR_STATUS_TOTAL_ALERTS = "All workers with alerts"

ATTR_PROFIT_ESTIMATE = "estimated profit"
ATTR_PROFIT_EARNINGS = "yesterday's earnings"

ATTR_ACCOUNT = "account"
ATTR_ALGO = "algorithm"
ATTR_COIN = "coin"
