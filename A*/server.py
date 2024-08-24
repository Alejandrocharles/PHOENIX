# shelves initialized  in 0 
# 3 types of packages id = 001, 002, 003
# start positions predefined for different options 5 to 10 robots, fully charged batteries
# the user sets a maximum simutlation time
# Each robot has a battery discharge profile influenced by actions and distance traveled.
# central robot that tells the robots what path they will follow

import mesa
from mesa.visualization.modules import CanvasGrid, ChartModule
from model import WarehouseModel, LGVAgent, Shelf, Truck, ChargingStation, Package

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
battery_chart = ChartModule([{"Label": "Battery Levels", "Color": "Black"}], data_collector_name='datacollector')
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
    "num_lgvs": mesa.visualization.Slider(
        "Number of Robots",
        6,  # Default value
        5,  # Minimum value
        10,  # Maximum value
        1,  # Step size
        description="Choose the number of robots in the model",
    ),
    "initial_packages": mesa.visualization.Slider(
        "Initial Total Packages",
        100,  # Default value
        0,  # Minimum value
        200,  # Maximum value
        10,  # Step size
        description="Set total number of initial packages in the system",
    ),
    "max_time": mesa.visualization.Slider(
        "Max Simulation Time",
        1000,  # Default value
        100,  # Minimum value
        10000,  # Maximum value
        100,  # Step size
        description="Set the maximum simulation time",
    ),
    "k": mesa.visualization.Slider(
        "Initial Shelf Load Factor",
        1,  # Default value
        0,  # Minimum value
        3,  # Maximum value
        1,  # Step size
        description="Set the initial load factor for shelves (0-3)",
    ),
}

# Create and launch the server
server = mesa.visualization.ModularServer(
    WarehouseModel,
    [grid, battery_chart, package_chart, movement_chart, delivery_chart],
    "Warehouse Model",
    model_params
)

server.port = 8521  # Default port for the server
server.launch()