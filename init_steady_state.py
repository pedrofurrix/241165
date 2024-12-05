from neuron import h,gui
import numpy as np
from neuron.units import mV,ms,um
import matplotlib.pyplot as plt
from savedata import saveplot
import os
import json
import pandas as pd

h.load_file("interpCoordinates.hoc") #interp_coordinates 
h.load_file("setPointers.hoc")
h.load_file("calcVe_noGUI.hoc")
h.load_file("cellChooser.hoc")
h.load_file("setParams.hoc")
h.load_file("editMorphology.hoc")
h.load_file("stdrun.hoc")
h.load_file("plot_max.hoc")
h.load_file("field.hoc")


#Initializes the cell
id=1 # between 1 and 25
cell_name = h.cell_names.o(id-1).s  # `.s` converts HOC String to Python string
h.setParamsAdultHuman()
h.myelinate_ax=1
h.cell_chooser(id)
print(cell_name)
cell=h.cell

h.theta = 180 
h.phi = 0 
h.stim_mode=2
h.getes()

#Record things
t=h.Vector().record(h._ref_t)
soma_v=h.Vector().record(cell.soma[0](0.5)._ref_v)
dend_v=h.Vector().record(cell.dend[0](0.5)._ref_v)
axon_v=h.Vector().record(cell.axon[0](0.5)._ref_v)

simtime=1000
dt=0.1
celsius=37
h.celsius=celsius
h.tstop=simtime
h.dt=dt

h.v_init=-65*mV

h.finitialize()

# Check voltages at multiple timesteps...
'''
def get_voltages():
    return [seg.v for sec in cell.all for seg in sec]

voltages_over_time = []
time_points = list(range(0, simtime + 1, 10)) 

def record_voltages():
    voltages_over_time.append(get_voltages())


for t in range(0, simtime + 1, 10):  # Every 10 ms
    h.cvode.event(t, record_voltages)
'''


# Check voltage at 1 point...
voltages=[]
def record_voltages():
    global voltages
    voltages=[seg.v for sec in cell.all for seg in sec]

h.cvode.event(simtime-20, record_voltages)

h.continuerun(simtime)


# # Check steady_state multiple time points
# def steady_state_reached(threshold=1e-3):
#     for i in range(1, len(voltages_over_time)):
#         delta = [abs(v2 - v1) for v1, v2 in zip(voltages_over_time[i-1], voltages_over_time[i])]
#         if max(delta) >= threshold:
#             return False
#     return True




final_v=[seg.v for sec in cell.all for seg in sec]
seg=[seg for sec in cell.all for seg in sec]


delta = [final-v for final,v in zip(final_v, voltages)]
# Check steady_state one time point
def steady_state_reached(threshold=1e-3):
    if abs(max(delta,key=abs)) >= threshold:
        return False
    return True

threshold=1e-3
steady_state=steady_state_reached(threshold)

max_dif=max(delta,key=abs)

#plot intracellular voltage over time
fig,ax=plt.subplots()
ax.plot(t,soma_v,label="soma")
#ax.plot(t,dend_v,label="dend")
#ax.plot(t,axon_v,label="axon")
ax.set_xlabel("time(ms)")
ax.set_ylabel("Membrane Voltage (mV)") #vint-vext~
ax.legend()
title1="Membrane Potential"

plt.show()




#Save params
def saveparams(cell_id,simtime):
    #Create folder for run
    current_directory = os.getcwd()
    print(current_directory)

    folder_name=f"data\\{cell_id}\\steady_state"
    ssfolder = os.path.join(current_directory, folder_name,f"{simtime}")
    if not os.path.exists(ssfolder):
        os.makedirs(ssfolder)

    filename="params.json"
    path=os.path.join(ssfolder,filename)

    params = {"temperature" : h.celsius,
                "dt": h.dt,  # in ms
                "simtime": h.tstop,  # in ms
                "v_init": h.v_init,  # in ms
                "max_dif": max_dif,
                "threshold" : threshold,
                "reached_ss": steady_state
            }
    
    with open(path, "w") as file:
       json.dump(params, file, indent=4)  # Use indent=4 for readability
    print(f"Parameters saved to {path}")
    
    filev="voltages.csv"
    pathv=os.path.join(ssfolder,filev)
    data=pd.DataFrame({"seg_info":seg,"v_final":final_v,"v_20":voltages,"difference":delta})
    data.to_csv(pathv)
    print(f"Voltages saved to {pathv}")

    return ssfolder,folder_name

ssfolder,folder_name=saveparams(id,simtime)

from savedata import saveplot
saveplot(ssfolder,title1,fig)

def save_steady_state(folder_name,steady_state):
    savestate=h.SaveState()
    steady_state_file = "steady_state.dat" 
    path=os.path.join(folder_name,steady_state_file)

    if steady_state:
        savestate.save()
        h_file = h.File(path)  # Create an h.File object
        savestate.fwrite(h_file)           # Use fwrite with the h.File object
        h_file.close()                     # Close the file
        print(f"Steady state saved to {path}")

        filev="steady_voltages.csv"
        pathv=os.path.join(folder_name,filev)
        data=pd.DataFrame({"seg_info":seg,"v_init":final_v})
        data.to_csv(pathv)
        print(f"Voltages saved to {pathv}")


save_steady_state(folder_name,steady_state)

import savedata
folder=f"data\\{id}"
savedata.savelocations_xtra(folder,cell)
savedata.save_locations(folder,cell)
