import os
import sys

import click
# Hide the "FutureWarning: pandas.util.testing is deprecated." caused by empyrical
import jesse.helpers as jh
from jesse.helpers import get_config

from jessetk import timemachine

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

    from jessetk.refine import refine
    refiner = refine(dna_file, start_date, finish_date)
    refiner.run_refine()


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
