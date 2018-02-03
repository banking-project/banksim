import numpy as np
from mesa import Agent

from banksim.util import Util
from ..exogeneous_factors import ExogenousFactors, InterbankPriority


class ClearingHouse(Agent):

    def __init__(self, number_banks, clearing_guarantee_available, model):
        super().__init__(Util.get_unique_id(), model)
        self.numberBanks = number_banks
        self.clearingGuaranteeAvailable = clearing_guarantee_available

        self.biggestInterbankDebt = 0
        self.totalInterbankDebt = 0
        self.totalCollateralDeficit = 0
        self.totalCollateralSurplus = 0

        self.interbankLendingMatrix = np.zeros((self.numberBanks, self.numberBanks))
        self.vetor_recuperacao = np.ones(self.numberBanks)
        # worst case scenario...
        self.banksNeedingLiquidity = list()
        self.banksOfferingLiquidity = list()

    def reset(self):
        self.interbankLendingMatrix[:, :] = 0
        self.reset_vetor_recuperacao()
        self.biggestInterbankDebt = 0
        self.totalInterbankDebt = 0
        self.totalCollateralDeficit = 0
        self.totalCollateralSurplus = 0
        self.banksNeedingLiquidity.clear()
        self.banksOfferingLiquidity.clear()

    def reset_vetor_recuperacao(self):
        self.vetor_recuperacao[:] = 1

    def organize_interbank_market_common(self, banks, simulation=False, m=0, simulated_strategy=None):
        for bank in self.model.schedule.banks:
            bank.interbankHelper.amountLiquidityLeftToBorrowOrLend = bank.liquidityNeeds
            if bank.needs_liquidity():
                self.banksNeedingLiquidity.append(bank)
            else:
                self.banksOfferingLiquidity.append(bank)

        if ExogenousFactors.interbankPriority == InterbankPriority.Random:
            np.random.shuffle(self.banksOfferingLiquidity)
            np.random.shuffle(self.banksNeedingLiquidity)
        elif ExogenousFactors.interbankPriority == InterbankPriority.RiskSorted:
            self.sort_queues_by_risk(simulation, m, simulated_strategy)

        for i, bank in enumerate(self.banksOfferingLiquidity):
            bank.interbankHelper.priorityOrder = i

        for i, bank in enumerate(self.banksNeedingLiquidity):
            bank.interbankHelper.priorityOrder = i

        iterator_lenders = iter(self.banksOfferingLiquidity)
        iterator_borrowers = iter(self.banksNeedingLiquidity)

        if len(self.banksOfferingLiquidity) > 0 and len(self.banksNeedingLiquidity) > 0:
            lender = next(iterator_lenders)
            borrower = next(iterator_borrowers)
            while True:
                try:
                    amount_offered = lender.interbankHelper.amountLiquidityLeftToBorrowOrLend
                    amount_requested = abs(borrower.interbankHelper.amountLiquidityLeftToBorrowOrLend)
                    amount_lent = min(amount_offered, amount_requested)
                    lender.interbankHelper.amountLiquidityLeftToBorrowOrLend -= amount_lent
                    borrower.interbankHelper.amountLiquidityLeftToBorrowOrLend += amount_lent

                    lender_id = (lender.unique_id - self.numberBanks) % self.numberBanks
                    borrower_id = (borrower.unique_id - self.numberBanks) % self.numberBanks

                    self.interbankLendingMatrix[lender_id, borrower_id] = amount_lent
                    self.interbankLendingMatrix[borrower_id, lender_id] = -amount_lent

                    if lender.interbankHelper.amountLiquidityLeftToBorrowOrLend == 0:
                        lender = next(iterator_lenders)
                    if borrower.interbankHelper.amountLiquidityLeftToBorrowOrLend == 0:
                        borrower = next(iterator_borrowers)
                except StopIteration:
                    break

        for bank in banks:
            bank.balanceSheet.interbankLoan = self.get_interbank_market_position(bank)

            if bank.offers_liquidity():
                # if there is any amount left offered, assign it to liquid assets
                bank.balanceSheet.liquidAssets = bank.interbankHelper.amountLiquidityLeftToBorrowOrLend
                bank.interbankHelper.amountLiquidityLeftToBorrowOrLend = 0

            if not bank.is_interbank_creditor():
                # if bank used interbank loan to pay depositors back, adjust deposit account
                bank.balanceSheet.deposits -= bank.balanceSheet.interbankLoan

            bank.liquidityNeeds = bank.interbankHelper.amountLiquidityLeftToBorrowOrLend

    def get_interbank_market_position(self, bank):
        bank_id_adjusted = (bank.unique_id - self.numberBanks) % self.numberBanks
        return np.sum(self.interbankLendingMatrix[bank_id_adjusted, :])

    def sort_queues_by_risk(self, simulation, bank_id_simulating, strategy_simulated):

        def bank_to_alpha_beta(_bank):
            strategy = _bank.interbankHelper.riskSorting
            return strategy.get_alpha_value(), strategy.get_beta_value()

        for bank in self.banksOfferingLiquidity:
            if simulation and bank.unique_id == bank_id_simulating:
                bank.interbankHelper.riskSorting = strategy_simulated
            else:
                bank.interbankHelper.riskSorting = bank.currentlyChosenStrategy

        for bank in self.banksNeedingLiquidity:
            if simulation and bank.unique_id == bank_id_simulating:
                bank.interbankHelper.riskSorting = strategy_simulated
            else:
                bank.interbankHelper.riskSorting = bank.currentlyChosenStrategy

        self.banksOfferingLiquidity.sort(key=bank_to_alpha_beta).reverse()
        self.banksNeedingLiquidity.sort(key=bank_to_alpha_beta).reverse()

    def interbank_clearing_guarantee(self, banks):
        self.calculate_total_and_biggest_interbank_debt(banks)
        self.organize_guarantees(banks)

    def calculate_total_and_biggest_interbank_debt(self, banks):
        for bank in banks:
            if bank.balanceSheet.interbankLoan < self.biggestInterbankDebt:
                self.biggestInterbankDebt = bank.balanceSheet.interbankLoan

            if bank.balanceSheet.interbankLoan < 0:
                self.totalInterbankDebt = self.totalInterbankDebt - bank.balanceSheet.interbankLoan

    def organize_guarantees(self, banks):
        for bank in banks:
            bank.reset_collateral()
            if not bank.is_interbank_creditor():
                g_helper = bank.guaranteeHelper
                ratio = bank.balanceSheet.interbankLoan / self.totalInterbankDebt
                g_helper.potentialCollateral = self.biggestInterbankDebt * ratio
                # both assets can be used as collateral
                g_helper.feasibleCollateral = min(
                    g_helper.potentialCollateral,
                    bank.balanceSheet.liquidAssets + bank.balanceSheet.nonFinancialSectorLoan)
                # minimize to avoid insolvent bank to use collateral
                g_helper.feasibleCollateral = min(
                    g_helper.feasibleCollateral,
                    max(0, -bank.balanceSheet.interbankLoan - min(0, bank.balanceSheet.capital)))

                # interbank debit balance impact
                g_helper.outstandingAmountImpact = max(
                    0,
                    min(
                        bank.balanceSheet.capital + g_helper.feasibleCollateral,
                        -bank.balanceSheet.interbankLoan))
                # residual collateral
                g_helper.residual = g_helper.feasibleCollateral - g_helper.outstandingAmountImpact

        for bank in banks:

            g_helper = bank.guaranteeHelper

            # total of collateral deficit or surplus
            if g_helper.residual < 0:
                self.totalCollateralDeficit += g_helper.residual
            else:
                self.totalCollateralSurplus += g_helper.residual

        for bank in banks:

            g_helper = bank.guaranteeHelper

            # residual collateral redistributed
            if g_helper.residual < 0:
                g_helper.redistributedCollateral = g_helper.residual
            else:
                f = min(1.0, -self.totalCollateralDeficit / self.totalCollateralSurplus)
                g_helper.redistributedCollateral = (1 - f) * g_helper.residual

            # final total collateral
            g_helper.collateralAdjustment = g_helper.outstandingAmountImpact + g_helper.redistributedCollateral
            collateral = g_helper.feasibleCollateral - g_helper.collateralAdjustment
            bank.balanceSheet.nonFinancialSectorLoan += - max(0, collateral - bank.balanceSheet.liquidAssets)
            bank.balanceSheet.liquidAssets += -min(bank.balanceSheet.liquidAssets, collateral)

    def interbank_contagion(self, banks, central_bank):
        self.reset_vetor_recuperacao()
        for bank in banks:

            bank_id = (bank.unique_id - self.numberBanks) % self.numberBanks

            if not bank.is_solvent() and bank.is_interbank_debtor():
                if self.clearingGuaranteeAvailable:
                    _max = max(0, -self.totalCollateralDeficit - self.totalCollateralSurplus)
                    self.vetor_recuperacao[bank_id] = (self.totalInterbankDebt + _max) / self.totalInterbankDebt
                else:
                    self.vetor_recuperacao[bank_id] = (bank.balanceSheet.interbankLoan + min(
                        -bank.balanceSheet.interbankLoan,
                        bank.balanceSheet.capital)) / bank.balanceSheet.interbankLoan

        for i in range(self.numberBanks):
            for j in range(i, self.numberBanks):
                self.interbankLendingMatrix[i, j] *= self.vetor_recuperacao[j]
                self.interbankLendingMatrix[j, i] = -self.interbankLendingMatrix[i, j]

        for bank in banks:
            bank_id = (bank.unique_id - self.numberBanks) % self.numberBanks
            bank.balanceSheet.interbankLoan = np.sum(self.interbankLendingMatrix[bank_id, :])
            if bank.is_insolvent():
                central_bank.punish_contagion_insolvency(bank)

    def accrue_interest(self, banks, interbank_rate):
        np.multiply(self.interbankLendingMatrix, (1 + interbank_rate), out=self.interbankLendingMatrix)
        for bank in banks:
            bank.balanceSheet.interbankLoan = self.get_interbank_market_position(bank)

    def period_0(self):
        self.reset()

    def period_1(self):
        if self.model.interbankLendingMarketAvailable:
            self.organize_interbank_market_common(self.model.schedule.banks)
            if self.clearingGuaranteeAvailable:
                self.interbank_clearing_guarantee(self.model.schedule.banks)

    def period_2(self):
        self.accrue_interest(self.model.schedule.banks, self.model.interbankInterestRate)
