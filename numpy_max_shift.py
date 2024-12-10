import os
import numpy as np
import pandas as pd

def load_voltages_numpy(bot_dir):
    """
    Load voltage data saved in compressed numpy format (.npz) by record_voltages_numpy.
    
    Parameters:
    bot_dir (str): Directory containing the .npz file.

    Returns:
    tuple: (voltages, segment_names, time)
        - voltages: 2D NumPy array of shape (time_points, num_segments).
        - segment_names: List of segment names corresponding to the columns in voltages.
        - time: 1D NumPy array of time points.
    """
    vfile = os.path.join(bot_dir, "run_voltages.npz")
    if not os.path.exists(vfile):
        raise FileNotFoundError(f"Voltage file not found at {vfile}")

    # Load data from npz file
    with np.load(vfile) as data:
        voltages = np.array(data["voltages"])  # Voltage data as a 2D array
        segment_names = list(data["segment_names"])  # Segment names as a list
        time = np.array(data["time"])  # Time points as a 1D array

    return voltages, segment_names, time

def cmax_shift_numpy(bot_dir, top_dir, cell=None):
    """
    Calculate shifts based on voltage data saved as a NumPy array.

    Parameters:
    bot_dir (str): Directory containing voltage data (.npz file).
    top_dir (str): Directory for saving results.
    cell (object, optional): Neuron cell object for segment information.

    Returns:
    tuple: (max_shift, max_v, min_v, results)
    """
    # Load data from npz file
    voltages, segment_names, time = load_voltages_numpy(bot_dir)

    num_seg = voltages.shape[1]
    v_init = voltages[0, :]  # Initial voltage (first time point)

    # Segment list and tracking variables
    if cell:
        segments = [seg for sec in cell.all for seg in sec]
    else:
        segments = range(num_seg)

    max_shift = [0] * len(segments)
    max_v = [v_init[i] for i in range(len(segments))]
    min_v = [v_init[i] for i in range(len(segments))]
    pshift = [0] * len(segments)
    nshift = [0] * len(segments)

    results = {
        "EValue": "Not available",  # Update with actual value if needed
        "CFreq": "Not available",  # Update with actual value if needed
        "max_shiftp": -1e5,
        "min_shiftp": 1e5,
        "max_shiftn": 0,
        "min_shiftn": 0,
        "maxp_seg": None, 
        "minp_seg": None,
        "maxn_seg": None,  
        "minn_seg": None,
        "maxp_sec": None,  
        "minp_sec": None,
        "maxn_sec": None,  
        "minn_sec": None
    }

    # Max and min calculations
    max_v = voltages.max(axis=0).tolist()  # Maximum across time for each segment
    min_v = voltages.min(axis=0).tolist()  # Minimum across time for each segment

    pshift = [max_v[i] - v_init[i] for i in range(len(segments))]
    nshift = [min_v[i] - v_init[i] for i in range(len(segments))]
    max_shift = [max(p, n, key=abs) for p, n in zip(pshift, nshift)]

    results["max_shiftp"] = max(pshift)
    results["min_shiftp"] = min(pshift)
    results["max_shiftn"] = max(nshift, key=abs)
    results["min_shiftn"] = min(nshift, key=abs)
    results["maxp_index"] = np.argmax(pshift)
    results["minp_index"] = np.argmin(pshift)
    results["maxn_index"] = np.argmax(np.abs(nshift))
    results["minn_index"] = np.argmin(np.abs(nshift))
    results["maxp_seg"] = segment_names[results["maxp_index"]]
    results["minp_seg"] = segment_names[results["minp_index"]]
    results["maxn_seg"] = segment_names[results["maxn_index"]]
    results["minn_seg"] = segment_names[results["minn_index"]]

    if cell:
        results["maxp_seg"] = segments[results["maxp_index"]]
        results["minp_seg"] = segments[results["minp_index"]]
        results["maxn_seg"] = segments[results["maxn_index"]]
        results["minn_seg"] = segments[results["minn_index"]]
        results["maxp_sec"] = results["maxp_seg"].sec
        results["minp_sec"] = results["minp_seg"].sec
        results["maxn_sec"] = results["maxn_seg"].sec
        results["minn_sec"] = results["minn_seg"].sec
    
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

        top_file=os.path.join(top_dir, "results_summary.csv")
        results_df = pd.DataFrame([results])

        if os.path.exists(top_file):
            # If file exists, append the new results without writing the header
            results_df.to_csv(top_file, mode='a', index=False, header=False)
        else:
            # If file does not exist, write the results with the header
            results_df.to_csv(top_file, index=False, header=True)
        
    save_max()

    return max_shift, max_v, min_v, results
