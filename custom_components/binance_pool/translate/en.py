{
    "config": {
        "abort": {
            "already_exists": "Record with same name already exists.",
            "empty_config": "Config looks like empty.",
            "empty auth data": "Can not authorize on Binance API (empty api_key or api_secret)"
        },
        "step": {
            "user": {
                "data": {
                    "name": "Unique name for integration",
                    "api_key": "Binance API key",
                    "api_secret": "Binance API secret",
                    "domain": "Register domain"
                },
                "description": "Come up with a unique name for the integration.\n\nSpecify the domain in which the account is registered, as well as data for connecting to the Binance API.\n\nConnection data can be obtained in the profile settings ("API Management\")",
                "title": "Main Settings"
            }
        }
    },
    "options": {
        "abort": {
            "yaml_not_supported": "YAML configuration is not supported.\n\nSettings can only be changed via YAML."
        },
        "errors": {
            "invalid_input": "Input Error"
        },
        "step": {
            "init": {
                "data": {
                    "balances": "Coins to display balance",
                    "exchanges": "Exchange rates to be monitored",
                    "native_currency": "Coins for automatic conversion",
                    "mining": "Pool accounts (comma separated)"
                },
                "description": "Settings for automatically generated sensors.\n\n Default:\n\tbalances: [BTC, ETH],\n\texchanges: [BTCUSDT, ETHUSDT],\n\tnative_currency: [USDT]", 
                "title": "Sensors settings"
            }
        }
    },
    "title": "Binance Pool"
}
