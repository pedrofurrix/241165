import numpy as np
import os
import gc
from neuron import h
from itertools import product
from multiprocessing import Pool, cpu_count

h.nrn_mainmenu(False)  # Disable NEURON's main menu and GUI

from argparse import ArgumentParser

parser = ArgumentParser(description="Run NEURON simulations with specified parameters.")
parser.add_argument("-f", "--freq", type=float, nargs="*", required=True, help="Frequencies (Hz) for the simulations")
parser.add_argument("-v", "--voltage", type=float, nargs="*", required=True, help="Voltages (mV) for the simulations")
parser.add_argument("-d", "--depth", type=float, nargs="*", required=False,  default=1.0, help="Modulation depth (0-1)")
parser.add_argument("-m", "--modfreq", type=float, nargs="*", required=False,  default=10, help="Modulation Frequency (Hz)")
parser.add_argument("-b","--batch", action="store_true", help="Enable batch processing mode")



# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Change the working directory to the script's directory
os.chdir(script_dir)
import init_stim  
var="cfreq"
cell_id=1
theta = 180
phi = 0
simtime = 1000
dt = 0.001
amp = 40
depth = 1
freq = 500
modfreq = 100
ton = 0
dur = simtime
run_id = 0
cb=True
ramp=True
ramp_duration=400
tau=0
data_dir="/media/sf_Data"


def run_sim(params):
    freq, amp, modfreq, depth = params
    try:
        print(f"Running simulation for freq={freq}, amp={amp}, modfreq={modfreq}, depth={depth}")
        e_dir,t, is_xtra,vrec,soma_v,dend_v,axon_v,cell=init_stim.run_simulation(cell_id, theta, phi, simtime, dt, amp,
                                                                                  depth, freq, modfreq, ton,dur,run_id,cb,var,ramp,ramp_duration,tau,data_dir)
        print(f"Simulation completed for freq={freq}, amp={amp}")
        init_stim.save_plots(e_dir, t, is_xtra, vrec, soma_v, dend_v)

    except Exception as e:
        print(f"Error during simulation for freq={freq}, amp={amp}: {e}")
    finally:
        h("forall delete_section()")  # Cleanup NEURON sections
        gc.collect()  # Force garbage collection
    

if __name__ == "__main__":
    # Parse arguments
    args = parser.parse_args()

    # Get values
    freqs = args.freq
    amps = args.voltage
    modfreqs = args.modfreq
    depths = args.depth

    if args.batch:
        # Generate all combinations of (freq, amp)
        param_combinations = list(product(freqs, amps,modfreqs,depths))

        # # Add modfreq and depth to each combination
        # params = [(freq, amp, modfreq, depth) for freq, amp in param_combinations]
        params=param_combinations

         # Use multiprocessing
        maxnum_processes = cpu_count()  # Use all available cores
        num_processes=len(params)

        if num_processes>maxnum_processes:
            raise ValueError("Trying to run too many processes at once")
        with Pool(processes=num_processes) as pool:
            pool.map(run_sim, params)

        
    else:
        # Run a single simulation
        if len(freqs) > 1 or len(amps) > 1:
            raise ValueError("Batch mode (--batch) must be enabled for multiple frequencies/voltages.")

        # Extract single values for freq and amp
        freq = freqs[0]
        amp = amps[0]
        modfreq = modfreqs[0]
        depth = depths[0]

        run_sim((freq, amp, modfreq, depth))