import itertools


class MultiStepActivation:

    def __init__(self, model):
        self.model = model
        self.cycle = 0
        self.period = 0

        # Agents
        self.central_bank = None
        self.clearing_house = None
        self.banks = []
        self.depositors = []
        self.corporate_clients = []

    def add_central_bank(self, central_bank):
        self.central_bank = central_bank

    def add_clearing_house(self, clearing_house):
        self.clearing_house = clearing_house

    def add_bank(self, bank):
        self.banks.append(bank)

    def add_depositor(self, depositor):
        self.depositors.append(depositor)

    def add_corporate_client(self, corporate_client):
        self.corporate_clients.append(corporate_client)

    @property
    def agents(self):
        # The order is important
        return itertools.chain(self.depositors, self.banks, [self.clearing_house], [self.central_bank],
                               self.corporate_clients)

    def reset_cycle(self):
        self.cycle += 1
        for _ in self.agents:
            _.reset()

    def period_0(self):
        self.period = 0
        for _ in self.agents:
            _.period_0()

    def period_1(self):
        self.period = 1
        for _ in self.agents:
            _.period_1()

    def period_2(self):
        self.period = 2
        for _ in self.agents:
            _.period_2()
