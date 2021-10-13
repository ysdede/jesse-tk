import os


def make_routes(template, anchor, dna_code):
    if anchor not in template:
        os.system('color')
        print('\nReplace the dna strings in routes.py with anchors. eg:\n')
        print(f"""(\033[32m'Bitfinex', 'BTC-USD', '2h', 'myStra', '{anchor}'\033[0m),\n""")
        exit()
    # print(dna_code, 'dna code')
    # template = template.replace("'" + anchor + "'", repr(dna_code))
    write_file('routes.py', template.replace("'" + anchor + "'", repr(dna_code)))


def split(line):
    ll = line.split(' ')
    r = ll[len(ll) - 1].replace('%', '')
    r = r.replace(')', '')
    r = r.replace('(', '')
    return r.replace(',', '')


def split_n_of_longs_shorts(line):
    ll = line.split(' ')
    shorts = ll[len(ll) - 1].replace('%', '')
    longs = ll[len(ll) - 3].replace('%', '')
    return longs, shorts


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


def get_metrics3(console_output) -> dict:
    import jessetk.Vars
    metrics = jessetk.Vars.Metrics
    lines = console_output.splitlines()

    for index, line in enumerate(lines):

        if 'Aborted!' in line:
            print(console_output)
            print("Aborted! error. Possibly pickle database is corrupt. Delete temp/ folder to fix.")
            exit(1)

        if 'CandleNotFoundInDatabase' in line:
            print(console_output)
            return metrics
            # exit(1)

        if 'Uncaught Exception' in line:
            print(console_output)
            exit(1)

        if 'No trades were made' in line:
            return metrics

        if 'Total Closed Trades' in line:
            metrics['total_trades'] = split(line)

        if 'Total Net Profit' in line:
            metrics['total_profit'] = split(line)

        if 'Max Drawdown' in line:
            metrics['max_dd'] = split(line)

        if 'Total Paid Fees' in line:
            metrics['paid_fees'] = split(line)

        if 'Annual Return' in line:
            metrics['annual_return'] = float(split(line))

        if 'Percent Profitable' in line:
            metrics['win_rate'] = split(line)

        if 'Serenity Index' in line:
            metrics['serenity'] = split(line)

        if 'Sharpe Ratio' in line:
            metrics['sharpe'] = split(line)

        if 'Calmar Ratio' in line:
            metrics['calmar'] = split(line)

        if 'Winning Streak' in line:
            metrics['win_strk'] = split(line)

        if 'Losing Streak' in line:
            metrics['lose_strk'] = split(line)

        if 'Longs | Shorts' in line:
            metrics['n_of_longs'], metrics['n_of_shorts'] = split_n_of_longs_shorts(line)

        if 'Largest Winning Trade' in line:
            metrics['largest_win'] = round(float(split(line)))

        if 'Largest Losing Trade' in line:
            metrics['largest_lose'] = round(float(split(line)))

        if 'Total Winning Trades' in line:
            metrics['n_of_wins'] = split(line)

        if 'Total Losing Trades' in line:
            metrics['n_of_loses'] = split(line)

        if 'Market Change' in line:
            metrics['market_change'] = split(line)
    return metrics


def write_file(fn, body):
    remove_file(fn)
    with open(fn, 'w', encoding='utf-8') as f:
        f.write(body)
        f.flush()
        os.fsync(f.fileno())


def read_file(fn):
    with open(fn, 'r', encoding='utf-8') as f:
        return f.read()


def remove_file(fn):
    if os.path.exists(fn):
        try:
            os.remove(fn)
        except:
            print(f'Failed to remove file {fn}')
            exit()
