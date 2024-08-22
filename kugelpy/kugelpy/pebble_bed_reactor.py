'''
@authors: balep, stewryan, ethan-fowler

Copyright 2024, Battelle Energy Alliance, LLC, ALL RIGHTS RESERVED
'''

import math
from kugelpy.kugelpy.sea_serpent.reactor import SerpentReactor
import os

class PebbleBedReactor(SerpentReactor):
    
    def __init__(self, **kwargs):
        
        super().__init__()

        ## (str, default: 'pf61_Step1.pbed') Name of file containing pebble bed geometry \n
        ## For pebble bed regions that differ significantly, or for different size pebbles, this variable will need to be the name of the file supplied by the user located in`/kugelpy/kugelpy/data/`.
        self.pebble_bed_name = 'pf61_Step1.pbed'
        ## (str, default: 'pbr_structure.inp') Name of file that stores the general core structure surfaces and cells generated by `PebbleBedReactor.write_pbr_core()`.
        self.core_file_name = 'pbr_structure.inp'
        ## (str, default: '') Name of directory where output files are stored.
        self.output_dir = ''
        ## (str, default: 'reflector') Name of material, which can be found in `PebbleSorter.core_materials`, composing the reflector blocks.
        self._block_material = 'reflector'
        ## (str, default: 'pebble_shoot') Name of the homogenized material, which can be found in `PebbleSorter.core_materials`, composing the pebble chute region where burned fuel is removed from the core.
        self._pebble_shoot_material = 'pebble_shoot'
        ## (str, default 'outlet_plenum') Name of material, which can be found in `PebbleSorter.core_materials`, composing the outlet plenum where hot helium exits the core.
        self._outlet_plenum_material = 'outlet_plenum'
        ## (str, default: 'outlet_channel') Name of material composing the outlet channel (see figure). 
        self._outlet_channel_material = 'outlet_channel'
        ## (str, default: 'safety_rod') Name of material composing the safety rods/shutdown rods.
        self._safety_rod_material = 'safety_rod'
        ## (str, default: 'control_rod') Name of material composing the control rods.
        self._control_rod_material = 'control_rod'
        ## (str, default: 'helium') Name of material filling reactor cavities (background universe for pebble bed geometry).
        self._cavity_material = 'helium'
        ## (str, default: 'riser') Name of material filling the helium riser region.
        self.riser_material = 'helium'
        ## (str, default: 'helium') Name of material filling the empty region(s) of the control rods.
        self._control_rod_cavity_material = 'helium'
        ## (bool, default: True) Parameter used to determine whether the reactor will have dimples along the inner wall of the reflector \n
        ## Dimples serve an important role in pebble flow but have little neutronic worth and introduce additional surfaces which can make the model run slower.
        self.create_dimples = True
        ## (bool, default: False) Parameter used to create a simplified pebble bed model \n 
        ## If this parameter is set to True the model will only include a cylindrical core, radial reflectors/blocks, pebbles, and upper and lower reflectors.
        self.simple_core = False
        ## (float, default: 70.772) The height in centimeters (cm) of the cone used to create the lower conus (NOT height of conus) \n 
        ## Note, 70.772cm gives a conus height of 55.438cm.
        self.conus_height = 70.772 
        ## (float, default: 0) Vertical position in centimeters (cm) of the bottom of the lower conus \n 
        ## This is determined based on where the bottom of the pebbles are in the pebble file (see `pebble_bed_name`).
        self.conus_z_offset = 0
        ## (float, default: 85.438) The total height in centimeters (cm) of the actual conus height (NOT cone) plus 30 cm.
        self.conus_channel_height = 85.438 # Note, the conus channel is the total height of the conus plus 30 cm of height
        ## (float, default: 26.0) Radius in centimeters (cm) of the pebble chute located below the conus and through the outlet plenum and lower reflector.
        self.pebble_shoot_radius = 26.0
        ## (float, default: 185.1) Height in centimeters (cm) of the pebble chute located at the bottom of the core.
        self.pebble_chute_height = 185.1
        ## (float, default: 58.4) Height in centimeters (cm) of the reflector spanning from the bottom of the reactor to the bottom of the lower plenum.
        self.bottom_reflector_height = 58.4
        ## (float, default: 96.7) Height in centimeters (cm) of the lower plenum spanning from the top of the bottom reflector to the bottom of the lower pebble bed support/conus.
        self.outlet_plenum_height = 96.7
        ## (float, default: 0.0) Depth of the control rod [centimeters (cm)] into the active core region \n 
        ## At 0.0, conrtrol rods are at the top of the upper conus \n
        ## A negative value indicates pulling the control rods futher above the conus, positive puts the control rods futher into the core.
        self.cr_insertion_depth = 0.0
        ## (float, default: -25.0) Depth of the safety rod [centimeters (cm)] into the active core region \n
        ## At 0.0, safety rods are at the top of the upper conus \n
        ## A negative value indicates pulling the safety rods futher above the conus, positive puts the safety rods futher into the core.
        self.sr_insertion_depth = -25.0
        ## (float, default: 133) Radius/distance in centimeters (cm) from the center of the core to the center of the control rod cavity.
        self.radius_to_cr_center = 133
        ## (float, default: 6.25) Radius in centimeters (cm) of the control and safety rods.
        self.control_rod_radius = 6.25
        ## (float, default: 6.5) Radius in centimeters (cm) of the cavities containing the control and safety rods.
        self.control_rod_cavity_radius = 6.5
        ## (float, default: 178.5) Radius/distance in centimeters (cm) from the center of the core to the center of the helium riser channels.
        self.radius_to_riser_center = 178.5
        ## (float, default: 8.5) Radius in centimeters (cm) of the helium riser channels.
        self.riser_radius = 8.5
        ## (float, default: 45.8) Height in centimeters (cm) of the helium region above the upper conus of the pebble bed.
        self.cavity_height = 45.8
        ## (float, default: 86.0) Height in centimeters (cm) of the reflector located above the core cavity. 
        self.top_reflector_height = 86.0
        ## (float, default: 2.5) Radius in centimeters (cm) of the fueled matrix region of the pebbles loaded in the core \n
        ## Currently the value in `Pebble` does not affect the radius printed in Serpent.
        self.pebble_inner_radius = 2.5
        ## (float, default: 3.0) Radius in centimeters (cm) of the pebbles loaded in the core \n
        ## Currently the value in `Pebble` does not affect the radius printed in Serpent.
        self.pebble_outer_radius = 3.0
        ## (float, default: 893.0) Height in centimeters (cm) of the 'proper core' \n
        ## This refers to where the pebbles touch the side walls, ie does not include the upper or lower conus.
        self.pebble_bed_height = 893.0  
        ## (float, default: 20.5) Axial distance between dimples in adjacent blocks \n
        ## Note, dimples are not included in geometry if `create_dimples` is set to False.
        self.dimple_axial_offset = 20.5
        ## (float, default: 17.5) Radius in centimeters (cm) of the cylindrical dimples set in the side of the core wall/reflector inner wall \n 
        ## Note, dimples are not included in geometry if `create_dimples` is set to False.
        self.dimple_radius = 17.5
        ## (float, default: 3.0) Depth in centimeters (cm) of the cylindrical dimples set in the side of the core wall/reflector inner wall \n
        ## Note, dimples are not included in geometry if simple_core is set to True or `create_dimples` is set to False.
        self.dimple_depth = 3.0
        ## (int, default: 12) The number of cylindrical dimples in a vertical column along the core wall/reflector inner wall \n
        ## The total number of dimples is `num_dimples`*`number_of_blocks`.
        self.num_dimples = 12      
        ## (float, default: 120.0) The inner radius in centimeters of the reflector \n
        ## The core is assembled in repeating blocks around the 'proper core' region, so block generally refers to the reflector along with other components including dimples, control rods, safety rods, and helium riser channels.
        self.block_inner_radius = 120.0
        ## (float, default: 206.6) The outer radius in centimeters (cm) of the reflector \n
        ## The core is assembled in repeating blocks around the 'proper core' region, so block generally refers to the reflector along with other components including dimples, control rods, safety rods, and helium riser channels.
        self.block_outer_radius = 206.6
        ## (float, default: block_inner_radius + dimple_depth) Distance from the core centerline to the outer face of a dimple in centimeters (cm).
        self.pebble_bed_dimple_radius = self.block_inner_radius + self.dimple_radius
        ## (int, default: 18) This parameter determines the number of blocks used to generate the radial reflector region located outside the 'proper core', which exludes the upper cone and lower conus. Each block contains a control rod or safety rod, helium riser channel, and column of dimples. Therefore the number of control rods, helium riser channels, and dimples are changed by changing this value.
        self.number_of_blocks = 18
        ## (dict, default: {}) Contains information about the blocks used to define the radial reflector region \n
        ## This parameter is generally changed using `build_block().`
        self._block_dict = {}
        ## (dict, default: {}) Dictionary storing geometry information used to build the reactor model.
        self._reactor_dict = {}
        ## (float, default: 360 / self.number_of_blocks) Angle between the centerlines of neighboring blocks.
        self._block_angle = 360 / self.number_of_blocks
        ## (list, default: ) List of angles of centerline for each block \n
        ##  We added the 90 degree rotation to align with the pebble model generated from ProjectChrono.
        self._block_angles = [self._block_angle * block_num + 90 for block_num in range(self.number_of_blocks)] 

        for k,v in kwargs.items():
            setattr(self, k, v)

        if self.simple_core:
            self.conus_height = 0.0
            self.conus_channel_height = 0.0
            self.outlet_plenum_height = 0.0
            self.cavity_height = 0.0

        self.__init__heights()
        
    def __init__heights(self):
        self.lower_model_height = -(self.bottom_reflector_height + self.conus_channel_height + self.outlet_plenum_height)

        self.bottom_reflector_lower_height = self.lower_model_height
        self.bottom_reflector_upper_height = self.bottom_reflector_lower_height + self.bottom_reflector_height
        
        self.outlet_plenum_lower_height = self.bottom_reflector_upper_height
        self.outlet_plenum_upper_height = self.outlet_plenum_lower_height + self.outlet_plenum_height    
        
        self.outlet_channel_lower_height = self.outlet_plenum_upper_height
        self.outlet_channel_upper_height = self.outlet_channel_lower_height + self.conus_channel_height
        
        self.pebble_shoot_lower_height = self.lower_model_height
        self.pebble_shoot_upper_height = self.pebble_shoot_lower_height + self.pebble_chute_height     
        
        self.pebble_bed_lower_height = self.outlet_channel_upper_height
        self.pebble_bed_upper_height = self.pebble_bed_lower_height + self.pebble_bed_height
        
        self.cavity_lower_height = self.pebble_bed_upper_height
        self.cavity_upper_height = self.cavity_lower_height + self.cavity_height
        
        self.top_reflector_lower_height = self.cavity_upper_height
        self.top_reflector_upper_height = self.top_reflector_lower_height + self.top_reflector_height    
        
        self.model_upper_height = self.top_reflector_upper_height
        
        self.control_rod_lower_height = self.pebble_bed_lower_height
        self.control_rod_upper_height = self.model_upper_height

        self.riser_lower_height = self.pebble_bed_lower_height
        self.riser_upper_height = self.cavity_upper_height
    
    def build_block(self, block_id, angle):
        """
        Collection of function required to build a reflector block.
        """
        self._block_dict[block_id] = {'surfaces': {'block': '', 'dimples': '', 'control_rods': '', 'risers': ''},
                                     'cells': {'block': '', 'dimples': '', 'control_rods': '', 'risers': ''},
                                     'universes': {'block': '', 'dimples': '', 'control_rods': '', 'risers': ''},}
        
        surfaces_to_skip = []
        cells_to_skip = []
        self._block_dict[block_id]['surfaces']['block'] = self.build_block_surface(block_id, self.block_inner_radius, self.block_outer_radius, angle, angle+self._block_angle)
        
        if self.create_dimples:
            dimple_surface_names, dimple_surfaces = self.build_dimple_surfaces(block_id, self.dimple_radius, angle, self.num_dimples)
            self._block_dict[block_id]['surfaces']['dimples'] = dimple_surfaces
            dimple_cell_names, dimple_cells = self.build_dimple_cells(block_id,self.num_dimples)
            self._block_dict[block_id]['cells']['dimples'] = dimple_cells
            self._block_dict[block_id]['universes']['dimples'] = self.build_dimple_universes(block_id,self.num_dimples)
            cells_to_skip += dimple_cell_names
        
        if not self.simple_core:
            # Grab all of the surfaces, cells, and universes for the safety and control rods
            rod_type = 'cr' if block_id % 2 == 0 else 'sr'
            cr_insertion_depth = self.cr_insertion_depth if rod_type == 'cr' else self.sr_insertion_depth
            rod_material = self._control_rod_material if rod_type == 'cr' else self._safety_rod_material
            control_rod_surface_names, control_rod_surfaces = self.build_rod_surfaces(block_id, self.radius_to_cr_center, self.control_rod_radius, angle, rod_type, self.pebble_bed_upper_height - cr_insertion_depth, self.control_rod_upper_height)
            self._block_dict[block_id]['surfaces']['control_rod'] = control_rod_surfaces
            control_rod_cell_names, control_rod_cells = self.build_rod_cells(block_id, rod_type, rod_material)
            self._block_dict[block_id]['cells']['control_rod'] = control_rod_cells
            self._block_dict[block_id]['universes']['control'] = self.build_rod_universe(block_id, rod_type)
            cells_to_skip += control_rod_cell_names        

            control_rod_cavity_surface_names, control_rod_cavity_surfaces = self.build_rod_surfaces(block_id, self.radius_to_cr_center, self.control_rod_cavity_radius, angle, 'cr_cavity', self.control_rod_lower_height, self.control_rod_upper_height)
            self._block_dict[block_id]['surfaces']['control_rod_cavity'] = control_rod_cavity_surfaces
            control_rod_cavity_cell_names, control_rod_cavity_cells = self.build_rod_cells(block_id, 'cr_cavity', self._cavity_material, cells_to_skip=control_rod_cell_names)
            self._block_dict[block_id]['cells']['control_rod_cavity'] = control_rod_cavity_cells
            self._block_dict[block_id]['universes']['control_rod_cavity'] = self.build_rod_universe(block_id, 'cr_cavity',cells_to_skip=control_rod_cell_names)
            cells_to_skip += control_rod_cavity_cell_names        

            # Grab all of the surfaces, cells, and universes for the risers
            rod_type = 'riser'
            risers_surface_names, risers_surfaces = self.build_rod_surfaces(block_id, self.radius_to_riser_center, self.riser_radius, angle, rod_type, self.riser_lower_height, self.riser_upper_height)
            self._block_dict[block_id]['surfaces']['risers'] = risers_surfaces
            risers_cell_names, risers_cells = self.build_rod_cells(block_id, rod_type, self.riser_material)
            self._block_dict[block_id]['cells']['risers'] = risers_cells
            self._block_dict[block_id]['universes']['risers'] = self.build_rod_universe(block_id, rod_type)
            cells_to_skip += risers_cell_names  
        
        self._block_dict[block_id]['cells']['block'] = self.build_block_cell(block_id,surfaces_to_skip=surfaces_to_skip,
                                                                           cells_to_skip=cells_to_skip)
        self._block_dict[block_id]['universes']['block'] = self.build_block_universe(block_id,surfaces_to_skip=surfaces_to_skip,
                                                                                       cells_to_skip=cells_to_skip)

    def build_all_blocks(self):
        # Grab all of the surfaces, cells, and universes for the dimples
        if self.create_dimples:
            self._reactor_dict['dimples'] = {'surface': self.build_cylinder_surface('inner_dimple', 'cylz', self.block_inner_radius, lower_height=self.pebble_bed_lower_height, upper_height=self.pebble_bed_upper_height)}
            self._reactor_dict['dimples']['surface'] += self.build_cylinder_surface('outer_dimple', 'cylz', self.block_inner_radius + self.dimple_depth, lower_height=self.pebble_bed_lower_height, upper_height=self.pebble_bed_upper_height) 

        for block_id, angle in enumerate(self._block_angles):
            self.build_block(block_id, angle)
    
    def build_pbr_core(self):
        if self.simple_core:
           self.build_bottom_reflector()
           self.build_all_blocks()
           self.build_pebble_bed()
           self.build_pebble()
           self.build_top_reflector()
           self.build_outside()         
        else:
            self.build_pebble_shoot()  
            self.build_conus(z_offset=self.conus_z_offset, radius=self.block_inner_radius, height=self.conus_height)
            self.build_outlet_plenum()
            self.build_outlet_channel()
            self.build_bottom_reflector()
            self.build_all_blocks()
            self.build_pebble_bed()
            self.build_pebble()
            self.build_cavity()
            self.build_top_reflector()
            self.build_outside()
    
    def build_conus(self, surface_name='conus_s', x_offset=0.0, y_offset=0.0, z_offset=0.0, radius=0.0, height=0.0):
        surf = f'surf {surface_name} cone {x_offset} {y_offset} {z_offset} {radius} -{height}\n'
        surf += f'trans s conus_s rot 0.0 0.0  {z_offset}      0. 0. 1. 180.\n'
        surf += f'surf upper_cone pz {self.pebble_bed_lower_height}'
        self._reactor_dict['conus'] = {'surface': surf}
        self._reactor_dict['conus']['cells'] = self.build_filled_cell('cone_c', 'cone_u', 'pebble_bed', ['conus_s'])
        self._reactor_dict['conus']['universes'] = self.build_universe('cone_u', ['conus_s', 'upper_cone'], outside_surfaces=['pebble_shoot_s'])

    def build_outlet_plenum(self):
        surf = self.build_cylinder_surface('outlet_plenum_s', 'cylz', self.block_inner_radius, lower_height=self.outlet_plenum_lower_height, upper_height=self.outlet_plenum_upper_height)
        self._reactor_dict['outlet_plenum'] = {'surface': surf}
        self._reactor_dict['outlet_plenum']['cells'] = self.build_cell('outlet_plenum_c', 'outlet_plenum_u', self._outlet_plenum_material, ['outlet_plenum_s'], outside_surfaces=['pebble_shoot_s'])
        self._reactor_dict['outlet_plenum']['universes'] = self.build_universe('outlet_plenum_u', ['outlet_plenum_s'], outside_surfaces=['pebble_shoot_s'])
        
    def build_outlet_channel(self):
        surf = self.build_cylinder_surface('outlet_channel_s', 'cylz', self.block_inner_radius, lower_height=self.outlet_channel_lower_height, upper_height=self.outlet_channel_upper_height)
        self._reactor_dict['outlet_channel'] = {'surface': surf}
        self._reactor_dict['outlet_channel']['cells'] = self.build_cell('outlet_channel_c', 'outlet_channel_u', self._outlet_channel_material, ['outlet_channel_s'], outside_surfaces=['pebble_shoot_s', 'conus_s'])
        self._reactor_dict['outlet_channel']['universes'] = self.build_universe('outlet_channel_u', ['outlet_channel_s'], outside_surfaces=['pebble_shoot_s', 'conus_s'])

    def build_pebble_shoot(self):
        surf = self.build_cylinder_surface('pebble_shoot_s', 'cylz', self.pebble_shoot_radius , lower_height=self.pebble_shoot_lower_height, upper_height=self.pebble_shoot_upper_height)
        self._reactor_dict['pebble_shoot'] = {'surface': surf}
        #self._reactor_dict['pebble_shoot']['cells'] = self.build_filled_cell('pebble_shoot_c', 'pebble_shoot_u', 'pebble_bed', ['pebble_shoot_s'])
        self._reactor_dict['pebble_shoot']['cells'] = self.build_cell('pebble_shoot_c', 'pebble_shoot_u', self._pebble_shoot_material, ['pebble_shoot_s'])
        self._reactor_dict['pebble_shoot']['universes'] = self.build_universe('pebble_shoot_u', ['pebble_shoot_s'])

    def build_bottom_reflector(self):
        pebble_shoot_surface = '' if self.simple_core else 'pebble_shoot_s'
        surf = self.build_cylinder_surface('bottom_reflector_s', 'cylz', self.block_inner_radius, lower_height=self.bottom_reflector_lower_height, upper_height=self.bottom_reflector_upper_height)
        self._reactor_dict['bottom_reflector'] = {'surface': surf}
        self._reactor_dict['bottom_reflector']['cells'] = self.build_cell('bottom_reflector_c', 'bottom_reflector_u', self._block_material, ['bottom_reflector_s'], outside_surfaces=[pebble_shoot_surface])
        self._reactor_dict['bottom_reflector']['universes'] = self.build_universe('bottom_reflector_u', ['bottom_reflector_s'], outside_surfaces=[pebble_shoot_surface])
        
    def build_pebble_bed(self):
        surf  = 'surf inf_surf inf\n'
        surf += f'pbed pebble_bed helium_u "{self.pebble_bed_name}" pow\n' 
        surf += self.build_cylinder_surface('pebbles_s', 'cylz', self.block_inner_radius, lower_height=self.pebble_bed_lower_height, upper_height=self.pebble_bed_upper_height)
        self._reactor_dict['pebble_bed'] = {'surface': surf}
        self._reactor_dict['pebble_bed']['cells'] = 'cell c_he helium_u helium  -inf_surf\n'
        self._reactor_dict['pebble_bed']['cells'] += self.build_filled_cell('pebbles_c', 'pebbles_u', 'pebble_bed', ['pebbles_s'])
        self._reactor_dict['pebble_bed']['universes'] = self.build_universe('pebbles_u', ['pebbles_s'])
        
    def build_pebble(self):
        surf = f'surf pebble_inner sph 0. 0. 0. {self.pebble_inner_radius}\n'
        surf += f'surf pebble_outer sph 0. 0. 0. {self.pebble_outer_radius}\n'
        self._reactor_dict['pebble'] = {'surface': surf}
        
    def build_outside(self):
        self._reactor_dict['outside'] = {'surface': self.build_cylinder_surface('outside_s', 'cylz', self.block_outer_radius, self.bottom_reflector_lower_height, self.model_upper_height)}
        self._reactor_dict['outside']['universe'] = 'cell out        0 outside            outside_s'
        
    def build_cavity(self):
        self._reactor_dict['cavity'] = {'surface':self.build_cylinder_surface('cavity_s', 'cylz', self.block_inner_radius, self.cavity_lower_height, self.cavity_upper_height)} 
        self._reactor_dict['cavity']['cells'] = self.build_cell('cavity_c', 'cavity_u', self._cavity_material, ['cavity_s'])
        self._reactor_dict['cavity']['universes'] = self.build_universe('cavity_u', ['cavity_s'])
        
    def build_top_reflector(self):
        self._reactor_dict['top_reflector'] = {'surface':self.build_cylinder_surface('top_reflector_s', 'cylz', self.block_inner_radius, self.top_reflector_lower_height, self.top_reflector_upper_height)} 
        self._reactor_dict['top_reflector']['cells'] = self.build_cell('top_reflector_c', 'top_reflector_u', self._block_material, ['top_reflector_s'])
        self._reactor_dict['top_reflector']['universes'] = self.build_universe('top_reflector_u', ['top_reflector_s'])
            
    def build_block_surface(sefl, id_, ir_, or_, ang1, ang2, x_offset=0.0, y_offset=0.0):
        return f'surf block_{id_}_s  pad {x_offset} {y_offset} {ir_} {or_} {ang1} {ang2}\n'
        
    def build_dimple_surfaces(self, id_, dr_, ang, num_dimples, x_offset=0.0, y_offset=0.0):
        # 7.0 is the dimple off set
        base_height = self.dimple_axial_offset + self.pebble_bed_lower_height + self.dimple_radius if id_ % 2 == 0 else self.pebble_bed_lower_height + self.dimple_radius * 4
        u, v = self.convert_theta_to_uv(math.radians(ang+100))
        dimple = f'surf block_{id_}_plane plane {u} {v}\n'
        dimple_surfaces = []
        for num in range(num_dimples):
            z_offset=base_height + num * dr_ * 4
            dimple += self.build_cylinder_surface(f'block_{id_}_d{num}_s', 'cylv', dr_, x_offset=x_offset, y_offset=y_offset, z_offset=z_offset, u=u, v=v, w=0.0)
            dimple_surfaces.append(f'block_{id_}_d{num}_s')
        return dimple_surfaces, dimple
        
    def build_rod_surfaces(self, id_, r2c, or_, ang, rod_type, lh, uh):
        u, v = self.convert_theta_to_uv(math.radians(ang+100), r=r2c)    
        return f'block_{id_}_{rod_type}_s', self.build_cylinder_surface(f'block_{id_}_{rod_type}_s', 'cylz', or_, x_offset=u, y_offset=v,  lower_height=lh, upper_height=uh)
        
    def build_block_cell(self, id_, surfaces_to_skip=[], cells_to_skip=[]):
        surfaces_to_skip_str = ' '.join(surf for surf in surfaces_to_skip)
        cells_to_skip_str = '#' + ' #'.join(surf for surf in cells_to_skip) if len(cells_to_skip)>0 else ''
    
        return f'cell block_{id_}_c block_{id_}_u {self._block_material} -block_{id_}_s {surfaces_to_skip_str} {cells_to_skip_str}'
    
    def build_dimple_cells(self, block_id, num):
        cell = ''
        dimple_cells = []
        for num in range(num):
            cell += f'cell block_{block_id}_d{num}_c pebbles_u fill pebble_bed -block_{block_id}_d{num}_s -outer_dimple inner_dimple block_{block_id}_plane\n'   
            dimple_cells.append(f'block_{block_id}_d{num}_c')
        return dimple_cells, cell
    
    def build_rod_cells(self, block_id, rod_type, material, surfaces_to_skip=[], cells_to_skip=[]):
        surfaces_to_skip_str = ' '.join(surf for surf in surfaces_to_skip)
        cells_to_skip_str = '' if cells_to_skip == [] else '#' + ' #'.join(surf for surf in cells_to_skip)
        cell_str = f'cell block_{block_id}_{rod_type}_c block_{block_id}_{rod_type}_u {material} -block_{block_id}_{rod_type}_s {surfaces_to_skip_str}  {cells_to_skip_str}'
        cell = [f'block_{block_id}_{rod_type}_c']
        return cell, cell_str
        
    def build_block_universe(self, id_, surfaces_to_skip=[], cells_to_skip=[]):
        surfaces_to_skip_str = ' '.join(surf for surf in surfaces_to_skip)
        cells_to_skip_str = '#' + ' #'.join(surf for surf in cells_to_skip) if len(cells_to_skip)>0 else ''
        return f'cell block_{id_}_u 0 fill block_{id_}_u -block_{id_}_s {surfaces_to_skip_str} {cells_to_skip_str}'
    
    def build_dimple_universes(self, block_id, num):
        cell = ''
        for num in range(num):
            cell += f'cell block_{block_id}_d{num}_u 0 fill pebbles_u -block_{block_id}_d{num}_s -outer_dimple inner_dimple block_{block_id}_plane\n'   
        return cell
    
    def build_rod_universe(self, block_id, rod_type, surfaces_to_skip=[], cells_to_skip=[]):
        surfaces_to_skip_str = ' '.join(surf for surf in surfaces_to_skip)
        cells_to_skip_str = '' if cells_to_skip == [] else '#' + ' #'.join(surf for surf in cells_to_skip)
        cell = f'cell block_{block_id}_{rod_type}_u 0 fill block_{block_id}_{rod_type}_u -block_{block_id}_{rod_type}_s {surfaces_to_skip_str}  {cells_to_skip_str}'
        return cell
    
    def write_pbr_core(self):
        core_input = os.path.join(self.output_dir,self.core_file_name)

        f = open(core_input, 'w')
        for block_id, block in self._block_dict.items():
            for print_type, region in block.items():
                f.write(f'\n\n%%%%%%%%%%%%%%%%%%%%% Block {block_id} {print_type} %%%%%%%%%%%%%%%%%%%%%\n\n')
                for region_name, region_print in region.items():
                    f.write(f'\n\n%%%%%%%%%%%%%%%%%%%%% Block {block_id} {print_type} {region_name} %%%%%%%%%%%%%%%%%%%%%\n\n')
                    f.write(region_print)

        for region_name, region in self._reactor_dict.items():
            for print_type, region in region.items():
                f.write(f'\n\n%%%%%%%%%%%%%%%%%%%%% {region_name} {print_type} %%%%%%%%%%%%%%%%%%%%%\n\n')
                f.write(region)