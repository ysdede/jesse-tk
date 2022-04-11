import click
import optuna
import statistics
import json
from jessetk.utils import hp_to_seq
import csv

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


class OptunaPick:
    def __init__(self, t1=0.001, t2=-50):
        self.t1 = t1
        self.t2 = t2
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

    def dump_best_parameters(self):
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

        # sorted(study.best_trials, key=lambda t: t.values)
        trials = study.trials
        results = []
        parameter_list = []  # to eliminate redundant trials with same parameters
        candidates = {}

        r = router.routes[0]
        StrategyClass = jh.get_strategy_class(r.strategy_name)
        r.strategy = StrategyClass()

        for trial in trials:
            total_profit = max_mr = None
            if trial.state != optuna.trial.TrialState.COMPLETE:
                continue

            # Check each trial values
            # if any(v < 0 for v in trial.values):  # 1
            #     continue

            if (not trial.user_attrs['trades1']) or trial.user_attrs['trades1'] < 5:
                continue

            # Make this part customizable for each strategy
            # It's hardcoded for Gambler's Conceit for now.

            # Total profit
            if trial.values[0] < self.t1:
                continue

            # Max DD
            if trial.values[1] > self.t2:
                continue

            total_profit = trial.values[0]
            max_mr = trial.values[1]

            try:
                serenity = trial.user_attrs['serenity1']
            except KeyError:
                continue

            if serenity < 3:
                continue

            # Statistics test are useful for some strategies!
            # mean_value = round(statistics.mean((*trial.values, trial.user_attrs['sharpe3'])), 3)
            # std_dev = round(statistics.stdev((*trial.values, trial.user_attrs['sharpe3'])), 5)

            # {key : round(trial.params[key], 5) for key in trial.params}
            rounded_params = trial.params

            # Inject payload HP to route
            hp_new = {}

            # Sort hyperparameters as defined in the strategy
            for p in r.strategy.hyperparameters():
                hp_new[p['name']] = rounded_params[p['name']]

            rounded_params = hp_new

            # Remove duplicates
            # and mean_value > score_treshold and std_dev < std_dev_treshold:
            if trial.params not in parameter_list:
                hash = hp_to_seq(rounded_params)
                # candidates.append([hash, hp])
                candidates[hash] = rounded_params
                # print(type(trial.values), trial.values)

                # This is also hardcoded for Gambler's Conceit for now.
                result_line = [
                    trial.number, f"'{hash}'",
                    *trial.values,
                    trial.user_attrs['serenity1'],
                    total_profit if max_mr == 0 else round(
                        total_profit / abs(max_mr)),
                    trial.user_attrs['sharpe1'],
                    trial.user_attrs['trades1'],
                    trial.user_attrs['fees1'],
                    rounded_params]

                results.append(result_line)
                parameter_list.append(trial.params)

                # If parameters meet criteria, add to candidates
                # if mean_value > score_treshold and std_dev < std_dev_treshold and  trial.user_attrs['sharpe3'] > 2:

        results = sorted(results, key=lambda x: x[2], reverse=True)
        print(f"Picked {len(results)} trials")

        # field names
        fields = ['Trial #', 'Seq', 'Profit',
                  'Max DD', 'Serenity', 'Score', 'Sharpe', 'Trades', 'Fees', 'HP']

        with open(f'Results-{self.db_name}-{study_name.replace(" ", "-")}.csv', 'w') as f:
            # using csv.writer method from CSV package
            write = csv.writer(f, delimiter='\t', lineterminator='\n')

            write.writerow(fields)
            write.writerows(results)

        with open(f'SEQ-{self.db_name}-{study_name.replace(" ", "-")}.py', 'w') as f:
            f.write("hps = ")
            f.write(json.dumps(candidates, indent=1))

        print("Tada! Results saved to file.")
