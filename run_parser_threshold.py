import os
import time
import sys
from argparse import ArgumentParser


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


args = parser.parse_args()

from filter_and_max import get_folder
from init_threshold import threshold
from debug_thresholds import get_maxv,plot_voltage_highest_spiken

def run_threshold(cell_id,freq,var,data_dir):
    start=time.time()
   
    init_amp = 100
    top_dir,bot_dir,param_dir=get_folder(freq,init_amp,cell_id,var=var,filtered=False,data_dir=data_dir)
    

    pathf=os.path.join(data_dir,"data",str(cell_id),str(var),"threshold",f"{int(freq)}Hz")
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

# Get command-line arguments
freq = args.freq
cell_id = args.id

var="cfreq"
data_dir=os.getcwd()

run_threshold(cell_id,freq,var,data_dir)

hdf5=True
max_v=get_maxv(cell_id,freq,var,hdf5,data_dir)
v_max,t,max_segment=plot_voltage_highest_spiken(cell_id,freq,var,hdf5,data_dir,save=True)