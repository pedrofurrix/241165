from neuron import h
import numpy as np
import csv
import pandas as pd
import os
import matplotlib.pyplot as plt
import plotly
import matplotlib.colors as mcolors
from matplotlib import cm
import plotly.graph_objects as go
import pickle
import json
import h5py




def load_voltages_csv(bot_dir):
    '''
    Loads voltages file - from the Electric field folder
    '''
    
    vfile=os.path.join(bot_dir,"run_voltages.csv")
    voltages=pd.read_csv(vfile)
    return voltages

def load_voltages_hdf5(bot_dir,filtered=False):
    """
    
    Load voltage data from HDF5 file.

    """
    if not filtered:
        vfile = os.path.join(bot_dir, "run_voltages.h5")
        with h5py.File(vfile, "r") as file:
            # Read time and voltages
            time = file["time"][:]
            voltages = file["voltages"][:]
            segment_names = file["voltages"].attrs["segment_names"]

    else:
        vfile=os.path.join(bot_dir,"filtered_voltages.h5")
        with h5py.File(vfile, "r") as file:
            # Read time and voltages
            time = file["time"][:]
            voltages = file["filtered_voltages"][:]
            segment_names = file["filtered_voltages"].attrs["segment_names"]
    
    # Create a DataFrame for easier handling
    df = pd.DataFrame(voltages, columns=segment_names)
    df.insert(0, "t", time)  # Add time as the first column
    return df


def load_params(param_dir): #Load paramsssssssss (get them into a format where I can easily extract them.., ) - json
    '''
    Loads parameters - from json
    '''
    filename="params.json"
    path = os.path.join(param_dir, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"The parameters file does not exist at {path}")
    # Load the JSON file
    with open(path, "r") as file:
        params = json.load(file)
    # Extract simulation and stimulation parameters
    simparams = params["Simulation Parameters"]
    stimparams = params["Stimulation Parameters"]
    # Return the parameters
    return simparams, stimparams


def cmax_shift(bot_dir,top_dir,param_dir,var,cell=None, filtered=False):
    # voltages=load_voltages_csv(bot_dir)
    voltages=load_voltages_hdf5(bot_dir,filtered)
    headers=voltages.drop(columns=["t"]).columns.to_list()
    simparams, stimparams=load_params(param_dir)

    num_seg=len(voltages.iloc[0,1:]) #iterate through all but the column that has the time
    v_init=voltages.iloc[0,1:].to_list()

    if cell:
        segments = [seg for sec in cell.all for seg in sec]
    else:
        segments = range(num_seg)

    # Excludes the "t" column, calculates the maximum and minimum for each column (segment)
    max_v = voltages.iloc[:, 1:].max().tolist()  # Returns a list of maximum values per segment
    min_v = voltages.iloc[:, 1:].min().tolist()  # Returns a list of minimum values per segment
    pshift = [max_v[i] - v_init[i] for i in range(len(segments))]
    nshift = [min_v[i] - v_init[i] for i in range(len(segments))]
    max_shift = [max(p, n, key=abs) for p, n in zip(pshift, nshift)]
    
     
    results = {
        "EValue": stimparams["E"],
        "CFreq": stimparams["Carrier Frequency"],
        "ModFreq": stimparams["Modulation Frequency"],
        "max_shiftp": max(pshift),
        "min_shiftp": min(pshift),
        "max_shiftn": max(nshift, key=abs),
        "min_shiftn": min(nshift, key=abs),
        "maxp_index": pshift.index(max(pshift)),
        "minp_index": pshift.index(min(pshift)),
        "maxn_index": nshift.index(max(nshift, key=abs)),
        "minn_index": nshift.index(min(nshift, key=abs)),
        "maxp_seg": headers[pshift.index(max(pshift))],
        "minp_seg": headers[pshift.index(min(pshift))],
        "maxn_seg": headers[nshift.index(max(nshift, key=abs))],
        "minn_seg": headers[nshift.index(min(nshift, key=abs))]
    }

    if cell:
        results["maxp_seg"]=segments[results["maxp_index"]]
        results["minp_seg"]=segments[results["minp_index"]]
        results["maxn_seg"]=segments[results["maxn_index"]]
        results["minn_seg"]=segments[results["minn_index"]]
        results["maxp_sec"]=results["maxp_seg"].sec
        results["minp_sec"]=results["minp_seg"].sec
        results["maxn_sec"]=results["maxn_seg"].sec
        results["minn_sec"]=results["minn_seg"].sec

    # Save the results obtained into files.
    def save_max():
        data={
            "seg" : headers,
            "max_v" : max_v,
            "min_v" : min_v,
            "max_shift" : max_shift,
            "pshift" : pshift,
            "nshift" : nshift
        }
        # Save the data
        out_file=os.path.join(bot_dir,"max_shift_data.csv")
        data_pd=pd.DataFrame([data])
        data_pd.to_csv(out_file,index=False)

        if filtered:
            top_file=os.path.join(top_dir, "results_summary_filtered.csv")
            results_df = pd.DataFrame([results])
        else:
            top_file=os.path.join(top_dir, "results_summary.csv")
            results_df = pd.DataFrame([results])

        if os.path.exists(top_file):
            # If file exists, append the new results without writing the header
            results_df.to_csv(top_file, mode='a', index=False, header=False)
        else:
            # If file does not exist, write the results with the header
            results_df.to_csv(top_file, index=False, header=True)
        
    save_max()

    return max_shift, max_v, min_v, results

def plot_show(bot_dir,results):
    voltages=load_voltages_hdf5(bot_dir)

    t=voltages["t"]
    v_maxp_index=results["maxp_index"]
    v_maxn_index=results["maxn_index"]
    vmaxp=voltages.iloc[:,v_maxp_index+1]
    vmaxn=voltages.iloc[:,v_maxn_index+1]
    segmaxp=results["maxp_seg"]
    segmaxn=results["maxn_seg"]

    # Plot Max both
    fig3,ax3=plt.subplots()
    title3=("Membrane potential over time - Maxshift")
    ax3.plot(t, vmaxp,label=f"maxp_shift_{segmaxp}")
    ax3.plot(t, vmaxn,label=f"maxn_shift_{segmaxn}")
    ax3.set_xlabel("time (ms)")  # Correct method to set labels
    ax3.set_ylabel("Membrane potential (mV)")
    ax3.legend()
    ax3.set_title(title3)  # Optional: add title to the plot
    return fig3

def plot_voltage(bot_dir,results,filtered=False):
    voltages=load_voltages_hdf5(bot_dir,filtered)

    t=voltages["t"]

    # Plot Max positive
    v_max_index=results["maxp_index"]
    v_min_index=results["minp_index"]
    vmaxp=voltages.iloc[:,v_max_index+1]
    vminp=voltages.iloc[:,v_min_index+1]

    segmaxp=results["maxp_seg"]
    segminp=results["minp_seg"]

    
    fig,ax=plt.subplots()
    title1=("Membrane potential over time - Pshift")
    ax.plot(t, vmaxp,label=f"maxp_shift_{segmaxp}")
    ax.plot(t, vminp,label=f"minp_shift_{segminp}")
    ax.set_xlabel("time (ms)")  # Correct method to set labels
    ax.set_ylabel("Membrane potential (mV)")
    ax.legend()
    ax.set_title(title1)  # Optional: add title to the plot
    # plt.show()

    #Plot Max Negative

    v_max_index=results["maxn_index"]
    v_min_index=results["minn_index"]
    vmaxn=voltages.iloc[:,v_max_index+1]
    vminn=voltages.iloc[:,v_min_index+1]
    
    segmaxn=results["maxn_seg"]
    segminn=results["minn_seg"]
    fig2,ax2=plt.subplots()
    title2=("Membrane potential over time - Nshift")
    ax2.plot(t, vmaxn,label=f"maxn_shift_{segmaxn}")
    ax2.plot(t, vminn,label=f"minn_shift_{segminn}")
    ax2.set_xlabel("time (ms)")  # Correct method to set labels
    ax2.set_ylabel("Membrane potential (mV)")
    ax2.legend()
    ax2.set_title(title2)  # Optional: add title to the plot
    # plt.show()
    
    # Plot Max both
    fig3,ax3=plt.subplots()
    title3=("Membrane potential over time - Maxshift")
    ax3.plot(t, vmaxp,label=f"maxp_shift_{segmaxp}")
    ax3.plot(t, vmaxn,label=f"maxn_shift_{segmaxn}")
    ax3.set_xlabel("time (ms)")  # Correct method to set labels
    ax3.set_ylabel("Membrane potential (mV)")
    ax3.legend()
    ax3.set_title(title3)  # Optional: add title to the plot

    def saveplot(bot_dir,title,fig_or_ax):
        filename=f"{title}.png"

        if isinstance(fig_or_ax, plt.Axes):
            # If it's an Axes object, get the Figure from the Axes
            fig = fig_or_ax.get_figure()
        elif isinstance(fig_or_ax, plt.Figure):
            # If it's already a Figure, use it as is
            fig = fig_or_ax
        else:
            raise TypeError("Input must be a matplotlib Figure or Axes object.")
        
        path=os.path.join(bot_dir,filename)
        
        fig.savefig(path, dpi=300, bbox_inches='tight')

        print(f"Successfully saved as {filename}")

    saveplot(bot_dir,title1,fig)
    saveplot(bot_dir,title2,fig2)
    saveplot(bot_dir,title3,fig3)

    plt.close()

def get_folder(CF,E,cell_id,data_dir=os.getcwd(),var="cfreq",filtered=False):
    top_dir=os.path.join(data_dir, "data",str(cell_id),var,f"{CF}Hz")
    param_dir=os.path.join(top_dir,f"{E}Vm")
    if not filtered:
        bot_dir=param_dir
    else:
        bot_dir=os.path.join(param_dir,"filtered")
    print(top_dir)
    print(bot_dir)
    return top_dir, bot_dir,param_dir

# top_dir,bot_dir=get_folder(500,40,1)
# voltages=load_voltages_hdf5(bot_dir)
# print(list(voltages.columns))