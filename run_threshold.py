import os
import time
import sys
# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Change the working directory to the script's directory
os.chdir(script_dir)

from init_stim import run_simulation,save_plots

from csv_max_minshift import get_folder
from init_threshold import threshold

save_out=sys.stdout

def run_threshold(cell_id,freq,var):
    start=time.time()
    #Parameters to change
    # freq = 2000
    amp = 100
    data_dir=os.getcwd()
    # var="cfreq"
    top_dir,bot_dir,param_dir=get_folder(freq,amp,cell_id,var=var,filtered=False,data_dir=data_dir)
    # Fixed parameters
    pathf=os.path.join(data_dir,"data",str(cell_id),str(var),"threshold",f"{freq}Hz")
    if not os.path.exists(pathf):
        os.makedirs(pathf)
    path=os.path.join(pathf,'output.log')
    log_file = open(path, 'a')  # Use 'w' to overwrite or 'a' to append
    sys.stdout = log_file
    sys.stderr = log_file
    
    theta = 180
    phi = 0
    simtime = 1000
    dt = 0.01
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
    threshold(cell_id, theta, phi, simtime, dt, amp, depth, freq, modfreq,ton,dur,top_dir,
              thresh=thresh,cb=cb,var=var,ramp=ramp,ramp_duration=ramp_duration,tau=tau,data_dir=data_dir)
    sys.stdout=save_out
    end=time.time()
    print(f"The time of execution of above program is : {end-start} s")
    print(f"The time of execution of above program is : {(end-start)/60} mins")


run_threshold(1,200,"cfreq")

