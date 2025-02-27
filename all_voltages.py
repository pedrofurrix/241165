import os
from neuron import h
import csv
import numpy as np
import h5py

def record_voltages(cell,e_dir):

    path=os.path.join(e_dir,f"run_voltages.csv")
    file= open(path,'w',newline='')
    writer = csv.writer(file)
    # Write header row with time and segment indexes
    # header = ["t"] + [f"{sec.name()}({i})" for sec in cell.all for i, _ in enumerate(sec)]
    header= ["t"] + [f"{seg}" for sec in cell.all for seg in sec]
    writer.writerow(header)

    def sum_voltages():
        current_voltages = [h.t] + [seg.v for sec in cell.all for seg in sec]
        writer.writerow(current_voltages) # Use writerow for single list
            
    callback=h.beforestep_callback(cell.soma[0](0.5))
    callback.set_callback(sum_voltages)

    return file,callback

def custom_threshold(cell,cell_id,freq,modfreq,depth,theta,phi, segments,var,max_timesteps = 100000, buffer_size=10000,save=False,data_dir=os.getcwd()):
    
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

    mapping = {
    "cfreq": freq,
    "modfreq": modfreq,
    "theta": theta,
    "phi": phi,
    "depth": depth
    }
    condition = mapping.get(var)  # Returns None if var is not in the dictionary

    # Define the path for the HDF5 file
    folder=os.path.join(data_dir,"data",str(cell_id),str(var),"threshold",f"{condition}")

    if not os.path.exists(folder):
        os.makedirs(folder)

    if save:
        path = os.path.join(folder, "run_voltages.h5")
        file = h5py.File(path, "w")

        # Create datasets
        max_timesteps = max_timesteps  # Preallocate for a large number of timesteps (adjust as needed)
        is_xtra_ds = file.create_dataset("is_xtra", shape=(max_timesteps,), maxshape=(None,), dtype='f8', chunks=True)
        time_dset = file.create_dataset("time", shape=(max_timesteps,), maxshape=(None,), dtype="f")
        voltages_dset = file.create_dataset(
            "voltages",
            shape=(max_timesteps, len(segments)),
            maxshape=(None, len(segments)),
            dtype="f",
            compression="gzip",
        )

        # Store segment names as an attribute
        segment_names = [f"{seg}" for seg in segments]
        voltages_dset.attrs["segment_names"] = segment_names

        # Buffer for storing data in memory
        time_buffer = np.zeros(buffer_size, dtype="f")
        voltages_buffer = np.zeros((buffer_size, len(segments)), dtype="f")
        is_buffer= np.zeros(buffer_size, dtype="f")

        buffer_index = 0  # Tracks the current position in the buffer
        voltages=voltages_buffer
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
                    is_xtra_ds.resize((new_size,))
                    voltages_dset.resize((new_size, len(segments)))

                # Write data from the buffer
                time_dset[total_timesteps:total_timesteps + buffer_index] = time_buffer[:buffer_index]
                voltages_dset[total_timesteps:total_timesteps + buffer_index, :] = voltages_buffer[:buffer_index, :]
                is_xtra_ds[total_timesteps:total_timesteps + buffer_index]  = is_buffer[:buffer_index]

                
                # Update the total number of timesteps and reset the buffer index
                total_timesteps += buffer_index
                buffer_index = 0

        def record_step():
            """Record the current time and voltages to the buffer."""
            nonlocal buffer_index
            
            # Store the current time and voltages in the buffer
            time_buffer[buffer_index] = h.t
            is_buffer[buffer_index]= h.stim_xtra
            voltages_buffer[buffer_index, :] = [seg.v for seg in segments]
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
    else:
        
        voltages=np.zeros((max_timesteps, len(segments)), dtype="f")
        index=0
        def every_tstep():
            nonlocal index
            voltages[:, index] = [seg.v for seg in segments]
            index+=1
    
        callback = h.beforestep_callback(cell.soma[0](0.5))
        callback.set_callback(every_tstep)
        file=None
        folder=None
        def finalize():
            return

    # Return the file object and a finalize function
    return folder,file, callback, voltages, finalize