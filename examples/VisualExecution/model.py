from mesa.datacollection import DataCollector

from banksim.model import BankingModel


class MyModel(BankingModel):
    """
    BankSim is a banking agent-based simulation framework developed in Python 3+.

    Its main goal is to provide an out-of-the-box simulation tool to study the impacts of a broad range of regulation policies over the banking system.

    The basic model is based on the paper by Barroso, R. V. et al., Interbank network and regulation policies: an analysis through agent-based simulations with adaptive learning, published in the Journal Of Network Theory In Finance, v. 2, n. 4, p. 53–86, 2016.

    The paper is available online at https://mpra.ub.uni-muenchen.de/73308.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # DataCollector
        self.datacollector = DataCollector(
            model_reporters={"Insolvencies": number_of_insolvencies,
                             "Contagions": number_of_contagions}
        )

    def step(self):
        super().step()
        # DataCollector
        self.datacollector.collect(self)


# Data Collector Functions
def number_of_insolvencies(model):
    return model.schedule.central_bank.insolvencyPerCycleCounter / model.numberBanks


def number_of_contagions(model):
    return model.schedule.central_bank.insolvencyDueToContagionPerCycleCounter / model.numberBanks
