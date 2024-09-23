# Copyright 2024 DeepMind Technologies Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Tests for mjSpec bindings."""

import inspect
import textwrap

from absl.testing import absltest
import mujoco
import numpy as np


def get_linenumber():
  cf = inspect.currentframe()
  return cf.f_back.f_lineno


class SpecsTest(absltest.TestCase):

  def test_basic(self):
    # Create a spec.
    spec = mujoco.MjSpec()

    # Check that euler sequence order is set correctly.
    self.assertEqual(spec.eulerseq[0], ord('x'))
    spec.eulerseq = ['z', 'y', 'x']
    self.assertEqual(spec.eulerseq[0], ord('z'))

    # Add a body, check that it has default orientation.
    body = spec.worldbody.add_body()
    self.assertEqual(body.name, '')
    np.testing.assert_array_equal(body.quat, [1, 0, 0, 0])

    # Change the name of the body and read it back twice.
    body.name = 'foobar'
    self.assertEqual(body.name, 'foobar')
    body.name = 'baz'
    self.assertEqual(body.name, 'baz')

    # Change the position of the body and read it back.
    body.pos = [1, 2, 3]
    np.testing.assert_array_equal(body.pos, [1, 2, 3])
    self.assertEqual(body.pos.shape, (3,))

    # Change the orientation of the body and read it back.
    body.quat = [0, 1, 0, 0]
    np.testing.assert_array_equal(body.quat, [0, 1, 0, 0])
    self.assertEqual(body.quat.shape, (4,))

    # Add a site to the body with user data and read it back.
    site = body.add_site()
    site.name = 'sitename'
    site.type = mujoco.mjtGeom.mjGEOM_BOX
    site.userdata = [1, 2, 3, 4, 5, 6]
    self.assertEqual(site.name, 'sitename')
    self.assertEqual(site.type, mujoco.mjtGeom.mjGEOM_BOX)
    np.testing.assert_array_equal(site.userdata, [1, 2, 3, 4, 5, 6])

    # Check that the site and body have no id before compilation.
    self.assertEqual(body.id, -1)
    self.assertEqual(site.id, -1)

    # Compile the spec and check for expected values in the model.
    model = spec.compile()
    self.assertEqual(spec.worldbody.id, 0)
    self.assertEqual(body.id, 1)
    self.assertEqual(site.id, 0)
    self.assertEqual(model.nbody, 2)  # 2 bodies, including the world body
    np.testing.assert_array_equal(model.body_pos[1], [1, 2, 3])
    np.testing.assert_array_equal(model.body_quat[1], [0, 1, 0, 0])
    self.assertEqual(model.nsite, 1)
    self.assertEqual(model.nuser_site, 6)
    np.testing.assert_array_equal(model.site_user[0], [1, 2, 3, 4, 5, 6])

    self.assertEqual(spec.to_xml(), textwrap.dedent("""\
        <mujoco model="MuJoCo Model">
          <compiler angle="radian"/>

          <size nuser_site="6"/>

          <worldbody>
            <body name="baz" pos="1 2 3" quat="0 1 0 0">
              <site name="sitename" pos="0 0 0" type="box" user="1 2 3 4 5 6"/>
            </body>
          </worldbody>
        </mujoco>
    """),)

  def test_kwarg(self):
    # Create a spec.
    spec = mujoco.MjSpec()

    # Add material.
    material = spec.add_material(texrepeat=[1, 2], emission=-1)
    np.testing.assert_array_equal(material.texrepeat, [1, 2])
    self.assertEqual(material.emission, -1)

    # Add mesh.
    mesh = spec.add_mesh(refpos=[1, 2, 3])
    np.testing.assert_array_equal(mesh.refpos, [1, 2, 3])

    # Add pair.
    pair = spec.add_pair(gap=0.1)
    self.assertEqual(pair.gap, 0.1)

    # Add equality.
    equality = spec.add_equality(objtype=mujoco.mjtObj.mjOBJ_SITE)
    self.assertEqual(equality.objtype, mujoco.mjtObj.mjOBJ_SITE)

    # Add tendon.
    tendon = spec.add_tendon(stiffness=2, springlength=[0.1, 0.2])
    self.assertEqual(tendon.stiffness, 2)
    np.testing.assert_array_equal(tendon.springlength, [0.1, 0.2])

    # Add actuator.
    actuator = spec.add_actuator(actdim=10, ctrlrange=[-1, 10])
    self.assertEqual(actuator.actdim, 10)
    np.testing.assert_array_equal(actuator.ctrlrange, [-1, 10])

    # Add skin.
    skin = spec.add_skin(inflate=2.0, vertid=[[1, 1], [2, 2]])
    self.assertEqual(skin.inflate, 2.0)
    np.testing.assert_array_equal(skin.vertid, [[1, 1], [2, 2]])

    # Add texture.
    texture = spec.add_texture(builtin=0, nchannel=3)
    self.assertEqual(texture.builtin, 0)
    self.assertEqual(texture.nchannel, 3)

    # Add text.
    text = spec.add_text(data='data', info='info')
    self.assertEqual(text.data, 'data')
    self.assertEqual(text.info, 'info')

    # Add tuple.
    tuple_ = spec.add_tuple(objprm=[2.0, 3.0, 5.0], objname=['obj'])
    np.testing.assert_array_equal(tuple_.objprm, [2.0, 3.0, 5.0])
    self.assertEqual(tuple_.objname, ['obj'])

    # Add flex.
    flex = spec.add_flex(friction=[1, 2, 3], texcoord=[1.0, 2.0, 3.0])
    np.testing.assert_array_equal(flex.friction, [1, 2, 3])
    np.testing.assert_array_equal(flex.texcoord, [1.0, 2.0, 3.0])

    # Add hfield.
    hfield = spec.add_hfield(nrow=2, content_type='type')
    self.assertEqual(hfield.nrow, 2)
    self.assertEqual(hfield.content_type, 'type')

    # Add key.
    key = spec.add_key(time=1.2, qpos=[1.0, 2.0])
    self.assertEqual(key.time, 1.2)
    np.testing.assert_array_equal(key.qpos, [1.0, 2.0])

    # Add numeric.
    numeric = spec.add_numeric(data=[1.0, 1.1, 1.2], size=2)
    np.testing.assert_array_equal(numeric.data, [1.0, 1.1, 1.2])
    self.assertEqual(numeric.size, 2)

    # Add exclude.
    exclude = spec.add_exclude(bodyname2='body2')
    self.assertEqual(exclude.bodyname2, 'body2')

    # Add sensor.
    sensor = spec.add_sensor(
        needstage=mujoco.mjtStage.mjSTAGE_ACC, objtype=mujoco.mjtObj.mjOBJ_SITE
    )
    self.assertEqual(sensor.needstage, mujoco.mjtStage.mjSTAGE_ACC)
    self.assertEqual(sensor.objtype, mujoco.mjtObj.mjOBJ_SITE)

    # Add plugin.
    plugin = spec.add_plugin(
        name='name',
        instance_name='instance',
        plugin_slot=7,
        active=True,
        info='info',
    )
    self.assertEqual(plugin.name, 'name')
    self.assertEqual(plugin.instance_name, 'instance')
    self.assertEqual(plugin.plugin_slot, 7)
    self.assertEqual(plugin.active, True)
    self.assertEqual(plugin.info, 'info')

    # Add a body.
    body = spec.worldbody.add_body(
        name='body', pos=[1, 2, 3], quat=[0, 0, 0, 1]
    )
    self.assertEqual(body.name, 'body')
    np.testing.assert_array_equal(body.pos, [1, 2, 3])
    np.testing.assert_array_equal(body.quat, [0, 0, 0, 1])

    # Add a body with a plugin.
    body_with_plugin = spec.worldbody.add_body(plugin=plugin)
    self.assertEqual(body_with_plugin.plugin.name, 'name')
    self.assertEqual(body_with_plugin.plugin.instance_name, 'instance')
    self.assertEqual(body_with_plugin.plugin.plugin_slot, 7)
    self.assertEqual(body_with_plugin.plugin.active, True)
    self.assertEqual(body_with_plugin.plugin.info, 'info')

    # Add a geom.
    geom = body.add_geom(
        name='geom',
        pos=[3, 2, 1],
        fromto=[1, 2, 3, 4, 5, 6],
        contype=3,
    )

    self.assertEqual(geom.name, 'geom')
    np.testing.assert_array_equal(geom.pos, [3, 2, 1])
    np.testing.assert_array_equal(geom.fromto, [1, 2, 3, 4, 5, 6])
    self.assertEqual(geom.contype, 3)

    # Add a site to the body with user data and read it back.
    site = body.add_site(
        name='sitename',
        pos=[0, 1, 2],
        quat=[1, 0, 0, 0],
        fromto=[0, 1, 2, 3, 4, 5],
        size=[3, 2, 1],
        type=mujoco.mjtGeom.mjGEOM_BOX,
        material='material',
        group=7,
        rgba=[1, 1, 1, 0.5],
        userdata=[1, 2, 3, 4, 5, 6],
        info='info',
    )
    self.assertEqual(site.name, 'sitename')
    np.testing.assert_array_equal(site.pos, [0, 1, 2])
    np.testing.assert_array_equal(site.quat, [1, 0, 0, 0])
    np.testing.assert_array_equal(site.fromto, [0, 1, 2, 3, 4, 5])
    np.testing.assert_array_equal(site.size, [3, 2, 1])
    self.assertEqual(site.type, mujoco.mjtGeom.mjGEOM_BOX)
    self.assertEqual(site.material, 'material')
    self.assertEqual(site.group, 7)
    np.testing.assert_array_equal(site.rgba, [1, 1, 1, 0.5])
    np.testing.assert_array_equal(site.userdata, [1, 2, 3, 4, 5, 6])
    self.assertEqual(site.info, 'info')

    # Add camera.
    cam = body.add_camera(orthographic=1, resolution=[10, 20])
    self.assertEqual(cam.orthographic, 1)
    np.testing.assert_array_equal(cam.resolution, [10, 20])

    # Add frame.
    framea0 = body.add_frame(name='framea', pos=[1, 2, 3], quat=[0, 0, 0, 1])
    np.testing.assert_array_equal(framea0.pos, [1, 2, 3])
    np.testing.assert_array_equal(framea0.quat, [0, 0, 0, 1])

    frameb0 = body.add_frame(
        framea0, name='frameb', pos=[4, 5, 6], quat=[0, 1, 0, 0]
    )

    framea1 = body.first_frame()
    frameb1 = body.next_frame(framea1)

    self.assertEqual(framea1.name, framea0.name)
    self.assertEqual(frameb1.name, frameb0.name)
    np.testing.assert_array_equal(framea1.pos, framea0.pos)
    np.testing.assert_array_equal(framea1.quat, framea0.quat)
    np.testing.assert_array_equal(frameb1.pos, frameb0.pos)
    np.testing.assert_array_equal(frameb1.quat, frameb0.quat)

    # Add joint.
    joint = body.add_joint(type=mujoco.mjtJoint.mjJNT_HINGE, axis=[0, 1, 0])
    self.assertEqual(joint.type, mujoco.mjtJoint.mjJNT_HINGE)
    np.testing.assert_array_equal(joint.axis, [0, 1, 0])

    # Add freejoint.
    freejoint = body.add_freejoint()
    self.assertEqual(freejoint.type, mujoco.mjtJoint.mjJNT_FREE)
    freejoint_align = body.add_freejoint(align=True)
    self.assertEqual(freejoint_align.align, True)

    with self.assertRaises(TypeError) as cm:
      body.add_freejoint(axis=[1, 2, 3])
    self.assertEqual(
        str(cm.exception),
        'Invalid axis keyword argument. Valid options are: align, group, name.',
    )

    # Add light.
    light = body.add_light(attenuation=[1, 2, 3])
    np.testing.assert_array_equal(light.attenuation, [1, 2, 3])

    # Invalid input for valid keyword argument.
    with self.assertRaises(ValueError) as cm:
      body.add_geom(pos='pos')
    self.assertEqual(
        str(cm.exception),
        'pos should be a list/array.',
    )

    with self.assertRaises(ValueError) as cm:
      body.add_geom(pos=[0, 1])
    self.assertEqual(
        str(cm.exception),
        'pos should be a list/array of size 3.',
    )

    with self.assertRaises(ValueError) as cm:
      body.add_geom(type='type')
    self.assertEqual(
        str(cm.exception),
        'type is the wrong type.',
    )

    with self.assertRaises(ValueError) as cm:
      body.add_geom(userdata='')
    self.assertEqual(
        str(cm.exception),
        'userdata has the wrong type.',
    )

    # Invalid keyword argument.
    with self.assertRaises(TypeError) as cm:
      body.add_geom(vel='vel')
    self.assertEqual(
        str(cm.exception),
        'Invalid vel keyword argument. Valid options are: name, type, pos,'
        ' quat, axisangle, xyaxes, zaxis, euler, fromto, size, contype,'
        ' conaffinity, condim, priority, friction, solmix, solref, solimp,'
        ' margin, gap, mass, density, typeinertia, fluid_ellipsoid,'
        ' fluid_coefs, material, rgba, group, hfieldname, meshname, fitscale,'
        ' userdata, plugin, info.',
    )

    # Orientation keyword arguments.
    geom_axisangle = body.add_geom(axisangle=[1, 2, 3, 4])
    geom_xyaxes = body.add_geom(xyaxes=[1, 2, 3, 4, 5, 6])
    geom_zaxis = body.add_geom(zaxis=[1, 2, 3])
    geom_euler = body.add_geom(euler=[1, 2, 3])

    self.assertEqual(
        geom_axisangle.alt.type, mujoco.mjtOrientation.mjORIENTATION_AXISANGLE
    )
    self.assertEqual(
        geom_xyaxes.alt.type, mujoco.mjtOrientation.mjORIENTATION_XYAXES
    )
    self.assertEqual(
        geom_zaxis.alt.type, mujoco.mjtOrientation.mjORIENTATION_ZAXIS
    )
    self.assertEqual(
        geom_euler.alt.type, mujoco.mjtOrientation.mjORIENTATION_EULER
    )
    np.testing.assert_array_equal(geom_axisangle.alt.axisangle, [1, 2, 3, 4])
    np.testing.assert_array_equal(geom_xyaxes.alt.xyaxes, [1, 2, 3, 4, 5, 6])
    np.testing.assert_array_equal(geom_zaxis.alt.zaxis, [1, 2, 3])
    np.testing.assert_array_equal(geom_euler.alt.euler, [1, 2, 3])

    body_iaxisangle = spec.worldbody.add_body(iaxisangle=[1, 2, 3, 4])
    body_ixyaxes = spec.worldbody.add_body(ixyaxes=[1, 2, 3, 4, 5, 6])
    body_izaxis = spec.worldbody.add_body(izaxis=[1, 2, 3])
    body_ieuler = spec.worldbody.add_body(ieuler=[1, 2, 3])
    body_euler_ieuler = spec.worldbody.add_body(
        euler=[1, 2, 3], ieuler=[4, 5, 6]
    )
    np.testing.assert_array_equal(body_iaxisangle.ialt.axisangle, [1, 2, 3, 4])
    np.testing.assert_array_equal(body_ixyaxes.ialt.xyaxes, [1, 2, 3, 4, 5, 6])
    np.testing.assert_array_equal(body_izaxis.ialt.zaxis, [1, 2, 3])
    np.testing.assert_array_equal(body_ieuler.ialt.euler, [1, 2, 3])
    np.testing.assert_array_equal(body_euler_ieuler.alt.euler, [1, 2, 3])
    np.testing.assert_array_equal(body_euler_ieuler.ialt.euler, [4, 5, 6])

    # Test invalid orientation keyword arguments.
    with self.assertRaises(ValueError) as cm:
      body.add_geom(axisangle=[1, 2, 3])
    self.assertEqual(
        str(cm.exception),
        'axisangle should be a list/array of size 4.',
    )
    with self.assertRaises(ValueError) as cm:
      body.add_geom(xyaxes=[1, 2, 3, 4, 5])
    self.assertEqual(
        str(cm.exception),
        'xyaxes should be a list/array of size 6.',
    )
    with self.assertRaises(ValueError) as cm:
      body.add_geom(zaxis=[1, 2, 3, 4])
    self.assertEqual(
        str(cm.exception),
        'zaxis should be a list/array of size 3.',
    )
    with self.assertRaises(ValueError) as cm:
      body.add_geom(euler=[1])
    self.assertEqual(
        str(cm.exception),
        'euler should be a list/array of size 3.',
    )
    with self.assertRaises(ValueError) as cm:
      body.add_geom(axisangle=[1, 2, 3, 4], euler=[1, 2, 3])
    self.assertEqual(
        str(cm.exception),
        'Only one of: axisangle, xyaxes, zaxis, oreuler can be set.',
    )
    with self.assertRaises(ValueError) as cm:
      spec.worldbody.add_body(iaxisangle=[1, 2, 3, 4], ieuler=[1, 2, 3])
    self.assertEqual(
        str(cm.exception),
        'Only one of: iaxisangle, ixyaxes, izaxis, orieuler can be set.',
    )

  def test_load_xml(self):
    filename = '../../test/testdata/model.xml'
    state_type = mujoco.mjtState.mjSTATE_INTEGRATION

    # Load from file.
    spec1 = mujoco.MjSpec()
    spec1.from_file(filename)
    model1 = spec1.compile()
    data1 = mujoco.MjData(model1)
    mujoco.mj_step(model1, data1)
    size1 = mujoco.mj_stateSize(model1, state_type)
    state1 = np.empty(size1, np.float64)
    mujoco.mj_getState(model1, data1, state1, state_type)

    # Load from string.
    spec2 = mujoco.MjSpec()
    with open(filename, 'r') as file:
      spec2.from_string(file.read().rstrip())
    model2 = spec2.compile()
    data2 = mujoco.MjData(model2)
    mujoco.mj_step(model2, data2)
    size2 = mujoco.mj_stateSize(model2, state_type)
    state2 = np.empty(size2, np.float64)
    mujoco.mj_getState(model2, data2, state2, state_type)

    # Check that the state is the same.
    np.testing.assert_array_equal(state1, state2)

  def test_compile_errors_with_line_info(self):
    spec = mujoco.MjSpec()

    added_on_line = get_linenumber() + 1
    geom = spec.worldbody.add_geom()
    geom.name = 'MyGeom'
    geom.info = f'geom added on line {added_on_line}'

    # Try to compile, get error.
    expected_error = (
        'Error: size 0 must be positive in geom\n'
        + f'Element name \'MyGeom\', id 0, geom added on line {added_on_line}'
    )
    with self.assertRaisesRegex(ValueError, expected_error):
      spec.compile()

  def test_recompile(self):
    # Create a spec.
    spec = mujoco.MjSpec()

    # Add movable body1.
    body1 = spec.worldbody.add_body()
    geom = body1.add_geom()
    geom.size[0] = 1
    geom.pos = [1, 1, 0]
    joint = body1.add_joint()
    joint.type = mujoco.mjtJoint.mjJNT_BALL

    # Compile model, make data.
    model = spec.compile()
    data = mujoco.MjData(model)

    # Simulate for 1 second.
    while data.time < 1:
      mujoco.mj_step(model, data)

    # Add movable body2.
    body2 = spec.worldbody.add_body()
    body2.pos[1] = 3
    geom = body2.add_geom()
    geom.size[0] = 1
    geom.pos = [0, 1, 0]
    joint = body2.add_joint()
    joint.type = mujoco.mjtJoint.mjJNT_BALL

    # Recompile model and data while maintaining the state.
    model_new, data_new = spec.recompile(model, data)

    # Check that the state is preserved.
    np.testing.assert_array_equal(model_new.body_pos[1], model.body_pos[1])
    np.testing.assert_array_equal(data_new.qpos[:4], data.qpos)
    np.testing.assert_array_equal(data_new.qvel[:3], data.qvel)

  def test_uncompiled_spec_cannot_be_written(self):
    spec = mujoco.MjSpec()

    # Cannot write XML of an uncompiled spec.
    expected_error = 'XML Write error: Only compiled model can be written'
    with self.assertRaisesWithLiteralMatch(mujoco.FatalError, expected_error):
      spec.to_xml()

  def test_modelname_default_class(self):
    spec = mujoco.MjSpec()
    spec.modelname = 'test'

    main = spec.default()
    main.geom.size[0] = 2

    def1 = spec.add_default('def1', main)
    def1.geom.size[0] = 3

    spec.worldbody.add_geom(def1)
    spec.worldbody.add_geom(main)

    spec.compile()
    self.assertEqual(spec.to_xml(), textwrap.dedent("""\
        <mujoco model="test">
          <compiler angle="radian"/>

          <default>
            <geom size="2 0 0"/>
            <default class="def1">
              <geom size="3 0 0"/>
            </default>
          </default>

          <worldbody>
            <geom class="def1"/>
            <geom/>
          </worldbody>
        </mujoco>
    """))
    spec = mujoco.MjSpec()
    spec.modelname = 'test'

    main = spec.default()
    main.geom.size[0] = 2

    def1 = spec.add_default('def1', main)
    def1.geom.size[0] = 3

    spec.worldbody.add_geom(def1)
    spec.worldbody.add_geom(main)

    spec.compile()
    self.assertEqual(spec.to_xml(), textwrap.dedent("""\
        <mujoco model="test">
          <compiler angle="radian"/>

          <default>
            <geom size="2 0 0"/>
            <default class="def1">
              <geom size="3 0 0"/>
            </default>
          </default>

          <worldbody>
            <geom class="def1"/>
            <geom/>
          </worldbody>
        </mujoco>
    """))

  def test_element_list(self):
    spec = mujoco.MjSpec()
    sensor1 = spec.add_sensor()
    sensor2 = spec.add_sensor()
    sensor3 = spec.add_sensor()
    sensor1.name = 'sensor1'
    sensor2.name = 'sensor2'
    sensor3.name = 'sensor3'
    self.assertLen(spec.sensors, 3)
    self.assertEqual(spec.sensors[0].name, 'sensor1')
    self.assertEqual(spec.sensors[1].name, 'sensor2')
    self.assertEqual(spec.sensors[2].name, 'sensor3')

  def test_iterators(self):
    spec = mujoco.MjSpec()
    geom1 = spec.worldbody.add_geom()
    geom2 = spec.worldbody.add_geom()
    geom3 = spec.worldbody.add_geom()
    geom1.name = 'geom1'
    geom2.name = 'geom2'
    geom3.name = 'geom3'
    geom = spec.worldbody.first_geom()
    i = 1
    while geom:
      self.assertEqual(geom.name, 'geom' + str(i))
      geom = spec.worldbody.next_geom(geom)
      i += 1

  def test_assets(self):
    cube = """
      v -1 -1  1
      v  1 -1  1
      v -1  1  1
      v  1  1  1
      v -1  1 -1
      v  1  1 -1
      v -1 -1 -1
      v  1 -1 -1"""
    spec = mujoco.MjSpec()
    mesh = spec.add_mesh()
    mesh.name = 'cube'
    mesh.file = 'cube.obj'
    geom = spec.worldbody.add_geom()
    geom.type = mujoco.mjtGeom.mjGEOM_MESH
    geom.meshname = 'cube'
    model = spec.compile({'cube.obj': cube})
    self.assertEqual(model.nmeshvert, 8)

  def test_delete(self):
    filename = '../../test/testdata/model.xml'

    spec = mujoco.MjSpec()
    spec.from_file(filename)

    model = spec.compile()
    self.assertIsNotNone(model)
    self.assertEqual(model.nsite, 11)
    self.assertEqual(model.nsensor, 11)

    head = spec.find_body('head')
    self.assertIsNotNone(head)
    site = head.first_site()
    self.assertIsNotNone(site)

    site.delete()
    spec.sensors[-1].delete()
    spec.sensors[-1].delete()

    model = spec.compile()
    self.assertIsNotNone(model)
    self.assertEqual(model.nsite, 10)
    self.assertEqual(model.nsensor, 9)

  def test_plugin(self):
    xml = """
    <mujoco>
      <extension>
        <plugin plugin="mujoco.elasticity.cable"/>
      </extension>
    </mujoco>
    """

    spec = mujoco.MjSpec()
    spec.from_string(xml)
    self.assertIsNotNone(spec.worldbody)

    body = spec.worldbody.add_body()
    body.plugin.name = 'mujoco.elasticity.cable'
    body.plugin.id = spec.add_plugin()
    body.plugin.active = True
    self.assertEqual(body.plugin.id, 0)

    geom = body.add_geom()
    geom.type = mujoco.mjtGeom.mjGEOM_BOX
    geom.size[0] = 1
    geom.size[1] = 1
    geom.size[2] = 1

    model = spec.compile()
    self.assertIsNotNone(model)
    self.assertEqual(model.nplugin, 1)
    self.assertEqual(model.body_plugin[1], 0)

  def test_recompile_error(self):
    main_xml = """
    <mujoco>
      <worldbody>
        <body>
          <geom size="0.1"/>
        </body>
      </worldbody>
    </mujoco>
    """

    spec = mujoco.MjSpec()
    spec.from_string(main_xml)
    model = spec.compile()
    data = mujoco.MjData(model)

    spec.add_material().name = 'yellow'
    spec.add_material().name = 'yellow'

    with self.assertRaisesRegex(
        ValueError, "Error: repeated name 'yellow' in material"
    ):
      spec.recompile(model, data)

  def test_delete_unused_plugin(self):
    spec = mujoco.MjSpec()
    spec.from_string(textwrap.dedent("""
      <mujoco model="MuJoCo Model">
        <extension>
          <plugin plugin="mujoco.pid">
            <instance name="pid1">
              <config key="kp" value="4.0"/>
            </instance>
          </plugin>
        </extension>

        <worldbody>
          <body>
            <geom size="1"/>
          </body>
        </worldbody>
      </mujoco>
    """))
    plugin = spec.plugins[0]
    self.assertIsNotNone(plugin)
    plugin.delete()

    model = spec.compile()
    self.assertIsNotNone(model)
    self.assertEqual(model.nplugin, 0)

if __name__ == '__main__':
  absltest.main()
