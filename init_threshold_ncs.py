from neuron import h
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
import json

# import load_files
h.load_file("stdrun.hoc")
h.load_file("interpCoordinates.hoc")
h.load_file("setPointers.hoc")
h.load_file("calcVe_noGUI.hoc")
h.load_file("cellChooser.hoc")
h.load_file("setParams.hoc")
h.load_file("editMorphology.hoc")
h.load_file("plot_max.hoc")
h.load_file("field.hoc")

#Initializes the cell
def initialize_cell(cell_id,theta,phi,ufield,coordinates,rho):
    h.setParamsAdultHuman()
    h.myelinate_ax=1
    h.cell_chooser(cell_id)
    cell_name = h.cell_names.o(cell_id-1).s  # `.s` converts HOC String to Python string
    cell=h.cell

    if ufield:
        h.theta = theta
        h.phi = phi
        h.stim_mode=2
        h.getes()
    else:
        h.xe,h.ye,h.ze=coordinates
        h.sigma_e=rho
        h.stim_mode=1
        h.getes()

    print(f"Initialized {cell_name}")

    return cell, cell_name


# Restore Steady State
def restore_steady_state(cell_id,var,data_dir):
    path = os.path.join(data_dir, "data",str(cell_id),str(var),"threshold", "steady_state","steady_state.bin")
    print(path)
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

def setstim(simtime,dt,ton,amp,depth,dur,freq,modfreq,ramp,ramp_duration,tau):
    time,stim1=stim.ampmodulation(ton,amp,depth,dt,dur,simtime,freq,modfreq,ramp,ramp_duration,tau)
    return time,stim1

def add_callback(cell,cell_id,freq,modfreq,depth,theta,phi,segments,var,data_dir,save):
    from all_voltages import custom_threshold
    folder,file,callback,voltages,finalize=custom_threshold(cell,cell_id,freq,modfreq,depth,theta,phi,segments,var,data_dir=data_dir,save=save,max_timesteps=1000000,buffer_size=100000)
    return  folder,file,callback,voltages,finalize
    # file,callback,finalize=record_voltages_gpt.record_voltages_hdf5(cell,e_dir)
    # return file, callback


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
    # segments=get_max_segs(top_dir,cell)
    segments=[seg for sec in cell.all for seg in sec]
    APCounters=[]
    for segment in segments:
        ap_counter = h.APCount(segment)  # Use parentheses, not square brackets
        APCounters.append(ap_counter)
    return segments,APCounters

def setup_netcons(cell,record_all=False):
    # segments=get_max_segs(top_dir,cell)
    if record_all:
        segments=[seg for sec in cell.all for seg in sec]
    else:
        segments=[cell.soma[0](0.5)]
    NCs=[]
    Recorders=[h.Vector() for seg in segments]
    for i,segment in enumerate(segments):
        netcon = h.NetCon(segment._ref_v,None)  # Use parentheses, not square brackets
        NCs.append(netcon)
        netcon.record(Recorders[i])
    return segments,NCs,Recorders

def initialize(cell_id, theta, phi,ufield,coordinates,rho,record_all):
    cell, cell_name = initialize_cell(cell_id, theta, phi,ufield,coordinates,rho)
    # segments,APCounters=setup_apcs(top_dir,cell)
    segments,NCs,Recorders=setup_netcons(cell,record_all=record_all)
    print(f"Initialized")
    return cell,segments,NCs,Recorders


def threshsearch(cell_id,theta,phi,cell,simtime,dt,ton,amp,depth,dur,freq,modfreq,NCs,Recorders,
                 segments, var,ramp,ramp_duration, tau, thresh=0,cb=False,save=False,data_dir=os.getcwd()):
    
    time,stim1= setstim(simtime,dt,ton,amp,depth,dur,freq,modfreq,ramp,ramp_duration,tau)
    
    print(f"Set stim with amplitude: {amp} V/m")
    h.finitialize(-72)
    restore_steady_state(cell_id,var,data_dir)

    if cb:
        print("Adding Callback")
        folder,file,callback,voltages,finalize=add_callback(cell,cell_id,freq,modfreq,depth,theta,phi,segments,var,data_dir,save)

    h.dt = dt
    h.tstop = simtime
    h.celsius = 37

    for nc in NCs:
        nc.threshold=thresh

    h.continuerun(simtime)

    if cb:
        file.close()

    if cb and save:
        finalize()
        # get_maxv(cell_id,freq,segments,writer2)

    minspikes=(simtime-(ramp_duration))/1000*modfreq
    
    num_spikes=[]

    for recorder in Recorders:
        spike_count=0
        spikes=recorder.to_python()
        if len(spikes) > 0:
            spike_count += 1  # Always count the first spike
            for i in range(1, len(spikes)):
                if spikes[i] - spikes[i-1] > 5:
                    spike_count += 1  # Count as new spike if time gap is large enough
        num_spikes.append(spike_count)

    if save:
        save_spiketimes(folder,Recorders,num_spikes,segments)

    any1=any(num>=minspikes for num in num_spikes)

    # ax,fig,title=plot_v(recordings,segments,freq,amp)

    return any1

def threshold(cell_id, theta, phi, simtime, dt, amp, depth, freq, modfreq,ton,dur,
              thresh=0,cb=False,var="cfreq",ramp=False,ramp_duration=0,tau=None,save=True,data_dir=os.getcwd(),record_all=False,
              ufield=True,coordinates=[0,0,0],rho=0.276e-6):
    low=0
    high=1e6
    cell,segments,NCs,Recorders=initialize(cell_id, theta, phi,ufield,coordinates,rho,record_all)

    if amp==0: amp=50

    while low==0 or high==1e6:
        print(f"Searching bounds: low={low}, high={high}, amp={amp}")
        if threshsearch(cell_id,theta,phi,cell,simtime,dt,ton,amp,depth,dur,freq,modfreq,NCs,Recorders,segments,
                        var=var,ramp=ramp,ramp_duration=ramp_duration, tau=tau, thresh=thresh,data_dir=data_dir):
            high = amp
            amp /= 2  # Reduce amplitude
        else:
            low = amp
            amp *= 2  # Increase amplitude
        # Stop the loop if stoprun_flag is True
        if h.stoprun==1: 
            print("Stop flag raised. Exiting.")
            return amp
        
        if high > 1e7:
            print("Amplitude exceeded maximum allowable value. Exiting.")
            amp=None
            savethresh(amp,freq,cell_id)
            return amp
        
        
    amp=(high+low)/2
    epsilon = amp*1e-2

    while (high - low) > epsilon:
        amp = (high + low)/2
        epsilon = amp*1e-2
        print(f"Binary search: low={low}, high={high}, amp={amp}")
        
        if threshsearch(cell_id,theta,phi,cell,simtime,dt,ton,amp,depth,dur,freq,modfreq,NCs,Recorders,segments,
                    var=var,ramp=ramp,ramp_duration=ramp_duration, tau=tau, thresh=thresh,data_dir=data_dir):
            high = amp
        else:
            low = amp

        # Stop the loop if stoprun_flag is True
        if h.stoprun==1: 
            print("Stop flag raised. Exiting.")
            break
        
    final_amp=(high+low)/2
    
    
    cb=True
    save=True
    threshsearch(cell_id,theta,phi,cell,simtime,dt,ton,final_amp,depth,dur,freq,modfreq,NCs,Recorders,segments,
                    var=var,ramp=ramp,ramp_duration=ramp_duration, tau=tau, thresh=thresh,data_dir=data_dir,cb=cb,save=save)
    savethresh(final_amp,freq,modfreq,depth,theta,phi,cell_id,var,data_dir)
    return high

def savethresh(amp,freq,modfreq,depth,theta,phi,cell_id,var,data_dir):
    path = os.path.join(data_dir, "data",str(cell_id),str(var),"threshold","thresholds.csv")
    file_exists = os.path.exists(path)
    # Initialize a list to store the updated data
    updated_data = []
    condition_exists = False  # Flag to check if the frequency exists in the file
    mapping = {
    "cfreq": freq,
    "modfreq": modfreq,
    "theta": theta,
    "phi": phi,
    "depth": depth
    }
    condition = mapping.get(var)  # Returns None if var is not in the dictionary
    # Check if the file exists
    if file_exists:
        # Read the existing file
        with open(path, mode="r", newline="") as file:
            reader = csv.reader(file)
            header = next(reader, None)  # Read the header (if it exists)
            
            # Add the header to updated_data
            if header:
                updated_data.append(header)

            # Iterate through the rows and update the amp value if the freq matches
            for row in reader:
                if len(row) >= 2 and row[0] == str(condition):  # Match the frequency
                    updated_data.append([condition, amp])  # Replace the amp value
                    condition_exists = True
                else:
                    updated_data.append(row)  # Keep the row unchanged
    # If the file doesn't exist, create it and add headers
    else:
        updated_data.append([var, "Threshold"])  # Add header to new file

     # If the frequency doesn't exist, add it as a new row
    if not condition_exists:
        if not updated_data: # If the file was empty, add the header
            updated_data.append([var, "Threshold"])
        updated_data.append([condition, amp])
    
    # Write the updated data back to the file
    with open(path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(updated_data)  # Write all rows back to the file
    print(amp)
    print(f"Threshold for var:{var}={condition} saved to {path}")

def save_apcs(folder,APCounters,segments):
    """
    Saves the APCounters and segments data into a JSON file.

    Parameters:
    - APCounters: A list or array of spike counts (number of spikes per segment).
    - segments: A list or array of segment identifiers (e.g., segment names or indices).
    - filename: The name of the file to save the data in (default is "spikes_data.json").
    """
    file=os.path.join(folder,"spikes_data.json")
     # Create a dictionary to store the data
    data = {}
    
    # Assuming APCounters and segments have the same length, pair them together
    for i in range(len(segments)):
        data[str(segments[i])] = APCounters[i].n
     # Save the data to a JSON file~

    with open(file, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Data saved to {file}")

def save_spiketimes(folder,Recorders,num_spikes,segments):
    """
    Saves the APCounters and segments data into a JSON file.

    Parameters:
    - APCounters: A list or array of spike counts (number of spikes per segment).
    - segments: A list or array of segment identifiers (e.g., segment names or indices).
    - filename: The name of the file to save the data in (default is "spikes_data.json").
    """
    file=os.path.join(folder,"spike_times.json")
    file_number=os.path.join(folder,"spike_number.json")
     # Create a dictionary to store the data
    data = {}
    num={}
    # Assuming APCounters and segments have the same length, pair them together
    for i in range(len(segments)):
        times=Recorders[i].to_python()
        data[str(segments[i])] = times
        num[str(segments[i])]=num_spikes[i]
     # Save the data to a JSON file

    with open(file, 'w') as json_file:
        json.dump(data, json_file, indent=4)

    with open(file_number, 'w') as json_file:
        json.dump(num, json_file, indent=4)
    print(f"Data saved to {file}")     
