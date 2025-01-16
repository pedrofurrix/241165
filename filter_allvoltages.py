import os
import h5py
import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt
import json


def lowpass_filter(data, cutoff, fs, order):
    """
    Apply a low-pass Butterworth filter.
    
    Args:
        data (array-like): The input signal.
        cutoff (float): The cutoff frequency of the filter (Hz).
        fs (float): The sampling frequency of the signal (Hz).
        order (int): The order of the filter.
        
    Returns:
        filtered_data (array): The filtered signal.
    """
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype="low", analog=False)
    filtered_data = filtfilt(b, a, data)
    return filtered_data

def filter_and_save_voltages(bot_dir, cutoff_freq=100,order=4):
    """
    Apply a low-pass filter to the voltages in an HDF5 file and save the filtered data to a new file.
    
    Args:
        input_dir (str): Directory containing the input HDF5 file.
        output_dir (str): Directory to save the filtered HDF5 file.
        cutoff_freq (float): Cutoff frequency for the low-pass filter (Hz).
        sampling_rate (float): Sampling frequency of the data (Hz).
    """
    # Load the input HDF5 file
    input_file = os.path.join(bot_dir, "run_voltages.h5")
    output_path = os.path.join(bot_dir,"filtered")

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    output_file = os.path.join(output_path, f"filtered_voltages.h5")
    
    with h5py.File(input_file, "r") as infile, h5py.File(output_file, "w") as outfile:
        # Read time and voltages
        time = infile["time"][:]
        voltages = infile["voltages"][:]
        segment_names = infile["voltages"].attrs["segment_names"]
        dt=time[1]-time[0] #dt ms
        fs=1/(dt/1000) # Hz
        # Create datasets for filtered data
        num_timesteps, num_segments = voltages.shape
        filtered_voltages = outfile.create_dataset(
            "filtered_voltages",
            shape=(num_timesteps, num_segments),
            dtype="f",
            compression="gzip",
        )
        outfile.create_dataset("time", data=time, dtype="f")
        filtered_voltages.attrs["segment_names"] = segment_names
        
        # Apply the low-pass filter to each segment
        for i, segment_name in enumerate(segment_names):
            print(f"Filtering segment {segment_name} ({i+1}/{num_segments})...")
            filtered_data = lowpass_filter(voltages[:, i], cutoff_freq, fs,order)
            filtered_voltages[:, i] = filtered_data
        
        print(f"Filtered data saved to {output_file}")
    save_filterparams(output_path,cutoff_freq,order)

def save_filterparams(output_dir,cutoff_freq,order):
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
        "filter_order": order,
        "cutoff_frequency": cutoff_freq
          }
    
     # Save the dictionary to a JSON file
    with open(params_file, "w") as file:
        json.dump(parameters, file, indent=4)
    print(f"Filter parameters saved to {params_file}")