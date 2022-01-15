# homeassistant-binance-pool

Project based on https://github.com/drinfernoo/homeassistant-binance

Added pool monitoring functionality

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

# Binance Pool

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
binance_pool:
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
![alt text](https://raw.githubusercontent.com/shammysha/homeassistant-binance-pool/main/card.png "Example Card")
```yaml
type: custom:layout-card
layout_type: vertical
cards:
  - type: custom:vertical-stack-in-card
    title: Wallet
    cards:
      - type: entities
        entities:
          - entity: sensor.my_binance_btc_balance
            name: BTC free
          - entity: sensor.my_binance_btc_balance
            name: BTC locked
            type: attribute
            attribute: locked
          - type: divider
          - entity: sensor.my_binance_usdt_balance
            icon: mdi:currency-usd
            name: USDT free
          - entity: sensor.my_binance_usdt_balance
            name: USDT locked
            type: attribute
            attribute: locked
            icon: mdi:currency-usd
  - type: custom:apexcharts-card
    graph_span: 4d
    header:
      show: true
      title: Exchange
      standard_format: true
      show_states: true
    now:
      show: true
      label: Now
    all_series_config:
      curve: smooth
      type: line
      stroke_width: 1
      show:
        extremas: true
    series:
      - entity: sensor.my_binance_btcusdt_exchange
  - type: custom:layout-break
  - type: custom:vertical-stack-in-card
    title: Pool
    cards:
      - type: entities
        entities:
          - entity: sensor.my_binance_account_sha256_status
            name: Workers active
            type: attribute
            attribute: valid workers
            icon: mdi:server-network
          - entity: sensor.my_binance_account_sha256_status
            name: Workers inactive
            type: attribute
            attribute: invalid workers
            icon: mdi:server-network-off
          - type: divider
          - entity: sensor.my_binance_account_sha256_btc_profit
            name: Yesterday earnings
            type: attribute
            attribute: yesterday's earnings
            icon: mdi:currency-btc
            suffix: BTC
          - entity: sensor.my_binance_account_sha256_btc_profit
            name: Estimated profit
            type: attribute
            attribute: estimated profit
            icon: mdi:currency-btc
            suffix: BTC
  - type: custom:apexcharts-card
    graph_span: 1d
    header:
      show: true
      title: Workers
      standard_format: true
      show_states: true
    now:
      show: true
      label: Now
    all_series_config:
      curve: smooth
      type: line
      stroke_width: 1
      fill_raw: zero
      show:
        in_header: false
        extremas: false
    series:
      - entity: sensor.my_binance_account_002_sha256_worker
        name: '002'
      - entity: sensor.my_binance_account_003_sha256_worker
        name: '003'
      - entity: sensor.my_binance_account_005_sha256_worker
        name: '005'
      - entity: sensor.my_binance_account_006_sha256_worker
        name: '006'
      - entity: sensor.my_binance_account_007_sha256_worker
        name: '007'
      - entity: sensor.my_binance_account_10x5x18x7_sha256_worker
        name: 10x5x18x7
      - entity: sensor.my_binance_account_10x5x18x8_sha256_worker
        name: 10x5x18x8
      - entity: sensor.my_binance_account_sha256_status
        name: 15 min average
        attribute: average hashrate (15 mins)
        transform: return x / 10**12
        unit: TH/s
        show:
          in_header: true
          in_chart: false
      - entity: sensor.my_binance_account_sha256_status
        name: 24 hour average
        attribute: average hashrate (24 hours
        transform: return x / 10**12
        unit: TH/s
        show:
          in_header: true
          in_chart: false
```
