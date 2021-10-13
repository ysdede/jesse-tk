import copy
import os
import sys
from time import strftime, gmtime
from timeit import default_timer as timer

import click
# Hide the "FutureWarning: pandas.util.testing is deprecated." caused by empyrical
import jesse.helpers as jh
from jesse.helpers import get_config

from jessetk import timemachine, utils, Vars

# Python version validation.
# from jessepicker import timemachine
# from jessepicker.dnasorter import sortdnas, valideoutputfile
# from jessetk.pick import sortdnas, validate_output_file

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
    # from jessepicker.dnasorter import sortdnas, valideoutputfile

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
def refine(dna_file, start_date: str, finish_date: str) -> None:
    """
    backtest all candidate dnas. Enter in "YYYY-MM-DD" "YYYY-MM-DD"
    """
    os.chdir(os.getcwd())
    validate_cwd()
    validateconfig()
    makedirs()
    print('Please wait while performing initial test...')
    from jessetk.refine import refine

    refiner = refine(dna_file, start_date, finish_date)

    refiner.import_dnas()
    refiner.routes_template = utils.read_file('routes.py')

    results = []
    start = timer()

    for index, dnac in enumerate(refiner.dnas, start=1):

        # Inject dna to routes.py
        utils.make_routes(refiner.routes_template, refiner.anchor, dna_code=dnac[0])

        # Run jesse backtest and grab console output
        console_output = refiner.run_test()

        # Scrape console output and return metrics as a dict
        metric = utils.get_metrics3(console_output)

        # Add test specific static values
        metric['dna'] = dnac[0]
        metric['symbol'] = refiner.pair
        metric['tf'] = refiner.timeframe
        metric['start_date'] = refiner.start_date
        metric['finish_date'] = refiner.finish_date

        if metric not in results:
            results.append(copy.deepcopy(metric))

        # f.write(str(metric) + '\n')  # Logging
        # f.flush()

        refiner.sorted_results = sorted(results, key=lambda x: float(x['serenity']), reverse=True)

        clear_console()

        rt = ((timer() - start) / index) * (refiner.n_of_dnas - index)
        eta_formatted = strftime("%H:%M:%S", gmtime(rt))
        print(
            f'{index}/{refiner.n_of_dnas}\teta: {eta_formatted} | {refiner.pair} '
            f'| {refiner.timeframe} | {refiner.start_date} -> {refiner.finish_date}')

        refiner.print_tops_formatted(refiner.sorted_results[0:30])

    # Restore routes.py
    utils.write_file('routes.py', refiner.routes_template)
    refiner.save_dnas(refiner.sorted_results)
    refiner.create_csv_report(refiner.sorted_results)

    # # Sync and close log file
    # os.fsync(f.fileno())
    # f.close()


@cli.command()
@click.argument('start_date', required=True, type=str)
@click.argument('finish_date', required=True, type=str)
@click.argument('iterations', required=False, type=int)
@click.argument('days', required=False, type=int)
def random(start_date: str, finish_date: str, iterations: int, days: int) -> None:
    """
    random walk backtest. Enter period "YYYY-MM-DD" "YYYY-MM-DD
                                iterations eg. 100
                                window width in days eg 180"
    """
    os.chdir(os.getcwd())
    validate_cwd()
    validateconfig()
    from jesse.routes import router
    import jesse.helpers as jh

    r = router.routes[0]  # Read first route from routes.py
    timeframe = r.timeframe

    if start_date is None or finish_date is None:
        print('Enter dates!')
        exit()

    if not iterations:
        iterations = 30
        print('Iterations not provided, falling back to 30 iters!')
    if not days:
        days = 60
        print('Window width not provided, falling back to 60 days window!')

    width = (24 / (jh.timeframe_to_one_minutes(timeframe) / 60)) * days

    makedirs()
    timemachine.run(_start_date=start_date, _finish_date=finish_date, _iterations=iterations, _width=width)


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

    # from jessepicker.refinepairs import run
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


# ///


def makedirs():
    jessetkdir = 'jessetkdata'

    os.makedirs(f'./{jessetkdir}', exist_ok=True)
    os.makedirs(f'./{jessetkdir}/results', exist_ok=True)
    os.makedirs(f'./{jessetkdir}/logs', exist_ok=True)
    os.makedirs(f'./{jessetkdir}/dnafiles', exist_ok=True)
    os.makedirs(f'./{jessetkdir}/pairfiles', exist_ok=True)


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
