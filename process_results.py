import pandas as pd
import matplotlib.pyplot as plt
import os
import csv

def get_main_folder(cell_id,var,data_dir):
    top_top_dir=os.path.join(data_dir,"data",str(cell_id),str(var))
    print(data_dir)
    print(top_top_dir)
    return top_top_dir

def load_results(cell_id,var,data_dir=os.getcwd(),filtered=False):
    top_dir=get_main_folder(cell_id,var,data_dir)
    if not filtered:
        pos_file=os.path.join(top_dir,"maxshiftp.csv")
        neg_file=os.path.join(top_dir,"maxshiftn.csv")
    else:
        pos_file=os.path.join(top_dir,"maxshiftp_filtered.csv")
        neg_file=os.path.join(top_dir,"maxshiftn_filtered.csv")

    # Initialize an empty dictionary to store results
    summary_datap = {}
    summary_datan = {}
    for folder_name in os.listdir(top_dir):
        # Construct the full path
        folder_path = os.path.join(top_dir, folder_name)

          # Check if it's a directory
        if os.path.isdir(folder_path):
            print(f"Processing folder: {folder_name}")
            if not filtered:
                results_file=os.path.join(folder_path,"results_summary.csv")
            else:
                results_file=os.path.join(folder_path,"results_summary_filtered.csv")
        
            if os.path.exists(results_file):
                # Load the results summary file
                data = pd.read_csv(results_file)

                # Extract the E value, CFreq, and max_shiftp
                for _, row in data.iterrows():
                    E = row["EValue"]
                    if var=="cfreq":
                        CFreq = row["CFreq"]
                    elif var=="modfreq":
                        ModFreq=row["ModFreq"]  

                    max_shiftp = row["max_shiftp"]
                    max_shiftn=row["max_shiftn"]

                    # Initialize row if not present
                    if E not in summary_datap:
                        summary_datap[E] = {}
                    if E not in summary_datan:
                        summary_datan[E] = {}

                    # Add the max_shiftp for this CFreq
                    if var=="cfreq":
                        summary_datap[E][CFreq] = max_shiftp
                        summary_datan[E][CFreq] = max_shiftn
                    elif var=="modfreq":
                        summary_datap[E][ModFreq] = max_shiftp
                        summary_datan[E][ModFreq] = max_shiftn
            else:
                print(f"Warning: Results file not found in {folder_path}")

    # Convert the dictionary to a DataFrame
    summary_dfp = pd.DataFrame(summary_datap).T
    summary_dfp.index.name = "E"
    summary_dfp.to_csv(pos_file)
    print(f"Summary saved to {pos_file}")
    summary_dfn = pd.DataFrame(summary_datan).T
    summary_dfn.index.name = "E"
    summary_dfn.to_csv(neg_file)

    return summary_dfp,summary_dfn,top_dir

def plot_results(summary_df,title="Max Shiftp",top_dir=None,var="cfreq",evalue_threshold=None,filtered=False):
     # Extract E values (index) and carrier frequencies (columns)
    if evalue_threshold is not None:
        summary_df = summary_df[summary_df.index < evalue_threshold]
        
    summary_df = summary_df.sort_index()  # Ensure E_values are sorted
    E_values = summary_df.index.tolist()
    CFreq_columns = sorted(summary_df.columns.tolist(), key=float)  # Sort CFreq in ascending order
    fig,ax=plt.subplots()
    for CFreq in CFreq_columns:
            ax.plot(E_values, summary_df[CFreq], label=f"{CFreq} Hz",marker='o') 
       
      # Add labels, title, legend, and grid
    ax.set_xlabel("E (Electric Field Strength)", fontsize=12)
    ax.set_ylabel(f"{title} (mV)", fontsize=12)
    ax.set_title(title, fontsize=14)
    # Position the legend outside the plot
    if var=="cfreq":
        ax.legend(title="Carrier Frequency", fontsize=10, loc='upper left', bbox_to_anchor=(1.05, 1))
    elif var=="modfreq":
        ax.legend(title="Modulation Frequency", fontsize=10, loc='upper left', bbox_to_anchor=(1.05, 1))

    ax.grid(True)
    plt.show()

    if top_dir:
        if filtered:
            out_file=os.path.join(top_dir,f"{title}_filtered.png")
        else:
            out_file=os.path.join(top_dir,f"{title}.png")
            
        fig.savefig(out_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {out_file}")

