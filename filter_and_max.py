import os
import h5py
import json
import pandas as pd
from scipy.signal import butter, filtfilt
from scipy.fft import fft, rfft
from scipy.fft import fftfreq, rfftfreq
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from scipy.stats import trim_mean
import re

from savedata import saveplot

# Get folder
def get_folder(CF,E,cell_id,var,filtered=False,data_dir=os.getcwd()):
    top_dir=os.path.join(data_dir,"data",str(cell_id),str(var),f"{CF}Hz")
    param_dir=os.path.join(top_dir,f"{E}Vm")
    if not filtered:
        bot_dir=param_dir
    else:
        bot_dir=os.path.join(param_dir,"filtered")
        if not os.path.exists(bot_dir):
            os.makedirs(bot_dir)
    print(top_dir)
    print(bot_dir)
    
    return top_dir, bot_dir, param_dir

# Load HDF5 data
def load_voltages_hdf5(bot_dir):
    filepath = os.path.join(bot_dir, "run_voltages.h5")
    with h5py.File(filepath, "r") as file:
        time = file["time"][:]
        voltages = file["voltages"][:]
        segment_names = file["voltages"].attrs["segment_names"]
    return time, voltages, segment_names


def load_params(param_dir): #Load paramsssssssss (get them into a format where I can easily extract them.., ) - json
    '''
    Loads parameters - from json
    '''
    filename="params.json"
    path = os.path.join(param_dir, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"The parameters file does not exist at {path}")
    # Load the JSON file
    with open(path, "r") as file:
        params = json.load(file)
    # Extract simulation and stimulation parameters
    simparams = params["Simulation Parameters"]
    stimparams = params["Stimulation Parameters"]
    # Return the parameters
    return simparams, stimparams


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
    print(f"Low pass filter of order:{order*2} and with a cutoff:{cutoff} applied to the data successfully")
    return filtered_data

def subsample_data(data, original_fs, target_fs):
    """
    Subsample the data to achieve the target sampling rate.

    Args:
        data: NumPy array of the data to be subsampled.
        original_fs: Original sampling frequency in Hz.
        target_fs: Target sampling frequency in Hz.

    Returns:
        subsampled_data: NumPy array of the subsampled data.
        subsampled_time: NumPy array of the corresponding time points.
    """
    subsample_factor = int(original_fs / target_fs)
    subsampled_data = data[::subsample_factor]
    return subsampled_data

def butter_bandpass(lowcut, highcut, fs, order=3):
    nyquist=0.5*fs
    low = lowcut / nyquist
    high = highcut / nyquist
    # Ensure frequencies are valid
    if not (0 < low < 1 and 0 < high < 1):
        raise ValueError(f"Cutoff frequencies must be within (0, Nyquist). Got low={lowcut}, high={highcut}, fs={fs}.")
    
    b,a=butter(order, [low, high], btype='band', analog=False)
    return b,a
    
def butter_bandpass_filter(signal, fs, modfreq=10,lowcut=None, highcut=None,order=3):
    if lowcut is None:
        lowcut=0.7*modfreq
    if highcut is None:
        highcut = 1.3 * modfreq
    
    b, a = butter_bandpass(lowcut, highcut, fs, order)

    #Add Padding
    pad_len = max(len(b), len(a)) * 3  # Safe padding
    padded_signal = np.pad(signal, (pad_len, pad_len), mode="reflect")
    filtered = filtfilt(b, a, padded_signal)[pad_len:-pad_len]
    # filtered = filtfilt(b, a, signal)
    # filtered = filtfilt(b, a, signal)
    return filtered,highcut,lowcut

def filter_voltages(voltages, segment_names, time, fs, modfreq,bp=False, lowcut=None, highcut=None, order_low=3,order_bp=3,cutoff=100,target_fs=1000,cutoff_dc=2):
    
    # Filter the voltages on-the-fly
    filtered_voltages = []
    for i, segment_name in enumerate(segment_names):
        v = voltages[:, i] - voltages[0, i]  # Zero baseline
        filtered_v = butter_lowpass_filter(v, cutoff, fs, order_low)

        if bp:
            subsampled=subsample_data(filtered_v,fs,target_fs)
            dc_v=butter_lowpass_filter(subsampled,cutoff_dc,target_fs,order=4)
            filtered_v,highcut,lowcut = butter_bandpass_filter(subsampled, target_fs, modfreq, lowcut, highcut, order_bp)
    
        filtered_voltages.append(filtered_v)
    if bp:
        time = subsample_data(time, fs, target_fs)
    filtered_voltages = np.array(filtered_voltages).T
    return filtered_voltages,time,highcut,lowcut


def save_filterparams(output_dir,highcut,lowcut,order_low,order_bp,bp,target_fs,cutoff):
    """
        Save filter parameters to a JSON file.
    
         rgs:
        output_dir (str): Directory to save the parameters file.
        filter_order (int): The order of the filter.
        cutoff_freq (float): The cutoff frequency of the filter.
    """
    # Define the file path for the parameters file
    params_file = os.path.join(output_dir, "filter_parameters.json")
    
    # Create a dictionary of parameters
    parameters = {
        "Low pass filter_order": order_low*2,
        "Cutoff LP": cutoff,
        "BandPass": bp,
        "Order BP": order_bp*2,
        "High Cut": highcut,
        "Low Cut": lowcut,
        "Target Fs":target_fs
          }
    
     # Save the dictionary to a JSON file
    with open(params_file, "w") as file:
        json.dump(parameters, file, indent=4)
    print(f"Filter parameters saved to {params_file}")

def analyze_shifts(CF,E,cell_id,var="cfreq",data_dir=os.getcwd(),voltages=None, time=None,segment_names=None, 
                   filtered=False,cutoff=200,highcut=None, order_low=4, order_bp=3, lowcut=None, bp=False, modfreq=10,target_fs=1000):

    top_dir,bot_dir,param_dir=get_folder(CF,E,cell_id,var,filtered,data_dir)

    if voltages is None:
        time, voltages, segment_names=load_voltages_hdf5(param_dir)
    
    if filtered:
        dt = time[1] - time[0]
        fs = 1 / (dt / 1000)    
        voltages,time,highcut,lowcut=filter_voltages(voltages, segment_names, time,fs, modfreq,bp, lowcut, highcut, order_low=order_low,order_bp=order_bp,cutoff=cutoff,target_fs=target_fs)
        save_filterparams(bot_dir,highcut,lowcut,order_low,order_bp,bp,target_fs,cutoff)
        print(time)

    # Analyze max_shift
    simparams, stimparams = load_params(param_dir)
    v_init = voltages[0, :].tolist()
    start_time=stimparams["RUp Duration"]+100
    if start_time is not None:
        valid_indices = time >= start_time
        time = time[valid_indices]
        voltages = voltages[valid_indices, :]
    max_v = voltages.max(axis=0).tolist()
    min_v = voltages.min(axis=0).tolist()
    if not filtered:
        pshift = [max_v[i] - v_init[i] for i in range(len(segment_names))]
        nshift = [min_v[i] - v_init[i] for i in range(len(segment_names))]
        max_shift = [max(p, n, key=abs) for p, n in zip(pshift, nshift)]
    else:
        pshift = max_v
        nshift = min_v
        max_shift = [max(p, n, key=abs) for p, n in zip(pshift, nshift)]
        

    # Create results
    results = {
        "EValue": stimparams["E"],
        "CFreq": stimparams["Carrier Frequency"],
        "ModFreq": stimparams["Modulation Frequency"],
        "max_shiftp": max(pshift),
        "min_shiftp": min(pshift),
        "max_shiftn": max(nshift, key=abs),
        "min_shiftn": min(nshift, key=abs),
        "maxp_index": pshift.index(max(pshift)),
        "minp_index": pshift.index(min(pshift)),
        "maxn_index": nshift.index(max(nshift, key=abs)),
        "minn_index": nshift.index(min(nshift, key=abs)),
        "maxp_seg": segment_names[pshift.index(max(pshift))],
        "minp_seg": segment_names[pshift.index(min(pshift))],
        "maxn_seg": segment_names[nshift.index(max(nshift, key=abs))],
        "minn_seg": segment_names[nshift.index(min(nshift, key=abs))]
    }

    # Save the results obtained into files.
    def save_max():
        data={
            "seg" : segment_names,
            "max_v" : max_v,
            "min_v" : min_v,
            "max_shift" : max_shift,
            "pshift" : pshift,
            "nshift" : nshift
        }
        # Save the data
        out_file=os.path.join(bot_dir,"max_shift_data.csv")
        data_pd=pd.DataFrame([data])
        data_pd.to_csv(out_file,index=False)

    if filtered:
            top_file=os.path.join(top_dir, "results_summary_filtered.csv")
            results_df = pd.DataFrame([results])
    else:
        top_file=os.path.join(top_dir, "results_summary.csv")
        results_df = pd.DataFrame([results])

    if os.path.exists(top_file):
        # If file exists, append the new results without writing the header
        results_df.to_csv(top_file, mode='a', index=False, header=False)
        print(f"Results summary saved to {top_file}")
    else:
        # If file does not exist, write the results with the header
        results_df.to_csv(top_file, index=False, header=True)
        print(f"Results summary saved to {top_file}")

    save_max()
    
    vmaxp=plot_max(bot_dir,results,voltages,time)


    return max_shift, max_v, min_v, results


def plot_max(bot_dir,results,voltages,time,filtered=False):
    v_maxp_index=results["maxp_index"]
    vmaxp=voltages[:,v_maxp_index]
    segmaxp=results["maxp_seg"]

    # Plot Max both
    fig3,ax3=plt.subplots()
    title3=("Membrane potential over time - Maxshift")
    ax3.plot(time, vmaxp,label=f"maxp_shift_{segmaxp}")
    ax3.set_xlabel("time (ms)")  # Correct method to set labels
    ax3.set_ylabel("Membrane potential (mV)")
    ax3.legend()
    ax3.set_title(title3)  # Optional: add title to the plot

    def saveplot(bot_dir,title,fig_or_ax):
        filename=f"{title}.png"

        if isinstance(fig_or_ax, plt.Axes):
            # If it's an Axes object, get the Figure from the Axes
            fig = fig_or_ax.get_figure()
        elif isinstance(fig_or_ax, plt.Figure):
            # If it's already a Figure, use it as is
            fig = fig_or_ax
        else:
            raise TypeError("Input must be a matplotlib Figure or Axes object.")
        
        path=os.path.join(bot_dir,filename)
        
        fig.savefig(path, dpi=300, bbox_inches='tight')
        
        print(f"Successfully saved as {filename}")
    saveplot(bot_dir,title3,fig3)
    plt.close(fig3)
    return vmaxp

def plot_filtered(bot_dir,results,voltages,time,filtered=False):
    return None

# Building a class Fourier for better use of Fourier Analysis.
class Fourier:
    """
    Apply the Discrete Fourier Transform (DFT) on the signal using the Fast Fourier 
    Transform (FFT) from the scipy package.

    Example:
        fourier = Fourier(signal, sampling_rate=2000.0)
    """
  
    def __init__(self, signal,dt=0.001,start_time=0,modfreq=10):
        """
        Initialize the Fourier class.

        Args:
            signal (np.ndarray): The samples of the signal.
            dt (float): Time step of the signal in seconds. Default is 0.001 (1 ms).
            start_time (float): Time in seconds to start analyzing the signal. Default is 0.0.

        Additional parameters:
            sampling_rate (float): The sampling rate in Hz.
            duration (float): The duration of the signal in seconds.
            time_axis (np.ndarray): Time axis of the filtered signal (after start_time).
            frequencies (np.ndarray): Frequency axis for Fourier analysis.
            fourier (np.ndarray): Fourier transform of the filtered signal.
        """
        self.original_signal = signal
        self.sampling_rate = 1 / (dt / 1000)  # Hz
        self.time_step = dt / 1000
        self.start_time = start_time
        self.modfreq=modfreq

        # Calculate time axis for the original signal
        self.original_duration = len(signal) / self.sampling_rate
        self.original_time_axis = np.arange(0, self.original_duration, self.time_step)
        
        # Filter the signal based on start_time
        start_index = int(self.start_time/1000 * self.sampling_rate)
        self.signal = signal[start_index:]
        self.time_axis = self.original_time_axis[start_index:]
        self.ac = self.signal - np.mean(self.signal)

        self.dc=signal[start_index:]-signal[0]
    
        # Update duration, frequencies, and Fourier transform
        self.duration = len(self.signal) / self.sampling_rate
        self.frequencies = rfftfreq(len(self.signal), d=self.time_step)
        self.fourier = rfft(self.ac)

        
    

  # Generate the actual amplitudes of the spectrum
    def amplitude(self):
        """
        Method of Fourier

        Returns:
            numpy.ndarray of the actual amplitudes of the sinusoids.
        """

        return 2*np.abs(self.fourier)/len(self.signal)
    
    def powermod(self):
        """
        Method of Fourier

        Returns:
            numpy.ndarray of the actual amplitudes of the sinusoids.
        """
        # Create a frequency mask for the modulation band
        freqmask = (self.frequencies >= 0.7 * self.modfreq) & (self.frequencies <= 1.3 * self.modfreq)
        mod_power=sum(self.amplitude()[freqmask]**2)
        total_power = np.sum(self.amplitude() ** 2)
        # Normalize modulation power
        normalized_power = mod_power / total_power

        return mod_power, normalized_power
    
    def dc_power(self):
        freqmask=self.frequencies==0
        mod_power=sum(self.amplitude()[freqmask]**2)
        total_power = np.sum(self.amplitude() ** 2)
        # Normalize modulation power
        normalized_power = mod_power / total_power

        return mod_power, normalized_power

    # Generate the phase information from the output of rfft  
    def phase(self, degree = False):
        """
        Method of Fourier

        Args:
            degree: To choose the type of phase representation (Radian, Degree).
                    By default, it's in radian. 

        Returns:
            numpy.ndarray of the phase information of the Fourier output.
        """
        return np.angle(self.fourier, deg = degree)

    def plot_spectrum(self, interactive=False, max_freq=None, line_color='blue', line_width=2):
        """
        Plot the spectrum (Frequency Domain) of the signal.

        Args:
            interactive (bool): If True, creates an interactive plot using Plotly.
            max_freq (float): Maximum frequency to display in the spectrum. If None, displays all.
            line_color (str): Color of the spectrum line.
            line_width (float): Width of the spectrum line.

        Returns:
            None
        """
        if max_freq is not None:
            freq_mask = self.frequencies <= max_freq
            freqs_to_plot = self.frequencies[freq_mask]
            amps_to_plot = self.amplitude()[freq_mask]
        else:
            freqs_to_plot = self.frequencies
            amps_to_plot = self.amplitude()


        if interactive:
            trace = go.Scatter(
                x=freqs_to_plot,
                y=amps_to_plot,
                mode='lines',
                line=dict(color=line_color, width=line_width),
                name="Spectrum"
            )
            layout = go.Layout(
                title=dict(
                    text='Spectrum',
                    x=0.5,
                    xanchor='center',
                    yanchor='top',
                    font=dict(size=25, family='Arial, bold')
                ),
                xaxis=dict(title='Frequency [Hz]'),
                yaxis=dict(title='Amplitude')
            )
            fig = go.Figure(data=[trace], layout=layout)
            fig.show()
        else:
            fig, ax = plt.subplots(figsize=(10, 6))            
            ax.plot(freqs_to_plot, amps_to_plot, color=line_color, linewidth=line_width)
            # Set titles and labels
            ax.set_title('Spectrum', fontsize=16)
            ax.set_xlabel('Frequency [Hz]', fontsize=14)
            ax.set_ylabel('Amplitude', fontsize=14)
            # Customize ticks
            ax.tick_params(axis='both', which='major', labelsize=12)
            # Add grid for better readability
            ax.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            return fig
        return fig
  
    def plot_time_frequency(self, max_freq=None, t_ylabel="Amplitude", f_ylabel="Amplitude",
                            t_title="Signal (Time Domain)", f_title="Spectrum (Frequency Domain)",
                            line_color='blue', line_width=2):
        """
        Plot the signal in both time domain and frequency domain.

        Args:
            max_freq (float): Maximum frequency to display in the spectrum. If None, displays all.
            t_ylabel (str): Y-axis label for the time-domain plot.
            f_ylabel (str): Y-axis label for the frequency-domain plot.
            t_title (str): Title for the time-domain plot.
            f_title (str): Title for the frequency-domain plot.
            line_color (str): Color of the spectrum line.
            line_width (float): Width of the spectrum line.

        Returns:
            None
        """

        if max_freq is not None:
            freq_mask = self.frequencies <= max_freq
            freqs_to_plot = self.frequencies[freq_mask]
            amps_to_plot = self.amplitude()[freq_mask]
        else:
            freqs_to_plot = self.frequencies
            amps_to_plot = self.amplitude()


        # Time-domain plot
        time_trace = go.Scatter(
            x=self.time_axis,
            y=self.signal,
            mode='lines',
            line=dict(color='red', width=line_width),
            name="Time Domain"
        )

        time_layout = go.Layout(
            title=dict(
                text=t_title,
                x=0.5,
                xanchor='center',
                yanchor='top',
                font=dict(size=25, family='Arial, bold')
            ),
            xaxis=dict(title='Time [sec]'),
            yaxis=dict(title=t_ylabel),
            width=1000,
            height=400
        )
        time_fig = go.Figure(data=[time_trace], layout=time_layout)
        time_fig.show()

        # Frequency-domain plot
        freq_trace = go.Scatter(
            x=freqs_to_plot,
            y=amps_to_plot,
            mode='lines',
            line=dict(color=line_color, width=line_width),
            name="Frequency Domain"
        )
        freq_layout = go.Layout(
            title=dict(
                text=f_title,
                x=0.5,
                xanchor='center',
                yanchor='top',
                font=dict(size=25, family='Arial, bold')
            ),
            xaxis=dict(title='Frequency [Hz]'),
            yaxis=dict(title=f_ylabel),
            width=1000,
            height=400
        )
        freq_fig = go.Figure(data=[freq_trace], layout=freq_layout)
        freq_fig.show()
        return time_fig,freq_fig
  
    def plot_save(self,fig,title,e_dir):
        saveplot(e_dir,title,fig)

def analyze_fourier_power(CF,E,cell_id,var,filtered=False,data_dir=os.getcwd(),voltages=None,
                          segment_names=None, dt=0.001, modfreq=10):
    
    top_dir,bot_dir,param_dir=get_folder(CF,E,cell_id,var,filtered,data_dir)
    simparams, stimparams = load_params(param_dir)
    start_time=stimparams["RUp Duration"]+100
    """
    Analyze Fourier power and save the results to a CSV file.

    Args:
        voltages (pd.DataFrame): Voltages for all segments (time x segments).
        segment_names (list): Names of the segments.
        fs (float): Sampling frequency in Hz.
        modfreq (float): Modulation frequency for power calculation.
        output_dir (str): Directory to save the CSV file.

    Returns:
        dict: Contains maximum power, maximum normalized power, and corresponding segments.
    """
    if voltages is None:
        time, voltages, segment_names=load_voltages_hdf5(bot_dir)

    results = []

    for i, segment_name in enumerate(segment_names):
        # Extract voltage data for the segment
        signal = voltages[:, i]

        # Initialize Fourier class
        fourier = Fourier(signal, dt=dt, modfreq=modfreq,start_time=start_time)

        # Calculate modulation power and normalized power
        mod_power, normalized_power = fourier.powermod()

        # Append results for this segment
        results.append({
            "Segment": segment_name,
            "Modulation Power": mod_power,
            "Normalized Power": normalized_power
        })

    # Convert results to DataFrame
    results_df = pd.DataFrame(results)

    # Identify maximum power and maximum normalized power
    max_power_row = results_df.loc[results_df["Modulation Power"].idxmax()]
    max_norm_power_row = results_df.loc[results_df["Normalized Power"].idxmax()]

    # Add maximum power and normalized power to the result dictionary
    summary = {
        "EValue": stimparams["E"],
        "CFreq": stimparams["Carrier Frequency"],
        "ModFreq": stimparams["Modulation Frequency"],
        "Max Power": max_power_row["Modulation Power"],
        "Max P Norm": max_power_row["Normalized Power"],
        "Max Power Segment": max_power_row["Segment"],
        "Max Norm": max_norm_power_row["Normalized Power"],
        "Max Norm Power": max_norm_power_row["Modulation Power"],
        "Max Normalized Power Segment": max_norm_power_row["Segment"]
    }

    if filtered:
            top_file=os.path.join(top_dir, "FT_filtered.csv")
            results_df = pd.DataFrame([results])
    else:
        top_file=os.path.join(top_dir, "FT_power.csv")
        summary_df = pd.DataFrame([summary])

    if os.path.exists(top_file):
        # If file exists, append the new results without writing the header
        summary_df.to_csv(top_file, mode='a', index=False, header=False)
    else:
        # If file does not exist, write the results with the header
        summary_df.to_csv(top_file, index=False, header=True)

    # Save the results to a CSV file
    output_file = os.path.join(bot_dir, "fourier_power_analysis.csv")
    results_df.to_csv(output_file, index=False)


    print(f"Fourier power analysis saved to {output_file}")

    return summary

def analyze_fourier_averages(CF,E,cell_id,var,filtered=False,data_dir=os.getcwd()):
    """
    Load and summarize Fourier power data from a given directory structure.
    
    Args:
        cell_id: Identifier for the cell.
        var: The variable of interest ("cfreq" or "modfreq").
        filtered: Whether to load filtered data.
    
    Returns:
        summary_df: DataFrame summarizing Fourier power.
        top_dir: Top-level directory where the data was loaded from.
    """
    top_dir, bot_dir, param_dir=get_folder(CF,E,cell_id,var,data_dir=data_dir)
 
    average_file = os.path.join(top_dir, "average_fourier.csv")

    # Initialize an empty dictionary to store Fourier power data
    fourier_data = {}
    fourier_norm={}

    for folder_name in os.listdir(top_dir):
        # Construct the full path
        folder_path = os.path.join(top_dir, folder_name)

        # Check if it's a directory
        if os.path.isdir(folder_path):
            print(f"Processing folder: {folder_name}")

            # Extract the number (digits) from the folder name
            match = re.search(r"\d+", folder_name)
            if match:
                evalue = int(match.group())  # Convert to integer

            results_file = os.path.join(folder_path, "fourier_power_analysis.csv")           
            if os.path.exists(results_file):
                # Load the Fourier summary file
                data = pd.read_csv(results_file)
        
                norm_power=data["Normalized Power"].tolist()
                fourier_power=data["Modulation Power"].tolist()
                
                # Calculate the trimmed mean (removes lowest and highest 5%)
                norm_avg = trim_mean(norm_power, proportiontocut=0.05)
                fourier_avg = trim_mean(fourier_power, proportiontocut=0.05)
                summary = {
                        "EValue": evalue,
                        "CFreq": CF,
                        "power":fourier_avg,
                        "norm":norm_avg,
                }
                top_file=average_file
                summary_df = pd.DataFrame([summary])
                if os.path.exists(top_file):
                    # If file exists, append the new results without writing the header
                    summary_df.to_csv(top_file, mode='a', index=False, header=False)
                else:
                    # If file does not exist, write the results with the header
                    summary_df.to_csv(top_file, index=False, header=True)