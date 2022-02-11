# Jesse Toolkit
[![Sourcery](https://img.shields.io/badge/Sourcery-enabled-brightgreen)](https://sourcery.ai)
### Installation

You need to install the legacy version of the jesse.


#### Linux:

Use: [jesse stack installer](https://github.com/ysdede/stack-installer/blob/master/jesse-cli-ubuntu20.sh)

it will install modified version of legacy jesse cli and jesse-tk. You still need to create jesse_db manually as stated in original jesse installation document.

```console

bash <(curl -s https://raw.githubusercontent.com/ysdede/stack-installer/master/jesse-cli-ubuntu20.sh)

```
  

#### Windows:

Download and install prebuilt ta-lib from [https://www.lfd.uci.edu/~gohlke/pythonlibs/](https://www.lfd.uci.edu/~gohlke/pythonlibs/)

```console

pip install downloaded wheel file

```  

install legacy jesse cli from [https://github.com/ysdede/jesse](https://github.com/ysdede/jesse)

Clone this repository and install with pip.

```console

pip install .

```

or

```console

pip install -e git+https://github.com/ysdede/jesse-tk.git#egg=jesse-tk

```

## Usage
### jesse-tk import-routes  
CLI help explains it:
```console
Usage: jesse-tk import-routes [OPTIONS] [START_DATE]

  Import-candles for pairs listed in routes.py Enter start date "YYYY-MM-DD"
  If no start date is specified, the system will default to two days earlier.
  It's useful for executing script in a cron job to download deltas on a
  regular basis.
```
### jesse-tk bulk  
It's name is confusing, I need to change it. `bulk` helps to download candle data faster. It downloads zipped kline csv files from Binance Vision as monthly and daily packets. One disadvantage of it is packed csv files (rarely) has missing data points. Running `jesse import-candles`helps to fill gaps.  
```console
Usage: jesse-tk bulk [OPTIONS] EXCHANGE SYMBOL START_DATE

  Bulk download Binance candles Enter EXCHANGE SYMBOL START_DATE { Optional: --workers n}

  jesse-tk bulk Binance btc-usdt 2020-01-01  
  jesse-tk bulk 'Binance Futures' btc-usdt 2020-01-01

  You can use spot or futures keywords instead of full exchange name.

  jesse-tk bulk spot btc-usdt 2020-01-01  
  jesse-tk bulk futures eth-usdt 2017-05-01 --workers 8

Options:
  --workers INTEGER  The number of workers to run simultaneously. You can use
                     cpu thread count or x2.  [default: 4]
```
```console
Downloading ADAUSDT-1m-2022-02-05.csv
Candles already exits in DB skipping 1440 datapoints, /tmp/bulkdata/futures/um/daily/klines/ADAUSDT/1m/ADAUSDT-1m-2022-02-01.csv
Downloading ADAUSDT-1m-2022-02-06.csv
 OK  1440 /tmp/bulkdata/futures/um/daily/klines/ADAUSDT/1m/ADAUSDT-1m-2022-02-01.csv
DEBUG: self.exchange Binance Futures, self.symbol ADA-USDT
DEBUG: 1644019200000, 1644105540000, query result: 0, datapoints: 1440
Saving to db: /tmp/bulkdata/futures/um/daily/klines/ADAUSDT/1m/ADAUSDT-1m-2022-02-05.csv Size: 152170 bytes, 1440 datapoints. time passed: 37 seconds.
DEBUG: self.exchange Binance Futures, self.symbol ADA-USDT
DEBUG: self.exchange Binance Futures, self.symbol ADA-USDT
DEBUG: 1643932800000, 1644019140000, query result: 1395, datapoints: 1440
Saving to db: /tmp/bulkdata/futures/um/daily/klines/ADAUSDT/1m/ADAUSDT-1m-2022-02-04.csv Size: 151526 bytes, 1440 datapoints. time passed: 38 seconds.
Candles already exits in DB skipping 1440 datapoints, /tmp/bulkdata/futures/um/daily/klines/ADAUSDT/1m/ADAUSDT-1m-2022-02-03.csv
 OK  1440 /tmp/bulkdata/futures/um/daily/klines/ADAUSDT/1m/ADAUSDT-1m-2022-02-03.csv
DEBUG: self.exchange Binance Futures, self.symbol ADA-USDT
Candles already exits in DB skipping 1440 datapoints, /tmp/bulkdata/futures/um/daily/klines/ADAUSDT/1m/ADAUSDT-1m-2022-02-06.csv
 OK  1440 /tmp/bulkdata/futures/um/daily/klines/ADAUSDT/1m/ADAUSDT-1m-2022-02-06.csv
 OK  1440 /tmp/bulkdata/futures/um/daily/klines/ADAUSDT/1m/ADAUSDT-1m-2022-02-04.csv
 OK  1440 /tmp/bulkdata/futures/um/daily/klines/ADAUSDT/1m/ADAUSDT-1m-2022-02-05.csv
Completed in 41 seconds.
```
  ### jesse-tk bulk-pairs  
  ```
  Usage: jesse-tk bulkpairs [OPTIONS] EXCHANGE START_DATE

  Bulk download ALL! Binance Futures candles to Jesse DB. Enter EXCHANGE START_DATE {Optional: --workers n}

  jesse-tk bulkpairs 'Binance Futures' 2020-01-01 jesse-tk bulkpairs futures 2017-05-01 -- workers 8

Options:
  --workers INTEGER  The number of workers to run simultaneously.  [default: 2]
  --all / --list     Get pairs list from api or pairs from file.
  ```
  * --all / --list: Default is list. Get candle list from user defined `pair.py`file.  
  If you add `--all`it will get pair list from exchange api. Use it with caution. It will take a long time and fill up your disk.  
  ```
  jesse-tk bulkpairs futures 2021-01-01 --workers 4 --all
There's 140 available pairs in Binance Futures:
['BTC-USDT', 'ETH-USDT', 'BCH-USDT', 'XRP-USDT', 'EOS-USDT', 'LTC-USDT', 'TRX-USDT', 'ETC-USDT', 'LINK-USDT', 'XLM-USDT', 'ADA-USDT', 'XMR-USDT', 'DASH-USDT', 'ZEC-USDT', 'XTZ-USDT', 'BNB-USDT', 'ATOM-USDT', 'ONT-USDT', 'IOTA-USDT', 'BAT-USDT', 'VET-USDT', 'NEO-USDT', 'QTUM-USDT', 'IOST-USDT', 'THETA-USDT', 'ALGO-USDT', 'ZIL-USDT', 'KNC-USDT', 'ZRX-USDT', 'COMP-USDT', 'OMG-USDT', 'DOGE-USDT', 'SXP-USDT', 'KAVA-USDT', 'BAND-USDT', 'RLC-USDT', 'WAVES-USDT', 'MKR-USDT', 'SNX-USDT', 'DOT-USDT', 'DEFI-USDT', 'YFI-USDT', 'BAL-USDT', 'CRV-USDT', 'TRB-USDT', 'YFII-USDT', 'RUNE-USDT', 'SUSHI-USDT', 'SRM-USDT', 'EGLD-USDT', 'SOL-USDT', 'ICX-USDT', 'STORJ-USDT', 'BLZ-USDT', 'UNI-USDT', 'AVAX-USDT', 'FTM-USDT', 'HNT-USDT', 'ENJ-USDT', 'FLM-USDT', 'TOMO-USDT', 'REN-USDT', 'KSM-USDT', 'NEAR-USDT', 'AAVE-USDT', 'FIL-USDT', 'RSR-USDT', 'LRC-USDT', 'MATIC-USDT', 'OCEAN-USDT', 'CVC-USDT', 'BEL-USDT', 'CTK-USDT', 'AXS-USDT', 'ALPHA-USDT', 'ZEN-USDT', 'SKL-USDT', 'GRT-USDT', '1INCH-USDT', 'AKRO-USDT', 'CHZ-USDT', 'SAND-USDT', 'ANKR-USDT', 'LUNA-USDT', 'BTS-USDT', 'LIT-USDT', 'UNFI-USDT', 'DODO-USDT', 'REEF-USDT', 'RVN-USDT', 'SFP-USDT', 'XEM-USDT', 'BTCST-USDT', 'COTI-USDT', 'CHR-USDT', 'MANA-USDT', 'ALICE-USDT', 'HBAR-USDT', 'ONE-USDT', 'LINA-USDT', 'STMX-USDT', 'DENT-USDT', 'CELR-USDT', 'HOT-USDT', 'MTL-USDT', 'OGN-USDT', 'NKN-USDT', 'SC-USDT', 'DGB-USDT', '1000SHIB-USDT', 'ICP-USDT', 'BAKE-USDT', 'GTC-USDT', 'BTCDOM-USDT', 'KEEP-USDT', 'TLM-USDT', 'IOTX-USDT', 'AUDIO-USDT', 'RAY-USDT', 'C98-USDT', 'MASK-USDT', 'ATA-USDT', 'DYDX-USDT', '1000XEC-USDT', 'GALA-USDT', 'CELO-USDT', 'AR-USDT', 'KLAY-USDT', 'ARPA-USDT', 'NU-USDT', 'CTSI-USDT', 'LPT-USDT', 'ENS-USDT', 'BTC-USDT', 'ETH-USDT', 'PEOPLE-USDT', 'ANT-USDT', 'ROSE-USDT', 'DUSK-USDT', '1000BTTC-USDT']
There's 80 available pairs in candle database at: 2021-01-01
Start: 2021-01-01 00:00:00  2022-01-01T00:00:00+00:00
  temp_dir /tmp
  ```  
  
### jesse-tk backtest
Works same as classic `jesse backtest` but it has ability to inject hyperparameters from command line. Useful for batch testing, research.
```
  --dna TEXT                      Base32 encoded dna string payload  [default:None]
  --hp TEXT                       Hyperparameters payload as dict  [default: None]
  --seq TEXT                      Fixed width hyperparameters payload [default: None]
```

* --dna: Jesse encoded dna strings. Supports only integer hyperparameters. eg. `A0@1J`
* -- hp: Hyperparameters as json/dict. eg: `{'name': 'boost', 'type': int, 'min': 0, 'max': 150, 'default': 68}`  

My favourite:
* --seq: Fixed width, zero padded hyperparameters. Last number identifies the width. eg. 730900202   
can be encoded as: 73 9 0 20 [2 is width]
Jesse-tk tools like random, refine uses seq as default input.  
If you pass seq code and  `--full-reports` at the same time tk prints seq code into quantstats reports to identify results. It has a special use case.  




see old tool [jesse-picker](https://github.com/ysdede/jesse-picker) for details.

  
  
  
  

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

  

## License

[MIT](https://choosealicense.com/licenses/mit/)
