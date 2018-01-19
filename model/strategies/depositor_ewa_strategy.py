import numpy as np


class DepositorEWAStrategy:
    numberAlphaOptions = 10

    def __init__(self, alpha_index_option=0):
        self.alphaIndex = alpha_index_option
        self.strategyProfit = self.amountEarlyWithdraw = self.amountFinalWithdraw = 0
        self.insolvencyCounter = self.finalConsumption = 0
        self.A = self.P = self.F = 0

    def get_alpha_value(self):
        return (self.alphaIndex + 1) / 100

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.alphaIndex == other.alphaIndex
        return False

    def reset(self):
        self.strategyProfit = self.amountEarlyWithdraw = self.amountFinalWithdraw = 0
        self.insolvencyCounter = self.finalConsumption = 0
        self.A = self.P = self.F = 0

    @classmethod
    def depositor_ewa_strategy_list(cls):
        return np.array([DepositorEWAStrategy(a) for a in range(cls.numberAlphaOptions)], dtype=DepositorEWAStrategy)
