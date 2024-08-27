from mesa.agent import Agent
import numpy as np
import heapq

class Package(Agent):
    def __init__(self, unique_id, model, ):
        super().__init__(unique_id, model)
        self. = 

class LGVAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.carrying_package = None
        self.destination = None
        self.path = []
        self.speed = 1
        self.movements = 0
        self.packages_delivered = 0
        self.stuck_time = 0

    def step(self):
        self.adjust_speed()
        self.report_status()

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
                return  
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
            if not self.is_position_occupied(next_pos) or next_pos == self.destination:
                self.path.pop(0)
                print(f"Robot {self.unique_id} moving to {next_pos}")
                self.model.grid.move_agent(self, next_pos)
                self.movements += 1
                self.stuck_time = 0
            else:
                print(f"Robot {self.unique_id} waiting, position {next_pos} occupied")
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
        free_steps = [pos for pos in possible_steps if not self.is_position_occupied(pos) and not self.is_out_of_bounds(pos)]
        if free_steps:
            new_position = self.random.choice(free_steps)
            print(f"Robot {self.unique_id} taking alternative step to {new_position}")
            self.model.grid.move_agent(self, new_position)
            self.movements += 1
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
                
                # Allow movement to the goal even if it's occupied (for interaction)
                if next_pos != goal and self.is_position_occupied(next_pos):
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
            current = came_from.get(current)
            if current is None:
                return []  # No path found
        path.reverse()
        return path

    
    def manhattan_distance(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def adjust_speed(self):
        obstacle_free_distance = self.calculate_obstacle_free_distance()
        self.speed = min(1, max(0.1, obstacle_free_distance / 10))

    def report_status(self):
        print(f"Robot {self.unique_id}: Pos={self.pos}, Carrying={self.carrying_package is not None}, Speed={self.speed:.2f}")

    def calculate_obstacle_free_distance(self):
        max_distance = 5
        for distance in range(1, max_distance + 1):
            next_pos = (self.pos[0] + distance, self.pos[1])
            if self.model.grid.out_of_bounds(next_pos) or self.is_position_occupied(next_pos):
                return distance - 1
        return max_distance
    def is_position_occupied(self, pos):
        cell_contents = self.model.grid.get_cell_list_contents(pos)
        return any(isinstance(agent, (LGVAgent, Shelf)) for agent in cell_contents)

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