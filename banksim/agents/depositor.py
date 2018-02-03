import numpy as np
from mesa import Agent

from banksim.strategies.depositor_ewa_strategy import DepositorEWAStrategy
from banksim.util import Util
from ..exogeneous_factors import ExogenousFactors


class Depositor(Agent):

    def __init__(self, is_intelligent, ewa_damping_factor, bank, model):
        super().__init__(Util.get_unique_id(), model)

        # Bank Reference
        self.bank = bank

        self.amountEarlyWithdraw = 0
        self.amountFinalWithdraw = 0
        self.safetyTreshold = 0

        self.initialDeposit = Deposit()
        self.deposit = self.initialDeposit

        self.isIntelligent = is_intelligent
        if self.isIntelligent:
            self.strategiesOptionsInformation = DepositorEWAStrategy.depositor_ewa_strategy_list()
            self.currentlyChosenStrategy = None
            self.EWADampingFactor = ewa_damping_factor

    def update_strategy_choice_probability(self):
        list_a = np.array([s.A + s.strategyProfit for s in self.strategiesOptionsInformation])
        _exp = np.exp(list_a)
        list_p = _exp / np.sum(_exp)
        list_f = np.cumsum(list_p)
        for i, strategy in enumerate(self.strategiesOptionsInformation):
            strategy.A, strategy.P, strategy.F = list_a[i], list_p[i], list_f[i]

    def pick_new_strategy(self):
        probability_threshold = Util.get_random_uniform(1)
        self.currentlyChosenStrategy = [s for s in self.strategiesOptionsInformation if s.F > probability_threshold][0]

    def make_deposit(self, amount):
        self.initialDeposit.amount = amount
        self.deposit = Deposit(amount, self.initialDeposit.lastPercentageWithdrawn)

    def withdraw_deposit(self, simulation=False):
        if self.isIntelligent:
            # Smart depositor
            bank_car = self.bank.get_capital_adequacy_ratio()
            shock = 0 if bank_car > self.safetyTreshold else ExogenousFactors.amountWithdrawn
        else:
            if simulation:
                # if in simulation, uses last real withdrawal by this depositor
                shock = self.deposit.lastPercentageWithdrawn
            else:
                # Simulating a Diamond & Dribvig banksim...
                shock = ExogenousFactors.amountWithdrawn if Util.get_random_uniform(
                    1) < ExogenousFactors.probabilityofWithdrawal else 0
        self.deposit.lastPercentageWithdrawn = shock
        amount_depositor_wish_to_withdraw = self.deposit.amount * shock
        amount_withdrawn = self.bank.withdraw_deposit(amount_depositor_wish_to_withdraw)
        self.deposit.amount -= amount_withdrawn
        self.amountEarlyWithdraw = amount_withdrawn

    def calculate_final_utility(self):
        if self.isIntelligent:
            strategy = self.currentlyChosenStrategy
            self.amountFinalWithdraw = self.deposit.amount
            final_consumption = self.amountEarlyWithdraw + self.amountFinalWithdraw

            if final_consumption < self.initialDeposit.amount:
                if ExogenousFactors.isDepositInsuranceAvailable:
                    final_consumption = self.initialDeposit.amount * (1 + ExogenousFactors.depositInterestRate)
                else:
                    strategy.insolvencyCounter += 1

            amount = self.initialDeposit.amount
            profit = 100 * np.log(final_consumption / amount)
            strategy.finalConsumption = final_consumption
            strategy.strategyProfit = profit
            strategy.amountEarlyWithdraw = self.amountEarlyWithdraw
            strategy.amountFinalWithdraw = self.amountFinalWithdraw

    def reset(self):
        self.deposit = self.initialDeposit

    def period_0(self):
        if self.isIntelligent:
            self.update_strategy_choice_probability()
            self.pick_new_strategy()
            self.safetyTreshold = self.currentlyChosenStrategy.get_alpha_value()

    def period_1(self):
        #  Liquidity Shock
        if ExogenousFactors.areBankRunsPossible:
            self.withdraw_deposit()

    def period_2(self):
        pass


class Deposit:
    def __init__(self, amount=0, last_percentage_withdrawn=0):
        self.amount = amount
        self.lastPercentageWithdrawn = last_percentage_withdrawn
