# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import sys
import sgtk
import json
from pprint import pprint

from tank_vendor import six

from syntheyes import get_existing_connection

HookBaseClass = sgtk.get_hook_baseclass()


class SyntheyesDistortionPublishPlugin(HookBaseClass):
    """
    Plugin for publishing an open camera, session.

    This hook relies on functionality found in the base file publisher hook in
    the publish2 app and should inherit from it in the configuration. The hook
    setting for this plugin should look something like this::

        hook: "{self}/publish_file.py:{engine}/tk-multi-publish2/basic/publish_session.py"

    """

    # NOTE: The plugin icon and name are defined by the base file plugin.


    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does. This can
        contain simple html for formatting.
        """

        return """
        <p>This plugin publishes lens for the current session. Any
        camerawill be exported to the path defined by this plugin's
        configured "Publish Template" setting. The plugin will fail to validate
        
        """

    @property
    def settings(self):

        """
        Dictionary defining the settings that this plugin expects to receive
        through the settings parameter in the accept, validate, publish and
        finalize methods.

        A dictionary on the following form::

            {
                "Settings Name": {
                    "type": "settings_type",
                    "default": "default_value",
                    "description": "One line description of the setting"
            }

        The type string should be one of the data types that toolkit accepts as
        part of its environment configuration.
        """
        # inherit the settings from the base publish plugin
        base_settings = super(SyntheyesDistortionPublishPlugin, self).settings or {}

        # settings specific to this class
        syntheyes_distortion_publish_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                "correspond to a template defined in "
                "templates.yml.",
            },
            "Publish Type": {
                "type": "string",
                "default": "exr format",
                "description": "Template path for published work files. Should"
                               "correspond to a template defined in "
                               "templates.yml.",
            }


        }

        # update the base settings
        base_settings.update(syntheyes_distortion_publish_settings)

        return base_settings

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """
        return ["syntheyes.session.distortion"]

    def accept(self, settings, item):

        """
        Method called by the publisher to determine if an item is of any
        interest to this plugin. Only items matching the filters defined via the
        item_filters property will be presented to this method.

        A publish task will be generated for each item accepted here. Returns a
        dictionary with the following booleans:

            - accepted: Indicates if the plugin is interested in this value at
                all. Required.
            - enabled: If True, the plugin will be enabled in the UI, otherwise
                it will be disabled. Optional, True by default.
            - visible: If True, the plugin will be visible in the UI, otherwise
                it will be hidden. Optional, True by default.
            - checked: If True, the plugin will be checked in the UI, otherwise
                it will be unchecked. Optional, True by default.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process

        :returns: dictionary with boolean keys accepted, required and enabled
        """

        accepted = True
        publisher = self.parent
        self.engine = publisher.engine
        template_name = settings["Publish Template"].value


        # ensure a work file template is available on the parent item
        work_template = item.parent.properties.get("work_template")
        if not work_template:
            self.logger.debug(
                "A work template is required for the session item in order to "
                "publish session geometry. Not accepting session geom item."
            )
            accepted = False

        # ensure the publish template is defined and valid and that we also have
        publish_template = publisher.get_template_by_name(template_name)

        if not publish_template:
            self.logger.debug(
                "The valid publish template could not be determined for the "
                "session geometry item. Not accepting the item."
            )
            accepted = False

        # we've validated the publish template. add it to the item properties
        # for use in subsequent methods
        item.properties["publish_template"] = publish_template
        item.context_change_allowed = False

        return {"accepted": accepted, "checked": True}

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish. Returns a
        boolean to indicate validity.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: True if item is valid, False otherwise.
        """

        path = _session_path()

        # ---- ensure the session has been saved
        if not path:
            # the session still requires saving. provide a save button.
            # validation fails.
            error_msg = "The Syntheyes session has not been saved."
            self.logger.error(error_msg, extra=_get_save_as_action())
            raise Exception(error_msg)

        plate_aspect_ratio = item.properties["working_pixel_aspect_ratio"]
        plate_resolution = item.properties["resolution"]
        scene_resolution, scene_aspect_ratio = get_scene_resolution(item.properties["hlev"])

        # validating plate resolution
        if plate_resolution != scene_resolution:
            raise Exception("Scene resolution was not matching with the plate")

        # validating plate aspect ratio
        if plate_aspect_ratio != scene_aspect_ratio:
            raise Exception("Scene aspect_ratio was not matching with the plate")

        # get the normalized path
        path = sgtk.util.ShotgunPath.normalize(path)


        # get the configured work file template
        work_template = item.parent.properties.get("work_template")
        publish_template = item.properties.get("publish_template")

        # get the current scene path and extract fields from it using the work
        # template:
        work_fields = work_template.get_fields(path)

        work_fields.update(
            {
                "plate_name": item.properties.get("plate_name"),
                "publish_type": item.properties.get("publish_type")
            }
        )


        # ensure the fields work for the publish template
        missing_keys = publish_template.missing_keys(work_fields)
        if missing_keys:
            error_msg = (
                "Work file '%s' missing keys required for the "
                "publish template: %s" % (path, missing_keys)
            )
            self.logger.error(error_msg)
            raise Exception(error_msg)

        # create the publish path by applying the fields. store it in the item's
        # properties. This is the path we'll create and then publish in the base
        # publish plugin. Also set the publish_path to be explicit.

        item.properties["path"] = publish_template.apply_fields(work_fields)
        item.properties["publish_type"] = "Lens"
        item.properties["publish_path"] = item.properties["path"]

        # use the work file's version number when publishing
        if "version" in work_fields:
            item.properties["publish_version"] = work_fields["version"]

        # run the base class validation
        return super(SyntheyesDistortionPublishPlugin, self).validate(settings, item)

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """

        publisher = self.parent
        path = item.properties["path"]

        # extract the version number for publishing. use 1 if no version in path
        version_number = publisher.util.get_version_number(path) or 1

        hlev = item.properties["hlev"]
        sht = item.properties["shot"]
        cam = item.properties["cam"]

        # get the path to create and publish
        rd_publish_path = item.properties["publish_path"].replace("task", "rd")
        rd_publish_folder = os.path.dirname(rd_publish_path)

        ud_publish_path = item.properties["publish_path"].replace("task", "ud")
        ud_publish_folder = os.path.dirname(ud_publish_path)

        self.parent.ensure_folder_exists(rd_publish_folder)
        self.parent.ensure_folder_exists(ud_publish_folder)

        distortion =[]
        field_of_view = {}
        focal_length = {}

        type_of_distortion = "animated" if len(set(distortion)) > 1 else "static"

        if type_of_distortion == "animated":
            for frame in range(int(item.properties["start_frame"]), int(item.properties["end_frame"])):
                hlev.SetSzlFrame(frame)
                rd_filepath = rd_publish_path.replace("frame",str(frame).zfill(4))
                ud_filepath = ud_publish_path.replace("frame",str(frame).zfill(4))
                sht.Call("WriteRedistortImage", rd_filepath)
                sht.Call("WriteUndistortImage", ud_filepath)
                field_of_view.update({frame: cam.solveFOV})
                focal_length.update({frame:  cam.fl})


            # expotting metadadta to json file
            metadata = {"type_of_distortion": type_of_distortion, "field_of_view": field_of_view, "focal_length":focal_length}
            metadata_file_path = os.path.join(os.path.dirname(os.path.dirname(ud_publish_path)), "metadata.json")
            with open(metadata_file_path, "w") as json_file:
                json.dump(metadata, json_file, indent=4, sort_keys=True)

        else:
            rd_publish_path = rd_publish_path.replace("frame", "%04d")
            ud_publish_path = rd_publish_path.replace("frame", "%04d")
            #excecuting the write re& un distortion iage
            sht.Call("WriteRedistortImage", rd_publish_path)
            sht.Call("WriteUndistortImage", ud_publish_path)

        # get the publish name for this file path. this will ensure we get a
        # consistent name across version publishes of this file.
        item.properties["publish_name"] = publisher.util.get_publish_name(rd_publish_path)
        item.properties['version_number'] = version_number


        self.logger.info("Registering publish...")
        item.properties["publish_fields"] = {

                "sg_metadata": item.properties['metadata'],
                "upstream_published_files": [{"type": "PublishedFile", "id": item.properties["plate_id"]}]

            }

        item.properties["publish_path"]= item.properties["path"] = rd_publish_path
        super(SyntheyesDistortionPublishPlugin, self).publish(settings, item)


def get_scene_resolution(hlev):
    cameras = [camera.Name() for camera in hlev.Cameras()]
    cam = hlev.FindObjByName(cameras[0])
    sht = cam.Get("shot")
    resolution = "{}x{}".format(int(sht.width), int(sht.height))
    aspect_ratio = str(sht.pixasp)
    return resolution, aspect_ratio



def _session_path():
    """
    Return the path to the current session
    :return:
    """
    hlev = get_existing_connection()
    return hlev.SNIFileName()



def _get_save_as_action():
    """
    Simple helper for returning a log action dict for saving the session
    """

    engine = sgtk.platform.current_engine()

    # default save callback



    # if workfiles2 is configured, use that for file save
    if "tk-multi-workfiles2" in engine.apps:
        app = engine.apps["tk-multi-workfiles2"]
        if hasattr(app, "show_file_save_dlg"):
            callback = app.show_file_save_dlg

    return {
        "action_button": {
            "label": "Save As...",
            "tooltip": "Save the current session",
            "callback": callback,
        }
    }
