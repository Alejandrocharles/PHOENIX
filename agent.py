from mesa.agent import Agent
import numpy as np
import heapq

class Package(Agent):
    def __init__(self, unique_id, model, ):
        super().__init__(unique_id, model)
        self. = 

class LGVAgent(Agent):
    package_count = 0
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



    def pick_up_package(self):
        unload_truck = self.model.grid.get_cell_list_contents([self.model.unload_for_agent])[0]
        if isinstance(unload_truck, Truck) and unload_truck.packages:
            self.carrying_package = unload_truck.packages.pop()
            print(f"Robot {self.unique_id} picked up a package from unload truck")
        self.destination = None
        self.stuck_time = 0



    def deliver_package(self):
        if self.pos == self.model.load_for_agent:
            # Deliver the package to the load truck
            load_truck = self.model.grid.get_cell_list_contents([self.pos])[0]
            if isinstance(load_truck, Truck):
                load_truck.packages.append(self.carrying_package)
                self.packages_delivered += 1
                print(f"Robot {self.unique_id} delivered a package to load truck")
        else:
            # The agent is at a stopping position; find the corresponding shelf
            shelf_pos = self.model.shelf_to_stop.get(self.pos, None)

            if shelf_pos:
                # Check if the shelf is actually at the expected position
                shelf = self.model.grid.get_cell_list_contents([shelf_pos])
                print(f"Contents at {shelf_pos}: {shelf}")

                if shelf and isinstance(shelf[0], Shelf) and shelf[0].add_package(self.carrying_package):
                    self.packages_delivered += 1
                    print(f"Robot {self.unique_id} delivered a package to shelf at {shelf_pos}")
                else:
                    print(f"Robot {self.unique_id} couldn't deliver package, shelf at {shelf_pos} is full or not found")
            else:
                print(f"Robot {self.unique_id} is at stop position {self.pos} but could not find corresponding shelf")

        # Reset the robot's state after delivery
        self.carrying_package = None
        self.destination = None
        self.stuck_time = 0




    def find_shelf_or_load_truck(self):
        shelves = [agent for agent in self.model.schedule.agents if isinstance(agent, Shelf) and agent.current_load < agent.capacity]
        if not shelves:
            return self.model.load_for_agent
        # return min(shelves, key=lambda shelf: self.manhattan_distance(self.pos, shelf.pos)).pos
        
        # Find the nearest shelf's stopping position
        nearest_shelf = min(shelves, key=lambda shelf: self.manhattan_distance(self.pos, shelf.pos))
        
        # Get the stopping position from the dictionary
        stop_position = self.model.shelf_to_stop.get(nearest_shelf.pos, nearest_shelf.pos)
        return stop_position



    def move_along_path(self):
        if self.path:
            next_pos = self.path[0]
            if self.is_position_occupied_by_obstacle(next_pos):
                print(f"WARNING: Robot {self.unique_id} attempting to move onto an obstacle at {next_pos}!")

            # Check for out-of-bounds, obstacles, and other agents
            if not self.is_position_occupied(next_pos) and not self.is_out_of_bounds(next_pos) and not self.is_position_occupied_by_obstacle(next_pos):
                self.path.pop(0)
                print(f"Robot {self.unique_id} moving to {next_pos}")
                self.model.grid.move_agent(self, next_pos)
                self.movements += 1
                self.stuck_time = 0
            else:
                print(f"Robot {self.unique_id} cannot move to {next_pos} because it is occupied, out of bounds, or has an obstacle.")
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
            print(f"Robot {self.unique_id} taking alternative step to {new_position}")
            self.model.grid.move_agent(self, new_position)
            self.movements += 1
            self.recalculate_path()
        self.stuck_time = 0


    def recalculate_path(self):
        if self.destination:
            # Ensure the new path avoids shelves
            self.path = self.a_star_search(self.destination)
            # Check the first few positions in the path and avoid shelves
            if self.path and any(self.is_position_occupied_by_obstacle(pos) for pos in self.path[:3]):
                print(f"Robot {self.unique_id} recalculated path still includes a shelf, reattempting.")
                self.path = self.a_star_search(self.destination)
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

        current = goal
        path = []
        while current != self.pos:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path



    def is_position_occupied_by_obstacle(self, pos):
        cell_contents = self.model.grid.get_cell_list_contents(pos)
        return any(isinstance(agent, (Shelf, VisualTruck)) for agent in cell_contents)



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
