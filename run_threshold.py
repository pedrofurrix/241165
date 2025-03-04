import os
import time
import sys
# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Change the working directory to the script's directory
os.chdir(script_dir)

from init_stim import run_simulation,save_plots

from filter_and_max import get_folder
nc=True
if not nc:
    from init_threshold import threshold
else:
    from init_threshold_ncs import threshold


from debug_thresholds import get_maxv,plot_voltage_highest_spiken

save_out=sys.stdout

def run_threshold(cell_id,freq,var,data_dir):
    start=time.time()
    #Parameters to change
    # freq = 2000
    
    # # Fixed parameters
    # pathf=os.path.join(data_dir,"data",str(cell_id),str(var),"threshold",f"{int(freq)}Hz")
    # if not os.path.exists(pathf):
    #     os.makedirs(pathf)
    # path=os.path.join(pathf,'output.log')
    # log_file = open(path, 'a')  # Use 'w' to overwrite or 'a' to append
    # sys.stdout = log_file
    # sys.stderr = log_file

    amp=100
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
    record_all=False
    ufield=True
    coordinates=[0,0,0]
    rho=0.276e-6
    threshold(cell_id, theta, phi, simtime, dt, amp, depth, freq, modfreq,ton,dur,
              thresh=thresh,cb=cb,var=var,ramp=ramp,ramp_duration=ramp_duration,tau=tau,data_dir=data_dir,
              record_all=record_all,ufield=ufield,coordinates=coordinates,rho=rho)
    sys.stdout=save_out
    end=time.time()
    print(f"The time of execution of above program is : {end-start} s")
    print(f"The time of execution of above program is : {(end-start)/60} mins")

cell_id=1
freq=2000
var="cfreq"
data_dir=os.getcwd()
run_threshold(cell_id,freq,var,data_dir)

hdf5=True
max_v=get_maxv(cell_id,freq,var,hdf5,data_dir)
v_max,t,max_segment=plot_voltage_highest_spiken(cell_id,freq,var,hdf5,data_dir,save=True)
