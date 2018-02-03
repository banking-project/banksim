from enum import Enum


class SimulationType(Enum):
    HighSpread = 1
    LowSpread = 2
    ClearingHouse = 3
    ClearingHouseLowSpread = 4
    Basel = 5
    BaselBenchmark = 6
    DepositInsurance = 7
    DepositInsuranceBenchmark = 8


class BankSizeDistribution(Enum):
    Vanilla = 1
    LogNormal = 2


class InterbankPriority(Enum):
    Random = 1
    RiskSorted = 2


class ExogenousFactors:
    # Model
    numberBanks = 10
    depositInterestRate = 0.005
    interbankInterestRate = 0.01
    liquidAssetsInterestRate = 0
    illiquidAssetDiscountRate = 0.15
    interbankLendingMarketAvailable = True
    banksMaySellNonLiquidAssetsAtDiscountPrices = True
    banksHaveLimitedLiability = False

    # Banks
    bankSizeDistribution = BankSizeDistribution.Vanilla
    numberDepositorsPerBank = 100
    numberCorporateClientsPerBank = 50
    areBanksZeroIntelligenceAgents = False

    # Central Bank
    centralBankLendingInterestRate = 0.04
    offersDiscountWindowLending = True
    minimumCapitalAdequacyRatio = -10
    isCentralBankZeroIntelligenceAgent = True
    isCapitalRequirementActive = False
    isTooBigToFailPolicyActive = False
    isDepositInsuranceAvailable = False

    # Clearing House
    isClearingGuaranteeAvailable = False
    interbankPriority = InterbankPriority.Random

    # Depositors
    areDepositorsZeroIntelligenceAgents = True
    areBankRunsPossible = True
    amountWithdrawn = 1.0
    probabilityofWithdrawal = 0.15

    # Firms / Corporate Clients
    standardCorporateClients = True
    standardCorporateClientDefaultRate = 0.045
    standardCorporateClientLossGivenDefault = 1
    standardCorporateClientLoanInterestRate = 0.08
    wholesaleCorporateClientDefaultRate = 0.04
    wholesaleCorporateClientLoanInterestRate = 0.06
    wholesaleCorporateClientLossGivenDefault = 1
    retailCorporateClientDefaultRate = 0.06
    # retailCorporateClientLoanInterestRate = 0.08
    # retailCorporateClientLossGivenDefault = 0.75

    # Risk Weights
    CashRiskWeight = 0
    CorporateLoanRiskWeight = 1
    InterbankLoanRiskWeight = 1
    retailCorporateLoanRiskWeight = 0.75
    wholesaleCorporateLoanRiskWeight = 1

    # Learning
    DefaultEWADampingFactor = 1
