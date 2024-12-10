import csv_max_minshift

CF=500
E=1000
cell_id=1

top_dir,bot_dir=max_minshift.get_folder(CF,E,cell_id)

max_shift, max_v, min_v, results=max_minshift.cmax_shift(bot_dir,top_dir, cell=None)

max_minshift.plot_voltage(bot_dir,results)

from maxshift_plot import plot_maxshift

# fig=plot_maxshift(bot_dir,filename="max_shift",cell=None,max_shift=max_shift)