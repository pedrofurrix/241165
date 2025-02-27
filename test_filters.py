import filter_and_max
import os
import h5py
from scipy.signal import detrend
import matplotlib.pyplot as plt
from savedata import saveplot

def get_soma_voltages(voltages, segment_names):
    """
    Extract the voltages for the soma from the voltages dataset.

    Args:
        voltages: NumPy array of shape (timesteps, segments).
        segment_names: List of segment names corresponding to the columns in `voltages`.

    Returns:
        soma_voltages: NumPy array of voltages for the soma.
    """
    # Find the index of the soma segment
    soma_index = next((i for i, name in enumerate(segment_names) if "soma" in name), None)
    
    if soma_index is None:
        raise ValueError("Soma segment not found in segment names.")
    
    # Extract voltages for the soma segment
    soma_voltages = voltages[:, soma_index] -voltages[0,soma_index]
    return soma_voltages


def detrend_data(filtered_voltages):
    detrended=detrend(filtered_voltages,axis=-1, type='linear', bp=0, overwrite_data=False)
    return detrended

def test_filters(CF,E,cell_id,var="cfreq",data_dir=os.getcwd(),voltages=None, 
                 time=None,segment_names=None, filtered=False,detrend=False,
                 target_fs=1000,modfreq=10,highcut=None,lowcut=None,order_bp=3,cutoff_dc=2):
    top_dir,bot_dir,param_dir=filter_and_max.get_folder(CF,E,cell_id,var,filtered,data_dir)
    if voltages is None:
        time, voltages, segment_names=filter_and_max.load_voltages_hdf5(bot_dir)
    
    soma_voltages=get_soma_voltages(voltages, segment_names)
    # Filter orders and cutoff frequencies to test
    dt=time[1]-time[0]
    fs=1/(dt/1000)
    filter_orders = [3, 4]
    cutoff_frequencies = [100, 200]

    # Create subplots
    fig, axes = plt.subplots(len(filter_orders), len(cutoff_frequencies), figsize=(15, 10), sharex=False, sharey=False)
    # Plot filtered signals in subplots
    for i, order in enumerate(filter_orders):
        for j, cutoff in enumerate(cutoff_frequencies):
            filtered_signal = filter_and_max.butter_lowpass_filter(soma_voltages,cutoff, fs,order)
            subsampled=filter_and_max.subsample_data(filtered_signal,fs,target_fs)
            t_subsampled=filter_and_max.subsample_data(time,fs,target_fs)
            dc_v=filter_and_max.butter_lowpass_filter(subsampled,cutoff_dc,target_fs,order=4)
            bandpassed,highcut,lowcut=filter_and_max.butter_bandpass_filter(subsampled,target_fs,modfreq=modfreq,order=order_bp)
            # if detrend:
            #     filtered_signal=detrend_data(filtered_signal)
            ax = axes[i, j]
            ax.plot(time, filtered_signal, color='blue',label="LP")
            ax.plot(t_subsampled, bandpassed, color='orange',label="BP")
            ax.set_title(f"Order: {order*2}, Cutoff: {cutoff} Hz")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Membrane Potential(mV)")
            ax.grid()

        title="Filtered Soma Membrane Potential with Different Orders and Cutoff Frequencies"

    fig.suptitle(title, fontsize=16)
    fig.tight_layout(rect=[0, 0, 1, 0.96])  # Leave space for the title
    saveplot(bot_dir,title,fig)
    plt.close(fig)      

    # Plot Unfiltered Voltage :D
    fig1,ax1=plt.subplots()
    ax1.plot(time,soma_voltages)
    title1=f"Unfiltered Soma Voltage"
    ax1.set_title(title1)
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Membrane Potential(mV)")
    saveplot(bot_dir,title1,fig1)
    plt.close(fig1)
    
def test_subsample(CF,E,cell_id,var="cfreq",data_dir=os.getcwd(),voltages=None,
                 time=None,segment_names=None, filtered=False,detrend=False,target_fs=1000,
                 modfreq=10,cutoff=None,highcut=None,lowcut=None,order_low=3,order_bp=3,cutoff_dc=2):
    top_dir,bot_dir,param_dir=filter_and_max.get_folder(CF,E,cell_id,var,filtered,data_dir)
    if voltages is None:
        time, voltages, segment_names=filter_and_max.load_voltages_hdf5(bot_dir)
    soma_voltages=get_soma_voltages(voltages, segment_names)
    # Filter orders and cutoff frequencies to test
    dt=time[1]-time[0]
    fs=1/(dt/1000)

    # Create subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10), sharex=False, sharey=False,dpi=300)
    # Plot 
    ax = axes[0, 0]

    ax.plot(time, soma_voltages-soma_voltages[0], color='blue')
    ax.set_title(f"Original voltages")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Membrane Potential(mV)")
    ax.grid()

    filtered_signal = filter_and_max.butter_lowpass_filter(soma_voltages,cutoff, fs,order_low)
    ax = axes[0, 1]
    ax.plot(time, filtered_signal, color='blue')
    ax.set_title(f"Low Pass: Order {order_low*2}, Cutoff: {cutoff} Hz")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Membrane Potential(mV)")
    ax.grid()
    subsampled=filter_and_max.subsample_data(filtered_signal,fs,target_fs)
    subsampled_time = filter_and_max.subsample_data(time, fs, target_fs)
    ax = axes[1, 0]
    ax.plot(subsampled_time, subsampled, color='blue')
    ax.set_title(f"Subsampled: fs= {target_fs} Hz")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Membrane Potential(mV)")
    ax.grid()
    bandpassed,highcut,lowcut=filter_and_max.butter_bandpass_filter(subsampled,target_fs,modfreq=modfreq,highcut=highcut,lowcut=lowcut,order=order_bp)
    ax = axes[1, 1]
    ax.plot(subsampled_time, bandpassed, color='blue')
    ax.set_title(f"BP: Order {order_bp*2}, Cutoffs:{lowcut}-{highcut} Hz")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Membrane Potential(mV)")
    ax.grid()

    # dc_v=filter_and_max.butter_lowpass_filter(subsampled,cutoff_dc,target_fs,order=4)
    # ax = axes[0, 2]
    # ax.plot(subsampled_time, dc_v, color='blue')
    # ax.set_title(f"DC: LP Order 8, Cutoffs:{cutoff_dc} Hz")
    # ax.set_xlabel("Time (s)")
    # ax.set_ylabel("Membrane Potential(mV)")
    # ax.grid()
    title="Processing Pipeline"

    fig.suptitle(title, fontsize=16)
    fig.tight_layout(rect=[0, 0, 1, 0.96])  # Leave space for the title
    saveplot(bot_dir,title,fig)
    plt.close(fig)      

    