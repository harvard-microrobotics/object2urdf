# object2urdf
Manage a library of objects for use in pybullet physics

## Installation
### Install the release version
[This package is available on pypi](https://pypi.org/project/object2urdf/), so anyone can install it with pip: `pip install object2urdf`

### Install the most-recent development version
1. Clone the package from the [github repo](https://github.com/cbteeple/object2urdf)
2. Navigate into the main folder
3. `pip install .`


## Usage
### Set up YCB objects
1. Download the **16k laser scan** from the [YCB Benchmarks website](http://ycb-benchmarks.s3-website-us-east-1.amazonaws.com/).
2. Unzip the folder. You'll now be able to find several files, some of which we use
    - Files named **textured** include both object geometry and texture maps.
    - Files named **nontextured** include only object geometry.
3. Notes:
    - All of these object files are in units of meters.

### Set up custom objects
1. Make your object in CAD or a 3D modeling software, and export it as either an **.OBJ** or **.STL** file.
    - **.OBJ** files can be rendered with a texture (using an **.MTL** file) and collisions with convex objects can be handled correctly (this utillity to handles that).
    - **.STL** files can only be rendered without textures, and the collision boundary will only be the convex hull of the object. _(This is due to the limitations of the Bullet physics engine)_
2. Set up your file structure
    - Each object set needs its own directory.
    - Inside your directory for the object set, create a subdirectory for each new object. _The subdirectory name will be used as the object name._
3. Place all of the relevant geometry and texture files into that subdirectory. _Filenames must all match, with correct file extensions_
    - Supported geometry must be either an **.OBJ** or **.STL** file.
    - Textures can be added to **.OBJ** files using an accompanying **.MTL** file. _Linking to this is handled within the **.OBJ** file._
    - **.MTL** files usually refer to an image texture (**jpg** or **png**) that gets mapped onto the object.


### Auto-generate URDFs
1. Set up your file structure per the instructions for custom objects above.
    - Each object set directory must have its own `_prototype.urdf` template file. This is where default units, colors, and masses are adjusted.
    - If objects are buried in sub-subdirectories within each object's directory, this utility will still find them. However, _only one URDF is generated from each object directory._
    - Geometry must be generated from a **.OBJ** or **.STL** file, with **.OBJ** taking priority if multiple are found in the same folder
    - _(optional)_ Add object-specific overrides to a **.OVR** file in the same folder. _Filenames must all match_
        - This can be things like the object's mass, orientations, etc.
        - This file should be an XML similar to the file in the **fancy_cube** >> **holder** example.
2. Use the package to automatically generate URDFs for your object library.
    - Start with the "**build_object_library.py**" example.
    - This example will place all URDFs into their respective object set directories, but you can change the output location by passing the `output_folder` argument to `build_urdf` or `build_library`
    - Due to limitations of Bullet's rigid body collision detection, concave objects must be split into several convex objects using a convex decomposition. You can do this with the `ObjectUrdfBuilder` class by passing `decompose_concave=True` to the `build_urdf` or `build_library` functions. The URDF builder will then generate a decomposed file, place it next to the original object file, and link to it as the collision geometry in the object's URDF.
    - By default, this package uses [trimesh](https://github.com/mikedh/trimesh) to calculate the center of mass of objects from thier geometry. To turn this behavir off and use the URDF or ORV files, pass `calculate_mass_center = False` to the `build_urdf` or `build_library` functions

### Use objects in simulation
Just import the object's URDF:

```python
object_urdf = "fancy_cube/small_holder.urdf"
boxStartPos = [0, 0, 0.5]
boxStartOr = p.getQuaternionFromEuler(np.deg2rad([0, 0, 0]))
boxId = p.loadURDF(object_urdf, boxStartPos, boxStartOr)
```
