import os
# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Change the working directory to the script's directory
os.chdir(script_dir)

from init_steady import run_steady
cell_id=1
theta = 180
phi = 0
simtime = 1100
dt = 0.1
amp = 0
depth = 1
freq = 0
modfreq = 0
ton = 0
dur = simtime
run_id = 0
ramp=True
ramp_duration=400
tau=0
data_dir=os.getcwd()
variation=1e-3
ufield=False
coordinates=[0,0,0]
rho=0.276e-6
time_before=20

run_steady(run_id,cell_id,theta,phi,simtime,dt,ton,amp,depth,dur,freq,modfreq,ramp,ramp_duration,tau,data_dir,
           threshold=variation,ufield=ufield,coordinates=coordinates,rho=rho,time_before=time_before)