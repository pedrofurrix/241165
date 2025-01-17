### Check if Maxpseg and maxnseg are the same...
import pandas as pd
import matplotlib.pyplot as plt
import os
import csv
import json

def get_main_folder(cell_id,var,data_dir):
    top_top_dir=os.path.join(data_dir,"data","no_ramp",str(cell_id),str(var))
    print(currdir)
    print(top_top_dir)
    return top_top_dir

def check_segs(cell_id,var,data_dir=os.getcwd(),filtered=False):
    top_dir=get_main_folder(cell_id,var,data_dir)

     # Initialize dictionaries to store max segments
    # Use sets to store only unique segment names
    max_segments = {
        "maxp_segments": set(),
        "maxn_segments": set()
    }
    
    for folder_name in os.listdir(top_dir):
        # Construct the full path
        folder_path = os.path.join(top_dir, folder_name)

        # Check if it's a directory
        if os.path.isdir(folder_path):
            print(f"Processing folder: {folder_name}")
            if not filtered:
                results_file = os.path.join(folder_path, "results_summary.csv")
            else:
                results_file = os.path.join(folder_path, "results_summary_filtered.csv")
        
            if os.path.exists(results_file):
                # Load the results summary file
                data = pd.read_csv(results_file)

                # Extract the maxp_seg and maxn_seg values and add them if unique
                for _, row in data.iterrows():
                    maxp_seg = row["maxp_seg"]
                    maxn_seg = row["maxn_seg"]  # Fixed key for maxn_seg

                    max_segments["maxp_segments"].add(maxp_seg)
                    max_segments["maxn_segments"].add(maxn_seg)

   # Convert sets back to lists for saving
    max_segments["maxp_segments"] = list(max_segments["maxp_segments"])
    max_segments["maxn_segments"] = list(max_segments["maxn_segments"])
    if not filtered:
        # Save max segments to a file (CSV or JSON)
        output_file = os.path.join(top_dir, "max_segments.json")
    else:
        output_file = os.path.join(top_dir, "max_segments_filtered.json")
    with open(output_file, "w") as f:
        json.dump(max_segments, f, indent=4)
    
    print(f"Max segments saved to {output_file}")