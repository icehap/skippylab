"""
Function generators

"""
import time


from . import oscilloscopes as osci
from ..scpi import commands as cmd
from .. import loggers
from math import sqrt,log10
import pprint

try:
    from plx_gpib_ethernet import PrologixGPIBEthernet
except ImportError as e:
    logger = loggers.get_logger(10)
    logger.warn('No plx_gpib_ethernet module installed')

bar_available = False

try:
    import pyprind
    bar_available = True
except ImportError:
    pass
    #logger.warning("No pyprind available")

setget = osci.setget
#KCmd = cmd.Agilent3322OACommands

q = cmd.query


def format_docstring(fmt, indent):
    def wrapper(func):
        pretty_fmt = pprint.pformat(fmt, indent)
        func.__doc__ = func.__doc__.format(pretty_fmt)
        return func
    return wrapper


class Agilent3322OAFunctionGenerator(object):
    """
    """
    #output = setget(KCmd.OUTPUT)

    def __init__(self, ip="10.25.123.111", gpib_address=15, loglevel=20):
        """
        Connect to the power supply via Prologix GPIB connector

        Keyword Args:
            ip (str): IP adress of the Prologix GPIB connector
            gpib_address (int): The GPIB address of the power supply
                                connected to the Prologix connector
        """
        gpib = PrologixGPIBEthernet(ip)
        gpib.connect()
        gpib.select(gpib_address)
        self.logger = loggers.get_logger(loglevel)
        self.instrument = gpib
        #self.P6 = KCmd.P6
        #self.P25 = KCmd.P25
        #self.N25 = KCmd.N25

    def __del__(self):
        self.instrument.close()

class Agilent3101CFunctionGenerator(object):
    SHAPES = {
        'sinusoidal': 'SIN',
        'square': 'SQU',
        'pulse': 'PULS',
        'ramp': 'RAMP',
        'prnoise': 'PRN',
        'dc': 'DC',
        'sinc': 'SINC',
        'gaussian': 'GAUS',
        'lorentz': 'LOR',
        'erise': 'ERIS',
        'edecay': 'EDEC',
        'haversine': 'HAV'
    }
    FREQ_LIMIT = [1e-6, 150e6] #Frequeny limit for sinusoidal function in Hz
    DUTY_LIMIT = [0.001, 99.999]
    AMPLITUDE_LIMIT = {
        'VPP': [20e-3, 10],
        'VRMS': list(map(lambda x: round(x/2/sqrt(2), 3), [20e-3, 10])),
        'DBM': list(map(lambda x: round(20*log10(x/2/sqrt(0.1)), 2),
                    [20e-3, 10]))
        } #Vpp, Vrms and dBm limits
    UNIT_LIMIT = ['VPP', 'VRMS', 'DBM']
    IMP_LIMIT = [1, 1e4]


    def __init__(self, ip="10.25.124.252", gpib_address=10, loglevel=20):
        """
        Connect to the power supply via Prologix GPIB connector

        This class is based on information provided by the AFG3021B Programmer Manual.
        For more information, please see AFG3000 Series Arbitrary/Function Generators
        Programmer Manual offered by Tecktronix.

        Keyword Args:
            ip (str): IP adress of the Prologix GPIB connector
            gpib_address (int): The GPIB address of the power supply
                                connected to the Prologix connector
        """

        try:
            gpib = PrologixGPIBEthernet(ip, timeout=15)
            gpib.connect()
        except OSError:
            raise ValueError('Connection to plx_gpib_ethernet failed, check connection!')

        try:
            gpib.select(gpib_address)
        except OSError:
            raise ValueError('Connection to plx_gpib_ethernet failed, check IP address!')

        self.logger = loggers.get_logger(loglevel)
        self.instrument = gpib

    def __del__(self):
        self.instrument.close()

    def get_ID(self):
        ''' Requests and returns the identification of the instrument.'''
        return self.instrument.write('*IDN?')

    def reset_instrument(self):
        ''' Resets the instrument to the factory default settings.

        Menu or System Default setting
        ----------------
        <<Output configuration>>
        Function Sine
        Frequency 1.000 000 000 00 MHz
        Amplitude 1.000 Vp-p
        Offset 0 mV
        Symmetry (Ramp) 50.0%
        Duty (Pulse) 50.0%
        Output Units Vp-p
        Output Impedance 50 Ω
        Output Invert Off
        Output Noise Add Off
        External Add Off

        <<Modulation>>
        Modulation Waveform 10.00 kHz, Sine (except FSK)
        Modulation Waveform 10.00 kHz, Square (FSK)
        AM Depth 50.0%
        FM Deviation 1.000 000 MHz
        PM Deviation 90.0 °
        FSK Hop Frequency 1.000 000 MHz
        FSK Rate 50.00 Hz
        PWM Deviation 5.0%

        <<Sweep>>
        Sweep Start Frequency 100.000 kHz
        Sweep Stop Frequency 1.000 000 MHz
        Sweep Time 10 ms
        Sweep Hold Time 0 ms
        Sweep Return Time 1 ms
        Sweep Type Linear
        Sweep Mode Repeat
        Sweep Source Internal
        Trigger Slope Positive
        Trigger Interval 1.000 ms

        <<Burst>>
        Burst Mode Triggered
        Burst Count 5
        Trigger Source Internal
        Trigger Delay 0.0 ns
        Trigger Interval 1.000 ms

        <<System-related settings>>
        Trigger Out Trigger
        Clock Reference Internal
        Access Protection Off
        '''
        self.instrument.write('*RST')

    def get_status(self):
        ''' Requests the status of the instrument.

        Definition of event codes
        Event class                     Code range          Description
        No error                        0                   No event or status
        Command errors                  –100 to –199        Command syntax errors
        Execution errors                –200 to –299        Command execution errors
        Device-specific errors          –300 to –399        Internal device errors
        Query errors                    –400 to –499        System event and query errors
        Power-on events                 –500 to –599        Power-on events
        User request events             –600 to –699        User request events
        Request control events          –700 to –799        Request control events
        Operation complete events       –800 to –899        Operation complete events
        Extended device-specific errors 1 to 32767          Device dependent device errors
        Reserved                        other than above    not used
        '''
        return self.instrument.write('STATus:OPERation:CONDition?')

    def waveform_frequency(self, value):
        '''
        Change the frequency of the function generator.

        Parameters
        ----------
        value : double
            Frequency value to set in Hz.
        '''
        self.instrument.write(f'source1:frequency {value}')

    @format_docstring(list(SHAPES.keys()), indent=12)
    def waveform_shape(self, value):
        '''
        Change the shape of the waveform.

        Parameters
        ----------
        value : string
            Can take the arguments:\n{}
        '''
        if value not in self.SHAPES.keys():
            raise ValueError(f'{value} is not a valid shape. Please select a ' +
                             f'shape from {self.SHAPES.keys()}.')
        self.instrument.write(f'source1:function:shape {self.SHAPES[value]}')

    def burst_mode(self, value):
        '''
        This command sets the number of cycles (burst count) to be output in
        burst mode for the specified channel. The query command returns 9.9E+37 if the
        burst count is set to INFinity.

        Parameters
        ----------
        value : double
            The burst count ranges from 1 to 1,000,000.
        '''
        self.instrument.write('source1:BURSt:STATe ON')
        self.instrument.write(f'source1:BURSt:NCYCles {value}')

    def burst_mode_end(self):
        self.instrument.write('source1:BURSt:STATe OFF')

    def beep(self):
        self.instrument.write("system:beep")

    def enable(self):
        self.instrument.write("output1:state on")

    def disable(self):
        self.instrument.write("output1:state off")

    @format_docstring(list(AMPLITUDE_LIMIT.keys()), indent=12)
    def waveform(self, shape='sinusoidal', frequency=1e6, units='VPP',
                 amplitude=1, offset=0):
        '''
        General setting method for a complete wavefunction

        Parameters
        ----------
        shape : string
            Type of waveform. Default sinusoidal.

        frequency : double
            Frequency given in Hz. Default 1e6 Hz.

        units : string
            The units used depend on the limits.
            Allowed units for the signal voltage include:\n{}

        amplitude : double
            Amplitude given in Volts. Default 1 Volt

        offset : double
            Default 0.
        '''
        self.waveform_shape(shape)
        self.instrument.write(f'source1:frequency {frequency}')
        self.instrument.write(f'source1:voltage:unit {units}')
        self.instrument.write(f'source1:voltage:amplitude {amplitude}{units}')
        self.instrument.write(f'source1:voltage:offset {offset}')

    def startup(self):
        '''
        This function will magically setup the function generator for a basic run.

        Startup that will reset the instrument and generate a square pulse with 3 Volts in amplitude at 1kHz.
        '''
        self.disable()
        print('Cheking the function generator response...')
        try:
            self.waveform(shape='sinusoidal')
            time.sleep(1)
        except Warning:
            print('Something went wrong... Check Function generator and connections! Is the function generator on?')
        print('Generating a 3V square pulse at 1kHz.')
        self.waveform(shape='square', amplitude=3, frequency=1e3)
        self.enable()

    #def modulate_waveform(self, value):
    #    '''
    #    This command uses the  pulse-width modulation (PWM) to create pulse-width modulated signals.
    #    The signal can be further characterized by the duty cycle, which is the ratio of the <<on>> time divided by the period.
    #    '''
