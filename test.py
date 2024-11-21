from neuron import h, gui

val = h.ref(42)

def show_val():
    print('value is: %g' % val[0])

h.xpanel('demo')
h.xpvalue('enter value', val, 10)
h.xbutton('show value', show_val)
h.xpanel()