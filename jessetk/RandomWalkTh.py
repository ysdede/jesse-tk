import random
from copy import deepcopy
from datetime import datetime, timedelta
from multiprocessing import cpu_count
from subprocess import PIPE, Popen
from time import gmtime, strftime
from timeit import default_timer as timer

from jesse.routes import router

import jessetk.Vars as Vars
from jessetk import utils
from jessetk.utils import clear_console
from jessetk.Vars import datadir, random_file_header


# Random walk backtesting w/ threading
class RandomWalk:
    def __init__(self, start_date, finish_date, n_of_iters, width, cpu):
        self.start_date = start_date
        self.finish_date = finish_date
        self.n_of_iters = n_of_iters
        self.width = width
        self.cpu = cpu

        self.jessetkdir = datadir
        self.max_retries = 6

        self.start_date_object = datetime.strptime(start_date,
                                                   '%Y-%m-%d')  # start_date as datetime object, to make calculations easier.
        self.finish_date_object = datetime.strptime(finish_date, '%Y-%m-%d')
        self.test_period_length = self.finish_date_object - \
            self.start_date_object  # Test period length as days
        self.rand_end = self.test_period_length - \
            timedelta(days=width)  # period - windows width

        self.results = []
        self.sorted_results = []
        self.random_numbers = []

        r = router.routes[0]  # Read first route from routes.py
        self.strategy = r.strategy_name  # get strategy name to create filenames
        self.exchange = r.exchange
        self.pair = self.symbol = r.symbol
        self.timeframe = r.timeframe
        self.dna = r.dna

        self.ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.filename = f'Random-{self.strategy}-{start_date}--{finish_date}-{self.ts}'
        self.report_file_name = f'{self.jessetkdir}/results/{self.filename}.csv'
        self.log_file_name = f'{self.jessetkdir}/logs/{self.filename}--{self.ts}.log'

    def run(self):
        max_cpu = self.cpu
        iters = self.n_of_iters
        width = self.width
        processes = []
        commands = []
        results = []
        sorted_results = []
        iters_completed = 0

        start = timer()
        while iters > 0:
            commands = []
            for _ in range(max_cpu):
                if iters > 0:
                    # Create a random period between given period
                    rand_period_start, rand_period_finish = self.make_random_period()
                    commands.append(
                        f'jesse-tk backtest {rand_period_start} {rand_period_finish}')
                    iters -= 1

            processes = [Popen(cmd, stdout=PIPE) for cmd in commands]
            # wait for completion
            for p in processes:
                p.wait()

                # Get thread's console output
                (output, err) = p.communicate()
                iters_completed += 1

                # Map console output to a dict
                metric = utils.get_metrics3(output.decode('utf-8'))

                if metric not in results:
                    results.append(deepcopy(metric))

                sorted_results = sorted(
                    results, key=lambda x: float(x['serenity']), reverse=True)

                eta_per_iter = (timer() - start) / iters_completed
                speed = round(width / eta_per_iter, 2)
                eta = eta_per_iter * (self.n_of_iters - iters)         # remaining
                remaining_time = eta_per_iter * self.n_of_iters        # estimated total time
                eta_formatted = strftime("%H:%M:%S", gmtime(eta))
                remaining_formatted = strftime("%H:%M:%S", gmtime(remaining_time))

                clear_console()

                print(
                    f'{iters_completed}/{self.n_of_iters}\teta: {eta_formatted}/{remaining_formatted} | Speed: {speed} days/sec | {metric["exchange"]} '
                    f'| {metric["symbol"]} | {metric["tf"]} | {repr(metric["dna"])} '
                    f'| Period: {self.start_date} -> {self.finish_date} | Sample width: {self.width} v7')

                metric = {}
                utils.print_random_tops(sorted_results, 40)


        utils.create_csv_report(
            sorted_results, self.report_file_name, random_file_header)

    def make_random_period(self):
        random_number = None

        for _ in range(self.max_retries):
            random_number = random.randint(
                0, self.rand_end.days)  # TODO Quantum random?
            if random_number not in self.random_numbers:
                break

        self.random_numbers.append(random_number)

        random_start_date = self.start_date_object + timedelta(
            days=random_number)  # Add random number of days to start date
        random_finish_date = random_start_date + timedelta(days=self.width)
        return random_start_date.strftime('%Y-%m-%d'), random_finish_date.strftime('%Y-%m-%d')
