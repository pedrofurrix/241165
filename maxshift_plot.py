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

import max_minshift


# max_shift, max_v, min_v, results=max_minshift.cmax_shift(folder)

def load_results(bot_dir):


#Plot Shape of the max_shift for each compartment, with a color scale
def plot_maxshift(bot_dir,filename,cell,max_shift=None):

    i=0
    for sec in cell.all:
        for seg in sec:
            seg.v=max_shift[i]
            i+=1    

    ps = h.PlotShape(False)
    vmin=min(max_shift)
    vmax=max(max_shift)
    
    ps.show(0) # Show Diameter (Not working)
    ps.variable("v")  # Associate the PlotShape with the 'v' variable
    ps.scale(vmin, vmax)  # Set the color scale

    fig=ps.plot(plotly, cmap=cm.cool)
    
    # Create a custom colormap using Matplotlib (cool colormap)
    cmap = cm.cool
    
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
    fig.update_xaxes(showticklabels=False, showgrid=False)
    fig.update_yaxes(showticklabels=False, showgrid=False)
    fig.update_layout(
    plot_bgcolor='rgba(0,0,0,0)'
    )

    def saveplot():
        output_dir="frames"
        out=os.path.join(folder,output_dir)
        os.makedirs(out, exist_ok=True)  # Create directory if it doesn't exist
        file=os.path.join(out,f"max_shift.eps")
        ps.printfile(file)

    fig.show()
    path= os.path.join(folder,f"{filename}.html")
    fig.write_html(path)
    # saveplot()
    
    return fig

filename="min_v"
fig=plot_maxshift(min_v,folder,filename,cell)