from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter
from mesa.visualization.modules import TextElement

from banksim.exogeneous_factors import SimulationType
from banksim.model import BankingModel


class InfoTextElement(TextElement):
    def render(self, model):
        n = len(model.schedule.banks)
        return 'Total number of Banks: {}'.format(n)


model_params = {
    'simulation_type': UserSettableParameter('choice', 'Simulation Type', value='HighSpread',
                                             choices=[_.name for _ in SimulationType]),

    'exogenous_factors': {'minimumCapitalAdequacyRatio': 0},

    'number_of_banks': UserSettableParameter('slider', 'Number of banks', 10, 2, 20, 1)
}

server = ModularServer(BankingModel, [InfoTextElement()], "BankSim", model_params)
server.port = 8521
server.launch()
