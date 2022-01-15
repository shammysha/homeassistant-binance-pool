# homeassistant-binance-pool

Project based on https://github.com/drinfernoo/homeassistant-binance

Added pool monitoring functionality

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

# Binance

### Installation with HACS
---
- Make sure that [HACS](https://hacs.xyz/) is installed
- Add the URL for this repository as a [custom repository](https://hacs.xyz/docs/faq/custom_repositories) in HACS
- Install via `HACS -> Integrations`

### Usage
---
In order to use this integration, you need to first [Register an account with Binance](https://accounts.binance.com/en/register), and then [generate an API key](https://www.binance.com/en/my/settings/api-management) from the "API Management" settings section.

To use this component in your installation, add the following to your `configuration.yaml` file:

```yaml
binance:
  api_key: !secret binance_api_key
  api_secret: !secret binance_api_secret
```

#### Configuration variables:
| Key               | Type   | Required | Description                            | Default |
| :---------------- | :----: | :------: |:-------------------------------------- | :-----: |
| `name`            | string | No       | Name for the created sensors           | Binance |
| `domain`          | string | No       | Binance domain to query                | us      |
| `native_currency` | string | No       | Native currency for price calculations | USD     |
| `api_key`         | string | Yes      | Binance API key                        | -       |
| `api_secret`      | string | Yes      | Binance API secret                     | -       |
| `balances`        | array  | No       | List of coins for wallet balances      | -       |
| `exchanges`       | array  | No       | List of pairs for exchange rates       | -       |
| `miners`          | array  | No       | List of pool accounts                  | -       |

#### Full example configuration
```yaml
binance_pool:
  name: My Binance
  domain: us
  native_currency: USD
  api_key: !secret binance_api_key
  api_secret: !secret binance_api_secret
  balances:
    - USD
    - BTC
    - ETH
  exchanges:
    - BTCUSC
    - ETHUSD
  miners:
    - account
```

This configuration will create the following entities in your Home Assistant instance:
- My Binance USD Balance (`sensor.my_binance_usd_balance`)
- My Binance BTC Balance (`sensor.my_binance_btc_balance`)
- My Binance ETH Balance (`sensor.my_binance_eth_balance`)
- My Binance BTCUSD Exchange (`sensor.my_binance_btcusd_exchange`)
- My Binance ETHUSD Exchange (`sensor.my_binance_ethusd_exchange`)
- Earnings sensors for each bundle (account + algo + coin), as example:
  - "My Binance account (sha256) BTC profit" (`sensor.my_binance_account_sha256_btc_profit`)
- Status sensors for each bundle (account + algo), as example:
  - "My Binance account (ethash) status" (`sensor.my_binance_account_ethash_status`)
- Worker's sensors for each bundle (account + algo + worker)> as example
  - "My Binance account.1023 (scrypt) worker" (`sensor.my_binance_account_1023_scrypt_worker`)

### Configuration details
---

#### `name`
The `name` you specify will be used as a prefix for all the sensors this integration creates. By default, the prefix is simply "Binance".

#### `domain`
This integration is set up to query [Binance.us](https://www.binance.us/) by default. If you've registered your Binance account with a different domain, like [Binance.com](https://www.binance.com/), make sure to set this key in your configuration accordingly.

#### `api_key` and `api_secret`
An API key and secret from Binance are **required** for this integration to function.  It is *highly recommended* to store your API key and secret in Home Assistant's `secrets.yaml` file.

#### `native_currency`
Each balance sensor this integration creates will have a state attribute named `native_balance`, which represents the current value of the represented balance, converted to the currency specified by `native_currency`. The default native currency used for balance conversions is USD.

#### `balances`
A list of coins (or currencies) can be specified here, and this integration will create a sensor for your current balance in each of them. By default (without adding this key), a sensor will be created for every coin that Binance offers (54 unique coins/currencies from Binance.us at this time). If one of the given coins isn't available from the specified domain, a sensor won't be created.

#### `exchanges`
A list of exchange pairs can be specified here, and this integration will create a sensor for the current exchange rate between each of them. By default (without adding this key), a sensor will be created for every exchange pair that Binance offers (109 pairs from Binance.us at this time). If one of the given pairs isn't available from the specified domain, a sensor won't be created.

#### `miners`
A list of pool accounts can be specified here

### Example Lovelace card
---
![alt text](https://raw.githubusercontent.com/drinfernoo/homeassistant-binance/master/screenshots/example_card.png "Example Card")
```yaml
type: vertical-stack
cards:
  - type: entities
    entities:
      - entity: sensor.binance_vet_balance
        type: 'custom:multiple-entity-row'
        name: Cardano Balance
        secondary_info:
          attribute: native_balance
      - entity: sensor.binance_doge_balance
        type: 'custom:multiple-entity-row'
        name: Dogecoin Balance
        secondary_info:
          attribute: native_balance
  - type: horizontal-stack
    cards:
      - type: 'custom:mini-graph-card'
        entities:
          - entity: sensor.binance_vetusd_exchange
            name: VET/USD
        smoothing: false
        decimals: 7
        points_per_hour: 12
        hours_to_show: 8
        show:
          fill: fade
          extrema: true
      - type: 'custom:mini-graph-card'
        entities:
          - entity: sensor.binance_dogeusd_exchange
            name: DOGE/USD
        smoothing: false
        decimals: 7
        points_per_hour: 12
        hours_to_show: 8
        show:
          fill: fade
          extrema: true
```
