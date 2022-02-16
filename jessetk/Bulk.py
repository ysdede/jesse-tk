import csv
import os
import platform
import tempfile
from io import BytesIO
from multiprocessing.pool import ThreadPool
from pathlib import Path
from timeit import default_timer as timer
from urllib.request import urlopen
from zipfile import ZipFile

import arrow


class Bulk:
    def __init__(self, start: str, end: str,
                 exchange: str, symbol: str,
                 tf: str = '1m',
                 market_type: str = 'futures',
                 margin_type: str = 'um',
                 data_type: str = 'klines', worker_count: int = 4) -> None:
        """Download kline, premiumIndex, trades data from Binance Vision

        Args:
            start (str): Start date
            end (str): End date
            exchange (str): Exchange name. Binance or Binance Futures
            symbol (str): Dash seperated pair symbol. eg. BTC-USDT
            tf (str, optional): Candle timeframe. Defaults to '1m'.
            market_type (str, optional): Spot or futures. Defaults to 'futures'.
            margin_type (str, optional): Futures only, um, cm (usdt margin, coin margin). Defaults to 'um'.
            data_type (str, optional): Spot: aggTrades, klines, trades
                                        Futures: aggTrades, indexPriceKlines, klines, markPriceKlines,  premiumIndexKlines, trades]. Defaults to 'klines'.
            worker_count (int, optional): Number of download jobs to run paralel. Defaults to 4.
        """

        self.timer_start = timer()
        self.start = start
        self.end = end
        self.exchange = exchange
        self.symbol = symbol
        self.sym = None
        self.market_type = market_type

        self.data_type = data_type
        self.margin_type = margin_type
        self.worker_count = worker_count
        self.mt = None  # combined market type string for usdt margin and coin margin types
        # -> futures/um - futures/cm
        self.tf = tf
        self.period = 'monthly'  # monthly, daily
        self.base_url = 'https://data.binance.vision/data/'

        # not tested on *nix & darwin
        temp_dir = Path("/tmp" if platform.system() ==
                        "Darwin" else tempfile.gettempdir())
        print('\033[1m', '\033[37m', 'temp_dir', temp_dir, '\033[0m')
        self.base_folder = str(temp_dir) + '/bulkdata/'
        os.makedirs(self.base_folder, exist_ok=True)

    def run(self):
        self.sym = self.symbol.replace('-', '')
        # Get list of months since start date
        months = get_months(self.start, self.end)

        # Get this month's days except today
        post_days = get_days(arrow.utcnow().floor('month'),
                             arrow.utcnow().floor('day').shift(days=-1))

        self.period = 'monthly'
        months_urls, months_checksum_urls = self.make_urls(months)
        self.spawn_downloaders(months_urls)

        self.period = 'daily'
        days_urls, days_checksum_urls = self.make_urls(post_days)
        self.spawn_downloaders(days_urls)

    def spawn_downloaders(self, urls):
        # Run multiple threads. Each call will take the next element in urls list
        results = ThreadPool(self.worker_count).imap_unordered(
            self.download, urls)

        for r, fn in results:  # TODO get rid of this loop
            if r and fn:
                print('\033[92m', 'OK', '\033[0m',  len(r), fn)
            elif fn:
                print('\033[91m', 'FAILED', '\033[0m', r, fn)

    def download(self, url):
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
                return None, r_fn
        else:
            print('Skipping download', fn, 'already exists.')

        if os.stat(r_fn).st_size <= 0:
            return None, r_fn

        # return csv contents as list object
        try:
            with open(r_fn, newline='') as csvfile:
                return list(csv.reader(csvfile, delimiter=',', quotechar="'")), r_fn
        except Exception as e:
            print('\033[33m', e, fn, '\033[0m')
            return None, r_fn

    def path_and_fn_from_url(self, url):
        fn = url.split('/')[-1].replace('.zip', '.csv')
        folder_name = f'{self.base_folder}{self.mt}/{self.period}/{self.data_type}/{self.sym}/{self.tf}/'
        return fn, folder_name

    def make_urls(self, date_list):
        urls = []
        checksum_urls = []

        # TODO
        if self.margin_type and self.market_type != 'spot':
            self.mt = f'{self.market_type}/{self.margin_type}'
        else:
            self.mt = self.market_type

        for m in date_list:
            if self.data_type in {'aggTrades', 'trades'}:
                urls.append(
                    f'{self.base_url}{self.mt}/{self.period}/{self.data_type}/{self.sym}/{self.sym}-{self.data_type}-{m}.zip')
            else:
                urls.append(
                    f'{self.base_url}{self.mt}/{self.period}/{self.data_type}/{self.sym}/{self.tf}/{self.sym}-{self.tf}-{m}.zip')

            checksum_urls.append(f'{urls[-1]}.CHECKSUM')
        # print(urls)
        return urls, checksum_urls


def get_months(start, end) -> list:
    return [m.strftime("%Y-%m") for m in arrow.Arrow.range('month', start, end)]


def get_days(start, end) -> list:
    return [d.strftime("%Y-%m-%d") for d in arrow.Arrow.range('day', start, end)]


def is_exist(file_name):
    return os.path.exists(file_name) or os.path.isfile(file_name)
