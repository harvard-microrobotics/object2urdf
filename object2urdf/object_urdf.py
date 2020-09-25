import pybullet as p
from scipy.spatial.transform import Rotation
import numpy as np
import os
import copy
import trimesh

import xml.etree.ElementTree as ET



class ObjectUrdfBuilder:
    def __init__(self, object_folder="", log_file ="vhacd_log.txt", urdf_prototype='_prototype.urdf'):
        self.object_folder = os.path.abspath(object_folder)
        self.log_file = os.path.abspath(log_file)
        self.suffix = "vhacd"

        self.urdf_base = self._read_xml(os.path.join(object_folder,urdf_prototype))


    # Recursively get all files with a specific extension, excluding a certain suffix
    def _get_files_recursively(self,start_directory, filter_extension=None, exclude_suffix=None):
        for root, dirs, files in os.walk(start_directory):
            for file in files:
                if filter_extension is None or file.lower().endswith(filter_extension):
                    if isinstance(exclude_suffix, str):
                        if not file.lower().endswith(exclude_suffix+filter_extension):
                            yield (root, file, os.path.abspath(os.path.join(root, file)))


    # Read and parse a URDF from a file
    def _read_xml(self, filename):
        root = ET.parse(filename).getroot()
        return root


    # Convert a list to a space-separated string
    def _list2str(self, in_list):
        out= ""
        for el in in_list:
            out += str(el)+" "
        return out[:-1]


    # Convert a space-separated string to a list
    def _str2list(self, in_str):
        out = in_str.split(' ')
        out = [float(el) for el in out]
        return out


    # Find the center of mass of the object
    def get_center_of_mass(self, filename):
        mesh = trimesh.load(filename)
        return mesh.center_mass

    # Find the center of mass of the object
    def save_to_obj(self, filename):
        name, ext = os.path.splitext(filename)
        obj_filename = name + '.obj'
        mesh = trimesh.load(filename)
        mesh.export(obj_filename)
        return obj_filename


    # Replace an attribute in a feild of a URDF
    def replace_urdf_attribute(self, urdf, feild, attribute, value):
        urdf = self.replace_urdf_attributes(urdf, feild, {attribute: value})
        return urdf


    # Replace several attributes in a feild of a URDF
    def replace_urdf_attributes(self, urdf, feild, attribute_dict, sub_feild=None):

        if sub_feild is None:
            sub_feild = []

        field_obj = urdf.find(feild)

        if field_obj is not None:
            if len(sub_feild) > 0:
                for child in reversed(sub_feild):
                    field_obj = ET.SubElement(field_obj,child)
            field_obj.attrib.update(attribute_dict)
            #field_obj.attrib = attribute_dict
        else:
            feilds = feild.split("/")
            new_feild="/".join(feilds[0:-1])
            sub_feild.append(feilds[-1])
            self.replace_urdf_attributes(urdf, new_feild, attribute_dict,sub_feild)
        

    # Make an updated copy of the URDF for the current object
    def update_urdf(self, object_file, object_name, collision_file=None, override=None, mass_center=None):
        # If no separate collision geometry is provided, use the object file
        if collision_file is None:
            collision_file = object_file

        # Update the filenames and object name
        new_urdf = copy.deepcopy(self.urdf_base)
        self.replace_urdf_attribute(new_urdf,'.//visual/geometry/mesh', 'filename', object_file)
        self.replace_urdf_attribute(new_urdf,'.//collision/geometry/mesh', 'filename', collision_file)
        new_urdf.attrib['name']= object_name

        # Update the overrides
        if override is not None:
            for orverride_el in override:
                # Update attributes
                out_el_all=new_urdf.findall('.//'+orverride_el.tag)

                for out_el in out_el_all:

                    for key in orverride_el.attrib:
                        out_el.set(key, orverride_el.attrib[key])

                    # Remove fields that will be overwritten
                    for child in orverride_el:
                        el=out_el.find(child.tag)
                        if el is not None:
                            out_el.remove(el)
                    # Add updated feilds
                    out_el.extend(orverride_el)

        # Output the center of mass if provided
        if mass_center is not None:
            # Check if there's a geometry offset
            offset_ob = new_urdf.find('.//collision/origin')
            if offset_ob is not None:
                offset_str = offset_ob.attrib.get('xyz', '0 0 0')
                rot_str = offset_ob.attrib.get('rpy', '0 0 0')
                offset = self._str2list(offset_str)
                rpy = self._str2list(rot_str)
            else:
                offset = [0, 0, 0]
                rpy = [0, 0, 0]


            # Check if there's a scale factor and apply it
            scale_ob = new_urdf.find('.//collision/geometry/mesh')
            if scale_ob is not None:
                scale_str = scale_ob.attrib.get('scale', '1 1 1')
                scale = self._str2list(scale_str)
            else:
                scale = [1, 1, 1]


            for idx,axis in enumerate(mass_center):
                mass_center[idx] = -mass_center[idx]*scale[idx] + offset[idx]

            rot = Rotation.from_euler('xyz',rpy)
            rot_matrix = rot.as_matrix()
            mass_center = np.matmul(rot_matrix, np.vstack(np.asarray(mass_center))).squeeze()


            self.replace_urdf_attributes(new_urdf,
                    './/visual/origin',
                    {'xyz': self._list2str(mass_center), 'rpy': self._list2str(rpy)})
            self.replace_urdf_attributes(new_urdf,
                    './/collision/origin',
                    {'xyz': self._list2str(mass_center), 'rpy': self._list2str(rpy)})



        return new_urdf


    # Save a URDF to a file
    def save_urdf(self, new_urdf, filename, overwrite=False):
        out_file = os.path.join(self.object_folder, filename)

        # Do not overwrite the file unless the option is True
        if os.path.exists(out_file) and not overwrite:
            return 

        # Save the file
        mydata = ET.tostring(new_urdf)
        with open(out_file, "wb") as f:
            f.write(mydata)


    # Build a URDF from an object file
    def build_urdf(self, filename, output_folder=None,
                   force_overwrite=False, decompose_concave=False, force_decompose=False, 
                   calculate_mass_center = True, **kwargs):

        # If no output folder is specified, use the base object folder
        if output_folder is None:
            output_folder = self.object_folder

        # Generate a relative path from the output folder to the geometry files
        common = os.path.commonprefix([output_folder,filename])
        rel = os.path.join(filename.replace(common,''))
        if rel[0]==os.path.sep:
            rel = rel[1:] 
        name= rel.split(os.path.sep)[0]
        rel = rel.replace(os.path.sep,'/')

        file_name_raw, file_extension = os.path.splitext(filename)

        # If an override file exists, include its data in the URDF
        override_file = filename.replace(file_extension,'.ovr')
        if os.path.exists(override_file):
            overrides = self._read_xml(override_file)
        else:
            overrides = None


        # Calculate the center of mass
        if calculate_mass_center:
            mass_center = self.get_center_of_mass(filename)

        else:
            mass_center = None


        # If the user wants to run convex decomposition on concave objects, do it.
        if decompose_concave:
            if file_extension == '.stl':
                obj_filename = self.save_to_obj(filename)
                visual_file = rel.replace(file_extension,'.obj')
            elif file_extension == '.obj':
                obj_filename = filename
                visual_file  = rel
            else:
                raise ValueError("Your filetype needs to be an STL or OBJ to perform concave decomposition")


            outfile=obj_filename.replace('.obj','_'+self.suffix+'.obj')
            collision_file = visual_file.replace('.obj','_'+self.suffix+'.obj')

            # Only run a decomposition if one does not exist, or if the user forces an overwrite
            if not os.path.exists(outfile) or force_decompose:
                p.vhacd(obj_filename, outfile, self.log_file, **kwargs)

            urdf_out = self.update_urdf(visual_file, name, collision_file=collision_file, override=overrides, mass_center=mass_center)
        else:
            urdf_out = self.update_urdf(rel, name, override=overrides, mass_center=mass_center)
        
        self.save_urdf(urdf_out, name+'.urdf', force_overwrite)


    # Build the URDFs for all objects in your library.
    def build_library(self, **kwargs):
        print("\nFOLDER: %s"%(self.object_folder))

        # Get all OBJ files
        obj_files  = self._get_files_recursively(self.object_folder, filter_extension='.obj', exclude_suffix=self.suffix)
        stl_files  = self._get_files_recursively(self.object_folder, filter_extension='.stl', exclude_suffix=self.suffix)       

        obj_folders=[]
        for root, _, full_file in obj_files:
            obj_folders.append(root)
            self.build_urdf(full_file,**kwargs)

            common = os.path.commonprefix([self.object_folder,full_file])
            rel = os.path.join(full_file.replace(common,''))
            print('\tBuilding: %s'%(rel) )
        
        for root, _, full_file in stl_files:
            if root not in obj_folders:
                self.build_urdf(full_file,**kwargs)
                
                common = os.path.commonprefix([self.object_folder,full_file])
                rel = os.path.join(full_file.replace(common,''))
                print('Building: %s'%(rel) )