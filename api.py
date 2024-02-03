# maya
from maya import cmds as mc
from maya import mel
from maya.api import OpenMaya as om

# built-ins
import json
import math
import traceback

data_structure = {
    "driver": "",
    "driven": [],
    "pose": {},
    "controller": ""
}

l_mirror_token = "_L"
r_mirror_token = "_R"


def initialize():
    manager = mc.createNode("transform", name="pose_manager") if not mc.objExists("pose_manager") else "pose_manager"
    mc.addAttr(manager, longName="_data", dataType="string") if not mc.objExists("pose_manager._data") else None
    mc.setAttr(manager + "._data", json.dumps({}), type="string") if not mc.getAttr("pose_manager._data") else None
    return manager


def get_data():
    return json.loads(mc.getAttr("pose_manager._data"))


def set_data(data):
    mc.setAttr("pose_manager._data", json.dumps(data), type="string")


def add_driver(driver, controller):
    if not mc.objExists(driver):
        mc.warning("Don't exists : '{0}'".format(driver))
        return
    if not mc.objExists(controller):
        mc.warning("Don't exists : '{0}'".format(controller))
        return
    interpolator_name = driver + "_pmInterpolator"
    if mc.objExists(interpolator_name):
        mc.warning("Already exists : '{0}'".format(interpolator_name))
        return

    try:
        mc.undoInfo(openChunk=True, infinity=True)

        manager = initialize()

        # new interpolator
        mc.select(driver)
        interpolator = "|" + mc.poseInterpolator(name=driver + "_pmInterpolator")[0]
        interpolator = mc.parent(interpolator, manager)[0]
        interpolator = mc.listRelatives(interpolator, shapes=True, fullPath=True)[0]
        mc.setAttr(interpolator + ".interpolation", 1)

        # add data
        data = get_data()
        data[interpolator_name] = data_structure

        data[interpolator_name]["driver"] = driver
        data[interpolator_name]["controller"] = controller

        set_data(data)
    except:
        print(traceback.format_exc())
        mc.warning("Occur error add_driver '{0}' '{1}'. Returned to action".format(driver, controller))
        mc.undoInfo(closeChunk=True)
        mc.undo()
    else:
        mc.undoInfo(closeChunk=True)


def add_pose(driver, pose):
    interpolator_name = driver + "_pmInterpolator"
    if not mc.objExists(interpolator_name):
        mc.warning("Don't exists '{0}' interpolator node '{1}'".format(driver, interpolator_name))
        return
    interpolator = mc.listRelatives(interpolator_name, shapes=True)[0]

    data = get_data()

    if pose in data[interpolator_name]["pose"]:
        mc.warning("Already exists pose '{0}' in _data".format(pose))
        return

    if pose in (mc.poseInterpolator(interpolator, query=True, poseNames=True) or []):
        mc.warning("Already exists pose '{0}' in interpolator".format(pose))
        return

    try:
        mc.undoInfo(openChunk=True, infinity=True)
        index = mc.poseInterpolator(interpolator, edit=True, addPose=pose)
        mc.setAttr(interpolator + ".pose[{0}].poseType".format(index), 1)

        for blend_m in data[interpolator_name]["driven"]:
            mc.connectAttr(interpolator + ".output[{0}]".format(index), blend_m + ".target[{0}].weight".format(index))
        driven = [k.replace("_bm", "") for k in data[interpolator_name]["driven"]]
        driven_pos = {}
        for d in driven:
            driven_pos[d] = {}
            driven_pos[d]["t"] = (0, 0, 0)
            driven_pos[d]["r"] = (0, 0, 0)

        data[interpolator_name]["pose"][pose] = {
            "t": mc.getAttr(data[interpolator_name]["controller"] + ".t")[0],
            "r": mc.getAttr(data[interpolator_name]["controller"] + ".r")[0],
            "driven": driven_pos
        }
        set_data(data)
    except:
        print(traceback.format_exc())
        mc.warning("Occur error add_pose '{0}' '{1}'. Returned to action".format(driver, pose))
        mc.undoInfo(closeChunk=True)
        mc.undo()
    else:
        mc.undoInfo(closeChunk=True)


def add_driven(driver, driven):
    interpolator_name = driver + "_pmInterpolator"
    if not mc.objExists(interpolator_name):
        mc.warning("Don't exists '{0}' interpolator node '{1}'".format(driver, interpolator_name))
        return
    interpolator = mc.listRelatives(interpolator_name, shapes=True)[0]

    data = get_data()

    driven_npo = driven + "_pm"
    blend_m = driven + "_bm"

    if blend_m in data[interpolator_name]["driven"]:
        mc.warning("Already exists '{0}' driven '{1}'".format(interpolator, driven))
        return

    data[interpolator_name]["driven"].append(blend_m)

    try:
        mc.undoInfo(openChunk=True, infinity=True)
        blend_m = mc.createNode("blendMatrix", name=blend_m) if not mc.objExists(blend_m) else blend_m

        if not mc.objExists(driven_npo):
            parent = mc.listRelatives(driven, parent=True)
            driven_npo = mc.createNode("transform", name=driven_npo, parent=parent[0] if parent else None)
            m = mc.xform(driven, query=True, matrix=True, worldSpace=True)
            mc.xform(driven_npo, matrix=m, worldSpace=True)
            mc.parent(driven, driven_npo)

            decom_m = mc.createNode("decomposeMatrix")
            mc.connectAttr(blend_m + ".outputMatrix", decom_m + ".inputMatrix")
            mc.connectAttr(decom_m + ".outputTranslate", driven_npo + ".t")
            mc.connectAttr(decom_m + ".outputRotate", driven_npo + ".r")

        for k, v in data[interpolator_name]["pose"].items():
            names = mc.poseInterpolator(interpolator, query=True, poseNames=True)
            indexes = mc.poseInterpolator(interpolator, query=True, index=True)
            index = indexes[names.index(k)]

            data[interpolator_name]["pose"][k]["driven"][driven] = {}
            data[interpolator_name]["pose"][k]["driven"][driven]["t"] = (0, 0, 0)
            data[interpolator_name]["pose"][k]["driven"][driven]["r"] = (0, 0, 0)
            mc.connectAttr(interpolator + ".output[{0}]".format(index),
                           blend_m + ".target[{0}].weight".format(index))
            m = [x for x in om.MMatrix()]
            mc.setAttr(blend_m + ".target[{0}].targetMatrix".format(index), m, type="matrix")
        set_data(data)
    except Exception:
        print(traceback.format_exc())
        mc.warning("Occur error add_driven '{0}' '{1}'. Returned to action".format(driver, driven))
        mc.undoInfo(closeChunk=True)
        mc.undo()
    else:
        mc.undoInfo(closeChunk=True)


def update_pose(driver, pose):
    interpolator_name = driver + "_pmInterpolator"
    if not mc.objExists(interpolator_name):
        mc.warning("Don't exists '{0}' interpolator node '{1}'".format(driver, interpolator_name))
        return
    interpolator = mc.listRelatives(interpolator_name, shapes=True)[0]

    data = get_data()

    if pose not in data[interpolator_name]["pose"]:
        mc.warning("Don't exists '{0}' pose '{1}'".format(interpolator, pose))
        return

    try:
        mc.undoInfo(openChunk=True, infinity=True)

        controller = data[interpolator_name]["controller"]
        data[interpolator_name]["pose"][pose]["t"] = mc.getAttr(controller + ".t")[0]
        data[interpolator_name]["pose"][pose]["r"] = mc.getAttr(controller + ".r")[0]
        mc.poseInterpolator(interpolator, edit=True, updatePose=pose)

        set_data(data)
    except Exception:
        print(traceback.format_exc())
        mc.warning("Occur error edit_pose '{0}' '{1}'. Returned to action".format(driver, pose))
        mc.undoInfo(closeChunk=True)
        mc.undo()
    else:
        mc.undoInfo(closeChunk=True)


def update_driven(driver, pose, driven):
    interpolator_name = driver + "_pmInterpolator"
    if not mc.objExists(interpolator_name):
        mc.warning("Don't exists '{0}' interpolator node '{1}'".format(driver, interpolator_name))
        return
    interpolator = mc.listRelatives(interpolator_name, shapes=True)[0]

    data = get_data()

    blend_m = driven + "_bm"
    driven_npo = driven + "_pm"

    if blend_m not in data[interpolator_name]["driven"]:
        mc.warning("Don't exists blendMatrix '{0}' in _data".format(blend_m))
        return

    if not mc.objExists(blend_m):
        mc.warning("Don't exists blendMatrix '{0}'".format(blend_m))
        return

    try:
        mc.undoInfo(openChunk=True, infinity=True)

        names = mc.poseInterpolator(interpolator, query=True, poseNames=True)
        indexes = mc.poseInterpolator(interpolator, query=True, index=True)
        index = indexes[names.index(pose)]

        parent = mc.listRelatives(driven_npo, parent=True)
        if parent:
            parent_m = om.MMatrix(mc.xform(parent[0], query=True, matrix=True, worldSpace=True))
        else:
            parent_m = om.MMatrix()
        driven_m = om.MMatrix(mc.xform(driven, query=True, matrix=True, worldSpace=True))
        m = driven_m * parent_m.inverse()

        mc.setAttr(blend_m + ".target[{0}].targetMatrix".format(index), m, type="matrix")
        mc.xform(driven, matrix=[x for x in om.MMatrix()], worldSpace=False)

        m = om.MTransformationMatrix(m)
        t = [x for x in m.translation(om.MSpace.kWorld)]
        r = [math.degrees(x) for x in m.rotation()]

        data[interpolator_name]["pose"][pose]["driven"][driven]["t"] = t
        data[interpolator_name]["pose"][pose]["driven"][driven]["r"] = r
        set_data(data)
    except Exception:
        traceback.print_exc()
        mc.warning("Occur error edit_driven '{0}' '{1}'. Returned to action".format(driver, pose))
        mc.undoInfo(closeChunk=True)
        mc.undo()
    else:
        mc.undoInfo(closeChunk=True)


def delete_driver(driver):
    interpolator_name = driver + "_pmInterpolator"
    if not mc.objExists(interpolator_name):
        mc.warning("Don't exists '{0}' interpolator node '{1}'".format(driver, interpolator_name))
        return

    data = get_data()

    try:
        mc.undoInfo(openChunk=True, infinity=True)

        delete_list = []
        for blend_m in data[interpolator_name]["driven"]:
            driven = blend_m.replace("_bm", "")

            driven_npo = driven + "_pm"
            parent = mc.listRelatives(driven_npo, parent=True)
            if parent:
                mc.parent(driven, parent[0])
            else:
                mc.parent(driven, world=True)
            mc.xform(driven, matrix=om.MMatrix(), worldSpace=False)

            delete_list.append(driven_npo)

        mc.delete([interpolator_name] + delete_list + data[interpolator_name]["driven"])

        del data[interpolator_name]

        set_data(data)
        if not data:
            mc.delete(initialize())
    except Exception:
        traceback.print_exc()
        mc.warning("Occur error remove_driver '{0}'. Returned to action".format(driver))
        mc.undoInfo(closeChunk=True)
        mc.undo()
    else:
        mc.undoInfo(closeChunk=True)


def delete_pose(driver, pose):
    interpolator_name = driver + "_pmInterpolator"
    if not mc.objExists(interpolator_name):
        mc.warning("Don't exists '{0}' interpolator node '{1}'".format(driver, interpolator_name))
        return
    interpolator = mc.listRelatives(interpolator_name, shapes=True)[0]

    data = get_data()

    if pose not in data[interpolator_name]["pose"]:
        mc.warning("Don't exists '{0}' pose '{1}'".format(driver, pose))
        return

    if pose not in mc.poseInterpolator(interpolator, query=True, poseNames=True):
        mc.warning("Don't exists '{0}' pose '{1}'".format(driver, pose))
        return

    try:
        mc.undoInfo(openChunk=True, infinity=True)

        index = mc.poseInterpolator(interpolator, edit=True, deletePose=pose)
        for blend_m in data[interpolator_name]["driven"]:
            mc.removeMultiInstance(blend_m + ".target[{0}]".format(index))
        del data[interpolator_name]["pose"][pose]

        set_data(data)
    except Exception:
        traceback.print_exc()
        mc.warning("Occur error edit_driven '{0}' '{1}'. Returned to action".format(driver, pose))
        mc.undoInfo(closeChunk=True)
        mc.undo()
    else:
        mc.undoInfo(closeChunk=True)


def delete_driven(driver, driven):
    interpolator_name = driver + "_pmInterpolator"
    if not mc.objExists(interpolator_name):
        mc.warning("Don't exists '{0}' interpolator node '{1}'".format(driver, interpolator_name))
        return

    data = get_data()

    blend_m = driven + "_bm"
    driven_npo = driven + "_pm"
    if not mc.objExists(blend_m):
        mc.warning("Don't exists '{0}'".format(blend_m))
        return
    if not mc.objExists(driven_npo):
        mc.warning("Don't exists '{0}'".format(driven_npo))
        return
    if blend_m not in data[interpolator_name]["driven"]:
        mc.warning("Don't exists '{0}' in _data".format(blend_m))
        return

    try:
        mc.undoInfo(openChunk=True, infinity=True)

        parent = mc.listRelatives(driven_npo, parent=True)
        if parent:
            mc.parent(driven, parent[0])
        else:
            mc.parent(driven, world=True)

        mc.delete([blend_m, driven_npo])

        data[interpolator_name]["driven"].remove(blend_m)
        for v in data[interpolator_name]["pose"].values():
            del v["driven"][driven]
        set_data(data)
    except Exception:
        traceback.print_exc()
        mc.warning("Occur error remove_driven '{0}' '{1}'. Returned to action".format(driver, driven))
        mc.undoInfo(closeChunk=True)
        mc.undo()
    else:
        mc.undoInfo(closeChunk=True)


def mirror_driver(driver):
    source_interpolator_name = driver + "_pmInterpolator"
    if not mc.objExists(source_interpolator_name):
        mc.warning("Don't exists '{0}' interpolator node '{1}'".format(driver, source_interpolator_name))
        return

    data = get_data()

    if source_interpolator_name not in data:
        mc.warning("Don't exists '{0}' interpolator in _data".format(source_interpolator_name))
        return

    # target name
    source_side = l_mirror_token if l_mirror_token in driver else r_mirror_token
    target_side = r_mirror_token if source_side == l_mirror_token else l_mirror_token
    target_interpolator_name = source_interpolator_name.replace(source_side, target_side)
    target_driver = driver.replace(source_side, target_side)
    target_controller = data[source_interpolator_name]["controller"].replace(source_side, target_side)

    if not mc.objExists(target_driver):
        mc.warning("Don't exists target driver '{0}'".format(target_driver))
        return
    if not mc.objExists(target_controller):
        mc.warning("Don't exists target controller '{0}'".format(target_controller))
        return

    try:
        mc.undoInfo(openChunk=True, infinity=True)

        manager = initialize()

        # target interpolator
        mc.select(target_driver)
        mc.xform(target_controller, matrix=om.MMatrix(), worldSpace=False)
        interpolator = "|" + mc.poseInterpolator(name=target_interpolator_name)[0]
        interpolator = mc.parent(interpolator, manager)[0]
        interpolator = mc.listRelatives(interpolator, shapes=True, fullPath=True)[0]
        mc.setAttr(interpolator + ".interpolation", 1)

        # target interpolator in _data
        data[target_interpolator_name] = {}
        data[target_interpolator_name]["driver"] = target_driver
        data[target_interpolator_name]["controller"] = target_controller
        data[target_interpolator_name]["driven"] = []
        data[target_interpolator_name]["pose"] = {}

        for pose, v in data[source_interpolator_name]["pose"].items():
            # add pose
            data[target_interpolator_name]["pose"][pose] = {"driven": {}}

            # get inv target driver pose
            # rule is controller attribute
            inv_tx = -1 if mc.getAttr(data[source_interpolator_name]["controller"] + ".invTx") else 1
            inv_ty = -1 if mc.getAttr(data[source_interpolator_name]["controller"] + ".invTy") else 1
            inv_tz = -1 if mc.getAttr(data[source_interpolator_name]["controller"] + ".invTz") else 1
            inv_rx = -1 if mc.getAttr(data[source_interpolator_name]["controller"] + ".invRx") else 1
            inv_ry = -1 if mc.getAttr(data[source_interpolator_name]["controller"] + ".invRy") else 1
            inv_rz = -1 if mc.getAttr(data[source_interpolator_name]["controller"] + ".invRz") else 1

            source_t = data[source_interpolator_name]["pose"][pose]["t"]
            target_t = [source_t[0] * inv_tx, source_t[1] * inv_ty, source_t[2] * inv_tz]

            source_r = data[source_interpolator_name]["pose"][pose]["r"]
            target_r = [source_r[0] * inv_rx, source_r[1] * inv_ry, source_r[2] * inv_rz]

            mc.setAttr(target_controller + ".t", *target_t)
            mc.setAttr(target_controller + ".r", *target_r)
            index = mc.poseInterpolator(interpolator, edit=True, addPose=pose)
            mc.setAttr(interpolator + ".pose[{0}].poseType".format(index), 1)

            # add pose in _data
            data[target_interpolator_name]["pose"][pose]["t"] = target_t
            data[target_interpolator_name]["pose"][pose]["r"] = target_r
            for source_driven in v["driven"].keys():
                # add driven
                target_driven = source_driven.replace(source_side, target_side)
                if not mc.objExists(target_driven):
                    mc.warning("Don't exists target driven '{0}'".format(target_driven))
                    continue

                # add blendMatrix
                target_blend_m = target_driven + "_bm"
                if not mc.objExists(target_blend_m):
                    target_blend_m = mc.createNode("blendMatrix", name=target_blend_m)

                # get inv target driven pose
                # rule is controller attribute
                inv_tx = -1 if mc.getAttr(source_driven + ".invTx") else 1
                inv_ty = -1 if mc.getAttr(source_driven + ".invTy") else 1
                inv_tz = -1 if mc.getAttr(source_driven + ".invTz") else 1
                inv_rx = -1 if mc.getAttr(source_driven + ".invRx") else 1
                inv_ry = -1 if mc.getAttr(source_driven + ".invRy") else 1
                inv_rz = -1 if mc.getAttr(source_driven + ".invRz") else 1

                source_t = v["driven"][source_driven]["t"]
                target_t = [source_t[0] * inv_tx, source_t[1] * inv_ty, source_t[2] * inv_tz]

                source_r = v["driven"][source_driven]["r"]
                target_r = [source_r[0] * inv_rx, source_r[1] * inv_ry, source_r[2] * inv_rz]

                target_m = om.MTransformationMatrix()
                target_m.setTranslation(om.MVector(target_t), om.MSpace.kWorld)
                target_m.setRotation(om.MEulerRotation([math.radians(x) for x in target_r]))

                mc.setAttr(target_blend_m + ".target[{0}].targetMatrix".format(index),
                           target_m.asMatrix(),
                           type="matrix")
                mc.connectAttr(interpolator + ".output[{0}]".format(index),
                               target_blend_m + ".target[{0}].weight".format(index))

                # add driven in _data
                data[target_interpolator_name]["pose"][pose]["driven"][target_driven] = {}
                data[target_interpolator_name]["pose"][pose]["driven"][target_driven]["t"] = target_t
                data[target_interpolator_name]["pose"][pose]["driven"][target_driven]["r"] = target_r

                # add driven npo
                driven_npo = target_driven + "_pm"
                if not mc.objExists(driven_npo):
                    parent = mc.listRelatives(target_driven, parent=True)
                    driven_npo = mc.createNode("transform", name=driven_npo, parent=parent[0] if parent else None)
                    m = mc.xform(target_driven, query=True, matrix=True, worldSpace=True)
                    mc.xform(driven_npo, matrix=m, worldSpace=True)
                    mc.parent(target_driven, driven_npo)

                    decom_m = mc.createNode("decomposeMatrix")
                    mc.connectAttr(target_blend_m + ".outputMatrix", decom_m + ".inputMatrix")
                    mc.connectAttr(decom_m + ".outputTranslate", driven_npo + ".t")
                    mc.connectAttr(decom_m + ".outputRotate", driven_npo + ".r")

                # add blendMatrix in _data
                if target_blend_m not in data[target_interpolator_name]["driven"]:
                    data[target_interpolator_name]["driven"].append(target_blend_m)
        set_data(data)
    except Exception:
        traceback.print_exc()
        mc.warning("Occur error mirror_driver '{0}'. Returned to action".format(driver))
        mc.undoInfo(closeChunk=True)
        mc.undo()
    else:
        mc.undoInfo(closeChunk=True)


def go_to_pose(driver, pose):
    interpolator_name = driver + "_pmInterpolator"
    if not mc.objExists(interpolator_name):
        mc.warning("Don't exists '{0}' interpolator node '{1}'".format(driver, interpolator_name))
        return

    data = get_data()

    if pose not in data[interpolator_name]["pose"]:
        mc.warning("Don't exists pose '{0}' interpolator node '{1}'".format(pose, interpolator_name))
        return

    try:
        mc.undoInfo(openChunk=True, infinity=True)
        mc.setAttr(data[interpolator_name]["controller"] + ".t", *data[interpolator_name]["pose"][pose]["t"])
        mc.setAttr(data[interpolator_name]["controller"] + ".r", *data[interpolator_name]["pose"][pose]["r"])
    except Exception:
        traceback.print_exc()
        mc.undoInfo(closeChunk=True)
        mc.undo()
    else:
        mc.undoInfo(closeChunk=True)


def auto_adjust_gaussian_falloff():
    data = get_data()
    for interpolator in data.keys():
        for pose in data[interpolator]["pose"].keys():
            mel.eval('poseInterpolatorCalcKernelFalloff("{0}", "{1}")'.format(interpolator, pose))
