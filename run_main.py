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
simtime = 100
dt = 0.001
depth = 1
modfreq = 100
ton = 0
dur = simtime
run_id = 0
cb=True
e_dir,t, is_xtra,vrec,soma_v,dend_v,axon_v,cell=run_simulation(cell_id, theta, phi, simtime, dt, amp, depth, freq, modfreq,ton,dur,run_id,cb,var)

save_plots(e_dir,t,is_xtra,vrec,soma_v,dend_v,axon_v)

end=time.time()
print(f"The time of execution of above program is : {end-start} s")
print(f"The time of execution of above program is : {(end-start)/60} mins")