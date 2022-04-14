import sys, json
from jesse.strategies import Strategy as Vanilla, cached

class Strategy(Vanilla):
    """
    The proxy strategy class which adds extra methods to Jesse base strategy.
    """
    def __init__(self):
        super().__init__()
        self.trade_ts = None
        self.first_run = True
        self.got_optional_hps = False
        self.optional_hps = {}
        
        print('sys.argv', sys.argv)

        for arg in sys.argv:
            if '!DNA!:' in arg:
                print('found dna parameters: ', arg)
                self.got_optional_hps = True
                self.optional_hps = json.loads(arg.replace('!DNA!:', ''))

    def before(self) -> None:
        if self.first_run: self.run_once()

    def run_once(self):
        print('\nHPs: ', self.hp)
        
        if self.optional_hps:
            print('self.optional_hps', self.optional_hps, type(self.optional_hps))

            if self.hp is None and len(self.hyperparameters()) > 0:
                try:
                    self.hp = self.optional_hps
                except:
                    print('Check optional parameters you passed!')

        self.first_run = False
    