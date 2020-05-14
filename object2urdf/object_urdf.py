import pybullet as p
import os
import copy

import xml.etree.ElementTree as ET



class ObjectUrdfBuilder:
    def __init__(self, object_folder="", log_file ="vhacd_log.txt", urdf_prototype='_prototype.urdf'):
        self.object_folder = os.path.abspath(object_folder)
        self.log_file = os.path.abspath(log_file)
        self.suffix = "vhacd"

        self.urdf_base = self._read_xml(os.path.join(object_folder,urdf_prototype))
        p.connect(p.DIRECT)


    # Recursively get all files with a specific extension, excluding a certain suffix
    def get_files_recursively(self,start_directory, filter_extension=None, exclude_suffix=None):
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


    # Replace an attribute in a feild of a URDF
    def replace_urdf_attribute(self, urdf, feild, attribute, value):
        urdf.find(feild).attrib[attribute] = value
        return urdf
        

    # Make an updated copy of the URDF for the current object
    def update_urdf(self, object_file, object_name, collision_file=None, override=None):
        # If no separate collision geometry is provided, use the object file
        if collision_file is None:
            collision_file = object_file

        # Update the filenames and object name
        new_urdf = copy.deepcopy(self.urdf_base)
        self.replace_urdf_attribute(new_urdf,'.//visual/geometry/mesh', 'filename', object_file)
        self.replace_urdf_attribute(new_urdf,'.//collision/geometry/mesh', 'filename', collision_file)
        self.replace_urdf_attribute(new_urdf,'.//link', 'name', object_name)
        new_urdf.attrib['name']= object_name

        # Update the inertias
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
    def build_urdf(self, filename, output_folder=None, force_overwrite=False, decompose_concave=False, force_decompose=False, **kwargs):

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

        _, file_extension = os.path.splitext(filename)

        # If an override file exists, include its data in the URDF
        override_file = filename.replace(file_extension,'.ovr')
        if os.path.exists(override_file):
            overrides = self._read_xml(override_file)
        else:
            overrides = None

        # If the user wants to run convex decomposition on concave objects, do it.
        if decompose_concave and file_extension=='.obj':
            outfile=filename.replace(file_extension,'_'+self.suffix+file_extension)
            collision_file = rel.replace(file_extension,'_'+self.suffix+file_extension)

            # Only run a decomposition if one does not exist, or if the user forces an overwrite
            if not os.path.exists(outfile) or force_decompose:
                p.vhacd(filename, outfile, self.log_file, **kwargs)

            urdf_out = self.update_urdf(rel, name, collision_file=collision_file, override=overrides)
        else:
            urdf_out = self.update_urdf(rel, name, override=overrides)
        
        self.save_urdf(urdf_out, name+'.urdf', force_overwrite)


    # Build the URDFs for all objects in your library.
    def build_library(self, **kwargs):
        # Get all OBJ files
        obj_files  = self.get_files_recursively(self.object_folder, filter_extension='.obj', exclude_suffix=self.suffix)
        stl_files  = self.get_files_recursively(self.object_folder, filter_extension='.stl', exclude_suffix=self.suffix)       

        obj_folders=[]
        for root, _, full_file in obj_files:
            obj_folders.append(root)
            self.build_urdf(full_file,**kwargs)
        
        for root, _, full_file in stl_files:
            if root not in obj_folders:
                self.build_urdf(full_file,**kwargs)