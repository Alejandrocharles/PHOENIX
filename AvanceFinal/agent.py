from mesa.agent import Agent
import numpy as np
import heapq

class Package(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model) 

class Battery(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model) 
    

class LGVAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        # Keep track of the spawn position (initial position)
        self.spawn_position = None
        # Initially None, this attribute keeps track of the package the agent is carrying.
        self.carrying_package = None
        # The target location where the agent is heading.
        self.destination = None
        # A list that holds the sequence of positions the agent should move through.
        self.path = []
        # Represents how fast the agent moves, default is 1.
        self.speed = 1
        # Tracks how many movements the agent has made.
        self.movements = 0
        # Tracks the number of packages delivered by the agent.
        self.packages_delivered = 0
        # Tracks the time the agent has been stuck without progress.
        self.stuck_time = 0
        # Initialize battery level to 100%.
        self.battery = 100  
        # Indicates if the agent is currently charging.
        self.charging = False  
        # Default discharge rate per movement.
        self.battery_discharge_rate = 1  
        # Battery percentage to trigger charging.
        self.low_battery_threshold = 30  
        # Keeps track of positions and actions the agent has taken.
        self.path_taken = []

    def on_grid(self, pos):
        self.spawn_position = pos
        self.pos = pos  # Ensure the agent knows its position



    def step(self):
        # Debug: Print the robot's battery level each step.
        print(f"Robot {self.unique_id} battery level: {self.battery}%")

        # If the robot is charging, continue charging.
        if self.charging:
            self.charge_battery()
            return

        # If the battery is low and the robot is not charging, find the nearest battery station.
        if self.battery <= self.low_battery_threshold:
            self.destination = self.find_nearest_battery()
            self.path = self.a_star_search(self.destination)
            self.move_along_path()
            return

        # Normal operations (picking up and delivering packages)
        
        if not self.carrying_package:
            if self.destination is None:
                self.destination = self.model.unload_for_agent
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

    def discharge_battery(self):
        self.battery -= self.battery_discharge_rate * self.speed
        if self.battery <= 0:
            self.battery = 0
            print(f"Robot {self.unique_id} has run out of battery and is unable to move.")
    
    def charge_battery(self):
        battery_agents = [agent for agent in self.model.grid.get_cell_list_contents([self.pos]) if isinstance(agent, Battery)]
        if battery_agents:
            self.battery += 5  # Charge rate per step
            if self.battery >= 100:
                self.battery = 100
                self.charging = False
                print(f"Robot {self.unique_id} has fully charged and is resuming its tasks.")
                # If the robot was carrying a package, continue to the original destination after charging.
                if self.carrying_package:
                    self.destination = self.find_shelf_or_load_truck()
                    self.path = self.a_star_search(self.destination)
            else:
                print(f"Robot {self.unique_id} is charging. Current battery level: {self.battery}%.")
        else:
            # If the robot is not on a battery position, recalculate path to the nearest battery
            print(f"Robot {self.unique_id} is not on a battery position, recalculating path to charge.")
            self.destination = self.find_nearest_battery()
            if self.destination:
                self.path = self.a_star_search(self.destination)
                self.move_along_path()


    def find_nearest_battery(self):
    # Get all the positions where Battery agents are placed
        batteries = [(agent.pos, agent) for agent in self.model.schedule.agents if isinstance(agent, Battery)]
        
        # Filter out batteries that are already occupied by other robots
        available_batteries = [
            (pos, battery) for pos, battery in batteries 
            if not any(isinstance(agent, LGVAgent) for agent in self.model.grid.get_cell_list_contents(pos))
        ]
        
        # If there are no available batteries, return None
        if not available_batteries:
            print(f"Robot {self.unique_id}: No available battery positions found.")
            return None

        # Find the nearest available battery position
        nearest_battery_pos, nearest_battery = min(available_batteries, key=lambda battery: self.manhattan_distance(self.pos, battery[0]))
        
        # Set charging to True and return the position
        self.charging = True
        return nearest_battery_pos


    def pick_up_package(self):
        unload_truck = self.model.grid.get_cell_list_contents([self.model.unload_for_agent])[0]
        if isinstance(unload_truck, Truck) and unload_truck.packages:
            self.carrying_package = unload_truck.packages.pop()
            self.path_taken.append({"position": list(self.pos), "action": "pickup"})
            print(f"Robot {self.unique_id} picked up a package from unload truck")
        self.destination = None
        self.stuck_time = 0

    def deliver_package(self):
        if self.pos == self.model.load_for_agent:
            load_truck = self.model.grid.get_cell_list_contents([self.pos])[0]
            if isinstance(load_truck, Truck):
                load_truck.packages.append(self.carrying_package)
                self.path_taken.append({"position": list(self.pos), "action": "deliver_load"})
                self.packages_delivered += 1
                self.model.packages_delivered_in_phase += 1
                print(f"Robot {self.unique_id} delivered a package to load truck. Total delivered: {self.packages_delivered}")
        else:
            shelf_pos = self.model.shelf_to_stop.get(self.pos, None)
            if shelf_pos:
                shelf = self.model.grid.get_cell_list_contents([shelf_pos])
                if shelf and isinstance(shelf[0], Shelf) and shelf[0].add_package(self.carrying_package):
                    self.path_taken.append({"position": list(self.pos), "action": "deliver_shelf"})
                    self.packages_delivered += 1
                    self.model.packages_delivered_in_phase += 1
                    print(f"Robot {self.unique_id} delivered a package to shelf at {shelf_pos}. Total delivered: {self.packages_delivered}")

        # Reset robot state after delivery
        self.carrying_package = None
        self.destination = None
        self.stuck_time = 0

    def find_shelf_or_load_truck(self):
        shelves = [agent for agent in self.model.schedule.agents if isinstance(agent, Shelf) and agent.current_load < agent.capacity]
        if not shelves:
            return self.model.load_for_agent
        
        # Find the nearest shelf's stopping position
        nearest_shelf = min(shelves, key=lambda shelf: self.manhattan_distance(self.pos, shelf.pos))
        
        # Get the stopping position from the dictionary
        stop_position = self.model.shelf_to_stop.get(nearest_shelf.pos, nearest_shelf.pos)
        return stop_position

    def is_battery_position(self, pos):
        """Check if a position is a battery position and the robot is not charging."""
        if pos in self.model.battery_positions and not self.charging:
            return True
        return False
    
    def move_along_path(self):
        if self.path:
            next_pos = self.path[0]
            # Ensure the robot only moves to a battery position if charging and a battery exists there
            battery_exists_at_pos = any(isinstance(agent, Battery) for agent in self.model.grid.get_cell_list_contents([next_pos]))
            if (not self.is_position_occupied(next_pos) and
                not self.is_out_of_bounds(next_pos) and
                not self.is_position_occupied_by_obstacle(next_pos) and
                (self.charging and battery_exists_at_pos or not self.is_battery_position(next_pos))):
                
                # Move to the next position
                self.path.pop(0)
                self.path_taken.append({"position": list(next_pos), "action": "move"})
                self.model.grid.move_agent(self, next_pos)
                self.movements += 1
                self.discharge_battery()
                self.stuck_time = 0
            else:
                self.stuck_time += 1
                if self.stuck_time > 5:
                    self.attempt_alternative_move()
        else:
            self.recalculate_path()




    def is_out_of_bounds(self, pos):
        x, y = pos
        return not (0 <= x < self.model.grid.width and 0 <= y < self.model.grid.height)

    def attempt_alternative_move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False)
        free_steps = [pos for pos in possible_steps if not self.is_position_occupied(pos) and not self.is_out_of_bounds(pos) and not self.is_position_occupied_by_obstacle(pos)]

        if free_steps:
            new_position = self.random.choice(free_steps)
            self.model.grid.move_agent(self, new_position)
            self.movements += 1
            self.recalculate_path()
        self.stuck_time = 0

    def recalculate_path(self):
        if self.destination:
            # Ensure the new path avoids shelves and prioritizes charging if needed
            self.path = self.a_star_search(self.destination)
            if self.charging and self.path:
                print(f"Robot {self.unique_id} recalculated path to battery station.")
        else:
            self.find_new_task()

    def find_new_task(self):
        if not self.carrying_package:
            self.destination = self.model.unload_for_agent
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
                if self.is_out_of_bounds(next_pos) or self.is_position_occupied_by_obstacle(next_pos):
                    continue
                new_cost = cost_so_far[current] + 1
                if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                    cost_so_far[next_pos] = new_cost
                    priority = new_cost + heuristic(goal, next_pos)
                    heapq.heappush(frontier, (priority, next_pos))
                    came_from[next_pos] = current

        if current != goal:
            print(f"Pathfinding failed from {self.pos} to {goal}. Returning to start or idle state.")
            return []

        path = []
        while current != self.pos:
            if current is None:
                return []
            path.append(current)
            current = came_from.get(current)
        path.reverse()
        return path

    def is_position_occupied_by_obstacle(self, pos):
        """Extend the method to consider battery positions as obstacles unless charging."""
        cell_contents = self.model.grid.get_cell_list_contents(pos)
        is_battery = self.is_battery_position(pos)
        return any(isinstance(agent, (Shelf, VisualTruck)) for agent in cell_contents) or is_battery

    def manhattan_distance(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def adjust_speed(self):
        obstacle_free_distance = self.calculate_obstacle_free_distance()
        self.speed = min(1, max(0.1, obstacle_free_distance / 10))


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



class Truck(Agent):
    def __init__(self, unique_id, model, truck_type):
        super().__init__(unique_id, model)
        self.truck_type = truck_type
        self.packages = []


class VisualTruck(Agent):
    def __init__(self, unique_id, model, truck_type):
        super().__init__(unique_id, model)
        self.truck_type = truck_type



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