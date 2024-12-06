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

def load_voltages(bot_dir):
    vfile=os.path.join(bot_dir,"run_voltages.csv")
    voltages=pd.read_csv(vfile)
    return voltages

def load_params(bot_dir): #Load paramsssssssss (get them into a format where I can easily extract them.., ) - json
    filename="params.json"
    path = os.path.join(bot_dir, filename)
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

def cmax_shift(bot_dir,top_dir, cell=None):
    voltages=load_voltages(bot_dir)
    headers=voltages.drop(columns=["t"]).columns.tolist()
    simparams, stimparams=load_params(bot_dir)

    num_seg=len(voltages.iloc[0,1:]) #remove column that has the time
    v_init=voltages.iloc[0,1:].to_list()

    if cell:
        # Initialize variables for tracking max/min values and corresponding segments
        max_shift=[0 for sec in cell.all for seg in sec] #alternatively, h.allsec() #Change also when obtaining the values...
        max_v=[v_init[seg] for seg in range(num_seg)]
        min_v=[v_init[seg] for seg in range(num_seg)]
        seg=[seg for sec in cell.all for seg in sec]
        pshift=[0 for sec in cell.all for seg in sec]
        nshift=[0 for sec in cell.all for seg in sec]
    else:
        max_shift=[0 for seg in range(num_seg)] #alternatively, h.allsec() #Change also when obtaining the values...
        max_v=[v_init[seg] for seg in range(num_seg)]
        min_v=[v_init[seg] for seg in range(num_seg)]
        seg=[seg for seg in range(num_seg)]
        pshift=[0 for seg in range(num_seg)]
        nshift=[0 for seg in range(num_seg)]

    # Initialize variables for tracking max/min values and corresponding segments
    results = {
        "EValue": stimparams["E"],
        "CFreq": stimparams["Carrier Frequency"],
        "max_shiftp": -1e5,
        "min_shiftp": 1e5,
        "max_shiftn": 0,
        "min_shiftn": 0,
        "maxp_seg": None, 
        "minp_seg": None,
        "maxn_seg": None,  
        "minn_seg": None,
        "maxp_sec": None,  
        "minp_sec": None,
        "maxn_sec": None,  
        "minn_sec": None
    }

    # i=0
    # for sec in cell.all: #alternatively, h.allsec() #Change also when obtaining the values...
    #     for seg in sec:

    for i in range(num_seg):
            v_seg=voltages.iloc[:,i+1] # Returns the membrane potential over time for each segment
            for v in v_seg:
                if v >=max_v[i]:
                    max_v[i]=v
                if v <=min_v[i]:
                    min_v[i]=v
    
    
    for i in range(len(max_shift)):
        pshift[i]=max_v[i]-v_init[i]
        nshift[i]=min_v[i]-v_init[i]
        if abs(pshift[i])>= abs(nshift[i]):
            max_shift[i]=pshift[i]
        else:
            max_shift[i]=nshift[i]

              #This has to change if they have different values...
    # In case they are different, h.v_init can be replaced by voltages.iloc[0,i] - initial voltage...
    # 
    results["max_shiftp"]=max(pshift)
    results["min_shiftp"]=min(pshift)
    results["max_shiftn"]=max(nshift,key=abs)
    results["min_shiftn"]=min(nshift,key=abs)
    results["maxp_index"]=next((i for i, val in enumerate(pshift) if abs(val) == abs(results["max_shiftp"])))
    results["minp_index"]=next((i for i, val in enumerate(pshift) if abs(val) == abs(results["min_shiftp"])))
    results["maxn_index"]=next((i for i, val in enumerate(nshift) if abs(val) == abs(results["max_shiftn"])))
    results["minn_index"]=next((i for i, val in enumerate(nshift) if abs(val) == abs(results["min_shiftn"])))
    results["maxp_seg"] = voltages.columns[results["maxp_index"]+1] # +1 is to account for time being the first column # could also just drop that column
    results["minp_seg"] = voltages.columns[results["minp_index"]+1]
    results["maxn_seg"] = voltages.columns[results["maxn_index"]+1] # +1 is to account for time being the first column # could also just drop that column
    results["minn_seg"] = voltages.columns[results["minn_index"]+1]   

    if cell:
        results["maxp_seg"]=seg[results["maxp_index"]]
        results["minp_seg"]=seg[results["minp_index"]]
        results["maxn_seg"]=seg[results["maxn_index"]]
        results["minn_seg"]=seg[results["minn_index"]]
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

def plot_voltage(bot_dir,results):
    voltages=load_voltages(bot_dir)

    t=voltages.iloc[:,0]

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
    ax2.plot(t, vmaxn,label=f"maxp_shift_{segmaxn}")
    ax2.plot(t, vminn,label=f"minp_shift_{segminn}")
    ax2.set_xlabel("time (ms)")  # Correct method to set labels
    ax2.set_ylabel("Membrane potential (mV)")
    ax2.legend()
    ax2.set_title(title2)  # Optional: add title to the plot
    # plt.show()
    
    # Plot Max both
    fig3,ax3=plt.subplots()
    title3=("Membrane potential over time - Maxshift")
    ax3.plot(t, vmaxp,label=f"maxp_shift_{segmaxp}")
    ax3.plot(t, vmaxn,label=f"minp_shift_{segmaxn}")
    ax3.set_xlabel("time (ms)")  # Correct method to set labels
    ax3.set_ylabel("Membrane potential (mV)")
    ax3.legend()
    ax3.set_title(title2)  # Optional: add title to the plot

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

def get_folder(CF,E,cell_id):
    currdir=os.getcwd()
    top_dir=os.path.join(currdir,f"data\\{cell_id}\\{CF}Hz")
    bot_dir=os.path.join(top_dir,f"{E}Vm")
    print(currdir)
    print(top_dir)
    print(bot_dir)
    
    return top_dir, bot_dir

