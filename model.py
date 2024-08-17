

# from mesa import Agent, Model
# from mesa.time import RandomActivation
# from mesa.space import MultiGrid
# from mesa.datacollection import DataCollector
# import heapq
# import random

# class Package(Agent):
#     def __init__(self, unique_id, model, sku):
#         super().__init__(unique_id, model)
#         self.sku = sku

# class LGVAgent(Agent):
#     def __init__(self, unique_id, model):
#         super().__init__(unique_id, model)
#         self.battery = 100
#         self.carrying_package = None
#         self.destination = None
#         self.path = []
#         self.speed = 1
#         self.movements = 0
#         self.packages_delivered = 0
#         self.stuck_time = 0

#     def step(self):
#         if self.battery <= 0:
#             return

#         self.adjust_speed()
#         self.report_status()

#         if self.battery <= 20:
#             self.find_charging_station()
#             return

#         if not self.carrying_package:
#             if self.destination is None:
#                 self.destination = self.model.UNLOAD_TRUCK_POSITION
#                 self.path = self.a_star_search(self.destination)

#             if self.pos == self.destination:
#                 self.pick_up_package()
#             else:
#                 self.move_along_path()
#         else:
#             if self.destination is None:
#                 self.destination = self.find_shelf_or_load_truck()
#                 self.path = self.a_star_search(self.destination)

#             if self.pos == self.destination:
#                 self.deliver_package()
#             else:
#                 self.move_along_path()

#     def pick_up_package(self):
#         unload_truck = self.model.grid.get_cell_list_contents([self.model.UNLOAD_TRUCK_POSITION])[0]
#         if isinstance(unload_truck, Truck) and unload_truck.packages:
#             self.carrying_package = unload_truck.packages.pop()
#             print(f"Robot {self.unique_id} picked up a package from unload truck")
#         self.destination = None
#         self.stuck_time = 0

#     def deliver_package(self):
#         if self.pos == self.model.LOAD_TRUCK_POSITION:
#             load_truck = self.model.grid.get_cell_list_contents([self.pos])[0]
#             if isinstance(load_truck, Truck):
#                 load_truck.packages.append(self.carrying_package)
#                 self.packages_delivered += 1
#                 print(f"Robot {self.unique_id} delivered a package to load truck")
#         else:
#             shelf = self.model.grid.get_cell_list_contents([self.pos])[0]
#             if isinstance(shelf, Shelf) and shelf.add_package(self.carrying_package):
#                 self.packages_delivered += 1
#                 print(f"Robot {self.unique_id} delivered a package to shelf")
#             else:
#                 print(f"Robot {self.unique_id} couldn't deliver package, shelf full")
#                 return  # Keep the package if shelf is full
#         self.carrying_package = None
#         self.destination = None
#         self.stuck_time = 0

#     def find_shelf_or_load_truck(self):
#         shelves = [agent for agent in self.model.schedule.agents if isinstance(agent, Shelf) and agent.current_load < agent.capacity]
#         if not shelves:
#             return self.model.LOAD_TRUCK_POSITION
#         return min(shelves, key=lambda shelf: self.manhattan_distance(self.pos, shelf.pos)).pos

#     def move_along_path(self):
#         if self.path:
#             next_pos = self.path[0]
#             if not self.is_position_occupied(next_pos) and not self.is_out_of_bounds(next_pos):
#                 self.path.pop(0)
#                 print(f"Robot {self.unique_id} moving to {next_pos}")
#                 self.model.grid.move_agent(self, next_pos)
#                 self.movements += 1
#                 self.battery -= self.calculate_battery_usage()
#                 self.stuck_time = 0
#             else:
#                 print(f"Robot {self.unique_id} waiting, position {next_pos} occupied or out of bounds")
#                 self.stuck_time += 1
#                 if self.stuck_time > 5:  # If stuck for more than 5 steps
#                     self.attempt_alternative_move()
#         else:
#             self.recalculate_path()

#     def is_out_of_bounds(self, pos):
#         x, y = pos
#         return not (0 <= x < self.model.grid.width and 0 <= y < self.model.grid.height)

#     def attempt_alternative_move(self):
#         possible_steps = self.model.grid.get_neighborhood(
#             self.pos, moore=False, include_center=False)
#         free_steps = [pos for pos in possible_steps if not self.is_position_occupied(pos) and not self.is_out_of_bounds(pos)]
#         if free_steps:
#             new_position = self.random.choice(free_steps)
#             print(f"Robot {self.unique_id} taking alternative step to {new_position}")
#             self.model.grid.move_agent(self, new_position)
#             self.movements += 1
#             self.battery -= self.calculate_battery_usage()
#             self.recalculate_path()
#         self.stuck_time = 0

#     def recalculate_path(self):
#         if self.destination:
#             self.path = self.a_star_search(self.destination)
#         else:
#             self.find_new_task()

#     def find_new_task(self):
#         if not self.carrying_package:
#             self.destination = self.model.UNLOAD_TRUCK_POSITION
#         else:
#             self.destination = self.find_shelf_or_load_truck()
#         self.path = self.a_star_search(self.destination)

#     def is_position_occupied(self, pos):
#         cell_contents = self.model.grid.get_cell_list_contents(pos)
#         return any(isinstance(agent, LGVAgent) for agent in cell_contents)

#     def a_star_search(self, goal):
#         def heuristic(a, b):
#             return abs(a[0] - b[0]) + abs(a[1] - b[1])

#         frontier = []
#         heapq.heappush(frontier, (0, self.pos))
#         came_from = {}
#         cost_so_far = {}
#         came_from[self.pos] = None
#         cost_so_far[self.pos] = 0

#         while frontier:
#             current = heapq.heappop(frontier)[1]

#             if current == goal:
#                 break

#             for next_pos in self.model.grid.get_neighborhood(current, moore=False, include_center=False):
#                 if self.is_out_of_bounds(next_pos):
#                     continue
#                 new_cost = cost_so_far[current] + 1
#                 if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
#                     cost_so_far[next_pos] = new_cost
#                     priority = new_cost + heuristic(goal, next_pos)
#                     heapq.heappush(frontier, (priority, next_pos))
#                     came_from[next_pos] = current

#         current = goal
#         path = []
#         while current != self.pos:
#             path.append(current)
#             current = came_from[current]
#         path.reverse()
#         return path

#     def manhattan_distance(self, a, b):
#         return abs(a[0] - b[0]) + abs(a[1] - b[1])

#     def adjust_speed(self):
#         obstacle_free_distance = self.calculate_obstacle_free_distance()
#         self.speed = min(1, max(0.1, obstacle_free_distance / 10))

#     def calculate_battery_usage(self):
#         return 1 + (0.1 * self.speed) + (0.5 if self.carrying_package else 0)

#     def report_status(self):
#         print(f"Robot {self.unique_id}: Pos={self.pos}, Battery={self.battery:.2f}, "
#               f"Carrying={self.carrying_package is not None}, Speed={self.speed:.2f}")

#     def find_charging_station(self):
#         charging_stations = [agent for agent in self.model.schedule.agents if isinstance(agent, ChargingStation)]
#         if charging_stations:
#             nearest_station = min(charging_stations, key=lambda station: self.manhattan_distance(self.pos, station.pos))
#             self.destination = nearest_station.pos
#             self.path = self.a_star_search(self.destination)
#             print(f"Robot {self.unique_id} is heading to charging station at {self.destination}")

#     def calculate_obstacle_free_distance(self):
#         max_distance = 5
#         for distance in range(1, max_distance + 1):
#             next_pos = (self.pos[0] + distance, self.pos[1])
#             if self.model.grid.out_of_bounds(next_pos) or self.is_position_occupied(next_pos):
#                 return distance - 1
#         return max_distance

# class Shelf(Agent):
#     def __init__(self, unique_id, model, capacity=3):
#         super().__init__(unique_id, model)
#         self.capacity = capacity
#         self.packages = []

#     def add_package(self, package):
#         if len(self.packages) < self.capacity:
#             self.packages.append(package)
#             return True
#         return False

#     @property
#     def current_load(self):
#         return len(self.packages)

# class ChargingStation(Agent):
#     def __init__(self, unique_id, model):
#         super().__init__(unique_id, model)

# class Truck(Agent):
#     def __init__(self, unique_id, model, truck_type):
#         super().__init__(unique_id, model)
#         self.truck_type = truck_type
#         self.packages = []

# class WarehouseModel(Model):
#     UNLOAD_TRUCK_POSITION = (8, 0)
#     LOAD_TRUCK_POSITION = (0, 10)

#     def __init__(self, width, height, num_lgvs, initial_packages, max_time, k):
#         super().__init__()
#         self.current_id = 0
#         self.grid = MultiGrid(width, height, True)
#         self.schedule = RandomActivation(self)
#         self.max_time = max_time
#         self.time_elapsed = 0
#         self.total_movements = 0
#         self.total_packages_stored = 0
#         self.total_packages_delivered = 0

#         # Add shelves
#         shelf_positions = [
#             (7, 9), (7, 10), (8, 9), (8, 10), (9, 9), (9, 10),
#             (12, 9), (12, 10), (13, 9), (13, 10), (14, 9), (14, 10),
#             (7, 5), (7, 6), (8, 5), (8, 6), (9, 5), (9, 6),
#             (12, 1), (13, 1), (12, 2), (13, 2), (12, 3), (13, 3), (12, 4), (13, 4), (12, 5), (13, 5), (12, 6), (13, 6),
#             (17, 1), (17, 2), (17, 3), (17, 4), (17, 5), (17, 6),
#         ]
#         shelves = []
#         for pos in shelf_positions:
#             shelf = Shelf(self.next_id(), self)
#             self.grid.place_agent(shelf, pos)
#             self.schedule.add(shelf)
#             shelves.append(shelf)

#         # Distribute initial packages randomly across shelves
#         for _ in range(min(k * len(shelves), initial_packages)):
#             shelf = random.choice(shelves)
#             package = Package(self.next_id(), self, f"SKU-{random.randint(1000, 9999)}")
#             if shelf.add_package(package):
#                 self.grid.place_agent(package, shelf.pos)
#                 self.total_packages_stored += 1

#         # Add charging stations
#         charging_positions = [(0, 0), (2, 0), (4, 0), (0, 2), (2, 2), (4, 2)]
#         for pos in charging_positions:
#             station = ChargingStation(self.next_id(), self)
#             self.grid.place_agent(station, pos)
#             self.schedule.add(station)

#         # Add trucks at fixed positions
#         self.unload_truck = Truck(self.next_id(), self, "unload")
#         self.grid.place_agent(self.unload_truck, self.UNLOAD_TRUCK_POSITION)
#         self.schedule.add(self.unload_truck)

#         self.load_truck = Truck(self.next_id(), self, "load")
#         self.grid.place_agent(self.load_truck, self.LOAD_TRUCK_POSITION)
#         self.schedule.add(self.load_truck)

#         # Add remaining packages to unload truck
#         for _ in range(initial_packages - min(k * len(shelves), initial_packages)):
#             package = Package(self.next_id(), self, f"SKU-{random.randint(1000, 9999)}")
#             self.unload_truck.packages.append(package)

#         # Predefined positions for LGVs
#         lgv_positions = [(2, 3), (5, 11), (1, 7), (11, 6), (15, 0), (16, 10)]
#         for i in range(min(num_lgvs, len(lgv_positions))):
#             pos = lgv_positions[i]
#             lgv = LGVAgent(self.next_id(), self)
#             self.schedule.add(lgv)
#             self.grid.place_agent(lgv, pos)

#         self.datacollector = DataCollector(
#             model_reporters={
#                 "Battery Levels": lambda m: self.get_battery_levels(),
#                 "Packages in Unload Truck": lambda m: len(m.unload_truck.packages),
#                 "Packages in Load Truck": lambda m: len(m.load_truck.packages),
#                 "Packages in Shelves": lambda m: m.total_packages_stored,
#                 "Total Movements": lambda m: m.total_movements,
#                 "Total Packages Delivered": lambda m: m.total_packages_delivered
#             },
#             agent_reporters={"Battery": lambda a: getattr(a, 'battery', None)}
#         )

#     def next_id(self):
#         self.current_id += 1
#         return self.current_id

#     def get_battery_levels(self):
#         return [agent.battery for agent in self.schedule.agents if isinstance(agent, LGVAgent)]

#     def step(self):
#         self.time_elapsed += 1
#         self.schedule.step()
        
#         self.total_movements = sum(agent.movements for agent in self.schedule.agents if isinstance(agent, LGVAgent))
#         self.total_packages_delivered = sum(agent.packages_delivered for agent in self.schedule.agents if isinstance(agent, LGVAgent))
#         self.total_packages_stored = sum(len(shelf.packages) for shelf in self.schedule.agents if isinstance(shelf, Shelf))

#         self.datacollector.collect(self)

#         if self.time_elapsed >= self.max_time:
#             self.running = False
#             print(f"Simulation ended. Total movements: {self.total_movements}, "
#                   f"Packages stored: {self.total_packages_stored}, "
#                   f"Packages delivered: {self.total_packages_delivered}")

##sopa


from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
import heapq
import random

class Package(Agent):
    def __init__(self, unique_id, model, package_type):
        super().__init__(unique_id, model)
        self.package_type = package_type

class LGVAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.battery = 100
        self.carrying_package = None
        self.destination = None
        self.path = []
        self.speed = 1
        self.movements = 0
        self.packages_delivered = 0
        self.stuck_time = 0

    def step(self):
        if self.battery <= 0:
            return

        self.adjust_speed()
        self.report_status()

        if self.battery <= 20:
            self.find_charging_station()
            return

        if not self.carrying_package:
            if self.destination is None:
                self.destination = self.model.UNLOAD_TRUCK_POSITION
                self.path = self.a_star_search(self.destination)

            if self.pos == self.destination:
                self.pick_up_package()
            else:
                self.move_along_path()
        else:
            if self.destination is None:
                self.destination = self.find_shelf_or_load_truck()
                self.path = self.a_star_search(self.destination)

            if self.pos == self.destination:
                self.deliver_package()
            else:
                self.move_along_path()

    def pick_up_package(self):
        unload_truck = self.model.grid.get_cell_list_contents([self.model.UNLOAD_TRUCK_POSITION])[0]
        if isinstance(unload_truck, Truck) and unload_truck.packages:
            self.carrying_package = unload_truck.packages.pop()
            print(f"Robot {self.unique_id} picked up a package from unload truck")
        self.destination = None
        self.stuck_time = 0

    def deliver_package(self):
        if self.pos == self.model.LOAD_TRUCK_POSITION:
            load_truck = self.model.grid.get_cell_list_contents([self.pos])[0]
            if isinstance(load_truck, Truck):
                load_truck.packages.append(self.carrying_package)
                self.packages_delivered += 1
                print(f"Robot {self.unique_id} delivered a package to load truck")
        else:
            shelf = self.model.grid.get_cell_list_contents([self.pos])[0]
            if isinstance(shelf, Shelf) and shelf.add_package(self.carrying_package):
                self.packages_delivered += 1
                print(f"Robot {self.unique_id} delivered a package to shelf")
            else:
                print(f"Robot {self.unique_id} couldn't deliver package, shelf full")
                return  # Keep the package if shelf is full
        self.carrying_package = None
        self.destination = None
        self.stuck_time = 0

    def find_shelf_or_load_truck(self):
        shelves = [agent for agent in self.model.schedule.agents if isinstance(agent, Shelf) and agent.current_load < agent.capacity]
        if not shelves:
            return self.model.LOAD_TRUCK_POSITION
        return min(shelves, key=lambda shelf: self.manhattan_distance(self.pos, shelf.pos)).pos

    def move_along_path(self):
        if self.path:
            next_pos = self.path[0]
            if not self.is_position_occupied(next_pos) and not self.is_out_of_bounds(next_pos):
                self.path.pop(0)
                print(f"Robot {self.unique_id} moving to {next_pos}")
                self.model.grid.move_agent(self, next_pos)
                self.movements += 1
                self.battery -= self.calculate_battery_usage()
                self.stuck_time = 0
            else:
                print(f"Robot {self.unique_id} waiting, position {next_pos} occupied or out of bounds")
                self.stuck_time += 1
                if self.stuck_time > 5:  # If stuck for more than 5 steps
                    self.attempt_alternative_move()
        else:
            self.recalculate_path()


    def is_out_of_bounds(self, pos):
        x, y = pos
        return not (0 <= x < self.model.grid.width and 0 <= y < self.model.grid.height)

    def attempt_alternative_move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False)
        free_steps = [pos for pos in possible_steps if not self.is_position_occupied(pos) and not self.is_out_of_bounds(pos)]
        if free_steps:
            new_position = self.random.choice(free_steps)
            print(f"Robot {self.unique_id} taking alternative step to {new_position}")
            self.model.grid.move_agent(self, new_position)
            self.movements += 1
            self.battery -= self.calculate_battery_usage()
            self.recalculate_path()
        self.stuck_time = 0

    def recalculate_path(self):
        if self.destination:
            self.path = self.a_star_search(self.destination)
        else:
            self.find_new_task()

    def find_new_task(self):
        if not self.carrying_package:
            self.destination = self.model.UNLOAD_TRUCK_POSITION
        else:
            self.destination = self.find_shelf_or_load_truck()
        self.path = self.a_star_search(self.destination)

    def is_position_occupied(self, pos):
        cell_contents = self.model.grid.get_cell_list_contents(pos)
        return any(isinstance(agent, LGVAgent) for agent in cell_contents)

    def a_star_search(self, goal):
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        frontier = []
        heapq.heappush(frontier, (0, self.pos))
        came_from = {}
        cost_so_far = {}
        came_from[self.pos] = None
        cost_so_far[self.pos] = 0

        while frontier:
            current = heapq.heappop(frontier)[1]

            if current == goal:
                break

            for next_pos in self.model.grid.get_neighborhood(current, moore=False, include_center=False):
                if self.is_out_of_bounds(next_pos):
                    continue
                new_cost = cost_so_far[current] + 1
                if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                    cost_so_far[next_pos] = new_cost
                    priority = new_cost + heuristic(goal, next_pos)
                    heapq.heappush(frontier, (priority, next_pos))
                    came_from[next_pos] = current

        current = goal
        path = []
        while current != self.pos:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path

    def manhattan_distance(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def adjust_speed(self):
        obstacle_free_distance = self.calculate_obstacle_free_distance()
        self.speed = min(1, max(0.1, obstacle_free_distance / 10))

    def calculate_battery_usage(self):
        return 1 + (0.1 * self.speed) + (0.5 if self.carrying_package else 0)

    def report_status(self):
        print(f"Robot {self.unique_id}: Pos={self.pos}, Battery={self.battery:.2f}, "
              f"Carrying={self.carrying_package is not None}, Speed={self.speed:.2f}")

    def find_charging_station(self):
        charging_stations = [agent for agent in self.model.schedule.agents if isinstance(agent, ChargingStation)]
        if charging_stations:
            nearest_station = min(charging_stations, key=lambda station: self.manhattan_distance(self.pos, station.pos))
            self.destination = nearest_station.pos
            self.path = self.a_star_search(self.destination)
            print(f"Robot {self.unique_id} is heading to charging station at {self.destination}")

    def calculate_obstacle_free_distance(self):
        max_distance = 5
        for distance in range(1, max_distance + 1):
            next_pos = (self.pos[0] + distance, self.pos[1])
            if self.model.grid.out_of_bounds(next_pos) or self.is_position_occupied(next_pos):
                return distance - 1
        return max_distance

class Shelf(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.capacity = 3
        self.packages = []

    def add_package(self, package):
        if len(self.packages) < self.capacity:
            self.packages.append(package)
            return True
        return False

    @property
    def current_load(self):
        return len(self.packages)

class ChargingStation(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

class Truck(Agent):
    def __init__(self, unique_id, model, truck_type):
        super().__init__(unique_id, model)
        self.truck_type = truck_type
        self.packages = []

class WarehouseModel(Model):
    UNLOAD_TRUCK_POSITION = (8, 0)
    LOAD_TRUCK_POSITION = (0, 10)

    def __init__(self, width, height, num_lgvs, initial_packages, max_time, k):
        super().__init__()
        self.current_id = 0
        self.grid = MultiGrid(width, height, True)
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
            (7, 5), (7, 6), (8, 5), (8, 6), (9, 5), (9, 6),
            (12, 1), (13, 1), (12, 2), (13, 2), (12, 3), (13, 3), (12, 4), (13, 4), (12, 5), (13, 5), (12, 6), (13, 6),
            (17, 1), (17, 2), (17, 3), (17, 4), (17, 5), (17, 6),
        ]
        shelves = []
        for pos in shelf_positions:
            shelf = Shelf(self.next_id(), self)
            self.grid.place_agent(shelf, pos)
            self.schedule.add(shelf)
            shelves.append(shelf)

        # Add three types of packages
        package_types = ["Beer 1", "Beer 2", "Beer 3"]
        
        # Distribute initial packages randomly across shelves
        for _ in range(min(k * len(shelves), initial_packages)):
            shelf = random.choice(shelves)
            package_type = random.choice(package_types)
            package = Package(self.next_id(), self, package_type)
            if shelf.add_package(package):
                self.grid.place_agent(package, shelf.pos)
                self.total_packages_stored += 1

        # Add charging stations
        charging_positions = [(0, 0), (2, 0), (4, 0), (0, 2), (2, 2), (4, 2)]
        for pos in charging_positions:
            station = ChargingStation(self.next_id(), self)
            self.grid.place_agent(station, pos)
            self.schedule.add(station)

        # Add trucks at fixed positions
        self.unload_truck = Truck(self.next_id(), self, "unload")
        self.grid.place_agent(self.unload_truck, self.UNLOAD_TRUCK_POSITION)
        self.schedule.add(self.unload_truck)

        self.load_truck = Truck(self.next_id(), self, "load")
        self.grid.place_agent(self.load_truck, self.LOAD_TRUCK_POSITION)
        self.schedule.add(self.load_truck)

        # Add remaining packages to unload truck
        for _ in range(initial_packages - min(k * len(shelves), initial_packages)):
            package_type = random.choice(package_types)
            package = Package(self.next_id(), self, package_type)
            self.unload_truck.packages.append(package)

        # Predefined positions for LGVs
        lgv_positions = [(2, 3), (5, 11), (1, 7), (11, 6), (15, 0), (16, 10)]
        for i in range(min(num_lgvs, len(lgv_positions))):
            pos = lgv_positions[i]
            lgv = LGVAgent(self.next_id(), self)
            self.schedule.add(lgv)
            self.grid.place_agent(lgv, pos)

        self.datacollector = DataCollector(
            model_reporters={
                "Battery Levels": lambda m: self.get_battery_levels(),
                "Packages in Unload Truck": lambda m: len(m.unload_truck.packages),
                "Packages in Load Truck": lambda m: len(m.load_truck.packages),
                "Packages in Shelves": lambda m: m.total_packages_stored,
                "Total Movements": lambda m: m.total_movements,
                "Total Packages Delivered": lambda m: m.total_packages_delivered
            },
            agent_reporters={"Battery": lambda a: getattr(a, 'battery', None)}
        )

    def next_id(self):
        self.current_id += 1
        return self.current_id

    def get_battery_levels(self):
        return [agent.battery for agent in self.schedule.agents if isinstance(agent, LGVAgent)]

    def step(self):
        self.time_elapsed += 1
        
        # Central system logic
        for agent in self.schedule.agents:
            if isinstance(agent, LGVAgent):
                if agent.battery <= 20:
                    self.assign_charging_task(agent)
                elif not agent.carrying_package:
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

    def assign_charging_task(self, robot):
        charging_stations = [agent for agent in self.schedule.agents if isinstance(agent, ChargingStation)]
        if charging_stations:
            nearest_station = min(charging_stations, key=lambda station: self.grid.get_distance(robot.pos, station.pos))
            robot.destination = nearest_station.pos
            robot.path = robot.a_star_search(robot.destination)

    def assign_pickup_task(self, robot):
        if self.unload_truck.packages:
            robot.destination = self.UNLOAD_TRUCK_POSITION
            robot.path = robot.a_star_search(robot.destination)
        else:
            self.assign_idle_task(robot)

    def assign_delivery_task(self, robot):
        shelves = [agent for agent in self.schedule.agents if isinstance(agent, Shelf) and agent.current_load < agent.capacity]
        if shelves:
            nearest_shelf = min(shelves, key=lambda shelf: self.grid.get_distance(robot.pos, shelf.pos))
            robot.destination = nearest_shelf.pos
            robot.path = robot.a_star_search(robot.destination)
        else:
            robot.destination = self.LOAD_TRUCK_POSITION
            robot.path = robot.a_star_search(robot.destination)

    def assign_idle_task(self, robot):
        possible_positions = self.grid.get_neighborhood(robot.pos, moore=True, include_center=False)
        robot.destination = self.random.choice(possible_positions)
        robot.path = robot.a_star_search(robot.destination)

    ##* Hola te amo mucho