import os
import h5py
import numpy as np
from neuron import h

def record_voltages_hdf5(cell, e_dir):
    # Define the path for the HDF5 file
    path = os.path.join(e_dir, "run_voltages.h5")
    file = h5py.File(path, "w")

    # Create datasets
    num_segments = len([seg for sec in cell.all for seg in sec])  # Total number of segments
    max_timesteps = 100000 # Preallocate space for a large number of timesteps (adjust as needed)
    time_dset = file.create_dataset("time", shape=(max_timesteps,), maxshape=(None,), dtype="f")
    voltages_dset = file.create_dataset(
        "voltages",
        shape=(max_timesteps, num_segments),
        maxshape=(None, num_segments),
        dtype="f",
        compression="gzip",
    )

    # Store segment names as an attribute
    segment_names = [f"{seg}" for sec in cell.all for seg in sec]
    voltages_dset.attrs["segment_names"] = segment_names

    # Record data dynamically
    current_index = [0]  # Use a mutable list to allow closure to modify it

    def sum_voltages():
        # Collect current time and voltages
        if current_index[0] >= voltages_dset.shape[0]:
            # Expand datasets if needed
            new_size = voltages_dset.shape[0] + 10  # Expand in chunks of 10 # If I want to stimulate for more time, change this...

            time_dset.resize((new_size,))
            voltages_dset.resize((new_size, num_segments))

        time_dset[current_index[0]] = h.t
        voltages_dset[current_index[0], :] = [seg.v for sec in cell.all for seg in sec]
        current_index[0] += 1

    # Set up the callback
    callback = h.beforestep_callback(cell.soma[0](0.5))
    callback.set_callback(sum_voltages)

    return file, callback

def record_voltages_numpy(cell, e_dir):
    # Define paths
    path = os.path.join(e_dir, "run_voltages.npz")
    
    # Prepare to store data in memory first
    data = {
        "time": [],
        "voltages": [],
        "segment_names": [f"{seg}" for sec in cell.all for seg in sec],
    }

    def sum_voltages():
        # Collect current time and voltages
        data["time"].append(h.t)
        data["voltages"].append([seg.v for sec in cell.all for seg in sec])

    # Set up the callback
    callback = h.beforestep_callback(cell.soma[0](0.5))
    callback.set_callback(sum_voltages)

    def save_data():
        # Save data to disk in compressed format
        np.savez_compressed(path, **data)
        print(f"Data saved to {path}")

    return save_data, callback