import os
import h5py
import numpy as np
from neuron import h

def record_voltages_hdf5(cell, e_dir,max_timesteps = 100000, buffer_size=10000):
    
    """
    Efficiently record voltages from a neuron simulation to an HDF5 file.
    
    Args:
        cell: The NEURON cell object.
        e_dir: Directory to store the HDF5 file.
        buffer_size: Number of timesteps to store in memory before writing to disk.
    
    Returns:
        file: The HDF5 file object.
        flush_callback: The callback for flushing data to disk.
    """
    
    # Define the path for the HDF5 file
    path = os.path.join(e_dir, "run_voltages.h5")
    file = h5py.File(path, "w")

    # Create datasets
    num_segments = len([seg for sec in cell.all for seg in sec])  # Total number of segments
    max_timesteps = max_timesteps  # Preallocate for a large number of timesteps (adjust as needed)
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

    # Buffer for storing data in memory
    time_buffer = np.zeros(buffer_size, dtype="f")
    voltages_buffer = np.zeros((buffer_size, num_segments), dtype="f")
    buffer_index = 0  # Tracks the current position in the buffer

    # Index for tracking the total number of written timesteps
    total_timesteps = 0

    def flush_to_disk():
        """Flush the buffer to the HDF5 file."""
        nonlocal buffer_index, total_timesteps
        
        # If the buffer has data, write it to the datasets
        if buffer_index > 0:
            # Resize datasets if needed
            if total_timesteps + buffer_index > voltages_dset.shape[0]:
                new_size = voltages_dset.shape[0] + buffer_index #max_timesteps
                time_dset.resize((new_size,))
                voltages_dset.resize((new_size, num_segments))

            # Write data from the buffer
            time_dset[total_timesteps:total_timesteps + buffer_index] = time_buffer[:buffer_index]
            voltages_dset[total_timesteps:total_timesteps + buffer_index, :] = voltages_buffer[:buffer_index, :]
            
            # Update the total number of timesteps and reset the buffer index
            total_timesteps += buffer_index
            buffer_index = 0

    def record_step():
        """Record the current time and voltages to the buffer."""
        nonlocal buffer_index
        
        # Store the current time and voltages in the buffer
        time_buffer[buffer_index] = h.t
        voltages_buffer[buffer_index, :] = [seg.v for sec in cell.all for seg in sec]
        buffer_index += 1

        # Flush to disk if the buffer is full
        if buffer_index >= buffer_size:
            flush_to_disk()

    # Callback to record voltages at each timestep
    callback = h.beforestep_callback(cell.soma[0](0.5))
    callback.set_callback(record_step)

    def finalize():
        """Flush remaining data in the buffer to disk and close the file."""
        flush_to_disk()
        file.close()

    # Return the file object and a finalize function
    return file, callback, finalize

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