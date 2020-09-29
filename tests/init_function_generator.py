from skippylab.instruments.function_generators import Agilent3101CFunctionGenerator as FG3101

'''
Example of how to use the Agilent3101CFunctionGenerator class
'''

#Load
fg = FG3101()


'''
Startup that will reset the instrument and generate a square pulse with 3 Volts in amplitude at 1kHz.

Includes a factory reset function, best to use only from time to time.
Every time the reset is done, this device causes an extra voltage to be applied. This is what clears
the memeory or other elements. If done frequently, it could overheat and cause the bits to get over
heated and become unstable. In the long term, it could damage the device.
'''
fg.startup()


#Change the frequency, value in hertz
fg.waveform_frequency()


#Trun off the laser
fg.disable()


#If later the laser needs to be switched on
fg.enable()


#Generate a double pulse, can be combined with the fg.waveform_frequency() to change the frequency at which the pulses are fired.
fg.burst_mode(2)


#Exit burst Mode
fg.burst_mode_end()
