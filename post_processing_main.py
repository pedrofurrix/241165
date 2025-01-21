
import os

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Change the working directory to the script's directory
os.chdir(script_dir)
import csv_max_minshift

from maxshift_plot import plot_maxshift
from spike_detector import spike_detector

data_dir="/media/sf_Data"

CF=2000
E=[10,20,30,50,100,150,200,300,400,500,700,1000]
cell_id=1
var="cfreq"
filter=False
for e in E:
    top_dir,bot_dir,param_dir=csv_max_minshift.get_folder(CF,e,cell_id,data_dir,var,filtered=filter)

    max_shift, max_v, min_v, results=csv_max_minshift.cmax_shift(bot_dir,top_dir,param_dir,var, filtered=filter)

    csv_max_minshift.plot_voltage(bot_dir,results)



    fig=plot_maxshift(bot_dir,filename="max_shift",cell=None,max_shift=max_shift)



    threshold=0
    spike_detector(bot_dir,param_dir,data_dir,threshold)

from check_maxpseg import check_segs

check_segs(cell_id,var,data_dir,filtered=filter)