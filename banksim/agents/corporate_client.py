from mesa import Agent

from banksim.util import Util


class CorporateClient(Agent):

    def __init__(self, default_rate, loss_given_default, loan_interest_rate, bank, model):
        super().__init__(Util.get_unique_id(), model)

        # Bank Reference
        self.bank = bank

        self.loanAmount = 0
        self.percentageRepaid = 0

        self.probabilityOfDefault = default_rate
        self.lossGivenDefault = loss_given_default
        self.loanInterestRate = loan_interest_rate

    def pay_loan_back(self, simulation=False):
        if simulation:
            # if under simulation, assume last percetageRepaid used
            amount_paid = self.percentageRepaid * self.loanAmount
        else:
            amount_paid = self.loanAmount * (1 - self.lossGivenDefault) \
                if Util.get_random_uniform(1) <= self.probabilityOfDefault \
                else self.loanAmount * (1 + self.loanInterestRate)
            self.percentageRepaid = 0 if self.loanAmount == 0 else amount_paid / self.loanAmount

        self.loanAmount = amount_paid
        return amount_paid

    def reset(self):
        self.loanAmount = 0
        self.percentageRepaid = 0

    def period_0(self):
        self.reset()

    def period_1(self):
        pass

    def period_2(self):
        pass
