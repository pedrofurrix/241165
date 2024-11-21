from neuron import h

h.load_file("nrngui.hoc") # load gui
h.load_file("interpCoordinates.hoc") #interp_coordinates 
h.load_file("setPointers.hoc")
h.load_file("calcVe.hoc") #can be replaced with calcrx.py # add plots
# h.load_file("stimWaveform.hoc") # Can be replaced with stim.py #add stim plot
h.load_file("cellChooser.hoc")
h.load_file("setParams.hoc")
h.load_file("editMorphology.hoc")
h.load_file("rig.ses") # Run control

import stim

h.tstop=500
h.dt=0.01

ton=10
amp=-10
depth=1
dt=h.dt
dur=250
simtime=h.tstop
freq=1000
modfreq=10
t,stim1=stim.ampmodulation_wiki(ton,amp,depth,dt,dur,simtime,freq,modfreq)



h.createPanels()





