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
parser.add_argument("-f", "--freq", type=float, nargs="*", required=False,default=[2000], help="Frequencies (Hz) for the simulations")
parser.add_argument("-v", "--voltage", type=float, nargs="*", required=False,default=[100], help="Voltages (mV) for the simulations")
parser.add_argument("-d", "--depth", type=float, nargs="*", required=False,  default=[1.0], help="Modulation depth (0-1)")
parser.add_argument("-m", "--modfreq", type=float, nargs="*", required=False,  default=[10], help="Modulation Frequency (Hz)")
parser.add_argument("-t", "--theta", type=float, nargs="*", required=False,  default=[180], help="Polar Angle Theta (0-180) degrees")
parser.add_argument("-p", "--phi", type=float, nargs="*", required=False,  default=[0], help="Azimuthal Angle Phi (0-360) degrees")
parser.add_argument("-c", "--id", type=int, required=False,default=1, help="Cell id")
parser.add_argument("-b","--batch", action="store_true", help="Enable batch processing mode")

from filter_and_max import get_folder

nc=True
if not nc:
    from init_threshold import threshold
else:
    from init_threshold_ncs import threshold

# from debug_thresholds import get_maxv,plot_voltage_highest_spiken

def run_threshold(params):
    freq, amp, modfreq, depth,theta,phi,cell_id,var,data_dir = params
    start=time.time()
   
    init_amp = amp    
    
    simtime = 1000
    dt = 0.001
    ton = 0
    dur = simtime
    cb=False
    ramp=True
    ramp_duration=400
    tau=0
    thresh=20

    ufield=True
    coordinates=[0,0,0]
    rho=100
    record_all=False
    threshold(cell_id, theta, phi, simtime, dt, init_amp, depth, freq, modfreq,ton,dur,
              thresh=thresh,cb=cb,var=var,ramp=ramp,ramp_duration=ramp_duration,tau=tau,data_dir=data_dir,ufield=ufield,coordinates=coordinates,rho=rho,record_all=record_all)
    
    end=time.time()
    print(f"The time of execution of above program is : {end-start} s")
    print(f"The time of execution of above program is : {(end-start)/60} mins")
    hdf5=True
    # max_v=get_maxv(cell_id,freq,var,hdf5,data_dir)
    # v_max,t,max_segment=plot_voltage_highest_spiken(cell_id,freq,var,hdf5,data_dir,save=True)

# Get command-line arguments



def run_sim(params):
    try:
        print(f"Running simulation for cell_id={cell_id}, freq={freq}")
        run_threshold(params)
        print(f"Simulation completed for cell_id={cell_id}, freq={freq}")

    except Exception as e:
        print(f"Error during simulation for freq={freq}, cell={cell_id}: {e}")
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
    thetas = args.theta
    phis = args.phi
    cell_id=args.id  

    var="cfreq"
    data_dir=os.getcwd()


    if args.batch:
        # Generate all combinations of (freq, amp)
        param_combinations = list(product(freqs, amps,modfreqs,depths,thetas,phis))

        # # Add modfreq and depth to each combination
        params = [(freq, amp, modfreq, depth,theta,phi,cell_id,var,data_dir) for freq, amp,modfreq,depth,theta,phi in param_combinations]
    
         # Use multiprocessing
        maxnum_processes = cpu_count()  # Use all available cores
        num_processes=len(params)

        if num_processes>maxnum_processes:
            raise ValueError("Trying to run too many processes at once")
        with Pool(processes=num_processes) as pool:
            pool.map(run_sim, params)
    else:
        # Run a single simulation
        if len(freqs) > 1 or  len(amps)> 1 or len(modfreqs)>1 or len(depths)>1 or len(thetas)>1 or len(phis)>1:
            raise ValueError("Batch mode (--batch) must be enabled for multiple frequencies/voltages.")

        # Extract single values for freq and amp
        freq = freqs[0]
        amp = amps[0]
        modfreq = modfreqs[0]
        depth = depths[0]
        theta = thetas[0]
        phi = phis[0]
        params=(freq,amp,modfreq,depth,theta,phi,cell_id,var,data_dir)
        run_sim(params)