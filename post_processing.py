import numpy as np
import os
import time
from tqdm import tqdm
import gc 
import sys

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Change the working directory to the script's directory
os.chdir(script_dir)

save_out=sys.stdout


import filter_and_max as filter_and_max
import process_results as process_results
import test_filters as test_filters
import spike_detector as spike_detector
start=time.time()

CF=[2000,10000,30000]
E=[1,5,100]
cell_id=1
modfreq=10
dt=0.001
var="cfreq"
filter=False
data_dir="/media/sf_Data"

pathf=os.path.join(data_dir,"data",str(cell_id),str(var))
if not os.path.exists(pathf):
      os.makedirs(pathf)
path=os.path.join(pathf,'processing.log')
log_file = open(path, 'a')  # Use 'w' to overwrite or 'a' to append
sys.stdout = log_file
sys.stderr = log_file
order=4
highcut=None
target_fs=1000
for freq in CF:
      for e in tqdm(E):
            try:
#                   # Load data
                  top_dir, bot_dir, param_dir = filter_and_max.get_folder(freq, e, cell_id, var, filtered=filter, data_dir=data_dir)
                  t, voltages, segment_names = filter_and_max.load_voltages_hdf5(param_dir)
                  
#                   # # Before processing - Choose filter order
                  test_filters.test_filters(freq, e, cell_id, var="cfreq", data_dir=data_dir, voltages=voltages, 
                                          time=t, segment_names=segment_names,target_fs=target_fs,order_bp=3)
                  test_filters.test_subsample(freq,e,cell_id,var=var,data_dir=data_dir,voltages=voltages,
                        time=t,segment_names=segment_names, filtered=filter,detrend=False,target_fs=target_fs,
                        modfreq=modfreq,cutoff=200,highcut=None,lowcut=None,order_low=3,order_bp=3)
#                   # any_spikes = spike_detector.spike_detector(bot_dir, param_dir, filtered=filter, threshold=0)
    
#                   # if any_spikes:
#                   #       print("Spikes detected! Make sure to manually remove the spikes from the dataset.")
#                   # Uncomment if you want to run the commented parts in your loop
#                   max_shift, max_v, min_v, results = filter_and_max.analyze_shifts(
#                       freq, e, cell_id, var, data_dir, voltages, t, segment_names, 
#                       filtered=filter, highcut=highcut, order=order, modfreq=modfreq
#                   )
#                   max_shift, max_v, min_v, results = filter_and_max.analyze_shifts(
#                       freq, e, cell_id, var, data_dir, voltages, t, segment_names, 
#                       filtered=True, highcut=highcut, order=order, modfreq=modfreq
#                   )
#                   summary = filter_and_max.analyze_fourier_power(
#                       freq, e, cell_id, var, filtered=filter, data_dir=data_dir,
#                       voltages=voltages, segment_names=segment_names, dt=dt, modfreq=modfreq
#                   )
            finally:
#                   # Delete all large variables to free memory
                  del top_dir, bot_dir, param_dir
                  del t, voltages, segment_names
#                   del max_shift,max_v,min_v,results
#                   del summary
#                   gc.collect()  # Force garbage collection to release memory




# import functions.process_results as pr
# summary_dfp,summary_dfn,top_dir=pr.load_results(cell_id,var=var,filtered=filter,data_dir=data_dir)
# pr.plot_results(cell_id,summary_dfp,title="Max Depolarization",top_dir=top_dir,var=var,filtered=filter,pos=True,data_dir=data_dir)
# pr.plot_results(cell_id,summary_dfn,title="Max Hyperpolarization",top_dir=top_dir,var=var,filtered=filter,pos=False,data_dir=data_dir)
# summary_dfp_filtered,summary_dfn_filtered,top_dir=pr.load_results(cell_id,var=var,filtered=True)
# pr.plot_results(cell_id,summary_dfp_filtered,title="Max Depolarization",top_dir=top_dir,var=var,filtered=True,pos=True,data_dir=data_dir)
# pr.plot_results(cell_id,summary_dfn_filtered,title="Max Hyperpolarization",top_dir=top_dir,var=var,filtered=True,pos=False,data_dir=data_dir)

# summary_df, summary_norm,top_dir=pr.load_fourier_power(cell_id,var,norm=False,data_dir=data_dir)
# pr.plot_fourier_power(cell_id,summary_df,summary_norm,title="Fourier Power",top_dir=top_dir,var="cfreq",evalue_threshold=None,norm=False,data_dir=data_dir)


# from functions.check_maxpseg import check_segs
# check_segs(cell_id,var,filtered=filter)

# end=time.time()
# print(f"Time passed:{end-start} seconds")
sys.stdout=save_out

