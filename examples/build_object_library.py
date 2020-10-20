import os
import sys
from object2urdf import ObjectUrdfBuilder

# Build single URDFs
object_folder = "basketball"

builder = ObjectUrdfBuilder(object_folder, urdf_prototype='_prototype_ball.urdf')
builder.build_urdf(filename="basketball/ball/basketball_corrected.obj", force_overwrite=True, decompose_concave=True, force_decompose=False, center = 'mass')

builder = ObjectUrdfBuilder(object_folder, urdf_prototype='_prototype_hoop.urdf')
builder.build_urdf(filename="basketball/hoop/basketball_net_and_board.obj", force_overwrite=True, decompose_concave=True, force_decompose=False, center = 'bottom')

builder = ObjectUrdfBuilder(object_folder, urdf_prototype='_prototype_hoop.urdf')
builder.build_urdf(filename="basketball/hoop_no_net/basketball_net_and_board.obj", force_overwrite=True, decompose_concave=True, force_decompose=False, center = 'bottom')

builder = ObjectUrdfBuilder(object_folder, urdf_prototype='_prototype_hoop.urdf')
builder.build_urdf(filename="basketball/hoop_no_net_simple/basketball_net_and_board.obj", force_overwrite=True, decompose_concave=True, force_decompose=False, center = 'bottom')

# Build entire libraries of URDFs
object_folder = "ycb"
builder = ObjectUrdfBuilder(object_folder)
builder.build_library(force_overwrite=True, decompose_concave=True, force_decompose=False, center = 'top')

object_folder = "fancy_cube"
builder = ObjectUrdfBuilder(object_folder)
builder.build_library(force_overwrite=True, decompose_concave=True, force_decompose=False, center = 'mass')