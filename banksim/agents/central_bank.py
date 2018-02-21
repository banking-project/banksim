import numpy as np
from mesa import Agent

from banksim.exogeneous_factors import ExogenousFactors
from banksim.strategies.central_bank_ewa_strategy import CentralBankEWAStrategy
from banksim.util import Util


class CentralBank(Agent):

    def __init__(self, central_bank_lending_interest_rate, offers_discount_window_lending,
                 minimum_capital_adequacy_ratio, is_intelligent, ewa_damping_factor, model):
        super().__init__(Util.get_unique_id(), model)

        self.centralBankLendingInterestRate = central_bank_lending_interest_rate
        self.offersDiscountWindowLending = offers_discount_window_lending
        self.minimumCapitalAdequacyRatio = minimum_capital_adequacy_ratio

        self.insolvencyPerCycleCounter = 0
        self.insolvencyDueToContagionPerCycleCounter = 0

        self.isIntelligent = is_intelligent
        if self.isIntelligent:
            self.strategiesOptionsInformation = CentralBankEWAStrategy.central_bank_ewa_strategy_list()
            self.currentlyChosenStrategy = None
            self.EWADampingFactor = ewa_damping_factor

    def update_strategy_choice_probability(self):
        list_a = np.array([0.9999 * s.A + s.strategyProfit for s in self.strategiesOptionsInformation])
        _exp = np.exp(list_a)
        list_p = _exp / np.sum(_exp)
        list_f = np.cumsum(list_p)
        for i, strategy in enumerate(self.strategiesOptionsInformation):
            strategy.A, strategy.P, strategy.F = list_a[i], list_p[i], list_f[i]

    def pick_new_strategy(self):
        probability_threshold = Util.get_random_uniform(1)
        self.currentlyChosenStrategy = [s for s in self.strategiesOptionsInformation if s.F > probability_threshold][0]

    def observe_banks_capital_adequacy(self, banks):
        for bank in banks:
            if bank.get_capital_adequacy_ratio() < self.minimumCapitalAdequacyRatio:
                bank.adjust_capital_ratio(self.minimumCapitalAdequacyRatio)

    def organize_discount_window_lending(self, banks):
        for bank in banks:
            if not bank.is_liquid():
                loan_amount = self.get_discount_window_lend(bank, bank.liquidityNeeds)
                bank.receive_discount_window_loan(loan_amount)

    def get_discount_window_lend(self, bank, amount_needed):
        # when should not bank be eligible for such loans?
        if self.offersDiscountWindowLending:
            if ExogenousFactors.isTooBigToFailPolicyActive:
                if CentralBank.is_bank_too_big_to_fail(bank):
                    return min(amount_needed, 0)
                else:
                    return 0  # better luck next time!
            else:
                # If Central Bank offers lending and TBTF is not active, assume all banks get help
                return min(amount_needed, 0)
        else:
            return 0

    @staticmethod
    def is_bank_too_big_to_fail(bank):
        if ExogenousFactors.isTooBigToFailPolicyActive:
            random_uniform = Util.get_random_uniform(1)
            return random_uniform < 2 * bank.marketShare
        return False

    @staticmethod
    def make_banks_sell_non_liquid_assets(banks):
        for bank in banks:
            if not bank.is_liquid():
                bank.use_non_liquid_assets_to_pay_depositors_back()

    @staticmethod
    def bailout(bank):
        if not bank.is_liquid():
            liquidity_needs = -bank.liquidityNeeds
            bank.balanceSheet.liquidAssets += liquidity_needs
            bank.liquidityNeeds = 0
        if bank.is_insolvent():
            capital_shortfall = bank.balanceSheet.capital
            bank.balanceSheet.liquidAssets += capital_shortfall

    @staticmethod
    def punish_illiquidity(bank):
        # is there anything else to do?
        bank.use_non_liquid_assets_to_pay_depositors_back()

    def punish_insolvency(self, bank):
        insolvency_penalty = 0.5
        bank.balanceSheet.nonFinancialSectorLoan *= 1 - insolvency_penalty
        self.insolvencyPerCycleCounter += 1

    def punish_contagion_insolvency(self, bank):
        self.insolvencyDueToContagionPerCycleCounter += 1
        self.punish_insolvency(bank)

    def calculate_final_utility(self, banks):
        if self.isIntelligent:
            strategy = self.currentlyChosenStrategy
            strategy.numberInsolvencies = self.insolvencyPerCycleCounter
            strategy.totalLoans = CentralBank.get_total_real_sector_loans(banks)
            potential_total_size = len(banks)
            ratio = strategy.totalLoans / potential_total_size
            strategy.strategyProfit = ratio - (potential_total_size * strategy.numberInsolvencies)

    @staticmethod
    def get_total_real_sector_loans(banks):
        return sum([bank.balanceSheet.nonFinancialSectorLoan for bank in banks])

    @staticmethod
    def liquidate_insolvent_banks(banks):
        for bank in banks:
            if bank.is_insolvent():
                bank.liquidate()

    @property
    def banks(self):
        return self.model.schedule.banks

    def reset(self):
        self.insolvencyPerCycleCounter = 0
        self.insolvencyDueToContagionPerCycleCounter = 0

    def period_0(self):
        if self.isIntelligent:
            self.update_strategy_choice_probability()
            self.pick_new_strategy()
            self.minimumCapitalAdequacyRatio = self.currentlyChosenStrategy.get_alpha_value()
        if ExogenousFactors.isCapitalRequirementActive:
            self.observe_banks_capital_adequacy(self.banks)

    def period_1(self):
        # ... if banks still needs liquidity, central bank might rescue...
        if self.offersDiscountWindowLending:
            self.organize_discount_window_lending(self.banks)
        # ... if everything so far isn't enough, banks will sell illiquid assets at discount prices.
        if ExogenousFactors.banksMaySellNonLiquidAssetsAtDiscountPrices:
            CentralBank.make_banks_sell_non_liquid_assets(self.banks)

    def period_2(self):
        for bank in self.banks:
            if CentralBank.is_bank_too_big_to_fail(bank):
                CentralBank.bailout(bank)
            if not bank.is_liquid():
                CentralBank.punish_illiquidity(bank)
            if not bank.is_solvent():
                self.punish_insolvency(bank)

        if self.model.interbankLendingMarketAvailable:
            self.model.schedule.clearing_house.interbank_contagion(self.banks, self)

        for bank in self.banks:
            bank.calculate_profit(self.minimumCapitalAdequacyRatio)

        self.calculate_final_utility(self.banks)
        CentralBank.liquidate_insolvent_banks(self.banks)

        for depositor in self.model.schedule.depositors:
            depositor.calculate_final_utility()
