import os
# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Change the working directory to the script's directory
os.chdir(script_dir)

from init_steady import run_steady
cell_id=1
theta = 180
phi = 0
simtime = 1000
dt = 0.1
amp = 0
depth = 1
freq = 0
modfreq = 0
ton = 0
dur = simtime
run_id = 0

run_steady(run_id,cell_id,theta,phi,simtime,dt,ton,amp,depth,dur,freq,modfreq)