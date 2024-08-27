
from mesa.model import Model

from agent import Package, Shelf, Truck, LGVAgent, VisualTruck

from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector

import random

class WarehouseModel(Model):
    UNLOAD_TRUCK_POSITION = (8, 0)
    unload_for_agent = (8,1)
    LOAD_TRUCK_POSITION = (0, 10)
    load_for_agent = (1,10)

    def __init__(self, width, height, num_lgvs, initial_packages, max_time, k):
        super().__init__()
        self.current_id = 0
        self.grid = MultiGrid(width, height, False)
        self.schedule = RandomActivation(self)
        self.max_time = max_time
        self.time_elapsed = 0
        self.total_movements = 0
        self.total_packages_stored = 0
        self.total_packages_delivered = 0





        # Add shelves
        shelf_positions = [
            (7, 9), (7, 10), (8, 9), (8, 10), (9, 9), (9, 10),
            (12, 9), (12, 10), (13, 9), (13, 10), (14, 9), (14, 10),
            (5, 5), (5, 6), (6, 5), (6, 6), (7, 5), (7, 6), (12, 2), (13, 2), (12, 3), (13, 3), (12, 4), (13, 4), (12, 5), (13, 5), (12, 6), (13, 6),
            (17, 1), (17, 2), (17, 3), (17, 4), (17, 5), (17, 6),
        ]
        self.shelf_to_stop = {
            (5, 4): (5, 5), 
            (5, 7): (5, 6),  
            (6, 4): (6, 5), 
            (6, 7): (6, 6),
            (7, 4): (7, 5), 
            (7, 7): (7, 6), 

            (7,8): (7,9),
            (7,11):(7,10),
            (8,8): (8,9),
            (8,11):(8,10),
            (9,8): (9,9),
            (9,11):(9,10),

            (11, 2): (12, 2),
            (11, 3): (12, 3),
            (11, 4): (12, 4),  
            (11, 5): (12, 5),
            (11, 6): (12, 6),


            (14, 2): (13, 2),
            (14, 3): (13, 3),
            (14, 4): (13, 4),  
            (14, 5): (13, 5),
            (14, 6): (13, 6),
            
            (12, 8): (12, 9),
            (12, 11): (12, 10), 
            (13, 8): (13, 9),
            (13, 11): (13, 10),
            (14, 8): (14, 9),
            (14, 11): (14, 10),

            (16, 1): (17, 1),
            (16, 2): (17, 2), 
            (16, 3): (17, 3),
            (16, 4): (17, 4),
            (16, 5): (17, 5),
            (16, 6): (17, 6),


        }
        shelves = []
        for pos in shelf_positions:
            shelf = Shelf(self.next_id(), self)
            self.grid.place_agent(shelf, pos)
            self.schedule.add(shelf)
            shelves.append(shelf)


        # Add three types of packages
        package_types = ["Beer 1", "Beer 2", "Beer 3"]
        
        # Distribute initial packages randomly across shelves
        for _ in range(min(k * len(shelves), 0)):
            shelf = random.choice(shelves)
             = random.choice(package_types)
            package = Package(self.next_id(), self, )
            if shelf.add_package(package):
                self.grid.place_agent(package, shelf.pos)
                self.total_packages_stored += 1


        # Add trucks at fixed positions
        self.unload_truckVISUAL = VisualTruck(self.next_id(), self, "unload")
        self.grid.place_agent(self.unload_truckVISUAL, self.UNLOAD_TRUCK_POSITION)
        self.schedule.add(self.unload_truckVISUAL)

        self.load_truckVISUAL = VisualTruck(self.next_id(), self, "load")
        self.grid.place_agent(self.load_truckVISUAL, self.LOAD_TRUCK_POSITION)
        self.schedule.add(self.load_truckVISUAL)

        self.unload_truck = Truck(self.next_id(), self, "unload")
        self.grid.place_agent(self.unload_truck, self.unload_for_agent)
        self.schedule.add(self.unload_truck)

        self.load_truck = Truck(self.next_id(), self, "load")
        self.grid.place_agent(self.load_truck, self.load_for_agent)
        self.schedule.add(self.load_truck)


        #todo borrar si no
        self.initial_unload_truck_packages = len(self.unload_truck.packages)

        
        # # Add remaining packages to unload truck
        for _ in range(initial_packages - min(k * len(shelves), initial_packages)):
             = random.choice(package_types)
            package = Package(self.next_id(), self, )
            self.unload_truck.packages.append(package)

        # Predefined positions for LGVs
        lgv_positions = [(0, 2), (0, 3), (0, 4), (0, 5), (0, 6),(0,7),(0,8)]
        for i in range(min(num_lgvs, len(lgv_positions))):
            pos = lgv_positions[i]
            lgv = LGVAgent(self.next_id(), self)
            self.schedule.add(lgv)
            self.grid.place_agent(lgv, pos)

        self.datacollector = DataCollector(
            model_reporters={
                "Packages in Unload Truck": lambda m: len(m.unload_truck.packages),
                "Packages in Load Truck": lambda m: len(m.load_truck.packages),
                "Packages in Shelves": lambda m: m.total_packages_stored,
                "Total Movements": lambda m: m.total_movements,
                "Total Packages Delivered": lambda m: m.total_packages_delivered
            },
        )

    def next_id(self):
        self.current_id += 1
        return self.current_id



    def step(self):
        self.time_elapsed += 1
        
        # Central system logic
        for agent in self.schedule.agents:
            if isinstance(agent, LGVAgent):
                if not agent.carrying_package:
                    self.assign_pickup_task(agent)
                else:
                    self.assign_delivery_task(agent)

        self.schedule.step()
        
        self.total_movements = sum(agent.movements for agent in self.schedule.agents if isinstance(agent, LGVAgent))
        self.total_packages_delivered = sum(agent.packages_delivered for agent in self.schedule.agents if isinstance(agent, LGVAgent))
        self.total_packages_stored = sum(len(shelf.packages) for shelf in self.schedule.agents if isinstance(shelf, Shelf))

        self.datacollector.collect(self)

        if self.time_elapsed >= self.max_time:
            self.running = False
            print(f"Simulation ended. Total movements: {self.total_movements}, "
                  f"Packages stored: {self.total_packages_stored}, "
                  f"Packages delivered: {self.total_packages_delivered}")



    def assign_pickup_task(self, robot):
        if self.unload_truck.packages:
            robot.destination = self.unload_for_agent
            robot.path = robot.a_star_search(robot.destination)
        else:
            self.assign_idle_task(robot)



    def assign_delivery_task(self, robot):
        if self.should_deliver_to_load_truck():
            # Deliver to load truck
            robot.destination = self.load_for_agent
            print(f"Robot {robot.unique_id} assigned to deliver to load truck")
        else:
            # Deliver to shelves as before
            shelves = [agent for agent in self.schedule.agents if isinstance(agent, Shelf) and agent.current_load < agent.capacity]
            if shelves:
                nearest_shelf = min(shelves, key=lambda shelf: self.manhattan_distance(robot.pos, shelf.pos))
                stop_position = None
                for stop_pos, shelf_pos in self.shelf_to_stop.items():
                    if shelf_pos == nearest_shelf.pos:
                        stop_position = stop_pos
                        break
                if stop_position:
                    robot.destination = stop_position
                    print(f"Robot {robot.unique_id} assigned to stop position {stop_position} for shelf at {nearest_shelf.pos}")
                else:
                    print(f"Error: No stop position found for shelf at {nearest_shelf.pos}")
            else:
                robot.destination = self.load_for_agent
        robot.path = robot.a_star_search(robot.destination)

    
    def manhattan_distance(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def assign_idle_task(self, robot):
        possible_positions = self.grid.get_neighborhood(robot.pos, moore=True, include_center=False)
        robot.destination = self.random.choice(possible_positions)
        robot.path = robot.a_star_search(robot.destination)


    def should_deliver_to_load_truck(self):
        # Example condition: Deliver to the load truck if there are more than 50 packages in the warehouse
        return self.total_packages_stored > 20

 
        
