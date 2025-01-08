import os
from neuron import h
import csv


def record_voltages(cell,e_dir):

    path=os.path.join(e_dir,f"run_voltages.csv")
    file= open(path,'w',newline='')
    writer = csv.writer(file)
    # Write header row with time and segment indexes
    # header = ["t"] + [f"{sec.name()}({i})" for sec in cell.all for i, _ in enumerate(sec)]
    header= ["t"] + [f"{seg}" for sec in cell.all for seg in sec]
    writer.writerow(header)

    def sum_voltages():
        current_voltages = [h.t] + [seg.v for sec in cell.all for seg in sec]
        writer.writerow(current_voltages) # Use writerow for single list
            
    callback=h.beforestep_callback(cell.soma[0](0.5))
    callback.set_callback(sum_voltages)

    return file,callback

def custom_threshold(cell,cell_id,freq,segments,var):
    currdir=os.getcwd()
    print(currdir)
    folder=f"data\\{cell_id}\\{var}\\threshold\\{freq}Hz"
    path=os.path.join(currdir,folder)
    print(path)
    
    if not os.path.exists(path):
        os.makedirs(path)

    filepath=os.path.join(path,f"run_voltages.csv")
    file= open(filepath,'w',newline='')
    writer = csv.writer(file)
    # Write header row with time and segment indexes
    # header = ["t"] + [f"{sec.name()}({i})" for sec in cell.all for i, _ in enumerate(sec)]
    header= ["t"] + ["is_xtra"] + [f"{seg}" for seg in segments]
    writer.writerow(header)
   
    def sum_voltages():
        current_voltages = [h.t] + [h.is_xtra] + [seg.v for seg in segments]
        writer.writerow(current_voltages) # Use writerow for single list
        # global max_v
        # for seg in segments:
        #     if seg.v>max_v:
        #         max_v=seg.v
        
    callback=h.beforestep_callback(cell.soma[0](0.5))
    callback.set_callback(sum_voltages)

    return file,callback