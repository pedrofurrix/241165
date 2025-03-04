from neuron import h
import numpy as np
from neuron.units import mV,ms,um
import matplotlib.pyplot as plt
from savedata import saveplot
import os
import json
import pandas as pd
import stim

h.load_file("stdrun.hoc")
h.load_file("interpCoordinates.hoc") #interp_coordinates 
h.load_file("setPointers.hoc")
h.load_file("calcVe_noGUI.hoc")
h.load_file("cellChooser.hoc")
h.load_file("setParams.hoc")
h.load_file("editMorphology.hoc")
h.load_file("plot_max.hoc")
h.load_file("field.hoc")

voltages=[]
#Initializes the cell
def initialize_cell(cell_id,theta,phi,ufield,coordinates,rho=0.276e-6):
    
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

def setstim(simtime,dt,ton,amp,depth,dur,freq,modfreq,ramp,ramp_duration,tau):
    time,stim1=stim.ampmodulation(ton,amp,depth,dt,dur,simtime,freq,modfreq,ramp,ramp_duration,tau)
    return time,stim1


def run_steady(run_id,cell_id,theta,phi,simtime,dt,ton,amp,depth,dur,freq,modfreq,ramp=False,ramp_duration=0,tau=None,data_dir=os.getcwd(),threshold=1e-7,ufield=True,coordinates=[0,0,0],rho=0.276e-6,time_before=1000):
    cell,cell_name=initialize_cell(cell_id,theta,phi,ufield,coordinates,rho)
    time,stim1=setstim(simtime,dt,ton,amp,depth,dur,freq,modfreq,ramp,ramp_duration,tau)

      # Setup Recording Variables to watch over the simulation.
    t=h.Vector().record(h._ref_t)
    is_xtra=h.Vector().record(h._ref_stim_xtra)
    soma_v=h.Vector().record(cell.soma[0](0.5)._ref_v)
    dend_v=h.Vector().record(cell.dend[0](0.5)._ref_v)
    axon_v=h.Vector().record(cell.axon[0](0.5)._ref_v)
    vrec = h.Vector().record(h._ref_vrec)  # records vrec at each timestep


    h.dt = dt
    h.tstop = simtime
    h.celsius = 37
    h.v_init=-65*mV

    h.finitialize()

    def record_voltages():
        global voltages
        voltages=[seg.v for sec in cell.all for seg in sec]

    h.cvode.event(simtime-time_before, record_voltages)

    h.continuerun(simtime)

    final_v=[seg.v for sec in cell.all for seg in sec]
    seg=[seg for sec in cell.all for seg in sec]
    print(final_v)
    print(voltages)

    delta = [final-v for final,v in zip(final_v, voltages)]
    # Check steady_state one time point
    def steady_state_reached(threshold):
        if abs(max(delta,key=abs)) >= threshold:
            return False
        return True
    
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


    def saveparams(cell_id,simtime,data_dir):
        #Create folder for run

        print(data_dir)

        folder_name=os.path.join(data_dir,"data",str(cell_id), "steady_state")
        ssfolder = os.path.join(folder_name,f"{simtime}")
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

    ssfolder,folder_name=saveparams(cell_id,simtime,data_dir)

    from savedata import saveplot
    saveplot(ssfolder,title1,fig)

    def save_steady_state(folder_name,steady_state):
        savestate=h.SaveState()
        steady_state_file = "steady_state.bin" 
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
    folder=os.path.join(data_dir,"data",str(cell_id))
    savedata.savelocations_xtra(folder,cell)
    savedata.save_locations(folder,cell)
    savedata.savezones(folder,cell)
    savedata.save_es(folder,theta,phi,cell)

##### THRESHOLD


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
            for sec in cell.all:  # cell.all is a list of all sections
                if sec.name() == section_name:
                    # Access the segment
                    segment=sec(segment_loc)    
                    segments.append(segment)
        return segments
    
    segments=get_segments(segslist)
    return segments

def setup_apcs(cell,record_all):
    """
    Set up action potential counters for every segment in the cell.
    """
    # segments=get_max_segs(top_dir,cell)

    APCounters=[]
    if record_all:
        segments=[seg for sec in cell.all for seg in sec]   
    else:
        segments=[cell.soma[0](0.5)]
    
    for segment in segments:
        ap_counter = h.APCount(segment) 
        APCounters.append(ap_counter)
        
    return segments,APCounters

def setup_netcons(cell,record_all):
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


def run_threshold(run_id,cell_id,theta,phi,simtime,dt,ton,amp,depth,dur,freq,modfreq,var="cfreq",
                  ramp=False,ramp_duration=0,tau=None,data_dir=os.getcwd(),threshold=1e-7,nc=True,record_all=False,ufield=True,coordinates=[0,0,0],rho=0.276e-6,time_before=1000):
    cell,cell_name=initialize_cell(cell_id,theta,phi,ufield,coordinates,rho)
    time,stim1=setstim(simtime,dt,ton,amp,depth,dur,freq,modfreq,ramp,ramp_duration,tau)
    if not nc:
        segments,APCounters=setup_apcs(cell,record_all)
    else:
        segments,NCs,Recorders=setup_netcons(cell,record_all)

    h.dt = dt
    h.tstop = simtime
    h.celsius = 37
    h.v_init=-65*mV

    h.finitialize()

    def record_voltages():
        global voltages
        voltages=[seg.v for sec in cell.all for seg in sec]

    h.cvode.event(simtime-time_before, record_voltages)

    h.continuerun(simtime)

    final_v=[seg.v for sec in cell.all for seg in sec]
    seg=[seg for sec in cell.all for seg in sec]
    print(final_v)
    print(voltages)

    delta = [final-v for final,v in zip(final_v, voltages)]
    # Check steady_state one time point
    def steady_state_reached(threshold=1e-3):
        if abs(max(delta,key=abs)) >= threshold:
            return False
        return True
    
    steady_state=steady_state_reached(threshold)

    max_dif=max(delta,key=abs)

    def saveparams(cell_id,simtime,data_dir):
        #Create folder for run
        
        print(data_dir)
        folder_name=os.path.join(data_dir,"data",str(cell_id),str(var),"threshold", "steady_state")
        ssfolder = os.path.join(folder_name,f"{simtime}")

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

    ssfolder,folder_name=saveparams(cell_id,simtime,data_dir)

    def save_steady_state(folder_name,steady_state):
        savestate=h.SaveState()
        steady_state_file = "steady_state.bin" 
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

    # import savedata
    # folder=os.path.join(os.getcwd(),"data",str(cell_id))
    # savedata.savelocations_xtra(folder,cell)
    # savedata.save_locations(folder,cell)