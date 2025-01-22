import os

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Change the working directory to the script's directory
os.chdir(script_dir)
from csv_max_minshift import get_folder
CF=2000
E=100
cell_id=1
var="cfreq"
# data_dir="/media/sf_Data"
data_dir=os.getcwd()

top_dir,bot_dir,param_dir=get_folder(CF,E,cell_id,var=var,data_dir=data_dir)

from init_steady import run_threshold
cell_id=1
theta = 180
phi = 0
simtime = 2000
dt = 0.1
amp = 0
depth = 1
freq =2000
modfreq = 10
ton = 0
dur = simtime
run_id = 0
ramp=True
ramp_duration=400
tau=0


run_threshold(run_id,cell_id,theta,phi,simtime,dt,ton,amp,depth,dur,freq,modfreq,top_dir,var="cfreq",ramp=ramp,ramp_duration=ramp_duration,tau=tau,data_dir=data_dir)