import os
import sys
from copy import deepcopy
from multiprocessing import cpu_count
from pydoc import locate
from time import gmtime, sleep, strftime
from timeit import default_timer as timer

import click
import jesse.helpers as jh
from jesse.config import config
from jesse.helpers import get_config
from jesse.modes import backtest_mode
from jesse.routes import router
from jesse.services import db
from jesse.services.selectors import get_exchange
from jesse.services import report
import json as json_lib
from jessetk import Vars, randomwalk, utils
from jessetk.Vars import (Metrics, initial_test_message, random_console_formatter,
                          random_file_header, refine_file_header)
from jessetk.utils import clear_console, hp_to_seq

# # Python version validation.
# if jh.python_version() < 3.7:
#     print(
#         jh.color(
#             f'Jesse requires Python version above 3.7. Yours is {jh.python_version()}',
#             'red'
#         )
#     )

# fix directory issue
sys.path.insert(0, os.getcwd())

ls = os.listdir('.')
is_jesse_project = 'strategies' in ls and 'config.py' in ls and 'storage' in ls and 'routes.py' in ls


def inject_local_config() -> None:
    """
    injects config from local config file
    """
    local_config = locate('config.config')
    from jesse.config import set_config
    set_config(local_config)


def inject_local_routes() -> None:
    """
    injects routes from local routes folder
    """
    local_router = locate('routes')
    from jesse.routes import router

    router.set_routes(local_router.routes)
    router.set_extra_candles(local_router.extra_candles)


# inject local files
if is_jesse_project:
    inject_local_config()
    inject_local_routes()


def validate_cwd() -> None:
    """
    make sure we're in a Jesse project
    """
    if not is_jesse_project:
        print(
            jh.color(
                'Current directory is not a Jesse project. You must run commands from the root of a Jesse project.',
                'red'
            )
        )
        # os.exit(1)
        exit()


# create a Click group

@click.group()
def cli() -> None:
    pass


@cli.command()
@click.argument('dna_log_file', required=True, type=str)
@click.argument('sort_criteria', required=False, type=str)
@click.argument('len1', required=False, type=int)
@click.argument('len2', required=False, type=int)
def pick(dna_log_file, sort_criteria, len1, len2) -> None:
    """
    Picks dnas from Jesse optimization log file
    """

    if not dna_log_file:
        print('dna_log_file is required!')
        exit()

    sort_criteria = 'pnl1' if not sort_criteria else sort_criteria
    len1 = 30 if not len1 or len1 < 0 or len1 > 10_000 else len1
    len2 = 150 if not len2 or len2 < 0 or len2 > 10_000 else len2

    os.chdir(os.getcwd())
    validate_cwd()

    import jesse.helpers as jh
    from jesse.routes import router

    makedirs()
    r = router.routes[0]  # Read first route from routes.py
    strategy = r.strategy_name
    StrategyClass = jh.get_strategy_class(r.strategy_name)
    print('Strategy name:', strategy, 'Strategy Class:', StrategyClass)

    from jessetk.picker import picker

    dna_picker = picker(dna_log_file, strategy,
                        StrategyClass, len1, len2, sort_criteria)

    dna_picker.sortdnas()
    dna_picker.create_output_file()
    dna_picker.validate_output_file()


@cli.command()
@click.argument('dna_file', required=True, type=str)
@click.argument('start_date', required=True, type=str)
@click.argument('finish_date', required=True, type=str)
@click.option('--eliminate/--no-eliminate', default=False,
              help='Remove worst performing dnas at every iteration.')
@click.option(
    '--cpu', default=0, show_default=True,
    help='The number of CPU cores that Jesse is allowed to use. If set to 0, it will use as many as is available on your machine.')
@click.option('--full-reports/--no-full-reports', default=False,
              help="Generates QuantStats' HTML output with metrics reports like Sharpe ratio, Win rate, Volatility, etc., and batch plotting for visualizing performance, drawdowns, rolling statistics, monthly returns, etc.")
def refine(dna_file, start_date: str, finish_date: str, eliminate: bool, cpu: int, full_reports) -> None:
    """
    backtest all candidate dnas. Enter in "YYYY-MM-DD" "YYYY-MM-DD"
    """
    os.chdir(os.getcwd())
    validate_cwd()
    validateconfig()
    makedirs()

    if not eliminate:
        eliminate = False

    if cpu > cpu_count():
        raise ValueError(
            f'Entered cpu cores number is more than available on this machine which is {cpu_count()}')
    elif cpu == 0:
        max_cpu = cpu_count()
    else:
        max_cpu = cpu
    print('CPU:', max_cpu)

    from jessetk.RefineTh import Refine
    r = Refine(dna_file, start_date, finish_date,
               eliminate, max_cpu, full_reports)
    r.run()


@cli.command()
@click.argument('hp_file', required=True, type=str)
@click.argument('start_date', required=True, type=str)
@click.argument('finish_date', required=True, type=str)
@click.option('--eliminate/--no-eliminate', default=False,
              help='Remove worst performing dnas at every iteration.')
@click.option(
    '--cpu', default=0, show_default=True,
    help='The number of CPU cores that Jesse is allowed to use. If set to 0, it will use as many as is available on your machine.')
@click.option(
    '--dd', default=-90, show_default=True,
    help='Maximum drawdown limit for filtering results.')
@click.option('--full-reports/--no-full-reports', default=False,
              help="Generates QuantStats' HTML output with metrics reports like Sharpe ratio, Win rate, Volatility, etc., and batch plotting for visualizing performance, drawdowns, rolling statistics, monthly returns, etc.")
def refine_seq(hp_file, start_date: str, finish_date: str, eliminate: bool, cpu: int, dd: int, full_reports) -> None:
    """
    backtest all Sequential candidate Optuna parameters.
    Enter in "YYYY-MM-DD" "YYYY-MM-DD"
    """
    os.chdir(os.getcwd())
    validate_cwd()
    validateconfig()
    makedirs()

    if not eliminate:
        eliminate = False

    if cpu > cpu_count():
        raise ValueError(
            f'Entered cpu cores number is more than available on this machine which is {cpu_count()}')
    elif cpu == 0:
        max_cpu = cpu_count()
    else:
        max_cpu = cpu
    print('CPU:', max_cpu)

    from jessetk.RefineSeq import Refine
    r = Refine(hp_file, start_date, finish_date, eliminate,
               max_cpu, dd=dd, full_reports=full_reports)
    r.run()

# @cli.command()
# @click.argument('dna_file', required=True, type=str)
# @click.argument('start_date', required=True, type=str)
# @click.argument('finish_date', required=True, type=str)
# @click.option('--eliminate/--no-eliminate', default=False,
#               help='Remove worst performing dnas at every iteration.')
# @click.option(
#     '--cpu', default=0, show_default=True,
#     help='The number of CPU cores that Jesse is allowed to use. If set to 0, it will use as many as is available on your machine.')
# def refine_gly(dna_file, start_date: str, finish_date: str, eliminate: bool, cpu: int) -> None:
#     """
#     backtest all candidate dnas. Enter in "YYYY-MM-DD" "YYYY-MM-DD"
#     """
#     os.chdir(os.getcwd())
#     validate_cwd()
#     validateconfig()
#     makedirs()

#     if not eliminate:
#         eliminate = False

#     if cpu > cpu_count():
#         raise ValueError(
#             f'Entered cpu cores number is more than available on this machine which is {cpu_count()}')
#     elif cpu == 0:
#         max_cpu = cpu_count()
#     else:
#         max_cpu = cpu
#     print('CPU:', max_cpu)

#     from jessetk.RefineGlyph import Refine
#     r = Refine(dna_file, start_date, finish_date, eliminate, max_cpu)
#     r.run()


@cli.command()
@click.argument('start_date', required=True, type=str)
@click.argument('finish_date', required=True, type=str)
@click.argument('iterations', required=False, type=int)
@click.argument('width', required=False, type=int)
@click.option(
    '--cpu', default=0, show_default=True,
    help='The number of CPU cores that Jesse is allowed to use. If set to 0, it will use as many as is available on your machine.')
def random(start_date: str, finish_date: str, iterations: int, width: int, cpu: int) -> None:
    """
                                random walk backtest w/ threading.
                                Enter period "YYYY-MM-DD" "YYYY-MM-DD
                                Number of tests to perform  eg. 40
                                Sample width in days        eg. 30"
                                Thread counts to use        eg. 4
    """

    os.chdir(os.getcwd())
    validate_cwd()
    validateconfig()
    makedirs()

    if not iterations or iterations < 0:
        iterations = 32
        print(f'Iterations not provided, falling back to {iterations} iters!')
    if not width:
        width = 60
        print(
            f'Window width not provided, falling back to {width} days window!')

    max_cpu = utils.cpu_info(cpu)

    from jessetk.RandomWalkTh import RandomWalk
    rwth = RandomWalk(start_date, finish_date, iterations, width, max_cpu)
    rwth.run()


@cli.command()
@click.argument('start_date', required=False, type=str)
def import_routes(start_date: str) -> None:
    """
    Import-candles for pairs listed in routes.py
    Enter start date "YYYY-MM-DD"
    If no start date is specified, the system will default to two days earlier.
    It's useful for executing script in a cron job to download deltas on a regular basis.
    """
    from dateutil.parser import isoparse
    import datetime

    try:
        isoparse(start_date)
        sd = start_date
    except:
        sd = str(datetime.date.today() - datetime.timedelta(days=2))
        print('Falling-back to two days earlier. Given parameter:', start_date)

    # os.chdir(os.getcwd())
    # validate_cwd()
    # validateconfig()

    try:
        from jesse.config import config
        from jesse.modes import import_candles_mode
        from jesse.routes import router
        from jesse.services import db
        config['app']['trading_mode'] = 'import-candles'
    except Exception as e:
        print(e)
        print('Check your routes.py file or database settings in config.py')
        exit()

    print(f'Startdate: {sd}')

    routes_list = router.routes

    if not routes_list or len(routes_list) < 1:
        print('Check your routes.py file!')
        exit()

    for t in routes_list:
        pair = t.symbol
        exchange = t.exchange
        print(f'Importing {exchange} {pair}')

        try:
            import_candles_mode.run(exchange, pair, sd, skip_confirmation=True)
        except KeyboardInterrupt:
            print('Terminated!')
            db.close_connection()
            sys.exit()
        except:
            print(f'Import error, skipping {exchange} {pair}')

    db.close_connection()


@cli.command()
@click.argument('dna_file', required=True, type=str)
@click.argument('start_date', required=True, type=str)
@click.argument('finish_date', required=True, type=str)
@click.argument('iterations', required=False, type=int)
@click.argument('width', required=False, type=int)
@click.option(
    '--cpu', default=0, show_default=True,
    help='The number of CPU cores that Jesse is allowed to use. If set to 0, it will use as many as is available on your machine.')
def randomrefine(dna_file: str, start_date: str, finish_date: str, iterations: int, width: int, cpu: int) -> None:
    """
                                random walk backtest w/ threading.
                                Enter period "YYYY-MM-DD" "YYYY-MM-DD
                                Number of tests to perform  eg. 40
                                Sample width in days        eg. 30
                                Thread counts to use        eg. 4
    """
    print('Not implemented yet!')
    exit()

    # os.chdir(os.getcwd())
    # validate_cwd()
    # validateconfig()
    # makedirs()

    # from jessetk.Vars import datadir
    # os.makedirs(f'./{datadir}/results', exist_ok=True)

    # if cpu > cpu_count():
    #     raise ValueError(
    #         f'Entered cpu cores number is more than available on this machine which is {cpu_count()}')
    # elif cpu == 0:
    #     max_cpu = cpu_count()
    # else:
    #     max_cpu = cpu

    # print('Cpu count:', cpu_count(), 'Used:', max_cpu)

    # # if not eliminate:
    # #     eliminate = False
    # eliminate = False
    # from jessetk.refine import refine
    # r = refine(dna_file, start_date, finish_date, eliminate)
    # r.run(dna_file, start_date, finish_date)

    # if not iterations or iterations < 0:
    #     iterations = 32
    #     print(f'Iterations not provided, falling back to {iterations} iters!')
    # if not width:
    #     width = 40
    #     print(
    #         f'Window width not provided, falling back to {width} days window!')

    # if cpu > cpu_count():
    #     raise ValueError(
    #         f'Entered cpu cores number is more than available on this machine which is {cpu_count()}')
    # elif cpu == 0:
    #     max_cpu = cpu_count()
    # else:
    #     max_cpu = cpu

    # print('Cpu count:', cpu_count(), 'Used:', max_cpu)
    # from jessetk.RandomRefine import RandomRefine
    # from jessetk.RandomWalkTh import RandomWalk

    # rrefine = RandomRefine(dna_file, start_date, finish_date, False)
    # rwth = RandomWalk(start_date, finish_date, iterations, width, max_cpu)
    # rwth.run()
    # #

    # rrefine.import_dnas()
    # rrefine.routes_template = utils.read_file('routes.py')

    # results = []
    # start = timer()
    # print_initial_msg()
    # for index, dnac in enumerate(rrefine.dnas, start=1):
    #     # Inject dna to routes.py
    #     utils.make_routes(rrefine.routes_template,
    #                       rrefine.anchor, dna_code=dnac[0])

    #     # Run jesse backtest and grab console output
    #     console_output = utils.run_test(start_date, finish_date)

    #     # Scrape console output and return metrics as a dict
    #     metric = utils.get_metrics3(console_output)

    #     if metric not in results:
    #         results.append(deepcopy(metric))
    #     # f.write(str(metric) + '\n')  # Logging disabled
    #     # f.flush()
    #     sorted_results_prelist = sorted(
    #         results, key=lambda x: float(x['sharpe']), reverse=True)
    #     rrefine.sorted_results = []

    #     if rrefine.eliminate:
    #         for r in sorted_results_prelist:
    #             if float(r['sharpe']) > 0:
    #                 rrefine.sorted_results.append(r)
    #     else:
    #         rrefine.sorted_results = sorted_results_prelist

    #     clear_console()

    #     eta = ((timer() - start) / index) * (rrefine.n_of_dnas - index)
    #     eta_formatted = strftime("%H:%M:%S", gmtime(eta))
    #     print(
    #         f'{index}/{rrefine.n_of_dnas}\teta: {eta_formatted} | {rrefine.pair} '
    #         f'| {rrefine.timeframe} | {rrefine.start_date} -> {rrefine.finish_date}')

    #     rrefine.print_tops_formatted()

    # utils.write_file('routes.py', rrefine.routes_template)  # Restore routes.py

    # if rrefine.eliminate:
    #     rrefine.save_dnas(rrefine.sorted_results, dna_file)
    # else:
    #     rrefine.save_dnas(rrefine.sorted_results)

    # utils.create_csv_report(rrefine.sorted_results,
    #                         rrefine.report_file_name, refine_file_header)


@cli.command()
@click.argument('dna_file', required=True, type=str)
@click.argument('start_date', required=True, type=str)
@click.argument('finish_date', required=True, type=str)
@click.argument('iterations', required=False, type=int)
@click.argument('width', required=False, type=int)
def randomsg(dna_file, start_date: str, finish_date: str, iterations: int, width: int) -> None:
    """
    random walk backtest w/ elimination
                                Enter period "YYYY-MM-DD" "YYYY-MM-DD
                                number of tests to perform  eg. 40
                                sample width in days        eg. 30"
    """

    os.chdir(os.getcwd())
    validate_cwd()
    validateconfig()
    makedirs()

    if start_date is None or finish_date is None:
        print('Enter dates!')
        exit()

    if not iterations or iterations < 0:
        iterations = 25
        print('Iterations not provided, falling back to 30 iters!')
    if not width:
        width = 50
        print(
            f'Window width not provided, falling back to {width} days window!')

    from jessetk.randomwalk import RandomWalk
    random_walk = RandomWalk(start_date, finish_date, iterations, width)
    from jessetk.refine import refine

    print_initial_msg()
    # start = timer()
    results = []
    for _ in range(1, iterations + 1):
        # Create a random period between given period
        rand_period_start, rand_period_finish = random_walk.make_random_period()

        r = refine(dna_file, rand_period_start,
                   rand_period_finish, eliminate=True)
        #      v ?
        r.run(dna_file, rand_period_start, rand_period_finish)

        if len(r.sorted_results) <= 5:
            print('Target reached, exiting...')
            break


@cli.command()
@click.argument('exchange', required=True, type=str)
@click.argument('symbol', required=True, type=str)
@click.argument('start_date', required=True, type=str)
@click.argument('data_type', required=False, default='klines', type=str)
@click.option(
    '--workers', default=4, show_default=True,
    help='The number of workers to run simultaneously. You can use cpu thread count or x2 or more.')
def bulkdry(exchange: str, symbol: str, start_date: str, data_type: str, workers: int) -> None:
    """
    DRY RUN
    Bulk download Binance candles as csv files. It does not save them to db.

    Enter EXCHANGE SYMBOL START_DATE { Optional: --workers n}

    jesse-tk bulkdry Binance btc-usdt 2020-01-01
    jesse-tk bulkdry 'Binance Futures' btc-usdt 2020-01-01

    You can use spot or futures keywords instead of full exchange name.

    jesse-tk bulkdry spot btc-usdt 2020-01-01
    jesse-tk bulkdry futures eth-usdt 2017-05-01 --workers 16
    """

    import arrow
    from dateutil import parser
    from jessetk.Bulk import Bulk, get_days, get_months

    os.chdir(os.getcwd())
    validate_cwd()
    # validateconfig()

    try:
        start = parser.parse(start_date)
    except ValueError:
        print(f'Invalid start date: {start_date}')
        exit()

    symbol = symbol.upper()

    workers = max(workers, 8)

    try:
        sym = symbol.replace('-', '')
    except:
        print(f'Invalid symbol: {symbol}, format: BTC-USDT')
        exit()

    end = arrow.utcnow().floor('month').shift(months=-1)

    if exchange in {'binance', 'spot'}:
        exchange = 'Binance'
        market_type = 'spot'
        if data_type not in {'aggTrades', 'klines', 'trades'}:
            print(f'Invalid data type: {data_type}')
            print('Valid data types: aggTrades, klines, trades')
            exit()
        margin_type = None
    elif exchange in {'binance futures', 'futures'}:
        exchange = 'Binance Futures'
        market_type = 'futures'
        if data_type not in {'aggTrades', 'indexPriceKlines', 'klines', 'markPriceKlines',  'premiumIndexKlines', 'trades'}:
            print(f'Invalid data type: {data_type}')
            print('Valid data types: aggTrades, indexPriceKlines, klines, markPriceKlines, premiumIndexKlines, trades')
            exit()
        margin_type = 'um'
    else:
        print('Invalid market type! Enter: binance, binance futures, spot or futures')
        exit()

    # print start and end variables in color
    print(f'\x1b[36mStart: {start}\x1b[0m')
    print(f'\x1b[36mEnd: {end}\x1b[0m')

    b = Bulk(start=start, end=end, exchange=exchange, symbol=symbol,
             market_type=market_type, margin_type=margin_type, data_type=data_type, tf='1m', worker_count=workers)

    b.run()

    print('Completed in', round(timer() - b.timer_start), 'seconds.')


@cli.command()
@click.argument('exchange', required=True, type=str)
@click.argument('symbol', required=True, type=str)
@click.argument('start_date', required=True, type=str)
@click.option(
    '--workers', default=4, show_default=True,
    help='The number of workers to run simultaneously. You can use cpu thread count or x2.')
def bulk(exchange: str, symbol: str, start_date: str, workers: int) -> None:
    """
    Bulk download Binance candles
    Enter EXCHANGE SYMBOL START_DATE { Optional: --workers n}

    jesse-tk bulk Binance btc-usdt 2020-01-01
    jesse-tk bulk 'Binance Futures' btc-usdt 2020-01-01

    You can use spot or futures keywords instead of full exchange name.

    jesse-tk bulk spot btc-usdt 2020-01-01
    jesse-tk bulk futures eth-usdt 2017-05-01 --workers 8
    """

    import arrow
    from dateutil import parser
    from jessetk.BulkJesse import BulkJesse

    os.chdir(os.getcwd())
    validate_cwd()
    # validateconfig()
    exchange = exchange.lower()

    try:
        start = parser.parse(start_date)
    except ValueError:
        print(f'Invalid start date: {start_date}')
        exit()

    workers = max(workers, 64)

    symbol = symbol.upper()

    try:
        sym = symbol.replace('-', '')
    except:
        print(f'Invalid symbol: {symbol}, format: BTC-USDT')
        exit()

    end = arrow.utcnow().floor('month').shift(months=-1)

    if exchange in ['binance', 'spot']:
        exchange = 'Binance'
        market_type = 'spot'
        margin_type = None
    elif exchange in ['binance futures', 'futures']:
        exchange = 'Binance Futures'
        market_type = 'futures'
        margin_type = 'um'
    else:
        print('Invalid market type! Enter: binance, binance futures, spot or futures')
        exit()

    print(f'\x1b[36mStart: {start}  {end}\x1b[0m')

    bb = BulkJesse(start=start, end=end, exchange=exchange,
                   symbol=symbol, market_type=market_type, tf='1m')

    bb.run()

    print('Completed in', round(timer() - bb.timer_start), 'seconds.')
# /////


@cli.command()
@click.argument('exchange', required=True, type=str)
@click.argument('start_date', required=True, type=str)
@click.option(
    '--workers', default=2, show_default=True,
    help='The number of workers to run simultaneously.')
@click.option('--all/--list', default=False, help="Get pairs list from api or pairs from file.")
def bulkpairs(exchange: str, start_date: str, workers: int, all) -> None:
    """
    Bulk download ALL! Binance Futures candles to Jesse DB.
    Enter EXCHANGE START_DATE { Optional: --workers n}

    jesse-tk bulkpairs 'Binance Futures' 2020-01-01
    jesse-tk bulkpairs futures 2017-05-01 --workers 8
    """

    exchange_data = {'binance': {'exchange': 'Binance', 'market_type': 'spot', 'margin_type': None},
                     'spot': {'exchange': 'Binance', 'market_type': 'spot', 'margin_type': None},
                     'binance futures': {'exchange': 'Binance Futures', 'market_type': 'futures', 'margin_type': 'um'},
                     'futures': {'exchange': 'Binance Futures', 'market_type': 'futures', 'margin_type': 'um'}}

    import arrow
    from dateutil import parser
    from jessetk.BulkJesse import BulkJesse

    os.chdir(os.getcwd())
    validate_cwd()
    # validateconfig()
    exchange = exchange.lower()

    try:
        start = parser.parse(start_date)
    except ValueError:
        print(f'Invalid start date: {start_date}')
        exit()

    workers = max(workers, 2)

    end = arrow.utcnow().floor('month').shift(months=-1)
    
    print(exchange)
    print(exchange_data[exchange])
    print(exchange_data.keys())
    print(exchange_data[exchange]['market_type'])

    if exchange in exchange_data.keys():
        exchange_name = exchange_data[exchange]['exchange']
        market_type = exchange_data[exchange]['market_type']
        margin_type = exchange_data[exchange]['margin_type']

        if all:
            # Get pairs list from api
            from jessetk.utils import get_symbols_list, avail_pairs
            pairs_list = get_symbols_list(exchange_name)
            db_symbols = avail_pairs(start_date, exchange_name)

            print(f"There's {len(pairs_list)} available pairs in {exchange_name}:")
            print(pairs_list)
            print(f"There's {len(db_symbols)} available pairs in candle database at: {start_date}")
        else:
            # Get pair list from user defined py file
            if exchange_data[exchange]['market_type'] == 'spot':
                try:
                    import pairs
                    pairs_list = pairs.binance_spot_pairs
                except ImportError:
                    print('Pairs file not found in project folder, loading default pairs list.')
                    import jessetk.pairs
                    pairs_list = jessetk.pairs.binance_spot_pairs
                except:
                    print('Can not import pairs!')
                    exit()
            elif exchange_data[exchange]['market_type'] == 'futures':
                try:
                    import pairs
                    pairs_list = pairs.binance_perp_pairs
                except ImportError:
                    print('Pairs file not found in project folder, loading default pairs list.')
                    import jessetk.pairs
                    pairs_list = jessetk.pairs.binance_perp_pairs
                except:
                    print('Can not import pairs!')
                    exit()
    else:
        print('Invalid market type! Enter: binance, binance futures, spot or futures')
        exit()

    sloMo = False
    debug = False

    print(f'\x1b[36mStart: {start}  {end}\x1b[0m')

    bb = BulkJesse(start=start, end=end, exchange=exchange_name,
                   symbol='BTC-USDT', market_type=market_type, tf='1m')

    today = arrow.utcnow().format('YYYY-MM-DD')

    for pair in pairs_list:
        print(f'Importing {exchange_name} {pair} {start_date} -> {today}')
        # sleep2(5)
        bb.symbol = pair

        try:
            bb.run()
        except KeyboardInterrupt:
            print('Terminated!')
            sys.exit()
        except Exception as e:
            print(f'Error: {e}')
            continue
    print('Completed in', round(timer() - bb.timer_start), 'seconds.')

# ***************

# --------------------------------------------------


@cli.command()
@click.argument('dna_file', required=True, type=str)
@click.argument('start_date', required=True, type=str)
@click.argument('finish_date', required=True, type=str)
def refinepairs(dna_file, start_date: str, finish_date: str) -> None:
    """
    backtest all pairs with candidate dnas. Enter full path to dnafile and enter period in "YYYY-MM-DD" "YYYY-MM-DD"
    """
    os.chdir(os.getcwd())
    validate_cwd()

    from jessetk.refinepairs import run
    validateconfig()
    makedirs()
    run(dna_file, _start_date=start_date, _finish_date=finish_date)


@cli.command()
def score() -> None:
    """
    z
    """
    os.chdir(os.getcwd())
    validate_cwd()

    from jessetk.score import run
    validateconfig()
    makedirs()
    run()


# ///
@cli.command()
@click.argument('start_date', required=True, type=str)
@click.argument('finish_date', required=True, type=str)
def testpairs(start_date: str, finish_date: str) -> None:
    """
    backtest all candidate pairs. Enter in "YYYY-MM-DD" "YYYY-MM-DD"
    """

    # print in yellow color not implemented yet
    print('\x1b[33mNot implemented yet. Use old tool jesse-picker testpairs\x1b[0m')
    exit()

    os.chdir(os.getcwd())
    validate_cwd()

    # from jessepicker.testpairs import run
    from jessetk.testpairs import run
    validateconfig()
    makedirs()
    run(_start_date=start_date, _finish_date=finish_date)


@cli.command()
@click.argument('start_date', required=True, type=str)
@click.argument('finish_date', required=True, type=str)
@click.option('--debug/--no-debug', default=False,
              help='Displays logging messages instead of the progressbar. Used for debugging your strategy.')
@click.option('--csv/--no-csv', default=False,
              help='Outputs a CSV file of all executed trades on completion.')
@click.option('--json/--no-json', default=False,
              help='Outputs a JSON file of all executed trades on completion.')
@click.option('--fee/--no-fee', default=True,
              help='You can use "--no-fee" as a quick way to set trading fee to zero.')
@click.option('--chart/--no-chart', default=False,
              help='Generates charts of daily portfolio balance and assets price change. Useful for a visual comparision of your portfolio against the market.')
@click.option('--tradingview/--no-tradingview', default=False,
              help="Generates an output that can be copy-and-pasted into tradingview.com's pine-editor too see the trades in their charts.")
@click.option('--full-reports/--no-full-reports', default=False,
              help="Generates QuantStats' HTML output with metrics reports like Sharpe ratio, Win rate, Volatility, etc., and batch plotting for visualizing performance, drawdowns, rolling statistics, monthly returns, etc.")
@click.option(
    '--dna', default='None', show_default=True, help='Base32 encoded dna string payload')
@click.option(
    '--hp', default='None', show_default=True, help='Hyperparameters payload as dict')
@click.option(
    '--seq', default='None', show_default=True, help='Fixed width hyperparameters payload')
def backtest(start_date: str, finish_date: str, debug: bool, csv: bool, json: bool, fee: bool, chart: bool,
             tradingview: bool, full_reports: bool, dna: str, hp: str, seq: str) -> None:
    """
    backtest mode. Enter in "YYYY-MM-DD" "YYYY-MM-DD"
    """
    print('1')
    validate_cwd()

    config['app']['trading_mode'] = 'backtest'
    # register_custom_exception_handler()
    # debug flag
    config['app']['debug_mode'] = debug

    # fee flag
    if not fee:
        for e in config['app']['trading_exchanges']:
            config['env']['exchanges'][e]['fee'] = 0
            get_exchange(e).fee = 0
    # print(sys.argv)

    # for r in router.routes:
    #     hp_new = None

    #     StrategyClass = jh.get_strategy_class(r.strategy_name)
    #     r.strategy = StrategyClass()

    #     r.strategy.name = r.strategy_name
    #     r.strategy.exchange = r.exchange
    #     r.strategy.symbol = r.symbol
    #     r.strategy.timeframe = r.timeframe

    hp_new = None
    routes_dna = None
    decoded_base32_dna = None

    r = router.routes[0]
    StrategyClass = jh.get_strategy_class(r.strategy_name)
    r.strategy = StrategyClass()
    r.strategy.name = r.strategy_name
    r.strategy.exchange = r.exchange
    r.strategy.symbol = r.symbol
    r.strategy.timeframe = r.timeframe

    # Convert and inject regular DNA string to route
    if r.dna:  # and dna != 'None' and seq != 'None' and hp != 'None':
        routes_dna = dna
        hp_new = jh.dna_to_hp(r.strategy.hyperparameters(), r.dna)
        print(f'DNA: {r.dna} -> HP: {hp_new}')

    # Convert and inject base32 encoded DNA payload to route
    # r.dna is None and seq is None and hp is None:
    if dna != 'None' and hp_new is None:
        decoded_base32_dna = utils.decode_base32(dna)
        print('Decode base32', utils.decode_base32(dna))
        hp_new = jh.dna_to_hp(r.strategy.hyperparameters(), decoded_base32_dna)
        print(f'Base32 DNA: {dna} -> {hp_new}')

    # Convert and inject SEQ encoded payload to route
    # and hp_new is None and r.dna is None and dna is None and hp is None:
    if seq != 'None' and hp_new is None:
        seq_encoded = utils.decode_seq(seq)
        hp_new = {
            p['name']: int(val)
            for p, val in zip(r.strategy.hyperparameters(), seq_encoded)
        }


        # hp_new.update(hp)
        # print('New hp:', hp_new)
        # r.strategy.hp = hp_new
        print(f'SEQ: {seq} -> {hp_new}')

    hp_dict = None
    # Convert and inject HP (Json) payload to route
    # and hp_new is None and r.dna is None and dna is None and seq is None:
    if hp != 'None' and hp_new is None:
        hp_dict = json_lib.loads(hp.replace("'", '"').replace('%', '"'))
        hp_new = {p['name']: hp_dict[p['name']] for p in r.strategy.hyperparameters()}

            # hp_new.update(hp)
            # print('New hp:', hp_new)
            # print(f'Json HP: {hp} -> {hp_new}')

    # <-------------------------------

    # Inject Seq payload to route ->
    # if seq != 'None':
    #     print('Seq to decode:', seq)
    #     seq_encoded = utils.decode_seq(seq)

    #     for r in router.routes:
    #         StrategyClass = jh.get_strategy_class(r.strategy_name)
    #         r.strategy = StrategyClass()

    #         hp_new = {}

    #         for p, val in zip(r.strategy.hyperparameters(), seq_encoded):
    #             # r.strategy.hyperparameters()[p] = hp[p]
    #             # hp_new[p['name']] = hp[p]
    #             # print(p['name'], p['default'])
    #             hp_new[p['name']] = int(val)
    #         # hp_new.update(hp)
    #         # print('New hp:', hp_new)
    #         # r.strategy.hp = hp_new
    #         print('New hp:', hp_new)
    #         # sleep(5)
    # # <-------------------------------
    # Inject payload HP to route
    # refactor this shit
    # for r in router.routes:
    #     # print(r)
    #     StrategyClass = jh.get_strategy_class(r.strategy_name)
    #     r.strategy = StrategyClass()
    #     if hp != 'None':
    #         print('Payload: ', hp, 'type:', type(hp))

    #         hp_dict = json_lib.loads(hp.replace("'", '"').replace('%', '"'))

    #         print('Old hp:', r.strategy.hyperparameters())
    #         hp_new = {}

    #         for p in r.strategy.hyperparameters():
    #             # r.strategy.hyperparameters()[p] = hp[p]
    #             # hp_new[p['name']] = hp[p]
    #             # print(p['name'], p['default'])
    #             hp_new[p['name']] = hp_dict[p['name']]

    #         # hp_new.update(hp)
    #         # print('New hp:', hp_new)
    #         r.strategy.hp = hp_new

    # backtest_mode._initialized_strategies()
    backtest_mode.run(start_date, finish_date, chart=chart, tradingview=tradingview, csv=csv,
                      json=json, full_reports=full_reports, hyperparameters=hp_new)

    # Fix: Print out SeQ to console to help metrics module to grab it
    if seq != 'None':
        print('Sequential Hps:    |', seq)

    if hp != 'None':
        print('Sequential Hps:    |', hp)

    if decoded_base32_dna:
        print('Dna String:        |', decoded_base32_dna)

    if routes_dna:
        print('Dna String:        |', routes_dna)

    # try:    # Catch error when there's no trades.
    #     data = report.portfolio_metrics()
    #     print(data)
    #     print('*' * 50)
    #     print(type(data))
    #     print(data[0])
    # except:
    #     print('No Trades, no metrics!')

    db.close_connection()


def print_initial_msg():
    print(initial_test_message)


def makedirs():
    from jessetk.Vars import datadir

    os.makedirs(f'./{datadir}', exist_ok=True)
    os.makedirs(f'./{datadir}/results', exist_ok=True)
    os.makedirs(f'./{datadir}/logs', exist_ok=True)
    os.makedirs(f'./{datadir}/dnafiles', exist_ok=True)
    os.makedirs(f'./{datadir}/pairfiles', exist_ok=True)


def validateconfig():
    pass
    # if not (get_config('env.metrics.sharpe_ratio', False) and
    #         get_config('env.metrics.calmar_ratio', False) and
    #         get_config('env.metrics.winning_streak', False) and
    #         get_config('env.metrics.losing_streak', False) and
    #         get_config('env.metrics.largest_losing_trade', False) and
    #         get_config('env.metrics.largest_winning_trade', False) and
    #         get_config('env.metrics.total_winning_trades', False) and
    #         get_config('env.metrics.total_losing_trades', False)):
    #     print('Set optional metrics to True in config.py!')
    #     exit()

# @cli.command()
# @click.argument('dna_file', required=True, type=str)
# @click.argument('start_date', required=True, type=str)
# @click.argument('finish_date', required=True, type=str)
# @click.argument('eliminate', required=False, type=bool)
# def refine(dna_file, start_date: str, finish_date: str, eliminate: bool) -> None:
#     """
#     backtest all candidate dnas. Enter in "YYYY-MM-DD" "YYYY-MM-DD"
#     """
#     os.chdir(os.getcwd())
#     validate_cwd()
#     validateconfig()
#     makedirs()

#     if not eliminate:
#         eliminate = False

#     from jessetk.refine import refine
#     r = refine(dna_file, start_date, finish_date, eliminate)
#     r.run(dna_file, start_date, finish_date)
