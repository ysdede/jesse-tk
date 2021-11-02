import importlib
import os

import jesse.helpers as jh

from jessetk.Vars import datadir


def sort_array_by_key(rows, sort_key):
    return sorted(rows, key=lambda x: int(x[sort_key]), reverse=True)


class picker:
    def __init__(self, dna_log_file, strategy, strategy_class, len1, len2, criteria):
        self.jessetkdir = datadir
        self.dna_log_file = dna_log_file
        self.strategy = strategy
        self.strategy_class = strategy_class
        self.len1 = len1
        self.len2 = len2
        self.log_body = None
        self.rows = None
        self.fit_rows = None
        self.besties = None
        self.best_dnas_sorted = None

        self.sorted_by_pnl1 = None
        self.sorted_by_pnl2 = None
        self.sorted_by_wr1 = None
        self.sorted_by_wr2 = None

        self.dna_fn = f'{self.jessetkdir}/dnafiles/{strategy}dnas.py'

        self.sort_criterias = ('pnl1', 'pnl2', 'wr1', 'wr2')
        pnl1, pnl2, wr1, wr2 = 3, 6, 1, 4

        self.sort_by = {'pnl1': pnl1, 'pnl2': pnl2, 'wr1': wr1, 'wr2': wr2}

        self.criteria = criteria.lower()
        # Accept only 'pnl1', 'pnl2', 'wr1', 'wr2' as sort criteria, if it's not in list use pnl1 as default.
        if criteria not in self.sort_criterias:
            print('Unknown sort criteria, using pnl1 as default.')
            self.criteria = 'pnl1'

    def read_log(self):
        with open(self.dna_log_file, 'r') as ff:
            self.log_body = ff.read()

    def pick_lines(self, limit: int = 0):
        rows = []
        lines = self.log_body.splitlines()

        llines = lines[-limit:] if limit != 0 else lines

        for index, line in enumerate(llines):

            if '|| win-rate:' in line:
                ll = line.replace('%', '')
                ll = ll.split('total:')
                dna = ll[0].split(' == ')[1].replace(' ', '')

                winrate1 = ll[0].split('win-rate')[1].replace(' ', '').replace(',', '').replace(':', '').replace('None',
                                                                                                                 '0')
                winrate2 = ll[1].split('win-rate')[1].replace(' ', '').replace(',', '').replace(':', '').replace('None',
                                                                                                                 '0')
                pnl1 = ll[1].split(' ')[3].replace(' ', '').replace('None', '0')
                pnl2 = ll[2].split(' ')[3].replace(' ', '').replace('None', '0')
                total1 = ll[1].split(' ')[1].replace(' ', '').replace(',', '').replace('None', '0')
                total2 = ll[2].split(' ')[1].replace(' ', '').replace(',', '').replace('None', '0')

                row = [dna, int(winrate1), int(total1), float(pnl1), int(winrate2), int(total2), float(pnl2)]
                if row not in rows:
                    rows.append(row)
        return rows

    def create_sorted_groups(self):
        self.sorted_by_pnl1 = sort_array_by_key(self.rows, self.sort_by['pnl1'])
        self.sorted_by_pnl2 = sort_array_by_key(self.rows, self.sort_by['pnl2'])
        self.sorted_by_wr1 = sort_array_by_key(self.rows, self.sort_by['wr1'])
        self.sorted_by_wr2 = sort_array_by_key(self.rows, self.sort_by['wr2'])

    def sortdnas(self):
        # read log file to log_body variable
        self.read_log()

        # Extract useful information from log file, return as 2d array
        self.rows = self.pick_lines()

        # Get values from last iteration as extra
        self.fit_rows = self.pick_lines(30)

        print(f'Total {len(self.rows)} unique dnas found.')

        self.create_sorted_groups()

        top_pnl1 = self.sorted_by_pnl1[0:self.len2]
        top_pnl2 = self.sorted_by_pnl2[0:self.len2]

        topten_pnl1 = self.sorted_by_pnl1[0:self.len1]
        topten_pnl2 = self.sorted_by_pnl2[0:self.len1]

        top_wr1 = self.sorted_by_wr1[0:self.len2]
        top_wr2 = self.sorted_by_wr2[0:self.len2]

        topten_wr1 = self.sorted_by_pnl1[0:self.len1]
        topten_wr2 = self.sorted_by_pnl2[0:self.len1]

        # print('PNL1', toppnl1)
        # print('PNL2', toppnl2)
        # print('Winrate1', topwr1)
        # print('Winrate2', topwr2)

        self.besties = self.fit_rows

        """for __dna in topwr1:
            if __dna not in besties and __dna in topwr2:
                # print('pnl1 not in besties:', __dna)
                besties.append(__dna)"""
        for dna in topten_wr1:
            if dna not in self.besties:
                # print('pnl1 not in besties:', __dna)
                self.besties.append(dna)

        for dna in topten_wr2:
            if dna not in self.besties:
                # print('pnl1 not in besties:', __dna)
                self.besties.append(dna)

        for dna in topten_pnl1:
            if dna not in self.besties:
                # print('pnl1 not in besties:', __dna)
                self.besties.append(dna)

        for dna in topten_pnl2:
            if dna not in self.besties:
                # print('pnl2 not in besties:', __dna)
                self.besties.append(dna)

        for dna in top_pnl1:
            # print(sortedbypnl2[i])
            if dna not in self.besties:  # and __dna in toppnl2:  # and __dna in topwr1:  # and sortedbypnl2[i] in topwr1 and sortedbypnl2[i] in topwr2:
                self.besties.append(dna)
                # print(__dna)

        for dna in top_pnl2:
            # print(sortedbypnl2[i])
            if dna not in self.besties:  # __dna in toppnl2 and :  # and __dna in topwr1:  # and sortedbypnl2[i] in topwr1 and sortedbypnl2[i] in topwr2:
                self.besties.append(dna)
                # print(__dna)

        # sortkey = 3
        # pnl1, pnl2, wr1, wr2 = 3, 6, 1, 4
        # if criteria == 'pnl1':
        #     sortkey = 3
        # elif criteria == 'pnl2':
        #     sortkey = 6
        # elif criteria == 'wr1':
        #     sortkey = 1
        # elif criteria == 'wr2':
        #     sortkey = 4

        # print(f'*{criteria}* *{sortkey}*')
        self.besties = sort_array_by_key(self.besties, self.sort_by[self.criteria])
        # sorted(besties, key=lambda x: int(x[sort_criterias_dict[criteria]]), reverse=True)

        print(f'Picked dnas count: {len(self.besties)}')

        # return self.besties

    def create_output_file(self):
        # Create dna output file and write header
        print('self.dna_fn', self.dna_fn)
        if os.path.exists(self.dna_fn):
            os.remove(self.dna_fn)

        with open(self.dna_fn, 'w') as f:
            f.write('dnas = [\n')

            for dd in self.besties:
                hps = self.decode_dna(dd[0])
                # print('encoded:', hyperparameters)
                dd.append(hps)
                f.write(str(dd).replace("""\n['""", """\n[r'""") + ',\n')

            f.write(']\n')
            f.flush()
            os.fsync(f.fileno())

    def decode_dna(self, dna_str: str):
        hps = jh.dna_to_hp(self.strategy_class.hyperparameters(None), dna_str)
        if not hps:
            print(
                'Could not decode dnas! Please check strategy name in routes.py file.\n'
                'Check strategy file for hyperparameters definition! Bye.')
            exit()  # TODO: or return dummy values and keep running.
        return hps

    def validate_output_file(self):
        p = f'{self.jessetkdir}.dnafiles.{self.strategy}dnas'
        print('p:', p)
        dnas = importlib.import_module(p)

        if len(dnas.dnas) == len(self.besties):
            print(f'Validated dna. {len(dnas.dnas)}/{len(self.besties)}')
        else:
            print(f'Creating dna file failed!, {len(dnas.dnas)}/{len(self.besties)}')
