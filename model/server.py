from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter
from mesa.visualization.modules import TextElement

from .exogeneous_factors import SimulationType
from .model import BankingModel


class InfoTextElement(TextElement):
    def render(self, model):
        n = len(model.schedule.banks)
        return 'Total of Banks: {}'.format(n)


model_params = {
    'simulation_type': UserSettableParameter('choice', 'Simulation Type', value='HighSpread',
                                             choices=[_.name for _ in SimulationType]),

    'exogenous_factors': {'minimumCapitalAdequacyRatio': 0}
}

server = ModularServer(BankingModel, [InfoTextElement()], "Banking Model", model_params)
server.port = 8521
