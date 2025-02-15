import numpy as np
import os
import gc
from neuron import h
import pandas as pd
import matplotlib.pyplot as plt
import h5py
import json

# Get the directory of the current scripts
script_dir = os.path.dirname(os.path.abspath(__file__))
# Change the working directory to the script's directory
os.chdir(script_dir)

import savedata as savedata


# print("wassup")
print(os.getcwd())

def get_voltages(cell_id,freq,var,data_dir=os.getcwd()):
    folder=os.path.join(data_dir,"data",str(cell_id),str(var),"threshold",f"{int(freq)}Hz")
    path=os.path.join(os.getcwd(),folder)
    file=os.path.join(path,"run_voltages.csv")
    print(file)
    voltages=pd.read_csv(file)
    return voltages,folder

def get_voltages_hdf5(cell_id,freq,var,data_dir=os.getcwd()):
    folder=os.path.join(data_dir,"data",str(cell_id),str(var),"threshold",f"{int(freq)}Hz")
    filepath=os.path.join(folder,"run_voltages.h5")
    with h5py.File(filepath, 'r') as file:
        # Access datasets
        time = file["time"][:]
        is_xtra = file["is_xtra"][:]
        voltages = file["voltages"][:]
        
        # Read segment names from attributes
        segment_names = file["voltages"].attrs["segment_names"]
    return voltages, time, is_xtra, segment_names,folder

def get_threshold(freq,cell_id,var,data_dir):
    folder=os.path.join(data_dir,"data",str(cell_id),str(var),"threshold")
    file=os.path.join(folder,"thresholds.csv")
    thresholds=pd.read_csv(file)
    threshold=thresholds[thresholds["cfreq"]==int(freq)]["Threshold"].to_list()
    return threshold

def get_maxv(cell_id,freq,var,hdf5=True,data_dir=os.getcwd()):
    if not hdf5:
        voltages,folder=get_voltages(cell_id,freq,var)
        max_v = voltages.iloc[:, 2:].max().tolist()  # Returns a list of maximum values per segment
        headers=voltages.drop(columns=["t","is_xtra"]).columns.to_list()
        # Find the segment with the highest maximum voltage
        max_segment_idx = np.argmax(max_v)
        max_segment = headers[max_segment_idx]
        
        fig,ax=plt.subplots()
        time=voltages.iloc[:,0].to_list()
        is_xtra=voltages["is_xtra"].to_list()
        # Plot only the segment with the highest maximum voltage

        ax.plot(time, voltages[max_segment], label=max_segment)
    else:
        voltages, time, is_xtra, segment_names,folder= get_voltages_hdf5(cell_id,freq,var,data_dir)
        max_v = voltages.max(axis=0)

        # Find the segment with the highest maximum voltage
        max_segment_idx = np.argmax(max_v)
        max_segment = segment_names[max_segment_idx]

        fig,ax=plt.subplots()

        # Plot only the segment with the highest maximum voltage
        ax.plot(time, voltages[:, max_segment_idx], label=max_segment)

    threshold=get_threshold(freq,cell_id,var,data_dir)
    print(threshold)
    # threshold=1656.25
    print(max_v)

    # ax.plot(time,is_xtra,label="is_xtra")
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Membrane Potential (mV)")
    ax.legend()
    title=f"Membrane potential for highest V {max_segment}"    
    ax.set_title(title)

    savedata.saveplot(folder,title,fig)
    
    fig1,ax1=plt.subplots()
    ax1.plot(time,is_xtra)
    ax1.set_xlabel("Time (ms)")
    ax1.set_ylabel("Stimulation (V/m)")
    title1="Stimulation_Vm"
    ax1.set_title(title1)
    

    savedata.saveplot(folder,title1,fig1)
    plt.close()
    return max_v



# max_v=get_maxv(cell_id,freq,var)

def plot_voltage_highest_spiken(cell_id,freq,var,hdf5=True,data_dir=os.getcwd(),save=False):
    if not hdf5:
        voltages,folder=get_voltages(cell_id,freq,var)
        max_v = voltages.iloc[:, 2:].max().tolist()  # Returns a list of maximum values per segment
        headers=voltages.drop(columns=["t","is_xtra"]).columns.to_list()
        fig,ax=plt.subplots()
        time=voltages.iloc[:,0].to_list()
        is_xtra=voltages["is_xtra"].to_list()
        for val in headers:
            v=voltages[val].to_list()
            ax.plot(time,v,label=val)
    else:
        voltages, time, is_xtra, segment_names,folder= get_voltages_hdf5(cell_id,freq,var,data_dir)
        max_v = voltages.max(axis=0)
        data=load_apcs(folder)
        max_segment,max_value=get_max_spike_count(data)
        # print(f"Segment with max spikes: {max_segment} ({max_value} spikes)")

        # Locate the index of the max_segment using NumPy
        max_segment_index = np.where(segment_names == max_segment)[0]

        # Ensure the segment exists
        if len(max_segment_index) == 0:
            raise ValueError(f"Segment {max_segment} not found in segment_names")
        
        v_max=voltages[:, max_segment_index]
        fig,ax=plt.subplots()
        ax.plot(time,v_max,label=f"{max_segment}")
        ax.set_xlabel("Time (ms)")
        ax.set_ylabel("Membrane Potential (mV)")
        ax.legend()
        threshold=get_threshold(freq,cell_id,var,data_dir)
        print(threshold)
        title=f"Membrane potential for highest spiken segment {max_segment}"
        ax.set_title(title)
        if save:
            savedata.saveplot(folder,title,fig)
        plt.close()
        return v_max,time,max_segment

def load_apcs(folder):
    spike_file=os.path.join(folder,"spikes_data.json")
    with open(spike_file,'r') as file:
        data = json.load(file)
    return data

def get_max_spike_count(data):
    """Get the segment with the maximum spike count."""
    # Find the segment with the maximum value in the data dictionary
    max_segment = max(data, key=data.get)  # `key=data.get` ensures we're comparing the values
    max_value = data[str(max_segment)]  # This retrieves the spike count for that segment

    return max_segment, max_value

# cell_id=1
# freq=100
# var="cfreq"
# v,time=plot_voltage_highest_spiken(cell_id,freq,var,hdf5=True,save=True)

# # filtered=low_pass.butter_bandpass_filter(v,dt=0.001)
# from functions.csv_max_minshift import get_folder,load_voltages_hdf5
# def plot_difference_threshnorm(cell_id,freq,var,amp,hdf5=True,save=True,data_dir=os.getcwd()):   
#     v_max,time,max_segment= plot_voltage_highest_spiken(cell_id,freq,var,hdf5,data_dir,save=False) 
#     top_dir, bot_dir, param_dir=get_folder(freq,amp,cell_id,var,data_dir=data_dir)
#     voltages=load_voltages_hdf5(bot_dir,filtered=False)
#     threshold=get_threshold(freq,cell_id,var,data_dir)
#     folder=os.path.join(data_dir,"data",str(cell_id),str(var),"threshold",f"{freq}Hz")

#     v=voltages[max_segment].to_list()
#     print(v)
#     fig,ax=plt.subplots()
#     ax.plot(time,v_max,label="From threshold",alpha=0.5)
#     # ax.plot(time,v,label="From normal run",alpha=0.5)
#     ax.set_xlabel("Time (ms)")
#     ax.set_ylabel("Membrane Potential (mV)")
#     ax.legend()
#     title=f"Membrane potential for E={threshold[-1]} V_m vs E={amp}"

#     if save:
#          savedata.saveplot(folder,title,fig)
#     else:
#         plt.show()

# amp=70
# plot_difference_threshnorm(cell_id,freq,var,amp,hdf5=True,save=False,data_dir=os.getcwd())