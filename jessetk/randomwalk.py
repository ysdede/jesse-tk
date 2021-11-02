import random
from datetime import datetime
from datetime import timedelta
from jesse.routes import router
import jessetk.Vars as Vars
from jessetk.Vars import datadir


class RandomWalk:
    def __init__(self, start_date, finish_date, n_of_iters, width):
        self.jessetkdir = datadir
        self.start_date = start_date
        self.finish_date = finish_date
        self.width = width
        self.n_of_iters = n_of_iters
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
