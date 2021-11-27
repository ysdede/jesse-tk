import optuna
from timeit import default_timer as timer
from jessetk.utils import hp_to_dna
from jesse.routes import router
import jesse.helpers as jh

class Optimize:
    def __init__(self, start_date: str, finish_Date: str, worker_count: int = 4) -> None:
        """Run objective function with Optuna Test 1

        Args:
            start (str): Start date
            end (str): End date
            worker_count (int, optional): Number of download jobs to run paralel. Defaults to 4.
        """

        self.timer_start = timer()
        self.start_date = start_date
        self.finish_date = finish_Date
        self.worker_count = worker_count
        self.strategy_hp = None
        

    def objective(trial):
        # x = trial.suggest_float("x", -100, 100)

        ott_len = trial.suggest_int('ott_len', 2, 50)
        ott_percent = trial.suggest_int('ott_percent', 50, 800)
        stop_loss = trial.suggest_int('stop_loss', 50, 400)
        risk_reward = trial.suggest_int('risk_reward', 10, 80)
        chop_rsi_len = trial.suggest_int('chop_rsi_len', 5, 50)
        chop_bandwidth = trial.suggest_int('chop_bandwidth', 10, 300)

        
        parameters = {'ott_len': ott_len, 'ott_percent': ott_percent, 'stop_loss': stop_loss,
                      'risk_reward': risk_reward, 'chop_rsi_len': chop_rsi_len, 'chop_bandwidth': chop_bandwidth}

        return 1

    def run(self):
        print(f"Start: {self.start_date}")
        print(f"Finish: {self.finish_date}")
        print(f"Worker count: {self.worker_count}")
        
        strategy_name = router.routes[0].strategy_name
        StrategyClass = jh.get_strategy_class(strategy_name)
        strategy_hp = StrategyClass.hyperparameters(None)
        self.strategy_hp = strategy_hp
        test_dna =  ['=)-r8j', 37, 353, 205.24, 36, 58, 22.39, {'ott_len': 15, 'ott_percent': 59, 'stop_loss': 72, 'risk_reward': 76, 'chop_rsi_len': 14, 'chop_bandwidth': 252}]
        
        test_parameters = test_dna[7]

        encoded_dna = hp_to_dna(strategy_hp, test_parameters)
        print(encoded_dna, encoded_dna == test_dna[0])

        # hps = [
        #     {'name': 'ott_len', 'type': int, 'min': 2, 'max': 50, 'default': 12},
        #     {'name': 'ott_percent', 'type': int, 'min': 50, 'max': 800, 'default': 153},
        #     {'name': 'stop_loss', 'type': int, 'min': 50, 'max': 400, 'default': 125},
        #     {'name': 'risk_reward', 'type': int, 'min': 10, 'max': 80, 'default': 37},
        #     {'name': 'chop_rsi_len', 'type': int, 'min': 5, 'max': 50, 'default': 36},
        #     {'name': 'chop_bandwidth', 'type': int, 'min': 10, 'max': 300, 'default': 72},
        # ]

        # trial_hps = {}
        # for hp in hps:
        #     print(hp)
        #     trial_hps[hp['name']] = hp['default']
        #     trial_hps[hp['name']] = hp['default']

        # print(trial_hps)

        #     # print('ott_len', hp['name'], hp['min'], hp['max'])
        #     # print('otp_percent', hp['name'], hp['min'], hp['max'])
        #     # print('stop_loss', hp['name'], hp['min'], hp['max'])
        #     # print('risk_reward', hp['name'], hp['min'], hp['max'])
        #     # print('chop_rsi_len', hp['name'], hp['min'], hp['max'])
        #     # print('chop_bandwidth', hp['name'], hp['min'], hp['max'])
