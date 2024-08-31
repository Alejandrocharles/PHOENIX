from fastapi import FastAPI, BackgroundTasks
from model import WarehouseModel
from agent import LGVAgent
import time

app = FastAPI()

# Initialize the model
model = WarehouseModel(width=18, height=12, num_lgvs=5, initial_packages=100, max_time=1000, k=0)

# Background task to run the simulation
def run_simulation(steps: int):
    for _ in range(steps):
        model.step()
        time.sleep(0.1)  # Adjust the sleep time as needed for a smoother simulation

@app.on_event("startup")
async def startup_event():
    # Start the simulation automatically when the server starts
    background_tasks = BackgroundTasks()
    background_tasks.add_task(run_simulation, 1000)  # Run the simulation for 1000 steps initially

@app.get("/run_simulation")
def run_simulation_endpoint(steps: int, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_simulation, steps)
    return {"message": f"Simulation running for {steps} steps."}

@app.get("/robots")
def get_robots():
    robots_data = []
    for agent in model.schedule.agents:
        if isinstance(agent, LGVAgent):
            path_data = [{"x": pos["position"][0], "y": pos["position"][1]} for pos in agent.path_taken]
            robots_data.append({
                "spawnPosition": {"x": agent.spawn_position[0], "y": agent.spawn_position[1]},
                "path": path_data
            })
    return {"robots": robots_data}

@app.get("/")
def read_root():
    return {"message": "Warehouse Simulation API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)