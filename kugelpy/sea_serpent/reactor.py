'''
@author: balep, stewryan, ethan-fowler

Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED
'''

##
# @mainpage kugelpy
#
# @section description_main Description
# A Python wrapper for generating PBR input files for Serpent and conducting run-in,
# jump-in, and criticality searches.
#
# @section notes_main Notes
# 1. **default values** - Some tests require the initial hard-coded parameters 
#     to remain unchanged. If any tests fail the parameter values in the code should 
#     be compared to the default values provided in `user_variables.md` or 
#     `other_variables.md`. 
#
# 2. **proper core** - refers to the the region of the core containing explicitly 
#     modeled pebbles excluding the upper cone and lower conus. In simpler terms, 
#     any pebble-filled region where pebbles make contact with the side wall. 
#
# 3. **block vs reflector** - Blocks include the radial reflector outside the 
#     'proper core' and any components therein (dimples, control/safety rods, helium 
#     riser channels). Other reflectors are located above and below the radial 
#     reflectors and core, but these reflectors are not a part of blocks. The radial 
#     reflector is broken into blocks to help simplify model geometry. 
#
# 4. **adding detectors** - Detectors can be added using the `python 
#     SerpentReactor.create_user_detector()` method. Energy divisions for user-made 
#     detectors can be created using `SerpentReactor.create_energy_grid()`. These 
#     methods can only be called after the SerpentReactor or PebbleSorter objects 
#     have been created. 
#
# 5. **reactor materials** - `Kugelpy` assumes materials fit into one of 9 non-fuel 
#     core materials, fuels, or TRISO layer materials.  The 9 core materials are 
#     stored in `PebbleSorter.core_materials`, spacially-dependent fuel definitions 
#     are stored in `PebbleSorter.equilibrium_materials`, equilibrium fuel is stored 
#     in `PebbleSorter.equilibrium_fuel_material` and `PebbleSorter.fuel_material`, 
#     and TRISO layer materials are stored in `Pebble.material`. Equilibrium 
#     materials, fuel materials, and equilibrium fuel material require user input. 
#     The initial fuel definition passed to fuel material will be the start-up fuel 
#     composition. TRISO layer material and core materials have default values. 
#     core_materials can be changed by the user in the class instance call, but 
#     non-fuel material definitions for pebbles/TRISO must be edited in pebble.py 
#     directly for run-in/jump-in modeling. 
#
# 6. **material dictionary formatting** - While other information stored in 
#     dictionaries has a function for creating those dictionaries, Serpent materials 
#     can contain any number of isotopes so these dictionaries must be passed 
#     directly. General material dictionaries are formatted as such: 
#     ```python
#         {'zaid_ID_1': weight_density_1, 'zaid_ID_2': weight_density_2, etc.}
#     ```
#     . Fuel material definitions take these lists directly since fuel temperatures 
#     are updated separately, but core materials take additional arguments to 
#     account for moderation and temperatures. Core materials are formatted as such:
#     ```python
#         {'material_name': {'temperature': float(temperature), 'moder': str(moder_name), 'moder_nuclide': int(moder_nuclide_zaid_ID), 'nuclides': dict(material_dictionary)}}
#     ```
#
# 7. **pbed geometries** - Serpent's pbed geometries require a pbed geometry input 
#     file containing the x-, y-, and z-coordinates of the pebble as well as the 
#     pebble radius and universe name. By default, kugelpy uses a TRISO input file 
#     containing 18,775 particles randomly dispersed in a 2.5 centimeter sphere and 
#     a pebble geometry input file containing over 220,000 pebbles filling the core 
#     region of the GPBR (120 centimeter 'proper core', 55.438 centimeter tall lower 
#     conus, and upper cone). The pebble bed geometry input file can be changed 
#     using ```PebbleSorter.pebble_bed_name``` and the TRISO geometry input file can 
#     be changed using ```PebbleSorter.triso_dist_name```. For cores or pebbles 
#     smaller than those used in the GPBR, existing pbed input files can be used but 
#     may result in partially cut spheres or particles, which can introduce error in 
#     the model. 
# 
# 8. **running on HPCs** - Kugelpy was developed on the INL HPC and is therefore 
#     configured to make use of MPI parallel computing. For this reason jobs are 
#     submitted using `mpiexec`. When trying to use `perform_run_in` or 
#     `perform_jump_in` on HPC services, it is advised that the user submit a job 
#     script which runs the Python script. `Kugelpy` will automatically run Serpent 
#     jobs after the input files have been generated so long as `one_run==True`. To 
#     make sure that `Kugelpy` runs correctly, the user should review the following 
#     functions which are used to run Serpent: `SerpentReactor.run_serpent()`, 
#     `PebbleBed.write_serpent_pbs()`. 
#
# 9. **fatal errors** - If issues with fatal errors occur when attempting to run 
#     Serpent models, the `nofatal` flag can be set to true which will ignore certain 
#     fatal errors. 
#
# 10. **re-running models with existing files** - If re-running a model either 
#     completely or from a pickled save point using `SerpentReactor.loader()`, 
#     errors were encountered where existing files were not always over-written 
#     by the new run. For this reason, it is recommended that all model files 
#     after the starting time step be removed from the working directory. 
# 
# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

##
# @file reactor.py
#
# @section description_reactor Description
# Module for creating basic Serpent inputs.
#
# @section libraries_reactor Libraries/Modules
# - numpy
# - os
# - shutil
# - pickle
# - math
# - random
# - operator
#
# @section author_reactor Author(s)
# - Created by Ryan Stewart and Paolo Balestra
# - Modified by Ethan Fowler
#
# Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED

import numpy as np
import os
import shutil
import pickle
import math
import random 
import operator


class SerpentReactor(object):
       
    def __init__(self):
        ## Specifies directory where output files will be stored.
        self.output_dir = './'
        ## Specifies name of reactor input file(s).
        self.reactor_file_name = 'reactor'
        ## This parameters determines if the simulations will be perfored in a single pbs/slurm simulation, or if each step will be a unqiue PBS/slurm submission.
        self.one_run = True
        ## This parameter determines whether or not pickled save states are produced, which can be used to re-start the model from a specific step/time.
        self.save_state_point = False
        ## The value of this parameter determines when a pickled save state is created, if `save_state_point` is True.
        self.save_state_point_frequency = 10

        # Serpent run parameters
        ## ```Does nothing in SerpentReactor but is inherited by PebbleSorter``` \n
        ##  Specifies the number of neutrons per generation for Serpent model.
        self.num_particles = 20000
        ## ```Does nothing in SerpentReactor but is inherited by PebbleSorter``` \n
        ## Specifies the number of active generations for Serpent model.
        self.num_generations = 400
        ## ```Does nothing in SerpentReactor but is inherited by PebbleSorter``` \n
        ## Specifies the number of innactive generations for Serpent model.
        self.skipped_generations = 40
        ## ```Does nothing in SerpentReactor but is inherited by PebbleSorter``` \n
        ## Specifies the Serpent optimization option for burnup.
        self.burnup_optimization_num = 1

        ## This parameter includes the ```nofatal``` flag when running Serpent if set to True.
        self.nofatal = True
        ## Sets the number of threads per node used by the HPC when running Serpent.
        self.num_threads = 40
        
        ## List containing additional plots set by the user using ```Reactor.create_geom_plot()```
        self.geom_plots = []
        ## Stores cross-section data \n
        ##  Key should be an integer for the temperature in Kelvin (K), value is a dictionary; the first key is the material name, the first value is the cross-section library name (ex `grph1500`); the second key is xs_set, the value is the cross-section library extension (ex `15c`).Stores cross-section data \n
        #  Key should be an integer for the temperature in Kelvin (K), value is a dictionary; the first key is the material name, the first value is the cross-section library name (ex `grph1500`); the second key is xs_set, the value is the cross-section library extension (ex `15c`).
        self.xs_dict = {}
        ## Stores material data \n
        ## Key should be material name, value should be a dictionary where the key is an isotope/element name and the value is its atomic/weight fraction.
        self.materials = {}
        ## Internal variable which stores detector data and how to print the detectors in a Serpent input.
        self._detector_dict = {}
        ## Stores user-made detector data \n
        ## Updated using `SerpentReactor.create_user_detector()`.
        self.user_detector_dict = {}
        ## Stores energy grids which can be used in detectors \n
        ## Updated using `SerpentReactor.create_energy_grid`.
        self.energy_grid_dict = {}

    def build_fuel_pin(self, pin_name, fuel_mat, fuel_radius, clad_mat, clad_radius, coolant_mat):
        """!
        Create all of the details required for building the specific pin cell in Serpent
        """
        pin_dict = {'fuel': {'mat': fuel_mat, 'radius': fuel_radius}, 'clad': {'mat': clad_mat, 'radius': clad_radius}, 'coolant': {'mat': coolant_mat, 'radius': ''}}
        pin_str = self.create_pin_input(pin_name, pin_dict)
        return pin_dict, pin_str

    def create_pin_input(self, pin_name, pin_dict):
        """!
        Create the input file string for the pin 
        """
        pin_str = '% ----- Fuel Pin\n\n'
        pin_str += f'pin {pin_name}\n'
        for k,v in pin_dict.items():
            pin_str += f"{v['mat']} {v['radius']}\n"
        return pin_str

    def build_cylinder_surface(self, surface_name, cyl_type, radius, lower_height='', upper_height='', x_offset=0.0, y_offset=0.0, z_offset=0.0, u=0.0, v=0.0, w=0.0):
        radius = round(float(radius),5)
        lower_height = round(float(lower_height),5) if lower_height != '' else ''
        upper_height = round(float(upper_height),5) if upper_height != '' else ''
        if cyl_type == 'cylv':
            return f'surf {surface_name} {cyl_type} {x_offset} {y_offset} {z_offset} {u} {v} {w} {radius}\n'
        elif cyl_type == 'cylz':
            return f'surf {surface_name} {cyl_type} {x_offset} {y_offset} {radius} {lower_height} {upper_height}\n'
        elif cyl_type == 'cyly':
            return f'surf {surface_name} {cyl_type} {x_offset} {z_offset} {radius} {lower_height} {upper_height}\n'
        elif cyl_type == 'cylx':
            return f'surf {surface_name} {cyl_type} {y_offset} {z_offset} {radius} {lower_height} {upper_height}\n'
        else:
            raise ValueError(f"Unknown cylinder surface type {cyl_type}, please select from 'cylv', 'cylx', 'cyly', 'cylz'")
    
    def build_cuboid_surface(self, surface_name, lower_x, upper_x, lower_y, upper_y, lower_z, upper_z):
        return f'surf {surface_name} cuboid {lower_x} {upper_x} {lower_y} {upper_y} {lower_z} {upper_z}\n'

    def build_cell(self, cell_name, universe_name, material, inside_surfaces=[], outside_surfaces=[], outside_cells=[]):  
        i_surfaces = '-' + ' -'.join([x for x in inside_surfaces]) if inside_surfaces else ''
        o_surfaces = ' '.join([x for x in outside_surfaces])
        o_cell = '' if len(outside_cells) == 0 else '#' + ' #'.join([x for x in outside_cells])
        return f'cell {cell_name} {universe_name} {material} {i_surfaces} {o_surfaces} {o_cell}\n'

    def build_filled_universe(self, cell_universe_name, fill_universe, inside_surfaces=[], outside_surfaces=[], outside_cells=[]):  
        i_surfaces = '-' + ' -'.join([x for x in inside_surfaces])
        o_surfaces = ' '.join([x for x in outside_surfaces])
        o_cell = '' if len(outside_cells) == 0 else '#' + ' #'.join([x for x in outside_cells])
        return f'cell {cell_universe_name} {fill_universe} fill {cell_universe_name} {i_surfaces} {o_surfaces} {o_cell}\n'

    def build_universe(self, cell_universe_name, inside_surfaces=[], outside_surfaces=[], outside_cells=[]):  
        i_surfaces = '-' + ' -'.join([x for x in inside_surfaces])
        o_surfaces = ' '.join([x for x in outside_surfaces])
        o_cell = '' if len(outside_cells) == 0 else '#' + ' #'.join([x for x in outside_cells])
        return f'cell {cell_universe_name} 0 fill {cell_universe_name} {i_surfaces} {o_surfaces} {o_cell}\n'

    def build_filled_cell(self, cell_name, universe_name, material, inside_surfaces=[], outside_surfaces=[], outside_cells=[]):  
        i_surfaces = '-' + ' -'.join([x for x in inside_surfaces]) if inside_surfaces else ''
        o_surfaces = ' '.join([x for x in outside_surfaces])
        o_cell = '' if len(outside_cells) == 0 else '#' + ' #'.join([x for x in outside_cells])
        return f'cell {cell_name} {universe_name} fill {material} {i_surfaces} {o_surfaces} {o_cell}\n'

    def build_plane_surface(self, surf_name, plane_orientation, position):
        return f'surf {surf_name} p{plane_orientation} {position}\n'
    
    def convert_theta_to_uv(self, theta, r=1):
        return (r*math.sin(theta), r*math.cos(theta))

    def prune_burn_material(self, mat_dict):
        """!
        Remove materials in the BU file that have an atom density less than the user-defined limit
        """
        pruned_mat_dict = {}
        for isotope, a_dens in mat_dict.items():
            if a_dens > self.atom_density_limit:
                pruned_mat_dict[isotope] = a_dens
        return pruned_mat_dict  

    def set_xs_set(self, temperature):
        """!
        Set the cross-section set based on the temperature of the component.
        """
        if temperature < 294:
            return self.xs_dict[0]['xs_set']
        else:
            dict_array = np.array([x for x in self.xs_dict.keys()])
            temp = dict_array[dict_array<temperature].max() if temperature not in self.xs_dict.keys() else temperature
        return self.xs_dict[temp]['xs_set']
        
    def create_geom_plot(self, ptype, xpix, ypix, pos=None, min1=None, max1=None, min2=None, max2=None):
        """!
        Create a Serpent geometry plot 
        """
        temp_geom_plot = {'type':ptype, 'xpix':xpix, 'ypix':ypix, 'pos':pos, 'min1':min1, 'max1':max1, 'min2':min2, 'max2':max2}
        self.geom_plots.append(temp_geom_plot)

    def create_energy_grid(self, name, type, boundaries):
        '''!
        Creates an energy grid which can be used by detectors

        @param name         (str) Name of energy grid
        @param type         (int) Specifies how boundaries should be formatted. For list of detector types, see Serpent documentation
        @param boundaries   (list) Contains boundaries as specified by energy grid type. Energy units in MeV. For formatting, see Serpent documentation
        '''

        energy_grid = {'type': type,
                       'boundaries': boundaries}
        
        energy_grid_str = f'ene {name} {energy_grid["type"] }'
        energy_grid_str += f' {" ".join([str(boundary) for boundary in energy_grid["boundaries"]])}'
        energy_grid_str += '\n'
        self.energy_grid_dict[name] = {'energy_grid':energy_grid, 'energy_grid_str':energy_grid_str}

    def create_detector(self, name, particle_type='n', energy_bins=None, surface=None, direction=None, cell=None, universe=None, materials=None, responses=None, micro_xs=True, axial_variation=None, cylindrical_variation=None):
        '''!
        For formatting of detector elements, see Serpent documentation
        '''
        detector = {'surface':       surface,
                    'cell':          cell,
                    'universe':      universe,
                    'energy_bins':   energy_bins,
                    'materials':     materials,
                    'reaction_rate': responses,
                    'axial_variation': axial_variation,
                    'cylindrical_variation': cylindrical_variation
                    }
                    
        det_str = f'det {name} {particle_type} '
        det_str += f'ds {surface} {direction} ' if surface else ''
        det_str += f'dc {cell} ' if cell else ''
        det_str += f'du {universe} ' if universe else ''
        det_str += f'de {energy_bins} ' if energy_bins else ''
        det_str += f'dz {" ".join([str(x) for x in axial_variation])}' if axial_variation else ''
        if cylindrical_variation:
            det_str += f'dn 1 '
            for key in ['r', 'theta', 'z']:
                for index in range(3):
                    det_str += f'{str(cylindrical_variation[key][index])} '

        if materials and micro_xs:
            assert len(materials) == len(responses)
            for mat, rr in zip(materials, responses):
                det_str += f'dr {rr} {mat} '
        elif materials:
            assert len(materials) == len(responses)
            for mat, rr in zip(materials, responses):
                det_str += f'dr {rr} void dm {mat}'
        det_str += '\n'
        self._detector_dict[name] = {'detector': detector, 'detector_str': det_str}    
    
    def create_user_detector(self, name, particle_type='n', energy_bins=None, surface=None, direction=None, cell=None, universe=None, materials=None, responses=None, micro_xs=True, axial_variation=None, cylindrical_variation=None):
        '''!
        For formatting of detector elements, see Serpent documentation
        '''
        detector = {'surface':       surface,
                    'cell':          cell,
                    'universe':      universe,
                    'energy_bins':   energy_bins,
                    'materials':     materials,
                    'reaction_rate': responses,
                    'axial_variation': axial_variation,
                    'cylindrical_variation': cylindrical_variation
                    }
                    
        det_str = f'det {name} {particle_type} '
        det_str += f'ds {surface} {direction} ' if surface else ''
        det_str += f'dc {cell} ' if cell else ''
        det_str += f'du {universe} ' if universe else ''
        det_str += f'de {energy_bins} ' if energy_bins else ''
        det_str += f'dz {" ".join([str(x) for x in axial_variation])}' if axial_variation else ''
        if cylindrical_variation:
            det_str += f'dn 1 '
            for key in ['r', 'theta', 'z']:
                for index in range(3):
                    det_str += f'{str(cylindrical_variation[key][index])} '

        if materials and micro_xs:
            assert len(materials) == len(responses)
            for mat, rr in zip(materials, responses):
                det_str += f'dr {rr} {mat} '
        elif materials:
            assert len(materials) == len(responses)
            for mat, rr in zip(materials, responses):
                det_str += f'dr {rr} void dm {mat}'
        det_str += '\n'
        self.user_detector_dict[name] = {'detector': detector, 'detector_str': det_str}    
        

    def keep_solutions(self, step):
        """!
        Keep all of the input/output files for each step
        """
        solution_path = os.path.join(self.output_dir, f'step_{step}')

        if not os.path.isdir(solution_path):
            os.mkdir(solution_path)
        for file in os.listdir(self.output_dir):
            if os.path.isfile(os.path.join(self.output_dir,file)) and file != 'reactor_status.csv' and 'run_des' not in file:
                old_file_path = os.path.join(self.output_dir, file)
                new_file_path = os.path.join(solution_path, file)
                shutil.move(old_file_path, new_file_path)  

    def run_serpent(self, step):
        """!
        Submit a serpent job to the HPC and wait for the results
        """
        cwd = os.getcwd()
        os.chdir(self.output_dir)
        if self.one_run:
            print(f'Starting Step {step}')
            if self.nofatal:
                os.system(f'mpiexec sss2 {self.reactor_file_name} -nofatal -omp {self.num_threads}')
            else:
                os.system(f'mpiexec sss2 {self.reactor_file_name} -omp {self.num_threads}')

        else:
            print(f'Starting {step}')
            os.system('qsub -W block=true serpent.pbs')
        
        os.chdir(cwd)

    def plot_serpent(self):
        """!
        Submit a serpent job to the HPC and wait for the results
        """
        self.create_solutions_file()
        self.update_temperature_profile()
        self.read_in_pebble_dist()
        self.setup_core()

        cwd = os.getcwd()
        os.chdir(self.output_dir)
        if self.one_run:
            os.system(f'mpiexec sss2 {self.reactor_file_name} -nofatal -plot -omp 40')
        
        os.chdir(cwd)


    def save(self, step):
        """!
        Save the current state of the scenario; this will create a pickle file which can be used with the loader function.
        Note: We save the file at the at the begining of the burnstep, so when reloading we are forced to rerun the same step before continuing.
        """
        step_path = os.path.join(self.output_dir, f'step_{step}/')
        dir_ = step_path if os.path.isdir(step_path) else self.output_dir       
        file_name = os.path.join(dir_, f'savepoint_step{step}.pkl')
        file = open(file_name, 'wb')
        pickle.dump(self,file,2)

    @classmethod
    def loader(cls,output_dir,step):
        """!
        Load the pickled save point and return the class.
        """
        step_path = os.path.join(output_dir, f'step_{step}/')
        dir_ = step_path if os.path.isdir(step_path) else output_dir 
        file_name = os.path.join(dir_, f'savepoint_step{step}.pkl')
        file = open(file_name, 'rb')
        return pickle.load(file)
    
    def set_random_seed(self, seed):
        """!
        Set the random seed for the problem
        """
        self.random_seed = seed
        random.seed(seed)
    
    def combine_dicts(self, a, b):   
        """!
        Combine two dictionaries and add common values
        """
        return {**a, **b, **{k: operator.add(a[k], b[k]) for k in a.keys() & b}}
        
    def convert_xy_to_r(self, x, y):
        """!
        Calculate the radius of the RZ system based on the XY coordinates.
        """
        return math.sqrt(pow(x, 2) + pow(y, 2))
    
    def prune_burn_material(self, mat_dict):
        """!
        Remove materials in the BU file that have an atom density less than the user-defined limit
        """
        pruned_mat_dict = {}
        for isotope, a_dens in mat_dict.items():
            if a_dens > self.atom_density_limit:
                pruned_mat_dict[isotope] = a_dens
        return pruned_mat_dict 