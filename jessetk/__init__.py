import copy
import os
import sys
from pydoc import locate
from time import strftime, gmtime
from timeit import default_timer as timer

import click
import jesse.helpers as jh
from jesse.helpers import get_config
from jesse.routes import router
from jessetk import randomwalk, utils, Vars
from jessetk.Vars import initial_test_message, random_file_header, refine_file_header

# Python version validation.
if jh.python_version() < 3.7:
    print(
        jh.color(
            f'Jesse requires Python version above 3.7. Yours is {jh.python_version()}',
            'red'
        )
    )

# fix directory issue
sys.path.insert(0, os.getcwd())

ls = os.listdir('.')
is_jesse_project = 'strategies' in ls and 'config.py' in ls and 'storage' in ls and 'routes.py' in ls

clear_console = lambda: os.system('cls' if os.name in ('nt', 'dos') else 'clear')


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
    print('tk ########################')
    my_routes = [('Binance Futures', "AAVE-USDT", '5m', 'OttBands5minFixed2', 'XGaf\\')]
    print(my_routes)
    print('tk ########################')
    router.set_routes(my_routes)
    router.set_extra_candles(local_router.extra_candles)


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

    from jesse.routes import router
    import jesse.helpers as jh

    makedirs()
    r = router.routes[0]  # Read first route from routes.py
    strategy = r.strategy_name
    StrategyClass = jh.get_strategy_class(r.strategy_name)
    print('Strategy name:', strategy, 'Strategy Class:', StrategyClass)

    from jessetk.picker import picker

    dna_picker = picker(dna_log_file, strategy, StrategyClass, len1, len2, sort_criteria)

    dna_picker.sortdnas()
    dna_picker.create_output_file()
    dna_picker.validate_output_file()


@cli.command()
@click.argument('dna_file', required=True, type=str)
@click.argument('start_date', required=True, type=str)
@click.argument('finish_date', required=True, type=str)
@click.argument('eliminate', required=False, type=bool)
def refine(dna_file, start_date: str, finish_date: str, eliminate:bool) -> None:
    """
    backtest all candidate dnas. Enter in "YYYY-MM-DD" "YYYY-MM-DD"
    """
    os.chdir(os.getcwd())
    validate_cwd()
    validateconfig()
    makedirs()

    if not eliminate:
        eliminate = False

    from jessetk.refine import refine
    r = refine(dna_file, start_date, finish_date, eliminate)
    r.run(dna_file, start_date, finish_date)


@cli.command()
@click.argument('start_date', required=True, type=str)
@click.argument('finish_date', required=True, type=str)
@click.argument('iterations', required=False, type=int)
@click.argument('width', required=False, type=int)
def random(start_date: str, finish_date: str, iterations: int, width: int) -> None:
    """
    random walk backtest. Enter period "YYYY-MM-DD" "YYYY-MM-DD
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
        iterations = 30
        print('Iterations not provided, falling back to 30 iters!')
    if not width:
        width = 30
        print(f'Window width not provided, falling back to {width} days window!')

    from jessetk.randomwalk import RandomWalk
    random_walk = RandomWalk(start_date, finish_date, iterations, width)

    print_initial_msg()
    start = timer()
    results = []
    for index in range(1, iterations + 1):
        rand_period_start, rand_period_finish = random_walk.make_random_period()  # Create a random period between given period

        # Run jesse backtest and grab console output
        console_output = utils.run_test(rand_period_start, rand_period_finish)

        # Scrape console output and return metrics as a dict
        metric = utils.get_metrics3(console_output)

        # Shared values TODO Make it common for all tools
        metric['dna'] = random_walk.dna
        metric['exchange'] = random_walk.exchange
        metric['symbol'] = random_walk.symbol
        metric['tf'] = random_walk.timeframe

        # Add test specific values
        metric['start_date'] = rand_period_start
        metric['finish_date'] = rand_period_finish

        if metric not in results:
            results.append(copy.deepcopy(metric))
        # f.write(str(metric) + '\n')  # Logging disabled
        # f.flush()
        random_walk.sorted_results = sorted(results, key=lambda x: float(x['serenity']), reverse=True)

        eta = ((timer() - start) / index) * (iterations - index)
        eta_formatted = strftime("%H:%M:%S", gmtime(eta))

        clear_console()
        print(
            f'{index}/{iterations}\teta: {eta_formatted} | {random_walk.exchange} '
            f'| {random_walk.symbol} | {random_walk.timeframe} | {repr(random_walk.dna)} '
            f'| Period: {start_date} -> {finish_date} | Sample width: {width}')

        random_walk.print_tops_formatted()

    utils.create_csv_report(random_walk.sorted_results, random_walk.report_file_name, random_file_header)

@cli.command()
@click.argument('dna_file', required=True, type=str)
@click.argument('start_date', required=True, type=str)
@click.argument('finish_date', required=True, type=str)
@click.argument('iterations', required=False, type=int)
@click.argument('width', required=False, type=int)
def randomsg(dna_file, start_date: str, finish_date: str, iterations: int, width: int) -> None:
    """
    random walk backtest. Enter period "YYYY-MM-DD" "YYYY-MM-DD
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
        print(f'Window width not provided, falling back to {width} days window!')

    from jessetk.randomwalk import RandomWalk
    random_walk = RandomWalk(start_date, finish_date, iterations, width)
    from jessetk.refine import refine

    print_initial_msg()
    # start = timer()
    results = []
    for _ in range(1, iterations + 1):
        rand_period_start, rand_period_finish = random_walk.make_random_period()  # Create a random period between given period

        r = refine(dna_file, rand_period_start, rand_period_finish, eliminate=True)
        r.run(dna_file, rand_period_start, rand_period_finish)

        if len(r.sorted_results) <= 5:
            print('Target reached, exiting...')
            break

        # eta = ((timer() - start) / index) * (iterations - index)
        # eta_formatted = strftime("%H:%M:%S", gmtime(eta))



# // *
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


# // *

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


@cli.command()
def fixcsv() -> None:
    """
    z
    """
    os.chdir(os.getcwd())
    validate_cwd()

    from jessetk.fixCsv import run
    # validateconfig()
    # makedirs()
    run()


# ///
@cli.command()
@click.argument('start_date', required=True, type=str)
@click.argument('finish_date', required=True, type=str)
def testpairs(start_date: str, finish_date: str) -> None:
    """
    backtest all candidate pairs. Enter in "YYYY-MM-DD" "YYYY-MM-DD"
    """
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
def backtest(start_date: str, finish_date: str, debug: bool, csv: bool, json: bool, fee: bool, chart: bool,
             tradingview: bool, full_reports: bool) -> None:
    """
    backtest mode. Enter in "YYYY-MM-DD" "YYYY-MM-DD"
    """
    validate_cwd()
    from jesse.services import report

    # router.routes[0].strategy_name
    # router.routes[0].exchange
    # router.set_routes(local_router.routes)
    # router.set_extra_candles(local_router.extra_candles)
    # inject local files

    # router.routes[0].symbol = 'MATIC-USDT'

    # print(router.routes[0].__dict__)
    # exit()
    # router.routes[0].timeframe

    from jesse.config import config
    config['app']['trading_mode'] = 'backtest'
    # register_custom_exception_handler()
    from jesse.services import db
    from jesse.modes import backtest_mode
    from jesse.services.selectors import get_exchange

    # debug flag
    config['app']['debug_mode'] = debug

    # fee flag
    if not fee:
        for e in config['app']['trading_exchanges']:
            config['env']['exchanges'][e]['fee'] = 0
            get_exchange(e).fee = 0

    # if is_jesse_project:
    #     inject_local_config()
    #     inject_local_routes()

    print(router.routes[0].__dict__)

    print('************ BEFORE ****************')
    print(config['app']['considering_candles'], '/////////////////////////////////////')
    print(config['app']['trading_symbols'], '/////////////////////////////////////')
    print('************ AFTER ****************')
    # config['app']['considering_candles'] = (('Binance Futures', 'MATIC-USDT'),)
    # config['app']['trading_symbols'] = ("MATIC-USDT",)

    print(config['app']['considering_candles'], '/////////////////////////////////////')
    print(config['app']['trading_symbols'], '/////////////////////////////////////')

    # backtest_mode._initialized_strategies()

    backtest_mode.run(start_date, finish_date, chart=chart, tradingview=tradingview, csv=csv,
                      json=json, full_reports=full_reports)

    data = report.portfolio_metrics()
    print(data)
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


def validateconfig():  # TODO Modify config without user interaction!
    if not (get_config('env.metrics.sharpe_ratio', False) and
            get_config('env.metrics.calmar_ratio', False) and
            get_config('env.metrics.winning_streak', False) and
            get_config('env.metrics.losing_streak', False) and
            get_config('env.metrics.largest_losing_trade', False) and
            get_config('env.metrics.largest_winning_trade', False) and
            get_config('env.metrics.total_winning_trades', False) and
            get_config('env.metrics.total_losing_trades', False)):
        print('Set optional metrics to True in config.py!')
        exit()
