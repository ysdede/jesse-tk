import copy
import importlib
import os
import sys
from datetime import datetime
from time import strftime, gmtime
from timeit import default_timer as timer

from jesse.routes import router

import jessetk.Vars as Vars
import jessetk.utils
from jessetk import utils, print_initial_msg, clear_console
from jessetk.Vars import datadir
from jessetk.Vars import refine_file_header


class refine:
    def __init__(self, dna_py_file, start_date, finish_date, eliminate: bool = False):
        import signal

        signal.signal(signal.SIGINT, self.signal_handler)

        self.jessetkdir = datadir
        self.dna_py_file = dna_py_file
        self.start_date = start_date
        self.finish_date = finish_date
        self.eliminate = eliminate
        self.anchor = 'DNA!'
        self.sort_by = {'serenity': 12, 'sharpe': 13, 'calmar': 14}

        self.results = []
        self.sorted_results = []
        self.results_without_dna = []

        self.dnas_module = None
        self.routes_template = None
        self.dnas = None
        self.n_of_dnas = None

        r = router.routes[0]  # Read first route from routes.py
        print('r.symbol', r.symbol)
        # exit()
        self.exchange = r.exchange
        self.pair = r.symbol
        print('Pair:', self.pair)
        self.timeframe = r.timeframe
        self.strategy = r.strategy_name

        self.removesimilardnas = False

        self.clear_console = lambda: os.system('cls' if os.name in ('nt', 'dos') else 'clear')

        self.ts = datetime.now().strftime("%Y%m%d %H%M%S")
        # TODO Create results, logs, dnafiles folders if needed.
        self.filename = f'Refine-{self.exchange}-{self.pair}-{self.timeframe}--{start_date}--{finish_date}'

        self.report_file_name = f'{self.jessetkdir}/results/{self.filename}--{self.ts}.csv'
        self.log_file_name = f'{self.jessetkdir}/logs/{self.filename}--{self.ts}.log'

    def run(self, dna_file: str, start_date: str, finish_date: str):
        # from jessetk.refine import refine
        # refiner = refine(dna_file, start_date, finish_date)
        self.import_dnas()
        self.routes_template = utils.read_file('routes.py')
        
        results = []
        start = timer()
        print_initial_msg()
        for index, dnac in enumerate(self.dnas, start=1):
            # Inject dna to routes.py
            utils.make_routes(self.routes_template, self.anchor, dna_code=dnac[0])

            # Run jesse backtest and grab console output
            console_output = utils.run_test(start_date, finish_date)

            # Scrape console output and return metrics as a dict
            metric = utils.get_metrics3(console_output)

            # Add test specific static values
            metric['dna'] = dnac[0]
            metric['exchange'] = self.exchange
            metric['symbol'] = self.pair
            metric['tf'] = self.timeframe
            metric['start_date'] = self.start_date
            metric['finish_date'] = self.finish_date

            if metric not in results:
                results.append(copy.deepcopy(metric))
            # f.write(str(metric) + '\n')  # Logging disabled
            # f.flush()
            sorted_results_prelist = sorted(results, key=lambda x: float(x['sharpe']), reverse=True)
            self.sorted_results = []

            if self.eliminate:
                for r in sorted_results_prelist:
                    if float(r['sharpe']) > 0:
                        self.sorted_results.append(r)
            else:
                self.sorted_results = sorted_results_prelist

            clear_console()

            eta = ((timer() - start) / index) * (self.n_of_dnas - index)
            eta_formatted = strftime("%H:%M:%S", gmtime(eta))
            print(
                f'{index}/{self.n_of_dnas}\teta: {eta_formatted} | {self.pair} '
                f'| {self.timeframe} | {self.start_date} -> {self.finish_date}')

            self.print_tops_formatted()

        utils.write_file('routes.py', self.routes_template)  # Restore routes.py

        if self.eliminate:
            self.save_dnas(self.sorted_results, dna_file)
        else:
            self.save_dnas(self.sorted_results)

        utils.create_csv_report(self.sorted_results, self.report_file_name, refine_file_header)
        # # Sync and close log file
        # os.fsync(f.fileno())
        # f.close()

    def signal_handler(self, sig, frame):
        print('You pressed Ctrl+C!')
        # Restore routes.py
        jessetk.utils.write_file('routes.py', self.routes_template)
        sys.exit(0)

    def import_dnas(self):
        module_name = self.dna_py_file.replace('\\', '.').replace('.py', '')
        module_name = module_name.replace('/', '.').replace('.py', '')
        print(module_name)

        self.dnas_module = importlib.import_module(module_name)
        importlib.reload(self.dnas_module)
        self.dnas = self.dnas_module.dnas

        self.n_of_dnas = len(self.dnas)

    def print_tops_formatted(self):
        print(
            Vars.refine_console_formatter.format(*Vars.refine_console_header1))
        print(
            Vars.refine_console_formatter.format(*Vars.refine_console_header2))

        for r in self.sorted_results[0:40]:
            print(
                Vars.refine_console_formatter.format(
                    r['dna'],
                    r['total_trades'],
                    r['n_of_longs'],
                    r['n_of_shorts'],
                    r['total_profit'],
                    r['max_dd'],
                    r['annual_return'],
                    r['win_rate'],
                    r['serenity'],
                    r['sharpe'],
                    r['calmar'],
                    r['win_strk'],
                    r['lose_strk'],
                    r['largest_win'],
                    r['largest_lose'],
                    r['n_of_wins'],
                    r['n_of_loses'],
                    r['paid_fees'],
                    r['market_change']))

    def save_dnas(self, sorted_results, dna_fn=None):

        if not dna_fn:
            dna_fn = f'{self.jessetkdir}/dnafiles/{self.pair} {self.start_date} {self.finish_date}.py'

        jessetk.utils.remove_file(dna_fn)

        with open(dna_fn, 'w', encoding='utf-8') as f:
            self.write_dna_file(f, sorted_results)

    def write_dna_file(self, f, sorted_results):
        f.write('dnas = [\n')

        for srr in sorted_results:
            for dnac in self.dnas:
                if srr['dna'] == dnac[0]:
                    f.write(str(dnac) + ',\n')

        f.write(']\n')
        f.flush()
        os.fsync(f.fileno())
