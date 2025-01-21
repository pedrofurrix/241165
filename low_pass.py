from scipy.signal import butter, filtfilt,freqz,hilbert
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from csv_max_minshift import get_folder,load_voltages_hdf5,load_params
import os
from savedata import saveplot
import json

# CF=100
# E=10
# cell_id=1



def get_results(freq_dir):
    path=os.path.join(freq_dir,"results_summary.csv")
    results=pd.read_csv(path)
    return results




def filter_data(CF,E,cell_id,cutoff=20,data_dir=os.getcwd(),results=None,var="cfreq",order=2,save=True,plot=True):

    freq_dir, e_dir,param_dir=get_folder(CF,E,cell_id,data_dir,var)
    voltages=load_voltages_hdf5(e_dir)
    simparams, stimparams=load_params(param_dir)

    dt=simparams["dt"] # ms
    fs=1/(dt*1e-3) # Hz
    simtime=simparams["simtime"] # ms

    if results==None:
        results=get_results(freq_dir)
        maxpseg = results[results['EValue'] == E]['maxp_seg'].values[0]
        maxnseg = results[results['EValue'] == E]['maxn_seg'].values[0]
    else:
        maxpseg=results["maxp_seg"]
        maxnseg=results["maxn_seg"]

    print(f"maxpseg={maxpseg}")
    print(f"maxnseg={maxnseg}")
    t=voltages["t"].to_list()
    maxpvoltages = voltages[maxpseg].to_list()
    maxnvoltages = voltages[maxnseg].to_list()

    # print(f"Length of maxpvoltages: {len(maxpvoltages)}")
    # print(f"Length of maxnvoltages: {len(maxnvoltages)}")


    # print(f"Raw maxpvoltages: {maxpvoltages[:10]}")
    # Filtered hilbert
    analytic_p,envelope_p=hilbert_transform(maxpvoltages)
    filtered_maxp=butter_lowpass_filter(maxpvoltages, cutoff, fs, order)
    filtered_maxpenvelope=butter_lowpass_filter(envelope_p, cutoff, fs, order)

    print(f"Filtered maxpvoltages: {filtered_maxp[:10]}")
    analytic_n,envelope_n=hilbert_transform(maxnvoltages)
    filtered_maxn=butter_lowpass_filter(maxnvoltages, cutoff, fs,order)
    filtered_maxnenvelope=butter_lowpass_filter(envelope_n, cutoff, fs, order)

    filtered_file=os.path.join(e_dir,"filtered")
    if not os.path.exists(filtered_file):
        os.makedirs(filtered_file)

    if save:
        # Save the data
        data={
            "t":t,
            "maxpvoltages":maxpvoltages,
            "filtered_maxp":filtered_maxp,
            # Added these 3 after
            "analytic_p": analytic_p,
            "envelope_p":envelope_p,
            "filtered_maxpenvelope":filtered_maxpenvelope,
            "maxnvoltages":maxnvoltages,
            "filtered_maxn":filtered_maxn,
            # Added these 3 after
            "analytic_n": analytic_n,
            "envelope_n":envelope_n,
            "filtered_maxnenvelope":filtered_maxnenvelope,
        }
        out_file=os.path.join(filtered_file,f"filtered_data{order}.csv")
        data_pd=pd.DataFrame([data])
        data_pd.to_csv(out_file,index=False)
        print(f"Filtered data saved to {out_file}")

        # Save params
        params = {   
            "dt":dt,
            "simtime":simtime,
            "cutoff":cutoff,
            "fs":fs,
            "order":order
        }

        path=os.path.join(filtered_file,f"params{order}.json")
        with open(path, "w") as file:
            json.dump(params, file, indent=4)  # Use indent=4 for readability

        print(f"Parameters saved to {path}")

    if plot:
        plot_filtered(t,maxpseg,maxpvoltages,filtered_maxp,filtered_file,order,info="maxp",save=save)
        plot_filtered(t,maxnseg,maxnvoltages,filtered_maxn,filtered_file,order,info="maxn",save=save)
        plot_hilbert(t,maxpseg,maxpvoltages,envelope_p,filtered_maxpenvelope,filtered_file,order,info="maxp",save=save)
        plot_hilbert(t,maxnseg,maxnvoltages,envelope_n,filtered_maxnenvelope,filtered_file,order,info="maxn",save=save)
        plot_bode(cutoff, fs, order,filtered_file,save)
        plot_onlyfiltered(t,filtered_maxp,filtered_file,order,info="filter_maxp",save=save)

    return maxpvoltages,maxnvoltages,filtered_maxp,filtered_maxn,filtered_file,t


def plot_filtered(t,maxseg,maxvoltage,filteredv,file,order,info=None,save=False):
    fig,ax=plt.subplots()
    ax.plot(t,maxvoltage,label=f"Unfiltered")
    ax.plot(t,filteredv,label=f"Filtered")
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Membrane Potential (mV)")
    ax.legend()
    title=f"Filtered response_{order}_{info}"
    ax.set_title(title)
    plt.show()
    if save:
        saveplot(file,title,fig)

def plot_hilbert(t,maxseg,maxvoltage,envelope,filtered_envelope,file,order,info=None,save=False):
    fig,ax=plt.subplots()
    ax.plot(t,maxvoltage,label=f"Unfiltered")
    ax.plot(t,envelope,label=f"Envelope")
    ax.plot(t,filtered_envelope,label=f"Filtered Envelope")
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Membrane Potential (mV)")
    ax.legend()
    title=f"Hilbert Filtered response_{order}_{info}"
    ax.set_title(title)
    plt.show()
    if save:
        saveplot(file,title,fig)    


def butter_lowpass_filter(data, cutoff, fs,order):
    """
    Applies a low-pass Butterworth filter.

    Parameters:
        data (array): The input signal.
        cutoff (float): The cutoff frequency of the filter (Hz).
        fs (float): The sampling frequency (Hz).
        order (int): The order of the filter.

    Returns:
        filtered_data (array): The filtered signal.
    """
    nyquist = 0.5 * fs  # Nyquist frequency
    normal_cutoff = cutoff / nyquist  # Normalized cutoff frequency
    # Design the Butterworth filter
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    # Apply the filter using filtfilt (zero-phase filtering)
    filtered_data = filtfilt(b, a, data)
    print(f"Low pass filter of order:{order} and with a cutoff:{cutoff} applied to the data successfully")
    return filtered_data


def plot_bode(cutoff, fs, order,save_dir=None,save=False):
    """
    Plots the Bode magnitude and phase response of a Butterworth filter.

    Parameters:
        cutoff (float): The cutoff frequency of the filter (Hz).
        fs (float): The sampling frequency (Hz).
        order (int): The order of the filter.
    """
    nyquist = 0.5 * fs  # Nyquist frequency
    normal_cutoff = cutoff / nyquist  # Normalized cutoff frequency

    # Design the Butterworth filter
    b, a = butter(order, normal_cutoff, btype='low', analog=False)

    # Compute the frequency response
    w, h = freqz(b, a, worN=8000)  # `w` is frequency, `h` is the response

    # Convert from rad/sample to Hz
    freqs = w * fs / (2 * np.pi)

    # Magnitude plot
    fig, ax = plt.subplots(2, 1, figsize=(10, 6))
    ax[0].semilogx(freqs, 20 * np.log10(abs(h)), label=f"Cutoff: {cutoff} Hz")
    ax[0].set_title('Bode Plot')
    ax[0].set_xlabel('Frequency (Hz)')
    ax[0].set_ylabel('Magnitude (dB)')
    ax[0].grid(which='both', linestyle='--', linewidth=0.5)
    ax[0].legend()

    # Phase plot
    ax[1].semilogx(freqs, np.angle(h, deg=True), label=f"Order: {order}")
    ax[1].set_xlabel('Frequency (Hz)')
    ax[1].set_ylabel('Phase (Degrees)')
    ax[1].grid(which='both', linestyle='--', linewidth=0.5)
    ax[1].legend()

    plt.tight_layout()

    # Save the plot if a directory is provided
    if save_dir:
        if save:
            title = f"Bode_Plot_Cutoff_{cutoff}_Order_{order}"
            saveplot(save_dir, title, fig)

    plt.show()
    print(f"Bode plot created for a {order}-order Butterworth filter with cutoff frequency {cutoff} Hz.")


def test_fake_data(dt=0.001, simtime=1000, noise_level=0.5,cfreq=100,modfreq=10,order=2,cutoff=20):
        
    """
    Generate fake membrane potential data for debugging.

    Parameters:
        dt (float): Time step in milliseconds.
        simtime (float): Total simulation time in milliseconds.
        noise_level (float): Amplitude of random noise to add to the signal.

    Returns:
        voltages (pd.DataFrame): Time and fake voltage data.
    """
    fs=1/(dt*1e-3) # Hz


    # Time vector: start=0, stop=simtime, step=dt
    t = np.arange(0, simtime, dt)
    
    # Simulated signal: a combination of sine waves + noise
    f1 = modfreq # Frequency of the main signal (Hz)
    f2 = cfreq  # Secondary frequency
    signal = -65 + 5 * np.sin(2 * np.pi * f1 * t / 1000) + 2 * np.sin(2 * np.pi * f2 * t / 1000)
    
    # Add random noise
    noise = np.random.normal(0, noise_level, size=len(t))
    voltages = signal + noise          

    filtered_data=butter_lowpass_filter(voltages, cutoff,fs,order)

    plt.plot()
    # Plot the original and filtered data
    plt.figure(figsize=(10, 6))
    plt.plot(t, voltages, label='Original Signal')
    plt.plot(t, filtered_data, label='Filtered Signal')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.title('Low-Pass Filtering Example')
    plt.legend()
    plt.grid(True)
    plt.show()


def hilbert_transform(signal):
    signal=np.array(signal)
    average=np.mean(signal)
    analytic_signal = hilbert(signal-average)
    envelope = np.abs(analytic_signal)+average
    return analytic_signal,envelope

def plot_onlyfiltered(t,filteredv,file=None,order=2,info=None,save=False):
    fig,ax=plt.subplots()
    ax.plot(t,filteredv,label=f"Filtered")
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Membrane Potential (mV)")
    ax.legend()
    title=f"Filtered response_{order}_{info}"
    ax.set_title(title)
    plt.show()
    if save:
        saveplot(file,title,fig)
