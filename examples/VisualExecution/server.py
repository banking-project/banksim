from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter
from mesa.visualization.modules import ChartModule
from mesa.visualization.modules import TextElement

from banksim.exogeneous_factors import SimulationType
from examples.VisualExecution.model import MyModel


class InfoTextElement(TextElement):
    def render(self, model):
        n = len(model.schedule.banks)
        return 'Total number of Banks: {}'.format(n)


chart = ChartModule([
    {"Label": "Insolvencies", "Color": "Green"},
    {"Label": "Contagions", "Color": "Red"}],
    data_collector_name='datacollector'
)

model_params = {
    'simulation_type': UserSettableParameter('choice', 'Simulation Type', value='HighSpread',
                                             choices=[_.name for _ in SimulationType]),

    'exogenous_factors': {'minimumCapitalAdequacyRatio': 0},

    'number_of_banks': UserSettableParameter('slider', 'Number of banks', 10, 2, 100, 1)
}

server = ModularServer(MyModel, [chart, InfoTextElement()], "BankSim", model_params)
server.port = 8521

server.launch()
