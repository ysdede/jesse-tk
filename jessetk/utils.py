import os
from subprocess import PIPE, Popen
from jessetk.Vars import random_console_formatter, random_console_header1, random_console_header2
import jessetk.Vars
import base64

def encode_base64(s):
    s_bytes = s.encode('ascii')
    base64_bytes = base64.urlsafe_b64encode(s_bytes)
    return base64_bytes.decode('ascii')

def decode_base64(b):
    base64_bytes = b.encode('ascii')
    message_bytes = base64.urlsafe_b64decode(base64_bytes)
    return message_bytes.decode('ascii')

def encode_base32(s):
    s_bytes = s.encode('ascii')
    base32_bytes = base64.b32encode(s_bytes) #urlsafe_b64encode(s_bytes)
    return base32_bytes.decode('ascii')

def decode_base32(b):
    base32_bytes = b.encode('ascii')
    try:
        message_bytes = base64.b32decode(base32_bytes) #urlsafe_b64decode(base64_bytes)
    except:
        print('bbbbbbbbbbbbbbbbb:', b)
        exit()
    return message_bytes.decode('ascii')

def clear_console(): return os.system(
    'cls' if os.name in ('nt', 'dos') else 'clear')


def run_test(start_date, finish_date):
    process = Popen(['jesse', 'backtest', start_date,
                    finish_date], stdout=PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()
    return output.decode('utf-8')


def make_routes(template, anchor, dna_code):
    if anchor not in template:
        os.system('color')
        print('\nReplace the dna strings in routes.py with anchors. eg:\n')
        print(
            f"""(\033[32m'Bitfinex', 'BTC-USD', '2h', 'myStra', '{anchor}'\033[0m),\n""")
        exit()

    write_file('routes.py', template.replace(
        "'" + anchor + "'", repr(dna_code)))


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
    return int(longs), int(shorts)


def split_dates(line):
    return line.replace(' ', '').split('|')[-1].split('=>')  # Lazy man's reg^x


def split_estfd(line):                          # Split Exchange, Symbol, Timeframe, Strategy,
    # DNA while keeping spaces in exchange name
    return [x.strip() for x in line.split('|')]


def print_tops_formatted(frmt, header1, header2, tr):
    print('\x1b[6;34;40m')
    print(
        frmt.format(*header1))
    print(
        frmt.format(*header2))
    print('\x1b[0m')

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


def print_random_header():
    print(
        random_console_formatter.format(*random_console_header1))
    print(
        random_console_formatter.format(*random_console_header2))

def print_random_tops(sr, top_n):
    for r in sr[0:top_n]:
        print(
            random_console_formatter.format(
                r['start_date'],
                r['finish_date'],
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


def print_tops_generic(frmt, header1, header2, tr):
    print(
        frmt.format(*header1))
    print(
        frmt.format(*header2))

    for r in tr:
        print(frmt.format(*tr))


def create_csv_report(sorted_results, filename, header):
    from jessetk.Vars import csvd
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(str(header).replace('[', '').replace(']', '').replace("'", "").replace(',',
                                                                                       csvd) + '\n')

        for srl in sorted_results:
            f.write(f"{srl['symbol']}{csvd}{srl['tf']}{csvd}" + repr(srl['dna']) +
                    f"{csvd}{srl['start_date']}{csvd}"
                    f"{srl['finish_date']}{csvd}"
                    f"{srl['total_trades']}{csvd}"
                    f"{srl['n_of_longs']}{csvd}"
                    f"{srl['n_of_shorts']}{csvd}"
                    f"{srl['total_profit']}{csvd}"
                    f"{srl['max_dd']}{csvd}"
                    f"{srl['annual_return']}{csvd}"
                    f"{srl['win_rate']}{csvd}"
                    f"{srl['serenity']}{csvd}"
                    f"{srl['sharpe']}{csvd}"
                    f"{srl['calmar']}{csvd}"
                    f"{srl['win_strk']}{csvd}"
                    f"{srl['lose_strk']}{csvd}"
                    f"{srl['largest_win']}{csvd}"
                    f"{srl['largest_lose']}{csvd}"
                    f"{srl['n_of_wins']}{csvd}"
                    f"{srl['n_of_loses']}{csvd}"
                    f"{srl['paid_fees']}{csvd}"
                    f"{srl['market_change']}\n")


def get_metrics3(console_output) -> dict:
    metrics = jessetk.Vars.Metrics
    lines = console_output.splitlines()

    for index, line in enumerate(lines):
        if 'Aborted!' in line:
            print(console_output)
            print(
                "Aborted! error. Possibly pickle database is corrupt. Delete temp/ folder to fix.")
            exit(1)

        if 'CandleNotFoundInDatabase' in line:
            print(console_output)
            return metrics

        if 'Uncaught Exception' in line:
            print(console_output)
            if 'must be within the range' in line:
                print('Check DNA String in routes file!')
            exit(1)

        if 'No trades were made' in line:
            return metrics

        if 'starting-ending date' in line:
            metrics['start_date'], metrics['finish_date'] = split_dates(line)

        if 'exchange' in line and 'symbol' in line and 'timeframe' in line:
            metrics['exchange'], metrics['symbol'], metrics['tf'], metrics['strategy'], metrics['dna'] = split_estfd(
                lines[index+2])

        if 'Total Closed Trades' in line:
            metrics['total_trades'] = int(split(line))

        if 'Total Net Profit' in line:
            metrics['total_profit'] = round(float(split(line)), 2)

        if 'Max Drawdown' in line:
            metrics['max_dd'] = round(float(split(line)), 2)

        if 'Total Paid Fees' in line:
            metrics['paid_fees'] = round(float(split(line)), 2)

        if 'Annual Return' in line:
            metrics['annual_return'] = round(float(split(line)), 2)

        if 'Percent Profitable' in line:
            metrics['win_rate'] = int(split(line))

        if 'Serenity Index' in line:
            metrics['serenity'] = round(float(split(line)), 2)

        if 'Sharpe Ratio' in line:
            metrics['sharpe'] = round(float(split(line)), 2)

        if 'Calmar Ratio' in line:
            metrics['calmar'] = round(float(split(line)), 2)

        if 'Winning Streak' in line:
            metrics['win_strk'] = int(split(line))

        if 'Losing Streak' in line:
            metrics['lose_strk'] = int(split(line))

        if 'Longs | Shorts' in line:
            metrics['n_of_longs'], metrics['n_of_shorts'] = split_n_of_longs_shorts(line)

        if 'Largest Winning Trade' in line:
            metrics['largest_win'] = round(float(split(line)), 2)

        if 'Largest Losing Trade' in line:
            metrics['largest_lose'] = round(float(split(line)), 2)

        if 'Total Winning Trades' in line:
            metrics['n_of_wins'] = int(split(line))

        if 'Total Losing Trades' in line:
            metrics['n_of_loses'] = int(split(line))

        if 'Market Change' in line:
            metrics['market_change'] = round(float(split(line)), 2)
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
