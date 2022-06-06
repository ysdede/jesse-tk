import importlib
import os
import sys
from copy import deepcopy
from datetime import datetime
from subprocess import PIPE, Popen, call
from time import sleep, strftime, gmtime
from timeit import default_timer as timer
from jesse.routes import router
import jessetk.Vars as Vars
import jessetk.utils
from jessetk.Vars import datadir
from jessetk.Vars import refine_file_header
import json
from millify import millify


class PureRefine:
    def __init__(self):

        import signal
        signal.signal(signal.SIGINT, self.signal_handler)

        self.exchange = None
        self.pair = None
        self.timeframe = None
        self.strategy = None

        self.sort_by = {'serenity': 12, 'sharpe': 13, 'calmar': 14}
        self.n_of_iters = 0
        self.hps_module = None

        self.removesimilardnas = False

    def get_routes_info(self):
        r = router.routes[0]  # Read first route from routes.py
        self.exchange = r.exchange
        self.pair = r.symbol
        self.timeframe = r.timeframe
        self.strategy = r.strategy_name

    def sort_hps(self, hps):
        """Sort hyperparameters as defined in the strategy"""
        r = router.routes[0]  # Read first route from routes.py
        new_hps = []
        for hp in hps:
            hp_new = {}
            for p in r.strategy.hyperparameters():
                try:
                    hp_new[p['name']] = hp[p['name']]
                except:
                    pass
            new_hps.append(hp_new)
        return new_hps

    def run(self, hps = None, seq = None, start_date: str = None, finish_date: str = None, eliminate: bool = False, cpu = None, mr = None, full_reports = None):
        if not isinstance(hps, list) ^ isinstance(seq, list):
            print('No hps or seq provided or both provided. Please provide either hps or seq.')
            return
        
        if not start_date or not finish_date:
            print('No start_date or finish_date provided')
            return
        
        cpu = jessetk.utils.cpu_info(cpu)
        fr = ' --full-reports' if full_reports else ''

        if hps:
            print(f"{len(hps)=}")
            hps = self.sort_hps(hps)
            print(f"After sort: {len(hps)=}")

        # If seq is provided, create hps from seq
        # if not hps and seq:
        #     print('Creating hps from seq')
        #     hps = []
        #     for s in seq:
        #         hps.append[jessetk.utils.decode_seq(s)]

        if not seq and hps:
            print('Creating seq codes from hps')
            seq = []
            for hp in hps:
                seq.append(jessetk.utils.hp_to_seq(hp))

        self.ts = datetime.now().strftime("%Y%m%d %H%M%S")
        self.filename = f'RefineHp-{self.exchange}-{self.pair}-{self.timeframe}--{start_date}--{finish_date}'
        self.report_file_name = f'{datadir}/results/{self.filename}--{self.ts}.csv'
        self.log_file_name = f'{datadir}/logs/{self.filename}--{self.ts}.log'
        
        processes = []
        commands = []
        results = []
        sorted_results = []
        iters_completed = 0
        self.n_of_iters = self.n_of_params = iters = len(seq)
        index = 0  # TODO Reduce number of vars ...
        start = timer()
        
        # for s in seq:
        #     print(s)
        # sleep(10)

        while iters > 0:
            commands = []

            for _ in range(cpu):
                if iters > 0:
                    s = seq[index]  # json.dumps(hps[index])

                    # hps = json.dumps(hps).replace('"', '%')
                    # print(f'parameters: {hps}')

                    commands.append(
                        f'jesse-tk backtest {start_date} {finish_date} --seq {s}{fr}'
                        )

                    index += 1
                    iters -= 1
            print(commands)
            processes = [Popen(cmd, shell=True, stdout=PIPE) for cmd in commands]

            # wait for completion
            for p in processes:
                p.wait()

                # Get thread's console output
                (output, err) = p.communicate()
                # debug
                # print(output.decode('utf-8'))
                # print(err.decode('utf-8'))
                # exit()
                iters_completed += 1

                # Map console output to a dict
                metric =jessetk.utils.get_metrics3(output.decode('utf-8'))
                metric['dna'] =  metric['seq_hps']

                # print('Metrics decoded', len(metric))
                print('Len results', len(results))
                if metric not in results:
                    results.append(deepcopy(metric))

                sorted_results_prelist = sorted(results, key=lambda x: float(x['pmr']), reverse=True)
                # print(f'Sorted results: {sorted_results_prelist}')
                # print('Sorted results', len(sorted_results_prelist))

                self.sorted_results = sorted_results_prelist

                jessetk.utils.clear_console()

                eta = ((timer() - start) / index) * (self.n_of_params - index)
                eta_formatted = strftime("%H:%M:%S", gmtime(eta))

                print(
                    f'{index}/{self.n_of_params}\teta: {eta_formatted} | {self.pair} '
                    f'| {self.timeframe} | {start_date} -> {finish_date}')

                self.print_tops_formatted(sorted_results_prelist, 40)

        # if self.eliminate:
        #     self.save_dnas(self.sorted_results, self.dna_py_file)
        # else:
        #     self.save_dnas(self.sorted_results)

        # self.save_seq(self.sorted_results)

        # candidates = {
        #     r['dna']: r['dna']
        #     for r in self.sorted_results
        #     if r['max_dd'] > self.dd
        # }


        # with open(f'SEQ-{self.pair}-{self.strategy}-{self.start_date}-{self.finish_date}.py', 'w') as f:
        #     f.write("hps = ")
        #     f.write(json.dumps(candidates, indent=1))

        # utils.create_csv_report(self.sorted_results,
        #                         self.report_file_name, refine_file_header)

    def signal_handler(self, sig, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)
        
    # v TODO Move to utils
    def print_tops_formatted(self, sorted_results=None, n:int = 25):
        print(
            Vars.refine_console_formatter.format(*Vars.refine_console_header1))
        print(
            Vars.refine_console_formatter.format(*Vars.refine_console_header2))

        for r in sorted_results[:n]:
            p = r
            # Replace None with empty string
            for k, v in p.items():
                if v is None:
                    p[k] = ''

            # p = {}
            # # make a copy of r dict but round values if they are floats
            # for k, v in r.items():
            #     try:
            #         if type(v) is float and v > 999999:
            #             p[k] = millify(v, 2)
            #         elif type(v) is float and abs(v) > 999:
            #             p[k] = round(v)
            #         else:
            #             p[k] = v
            #     except:
            #         p[k] = v

            # for i in range(len(r)):
            #     if isinstance(r[i], float) and r[i] > 999999:
            #         p.append(millify(round(r[i]), 2))  # '{:.2f}'.format(r[i])
            #     # elif isinstance(r[i], float) and r[i] > 1000:
            #     #     p.append(round(r[i], 2))
            #     else:
            #         p.append(r[i])

            print(
                Vars.refine_console_formatter.format(
                    p['dna'],
                    p['total_trades'],
                    p['n_of_longs'],
                    p['n_of_shorts'],
                    p['total_profit'],
                    p['max_margin_ratio'],
                    p['pmr'],
                    p['lpr'],
                    p['insuff_margin_count'],
                    p['max_dd'],
                    p['annual_return'],
                    p['win_rate'],
                    p['serenity'],
                    p['sharpe'],
                    p['calmar'],
                    p['win_strk'],
                    p['lose_strk'],
                    p['largest_win'],
                    p['largest_lose'],
                    p['n_of_wins'],
                    p['n_of_loses'],
                    p['paid_fees'],
                    p['market_change']))

    def save_dnas(self, sorted_results, dna_fn=None):

        if not dna_fn:
            dna_fn = f'{datadir}/dnafiles/{self.pair} {self.start_date} {self.finish_date}.py'

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
