import os
import time
# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Change the working directory to the script's directory
os.chdir(script_dir)

from init_stim import run_simulation,save_plots
start=time.time()

#Parameters to change
freq = 500
amp = 50

# Fixed parameters
var="cfreq"
cell_id=1
theta = 180
phi = 0
simtime = 1000
dt = 0.001
depth = 1
modfreq = 10
ton = 0
dur = simtime
run_id = 0
cb=True
ramp=True
ramp_duration=400
tau=0
data_dir="/media/sf_Data"
e_dir,t, is_xtra,vrec,soma_v,dend_v,axon_v,cell=run_simulation(cell_id, theta, phi, simtime, dt, amp, depth, freq, modfreq,
                                                               ton,dur,run_id,cb,var,ramp,ramp_duration,tau,data_dir)

save_plots(e_dir,t,is_xtra,vrec,soma_v,dend_v,axon_v)

end=time.time()
print(f"The time of execution of above program is : {end-start} s")
print(f"The time of execution of above program is : {(end-start)/60} mins")