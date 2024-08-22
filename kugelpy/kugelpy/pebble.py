'''
@authors: balep, stewryan, ethan-fowler

Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED
'''

import numpy as np
import math

class Pebble(object):
    """!
    Class for holding information for an individual pebble.
    """

    def __init__(self, x, y, z, r, radius, channel, volume, temperature=900.0, pass_limit=6, pebble_number=0):
        ## (str, default: 'graphite') Designation if this is a graphite or fuel pebble.
        self._pebble_type = 'graphite'
        ## (float, default: 2.5) Inner radius of the pebble surrounding the graphite matrix [cm].
        self._inner_radius = 2.5
        ## (float, default: radius) Radius of the pebble.
        self._radius = radius
        ##  (float, default: ) Dictionary of the materials in the pebble \n
        ## Takes the form: {'material_name': {'ZAID1': float, 'ZAID2': float, ...}}.
        self._material = {'matrix':   {'6000': 9.22570E-2, '5010': 2.28336E-9, '5011': 9.24876E-9},
                         'pebshell': {'6000': 6.61814E-2, '5010': 2.23273E-8,  '5011': 9.04368E-7}}
        ## (float, default: x) Current x coordinate of pebble in the pebble bed.
        self._x = x
        ## (float, default: y) Current y coordinate of pebble in the pebble bed.
        self._y = y
        ## (float, default: z) Current z coordinate of pebble in the pebble bed.
        self._z = z
        ## (float, default: r) Current radial position in the pebble bed.
        self._r = r
        ## (int, default: volume) Integer representation (index) of the volume region the pebble is in.
        self._volume_num = volume
        ## (int, default: channel) Integer representation (index) of the channel the pebble is in.
        self._channel_num = channel
        ## (str, default: f'c{channel}v{volume}') Combination of channel and volume numbers used to identify general position of pebble in core.
        self._mesh_location = f'c{channel}v{volume}'
        ## (str, default: temperature) Temperature of the pebble in Kelvin (assumes constant temperature over whole pebble).
        self._temperature = temperature
        ## (bool, default: False) Indicator if this is the first pass or Nth pass through the core.
        self._shuffled = False
        ## (str, default: '') Concatinated string containing the previous universes the pebble was exposed to \n
        ## If the pebble is homogenized after each pass, we default the previous universes to c0v0.
        self._previous_universe = ''
        ## (float, default: 0.) Burnup accrued during pebble movement [MWd/kg].
        self._burnup = 0.
        ## (float, default: 0.) Burnup accrued during pebble movement [J/cm3].
        self._burnup_j_cm3 = 0.
        ## (int, default: 0) Number of passes a pebble has gone through the core.
        self._num_passes = 0
        ## (int, default: pass_limit) Maximum number of times a pebble can go through the core before being discarded.
        self._pass_limit = pass_limit
        ## (int, default: pebble_number) Integer related to the pebble number in the core.
        self._pebble_number = pebble_number
        ## (dict, default: ) Dictionary containing temperature-dependent cross section data labels stored in the form {temp1:{'graphite':_, 'xs_set':_}, temp2:{'graphite':_, 'xs_set':_}, ...}
        self._xs_dict = {1500: {'graphite': 'grph1500', 'xs_set': '15c'},
                        1200: {'graphite': 'grph1200', 'xs_set': '12c'},
                         900: {'graphite':  'grph900', 'xs_set': '09c'},
                         600: {'graphite':  'grph600', 'xs_set': '06c'},
                         300: {'graphite':  'grph300', 'xs_set': '03c'},}
        ## (str, default: 'g0_' + self.mesh_location) Tracks previous universe of pebble.
        self._previous_universe = 'g0_' + self._mesh_location

        self.set_universe()
        
        ## (dict, default: self.set_xs_set(self.temperature)) Cross-section set and scattering library based on the temperature.
        self._xs_library, self._scattering_library = self.set_xs_set(self._temperature)
        ## (dict, default: ) Dictionary of the geometry in the pebble \n
        ## Each entry describes a part of the geometry, where a given radius and number of instances are used to calculate the volume \n 
        ## Takes the form: {'geometry_name': {'radius': float, 'number_of_instances': int, 'volume': float}}.
        self._geometry = {'matrix':    {'radius': self._inner_radius,    'number_of_instance': 1, 'volume': 0.0},
                         'pebshell':  {'radius': radius, 'number_of_instance': 1, 'volume': 0.0}}
        self.calculate_volumes()

    def calculate_volumes(self):
        """!
        Calculate the volume for each constituent part of the pebble
        """
        previous_volume = 0.0
        for data in self._geometry.values():
            volume = math.pi * 4 / 3 * math.pow(data['radius'], 3) 
            total_region_volume = volume * data['number_of_instance']
            data['volume'] = total_region_volume - previous_volume
            previous_volume = total_region_volume 

    def set_xs_set(self, temperature):
        """!
        Grab the correct cross-section set and scattering library based on the temperature
        """
        dict_array = np.array([x for x in self._xs_dict.keys()])
        temp = dict_array[dict_array<temperature].max() if temperature not in self._xs_dict.keys() else temperature
        return self._xs_dict[temp]['xs_set'], self._xs_dict[temp]['graphite']
        
    def update_position(self, x, y, z, r, channel, volume, shuffled=False):
        """!
        Update the position of the pebbles after a shift or refuel.
        """
        self._shuffled = shuffled
        self._x = x
        self._y = y
        self._z = z
        self._r = r
        self._channel_num = channel
        self._volume_num = volume
        self._mesh_location = f'c{channel}v{volume}'
        self.set_universe()

    def set_previous_universe(self, prev_universe):
        """!
        Update the previous universe after a shift or refuel
        """
        self._previous_universe = prev_universe

    def increase_pass(self):
        """!
        When pebble is refueled, increse the number of passes it has gone through.
        """
        self._num_passes += 1
    
    def set_universe(self):
        """!
        Update the current universe of the pebbble, if this is not the first pass (i.e. it has been shuffled, add the previous universe to the current pebble location
        """
        if self._shuffled:
            self._universe = self._previous_universe + '_' + self._mesh_location
        else:
            split_univ = self._previous_universe.split('_')[1:]
            univ = '' if len(split_univ) == 1 else '_'.join([x for x in split_univ[:-1]]) + '_'
            self._universe = f'g_' + univ + self._mesh_location 
            #self._universe = f'g_' + f'p{self._num_passes}_' + f'bu{self._burnup_group}_ + univ + self._mesh_location
    
    def update_pebble_temperature(self,pebble_temp,fuel_temp=None):
        """!
        Update the pebble temperature and corresponding cross-section/scattering libraries.
        """
        self._temperature = pebble_temp
        self._xs_library, self._scattering_library = self.set_xs_set(pebble_temp)

class FuelPebble(Pebble):
    """!
    Class for holding information for an individual pebble.
    """
    
    def __init__(self, x, y, z, r, radius, channel, volume, fuel_material=None, homogenization_group=0, temperature=900.0,  fuel_temperature=900.0, pass_limit=6, pebble_number=0, kernel_data=None):
        ## (int, default: 0) Index used to indicate which pebbles are homogenized within a volume.
        self._homogenization_group = homogenization_group
        super().__init__(x, y, z, r, radius, channel, volume, temperature=temperature, pass_limit=pass_limit, pebble_number=pebble_number)
        ## (str, default: 'fuel') Designation if this is a graphite or fuel pebble.
        self._pebble_type = 'fuel'
        ## (dict, default: None) Stores geometric information of TRISO particles within pebble matrix region in centimeters \n
        ## Stored in the form {'layer_name': outer_radius_of_layer(float), ..., 'kernels_per_pebble': number_kernels}
        self._kernel_data = kernel_data if kernel_data else {'fuel':0.02125, 'buffer':0.03125, 'inner_pyc':0.03525, 'sic':0.03875, 'outer_pyc':0.04275, 'kernels_per_pebble': 18775}
        ## (int, default: None) Number of TRISO particles in the matrix of an individual pebble.
        self._kernels_per_pebble = self._kernel_data.pop('kernels_per_pebble')
        ## (dict, default : ) Dictionary of material compositions for fueled pebbles including all TRISO laters \n
        ## Contains 'fuel', 'buffer', 'inner_pyc', 'sic', 'outer_pyc', 'martix', and 'pebshell' \n
        ## Stored in the form {'material':{'ZAID':atom_density, ...}, ...}.
        self._material = {'fuel':      {'92235': 3.70100E-3, '92238': 1.99216E-2,  '8016': 3.37331E-1, '6000': 9.26006E-3, '5010': 1.87091E-8, '5011': 7.57813E-8},
                         'buffer':    { '6000': 5.26466E-2,  '5010': 1.35512E-8,  '5011': 5.48894E-8},
                         'inner_pyc': { '6000': 9.52653E-2,  '5010': 2.45213E-8,  '5011': 9.93236E-8},
                         'sic':       {'14028': 4.43271E-2, '14029': 2.25082E-3, '14030': 1.48376E-3, '6000': 4.80616E-2,  '5010': 1.23711E-8,  '5011': 5.0109E-8},
                         'outer_pyc': { '6000': 9.52653E-2,  '5010': 2.45213E-8,  '5011': 9.93236E-8},
                         'matrix':    { '6000': 8.67416E-2,  '5010': 2.23273E-8,  '5011': 9.04368E-8},
                         'pebshell':  { '6000': 8.67416E-2,  '5010': 2.23273E-8,  '5011': 9.04368E-8}}
        ## (float, default: 900) Averaged fuel kernel temperature in Kelvin.
        self._fuel_temperature = fuel_temperature
        ## (_previous_universe** : str, default: f'f{self.homogenization_group}_' + self.mesh_location) Concatinated string containing the previous universes the pebble was exposed to \n
        ## If the pebble is homogenized after each pass, we default the previous universes to c0v0.
        self._previous_universe = f'f{self._homogenization_group}_' + self._mesh_location

        self.set_universe()
        self._previous_universe = self._universe

        ## (_triso_volume** : float, default: 18687 * 0.0000402) Volume of the fuel kernels in the pebble (required for correct burnup).
        self._triso_volume = self._kernels_per_pebble * 0.0000402
        ## (float, default: 0.) Number of megawatt days the pebbles has been in the core (days * power) [MWd].
        self._power_days = 0.
        ## (float, default: 0.) Current power density for the pebble (this is the power density for all pebbles of the same fuel type, same pass number, and in the same core location) [MW/cm3]
        self._power_density = 0.
        ## (float, default:0) Tracks how long the pebbles has been in-core.
        self._days_in_core = 0

        if fuel_material:
            self._material['fuel'] = fuel_material
        
        ## (dict, default: self.set_xs_set(self.lial2_temperature)[0]) Dictinary storing cross sections for the fuel at the current temperature.
        self._xs_fuel_library, self._fuel_scattering_library = self.set_xs_set(self._fuel_temperature)
        ## (dict, default: ) Dictionary containing geometry data for fuel pebble and TRISO particles \n
        ## Stored in the form {'layer':{'radius':outer_radius_of_layer, 'number_of_instances':number_of_layer_in_pebble}, ...}.
        self._geometry = {'fuel':      {'radius': self._kernel_data['fuel'],      'number_of_instance': self._kernels_per_pebble, 'volume': 0},
                         'buffer':    {'radius': self._kernel_data['buffer'],    'number_of_instance': self._kernels_per_pebble, 'volume': 0},
                         'inner_pyc': {'radius': self._kernel_data['inner_pyc'], 'number_of_instance': self._kernels_per_pebble, 'volume': 0},
                         'sic':       {'radius': self._kernel_data['sic'],       'number_of_instance': self._kernels_per_pebble, 'volume': 0},
                         'outer_pyc': {'radius': self._kernel_data['outer_pyc'], 'number_of_instance': self._kernels_per_pebble, 'volume': 0},
                         'matrix':    {'radius': self._inner_radius, 'number_of_instance': 1},
                         'pebshell':  {'radius': radius, 'number_of_instance': 1}}
        self.calculate_volumes()
        

    def update_fuel_material(self, material):
        """!
        Update the fuel material
        """
        self._material['fuel'] = material

    def update_burnup(self, power, days):
        """!
        Add up the total power days the pebble has been in the core.
        Divide by the kg of HM originally in the pebble (currently assumed to be 7 g or 0.007 kg)
        To obtain the burnup in J/cm^3 
        """
        self._days_in_core += days
        self._power_density = power / (1E6) # Convert from W to MW, power of an individual pebble
        self._power_days += (self._power_density * days)
        self._burnup =  self._power_days / 0.007 # MWd/kg
        self._burnup_j_cm3 = self._power_days / self._triso_volume * 1E6 * 86400# for J/cm^3 we divide the power days (Watt-day or J/s * days) by the kernel volume (cm^3) and convert to MJ from J (1E6) and from days to seconds (86,400 s/day)
        
    def set_universe(self):
        """!
        Update the current universe of the pebbble, if this is not the first pass (i.e. it has been shuffled, add the previous universe to the current pebble location        
        """
        if self._shuffled:
            self._universe = self._previous_universe + '_' + self._mesh_location
        else:
            split_univ = self._previous_universe.split('_')[1:]
            univ = '' if len(split_univ) == 1 else '_'.join([x for x in split_univ[:-1]]) + '_'
            self._universe = f'f{self._homogenization_group}_' + univ + self._mesh_location   
            
    def update_pebble_temperature(self,pebble_temp,fuel_temp=None):
        """!
        Update the temperatures (and corresponding cross-sections) for both the pebble and fuel materials.
        """
        self._temperature = pebble_temp
        self._fuel_temperature = fuel_temp
        self._xs_fuel_library, self._fuel_scattering_library = self.set_xs_set(fuel_temp)
        self._xs_library, self._scattering_library = self.set_xs_set(pebble_temp)
