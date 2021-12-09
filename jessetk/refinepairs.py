import importlib
import os
from datetime import datetime
from subprocess import Popen, PIPE
from time import gmtime
from time import strftime
from timeit import default_timer as timer

from jesse.routes import router

# from jessepicker import refine
import jessepicker.refine as refine

jessepickerdir = 'jessepickerdata'
anchor = 'ANCHOR!'
dna_anchor = '(╯°□°)╯︵ ┻━┻'


def make_routes(template, symbol):
    global anchor
    if anchor not in template:
        os.system('color')
        print('\nPlease replace the symbol strings in routes.py with anchors. eg:\n')
        print("""(\033[32m'FTX Futures', 'ANCHOR!', '15m', 'noStra'\033[0m),\n""")
        exit()

    template = template.replace(anchor, symbol)

    if os.path.exists('routes.py'):
        os.remove('routes.py')

    with open('routes.py', 'w', encoding='utf-8') as f:
        f.write(template)
        f.flush()
        os.fsync(f.fileno())


def make_refine_routes(_template, dna_code):
    global dna_anchor
    if dna_anchor not in _template:
        os.system('color')
        print('\nPlease replace the dna strings in routes.py with anchors. eg:\n')
        print("""(\033[32m'Binance Futures', 'ETH-USDT', '15m', 'noStra', '(╯°□°)╯︵ ┻━┻'\033[0m),\n""")
        exit()
    # print(dna_code, 'dna code')
    _template = _template.replace("'" + dna_anchor + "'", repr(dna_code))

    if os.path.exists('routes.py'):
        os.remove('routes.py')

    with open('routes.py', 'w', encoding='utf-8') as f:
        f.write(_template)
        f.flush()
        os.fsync(f.fileno())


def write_file(_fn, _body):
    if os.path.exists(_fn):
        os.remove(_fn)

    with open(_fn, 'w', encoding='utf-8') as f:
        f.write(_body)
        f.flush()
        os.fsync(f.fileno())


def read_file(_file):
    with open(_file, 'r', encoding='utf-8') as ff:
        _body = ff.read()
    return _body


def split(_str):
    _ll = _str.split(' ')
    _r = _ll[len(_ll) - 1].replace('%', '')
    _r = _r.replace(')', '')
    _r = _r.replace('(', '')
    _r = _r.replace(',', '')
    return _r


def getmetrics(_pair, _tf, _dna, metrics, _startdate, _enddate):
    metr = [_pair, _tf, _dna, _startdate, _enddate]
    lines = metrics.splitlines()
    for index, line in enumerate(lines):

        if 'Aborted!' in line:
            print(metrics)
            print("Aborted! error. Possibly pickle database is corrupt. Delete temp/ folder to fix.")
            exit(1)

        if 'CandleNotFoundInDatabase:' in line:
            print(metrics)
            return "Break!"  # [_pair, _tf, _dna, _startdate, _enddate, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        if 'Uncaught Exception' in line:
            print(metrics)
            exit(1)

        if 'No trades were made' in line:
            return [_pair, _tf, _dna, _startdate, _enddate, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

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

        if 'Serenity Index' in line:
            a = split(line)
            metr.append(a)
            # print('Serenity:', a)

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


def runtest(_start_date, _finish_date, _pair, _tf, symbol):
    process = Popen(['jesse', 'backtest', _start_date, _finish_date], stdout=PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()
    res = output.decode('utf-8', errors='ignore')
    # print(res)
    return getmetrics(_pair, _tf, symbol, res, _start_date, _finish_date)


def refine_runtest(_start_date, _finish_date, _pair, _tf, _dnaid):
    process = Popen(['jesse', 'backtest', _start_date, _finish_date], stdout=PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()
    res = output.decode('utf-8')
    # print(res)
    return getmetrics(_pair, _tf, _dnaid, res, _start_date, _finish_date)


def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')

    # Restore routes.py
    write_file('routes.py', routes_template)
    import sys
    sys.exit(0)


def run(dna_file, _start_date, _finish_date):
    import signal

    signal.signal(signal.SIGINT, signal_handler)

    results = []
    sortedresults = []

    r = router.routes[0]  # Read first route from routes.py
    exchange = r.exchange
    # pair = r.symbol
    timeframe = r.timeframe


    print('Please wait while loading candles...')

    # Read routes.py as template
    global routes_template
    routes_template = read_file('routes.py')
    pairs_list = None

    try:
        import jessepicker.pairs
    except:
        print('Can not import pairs!')
        exit()

    if exchange == 'Binance Futures':
        pairs_list = jessepicker.pairs.binance_perp_pairs
        print('Binance Futures all symbols')

    elif exchange == 'Binance':
        pairs_list = jessepicker.pairs.binance_spot_pairs
        print('Binance Spot symbols')

    elif exchange == 'FTX Futures':
        pairs_list = jessepicker.pairs.ftx_perp_pairs
        print('FTX Futures all symbols!')
    else:
        print('Unsupported exchange or broken routes file! Exchange = ', exchange)
        exit()

    if not pairs_list:
        print('pairs_list is empty!')
        exit()

    num_of_pairs = len(pairs_list)

    start = timer()
    # r = router.routes[0]  # Read first route from routes.py
    # pair = r.symbol
    for index, pair in enumerate(pairs_list, start=1):
        # Restore routes.py
        write_file('routes.py', routes_template)

        make_routes(routes_template, pair)

        print(pair)
        # exit()
        # Run refine on selected pair
        refine(pair, dna_file, _start_date, _finish_date)

        # Restore routes.py
        # write_file('routes.py', routes_template)


def refine(pair, dna_file, _start_date, _finish_date):
    import signal

    signal.signal(signal.SIGINT, signal_handler)
    # print('Press Ctrl+C')
    # signal.pause()

    # Starts here
    results = []
    resultswithoutdna = []
    sortedresults = []

    from jesse.routes import router
    r = router.routes[0]  # Read first route from routes.py
    print('r.symbol', r.symbol)
    # exit()
    exchange = r.exchange
    # pair = r.symbol
    print('Pair:', pair)
    timeframe = r.timeframe
    strategy = r.strategy_name

    removesimilardnas = False

    key = '!ChangeIt!'  # Used for injecting variables to strategy file.

    headerforfiles = ['Pair', 'TF', 'Dna', 'Start Date', 'End Date', 'Total Trades', 'Total Net Profit', 'Max.DD',
                      'Annual Profit', 'Winrate',
                      'Sharpe', 'Calmar', 'Serenity', 'Winning Strike', 'Losing Strike', 'Largest Winning',
                      'Largest Losing',
                      'Num. of Wins', 'Num. of Losses',
                      'Market Change']

    header1 = ['Pair', 'TF', 'Dna', 'Start Date', 'End Date', 'Total', 'Total Net', 'Max.', 'Annual', 'Win',
               'Sharpe', 'Calmar', 'Serenity', 'Winning', 'Losing', 'Largest', 'Largest', 'Winning', 'Losing',
               'Market']
    header2 = [' ', ' ', ' ', '   ', '   ', 'Trades', 'Profit %', 'DD %', 'Return %', 'Rate %',
               'Ratio', 'Ratio', 'Index', 'Streak', 'Streak', 'Win. Trade', 'Los. Trade', 'Trades', 'Trades',
               'Change %']

    formatter = '{: <10} {: <5} {: <12} {: <12} {: <12} {: <6} {: <12} {: <8} {: <10} {: <8} {: <8} {: <12} {: <10} {: <8} {: <8} ' \
                '{: <12} {: <12} {: <10} {: <10} {: <12}'

    clearConsole = lambda: os.system('cls' if os.name in ('nt', 'dos') else 'clear')

    ts = datetime.now().strftime("%Y%m%d %H%M%S")
    
    filename = f'{exchange}-{pair}-{timeframe}--{_start_date}--{_finish_date}'

    reportfilename = f'{jessepickerdir}/results/{filename}--{ts}.csv'
    logfilename = f'{jessepickerdir}/logs/{filename}--{ts}.log'
    f = open(logfilename, 'w', encoding='utf-8')
    f.write(str(headerforfiles) + '\n')

    # dnasmodule = importlib.import_module(f'{jessepickerdir}.dnafiles.{strategy}dnas')
    module_name = dna_file.replace('\\', '.').replace('.py', '')
    module_name = module_name.replace('/', '.').replace('.py', '')
    print(module_name)
    dnasmodule = importlib.import_module(module_name)
    dnas = dnasmodule.dnas

    lendnas = len(dnas)

    print('Please wait while loading candles...')

    # Read routes.py as template
    # global routes_template
    routes_template = read_file('routes.py')
    # print(routes_template)
    # r = router.routes[0]  # Read first route from routes.py
    # print('__dict__', router.routes.__dict__)
    # from foo import bar

    # sleep(5)
    # for ii in range(1,500):
    #     from jesse.routes import router
    #     # r = router.routes[0]  # Read first route from routes.py
    #     print('__dict__', router.routes[0].__dict__)
    #     print('__dict__', rt.routes[0].__dict__)
    #     # sleep(2)

    start = timer()
    for index, dnac in enumerate(dnas, start=1):
        # print(dnac[0])

        # Inject dna to routes.py
        make_refine_routes(routes_template, dna_code=dnac[0])
        # makestrat(_strat=strategy, _key=key, _dna=dnaindex)

        # Run jesse backtest and grab console output
        # print(_start_date, _finish_date, pair, timeframe, dnac[0])
        ress = refine_runtest(_start_date=_start_date, _finish_date=_finish_date, _pair=pair, _tf=timeframe,
                              _dnaid=dnac[0])
        if ress == "Break!":
            break
        
        if ress not in results:
            results.append(ress)

        # print(ress)
        f.write(str(ress) + '\n')
        f.flush()
        sortedresults = sorted(results, key=lambda x: float(x[12]), reverse=True)

        clearConsole()
        rt = ((timer() - start) / index) * (lendnas - index)
        rtformatted = strftime("%H:%M:%S", gmtime(rt))
        print(f'{index}/{lendnas}\tRemaining Time: {rtformatted}')

        print(
            formatter.format(*header1))
        print(
            formatter.format(*header2))
        topresults = sortedresults[0:30]
        # print(topresults)
        for r in topresults:
            print(
                formatter.format(*r))
        delta = timer() - start

    # Restore routes.py
    # write_file('routes.py', routes_template)

    # Sync and close log file
    os.fsync(f.fileno())
    f.close()

    # Create csv report
    
    f = open(reportfilename, 'w', encoding='utf-8')
    f.write(str(headerforfiles).replace('[', '').replace(']', '').replace(' ', '') + '\n')
    for srline in sortedresults:
        f.write(str(srline).replace('[', '').replace(']', '').replace(' ', '') + '\n')
    os.fsync(f.fileno())
    f.close()

    # Rewrite dnas.py, sorted by calmar

    # dnafilename = f'{jessepickerdir}/dnafiles/{filename}'
    dnafilename = f'{jessepickerdir}/dnafiles/{pair} {_start_date} {_finish_date}.py'
    if os.path.exists(dnafilename):
        os.remove(dnafilename)

    f = open(dnafilename, 'w', encoding='utf-8')
    f.write('dnas = [\n')

    sorteddnas = []
    for srr in sortedresults:
        for dnac in dnas:
            # print(srr[2], dnac[0], 'DNAC:', dnac)
            if srr[2] == dnac[0]:
                # f.write(str(dnac) + ',\n')
                # f.write(str(dnac).replace("""['""", """[r'""") + ',\n')
                # f.write(str(dnac).replace("""\n['""", """\n[r'""") + ',\n')
                f.write(str(dnac) + ',\n')
                # sorteddnas.append(dnac)

    f.write(']\n')
    f.flush()
    os.fsync(f.fileno())
    f.close()
