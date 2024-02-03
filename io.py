# built-ins
import json
import traceback

# maya
from maya import cmds as mc

# pose manager
from . import api


def load(file_path):
    """
    generate PSD from data

    loop data
        create interpolator
        loop driven
            create blendMatrix
            create driven npo
            connect blendMatrix -> driven npo
        loop pose
            add pose

    :param file_path:
    :return:
    """
    with open(file_path, "r", encoding="UTF-8") as f:
        data = json.load(f)

    mc.undoInfo(openChunk=True, infinity=True)
    try:
        for interpolator_name in data.keys():
            # add driver
            driver = interpolator_name.replace("_poseInterpolator", "")
            controller = data[interpolator_name]["controller"]
            api.add_driver(driver, controller)

            for blend_m in data[interpolator_name]["driven"]:
                # add driven
                driven = blend_m.replace("_bm", "")

                api.add_driven(driver, driven)

            for pose in data[interpolator_name]["pose"]:
                # add pose
                mc.setAttr(controller + ".t", *data[interpolator_name]["pose"][pose]["t"])
                mc.setAttr(controller + ".r", *data[interpolator_name]["pose"][pose]["r"])
                api.add_pose(driver, pose)

                for driven, v in data[interpolator_name]["pose"][pose]["driven"].items():
                    # edit driven
                    mc.setAttr(driven + ".t", *v["t"])
                    mc.setAttr(driven + ".r", *v["r"])
                    api.update_driven(driver, pose, driven)

            mc.setAttr(controller + ".t", 0, 0, 0)
            mc.setAttr(controller + ".r", 0, 0, 0)
    except Exception:
        traceback.print_exc()
        mc.undoInfo(closeChunk=True)
        mc.undo()
    else:
        mc.undoInfo(closeChunk=True)
    return data


def dump(file_path, data):
    with open(file_path, "w", encoding="UTF-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return file_path
