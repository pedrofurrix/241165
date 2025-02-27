import pandas as pd
import os
import matplotlib.pyplot as plt
import csv 
from neuron import h
import json


def savedata(bot_dir,t,is_xtra,vrec):
    filename=f"vrec.csv"
    path=os.path.join(bot_dir,filename)
    data=pd.DataFrame({"t": t,"is_xtra": is_xtra,"vrec": vrec})
    data.to_csv(path,index=False)
    print(f"Vrec and is saved to {path}")

def saveparams(run_id,simparams,stimparams,var,data_dir):
    #Create folder for run
    print(data_dir)
    top_top_dir = os.path.join(data_dir, "data", str(simparams[2]))

    # Create all necessary directories with exist_ok=True
    vari = os.path.join(top_top_dir, f"{var}")
    if var == "cfreq":
        top_dir = os.path.join(vari, f"{int(stimparams[3])}Hz")
    elif var == "depth":
        top_dir = os.path.join(vari, f"{int(stimparams[4] * 10)}")
    elif var == "modfreq":
        top_dir = os.path.join(vari, f"{int(stimparams[5])}Hz")
    elif var == "theta":
        top_dir = os.path.join(vari, f"{int(stimparams[6])}")   
    elif var == "phi":
        top_dir = os.path.join(vari, f"{int(stimparams[7])}")   
    else:
        top_dir = os.path.join(vari, f"{int(stimparams[3])}Hz")
    
    bot_dir = os.path.join(top_dir, f"{int(stimparams[0])}Vm")
    
    # Use os.makedirs with exist_ok=True
    os.makedirs(bot_dir, exist_ok=True)

    filename="params.json"
    path=os.path.join(bot_dir,filename)
    params = {   
        "Simulation Parameters": {
            "run_id": run_id,
            "cell_id" : simparams[2], # cell_id is in HOC
            "cell_name" : simparams[3], # cell_name
            "temperature" : h.celsius,
            "dt": simparams[0],  # in ms
            "simtime": simparams[1],  # in ms
            "v_init": h.v_init  # in ms
        },
        "Stimulation Parameters": {
            "E": stimparams[0],  # Electric field in V/m
            "Theta" : stimparams[6],
            "Phi" : stimparams[7],
            "Delay": stimparams[1],  # Delay in ms
            "Duration": stimparams[2],  # Duration in ms
            "Carrier Frequency": stimparams[3],  # Frequency in Hz
            "Modulation Depth": stimparams[4],  # Depth (0-1)
            "Modulation Frequency": stimparams[5],  # Modulation frequency in Hz
            "Ramp Up":stimparams[8],
            "RUp Duration":stimparams[9],
            "tau":stimparams[10]
        }
    }
    with open(path, "w") as file:
        json.dump(params, file, indent=4)  # Use indent=4 for readability

    print(f"Parameters saved to {path}")
    return top_dir,bot_dir

def savelocations_xtra(top_top_dir,cell):
    locations="locations_xtra.csv"
    path=os.path.join(top_top_dir,locations)
    with open(path, "w") as file:
        writer = csv.writer(file)
        header = ["seg", "x_xtra", "y_xtra", "z_xtra"]  # Column names as a list #[f"{sec.name()}({i})" for sec in cell.all for i, _ in enumerate(sec)]
        writer.writerow(header)
        for sec in cell.all:
            if h.ismembrane("xtra"):
                for seg in sec:
                    segname=seg
                    x = seg.x_xtra
                    y = seg.y_xtra
                    z = seg.z_xtra
                    # Write the values to the file
                    writer.writerow([segname,x,y,z])
    return print(f"Saved to {path}")

def save_es(top_dir,theta,phi,cell):
    """
    Save 'es' values to a CSV file, appending a new column for each run.

    Parameters:
    - es: List of es values.
    - top_dir
    - Evalue associated with the files...
    """
    # Convert 'es' to a pandas DataFrame
    es_values=[seg.es_xtra for sec in cell.all for seg in sec]
    out_file=os.path.join(top_dir,"es_values.csv")

    if os.path.exists(out_file):
        # File exists, load existing data
        existing_data = pd.read_csv(out_file)
        # Append the new column
        es_run = pd.DataFrame({f"Run_{theta}_{phi}": es_values})
        existing_data[f"Run_{theta}_{phi}"] = es_run[f"Run_{theta}_{phi}"]
    else:
        # File does not exist, initialize with the new data
        seg=[seg for sec in cell.all for seg in sec]
        es_init = pd.DataFrame({"seg_info":seg , f"Run_{theta}_{phi}": es_values})
        existing_data = es_init

    existing_data.to_csv(out_file, index=False)
    print(f"'es' values saved to {out_file} for Run {theta}_{phi}.")

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

def savespikes(bot_dir,spiketimes):
    filename=f"spikes.csv"
    path=os.path.join(bot_dir,filename)
    
    spike_dict = {}
    for i, spikes in enumerate(spiketimes):
        spike_dict[f"{i}"]= spikes
    data=pd.DataFrame(spike_dict)
    data.to_csv(path,index=False)
    
def save_locations(top_top_dir,cell):
    path=os.path.join(top_top_dir,f"run_locations.csv")
    with open(path,'w',newline='') as file:
        writer = csv.writer(file)
        header =["seg","x","y","z","arc","diam"] #[f"{sec.name()}({i})" for sec in cell.all for i, _ in enumerate(sec)]
        writer.writerow(header)
        for sec in cell.all:
            for i in range(sec.n3d()):
                section_info=f"{sec.name()}({i})"
                x=sec.x3d(i)
                y=sec.y3d(i)
                z=sec.z3d(i)
                arc=sec.arc3d(i)
                diam=sec.diam3d(i)
                location=[section_info,x,y,z,arc,diam]
                writer.writerow(location)

def savezones(top_top_dir,cell):
    path=os.path.join(top_top_dir,f"cellzones.json")
    somatic = [sec.name() for sec in cell.somatic]  # Convert objects to names
    apical = [sec.name() for sec in cell.apical]    # Convert objects to names
    basal = [sec.name() for sec in cell.basal]      # Convert objects to names
    axonal = [sec.name() for sec in cell.axonal]    # Convert objects to names
    myelin=[]
    unmyelin=[]
    nodes=[]
    for sec in cell.all:
        if "Myelin" in sec.name():
            myelin.append(sec.name())
        elif "Unmyelin" in sec.name():
            unmyelin.append(sec.name())
        elif "Node" in sec.name():
            nodes.append(sec.name())

    section_data = {
    "somatic": somatic,
    "apical": apical,
    "axonal": axonal,
    "basal": basal,
    "myelin" : myelin,
    "unmyelin": unmyelin,
    "nodes": nodes
    }
    with open(path, "w") as f:
        json.dump(section_data, f, indent=4)
    print(f"Section data has been saved to {path}")

