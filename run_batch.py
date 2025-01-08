import os
import numpy as np
import os
import gc
from neuron import h
from argparse import ArgumentParser

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Change the working directory to the script's directory
os.chdir(script_dir)

parser = ArgumentParser(description="Run a NEURON simulation with specified parameters.")
parser.add_argument("-f", "--freq", type=float, required=True, help="Frequency (Hz) for the simulation")
parser.add_argument("-v", "--voltage", type=float, required=True, help="Voltage (mV) for the simulation")

args = parser.parse_args()

from init_stim import run_simulation,save_plots
var="cfreq"
cell_id=1
theta = 180
phi = 0
simtime = 100
dt = 0.001
amp = 40
depth = 1
freq = 500
modfreq = 100
ton = 0
dur = simtime
run_id = 0
cb=True

# Get command-line arguments
freq = args.freq
amp = args.voltage

try:
    print(f"Running simulation for freq={freq}, v={amp}")   
    e_dir,t, is_xtra,vrec,soma_v,dend_v,axon_v,cell=run_simulation(
        cell_id, theta, phi, simtime, dt, amp, depth, freq, modfreq,ton,dur,run_id,cb,var)
    save_plots(e_dir,t,is_xtra,vrec,soma_v,dend_v,axon_v)
except Exception as e:
    print(f"Error during simulation for freq={freq}, v={amp}: {e}")
finally:
    # Cleanup to free resources
    h("forall delete_section()")  # Delete all sections
    gc.collect()  # Force garbage collection

