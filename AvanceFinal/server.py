# shelves initialized  in 0 
# 3 types of packages id = 001, 002, 003
# start positions predefined for 5 robots
# the user sets a maximum simutlation time


import mesa
from mesa.visualization.modules import CanvasGrid, ChartModule
from model import WarehouseModel, LGVAgent, Shelf, Truck, Package, VisualTruck

def agent_portrayal(agent):
    if isinstance(agent, LGVAgent):
        portrayal = {"Shape": "circle", "Filled": "true", "Color": "Cyan", "Layer": 1, "r": 0.5,

        }
        if agent.carrying_package:
            portrayal["Color"] = "Yellow"  
    elif isinstance(agent, Shelf):
        portrayal = {"Shape": "rect", "Filled": "true", "Layer": 0, "w": 0.9, "h": 0.9, "text_color": "Black",
                     "Color": "#ccbeaf", "text": f"📦 {agent.current_load}"}
    elif isinstance(agent, Truck):
        portrayal = {"Shape": "rect", "Filled": "true", "Layer": 0, "w": 0.9, "h": 0.9, "text_color": "Black",
                     "Color": "white"}
    elif isinstance(agent, VisualTruck):
        portrayal = {"Shape": "rect", "Filled": "true", "Layer": 0, "w": 0.9, "h": 0.9, "text_color": "Black",
                     "Color": "#ccbeaf", "text": "🚚 IN" if agent.truck_type == "unload" else "🚚 OUT"}
    elif isinstance(agent, Package):
        portrayal = {"Shape": "rect", "Filled": "true", "Layer": 0, "w": 0.5, "h": 0.5, "Color": "Brown"}
    else:
        portrayal = {"Shape": "rect", "Filled": "true", "Layer": 0, "w": 0.9, "h": 0.9, "text_color": "Black",
                     "Color": "white"}
    return portrayal

# Define the grid size and visualization
grid = CanvasGrid(agent_portrayal, 18, 12, 540, 360)

# Add charts for monitoring various metrics
package_chart = ChartModule([
    {"Label": "Packages in Unload Truck", "Color": "Red"},
    {"Label": "Packages in Load Truck", "Color": "Green"},
    {"Label": "Packages in Shelves", "Color": "Blue"}
], data_collector_name='datacollector')
movement_chart = ChartModule([{"Label": "Total Movements", "Color": "Orange"}], data_collector_name='datacollector')
delivery_chart = ChartModule([{"Label": "Total Packages Delivered", "Color": "Purple"}], data_collector_name='datacollector')

# Parameters for the model, using sliders
model_params = {
    "width": 18,
    "height": 12,
    "initial_packages": mesa.visualization.Slider(
        "Total number of incoming packages",
        100,
        20,
        200,
        10,
    ),
        "num_lgvs": mesa.visualization.Slider(
        "Number of robots",
        5,
        5,
        7,
        1,
    ),
    "max_time": mesa.visualization.Slider(
        "Max Simulation Time",
        1000,  # Default value
        100,  # Minimum value
        10000,  # Maximum value
        100,  # Step size
        description="Set the maximum simulation time",
    ),
    "k": 0
}

# Create and launch the server
server = mesa.visualization.ModularServer(
    WarehouseModel,
    [grid, package_chart, movement_chart, delivery_chart],
    "Warehouse Model",
    model_params
)

server.port = 8521  # Default port for the server
server.launch()