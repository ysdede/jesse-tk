import os
import random
import sys
from datetime import datetime
from datetime import timedelta
from subprocess import Popen, PIPE
from time import gmtime
from time import strftime
from timeit import default_timer as timer

import jesse.helpers as jh
from jesse.config import config
from jesse.routes import router
from jessetk.Vars import datadir


def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)


class RandomWalk:
    def __init__(self, start_date, finish_date, n_of_iters, width):
        import signal

        signal.signal(signal.SIGINT, signal_handler)

        self.jessetkdir = datadir
        self.start_date = start_date
        self.finish_date = finish_date

        self.start_date_object = datetime.strptime(start_date, '%Y-%m-%d')  # start_date as datetime object, to make calculations easier.
        self.finish_date_object = datetime.strptime(finish_date, '%Y-%m-%d')
        self.test_period_length = self.finish_date_object - self.start_date_object  # Test period length as days
        self.rand_end = self.test_period_length - timedelta(days=width)  # period - windows width

        self.results = []
        self.sorted_results = []
        self.random_numbers = []

        r = router.routes[0]                # Read first route from routes.py
        self.strategy = r.strategy_name     # get strategy name to create filenames

        self.ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.filename = f'Random-{self.strategy}-{start_date}--{finish_date}-{self.ts}'
        self.report_file_name = f'{self.jessetkdir}/results/{self.filename}--{self.ts}.csv'
        self.log_file_name = f'{self.jessetkdir}/logs/{self.filename}--{self.ts}.log'

    def make_random_period(self, width, random_numbers, random_end, start_date, timeframe):
        # rn = int(quantumrandom.randint(0, rand_end.days))  # random.randint(0, rand_end.days)
        # rn = random.randint(0, rand_end.days)

        max_retries = 6
        random_number = None

        for _ in range(max_retries):
            random_number = random.randint(0, random_end.days)
            if random_number not in random_numbers:
                break

        random_numbers.append(random_number)

        random_start_date = start_date + timedelta(days=random_number)  # Add random number of days to start date
        random_finish_date = random_start_date + timedelta(days=width)
        # _sd = random_start_date.strftime('%Y-%m-%d')
        # _ed = random_finish_date.strftime('%Y-%m-%d')
        # print(str(random_start_date), str(random_finish_date), _sd, _ed)
        return random_start_date.strftime('%Y-%m-%d'), random_finish_date.strftime('%Y-%m-%d'), random_numbers


def runtest(_startdate, _enddate, _pair, _tf):
    process = Popen(['jesse', 'backtest', _startdate, _enddate], stdout=PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()
    res = output.decode('utf-8')
    print(res)
    return getmetrics(_pair, _tf, res, _startdate, _enddate)



def createreport(_reportfilename, _csvheader, _sortedresults):
    with open(_reportfilename, 'w') as f:
        f.write(str(_csvheader).replace('[', '').replace(']', '').replace(' ', '') + '\n')
        for srline in _sortedresults:
            f.write(str(srline).replace('[', '').replace(']', '').replace(' ', '') + '\n')
        os.fsync(f.fileno())


def run(_start_date, _finish_date, _iterations, _width):
    results = []
    resultswithoutdna = []
    sortedresults = []
    periods = []

    r = router.routes[0]  # Read first route from routes.py
    exchange = r.exchange
    symbol = r.symbol
    timeframe = r.timeframe
    strategy = r.strategy_name
    # dna = r.dna
    # Make random periods
    # 2160  3240    4320    6480
    # from Jesse: Supported timeframes are 1m, 3m, 5m, 15m, 30m, 45m, 1h, 2h, 3h, 4h, 6h, 8h, 12h, 1D, 3D, 1W

    timeframe = r.timeframe if hasattr(r, 'timeframe') else jh.max_timeframe(config['app']['considering_timeframes'])
    print(timeframe)

    warmup_candles_count = jh.get_config('env.data.warmup_candles_num', 210)  # TODO: Consider higher TF candles!

    pre_candles_count = jh.timeframe_to_one_minutes(timeframe) * warmup_candles_count

    oldestdate = _start_date  # pairs[f'{exchange}-{symbol}']  # Get oldest candle date from hardcoded list. It is also can be retrieved from candle database. !Jesse already checks last available candle!
    fixedenddate = _finish_date  # '10/08/2021 00:00:00'        # Hardcoded

    # date_1 = datetime.strptime(oldestdate, '%Y-%m-%d')
    fd = datetime.strptime(_start_date, '%Y-%m-%d')  # start_date as datetime object, to make calculations easier.
    firstcandledate = fd.strftime('%Y-%m-%d')
    fixedenddateobject = datetime.strptime(_finish_date, '%Y-%m-%d')

    since = datetime.strptime(_finish_date, '%Y-%m-%d') - datetime.strptime(_start_date, '%Y-%m-%d')  # Test period length as days

    print(f'Start Date: {_start_date}, Finish Date: {_finish_date}, Period: {since}')
    rand_start = 0

    width = _width  # 4380 2h 1 year ##   2160 4320 = 3 mo for 30m, 8640 = 6 months for 30m
    numofiterations = _iterations  # 100

    rand_end = since - timedelta(days=width)  # period - windows width
    diff = (since - rand_end).days
    print('rand end as int:', rand_end.days, 'rand_end', rand_end, 'width:', diff, 'days')

    clearConsole = lambda: os.system('cls' if os.name in ('nt', 'dos') else 'clear')
    #
    # f = open(logfilename, 'w')
    # f.write(str(csvheader) + '\n')

    print('Please wait while loading candles...')

    start = timer()
    randomnumbers = []
    for index in range(1, numofiterations + 1):
        # print(dnac[0])
        # Inject dna to routes.py
        # makeroutes(exc=exchange, pai=symbol, tf=timeframe, stra=strategy, dnacode=dnac[0])
        # makestrat(_strat=strategy, _key=key, _dna=dnaindex)
        startdate, enddate, randomnumbers = makerandomperiod(width, randomnumbers, rand_end, fd, timeframe)
        # Run jesse backtest and grab console output
        ress = runtest(_startdate=startdate, _enddate=enddate, _pair=symbol, _tf=timeframe)
        print(ress)

        results.append(ress)

        # print(ress)
        f.write(str(ress) + '\n')
        f.flush()
        sortedresults = sorted(results, key=lambda x: float(x[10]), reverse=True)

        clearConsole()
        rt = ((timer() - start) / index) * (numofiterations - index)
        rtformatted = strftime("%H:%M:%S", gmtime(rt))
        print(f'{index}/{numofiterations}\tRemaining Time: {rtformatted}')

        print(
            formatter.format(*header1))
        print(
            formatter.format(*header2))
        topresults = sortedresults[0:40]
        for r in topresults:
            print(
                formatter.format(*r))
        delta = timer() - start
    # Sync and close log file
    os.fsync(f.fileno())
    f.close()

    createreport(reportfilename, csvheader, sortedresults)
