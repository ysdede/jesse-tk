import os
from multiprocessing.pool import ThreadPool
from timeit import default_timer as timer

import arrow
from jesse.helpers import generate_unique_id
from jesse.models import Candle
from jesse.services.db import store_candles

from jessetk.Bulk import Bulk, get_days, get_months


class BulkJesse(Bulk):
    
    def run(self):
        self.sym = self.symbol.replace('-', '')
        self.tf = '1m'
        self.margin_type = 'um'
        self.data_type = 'klines'
        # self.worker_count = 8
        # Get list of months since start date
        months = get_months(self.start, self.end)
        # Get this month's days except today
        post_days = get_days(arrow.utcnow().floor('month'),
                             arrow.utcnow().floor('day').shift(days=-1))

        self.period = 'monthly'
        months_urls, months_checksum_urls = self.make_urls(months)
        self.spawn_workers(months_urls)

        self.period = 'daily'
        days_urls, days_checksum_urls = self.make_urls(post_days)
        self.spawn_workers(days_urls)

    def spawn_workers(self, urls):
        # Run multiple threads. Each call will take the next element in urls list
        results = ThreadPool(self.worker_count).imap_unordered(self.worker, urls)

        for r, fn in results:
            if r and fn:
                print('\033[92m', 'OK', '\033[0m',  r, fn)
            elif fn:
                print('\033[91m', 'FAILED', '\033[0m', r, fn)

    def worker(self, url):
        data, r_fn = self.download(url)

        if not data:
            return None, r_fn

        candles = self.extract_ohlc(data)

        if not candles:
            print('\033[91m', 'Failed to extract data.', '\033[0m', r_fn)
            return None, r_fn

        if self.tf != '1m':
            print('\033[91m', 'Jesse stores only 1m candles! Current tf is',
                  '\033[0m', self.tf)
            return None, r_fn

        # Get the current csv file's first and last timestamp
        start_ts = candles[0]['timestamp']
        end_ts = candles[-1]['timestamp']
        len_data = len(candles)
        file_size = os.path.getsize(r_fn)

        # prevent duplicates calls to boost performance
        count = Candle.select().where(
            Candle.timestamp.between(
                start_ts, end_ts),
            Candle.symbol == self.symbol,
            Candle.exchange == self.exchange
        ).count()

        if already_exists := count >= len_data:
            print(
                f'\033[92mCandles already exits in DB skipping {len_data} datapoints, {r_fn}\033[0m')
            return len_data, r_fn

        print(
            f'\033[1;33mDEBUG: {start_ts}, {end_ts}, query result: {count}, datapoints: {len_data}\033[0m')

        print(f'\033[1;34mSaving to db: {r_fn} Size: {file_size} bytes, {len_data} datapoints.',
              'time passed:',
              round(timer() - self.timer_start), 'seconds.\033[0m')
        try:
            store_candles(candles)
            return len_data, r_fn
        except Exception as e:
            print('\033[33m', e, '\033[0m')
            return None, r_fn

    # Extract candles data for Jesse DB
    def extract_ohlc(self, data):
        print(
            f'DEBUG: self.exchange {self.exchange}, self.symbol {self.symbol}')
        return [{
            'id': generate_unique_id(),
            'symbol': self.symbol,
            'exchange': self.exchange,
            'timestamp': int(d[0]),
            'open': float(d[1]),
            'close': float(d[4]),
            'high': float(d[2]),
            'low': float(d[3]),
            'volume': float(d[5])
        } for d in data]
