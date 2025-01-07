
import os

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Change the working directory to the script's directory
os.chdir(script_dir)
import csv_max_minshift


CF=500
E=1000
cell_id=1

top_dir,bot_dir=csv_max_minshift.get_folder(CF,E,cell_id)

# max_shift, max_v, min_v, results=csv_max_minshift.cmax_shift(bot_dir,top_dir)

# csv_max_minshift.plot_voltage(bot_dir,results)

# from maxshift_plot import plot_maxshift

# fig=plot_maxshift(bot_dir,filename="max_shift",cell=None,max_shift=max_shift)


from spike_detector import spike_detector
threshold=0
spike_detector(bot_dir,threshold)
