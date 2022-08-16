# homeassistant-binance-pool

Project originally was forked from https://github.com/drinfernoo/homeassistant-binance

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

To use this component add new integration via HomeAssistant GUI or add the following to your `configuration.yaml` file: 

```yaml
binance_pool:
  - name: Binance 
  	api_key: !secret binance_api_key
  	api_secret: !secret binance_api_secret
```

#### Configuration variables:
| Key               | Type   | Required | Description                               | Default          |
| :---------------- | :----: | :------: |:--------------------------------------    | :-----:          |
| `name`            | string | yes      | Name for the created sensors              | Binance          |
| `domain`          | string | No       | Binance domain to query                   | us               |
| `native_currency` | array  | No       | List of currencies for price calculations | USDT             |
| `api_key`         | string | Yes      | Binance API key                           | -                |
| `api_secret`      | string | Yes      | Binance API secret                        | -                |
| `balances`        | array  | No       | List of coins for wallet balances         | BTC,ETH          |
| `exchanges`       | array  | No       | List of pairs for exchange rates          | BTCUSDT,ETHUSDT  |
| `miners`          | array  | No       | List of pool accounts                     | -                |

#### Full example configuration
```yaml
binance_pool:
  - name: My Binance
    domain: us
    api_key: !secret binance_api_key
    api_secret: !secret binance_api_secret
    native_currency: 
      - USD
    balances:
      - USDT
      - BTC
      - ETH
    exchanges:
      - BTCUSDT
      - ETHUSDT
    miners:
      - account
```

This configuration will create the following entities in your Home Assistant instance:
- My Binance USDT Balance (`sensor.my_binance_usdt_balance`)
- My Binance BTC Balance (`sensor.my_binance_btc_balance`)
- My Binance ETH Balance (`sensor.my_binance_eth_balance`)
- My Binance USDT Funding Balance (`sensor.my_binance_usdt_funding`)
- My Binance BTC Funding Balance (`sensor.my_binance_btc_funding`)
- My Binance ETH Funding Balance (`sensor.my_binance_eth_funding`)
- My Binance USDT Savings Balance (`sensor.my_binance_usdt_savings`)
- My Binance BTC Savings Balance (`sensor.my_binance_btc_savings`)
- My Binance BTCUSD Exchange (`sensor.my_binance_btcusdt_exchange`)
- My Binance ETHUSD Exchange (`sensor.my_binance_ethusdt_exchange`)
- Earnings sensors for each bundle (account + algo + coin), as example:
  - "My Binance account (sha256) BTC profit" (`sensor.my_binance_account_sha256_btc_profit`)
- Status sensors for each bundle (account + algo), as example:
  - "My Binance account (ethash) status" (`sensor.my_binance_account_ethash_status`)
- Worker's sensors for each bundle (account + algo + worker)> as example
  - "My Binance account.1023 (scrypt) worker" (`sensor.my_binance_account_1023_scrypt_worker`)

### Configuration details
---

#### `name`
The `name` you specify will be used as a prefix for all the sensors this integration creates. By default, the prefix is simply "Binance". Must be unique for each intergation

#### `domain`
This integration is set up to query [Binance.us](https://www.binance.us/) by default. If you've registered your Binance account with a different domain, like [Binance.com](https://www.binance.com/), make sure to set this key in your configuration accordingly.

#### `api_key` and `api_secret`
An API key and secret from Binance are **required** for this integration to function.  It is *highly recommended* to store your API key and secret in Home Assistant's `secrets.yaml` file.

#### `native_currency`
Each balance sensor this integration creates will have a state attributes, which represents pairs ("total", "free", "locked", "freeze") and list of `native_currency` items. The default native currency used for balance conversions is USD.

#### `balances`
A list of coins (or currencies) can be specified here, and this integration will create a sensor for your current balance in each of them. By default (without adding this key), a sensor will be created for every coin that Binance offers (54 unique coins/currencies from Binance.us at this time). If one of the given coins isn't available from the specified domain, a sensor won't be created.

#### `exchanges`
A list of exchange pairs can be specified here, and this integration will create a sensor for the current exchange rate between each of them. By default (without adding this key), a sensor will be created for every exchange pair that Binance offers (109 pairs from Binance.us at this time). If one of the given pairs isn't available from the specified domain, a sensor won't be created.

#### `miners`
A list of pool accounts can be specified here

### Example Lovelace card
---

![card](https://user-images.githubusercontent.com/65885873/149904873-d5cbf8b2-a69f-46be-bcdc-05b4133f6912.png)


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
            name: BTC
            unit: BTC
            type: custom:multiple-entity-row
            attribute: total
            styles:
              font-weight: bold
              font-size: 120%
            secondary_info:
              type: attribute
              attribute: Native total balance in USDT
              unit: USDT
              name: false
          - entity: sensor.my_binance_btc_balance
            type: custom:multiple-entity-row
            name: false
            icon: mdi:none
            show_state: false
            entities:
              - entity: sensor.my_binance_btc_balance
                name: Free
                type: attribute
                attribute: free
              - entity: sensor.my_binance_btc_balance
                name: Freeze
                type: attribute
                attribute: freeze
              - entity: sensor.my_binance_btc_balance
                name: Locked
                type: attribute
                attribute: locked
          - type: divider
          - entity: sensor.my_binance_usdt_balance
            name: USDT
            unit: USDT
            type: custom:multiple-entity-row
            attribute: total
            styles:
              font-weight: bold
              font-size: 120%
          - entity: sensor.my_binance_usdt_balance
            type: custom:multiple-entity-row
            name: false
            icon: mdi:none
            show_state: false
            entities:
              - entity: sensor.my_binance_usdt_balance
                name: Free
                type: attribute
                attribute: free
              - entity: sensor.my_binance_usdt_balance
                name: Freeze
                type: attribute
                attribute: freeze
              - entity: sensor.my_binance_usdt_balance
                name: Locked
                type: attribute
                attribute: locked
  - type: custom:apexcharts-card
    graph_span: 3d
    header:
      show: true
      title: Exchange
      standard_format: true
      show_states: true
    show:
      last_updated: true
    now:
      show: true
    all_series_config:
      curve: smooth
      type: line
      stroke_width: 1
      show:
        extremas: true
    series:
      - entity: sensor.my_binance_btcusdt_exchange
        name: 1 BTC
        unit: ' USDT'
  - type: custom:layout-break
  - type: custom:vertical-stack-in-card
    title: Pool
    cards:
      - type: entities
        entities:
          - entity: sensor.my_binance_account_sha256_status
            name: Valid workers
            type: custom:multiple-entity-row
            attribute: valid workers
            icon: mdi:server-network
            styles:
              font-weight: bold
              font-size: 120%
          - entity: sensor.my_binance_account_sha256_status
            type: custom:multiple-entity-row
            attribute: Workers with alerts
            icon: mdi:server-network-off
            name: false
            show_state: false
            styles:
              font-weight: bold
              font-size: 120%
            entities:
              - entity: sensor.my_binance_account_sha256_status
                name: Invalid
                type: attribute
                attribute: invalid workers
              - entity: sensor.my_binance_account_sha256_status
                name: Inactive
                type: attribute
                attribute: inactive workers
              - entity: sensor.my_binance_account_sha256_status
                name: Unavailable
                type: attribute
                attribute: unknown workers
          - type: divider
          - entity: sensor.my_binance_account_sha256_btc_profit
            name: Yesterday earnings
            unit: BTC
            type: custom:multiple-entity-row
            attribute: yesterday's earnings
            styles:
              font-weight: bold
              font-size: 120%
            secondary_info:
              type: attribute
              attribute: Native earnings in USDT
              unit: USDT
              name: false
              format: precision2
          - entity: sensor.my_binance_account_sha256_btc_profit
            name: Estimated profit
            unit: BTC
            type: custom:multiple-entity-row
            attribute: estimated profit
            styles:
              font-weight: bold
              font-size: 120%
            secondary_info:
              type: attribute
              attribute: Native estimate in USDT
              unit: USDT
              name: false
              format: precision2
  - type: custom:apexcharts-card
    graph_span: 1d
    header:
      show: true
      title: Workers
      standard_format: true
      show_states: true
    show:
      last_updated: true
    now:
      show: true
    all_series_config:
      curve: smooth
      type: line
      stroke_width: 1
      fill_raw: last
      group_by:
        func: avg
        duration: 15min
        fill: last        
      show:
        in_header: false
        extremas: false
    series:
      - entity: sensor.my_binance_account_002_sha256_worker
        name: '002'
        transform: return x / 10**12
        unit: ' TH/s'        
      - entity: sensor.my_binance_account_003_sha256_worker
        name: '003'
        transform: return x / 10**12
        unit: ' TH/s'        
      - entity: sensor.my_binance_account_005_sha256_worker
        name: '005'
        transform: return x / 10**12
        unit: ' TH/s'        
      - entity: sensor.my_binance_account_006_sha256_worker
        name: '006'
        transform: return x / 10**12
        unit: ' TH/s'        
      - entity: sensor.my_binance_account_007_sha256_worker
        name: '007'
        transform: return x / 10**12
        unit: ' TH/s'        
      - entity: sensor.my_binance_account_10x5x18x7_sha256_worker
        name: 10x5x18x7
        transform: return x / 10**12
        unit: ' TH/s'        
      - entity: sensor.my_binance_account_10x5x18x8_sha256_worker
        name: 10x5x18x8
        transform: return x / 10**12
        unit: ' TH/s'        
      - entity: sensor.my_binance_account_sha256_status
        name: Average (15m)
        attribute: average hashrate (15 mins)
        transform: return x / 10**12
        unit: ' TH/s'
        show:
          in_header: true
          in_chart: false
        group_by:
          func: raw          
      - entity: sensor.my_binance_account_sha256_status
        name: Average (24h)
        attribute: average hashrate (24 hours)
        transform: return x / 10**12
        unit: ' TH/s'
        show:
          in_header: true
          in_chart: false
        group_by:
          func: raw          
    apex_config:
      toolbar:
        followCursor: false
      legend:
        horizontalAlign: left
```

## Donate

if You like this component - feel free to donate me

* BTC: 1ALWfyhkniqZjLzckS2GDKmQXvEnzvDfth 
* ETH: 0xef89238d7a30694041e64e31b7991344e618923f
* LTC: LeHu1RaJhjH6bsoiqtEwZoZg6K6qeorsRf
* USDT: TFLt756zrKRFcvhSkjSWaXkfEzhv2M55YN
