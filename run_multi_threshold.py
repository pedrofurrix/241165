import os
import time
import sys
from argparse import ArgumentParser
from neuron import h
import gc
from itertools import product
from multiprocessing import Pool, cpu_count

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Change the working directory to the script's directory
os.chdir(script_dir)

parser = ArgumentParser(description="Run a NEURON simulation with specified parameters.")
parser.add_argument("-f", "--freq", type=float, nargs="*", required=True, help="Frequencies (Hz) for the simulations")
parser.add_argument("-c", "--id", type=int, nargs="*",required=True, help="Cell id")
parser.add_argument("-b","--batch", action="store_true", help="Enable batch processing mode")

from filter_and_max import get_folder
from init_threshold import threshold
from debug_thresholds import get_maxv,plot_voltage_highest_spiken

def run_threshold(cell_id,freq,var,data_dir):
    start=time.time()
   
    init_amp = 100
    top_dir,bot_dir,param_dir=get_folder(freq,init_amp,cell_id,var=var,filtered=False,data_dir=data_dir)
    

    pathf=os.path.join(data_dir,"data",str(cell_id),str(var),"threshold",f"{freq}Hz")
    if not os.path.exists(pathf):
        os.makedirs(pathf,exist_ok=True)
    
    theta = 180
    phi = 0
    simtime = 1000
    dt = 0.001
    depth = 1
    modfreq = 10
    ton = 0
    dur = simtime
    run_id = 0
    cb=False
    ramp=True
    ramp_duration=400
    tau=0
    thresh=20

    threshold(cell_id, theta, phi, simtime, dt, init_amp, depth, freq, modfreq,ton,dur,top_dir,
              thresh=thresh,cb=cb,var=var,ramp=ramp,ramp_duration=ramp_duration,tau=tau,data_dir=data_dir)
    end=time.time()
    print(f"The time of execution of above program is : {end-start} s")
    print(f"The time of execution of above program is : {(end-start)/60} mins")
    hdf5=True
    max_v=get_maxv(cell_id,freq,var,hdf5,data_dir)
    v_max,t,max_segment=plot_voltage_highest_spiken(cell_id,freq,var,hdf5,data_dir,save=True)

# Get command-line arguments



def run_sim(params):
    cell_id,freq,var,data_dir=params
    try:
        print(f"Running simulation for cell_id={cell_id}, freq={freq}")
        run_threshold(cell_id,freq,var,data_dir)
        print(f"Simulation completed for cell_id={cell_id}, freq={freq}")

    except Exception as e:
        print(f"Error during simulation for freq={freq}, cell={cell_id}: {e}")
    finally:
        h("forall delete_section()")  # Cleanup NEURON sections
        gc.collect()  # Force garbage collection



if __name__ == "__main__":
    # Parse arguments
    args = parser.parse_args()
    freqs = args.freq
    cell_ids = args.id  

    var="cfreq"
    data_dir=os.getcwd()


    if args.batch:
        # Generate all combinations of (freq, amp)
        param_combinations = list(product(cell_ids,freqs))

        # # Add modfreq and depth to each combination
        params=[(cell_id,freq,var,data_dir) for cell_id, freq in param_combinations]

         # Use multiprocessing
        maxnum_processes = cpu_count()  # Use all available cores
        num_processes=len(params)

        if num_processes>maxnum_processes:
            raise ValueError("Trying to run too many processes at once")
        with Pool(processes=num_processes) as pool:
            pool.map(run_sim, params)
    else:
        # Run a single simulation
        if len(freqs) > 1 or len(cell_ids) > 1:
            raise ValueError("Batch mode (--batch) must be enabled for multiple frequencies/voltages.")

        # Extract single values for freq and amp
        freq = freqs[0]
        cell_id = cell_ids[0]

        run_sim(cell_id,freq,var,data_dir)