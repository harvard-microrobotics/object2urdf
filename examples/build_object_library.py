import os
import sys
from object2urdf import ObjectUrdfBuilder

# Build your library
object_folder = "ycb"
builder = ObjectUrdfBuilder(object_folder)
builder.build_library(force_overwrite=True, decompose_concave=True, force_decompose=False, center = 'top')

object_folder = "fancy_cube"
builder = ObjectUrdfBuilder(object_folder)
builder.build_library(force_overwrite=True, decompose_concave=True, force_decompose=False, center = 'mass')