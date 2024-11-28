: $Id: xtra.mod,v 1.4 2014/08/18 23:15:25 ted Exp ted $
: 2018/05/20 Modified by Aman Aberra 

NEURON {
	SUFFIX xtra
	RANGE es, er : (es = max amplitude of the potential)		
	RANGE x, y, z, type, order
	GLOBAL stim : (stim = normalized waveform)
	POINTER im, ex 
}

PARAMETER {	
	es = 0 (mV)
	x = 0 (1) : spatial coords
	y = 0 (1)
	z = 0 (1)		
	type = 0 (1) : numbering system for morphological category of section - unassigned is 0
	order = 0 (1) : order of branch/collateral. 
}

ASSIGNED {
	v (millivolts)
	ex (millivolts)
	er (microvolts)
	im (milliamp/cm2)
	stim (unitless) 		
	area (micron2)
}

INITIAL {
	ex = stim*es : I can say that es is Ohm, if im and stim were in mAmp 
	er= es*im*area*0.00001 : er (Volts) =es (Ohms) *im*10**-3*10**-8 (Amp/um^2) *area
}


BEFORE BREAKPOINT { : before each cy' = f(y,t) setup
  ex = stim*es
}
AFTER SOLVE { : after each solution step
  er= es*im*area*0.00001
}
