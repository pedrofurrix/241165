from neuron import h,gui
import numpy as np
from neuron.units import mV,ms,um
import matplotlib.pyplot as plt
import os
import json
import pandas as pd
currdir=os.getcwd()
print(currdir)


# import load_files
h.load_file("interpCoordinates.hoc")
h.load_file("setPointers.hoc")
h.load_file("calcVe_noGUI.hoc")
h.load_file("cellChooser.hoc")
h.load_file("setParams.hoc")
h.load_file("editMorphology.hoc")
h.load_file("stdrun.hoc")
h.load_file("plot_max.hoc")
h.load_file("field.hoc")

run=0
#Initializes the cell
id=1 # between 1 and 25
h.setParamsAdultHuman()
h.myelinate_ax=1
h.cell_chooser(id)
cell_name = h.cell_names.o(id-1).s  # `.s` converts HOC String to Python string
cell=h.cell

theta=180
phi=0

h.theta = theta
h.phi = phi
h.stim_mode=2
h.getes()

#Record things
t=h.Vector().record(h._ref_t)
is_xtra=h.Vector().record(h._ref_stim_xtra)
soma_v=h.Vector().record(cell.soma[0](0.5)._ref_v)
dend_v=h.Vector().record(cell.dend[0](0.5)._ref_v)
axon_v=h.Vector().record(cell.axon[0](0.5)._ref_v)
vrec = h.Vector().record(h._ref_vrec)  # records vrec at each timestep

# #Restore steady state
# h.finitialize(-73*mV)
# path=os.path.join(currdir,f"data\\{id}\\steady_state\\steady_state.dat")
# savestate=h.SaveState()
# h_file = h.File(path)
# savestate.fread(h_file)
# savestate.restore(1)
# h.t = 0
# print(f"Steady state restored from {path}, and time reset to {h.t} ms")


#Stimulation
import stim
simtime=100
dt=0.001
ton=0
amp=1000
depth=1
dur=simtime
freq=500
modfreq=100
time,stim1=stim.ampmodulation(ton,amp,depth,dt,dur,simtime,freq,modfreq)

h.dt=dt
h.tstop=simtime
h.celsius=37

#Save params
simparams=[dt,simtime,id,cell_name]
stimparams=[amp,ton,dur,freq,depth,modfreq,theta,phi]

from savedata import saveparams, save_es
freq_dir, e_dir = saveparams(run,simparams,stimparams)

save_es(freq_dir,amp,cell)
h.dt=dt
h.tstop=simtime
h.celsius=37

# #Record voltages
# import all_voltages
# file,callback=all_voltages.record_voltages(cell,e_dir)

import record_voltages_gpt
file,callback=record_voltages_gpt.record_voltages_hdf5(cell,e_dir)
# save_data, callback=record_voltages_gpt.record_voltages_numpy(cell,e_dir)


h.finitialize(-73*mV)
h.frecord_init()	
h.continuerun(simtime)


print("Simulation Finished")
file.close()
# save_data()

from savedata import savedata,saveplot

time=t.to_python()
is_xtra=is_xtra.to_python()
vrec=vrec.to_python()
soma_v=soma_v.to_python()
dend_v=dend_v.to_python()
print(time)

print(soma_v,dend_v)
savedata(e_dir,t,is_xtra,vrec)



#Save plots
fig1,ax=plt.subplots()
ax.plot(t,soma_v,label="soma")
ax.plot(t,dend_v,label="dend")
ax.plot(t,axon_v,label="axon")
ax.set_xlabel("time(ms)")
ax.set_ylabel("Membrane Voltage (mV)") #vint-vext~
ax.legend()
title1="Membrane Potential"
ax.set_title(title1)
saveplot(e_dir,title1,fig1)

fig2,ax=plt.subplots()
ax.plot(t,is_xtra)
ax.set_xlabel("time(ms)")
ax.set_ylabel("IS_xtra")
title2="Stimulation"
ax.set_title(title2)
plt.show()
saveplot(e_dir,title2,fig2)

fig3,ax=plt.subplots()
ax.plot(t,vrec)
ax.set_xlabel("time(ms)")
ax.set_ylabel("vrec(uV)")
title3="Recorded Potential"
ax.set_title(title3)
plt.show()
saveplot(e_dir,title3,fig3)



