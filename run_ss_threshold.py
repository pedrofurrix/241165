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
from init_steady import run_threshold

cell_id=1
theta = 180 
phi = 0 
simtime = 30000
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
threshold=1e-7
nc=True
record_all=False
ufield=True
coordinates=[0,0,0]
rho=0.276e-6
time_before=1000

run_threshold(run_id,cell_id,theta,phi,simtime,dt,ton,amp,depth,dur,freq,modfreq,var=var,ramp=ramp,ramp_duration=ramp_duration,tau=tau,
              data_dir=data_dir,threshold=threshold,nc=nc,record_all=record_all,ufield=ufield,coordinates=coordinates,rho=rho,time_before=time_before)