# emc-instrument-drivers
Instrument drivers for EMC regulatory related tests and automation.

There are many different spectrum analyzers, signal generators and turntable controllers available today each with their own variation of SCPI commands.

In order to abstract away some of the variations between different models and manufacturers, pyemi was created.  With pyemi developers need only specify the model of the instrument from the available .yaml files.  The correct command is then chosen from the list of available commands.

# Quick Start Guide
'''
from pyemi import SpectrumAnalyzer

# Create the analyzer object with connection id/interface
sa = SpectrumAnalyzer(gpib=20, driver='esw.yaml')
# Or
sa = SpectrumAnalyzer(tcpip='10.0.0.10')
sa.load_driver('esw.yaml')

# Reset the instrument
sa.reset()

# Set it to spectrum analyzer mode
sa.mode = 'SAN'

# Write commands by setting the objects properties
sa.center_frequency = (100, 'MHz')

# Query commands by assigning the properties to a variable
span = sa.span_frequency

# Create trace object
t2 = sa.Trace(2)

# Set trace 2 to max holde
t2.mode = 'MAXH'

# Store trace data as a dataframe of frequency/amplitude
data = t2.dataframe()

# Create marker object
m1 = sa.Marker(1)

# Set marker to max value
m1.to_max()

# Store amplitude
y = m1.amplitude
'''