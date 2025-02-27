from neuron import h
import numpy as np
import os
import csv 
import json 
import matplotlib.pyplot as plt
import plotly
import matplotlib.colors as mcolors
from matplotlib import cm
import plotly.graph_objects as go
import pandas as pd

import ast

# max_shift, max_v, min_v, results=max_minshift.cmax_shift(folder)

def load_results(bot_dir,freq,amp,filtered=True):
    if filtered:
        path=os.path.join(bot_dir,f"max_shift_data_{int(freq/1000)}kHz_{amp}Vm.csv")
    else:
        path=os.path.join(bot_dir,f"max_shift_data_{int(freq/1000)}kHz_{amp}Vm_uf.csv")
    max_shift_data=pd.read_csv(path)
    # max_shift=max_shift_data["max_shift"].to_list()
    return max_shift_data


#Plot Shape of the max_shift for each compartment, with a color scale
def plot_maxshift(bot_dir,cell,max_value,min_value,max_seg,mark=False,sElec_list=None,scale=3):

    ps = h.PlotShape(False)
    vmin=min_value
    vmax=max_value
    
    # # ps.show(0) # Show Diameter (Not working)
    # for section in cell.all:
    #     # if section not in cell.somatic:
    #     ps.len_scale(0.0001,section)

   
    cmap=cm.get_cmap("Spectral")
    
            
   
    ps.variable("v")  # Associate the PlotShape with the 'v' variable
    ps.scale(vmin, vmax)  # Set the color scale

    if sElec_list is not None:
        ps.color_list(sElec_list,4)
    ps.show(0)
    fig=ps.plot(plotly, cmap=cmap)

     # Flip Y-axis (negative values go down)
    fig.update_yaxes(autorange="reversed")


    if mark:
        section_name = max_seg.split('(')[0]  # Example: "axon[0]"
        segment_loc = float(max_seg.split('(')[1].split(')')[0])  # Example: 0.5
        for sec in cell.all:
            if sec.name() == section_name:
                segment=sec(segment_loc)    
        fig.mark(segment, size=10, color=2)
    
    # for sec in h.allsec():
    #     if 'soma' not in sec.name():
    #         for i in range(sec.n3d()):
    #             d = sec.diam3d(i)
    #             sec.pt3dchange(i, d * scale)
    # elif 'soma' in sec.name():
    #     x, y, z, diam = [], [], [], []
    #     for i in range(sec.n3d()):
    #         x.append(sec.x3d(i))
    #         y.append(sec.y3d(i))
    #         z.append(sec.z3d(i))
    #         diam.append(sec.diam3d(i))
    #     sec.pt3dclear()
    #     x, y, z, diam = scale * np.array(x), scale * np.array(y), scale * np.array(z), scale * np.array(diam)
    #     i = int(len(x) / 2)
    #     midptx, midpty, midptz = x[i], y[i], z[i]
    #     x -= midptx / 2.
    #     y -= midpty / 2.
    #     z -= midptz / 2.
    #     for xpt, ypt, zpt, diampt in zip(x, y, z, diam):
    #         sec.pt3dadd(xpt, ypt, zpt, diampt)

    # Create a custom colormap using Matplotlib 
    
    # Collect values of the variable from all segments
    # Create a colormap function
    colormap = cm.ScalarMappable(cmap=cmap, norm=mcolors.Normalize(vmin=0, vmax=1)).to_rgba

    # Map the normalized values to a Plotly colorscale as strings
    plotly_colorscale = [[v, f'rgb{tuple(int(255 * c) for c in colormap(v)[:3])}'] for v in np.linspace(0, 1, cmap.N)]

    # Create a separate scatter plot for the colorbar
    colorbar_trace = go.Scatter(
    x=[0],
    y=[0],
    mode='markers',
    marker=dict(
        colorscale=plotly_colorscale,
        cmin=vmin,
        cmax=vmax,
        colorbar=dict(
            title="Max Shift",
            thickness=20  # Adjust the thickness of the colorbar
        ),
        showscale=True
    )
    )

    # Add the colorbar trace to the figure
    fig.add_trace(colorbar_trace)

    # # Add a scale bar (100 µm) at the bottom right
    # scale_length_um = 100  # Scale bar length in micrometers
    # fig.add_trace(go.Scatter(
    #     x=[-200, -100],  # Adjust X position as needed
    #     y=[-500, -500],  # Y position
    #     mode="lines",
    #     line=dict(color="black", width=3),
    #     showlegend=False
    # ))
    
    # # Add scale bar label
    # fig.add_trace(go.Scatter(
    #     x=[-150], 
    #     y=[-520], 
    #     text=["100 µm"], 
    #     mode="text",
    #     showlegend=False
    # ))

    fig.update_xaxes(showticklabels=False, showgrid=False)
    fig.update_yaxes(showticklabels=False, showgrid=False)
    fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0)'
    )

    fig.show()
    path= os.path.join(bot_dir,f"shape.html")
    fig.write_html(path)
    # saveplot()
    
    return fig,cell,ps

def assign_v_values(bot_dir,freq,amp,filename="max_v",cell=None,max_shift=None,filtered=True):
    if max_shift is None:
        
        max_shift_data= load_results(bot_dir,freq,amp,filtered)
        max_shift=max_shift_data[filename].iloc[0]
        segs=max_shift_data["seg"].iloc[0]
        print(type(segs))


        max_shift = ast.literal_eval(max_shift)

        # Fix `segs` if it's stored as a string of an array
        if isinstance(segs, str):  
            try:
                # If stored as a Python list string, evaluate it
                segs = ast.literal_eval(segs)
            except (SyntaxError, ValueError):
                # If it's a NumPy array in string form, process it manually
                segs = segs.strip("[]")  # Remove brackets
                segs = segs.replace("'", "").split()  # Split into individual items

        # Ensure it's a proper list
        seg_list = list(np.array(segs)) if isinstance(segs, np.ndarray) else list(segs)
        print(len(seg_list))
        print(seg_list)
        
    
    print(f"Loaded {len(max_shift)} max_shift values.")
    # Count total segments in cell.all

    total_segments = sum(1 for sec in cell.all for seg in sec)
    print(f"Total segments in cell: {total_segments}")
    if len(seg_list)!=total_segments:
        print("Seg list incomplete, generating new one!")
        seg_list=[str(seg) for sec in cell.all for seg in sec]

    # Ensure the lengths match
    if len(max_shift) != total_segments:
        raise ValueError(f"Mismatch: max_shift has {len(max_shift)} values but cell has {total_segments} segments.")
    
    min_value=min(max_shift)
    max_value=max(max_shift)
    print(f"Min Value:{min_value}\nMax Value:{max_value}\n")

    max_indices = [i for i, v in enumerate(max_shift) if v == max_value]    
    print(max_indices)
    # print(f"Max value {max_value} found at indices: {max_indices}")
    # print(segs)
    # print(seg_list[max_indices[0]])
    max_seg=seg_list[max_indices[0]]

    i=0
    for sec in cell.all:
        for seg in sec:

            seg.v=max_shift[i]
            i+=1    
        


    return cell,min_value,max_value,max_indices,max_seg


from neuron import h
import numpy as np

def create_e_field_vector(theta, phi,len_um,ps):
    """
    Create a visualization of an E-field vector in NEURON using pt3dadd.

    Args:
        theta (float): Elevation angle in degrees.
        phi (float): Azimuthal angle in degrees.

    Returns:
        h.Section: The created section representing the E-field vector.
    """

    # Convert angles from degrees to radians
    theta_rad = np.radians(theta)
    phi_rad = np.radians(phi)

    # Compute 3D coordinates
    x_end = len_um * np.sin(theta_rad) * np.cos(phi_rad)
    y_end = len_um * np.cos(theta_rad)
    z_end = -len_um * np.sin(theta_rad) * np.sin(phi_rad)

    # Create the section
    sElec = h.Section(name="sElec")
    sElec.pt3dclear()
    sElec.pt3dadd(0, 0, 0, 1)  # Start point
    sElec.pt3dadd(x_end, y_end, z_end, 1)  # End point

    # Store in SectionList for visualization
    sElec_list = h.SectionList()
    sElec_list.append(sec=sElec)

    # Apply color and label
    ps.color_list(sElec_list, 5)  # Color code 7 (Violet)
    ps.label(600, 100, "E-field vector", 1, 1, 0, 0, 7)

    print(f"Calculated potentials for theta = {theta} deg, phi = {phi} deg")

    return sElec

def mark_highest_v(cell,max_seg,maxv,minv,cmap="viridis"):
        # Create a PlotShape object
    ps = h.PlotShape(False)  # False means no automatic variable coloring
   
    ps.variable('v')
    ps.scale(minv, maxv)

     # Convert cmap string to colormap object
    cmap = cm.get_cmap(cmap)

    # for segment in max_segments:
    #     # Mark the desired segment (Example: soma at 0.5 and apical dendrite at index 68)
    #     # ps.mark(segment, size=10,color=4)   # Blue dot
    #     ps.plot(plt).mark(segment, size=10, color=2)  # Red dot (default NEURON color scheme)
    #     # ps.mark(h.apical_dendrite=8, color=4)   # Blue dot
    section_name = max_seg.split('(')[0]  # Example: "axon[0]"
    segment_loc = float(max_seg.split('(')[1].split(')')[0])  # Example: 0.5
    for sec in cell.all:
        ps.len_scale(0.01,sec)
        if sec.name() == section_name:
            segment=sec(segment_loc)    
    print(segment)
    ps.variable("v")
    # ps.show(0)

    fig=ps.plot(plt,cmap=cmap).mark(segment, size=10, color=2)  # Red dot (default NEURON color scheme)
    fig.grid(False)
    fig.axis('off')
    # Show the figure
    plt.show()
    
    return ps,fig


def plot_voltage_distribution(cell,list=None,cmap="Spectral", savefig=False, 
                              figname="voltage_plot", colorbarlabel="Peak Depolarization [mV]", 
                              ticklabels=False, tickmin=-70, tickmax=40, dt=10,scale_bar_position=(-500, -900, 0)):
    # Get all voltage values in the model
    v_vals = [seg.v for sec in cell.all for seg in sec]
    print("Voltage range:", min(v_vals), max(v_vals))
     # Convert cmap string to colormap object
    cmap = cm.get_cmap(cmap)

   
    minv = min(v_vals)
    maxv = max(v_vals)

    #### First Figure (Matplotlib) ####
    ps = h.PlotShape(False)  # No automatic NEURON GUI
    ps.variable('v')
    ps.scale(minv, maxv)
    ps.show(0)
    if list is not None:
        ps.color_list(list,4)
    ax = ps.plot(plt, cmap=cmap)
    ax.view_init(elev=0, azim=0)  # Make Y the height axis
    ax.view_init(elev=0, azim=0)  # Make Y the height axis
    ax.invert_zaxis()  # Flip Z to move yellow part down
    ax.set_zlim(ax.get_ylim())  # Make sure Z now follows Y's range
    ax.set_ylim(ax.get_zlim())  # Ensure Y follows Z's range
    # # Set axis limits
    # ax.set_xlim([-700, 0])
    # ax.set_ylim([500, 1400])
    # ax.set_zlim([-1000, 0])

    # # **Add Scale Bar (100 µm)**
    # scale_bar_length=100
    # x_start, y_start, z_start = scale_bar_position
    # ax.plot([x_start, x_start + scale_bar_length], [y_start, y_start], color='black', linewidth=3)
    # ax.text(x_start + scale_bar_length / 2, y_start - 50, z=z_start, s= f"{scale_bar_length} µm", fontsize=12, ha='center')
    # Remove grid and axis
    # ax.grid(True)
    # ax.axis('on')
      
    ax.grid(True,linewidth=1,alpha=0.3,axis="both",linestyle="--")
    # ax.axis('off')

    # Save as EPS (if needed)
    if savefig:
        plt.savefig(figname + '.eps', format='eps')

    plt.show()

    #### Second Figure (Plotly) ####
    ps = h.PlotShape(True)  # Enable color mapping
    ps.variable("v")
    ps.scale(minv, maxv)
    ps.show(0)
    if list is not None:
        ps.color_list(list,4)
    fig = ps.plot(plotly, cmap=cmap)  # Use Plotly
    
    # Create colormap
    colormap = cm.ScalarMappable(cmap=cmap, norm=mcolors.Normalize(vmin=minv, vmax=maxv)).to_rgba
    plotly_colorscale = [[v, f'rgb{tuple(int(255 * c) for c in colormap(v)[:3])}'] for v in np.linspace(0, 1, cm.get_cmap(cmap).N)]

    # Create a colorbar trace
    colorbar_trace = go.Scatter(
        x=[0],
        y=[0],
        mode='markers',
        marker=dict(
            colorscale=plotly_colorscale,
            cmin=minv,
            cmax=maxv,
            colorbar=dict(
                title=colorbarlabel,
                thickness=20
            ),
            showscale=True
        )
    )

    # Add colorbar trace to the figure
    fig.add_trace(colorbar_trace)
    fig.update_xaxes(showticklabels=False, showgrid=False)
    fig.update_yaxes(showticklabels=False, showgrid=False)
    # fig.update_zaxes(showticklabels=False, showgrid=False)
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)')
    fig.update_layout(
    scene=dict(
        xaxis=dict(title="X", showgrid=False, showbackground=False),
        yaxis=dict(title="Y", showgrid=False, showbackground=False),
        zaxis=dict(title="Z", showgrid=False, showbackground=False),
        camera=dict(up=dict(x=0, y=1, z=0), # Y is now UP
                    eye=dict(x=0.8, y=0, z=0.8))  

    )

)
    fig.show()

    if savefig:
        plotly.offline.plot(fig, filename=figname + '.html', auto_open=False)
        # fig.write_image(figname + ".svg")  # Save as vector format

    #### Colorbar Only (Matplotlib) ####
    colormap = cm.ScalarMappable(cmap=cmap, norm=mcolors.Normalize(vmin=minv, vmax=maxv))
    fig, ax = plt.subplots(figsize=(6, 1))
    cbar = plt.colorbar(colormap, cax=ax, orientation='horizontal')
    cbar.set_label(colorbarlabel)
    
    if ticklabels:
        tick_positions = [minv, minv + 0.25* (maxv - minv), minv + 0.5 * (maxv - minv),minv + 0.75 * (maxv - minv), maxv]
        cbar.set_ticks(tick_positions)        
        cbar.set_ticklabels([f'{i:.2f}' for i in tick_positions])

    plt.tight_layout()

    if savefig:
        plt.savefig(figname + 'colorbar' + '.eps', format='eps')

    plt.show()


def scale_diams(cell,scale=3,scale_soma=False):
    for sec in cell.all:
        if 'soma' not in sec.name():
            for i in range(sec.n3d()):
                d = sec.diam3d(i)
                sec.pt3dchange(i, d * scale)

        if scale_soma:
            if 'soma' in sec.name():
                x, y, z, diam = [], [], [], []
                for i in range(sec.n3d()):
                    x.append(sec.x3d(i))
                    y.append(sec.y3d(i))
                    z.append(sec.z3d(i))
                    diam.append(sec.diam3d(i))
                sec.pt3dclear()
                x, y, z, diam = scale * np.array(x), scale * np.array(y), scale * np.array(z), scale * np.array(diam)
                i = int(len(x) / 2)
                midptx, midpty, midptz = x[i], y[i], z[i]
                x -= midptx / 2.
                y -= midpty / 2.
                z -= midptz / 2.
                for xpt, ypt, zpt, diampt in zip(x, y, z, diam):
                    sec.pt3dadd(xpt, ypt, zpt, diampt)
    return cell