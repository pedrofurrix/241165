import os
import pandas as pd
import h5py
import pickle
from csv_max_minshift import load_voltages_hdf5,load_params,get_folder
import json

def load_zones(cell_id,data_dir):
    path=os.path.join(data_dir,"data", str(cell_id), "cellzones.json")
      # Check if the file exists
    if not os.path.exists(path):
        print(f"Error: The file {path} does not exist.")
        return None
    
    # Load the JSON data
    with open(path, "r") as f:
        section_data = json.load(f)
    
    print(f"Successfully loaded zones from {path}")
    return section_data

def spike_detector(bot_dir,param_dir,data_dir=os.getcwd(),threshold=0,filtered=False):

    '''
    Voltages is a pd dataframe with the columns as the membrane potential for each segment and the rows being this potential over time
    '''

    voltages=load_voltages_hdf5(bot_dir,filtered)
    simparams, stimparams=load_params(param_dir)
    cell_id=simparams["cell_id"]
    section_data=load_zones(cell_id,data_dir)

    spikedata = {zone: {} for zone in section_data.keys()}

    columns=list(voltages) # List of dataframe columns
    time=voltages[columns[0]].to_list() # Time values
    timesteps=len(time)

    for seg in columns[1:]:
        section_name = seg.split('(')[0]  # Example: "axon[0]"
        segment_loc = seg.split('(')[1].split(')')[0]  # Extract segment location (e.g., "0.5")

        # Get voltage values for the segment
        v_values = voltages[seg].to_list()

        for zone, sections in section_data.items(): 
            if section_name in sections:
                    if section_name not in spikedata[zone]:
                        spikedata[zone][section_name] = {}

                    # Add the segment to the section
                    if segment_loc not in spikedata[zone][section_name]:
                        spikedata[zone][section_name][segment_loc] = []
                     
                    
                    for i in range(timesteps - 1):
                        if v_values[i + 1] >= threshold and v_values[i] <= threshold:
                            spikedata[zone][section_name][segment_loc].append(time[i + 1])

                    # Stop checking other zones once a match is found
                    break 

    # Calculate the total spikes and the total spikes per zone
    total_spikes = 0
    total_spikes_per_zone = {}
    total_spikes_per_section = {}
    most_spikes_count = 0
    most_spikes_count_zone=0
    most_spikes_count_section=0
    most_spikes_segment = None
    most_spikes_section=None
    most_spikes_zone = None
    average_isi_per_zone = {}
    spike_frequency_per_zone = {}
    spike_frequency_total = 0
    isi_total=[]
    for zone, sections in spikedata.items():
        zone_spikes = 0 
        spike_frequency_per_zone[zone] =0
        total_spikes_per_section[zone] = {}
        isi_zone = []  # List to store ISIs for this zone
        spike_counts_zone = []  # List to store spike counts for frequency calculation
        secnum=len(sections)
        for section, segments in sections.items():
            spikes_section = 0
            isi_section = []  # List to store ISIs for this section
            segnum=len(segments)
            for segment, spike_times in segments.items():
                spike_count = len(spike_times)

                # Update total spikes across all zones
                total_spikes += spike_count
                zone_spikes += spike_count
                spikes_section+= spike_count

                # Calculate ISI for the segment if there are at least two spikes
                if spike_count > 1:
                    # Calculate ISIs for this segment
                    isi_segment = [spike_times[i+1] - spike_times[i] for i in range(spike_count - 1)]
                    isi_section.extend(isi_segment)  # Add ISIs to the section's list
                    isi_zone.extend(isi_segment)  # Add ISIs to the zone's list
                    isi_total.extend(isi_segment)

                # Track the segment with the most spikes
                if spike_count > most_spikes_count:
                    most_spikes_count = spike_count
                    most_spikes_segment = f"{section}({segment})"  # Identify the segment (section - segment)
                            
            total_spikes_per_section[zone][section]=spikes_section

            if spikes_section>most_spikes_count_section:
                most_spikes_count_section = spikes_section
                most_spikes_section=f"{section}"
    
            # Add to spike frequency for this section
            if spikes_section > 0:
                spike_frequency_section = spikes_section/ simparams["simtime"]/segnum*1000  # Spikes per unit time (e.g., ms)
            else:
                spike_frequency_section = 0
            spike_frequency_per_zone[zone] += spike_frequency_section

        total_spikes_per_zone[zone] = zone_spikes

        if zone_spikes>most_spikes_count_zone:
            most_spikes_count_zone=zone_spikes
            most_spikes_zone=zone

            # Calculate average ISI for the entire zone
        if isi_zone:
            average_isi_per_zone[zone] = sum(isi_zone) / len(isi_zone)
        else:
            average_isi_per_zone[zone] = 0
    
          # Calculate spike frequency for the entire zone
        if secnum!=0:
            spike_frequency_per_zone[zone]/=secnum
        else:
            spike_frequency_per_zone[zone]=0

    # Calculate average ISI for the entire cell
    if total_spikes > 1:
        average_isi_total= sum(isi_total)/len(isi_total)  # You use (total_spikes - number of segments) to avoid dividing by 0
    else:
        average_isi_total = 0

    # Calculate total spike frequency for the entire cell
    spike_frequency_total = total_spikes / simparams["simtime"]

    any_spikes = total_spikes > 0

    spikefolder=os.path.join(bot_dir,"spike_data")
    if not os.path.exists(spikefolder):
        os.makedirs(spikefolder)

    # if most_spikes_count>1:
    #     spikes=spikedata[most_spikes_segment]
    #     isi=[spikes[i+1]-spikes[i] for i in range(most_spikes_count-1)]
    #     avg_isi=sum(isi)/len(isi)
    # else:
    #     avg_isi=None
    #     isi=None


    if any_spikes==False:
        summary = {
        "any_spikes": any_spikes,
    }
    else:
        # Prepare summary data
        summary = {
            "any_spikes": any_spikes,
            "total_spikes": total_spikes,
            "most_spikes_segment": most_spikes_segment,
            "most_spikes_count": most_spikes_count,
            "most_spikes_count_section": most_spikes_count_section,
            "most_spikes_section": most_spikes_section,
            "most_spikes_count_zone": most_spikes_count_zone,
            "most_spikes_zone": most_spikes_zone,
            "average_isi_total": average_isi_total,
            "spike_frequency_total": spike_frequency_total,
            "average_isi_per_zone": average_isi_per_zone,
            "spike_frequency_per_zone": spike_frequency_per_zone
        }
        
        '''
        Choose one file format...
        '''
        # # Save the spikedata dictionary to a Pickle file
        # spikefile = os.path.join(spikefolder, "spiketimes.pkl")
        # with open(spikefile, "wb") as f:
        #     pickle.dump(spikedata, f)
        # print(f"Spike times saved to {spikefile}")

        # Save the spikedata dictionary to a JSON file
        spikefile = os.path.join(spikefolder, "spiketimes.json")
        with open(spikefile, "w") as f:
            json.dump(spikedata, f, indent=4)
        print(f"Spike times saved to {spikefile}")

    json_file=os.path.join(spikefolder,"spike_summary.json")
    with open(json_file, "w") as f:
        json.dump(summary, f, indent=4)
    print(f"Spike summary saved to {json_file}")    


# freq_dir,e_dir=get_folder(100,10,1)
# spike_detector(e_dir)