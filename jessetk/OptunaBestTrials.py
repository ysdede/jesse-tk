import click
import optuna
from jessetk.utils import hp_to_seq

try:
    from jesse.config import config
except:
    print('Check your config.py file or project folder structure. You need legacy jesse cli!')
    exit()

try:
    from jesse.routes import router
    import jesse.helpers as jh
except:
    print('Check your project folder structure. You need legacy jesse cli!')
    exit()


class OptunaBestTrials:
    def __init__(self):
        try:
            self.db_host = config['env']['databases']['optuna_db_host']
            self.db_port = config['env']['databases']['optuna_db_port']
            self.db_name = config['env']['databases']['optuna_db']
            self.db_user = config['env']['databases']['optuna_user']
            self.db_password = config['env']['databases']['optuna_password']
        except:
            print(
                'Check your config.py file for optuna database settings! example configuration:')
            print("""
                'databases': {
                'postgres_host': '192.168.1.27',
                'postgres_name': 'jesse_db',
                'postgres_port': 5432,
                'postgres_username': 'jesse_user',
                'postgres_password': 'password@€',
                
                'optuna_db_host': '192.168.1.27',
                'optuna_db_port': 5432,
                'optuna_db': 'optuna_db',
                'optuna_user': 'optuna_user',
                'optuna_password': 'password€',
                },
            """)
            exit()

        self.storage = f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}/{self.db_name}"

    def pick_best_parameters(self):
        study_summaries = optuna.study.get_all_study_summaries(storage=self.storage)
        # Sort study_summaries by datetime_start
        studies_sorted = sorted(study_summaries, key=lambda x: x._study_id)

        print(f"{'-'*10} {'-'*8} {'-'*26} {'-'*64}")
        print(f"{'Study ID':<10} {'Trials':<8} {'Datetime':<26} {'Study Name':<64}")
        print(f"{'-'*10} {'-'*8} {'-'*26} {'-'*64}")

        studies_dict = {}

        for ss in studies_sorted:
            studies_dict[ss._study_id] = ss.study_name
            print(
                f"{ss._study_id:<10} {ss.n_trials:<8} {str(ss.datetime_start):<26} {ss.study_name:<64}")

        value = click.prompt('Pick a study', type=int)

        try:
            study_name = studies_dict[value]
            study = optuna.load_study(study_name=study_name, storage=self.storage)
        except:
            print('Study not found!')
            exit()

        print(value, study_name)
        print("Number of finished trials: ", len(study.trials))

        r = router.routes[0]
        StrategyClass = jh.get_strategy_class(r.strategy_name)
        r.strategy = StrategyClass()

        bt_list = []
        hp_list = []
        best_trials = sorted(study.best_trials, key=lambda t: t.values)

        for bt in best_trials:
            # Sort hyperparameters as defined in the strategy
            hp_new = {}
            for p in r.strategy.hyperparameters():
                try:
                    hp_new[p['name']] = bt.params[p['name']]
                except:
                    pass

            if hp_new not in hp_list:
                print(f"Trial #{bt.number} Values: { bt.values} {hp_new}")
                bt_list.append(bt)
                hp_list.append(hp_new)

        return bt_list, hp_list
        