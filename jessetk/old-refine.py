import copy
import importlib
import os
import sys
from datetime import datetime
from subprocess import Popen, PIPE
from time import gmtime
from time import strftime
from timeit import default_timer as timer

from jesse.routes import router
import jessetk.Vars as Vars
import jessetk.utils


def print_tops_formatted(frmt, header1, header2, tr):
    print(
        frmt.format(*header1))
    print(
        frmt.format(*header2))

    for r in tr:
        print(
            frmt.format(
                r['dna'], r['total_trades'],
                r['n_of_longs'], r['n_of_shorts'],
                r['total_profit'], r['max_dd'],
                r['annual_return'], r['win_rate'],
                r['serenity'], r['sharpe'], r['calmar'],
                r['win_strk'], r['lose_strk'],
                r['largest_win'], r['largest_lose'],
                r['n_of_wins'], r['n_of_loses'],
                r['paid_fees'], r['market_change']))


class refine:
    def __init__(self, dna_py_file, start_date, finish_date):
        import signal

        signal.signal(signal.SIGINT, self.signal_handler)

        self.jessetkdir = 'jessetkdata'
        self.dna_py_file = dna_py_file
        self.start_date = start_date
        self.finish_date = finish_date

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
        self.filename = f'{self.exchange}-{self.pair}-{self.timeframe}--{start_date}--{finish_date}'

        self.report_file_name = f'{self.jessetkdir}/results/{self.filename}--{self.ts}.csv'
        self.log_file_name = f'{self.jessetkdir}/logs/{self.filename}--{self.ts}.log'

        # make routes unutma

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
        self.dnas = self.dnas_module.dnas

        self.n_of_dnas = len(self.dnas)

    def run_refine(self):
        # f = open(self.log_file_name, 'w', encoding='utf-8')
        # f.write(str(self.file_header) + '\n')

        self.import_dnas()

        # Read initial routes.py file as template
        self.routes_template = jessetk.utils.read_file('routes.py')
        results = []
        start = timer()

        for index, dnac in enumerate(self.dnas, start=1):

            # Inject dna to routes.py
            jessetk.utils.make_routes(self.routes_template, self.anchor, dna_code=dnac[0])

            # Run jesse backtest and grab console output
            console_output = self.run_test()

            # Scrape console output and return metrics as a dict
            metric = jessetk.utils.get_metrics3(console_output)
            metric['dna'] = dnac[0]
            metric['symbol'] = self.pair
            metric['tf'] = self.timeframe

            if metric not in results:
                results.append(copy.deepcopy(metric))

            # f.write(str(metric) + '\n')  # Logging
            # f.flush()

            self.sorted_results = sorted(results, key=lambda x: float(x['serenity']), reverse=True)

            self.clear_console()

            rt = ((timer() - start) / index) * (self.n_of_dnas - index)
            eta_formatted = strftime("%H:%M:%S", gmtime(rt))
            print(
                f'{index}/{self.n_of_dnas}\teta: {eta_formatted} | {self.pair} '
                f'| {self.timeframe} | {self.start_date} -> {self.finish_date}')

            print_tops_formatted(Vars.refine_console_formatter,
                                 Vars.refine_console_header1,
                                 Vars.refine_console_header2,
                                 self.sorted_results[0:30])

            # delta = timer() - start

        # Restore routes.py
        jessetk.utils.write_file('routes.py', self.routes_template)

        # # Sync and close log file
        # os.fsync(f.fileno())
        # f.close()

        self.save_dnas(self.sorted_results)
        self.create_csv_report(self.sorted_results)

    def run_test(self):
        process = Popen(['jesse', 'backtest', self.start_date, self.finish_date], stdout=PIPE)
        (output, err) = process.communicate()
        exit_code = process.wait()
        return output.decode('utf-8')

    def create_csv_report(self, sorted_results):
        with open(self.report_file_name, 'w', encoding='utf-8') as f:
            f.write(str(Vars.refine_file_header).replace('[', '').replace(']', '').replace(' ', '') + '\n')

            for srline in sorted_results:
                f.write(str(srline).replace('[', '').replace(']', '').replace(' ', '') + '\n')
            os.fsync(f.fileno())

    def save_dnas(self, sorted_results):
        dna_fn = f'{self.jessetkdir}/dnafiles/{self.pair} {self.start_date} {self.finish_date}.py'

        jessetk.utils.remove_file(dna_fn)

        with open(dna_fn, 'w', encoding='utf-8') as f:
            self.write_dna_file(f, sorted_results)

    def write_dna_file(self, f, sorted_results):
        f.write('dnas = [\n')

        for srr in sorted_results:
            for dnac in self.dnas:
                # if srr[2] == dnac[0]:
                if srr['dna'] == dnac[0]:
                    f.write(str(dnac) + ',\n')

        f.write(']\n')
        f.flush()
        os.fsync(f.fileno())
