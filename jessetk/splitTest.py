output = """
Start date: s, Finish date: s
Args: jesse-tk backtest 2021-03-11 2021-04-30 
 loading candles...
Recycling enabled!
Found a parent! 2019-12-13-2021-10-31-Binance Futures-ETH-USDT
Slice Start: 653760 Finish: 725759 | Calculated Slice len: 71999 | Slice len: 50.0 days | Orphan startdate: 1615420800000 Parent startdate: 1576195200000
Len parent_pickles 990720
 CANDLES              |
----------------------+--------------------------
 period               |    50 days (1.67 months)
 starting-ending date | 2021-03-11 => 2021-04-30


 exchange        | symbol   | timeframe   | strategy       | DNA
-----------------+----------+-------------+----------------+-------
 Binance Futures | ETH-USDT | 5m          | Ott2butKAMARe2 |


sys.argv ['C:\\Python38\\Scripts\\jesse-tk', 'backtest', '2021-03-11', '2021-04-30']
Executing simulation...

HPs:  {'ott_percent': 1940, 'stop_loss': 2190, 'risk_reward': 340, 'chop_bandwidth': 2790}
Executed backtest simulation in:  5.38 seconds


 METRICS                         |
---------------------------------+----------------------------------
 Total Closed Trades             |                               25
 Total Net Profit                |                 198.5409 (1.99%)
 Starting => Finishing Balance   |              10,000 => 10,198.54
 Total Open Trades               |                                0
 Open PL                         |                                0
 Total Paid Fees                 |                           101.88
 Max Drawdown                    |                            -4.9%
 Annual Return                   |                           15.11%
 Expectancy                      |                     7.94 (0.08%)
 Avg Win | Avg Loss              |                  293.88 | 126.62
 Ratio Avg Win / Avg Loss        |                             2.32
 Percent Profitable              |                              32%
 Longs | Shorts                  |                        44% | 56%
 Avg Holding Time                | 15 hours, 25 minutes, 36 seconds
 Winning Trades Avg Holding Time |             19 hours, 25 minutes
 Losing Trades Avg Holding Time  | 13 hours, 32 minutes, 56 seconds
 Serenity Index                  |                             0.23
 Sharpe Ratio                    |                              0.7
 Calmar Ratio                    |                             3.09
 Sortino Ratio                   |                             1.07
 Winning Streak                  |                                1
 Losing Streak                   |                                5
 Largest Winning Trade           |                           374.42
 Largest Losing Trade            |                          -288.71
 Total Winning Trades            |                                8
 Total Losing Trades             |                               17
 Market Change                   |                           53.56%

"""


def split_dates(line):
    return line.replace(' ', '').split('|')[-1].split('=>')  # Lazy man's reg^x

def split_estfd(line):
    return [x.strip() for x in line.split('|')]

lines = output.splitlines()

for index, line in enumerate(lines):

    if 'starting-ending date' in line:
            start_date, finish_date = split_dates(line)
            print(f'start_date={start_date}/finish_date={finish_date}/')
    
    if 'exchange' in line and 'symbol' in line and 'timeframe' in line:
        exchange, symbol, timeframe, strategy, dna = split_estfd(lines[index+2])
        print(f'{exchange},{symbol},{timeframe},{strategy},{dna},')


# metric['dna'] = random_walk.dna
# metric['exchange'] = random_walk.exchange
# metric['symbol'] = random_walk.symbol
# metric['tf'] = random_walk.timeframe
