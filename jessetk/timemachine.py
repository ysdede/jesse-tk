import os
import random
from datetime import datetime
from datetime import timedelta
from subprocess import Popen, PIPE
from time import gmtime
from time import strftime
from timeit import default_timer as timer

import jesse.helpers as jh
from jesse.config import config
from jesse.routes import router

jessepickerdir = 'jessepickerdata'


def split(_str):
    _ll = _str.split(' ')
    _r = _ll[len(_ll) - 1].replace('%', '')
    _r = _r.replace(')', '')
    _r = _r.replace('(', '')
    _r = _r.replace(',', '')
    return _r


def getmetrics(_pair, _tf, metrics, _startdate, _enddate):
    metr = [_pair, _tf, _startdate, _enddate]
    lines = metrics.splitlines()
    for index, line in enumerate(lines):

        if 'CandleNotFoundInDatabase' in line:
            return [_pair, _tf, _startdate, _enddate, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        if 'Uncaught Exception' in line:
            print(metrics)
            exit(1)

        if 'No trades were made' in line:
            return [_pair, _tf, _startdate, _enddate, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        if 'Total Closed Trades' in line:
            a = split(line)
            metr.append(a)
            # print('Total closed:', a)

        if 'Total Net Profit' in line:
            a = split(line)
            metr.append(a)
            # print('Net Profit:', a)

        if 'Max Drawdown' in line:
            a = split(line)
            metr.append(a)
            # print('Max Drawdown:', a)

        if 'Annual Return' in line:
            a = float(split(line))
            metr.append(round(a))
            # print('Annual Return:', a)

        if 'Percent Profitable' in line:
            a = split(line)
            metr.append(a)
            # print('Percent Profitable:', a)

        if 'Sharpe Ratio' in line:
            a = split(line)
            metr.append(a)
            # print('Sharpe Ratio:', a)

        if 'Calmar Ratio' in line:
            a = split(line)
            metr.append(a)
            # print('Calmar Ratio:', a)

        if 'Winning Streak' in line:
            a = split(line)
            metr.append(a)
            # print('Winning Streak:', a)

        if 'Losing Streak' in line:
            a = split(line)
            metr.append(a)
            # print('Losing Streak:', a)

        if 'Largest Winning Trade' in line:
            a = float(split(line))
            metr.append(round(a))
            # print('Largest Winning Trade:', a)

        if 'Largest Losing Trade' in line:
            a = float(split(line))
            metr.append(round(a))
            # print('Largest Losing Trade:', a)

        if 'Total Winning Trades' in line:
            a = split(line)
            metr.append(a)
            # print('Total Winning Trades:', a)

        if 'Total Losing Trades' in line:
            a = split(line)
            metr.append(a)
            # print('Total Losing Trades:', a)

        if 'Market Change' in line:
            a = split(line)
            metr.append(a)
            # print('Market Change:', a)
    return metr


def runtest(_startdate, _enddate, _pair, _tf):
    process = Popen(['jesse', 'backtest', _startdate, _enddate], stdout=PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()
    res = output.decode('utf-8')
    print(res)
    return getmetrics(_pair, _tf, res, _startdate, _enddate)


def makerandomperiod(_width, _randomnumbers, _rand_end, _fd, _timeframe):
    # rn = int(quantumrandom.randint(0, rand_end.days))  # random.randint(0, rand_end.days)
    # rn = random.randint(0, rand_end.days)
    rn = random.randint(0, _rand_end.days)

    if rn in _randomnumbers:
        rn = random.randint(0, _rand_end.days)
    _randomnumbers.append(rn)

    _start_date = _fd + timedelta(days=rn)
    _finish_date = _start_date + timedelta(minutes=jh.timeframe_to_one_minutes(_timeframe) * _width)
    _sd = _start_date.strftime('%Y-%m-%d')
    _ed = _finish_date.strftime('%Y-%m-%d')
    # print(str(start_date), str(end_date), _sd, _ed)
    startdate = _sd
    enddate = _ed
    return _sd, _ed, _randomnumbers


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
    fd = datetime.strptime(oldestdate, '%Y-%m-%d') + timedelta(minutes=pre_candles_count + 1440)
    firstcandledate = fd.strftime('%Y-%m-%d')
    fixedenddateobject = datetime.strptime(_finish_date, '%Y-%m-%d')
    since = fixedenddateobject - fd  # datetime.now() - fd

    print('oldestdate', oldestdate)
    print('warmup_candles_count', warmup_candles_count)
    print('pre_candles_count', pre_candles_count)
    print('pre_candles_count', pre_candles_count)
    print('First avail. date', fd)
    print('firstcandledate', firstcandledate)

    print('Since:', since)
    rand_start = 0

    width = _width  # 4380 2h 1 year ##   2160 4320 = 3 mo for 30m, 8640 = 6 months for 30m
    numofiterations = _iterations  # 100

    rand_end = since - timedelta(minutes=jh.timeframe_to_one_minutes(timeframe) * width)
    print('rand end as int:', rand_end.days)
    print('rand_end', rand_end)
    diff = (since - rand_end).days
    print('Period:', diff, 'days')

    csvheader = ['Pair', 'TF', 'Start Date', 'End Date', 'Total Trades', 'Total Net Profit', 'Max.DD',
                 'Annual Profit', 'Winrate',
                 'Sharpe', 'Calmar', 'Winning Strike', 'Losing Strike', 'Largest Winning', 'Largest Losing',
                 'Num. of Wins', 'Num. of Losses',
                 'Market Change']

    header1 = ['Pair', 'TF', 'Start Date', 'End Date', 'Total', 'Total Net', 'Max.', 'Annual', 'Win',
               'Sharpe', 'Calmar', 'Winning', 'Losing', 'Largest', 'Largest', 'Winning', 'Losing',
               'Market']
    header2 = [' ', ' ', '   ', '   ', 'Trades', 'Profit %', 'DD %', 'Return %', 'Rate %',
               'Ratio', 'Ratio', 'Streak', 'Streak', 'Win. Trade', 'Los. Trade', 'Trades', 'Trades',
               'Change %']

    formatter = '{: <10} {: <5} {: <12} {: <12} {: <6} {: <12} {: <8} {: <10} {: <8} {: <8} {: <12} {: <8} {: <8} ' \
                '{: <12} {: <12} {: <10} {: <10} {: <12}'

    clearConsole = lambda: os.system('cls' if os.name in ('nt', 'dos') else 'clear')

    ts = datetime.now().strftime("%Y%m%d %H%M%S")

    filename = f'{exchange}-{timeframe}--{ts}'

    reportfilename = f'{jessepickerdir}/results/{filename}--{ts}.csv'
    logfilename = f'{jessepickerdir}/logs/{filename}--{ts}.log'
    with open(logfilename, 'w') as f:
        f.write(str(csvheader) + '\n')

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
    createreport(reportfilename, csvheader, sortedresults)


if __name__ == "__main__":
    run()
