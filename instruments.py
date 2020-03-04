import logging
from pathlib import Path
import time
import glob

import numpy as np
import pandas as pd
from ruamel.yaml import YAML
import visa


class BaseInstrument:
    driver_folder = Path(__file__).parent.absolute() / Path('drivers')

    def __init__(self, resource=None, driver=None, log_level=logging.CRITICAL, **kwargs):
        if kwargs:
            for key, value in kwargs.items():
                self.interface = key.upper()
                self.id = value
            self.resource_string = f'{self.interface}::{self.id}::INSTR'
        else:
            self.resource_string = resource.upper()
        
        FORMAT = '[%(levelname)s]%(asctime)s - %(message)s'
        logging.basicConfig(level=log_level, format=FORMAT)
        logging.info(f'Resource string: {self.resource_string}')

        self.rm = visa.ResourceManager()
        self.resource = self.rm.open_resource(self.resource_string)

        if driver:
            self.load_driver(driver)
    
    def load_driver(self, driver_file):
        yaml=YAML(typ='safe')
        doc = self.driver_folder / Path(driver_file)
        if doc.exists():
            logging.info(f'Driver file: {doc}')
            self.commands = yaml.load(doc)
            if 'write_termination' in self.commands:
                self.resource.write_termination = self.commands['write_termination']
            if 'query_delay' in self.commands:
                self.resource.query_delay = float(self.commands['query_delay'])
        else:
            logging.warning(f'Driver file does not exist: {doc}')

    def list_available_drivers(self):
        drivers = glob.glob(str(self.driver_folder / Path('*.yaml')))
        return [Path(f).name for f in drivers]

    def __str__(self):
        '''Returns instrument ID'''
        idn = self.resource.query('*IDN?')
        idn = idn.split(',')
        if len(idn) >= 2:
            return idn[0] + ' ' + idn[1]
        else:
            return idn

    def __repr__(self):
        '''Returns instrument ID'''
        return self.resource.query('*IDN?')

    def reset(self):
        '''Resets instrument'''
        self.resource.write('*RST')

    def opc(self):
        '''Returns 1 when command is completed, 0 otherwise'''
        return int(self.resource.query('*OPC?'))


class SpectrumAnalyzer(BaseInstrument):
    def __init__(self, **kwargs):
        return super().__init__(**kwargs)

    def ese(self, val):
        '''Event status enable sets the bits of the event status registers'''
        self.resource.write(f'*ESE {val}')

    def esr(self):
        '''Queries the contents of the event status register'''
        self.resource.query('*ESR?')

    @property
    def rbw(self):
        command = self.commands['rbw']['get']
        return int(self.resource.query(command))

    @rbw.setter
    def rbw(self, val):
        command = self.commands['rbw']['set'] % val
        self.resource.write(command)

    @property
    def vbw(self):
        command = self.commands['vbw']['get']
        return int(self.resource.query(command))

    @vbw.setter
    def vbw(self, val):
        command = self.commands['vbw']['set'] % val
        self.resource.write(command)

    @property
    def amplitude_units(self):
        command = self.commands['amplitude']['units']['get']
        units = self.resource.query(command)
        units = units.lower().strip('\n').replace('b', 'B').replace('v', 'V')
        return units

    @amplitude_units.setter
    def amplitude_units(self, val):
        command = self.commands['amplitude']['units']['set'] % val
        self.resource.write(command)

    @property
    def start_frequency(self):
        command = self.commands['frequency']['start']['get']
        return int(self.resource.query(command))

    @start_frequency.setter
    def start_frequency(self, val):
        command = self.commands['frequency']['start']['set'] % val
        self.resource.write(command)

    @property
    def stop_frequency(self):
        command = self.commands['frequency']['stop']['get']
        return int(self.resource.query(command))

    @stop_frequency.setter
    def stop_frequency(self, val):
        command = self.commands['frequency']['stop']['set'] % val
        self.resource.write(command)

    @property
    def center_frequency(self):
        command = self.commands['frequency']['center']['get']
        return self.resource.query(command)

    @center_frequency.setter
    def center_frequency(self, val):
        command = self.commands['frequency']['center']['set'] % val
        self.resource.write(command)

    @property
    def span_frequency(self):
        command = self.commands['frequency']['span']['get']
        return self.resource.query(command)

    @span_frequency.setter
    def span_frequency(self, val):
        command = self.commands['frequency']['span']['set'] % val
        self.resource.write(command)

    @property
    def sweep_mode(self):
        command = self.commands['sweep']['mode']['get']
        return self.resource.query(command)

    @sweep_mode.setter
    def sweep_mode(self, val):
        if val.lower() == 'continuous' or val.lower() == 'on' or val == 1:
            command = self.commands['sweep']['mode']['continuous']['set']
        else:
            command = self.commands['sweep']['mode']['single']['set']
        return self.resource.write(command)

    @property
    def sweep_points(self):
        command = self.commands['sweep']['points']['get']
        return self.resource.query(command)

    @sweep_points.setter
    def sweep_points(self, val):
        command = self.commands['sweep']['points']['set'] % val
        return self.resource.query(command)

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, val):
        command = self.commands['mode']
        if 'spectrum' in val.lower() or 'san' in val.lower() or 'analyzer' in val.lower():
            command = command % 'SAN'
            self._mode = 'SAN'
        elif 'receiver' in val.lower() or 'emi' in val.lower():
            command = command % 'REC'
            self._mode = 'REC'
        self.resource.write(command)

    @property
    def rf_input(self):
        return self._rf_input

    @rf_input.setter
    def rf_input(self, val):
        command = self.commands['input'] % val
        self._rf_input = val
        self.resource.write(command)
    
    @property
    def format(self):
        command = self.commands['format']['get']
        return self.resource.query()

    @format.setter
    def format(self, val):
        if type(val) is tuple:
            command = self.commands['format']['binary'] % val
        elif 'asc' in val.lower():
            command = self.commands['format']['ascii']
        self.resource.write(command)

    @property
    def display(self):
        return self._display

    @display.setter
    def display(self, val):
        command = self.commands['display']
        command.format(val)
        self.resource.write(command)

    def Trace(self, t):
        return self._Trace(t, self)

    class _Trace: 
        def __init__(self, t, sa):
            self.sa = sa
            self._trace = t

        @property
        def mode(self):
            command = self.sa.commands['trace']['mode']['get'] % self._trace
            return self.sa.resource.query(command)

        @mode.setter
        def mode(self, val):
            command = self.sa.commands['trace']['mode']['set'] % (self._trace, val)
            self.sa.resource.write(command)

        @property
        def detector(self):
            command = self.sa.commands['trace']['detector']['get'] % self._trace
            return self.sa.resource.query(command)

        @detector.setter
        def detector(self, val):
            command = self.sa.commands['trace']['detector']['set'] % (self._trace, val)
            self.sa.resource.write(command)

        def dataframe(self, delay=None):
            ''' Returns pandas dataframe of Frequency (Hz), Amplitude ()'''
            command = self.sa.commands['trace']['values'] % self._trace
            pd.options.display.float_format = '{:.2f}'.format
            if self.sa.interface.upper() == 'TCPIP':
                self.sa.format = ('REAL', 32)
                data = self.sa.resource.query_binary_values(command, delay=delay, data_points=self.sa.sweep_points)
            elif self.sa.interface.upper() == 'GPIB':
                if delay:
                    time.sleep(delay)
                self.sa.format = 'ASCII'
                data = self.sa.resource.query(command)
                data = data.replace('\n', '001')
                data = data.replace('001001', '001')
                data = data.split(',')
            frequency = np.linspace(self.sa.start_frequency, self.sa.stop_frequency, len(data))
            units = self.sa.amplitude_units
            df = pd.DataFrame(data={'Frequency (Hz)': frequency, f'Amplitude ({units})': data})
            df[f'Amplitude ({units})'] = df[f'Amplitude ({units})'].astype(float)
            return df

    def Marker(self, m):
        return self._Marker(m, self)

    class _Marker: 
        def __init__(self, m, sa):
            self.sa = sa
            self._marker = m
            self.state = 'ON'

        @property
        def state(self):
            return self._state

        @state.setter
        def state(self, val):
            command = self.sa.commands['marker']['state'] % (self._marker, val)
            self._state = val
            self.sa.resource.write(command)

        @property
        def frequency(self):
            command = self.sa.commands['marker']['frequency']['get'] % self._marker
            return self.sa.resource.query(command)

        @frequency.setter
        def frequency(self, val):
            command = self.sa.commands['marker']['frequency']['set'] 
            f, v = val
            command = command % (self._marker, f, v)
            self.sa.resource.write(command)

        @property
        def amplitude(self):
            command = self.sa.commands['marker']['amplitude'] % self._marker
            return float(self.sa.resource.query(command))

        def goto_max(self):
            '''Moves marker to maximum value'''
            command = self.sa.commands['marker']['max'] % self._marker
            self.sa.resource.write(command)

        def goto_min(self):
            '''Moves marker to minimum value'''
            command = self.sa.commands['marker']['min'] % self._marker
            self.sa.resource.write(command)
        
        def center(self):
            '''Centers the frequency span around the marker'''
            command = self.sa.commands['marker']['center'] % self._marker
            self.sa.resource.write(command)


class SignalGenerator(BaseInstrument):
    def __init__(self, **kwargs):
        return super().__init__(**kwargs)

    @property
    def discrete_frequency(self):
        command = self.commands['frequency']['discrete']['get']
        return self.resource.query(command)

    @discrete_frequency.setter
    def discrete_frequency(self, val):
        command = self.commands['frequency']['discrete']['set'] % val
        self.resource.write(command)

    @property
    def output(self):
        command = self.commands['output']['get']
        return self.resource.query(command)

    @output.setter
    def output(self, val):
        command = self.commands['output']['set'] % val
        self.resource.write(command)

    @property
    def level(self):
        command = self.commands['level']['get']
        return self.resource.query(command)

    @level.setter
    def level(self, val):
        command = self.commands['level']['set'] % val
        self.resource.write(command)

    @property
    def unit(self):
        command = self.commands['unit']['get']
        return self.resource.query(command)

    @unit.setter
    def unit(self, val):
        command = self.commands['unit']['set'] % val
        self.resource.write(command)


class ControllerBase(BaseInstrument):
    def __init__(self, **kwargs):
        return super().__init__(**kwargs)

    @property
    def position(self):
        command = self.commands['position']['get']
        return self.resource.query(command)

    @position.setter
    def position(self, val):
        command = self.commands['position']['set'] % val
        return self.resource.write(command)

    @property
    def acceleration(self):
        command = self.commands['acceleration']['get']
        return self.resource.query(command)

    @acceleration.setter
    def acceleration(self, val):
        command = self.commands['acceleration']['set'] % val
        return self.resource.write(command)

    @property
    def speed(self):
        command = self.commands['speed']['get']
        return self.resource.query(command)

    @speed.setter
    def speed(self, val):
        command = self.commands['speed']['set'] % val
        return self.resource.write(command)

    @property
    def cycle(self):
        command = self.commands['cycle']['get']
        return self.resource.query(command)

    @cycle.setter
    def cycle(self, val):
        command = self.commands['cycle']['set'] % val
        return self.resource.write(command)

    @property
    def error(self):
        command = self.commands['error']['get']
        return self.resource.query(command)

    def start_scan(self):
        '''Starts scanning from upper and lower limits based on # of cycles'''
        command = self.commands['scan']['set']
        self.resource.write(command)
    
    def scan_progress(self):
        '''Returns scan progress'''
        command = self.commands['scan']['get']
        self.resource.query(command)


class Tower(ControllerBase):
    def __init__(self, **kwargs):
        return super().__init__(**kwargs)

    @property
    def direction(self):
        command = self.commands['direction']['get']
        return self.resource.query(command)

    @direction.setter
    def direction(self, val):
        if val == -1 or 'd' in val.lower():
            command = self.commands['direction']['set']['down']
        elif val == 1 or 'u' in val.lower():
            command = self.commands['direction']['set']['up']
        elif val == 0 or 's' in val.lower():
            command = self.commands['direction']['set']['stop']
        else:
            logging.critical('Invalid direction, choose 1, 0, -1 or up, stop, down')
            return
        self.resource.write(command)

    @property
    def polarity(self):
        command = self.commands['polarity']['get']
        return self.resource.query(command)

    @polarity.setter
    def polarity(self, val):
        if 'v' in val.lower():
            command = self.commands['polarity']['set'] % 'V'
        elif 'h' in val.lower():
            command = self.commands['polarity']['set'] % 'H'
        else:
            logging.critical('Invalid polarity, choose V or H')
            return
        self.resource.write(command)


class Turntable(ControllerBase):
    def __init__(self, **kwargs):
        return super().__init__(**kwargs)

    @property
    def direction(self):
        command = self.commands['direction']['get']
        return self.resource.query(command)
        
    @direction.setter
    def direction(self, val):
        if val == -1 or 'cc' in val.lower():
            command = self.commands['direction']['set']['counterclockwise']
        elif val == 1 or 'cw' in val.lower():
            command = self.commands['direction']['set']['clockwise']
        elif val == 0 or 's' in val.lower():
            command = self.commands['direction']['set']['stop']
        else:
            logging.critical('Invalid direction, choose 1, 0, -1 or cw, stop, cc')
            return
        self.resource.write(command)


class DualController(BaseInstrument):
    '''For devices with a single interface that control both antenna mast and turntable'''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.device = 'tower'

    def reset(self):
        command = self.commands['reset'] % self._device
        self.resource.write(command)

    @property
    def device(self):
        return self.readable_device

    @device.setter
    def device(self, val):
        if 'tower' in val.lower() or 'mast' in val.lower() or 'ant' in val.lower():
            self.readable_device = 'tower'
            self._device = self.commands['device']['tower']
        elif 'table' in val.lower():
            self.readable_device = 'turntable'
            self._device = self.commands['device']['turntable']
        else:
            logging.critical('Invalid device, choose tower or turntable')
            raise ValueError

    @property
    def position(self):
        command = self.commands['position']['get'] % self._device
        return self.resource.query(command)

    @position.setter
    def position(self, val):
        command = self.commands['position']['set'] % (self._device, val)
        return self.resource.write(command)

    @property
    def acceleration(self):
        command = self.commands['acceleration']['get'] % self._device
        return self.resource.query(command)

    @acceleration.setter
    def acceleration(self, val):
        command = self.commands['acceleration']['set'] % (self._device, val)
        return self.resource.write(command)

    @property
    def speed(self):
        command = self.commands['speed']['get'] % self._device
        return self.resource.query(command)

    @speed.setter
    def speed(self, val):
        command = self.commands['speed']['set'] % (self._device, val)
        return self.resource.write(command)

    @property
    def cycle(self):
        command = self.commands['cycle']['get'] % self._device
        return self.resource.query(command)

    @cycle.setter
    def cycle(self, val):
        command = self.commands['cycle']['set'] % (self._device, val)
        return self.resource.write(command)

    @property
    def error(self):
        command = self.commands['error']['get'] % self._device
        return self.resource.query(command)

    def start_scan(self):
        '''Starts scanning from upper and lower limits based on # of cycles'''
        command = self.commands['scan']['set'] % self._device
        self.resource.write(command)
    
    def scan_progress(self):
        '''Returns scan progress'''
        command = self.commands['scan']['get'] % self._device
        self.resource.query(command)

    @property
    def direction(self):
        command = self.commands['direction']['get']
        return self.resource.query(command)

    @direction.setter
    def direction(self, val):
        if self.readable_device == 'tower':
            if val == -1 or 'd' in val.lower():
                command = self.commands['direction']['set']['down']
            elif val == 1 or 'u' in val.lower():
                command = self.commands['direction']['set']['up']
            elif val == 0 or 's' in val.lower():
                command = self.commands['direction']['set']['stop']
            else:
                logging.critical('Invalid direction, choose 1, 0, -1 or up, stop, down')
                raise ValueError
        elif self.readable_device == 'turntable':
            if val == -1 or 'cc' in val.lower():
                command = self.commands['direction']['set']['counterclockwise']
            elif val == 1 or 'cw' in val.lower():
                command = self.commands['direction']['set']['clockwise']
            elif val == 0 or 's' in val.lower():
                command = self.commands['direction']['set']['stop']
            else:
                logging.critical('Invalid direction, choose 1, 0, -1 or cw, stop, cc')
                raise ValueError
        self.resource.write(command)

    @property
    def polarity(self):
        command = self.commands['polarity']['get'] % self.commands['device']['tower']
        return self.resource.query(command)

    @polarity.setter
    def polarity(self, val):
        if 'v' in val.lower():
            command = self.commands['polarity']['set'] % 'V'
        elif 'h' in val.lower():
            command = self.commands['polarity']['set'] % 'H'
        else:
            logging.critical('Invalid polarity, choose V or H')
            return
        self.resource.write(command)

if __name__ == "__main__":
    '''
    sa = SpectrumAnalyzer(gpib=20, driver='esw.yaml')
    print(sa)
    
    # Tower/Turntable example
    controller = DualController(gpib=7, driver='emcenter.yaml', log_level=logging.DEBUG)

    # Read device current position, default on object creation is tower
    print(controller.position)

    # Change device to turntable and set to 200
    controller.device = 'turntable'
    controller.position = 200

    # Should return 200 or the angle of the turntable during its current rotation to 200
    print(controller.position)

    # Close connection
    controller.resource.close()

    # Signal generator example
    sg = SignalGenerator(tcpip='10.0.0.11', driver='smw200a.yaml', log_level=logging.INFO)
    
    # Reset instrument
    sg.reset()

    # Set fixed frequency
    sg.discrete_frequency = (200, 'MHz')
    print(sg.discrete_frequency)

    # Turn rf output on
    sg.output = 1
    print(sg.output)
    
    # Set output signal level
    sg.level = -20
    print(sg.level)

    # Set output units dBm, dBuV etc.
    sg.unit = 'dbuv'
    print(sg.unit)

    # Close connection
    sg.resource.close()
    
    # Spectrum analyzer example
    sa = SpectrumAnalyzer(tcpip='10.0.0.10', driver='esw.yaml', log_level=logging.INFO)
    
    # Reset instrument
    sa.reset()

    # Set to spectrum analyzer mode
    sa.mode = 'SAN'

    # Set start frequency to 1MHz
    sa.start_frequency = (1, 'MHz')
    start = sa.start_frequency

    # Create trace object tied to trace 1 and read its contents as a pandas dataframe
    t1 = sa.Trace(1)
    print(t1.dataframe())
    
    # Create a marker object tied to marker 1
    m1 = sa.Marker(1)

    # Move the marker to the peak value
    m1.goto_max()

    # Read out marker frequency and amplitude
    amp = m1.amplitude
    x = m1.frequency
    print(amp, x)

    # Close connection
    sa.resource.close()
    '''