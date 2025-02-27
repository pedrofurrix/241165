import pandas as pd
import matplotlib.pyplot as plt
import os
import csv

def get_main_folder(cell_id,var,data_dir=os.getcwd()):
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
                    max_shiftn= row["max_shiftn"]

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


def plot_results(cell_id,summary_df=None,title="Maximum Depolarization",
                 top_dir=None,var="cfreq",evalue_threshold=None,filtered=False,pos=True,data_dir=os.getcwd()):
    """
    Plots the max shift data (positive or negative) with respect to E values for various carrier or modulation frequencies.
    If `summary_df` is not provided, the function attempts to load it from the appropriate CSV file.

    Args:
        summary_df (pd.DataFrame): DataFrame containing the summary data. If None, it will load the data from a file.
        title (str): Title of the plot.
        top_dir (str): Directory where the data files are stored.
        var (str): Variable type, either "cfreq" or "modfreq".
        evalue_threshold (float): Threshold to filter E values.
        filtered (bool): Whether to use filtered data files.
    """
    if top_dir is None:
        top_dir= get_main_folder(cell_id,var,data_dir)

    # Load summary_df from the CSV file if it's not provided
    if summary_df is None:
        if top_dir is None:
            raise ValueError("If no summary_df is provided, top_dir must be specified to load the data.")
        
        if pos:
            # Determine file paths
            if filtered:
                file = os.path.join(top_dir, "maxshiftp_filtered.csv")
            else:
                file = os.path.join(top_dir, "maxshiftp.csv")
        else:
            if filtered:
                file = os.path.join(top_dir, "maxshiftn_filtered.csv")
            else:
                file = os.path.join(top_dir, "maxshiftn.csv")

            
 
        if not os.path.exists(file):
                raise FileNotFoundError(f"Summary file not found: {file}")
         # Load the DataFrame from the CSV file
        summary_df = pd.read_csv(file, index_col=0)  # Assumes E is the index column
        print(f"Summary data loaded from {file}") 

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
    if pos:
        if filtered:
            ax.set_ylim(0.05)
        else:
            ax.set_ylim(15)
    else:
        if filtered:
            ax.set_ylim(-0.05)
        else:
            ax.set_ylim(-15)
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
    plt.close()

def load_fourier_power(cell_id, var,norm=False,data_dir=os.getcwd()):
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
    top_dir = get_main_folder(cell_id, var,data_dir)
    if not norm:
        summary_file = os.path.join(top_dir, "fourier_maxpower_power.csv")
        norm_file = os.path.join(top_dir, "fourier_maxpower_norm.csv")
    else:
        summary_file = os.path.join(top_dir, "fourier_maxnorm_power.csv")
        norm_file = os.path.join(top_dir, "fourier_maxnorm_norm.csv")

    # Initialize an empty dictionary to store Fourier power data
    fourier_data = {}
    fourier_norm={}

    for folder_name in os.listdir(top_dir):
        # Construct the full path
        folder_path = os.path.join(top_dir, folder_name)

        # Check if it's a directory
        if os.path.isdir(folder_path):
            print(f"Processing folder: {folder_name}")
            results_file = os.path.join(folder_path, "FT_power.csv")           
            if os.path.exists(results_file):
                # Load the Fourier summary file
                data = pd.read_csv(results_file)

                # Extract relevant columns (EValue, CFreq/ModFreq, and Fourier Power)
                for _, row in data.iterrows():
                    E = row["EValue"]
                    if var == "cfreq":
                        CFreq = row["CFreq"]
                    elif var == "modfreq":
                        ModFreq = row["ModFreq"]
                    if not norm:
                        max_power = row["Max Power"]
                        max_norm_power = row["Max P Norm"]
                    else:
                        max_power = row["Max Norm Power"]
                        max_norm_power = row["Max Norm"]
                    # Initialize row if not present
                    if E not in fourier_data:
                        fourier_data[E] = {}
                        fourier_norm[E] = {}
                        
                    # Add the Fourier power for this CFreq/ModFreq
                    if var == "cfreq":
                        fourier_data[E][CFreq] = max_power
                        fourier_norm[E][CFreq] = max_norm_power
                    elif var == "modfreq":
                        fourier_data[E][ModFreq] = max_power
                        fourier_norm[E][ModFreq] = max_norm_power
            else:
                print(f"Warning: Fourier summary file not found in {folder_path}")

    # Convert the dictionary to a DataFrame
    summary_df = pd.DataFrame(fourier_data).T
    summary_df.index.name = "E"
    summary_norm = pd.DataFrame(fourier_norm).T
    summary_norm.index.name = "E"
    summary_df.to_csv(summary_file)
    summary_norm.to_csv(norm_file)
    print(f"Fourier power summary saved to {summary_file}")
    print(f"Fourier normalized power summary saved to {norm_file}")
    return summary_df, summary_norm,top_dir


def load_fourier_averages(cell_id, var,norm=False,data_dir=os.getcwd()):
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
    top_dir = get_main_folder(cell_id, var,data_dir)
  
    power_file = os.path.join(top_dir, "fourier_average_power.csv")
    norm_file = os.path.join(top_dir, "fourier_average_norm.csv")

    # Initialize an empty dictionary to store Fourier power data
    fourier_data = {}
    fourier_norm={}

    for folder_name in os.listdir(top_dir):
        # Construct the full path
        folder_path = os.path.join(top_dir, folder_name)

        # Check if it's a directory
        if os.path.isdir(folder_path):
            print(f"Processing folder: {folder_name}")
            results_file = os.path.join(folder_path, "average_fourier.csv")           
            if os.path.exists(results_file):
                # Load the Fourier summary file
                data = pd.read_csv(results_file)

                # Extract relevant columns (EValue, CFreq/ModFreq, and Fourier Power)
                for _, row in data.iterrows():
                    E = row["EValue"]
                    if var == "cfreq":
                        CFreq = row["CFreq"]
            
                    average_power = row["power"]
                    average_norm = row["norm"]
                    # Initialize row if not present
                    if E not in fourier_data:
                        fourier_data[E] = {}
                        fourier_norm[E] = {}
                        
                    # Add the Fourier power for this CFreq/ModFreq
                    if var == "cfreq":
                        fourier_data[E][CFreq] = average_power
                        fourier_norm[E][CFreq] = average_norm
            else:
                print(f"Warning: Fourier summary file not found in {folder_path}")

    # Convert the dictionary to a DataFrame
    summary_df = pd.DataFrame(fourier_data).T
    summary_df.index.name = "E"
    summary_norm = pd.DataFrame(fourier_norm).T
    summary_norm.index.name = "E"
    summary_df.to_csv(power_file)
    summary_norm.to_csv(norm_file)
    print(f"Fourier power summary saved to {power_file}")
    print(f"Fourier normalized power summary saved to {norm_file}")
    return summary_df, summary_norm,top_dir




def calculate_polarization_and_std(summary_dfp, summary_dfn,top_dir,filtered=False):
    # Calculate polarization length for positive and negative shifts
    polarization_length_p = summary_dfp.abs().div(summary_dfp.index, axis=0)  # Divide by E for positive shifts
    polarization_length_n = summary_dfn.abs().div(summary_dfn.index, axis=0)  # Divide by E for negative shifts

    # Compute average and standard deviation for each carrier frequency
    average_polarization_length_p = polarization_length_p.mean(axis=0,skipna=True)
    std_polarization_length_p = polarization_length_p.std(axis=0,skipna=True)

    average_polarization_length_n = polarization_length_n.mean(axis=0,skipna=True)
    std_polarization_length_n = polarization_length_n.std(axis=0,skipna=True)

    # Combine the results into a single DataFrame
    polarization_stats = pd.DataFrame({
        "CFreq": summary_dfp.columns,
        "Avg_Positive": average_polarization_length_p.values,
        "STD_Positive": std_polarization_length_p.values,
        "Avg_Negative": average_polarization_length_n.values,
        "STD_Negative": std_polarization_length_n.values
    })

    # Save the results to a CSV file
    if not filtered:
        output_file = os.path.join(top_dir, "polarization_length_summary.csv")
    else:
        output_file = os.path.join(top_dir, "polarization_length_filtered_summary.csv")
    polarization_stats.to_csv(output_file, index=False)
    print(f"Polarization length statistics saved to {output_file}")

    # Display the summary
    print(polarization_stats.head())



def plot_fourier_power(cell_id,
    summary_df=None,
    summary_norm=None,
    title="Fourier Power",
    top_dir=None,
    var="cfreq",
    evalue_threshold=None,
    norm=False,
    data_dir=os.getcwd()
):
    """
    Plots the Fourier power (or normalized power) with respect to E values for various carrier or modulation frequencies.
    If `summary_df` is not provided, the function attempts to load it from the appropriate CSV file.

    Args:
        summary_df (pd.DataFrame): DataFrame containing the Fourier power data. If None, it will load the data from a file.
        title (str): Title of the plot.
        top_dir (str): Directory where the data files are stored.
        var (str): Variable type, either "cfreq" or "modfreq".
        evalue_threshold (float): Threshold to filter E values.
        norm (bool): Whether to plot normalized power or raw power.
    """
    # Load summary_df from the CSV file if it's not provided
    if top_dir is None:
        top_dir=get_main_folder(cell_id,var,data_dir)
    if summary_df is None:
        
        if not norm:
            power_file = os.path.join(top_dir, "fourier_maxpower_power.csv")
            norm_file = os.path.join(top_dir, "fourier_maxpower_norm.csv")
        else:
            power_file = os.path.join(top_dir, "fourier_maxnorm_power.csv")
            norm_file = os.path.join(top_dir, "fourier_maxnorm_norm.csv")

        if not os.path.exists(power_file):
            raise FileNotFoundError(f"Summary file not found: {power_file}")
        if not os.path.exists(norm_file):
            raise FileNotFoundError(f"Summary file not found: {norm_file}")
        
        # Load the DataFrame from the CSV file
        summary_df = pd.read_csv(power_file, index_col=0)  # Assumes E is the index column
        print(f"Summary data loaded from {power_file}")
        summary_norm = pd.read_csv(norm_file, index_col=0)  # Assumes E is the index column
        print(f"Summary data loaded from {norm_file}")

    # Filter data based on E value threshold if provided
    if evalue_threshold is not None:
        summary_df = summary_df[summary_df.index < evalue_threshold]
        summary_norm= summary_norm[summary_norm.index < evalue_threshold]

    # Sort the DataFrame by index (E values)
    summary_df = summary_df.sort_index()
    E_values = summary_df.index.tolist()
    Freq_columns = sorted(summary_df.columns.tolist(), key=float)  # Sort CFreq or ModFreq in ascending order

    # Sort the DataFrame by index (E values) #Norm
    summary_norm = summary_norm.sort_index()
    E_values_norm = summary_norm.index.tolist()
    Freq_columns_norm = sorted(summary_norm.columns.tolist(), key=float)  # Sort CFreq or ModFreq in ascending order


    # Plotting the results
    fig, ax = plt.subplots()
    for freq in Freq_columns:
        ax.plot(E_values, summary_df[freq], label=f"{freq} Hz", marker='o')


    # Add labels, title, legend, and grid
    ax.set_xlabel("E (Electric Field Strength)", fontsize=12)
    ylabel =  "Fourier Power"
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14)

    if var == "cfreq":
        ax.legend(title="Carrier Frequency", fontsize=10, loc='upper left', bbox_to_anchor=(1.05, 1))
    elif var == "modfreq":
        ax.legend(title="Modulation Frequency", fontsize=10, loc='upper left', bbox_to_anchor=(1.05, 1))

    ax.grid(True)
   
    fig_norm,ax_norm=plt.subplots()
    for freq in Freq_columns_norm:
        ax_norm.plot(E_values_norm, summary_norm[freq], label=f"{freq} Hz", marker='o')
    
    # Add labels, title, legend, and grid
    ax_norm.set_xlabel("E (Electric Field Strength)", fontsize=12)
    ylabel_norm =  "Normalized Fourier Power"
    ax_norm.set_ylabel(ylabel_norm, fontsize=12)
    title1="Normalized Fourier Power"
    ax_norm.set_title(title1, fontsize=14)

    # Save the plot to file if top_dir is provided
    if top_dir:
        suffix = "norm" if norm else "power"
        out_file = os.path.join(top_dir, f"{title}_{suffix}.png")
        fig.savefig(out_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {out_file}")
        out_norm=os.path.join(top_dir, f"{title1}_{suffix}.png")
        fig_norm.savefig(out_norm, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {out_norm}")

    plt.close()