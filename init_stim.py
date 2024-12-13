from neuron import h,gui
import numpy as np
from neuron.units import mV,ms,um
import matplotlib.pyplot as plt
import os
import pandas as pd
import stim
from savedata import saveparams, save_es, savedata, saveplot
import all_voltages
import record_voltages_gpt

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

#Initializes the cell
def initialize_cell(cell_id,theta,phi):
    
    h.setParamsAdultHuman()
    h.myelinate_ax=1
    h.cell_chooser(cell_id)
    cell_name = h.cell_names.o(cell_id-1).s  # `.s` converts HOC String to Python string
    cell=h.cell

    h.theta = theta
    h.phi = phi
    h.stim_mode=2
    h.getes()

    print(f"Initialized {cell_name}")

    return cell, cell_name


# Restore Steady State
def restore_steady_state(cell_id):
    currdir=os.getcwd()
    path = os.path.join(currdir, f"data\\{cell_id}\\steady_state\\steady_state.bin")
    savestate = h.SaveState()
    h_file = h.File(path)
    savestate.fread(h_file)
    savestate.restore(1)
    h.fcurrent()  # Synchronize restored state
    h.t = 0               # Reset simulation time to 0
    h.tstop = 0.1         # Run a very brief simulation
    h.continuerun(h.tstop)  # Allow NEURON to stabilize
    h.t = 0
    print(f"Steady state restored from {path}, and time reset to {h.t} ms")

def setstim(simtime,dt,ton,amp,depth,dur,freq,modfreq):
    time,stim1=stim.ampmodulation(ton,amp,depth,dt,dur,simtime,freq,modfreq)
    return time,stim1

def add_callback(cell,e_dir):
    file,callback=record_voltages_gpt.record_voltages_hdf5(cell,e_dir)
    return file, callback

def run_simulation(cell_id, theta, phi, simtime, dt, amp, depth, freq, modfreq,ton,dur,run_id,cb=True):
    cell, cell_name = initialize_cell(cell_id, theta, phi)
    time,stim1= setstim(simtime,dt,ton,amp,depth,dur,freq,modfreq)

    # Setup Recording Variables to watch over the simulation.
    t=h.Vector().record(h._ref_t)
    is_xtra=h.Vector().record(h._ref_stim_xtra)
    soma_v=h.Vector().record(cell.soma[0](0.5)._ref_v)
    dend_v=h.Vector().record(cell.dend[0](0.5)._ref_v)
    axon_v=h.Vector().record(cell.axon[0](0.5)._ref_v)
    vrec = h.Vector().record(h._ref_vrec)  # records vrec at each timestep

    h.finitialize(-72)
    restore_steady_state(cell_id)


    h.frecord_init()
    h.dt = dt
    h.tstop = simtime
    h.celsius = 37

    #Save params
    simparams=[dt,simtime,cell_id,cell_name]
    stimparams=[amp,ton,dur,freq,depth,modfreq,theta,phi]

    freq_dir, e_dir = saveparams(run_id, simparams, stimparams)
    save_es(freq_dir, amp, cell)

    # Record voltages
    if cb:
        file, callback = add_callback(cell,e_dir)
        print("Added Callback")
        
    print(f"Continue Run {simtime}")
    h.continuerun(simtime)

    if cb:
        file.close()

    print(f"Simulation Finished\n")
    print(f"Voltages saved to {file}")

    savedata(e_dir, t, is_xtra, vrec)

    print("Finished with success")

    return e_dir,t, is_xtra,vrec,soma_v,dend_v,axon_v,cell



def save_plots(e_dir,t,is_xtra,vrec,soma_v,dend_v,axon_v):
    fig1,ax1=plt.subplots()
    ax1.plot(t,soma_v,label="soma")
    ax1.plot(t,dend_v,label="dend")
    ax1.plot(t,axon_v,label="axon")
    ax1.set_xlabel("time(ms)")
    ax1.set_ylabel("Membrane Voltage (mV)") #vint-vext~
    ax1.legend()
    title1="Membrane_Potential"
    ax1.set_title(title1)
    saveplot(e_dir,title1,fig1)

    fig2,ax2=plt.subplots()
    ax2.plot(t,is_xtra)
    ax2.set_xlabel("time(ms)")
    ax2.set_ylabel("IS_xtra")
    title2="Stimulation_current"
    ax2.set_title(title2)
    saveplot(e_dir,title2,fig2)

    fig3,ax3=plt.subplots()
    ax3.plot(t,vrec)
    ax3.set_xlabel("time(ms)")
    ax3.set_ylabel("vrec(uV)")
    title3="Recorded_Potential"
    ax3.set_title(title3)
    saveplot(e_dir,title3,fig3)
