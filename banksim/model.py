from mesa import Model

from .activation import MultiStepActivation
from .agents.bank import Bank
from .agents.central_bank import CentralBank
from .agents.clearing_house import ClearingHouse
from .agents.corporate_client import CorporateClient
from .agents.depositor import Depositor
from .exogeneous_factors import ExogenousFactors, SimulationType, InterbankPriority


class BankingModel(Model):

    def __init__(self, simulation_type='HighSpread', exogenous_factors=None, number_of_banks=None):
        super().__init__()

        # Simulation data
        self.simulation_type = SimulationType[simulation_type]
        BankingModel.update_exogeneous_factors_by_simulation_type(self.simulation_type)

        BankingModel.update_exogeneous_factors(exogenous_factors, number_of_banks)

        # Economy data
        self.numberBanks = ExogenousFactors.numberBanks
        self.depositInterestRate = ExogenousFactors.depositInterestRate
        self.interbankInterestRate = ExogenousFactors.interbankInterestRate
        self.liquidAssetsInterestRate = ExogenousFactors.liquidAssetsInterestRate
        self.interbankLendingMarketAvailable = ExogenousFactors.interbankLendingMarketAvailable

        # Scheduler
        self.schedule = MultiStepActivation(self)

        # Central Bank
        _params = (ExogenousFactors.centralBankLendingInterestRate,
                   ExogenousFactors.offersDiscountWindowLending,
                   ExogenousFactors.minimumCapitalAdequacyRatio,
                   not ExogenousFactors.isCentralBankZeroIntelligenceAgent,
                   ExogenousFactors.DefaultEWADampingFactor)
        self.schedule.add_central_bank(CentralBank(*_params, self))

        # Clearing House
        _params = (self.numberBanks,
                   ExogenousFactors.isClearingGuaranteeAvailable)
        self.schedule.add_clearing_house(ClearingHouse(*_params, self))

        # Banks
        _params = (ExogenousFactors.bankSizeDistribution,
                   not ExogenousFactors.areBanksZeroIntelligenceAgents,
                   ExogenousFactors.DefaultEWADampingFactor)
        for _ in range(self.numberBanks):
            bank = Bank(*_params, self)
            self.schedule.add_bank(bank)
        self.normalize_banks()

        _params_depositors = (
            not ExogenousFactors.areDepositorsZeroIntelligenceAgents,
            ExogenousFactors.DefaultEWADampingFactor)

        # Depositors and Corporate Clients (Firms)
        if ExogenousFactors.standardCorporateClients:
            _params_corporate_clients = (ExogenousFactors.standardCorporateClientDefaultRate,
                                         ExogenousFactors.standardCorporateClientLossGivenDefault,
                                         ExogenousFactors.standardCorporateClientLoanInterestRate)
        else:
            _params_corporate_clients = (ExogenousFactors.wholesaleCorporateClientDefaultRate,
                                         ExogenousFactors.wholesaleCorporateClientLossGivenDefault,
                                         ExogenousFactors.wholesaleCorporateClientLoanInterestRate)

        for bank in self.schedule.banks:
            for i in range(ExogenousFactors.numberDepositorsPerBank):
                depositor = Depositor(*_params_depositors, bank, self)
                bank.depositors.append(depositor)
                self.schedule.add_depositor(depositor)
            for i in range(ExogenousFactors.numberCorporateClientsPerBank):
                corporate_client = CorporateClient(*_params_corporate_clients, bank, self)
                bank.corporateClients.append(corporate_client)
                self.schedule.add_corporate_client(corporate_client)

    def step(self):
        self.schedule.period_0()
        self.schedule.period_1()
        self.schedule.period_2()

    def run_model(self, n):
        for i in range(n):
            self.step()
        self.running = False

    def normalize_banks(self):
        # Normalize banks size and Compute market share (in % of total assets)
        total_size = sum([_.initialSize for _ in self.schedule.banks])
        factor = self.numberBanks / total_size
        for bank in self.schedule.banks:
            bank.marketShare = bank.initialSize / total_size
            bank.initialSize *= factor

    @staticmethod
    def update_exogeneous_factors(exogenous_factors, number_of_banks):
        if isinstance(exogenous_factors, dict):
            for key, value in exogenous_factors.items():
                setattr(ExogenousFactors, key, value)

        if number_of_banks:
            ExogenousFactors.numberBanks = number_of_banks

    @staticmethod
    def update_exogeneous_factors_by_simulation_type(simulation_type):
        if simulation_type == SimulationType.HighSpread:
            pass
        if simulation_type == SimulationType.LowSpread:
            ExogenousFactors.standardCorporateClientLoanInterestRate = 0.06
        elif simulation_type == SimulationType.ClearingHouse:
            ExogenousFactors.isClearingGuaranteeAvailable = True
        elif simulation_type == SimulationType.ClearingHouseLowSpread:
            ExogenousFactors.isClearingGuaranteeAvailable = True
            ExogenousFactors.standardCorporateClientLoanInterestRate = 0.06
        elif simulation_type == SimulationType.Basel:
            ExogenousFactors.standardCorporateClients = False
            ExogenousFactors.isCentralBankZeroIntelligenceAgent = False
            ExogenousFactors.isCapitalRequirementActive = True
            ExogenousFactors.interbankPriority = InterbankPriority.RiskSorted
            ExogenousFactors.standardCorporateClientDefaultRate = 0.05
        elif simulation_type == SimulationType.BaselBenchmark:
            ExogenousFactors.standardCorporateClients = False
            ExogenousFactors.standardCorporateClientDefaultRate = 0.05
        elif simulation_type == SimulationType.DepositInsurance:
            ExogenousFactors.areDepositorsZeroIntelligenceAgents = False
            ExogenousFactors.isDepositInsuranceAvailable = True
        elif simulation_type == SimulationType.DepositInsuranceBenchmark:
            ExogenousFactors.areDepositorsZeroIntelligenceAgents = False
