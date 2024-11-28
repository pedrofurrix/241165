import pandas as pd
import os
import matplotlib.pyplot as plt

from neuron import h


def savedata(folder,id,t,soma_v,dend_v,axon_v,v_extracellular,is_xtra,vrec):
    filename=f"run{id}.csv"
    path=os.path.join(folder,filename)
    data=pd.DataFrame({"t":t,"soma_v":soma_v,"dend_v":dend_v, "axon_v":axon_v, "v_extracellular":v_extracellular,"is_xtra":is_xtra,"vrec":vrec})
    data.to_csv(path,index=False)

def saveparams(id,cell,simparams,stimparams):
    #Create folder for run
    current_directory = os.getcwd()
    print(current_directory)
    folder_name=f"./data/run{id}"
    folder = os.path.join(current_directory, folder_name)
    if not os.path.exists(folder):
        os.makedirs(folder)

    filename=f"params{id}.txt"
    path=os.path.join(folder,filename)
    with open(path, "w") as file:
    # Write the header
        file.write("Simulation Parameters\n")
        file.write(f"dt={simparams[0]} ms\n simtime={simparams[1]} ms\n temperature={simparams[2]}ºC")
        file.write("Stimulation Parameters\n")
        file.write(f"E={stimparams[0]}V/m\n Delay={stimparams[1]} ms\n Amplitude={stimparams[2]} multiplier\n")
        file.write(f"Duration={stimparams[3]} ms\n Carrier Frequency={stimparams[4]} Hz\n Modulation Depth={stimparams[5]}\n Modulation Frequency={stimparams[6]} Hz\n  \n")    
        file.write("x   y   z (um)   es (mV)\n")
        for sec in cell.all:
            if h.ismembrane("xtra"):
                for seg in sec:
                    x = seg.x_xtra
                    y = seg.y_xtra
                    z = seg.z_xtra
                    es = seg.es_xtra
                    # Write the values to the file
                    file.write(f"{x} {y} {z} {es}\n")
    return folder 

def saveplot(folder,title,fig_or_ax):
    filename=f"{title}.png"

    if isinstance(fig_or_ax, plt.Axes):
        # If it's an Axes object, get the Figure from the Axes
        fig = fig_or_ax.get_figure()
    elif isinstance(fig_or_ax, plt.Figure):
        # If it's already a Figure, use it as is
        fig = fig_or_ax
    else:
        raise TypeError("Input must be a matplotlib Figure or Axes object.")
    
    path=os.path.join(folder,filename)
    
    fig.savefig(path)


def savespikes(folder,id,spiketimes):
    filename=f"spikes{id}.csv"
    path=os.path.join(folder,filename)
    
    spike_dict = {}
    for i, spikes in enumerate(spiketimes):
        spike_dict[f"{i}"]= spikes
    
    data=pd.DataFrame(spike_dict)
    data.to_csv(path,index=False)

