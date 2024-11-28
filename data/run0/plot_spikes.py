import pandas as pd
import matplotlib.pyplot as plt
from mpl_interactions import ioff, panhandler, zoom_factory
import os
path=os.getcwd()
file=os.path.join(path,"data\\run0\\run0.csv") # Weird #Must be because of the interpreter

# %matplotlib widget # if on jupyter


# Read the CSV file into a DataFrame
data = pd.read_csv(file)
t=data['t']
soma_v=data['soma_v']
dend_v=data['dend_v']
axon_v=data['axon_v']


# Enable scroll to zoom with the help of MPL
# Interactions library function like ioff and zoom_factory.
with plt.ioff():
    fig, ax = plt.subplots()

ax.plot(t,soma_v,label="soma")
ax.plot(t,dend_v,label="dend")
ax.plot(t,axon_v,label="axon")
ax.set_xlabel("time(ms)")
ax.set_ylabel("Membrane Voltage (mV)") #vint-vext~
ax.set_title("Membrane Potential over time")
ax.legend()
disconnect_zoom = zoom_factory(ax)

# Enable scrolling and panning with the help of MPL
# Interactions library function like panhandler.
pan_handler = panhandler(fig)
plt.show()

