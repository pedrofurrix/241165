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
import csv


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
    path = os.path.join(currdir, f"data\\{cell_id}\\threshold\\steady_state\\steady_state.bin")
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


def get_results(top_dir):
    top_file=os.path.join(top_dir, "results_summary.csv")
    results_df=pd.read_csv(top_file)
    return results_df

def get_max_segs(top_dir,cell):
    results_df=get_results(top_dir)
    maxp_seg=results_df["maxp_seg"].to_list()
    segslist=[]
    for seg in maxp_seg:
        if seg not in segslist:
            segslist.append(seg)

    def get_segments(segslist):
        segments=[]
        for seg in segslist:
            # Parse the string
            section_name = seg.split('(')[0]  # Example: "axon[0]"
            segment_loc = float(seg.split('(')[1].split(')')[0])  # Example: 0.5

            # Loop through all sections in the cell
            for sec in cell.all:  # Assuming `cell.all` is a list of all sections
                if sec.name() == section_name:
                    # Access the segment
                    segment=sec(segment_loc)    
                    segments.append(segment)
        return segments
    
    segments=get_segments(segslist)
    return segments

def setup_apcs(top_dir,cell):
    segments=get_max_segs(top_dir,cell)
    APCounters=[]
    for segment in segments:
        APCounters.append[h.APCount(segment)]
    return segments,APCounters


def initialize(cell_id, theta, phi,top_dir):
    cell, cell_name = initialize_cell(cell_id, theta, phi)
    segments,APCounters=setup_apcs(top_dir,cell)
    print(f"Initialized")
    return APCounters,cell


def threshsearch(cell_id,simtime,dt,ton,amp,depth,dur,freq,modfreq,APCounters,threshold):
    time,stim1= setstim(simtime,dt,ton,amp,depth,dur,freq,modfreq)
    print(f"Set stim with amplitude: {amp} V/m")
    h.finitialize(-72)
    restore_steady_state(cell_id)

    h.dt = dt
    h.tstop = simtime
    h.celsius = 37

    for apc in APCounters:
        apc.thresh=threshold
    h.continuerun(simtime)


    return any(apc.n>0 for apc in APCounters)

def threshold(cell_id, theta, phi, simtime, dt, amp, depth, freq, modfreq,ton,dur,run_id,top_dir,threshold=0):
    low=0
    high=1e6
    APCounters, cell=initialize(cell_id, theta, phi,top_dir)

    if amp==0: amp=50

    while low==0 or high==1e6:
        print(f"Searching bounds: low={low}, high={high}, amp={amp}")

        if threshsearch(cell_id,simtime,dt,ton,amp,depth,dur,freq,modfreq,APCounters):
            high = amp
            amp /= 2  # Reduce amplitude
        else:
            low = amp
            amp *= 2  # Increase amplitude
        # Stop the loop if stoprun_flag is True
        if h.stoprun==1: 
            return amp
        
        if high > 1e7:
            print("Amplitude exceeded maximum allowable value. Exiting.")
            amp=None
            savethresh(amp,freq,cell_id)
            return amp
        
        epsilon = high*1e-2
        amp=(high+low)/2

        while (high - low) > epsilon:
            print(f"Binary search: low={low}, high={high}, amp={amp}")

            if threshsearch(cell_id,simtime,dt,ton,amp,depth,dur,freq,modfreq,APCounters):
                high = amp
            else:
                low = amp
                
            amp = (high + low)/2
            epsilon=amp*1e-2
        
        # Stop the loop if stoprun_flag is True
        if h.stoprun==1: 
            break

        savethresh(high,freq,cell_id)
        return high

def savethresh(amp,freq,cell_id):
    currdir=os.getcwd()
    path = os.path.join(currdir, f"data\\{cell_id}\\threshold\\thresholds.csv")
    file_exists = os.path.exists(path)
     # Open the file in append mode
    with open(path, mode="a", newline="") as file:
        writer = csv.writer(file)
        # Write the header only if the file is new
        if not file_exists:
            writer.writerow(["Carrier_Frequency", "Threshold"])
        # Append the new data
        writer.writerow([freq, amp])

    print(f"Threshold for frequency {freq} saved to {path}")