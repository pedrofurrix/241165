import os
# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Change the working directory to the script's directory
os.chdir(script_dir)

from init_stim import run_simulation,save_plots

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

e_dir,t, is_xtra,vrec,soma_v,dend_v,axon_v,cell=run_simulation(cell_id, theta, phi, simtime, dt, amp, depth, freq, modfreq,ton,dur,run_id)

save_plots(e_dir,t,is_xtra,vrec,soma_v,dend_v,axon_v)