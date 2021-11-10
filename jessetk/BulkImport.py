import csv
import os
import threading
from datetime import datetime
from io import BytesIO
from multiprocessing.pool import ThreadPool
from timeit import default_timer as timer
from urllib.request import urlopen
from zipfile import ZipFile
from jesse.models import Candle

import arrow
import jesse.helpers as jh
from jesse.services.db import store_candles


class Bulk:
    def __init__(self, exchange: str, symbol: str, market_type: str) -> None:
        self.exchange = exchange
        self.symbol = symbol  # Pair to download
        self.sym = jh.dashless_symbol(self.symbol)
        self.market_type = market_type  # spot, futures
        # Futures: klines, premiumIndexKlines, markPriceKlines, indexPriceKlines
        self.data_type = 'klines'
        # Spot: klines
        self.margin_type = 'um'  # um, cm (Usdt margin, coin margin)
        self.mt = None  # combined market type string for usdt margin and coin margin types -> futures/um - futures/cm
        self.tf = '1m'  # timeframe
        self.period = 'monthly'  # monthly, daily
        self.count = 1000,
        self.endpoint = None
        self.timer_start = None
        self.base_url = 'https://data.binance.vision/data/spot/'  # Takeover this name
        self.base_url2 = 'https://data.binance.vision/data/'

        self.base_folder = './data/'
        self.zip_folder = f'{self.base_folder}zip/'
        self.csv_folder = f'{self.base_folder}csv/'

        os.makedirs(self.base_folder, exist_ok=True)
        # os.makedirs(self.zip_folder, exist_ok=True)
        # os.makedirs(self.csv_folder, exist_ok=True)

    def get_endpoint(self, symbol: str, date: str) -> str:
        symbol = jh.dashless_symbol(symbol)
        return f'{self.base_url}{self.period}/klines/{symbol}/1m/{symbol}-1m-{date}.zip'

    def get_months(self, start, end):
        months = []
        for d in arrow.Arrow.range('week', start, end):
            m = d.strftime("%Y-%m")
            if m not in months:
                months.append(m)
        return months

    def get_days(self, start, end) -> list:
        days = []
        for d in arrow.Arrow.range('day', start, end):
            day_str = d.strftime("%Y-%m-%d")
            if day_str not in days:
                days.append(day_str)
        return days

    def download_extract(self, url):
        fn = url.split('/')[-1].replace('.zip', '.csv')
        folder_name = f'{self.base_folder}{self.mt}/{self.period}/{self.data_type}/{self.sym}/{self.tf}/'
        os.makedirs(folder_name, exist_ok=True)

        # skip download if fn exits in archive folder
        if os.path.exists(folder_name + fn) or os.path.isfile(folder_name + fn):
            print('Skipping download', fn, 'already exists.')
            # return None
        else:
            try:
                http_response = urlopen(url)
                zipfile = ZipFile(BytesIO(http_response.read()))
                zipfile.extractall(path=folder_name)
                print('Downloading', fn)
            except Exception as e:
                # print e in orange color
                print('\033[33m', e, fn, '\033[0m')
                return None

        r_fn = folder_name + fn
        file_size = os.stat(r_fn).st_size

        if file_size <= 0:
            print(f'{r_fn} failed to download and extract. Size: {file_size} bytes.')
            return None
        else:
            candles = self.extract_ohlc(r_fn)
            if not candles:
                print(f'{r_fn} failed to extract.')
                exit()
                
            if self.tf == '1m':
                # threading.Thread(target=store_candles, args=[candles]).start()
                temp_start_timestamp = candles[0]['timestamp']
                temp_end_timestamp = candles[-1]['timestamp']
                
                # prevent duplicates calls to boost performance
                count = Candle.select().where(
                    Candle.timestamp.between(temp_start_timestamp, temp_end_timestamp),
                    Candle.symbol == self.symbol,
                    Candle.exchange == self.exchange
                ).count()
                already_exists = count == len(candles)
                
                
                if not already_exists:
                    # print in yellow
                    print(f'\033[1;33mDEBUG: {temp_start_timestamp}, {temp_end_timestamp}, count {count}, len(csv) {len(candles)}\033[0m')
                    
                    print(f'\033[1;34mSaving to db: {r_fn} Size: {file_size} bytes, {len(candles)} datapoints.', 'time passed:',
                      round(timer() - self.timer_start), 'seconds.\033[0m')
                    try:
                        store_candles(candles)
                    except KeyboardInterrupt:
                        print('KeyboardInterrupt')
                        exit()
                else:
                    print(f'\033[92mCandles already exits in DB skipping {r_fn}\033[0m')
            else:
                # print 'Warning' in red
                print(f'\033[91mWarning: Jesse stores only 1m candles!, your current timeframe is: {self.tf}.\033[0m')

        return folder_name + fn

    def run_threading_download_unzip(self, urls):
        # Run multiple threads. Each call will take the next element in urls list
        results = ThreadPool(8).imap_unordered(self.download_extract, urls)

        for r in results:  # TODO get rid of this loop
            if r:
                pass

    def extract_ohlc(self, fn):

        with open(fn, newline='') as csvfile:
            data = csv.reader(csvfile, delimiter=',', quotechar="'")
            print(f'DEBUG: self.exchange {self.exchange}, self.symbol {self.symbol}')
            
            return [{
                'id': jh.generate_unique_id(),
                'symbol': self.symbol,
                'exchange': self.exchange,
                'timestamp': int(d[0]),
                'open': float(d[1]),
                'close': float(d[4]),
                'high': float(d[2]),
                'low': float(d[3]),
                'volume': float(d[5])
            } for d in data]

    def make_urls(self, date_list):
        urls = []
        checksum_urls = []

        if self.margin_type and self.market_type != 'spot':
            self.mt = self.market_type + '/' + self.margin_type
        else:
            self.mt = self.market_type

        for m in date_list:
            urls.append(
                f'{self.base_url2}{self.mt}/{self.period}/{self.data_type}/{self.sym}/{self.tf}/{self.sym}-{self.tf}-{m}.zip')
            checksum_urls.append(urls[-1] + '.CHECKSUM')
        return urls, checksum_urls
