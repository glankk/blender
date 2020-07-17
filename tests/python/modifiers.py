# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

import math
import os
import sys
from random import shuffle, seed

import bpy

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from modules.mesh_test import ModifierTest, ModifierSpec

seed(0)


def get_generate_modifiers_list(test_object_name, randomize=False):
    """
    Construct a list of 'Generate' modifiers with default parameters.
    :param test_object_name: str - name of test object. Some modifiers like boolean need an extra parameter beside
                                    the default one. E.g. boolean needs object, mask needs vertex group etc...
                                    The extra parameter name will be <test_object_name>_<modifier_type>
    :param randomize: bool - if True shuffle the list of modifiers.
    :return: list of 'Generate' modifiers with default parameters.
    """

    boolean_test_object = bpy.data.objects[test_object_name + "_boolean"]

    generate_modifiers = [
        ModifierSpec('array', 'ARRAY', {}),
        ModifierSpec('bevel', 'BEVEL', {'width': 0.1}),
        ModifierSpec('boolean', 'BOOLEAN', {'object': boolean_test_object}),
        ModifierSpec('build', 'BUILD', {'frame_start': 0, 'frame_duration': 1}),
        ModifierSpec('decimate', 'DECIMATE', {}),
        ModifierSpec('edge split', 'EDGE_SPLIT', {}),

        # mask can effectively delete the mesh since the vertex group need to be updated after each
        # applied modifier. Needs to be tested separately.
        # ModifierSpec('mask', 'MASK', {'vertex_group': mask_vertex_group}, False),

        ModifierSpec('mirror', 'MIRROR', {}),
        ModifierSpec('multires', 'MULTIRES', {}),

        # remesh can also generate an empty mesh. Skip.
        # ModifierSpec('remesh', 'REMESH', {}),

        # ModifierSpec('screw', 'SCREW', {}), # screw can make the test very slow. Skipping for now.
        # ModifierSpec('skin', 'SKIN', {}), # skin is not reproducible .


        ModifierSpec('solidify', 'SOLIDIFY', {}),
        ModifierSpec('subsurf', 'SUBSURF', {}),
        ModifierSpec('triangulate', 'TRIANGULATE', {}),
        ModifierSpec('wireframe', 'WIREFRAME', {})

    ]

    if randomize:
        shuffle(generate_modifiers)

    return generate_modifiers


def main():
    mask_first_list = get_generate_modifiers_list("testCubeMaskFirst", randomize=True)
    mask_vertex_group = "testCubeMaskFirst" + "_mask"
    mask_first_list.insert(0, ModifierSpec('mask', 'MASK', {'vertex_group': mask_vertex_group}))

    tests = [
        ###############################
        # List of 'Generate' modifiers on a cube
        ###############################
        # 0
        # ["testCube", "expectedCube", get_generate_modifiers_list("testCube")],
        ["CubeRandom", "testCubeRandom", "expectedCubeRandom",
         get_generate_modifiers_list("testCubeRandom", randomize=True)],
        ["CubeMaskFirst", "testCubeMaskFirst", "expectedCubeMaskFirst", mask_first_list],

        ["CollapseDecimate", "testCollapseDecimate", "expectedCollapseDecimate",
         [ModifierSpec("subdivision", 'SUBSURF', {"levels": 2}),
          ModifierSpec('decimate', 'DECIMATE',
                       {'decimate_type': 'COLLAPSE', 'ratio': 0.25, 'use_collapse_triangulate': True})]],
        ["PlanarDecimate", "testPlanarDecimate", "expectedPlanarDecimate",
         [ModifierSpec("subdivision", 'SUBSURF', {"levels": 2}),
          ModifierSpec('decimate', 'DECIMATE', {'decimate_type': 'DISSOLVE', 'angle_limit': math.radians(30)})]],
        ["UnsubdivideDecimate", "testUnsubdivideDecimate", "expectedUnsubdivideDecimate",
         [ModifierSpec("subdivision", 'SUBSURF', {"levels": 2}),
          ModifierSpec('decimate', 'DECIMATE', {'decimate_type': 'UNSUBDIV', 'iterations': 2})]],

        # 5
        ["RadialBisectMirror", "testRadialBisectMirror", "expectedRadialBisectMirror",
         [ModifierSpec('mirror1', 'MIRROR', {'use_bisect_axis': (True, False, False)}),
          ModifierSpec('mirror2', 'MIRROR', {'use_bisect_axis': (True, False, False),
                                             'mirror_object': bpy.data.objects["testRadialBisectMirrorHelper"]}),
          ModifierSpec('mirror3', 'MIRROR', {'use_axis': (False, True, False), 'use_bisect_axis': (False, True, False),
                                             'use_bisect_flip_axis': (False, True, False),
                                             'mirror_object': bpy.data.objects["testRadialBisectMirrorHelper"]})]],
        ["T58411Mirror", "regressT58411Mirror", "expectedT58411Mirror",
         [ModifierSpec('mirror', 'MIRROR', {}),
          ModifierSpec('bevel', 'BEVEL', {'segments': 2, 'limit_method': 'WEIGHT'}),
          ModifierSpec('subd', 'SUBSURF', {'levels': 1})]],

        ["BasicScrew", "testBasicScrew", "expectedBasicScrew",
         [ModifierSpec('mirror', 'MIRROR', {'mirror_object': bpy.data.objects["testBasicScrewHelper"]}),
          ModifierSpec("screw", 'SCREW', {'angle': math.radians(400), 'steps': 20, 'iterations': 2, 'screw_offset': 2,
                                          'use_normal_calculate': True})]],
        ["ObjectScrew", "testObjectScrew", "expectedObjectScrew",
         [ModifierSpec('mirror', 'MIRROR', {'mirror_object': bpy.data.objects["testObjectScrewHelper2"]}),
          ModifierSpec("screw", 'SCREW',
                       {"angle": math.radians(600), 'steps': 32, 'iterations': 1, 'use_object_screw_offset': True,
                        'use_normal_calculate': True, 'object': bpy.data.objects["testObjectScrewHelper1"]})]],

        # 9
        ["MergedScrewWeld", "testMergedScrewWeld", "expectedMergedScrewWeld",
         [ModifierSpec("screw", 'SCREW', {'angle': math.radians(360), 'steps': 12, 'iterations': 1, 'screw_offset': 1,
                                          'use_normal_calculate': True, 'use_merge_vertices': True}),
          ModifierSpec("weld", 'WELD', {"merge_threshold": 0.001})]],
        ["T72380Weld", "regressT72380Weld", "expectedT72380Weld",
         [ModifierSpec('vedit', 'VERTEX_WEIGHT_EDIT',
                       {'vertex_group': 'Group', 'use_remove': True, 'remove_threshold': 1}),
          ModifierSpec("weld", 'WELD', {"merge_threshold": 0.2, "vertex_group": "Group"})]],
        ["T72792Weld", "regressT72792Weld", "expectedT72792Weld",
         [ModifierSpec('array', 'ARRAY', {'fit_type': 'FIXED_COUNT', 'count': 2}),
          ModifierSpec("weld", 'WELD', {"merge_threshold": 0.1, "vertex_group": "Group"})]],

        ############################################
        # One 'Generate' modifier on primitive meshes
        #############################################
        # 12
        ["CubeArray", "testCubeArray", "expectedCubeArray",
         [ModifierSpec('array', 'ARRAY', {})]],
        ["CapArray", "testCapArray", "expectedCapArray",
         [ModifierSpec('array', 'ARRAY',
                       {'fit_type': 'FIT_LENGTH', 'fit_length': 2.0, 'start_cap': bpy.data.objects["testCapStart"],
                        'end_cap': bpy.data.objects["testCapEnd"]})]],
        ["CurveArray", "testCurveArray", "expectedCurveArray",
         [ModifierSpec('array', 'ARRAY', {'fit_type': 'FIT_CURVE', 'curve': bpy.data.objects["testCurveArrayHelper"],
                                          'use_relative_offset': False, 'use_constant_offset': True,
                                          'constant_offset_displace': (0.5, 0, 0)})]],
        ["RadialArray", "testRadialArray", "expectedRadialArray",
         [ModifierSpec('array', 'ARRAY', {'fit_type': 'FIXED_COUNT', 'count': 3, 'use_merge_vertices': True,
                                          'use_merge_vertices_cap': True, 'use_relative_offset': False,
                                          'use_object_offset': True,
                                          'offset_object': bpy.data.objects["testRadialArrayHelper"]})]],

        ["CylinderBuild", "testCylinderBuild", "expectedCylinderBuild",
         [ModifierSpec('build', 'BUILD', {'frame_start': 0, 'frame_duration': 1})]],

        # 17
        ["ConeDecimate", "testConeDecimate", "expectedConeDecimate",
         [ModifierSpec('decimate', 'DECIMATE', {'ratio': 0.5})]],
        ["CubeEdgeSplit", "testCubeEdgeSplit", "expectedCubeEdgeSplit",
         [ModifierSpec('edge split', 'EDGE_SPLIT', {})]],

        ["SphereMirror", "testSphereMirror", "expectedSphereMirror",
         [ModifierSpec('mirror', 'MIRROR', {})]],
        ["LocalMirror", "testLocalMirror", "expectedLocalMirror",
         [ModifierSpec('mirror', 'MIRROR', {'use_clip': True})]],
        ["ObjectOffsetMirror", "testObjectOffsetMirror", "expectedObjectOffsetMirror",
         [ModifierSpec('mirror', 'MIRROR', {'mirror_object': bpy.data.objects["testObjectOffsetMirrorHelper"]})]],

        ["CylinderMask", "testCylinderMask", "expectedCylinderMask",
         [ModifierSpec('mask', 'MASK', {'vertex_group': "mask_vertex_group"})]],
        ["ConeMultiRes", "testConeMultiRes", "expectedConeMultiRes",
         [ModifierSpec('multires', 'MULTIRES', {})]],

        # 24
        ["CubeScrew", "testCubeScrew", "expectedCubeScrew",
         [ModifierSpec('screw', 'SCREW', {})]],

        ["CubeSolidify", "testCubeSolidify", "expectedCubeSolidify",
         [ModifierSpec('solidify', 'SOLIDIFY', {})]],
        ["ComplexSolidify", "testComplexSolidify", "expectedComplexSolidify",
         [ModifierSpec('solidify', 'SOLIDIFY', {'solidify_mode': 'NON_MANIFOLD', 'thickness': 0.05, 'offset': 0,
                                                'nonmanifold_thickness_mode': 'CONSTRAINTS'})]],
        ["T63063Solidify", "regressT63063Solidify", "expectedT63063Solidify",
         [ModifierSpec('solid', 'SOLIDIFY', {'thickness': 0.1, 'offset': 0.7})]],
        ["T61979Solidify", "regressT61979Solidify", "expectedT61979Solidify",
         [ModifierSpec('solid', 'SOLIDIFY',
                       {'thickness': -0.25, 'use_even_offset': True, 'use_quality_normals': True})]],

        ["MonkeySubsurf", "testMonkeySubsurf", "expectedMonkeySubsurf",
         [ModifierSpec('subsurf', 'SUBSURF', {})]],
        ["CatmullClarkSubdivisionSurface", "testCatmullClarkSubdivisionSurface",
         "expectedCatmullClarkSubdivisionSurface",
         [ModifierSpec("subdivision", 'SUBSURF', {"levels": 2})]],
        ["SimpleSubdivisionSurface", "testSimpleSubdivisionSurface", "expectedSimpleSubdivisionSurface",
         [ModifierSpec("subdivision", 'SUBSURF', {"levels": 2, 'subdivision_type': 'SIMPLE'})]],
        ["Crease2dSubdivisionSurface", "testCrease2dSubdivisionSurface", "expectedCrease2dSubdivisionSurface",
         [ModifierSpec("subdivision", 'SUBSURF', {"levels": 2})]],
        ["Crease3dSubdivisionSurface", "testCrease3dSubdivisionSurface", "expectedCrease3dSubdivisionSurface",
         [ModifierSpec("subdivision", 'SUBSURF', {"levels": 2})]],

        # 34
        ["SphereTriangulate", "testSphereTriangulate", "expectedSphereTriangulate",
         [ModifierSpec('triangulate', 'TRIANGULATE', {})]],
        ["MonkeyWireframe", "testMonkeyWireframe", "expectedMonkeyWireframe",
         [ModifierSpec('wireframe', 'WIREFRAME', {})]],

        # Duplicate the object, test object and expected object have same world coordinates.
        ["Skin", "testObjPlaneSkin", "expObjPlaneSkin",
         [ModifierSpec('skin', 'SKIN', {})]],

        ["MergedWeld", "testMergedWeld", "expectedMergedWeld",
         [ModifierSpec("weld", 'WELD', {"merge_threshold": 0.021})]],
        ["MergedAllWeld", "testMergedAllWeld", "expectedMergedAllWeld",
         [ModifierSpec("weld", 'WELD', {"merge_threshold": 1.1})]],
        ["MergedNoneWeld", "testMergedNoneWeld", "expectedMergedNoneWeld",
         [ModifierSpec("weld", 'WELD', {"merge_threshold": 0.019})]],

        #############################################
        # One 'Deform' modifier on primitive meshes
        #############################################
        # 39
        ["MonkeyArmature", "testMonkeyArmature", "expectedMonkeyArmature",
         [ModifierSpec('armature', 'ARMATURE',
                       {'object': bpy.data.objects['testArmature'], 'use_vertex_groups': True})]],
        ["TorusCast", "testTorusCast", "expectedTorusCast",
         [ModifierSpec('cast', 'CAST', {'factor': 2.64})]],
        ["CubeCurve", "testCubeCurve", "expectedCubeCurve",
         [ModifierSpec('curve', 'CURVE', {'object': bpy.data.objects['testBezierCurve']})]],
        ["MonkeyDisplace", "testMonkeyDisplace", "expectedMonkeyDisplace",
         [ModifierSpec('displace', "DISPLACE", {})]],

        # Hook modifier requires moving the hook object to get a mesh change
        # so can't test it with the current framework
        # ["MonkeyHook", "testMonkeyHook", "expectedMonkeyHook",
        #  [ModifierSpec('hook', 'HOOK', {'object': bpy.data.objects["EmptyHook"], 'vertex_group': "HookVertexGroup"})]],

        # 43
        # ModifierSpec('laplacian_deform', 'LAPLACIANDEFORM', {}) Laplacian requires a more complex mesh
        ["CubeLattice", "testCubeLattice", "expectedCubeLattice",
         [ModifierSpec('lattice', 'LATTICE', {'object': bpy.data.objects["testLattice"]})]],

        ["PlaneShrinkWrap", "testPlaneShrinkWrap", "expectedPlaneShrinkWrap",
         [ModifierSpec('shrinkwrap', 'SHRINKWRAP', {'target': bpy.data.objects["testCubeWrap"], 'offset': 0.5})]],

        ["CylinderSimpleDeform", "testCylinderSimpleDeform", "expectedCylinderSimpleDeform",
         [ModifierSpec('simple_deform', 'SIMPLE_DEFORM', {'angle': math.radians(180), 'deform_axis': 'Z'})]],

        ["PlaneSmooth", "testPlaneSmooth", "expectedPlaneSmooth",
         [ModifierSpec('smooth', 'SMOOTH', {'iterations': 11})]],

        # Smooth corrective requires a complex mesh.

        ["BalloonLaplacianSmooth", "testBalloonLaplacianSmooth", "expectedBalloonLaplacianSmooth",
         [ModifierSpec('laplaciansmooth', 'LAPLACIANSMOOTH', {'lambda_factor': 12, 'lambda_border': 12})]],

        ["WavePlane", "testObjPlaneWave", "expObjPlaneWave",
         [ModifierSpec('wave', 'WAVE', {})]],

        #### CURVES ####
        # Caution: Make sure test object has no modifier in "added" state, the test may fail.
        ["BezCurveArray", "testObjBezierCurveArray", "expObjBezierCurveArray",
         [ModifierSpec('array', 'ARRAY', {})]],

        ["CurveBevel", "testObjBezierCurveBevel", "expObjBezierCurveBevel",
         [ModifierSpec('bevel', 'BEVEL', {})]],

        ["CurveBuild", "testObjBezierCurveBuild", "expObjBezierCurveBuild",
         [ModifierSpec('build', 'BUILD', {'frame_start': 0, 'frame_duration': 1})]],

        ["CurveDecimate", "testObjBezierCurveDecimate", "expObjBezierCurveDecimate",
         [ModifierSpec('decimate', 'DECIMATE', {'ratio':0.5})]],

        ["CurveEdgeSplit", "testObjBezierCurveEdgeSplit", "expObjBezierCurveEdgeSplit",
         [ModifierSpec('edgeSplit', 'EDGE_SPLIT', {})]],

        ["CurveMirror", "testObjBezierCurveMirror", "expObjBezierCurveMirror",
         [ModifierSpec('mirror', 'MIRROR', {'use_axis': (True, True, False)})]],

        ["CurveScrew", "testObjBezierCurveScrew", "expObjBezierCurveScrew",
         [ModifierSpec('screw', 'SCREW', {})]],

        ["CurveSolidify", "testObjBezierCurveSolidify", "expObjBezierCurveSolidify",
         [ModifierSpec('solidify', 'SOLIDIFY', {'thickness':1})]],

        ["CurveSubSurf", "testObjBezierCurveSubSurf", "expObjBezierCurveSubSurf",
         [ModifierSpec('subSurf', 'SUBSURF', {})]],

        ["CurveTriangulate", "testObjBezierCurveTriangulate", "expObjBezierCurveTriangulate",
         [ModifierSpec('triangulate', 'TRIANGULATE', {})]],

        # Test 60
        ["CurveWeld", "testObjBezierCurveWeld", "expObjBezierCurveWeld",
         [ModifierSpec('weld', 'WELD', {})]],


    ]

    modifiers_test = ModifierTest(tests)

    command = list(sys.argv)
    for i, cmd in enumerate(command):
        if cmd == "--run-all-tests":
            modifiers_test.apply_modifiers = True
            modifiers_test.run_all_tests()
            break
        elif cmd == "--run-test":
            modifiers_test.apply_modifiers = False
            name = str(command[i + 1])
            modifiers_test.run_test(name)
            break


if __name__ == "__main__":
    main()
