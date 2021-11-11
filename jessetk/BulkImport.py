import csv
import os
from io import BytesIO
from multiprocessing.pool import ThreadPool
from timeit import default_timer as timer
from urllib.request import urlopen
from zipfile import ZipFile

from arrow import Arrow
import jesse.helpers as jh
from jesse.models import Candle
from jesse.services.db import store_candles

from pathlib import Path
import platform
import tempfile


def get_months(start, end) -> list:
    months = []
    for m in Arrow.range('week', start, end):
        m_str = m.strftime("%Y-%m")
        if m_str not in months:
            months.append(m_str)
    return months


def get_days(start, end) -> list:
    days = []
    for d in Arrow.range('day', start, end):
        d_str = d.strftime("%Y-%m-%d")
        if d_str not in days:
            days.append(d_str)
    return days

def is_exist(file_name):
    return os.path.exists(file_name) or os.path.isfile(file_name)

class Bulk:
    def __init__(self, exchange: str, symbol: str, market_type: str) -> None:
        self.exchange = exchange
        self.symbol = symbol  # Pair to download
        self.sym = jh.dashless_symbol(self.symbol)
        self.market_type = market_type  # spot, futures

        self.data_type = 'klines'
        # Spot: klines
        # Futures: klines, premiumIndexKlines, markPriceKlines, indexPriceKlines

        self.margin_type = 'um'  # um, cm (Usdt margin, coin margin)
        self.mt = None  # combined market type string for usdt margin and coin margin types
                        # -> futures/um - futures/cm

        self.tf = '1m'  # timeframe
        self.period = 'monthly'  # monthly, daily

        self.timer_start = None
        self.base_url = 'https://data.binance.vision/data/spot/'  # Takeover this name
        self.base_url2 = 'https://data.binance.vision/data/'

        # not tested on *nix & macos
        temp_dir = Path("/tmp" if platform.system() == "Darwin" else tempfile.gettempdir())
        print('\033[1m', '\033[37m', 'temp_dir', temp_dir, '\033[0m')
        
        self.base_folder = str(temp_dir) + '/bulkdata/'
        self.zip_folder = f'{self.base_folder}zip/'
        self.csv_folder = f'{self.base_folder}csv/'

        os.makedirs(self.base_folder, exist_ok=True)
        # os.makedirs(self.zip_folder, exist_ok=True)
        # os.makedirs(self.csv_folder, exist_ok=True)

    def path_and_fn_from_url(self, url):
        fn = url.split('/')[-1].replace('.zip', '.csv')
        folder_name = f'{self.base_folder}{self.mt}/{self.period}/{self.data_type}/{self.sym}/{self.tf}/'
        return fn, folder_name

    def main_func_to_rename(self, url):
        fn, folder_name = self.path_and_fn_from_url(url)
        r_fn = folder_name + fn
        os.makedirs(folder_name, exist_ok=True)

        # download if file doesn't exist
        if not is_exist(r_fn):
            try:        
                print('Downloading', fn)
                http_response = urlopen(url)
                zipfile = ZipFile(BytesIO(http_response.read()))
                zipfile.extractall(path=folder_name)
            except Exception as e:
                print('\033[33m', e, fn, '\033[0m')
                return None
        else:
            print('Skipping download', fn, 'already exists.')
        
        file_size = os.stat(r_fn).st_size

        if file_size > 0:
            candles = self.extract_ohlc(r_fn)
            if not candles:
                print(f'{r_fn} failed to extract.')
                return None

            if self.tf == '1m':
                # Get the current csv file's first and last timestamp
                temp_start_timestamp = candles[0]['timestamp']
                temp_end_timestamp = candles[-1]['timestamp']

                # prevent duplicates calls to boost performance
                count = Candle.select().where(
                    Candle.timestamp.between(
                        temp_start_timestamp, temp_end_timestamp),
                    Candle.symbol == self.symbol,
                    Candle.exchange == self.exchange
                ).count()
                # If number of candles (on db) between temp_start_timestamp and temp_end_timestamp
                # equal to current csv file's number of elements mark as already exists
                already_exists = count == len(candles)

                if not already_exists:
                    print(
                        f'\033[1;33mDEBUG: {temp_start_timestamp}, {temp_end_timestamp}, count {count}, len(csv) {len(candles)}\033[0m')

                    print(f'\033[1;34mSaving to db: {r_fn} Size: {file_size} bytes, {len(candles)} datapoints.',
                          'time passed:',
                          round(timer() - self.timer_start), 'seconds.\033[0m')
                    try:
                        store_candles(candles)
                    except KeyboardInterrupt:
                        print('KeyboardInterrupt')
                        exit()
                    except Exception as e:
                        print('\033[33m', e, '\033[0m')
                        return None
                else:
                    print(
                        f'\033[92mCandles already exits in DB skipping {r_fn}\033[0m')
            else:
                print(
                    f'\033[91mWarning: Jesse stores only 1m candles!, your current timeframe is: {self.tf}.\033[0m')
        else:
            print(f'{r_fn} failed to download and extract. Size: {file_size} bytes.')
            return None
            
            # return None
        return folder_name + fn

    def run_threading_download_unzip(self, urls):
        # Run multiple threads. Each call will take the next element in urls list
        results = ThreadPool(4).imap_unordered(self.main_func_to_rename, urls)

        for r in results:  # TODO get rid of this loop
            if r:
                # print OK to console in green
                print('\033[92m', 'OK', '\033[0m',  r)

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
