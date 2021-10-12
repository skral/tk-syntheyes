# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.


import sgtk
import os
from tank_vendor import six

from syntheyes import get_existing_connection
HookBaseClass = sgtk.get_hook_baseclass()


class SyntheyesCameraPublishPlugin(HookBaseClass):
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
        <p>This plugin publishes shot for the current session. Any
        camera will be exported to the path defined by this plugin's
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
        base_settings = super(SyntheyesCameraPublishPlugin, self).settings or {}

        # settings specific to this class
        syntheyes_camera_publish_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                "correspond to a template defined in "
                "templates.yml.",
            },
            "Camera": {
                "type": "list",
                "default": ['cam*'],
                "description": "Template path for published work files. Should"
                               "correspond to a template defined in "
                               "templates.yml.",
            }

        }

        # update the base settings
        base_settings.update(syntheyes_camera_publish_settings)

        return base_settings

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """
        return ["syntheyes.session.scene"]

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
        template_name = "syntheyes_shot_scene_publish_fbx"

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
        # item.properties["publish_fbx_template"] = publish_template
        item.local_properties.publish_template = publish_template
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
        publish_template = item.local_properties.get("publish_template")

        # get the current scene path and extract fields from it using the work
        # template:
        work_fields = work_template.get_fields(path)
        work_fields.update(
            {
                "plate_name":item.properties.get("plate_name"),
                "publish_type": item.properties["publish_type"],
                "pass_type":item.properties['camera_name']
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

        item.local_properties["path"] = publish_template.apply_fields(work_fields)
        item.properties["path"] = item.local_properties["path"]
        item.local_properties["publish_path"] = item.local_properties["path"]


        # use the work file's version number when publishing
        if "version" in work_fields:
            item.properties["publish_version"] = work_fields["version"]


        item.local_properties.publish_type = "FBX File"
        # run the base class validation
        return super(SyntheyesCameraPublishPlugin, self).validate(settings, item)

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """

        publisher = self.parent

        # get the path to create and publish
        fbx_publish_path = item.local_properties["publish_path"]


        # ensure the publish folder exists:
        self.parent.ensure_folder_exists(os.path.dirname(fbx_publish_path))


        hlev = item.properties["hlev"]

        #exporting the fbx data
        hlev.Export("Filmbox FBX", fbx_publish_path)

        path = item.local_properties["path"]
        item.local_properties["publish_name"] = publisher.util.get_publish_name(path)
        item.properties["version_number"] = publisher.util.get_version_number(path) or 1
        item.properties["publish_fields"] = {
                "upstream_published_files": [{"type": "PublishedFile", "id": item.properties["plate_id"]}]

            }

        self.logger.info("Registering publish...")

        # Now that the path has been generated, hand it off to the
        super(SyntheyesCameraPublishPlugin, self).publish(settings, item)




def _session_path():
    """
    Return the path to the current session
    :return:
    """
    hlev = get_existing_connection()
    return hlev.SNIFileName()


def get_scene_resolution(hlev):
    cameras = [camera.Name() for camera in hlev.Cameras()]
    cam = hlev.FindObjByName(cameras[0])
    sht = cam.Get("shot")
    resolution = "{}x{}".format(int(sht.width), int(sht.height))
    aspect_ratio = str(sht.pixasp)

    return resolution, aspect_ratio

