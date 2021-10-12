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
import json
import os
from tank_vendor import six

from syntheyes import get_existing_connection
from tracker_converter.utils import Shot
from tracker_converter.plugins import TDEFilePlugin
from tracker_converter.plugins import SynthEyesNativePlugin

HookBaseClass = sgtk.get_hook_baseclass()


class SyntheyesTrackerPublishPlugin(HookBaseClass):
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
        <p>This plugin publishes camera for the current session. Any
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
        base_settings = super(SyntheyesTrackerPublishPlugin, self).settings or {}

        # settings specific to this class
        syntheyes_tracker_publish_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                "correspond to a template defined in "
                "templates.yml.",
            },
            "Tracker": {
                "type": "list",
                "default": ['tra*'],
                "description": "Template path for published work files. Should"
                               "correspond to a template defined in "
                               "templates.yml.",
            }

        }

        # update the base settings
        base_settings.update(syntheyes_tracker_publish_settings)

        return base_settings

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """
        return ["syntheyes.session.tracker"]

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
        template_name = settings["Publish Template"].value


        # ensure a work file template is available on the parent item
        work_template = item.parent.properties.get("work_template")
        if not work_template:
            self.logger.debug(
                "A work template is required for the session item in order to "
                "publish session tracer. Not accepting session  item."
            )
            accepted = False

        # ensure the publish template is defined and valid and that we also have
        publish_template = publisher.get_template_by_name(template_name)
        if not publish_template:
            self.logger.debug(
                "The valid publish template could not be determined for the "
                "session tracker item. Not accepting the item."
            )
            accepted = False

        # we've validated the publish template. add it to the item properties
        # for use in subsequent methods
        item.properties["publish_template"] = publish_template


        # because a publish template is configured, disable context change. This
        # is a temporary measure until the publisher handles context switching
        # natively.
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

        hlev = item.properties["hlev"]
        cameras = [camera.Name() for camera in hlev.Cameras()]
        cam = hlev.FindObjByName(cameras[0])
        sht = cam.Get("shot")

        item.properties["shot"] = sht
        resolution = "{}x{}".format(int(sht.width), int(sht.height))
        item.properties['scene_resolution'] = resolution

        plate_aspect_ratio = item.properties["working_pixel_aspect_ratio"]
        scene_aspect_ratio = str(sht.pixasp)
        plate_resoluton = item.properties["resolution"]
        scene_resolution = resolution

        if scene_resolution != plate_resoluton:
            raise Exception("Scene not matched with plate resolution")

        # validating plate aspect ratio
        if plate_aspect_ratio != scene_aspect_ratio:
            raise Exception("Scene aspect_ratio was not matching with the plate")

        # get the normalized path
        path = sgtk.util.ShotgunPath.normalize(path)

        work_template = item.parent.properties.get("work_template")
        publish_template = item.properties.get("publish_template")


        # get the current scene path and extract fields from it using the work
        # template:
        work_fields = work_template.get_fields(path)
        work_fields.update(
            {
                "plate_name": item.properties.get("plate_name"),
                "publish_type": item.properties["publish_type"],
                "pass_type": resolution
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
        item.properties["publish_path"] = item.properties["path"]
        # use the work file's version number when publishing
        if "version" in work_fields:
            item.properties["publish_version"] = work_fields["version"]

        # run the base class validation
        return super(SyntheyesTrackerPublishPlugin, self).validate(settings, item)

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
        sht = item.properties["shot"]
        start = sht.start
        width = sht.width
        height = sht.height
        stop = sht.stop

        # offset = sht.frameFirstOffset

        txt_file_path = item.properties["publish_path"]
        item.properties["path"] = txt_file_path
        txt_folder_path = os.path.dirname(txt_file_path)
        aspect_ratio = item.properties["shot"].aspect
        point_type= "2D"



        # ensure the publish folder exists:

        self.parent.ensure_folder_exists(txt_folder_path)

        # export_2d_points.szl script have been migrate to to the below python function
        export_2d_points(item.properties["hlev"], txt_file_path, start, stop)

        # TODO: incorporate start frame/offset

        TDE_shot = Shot(width, height, 1)

        SE_shot = Shot(width, height, 0)

        exporting_plugin = SynthEyesNativePlugin.SynthEyesNativePlugin()
        importing_plugin = TDEFilePlugin.TrackingPlugin3DENative()

        trackers = exporting_plugin.trackers_to_internal(txt_file_path, SE_shot)
        importing_plugin.internal_to_trackers(trackers, txt_file_path, TDE_shot)
        metadata = {"resolution": item.properties["scene_resolution"], 'aspect_ratio': aspect_ratio, "point_type": point_type}
        metadata_file_path = os.path.join(os.path.dirname(txt_file_path), "metadata.json")
        with open(metadata_file_path, "w") as json_file:
            json.dump(metadata, json_file, indent=4, sort_keys=True)

        item.properties["publish_fields"] = {

                "upstream_published_files": [{"type": "PublishedFile", "id": item.properties["plate_id"]}]

            }

        # Now that the path has been generated, hand it off to the
        super(SyntheyesTrackerPublishPlugin, self).publish(settings, item)


def _session_path():
    """
    Return the path to the current session
    :return:
    """
    hlev = get_existing_connection()
    return hlev.SNIFileName()


def export_2d_points(hlev,se_out, start, stop):
    if os.path.exists(se_out):
        os.unlink(se_out)
    for tracker in hlev.Trackers():
        if tracker.isExported:
            for frame in range(int(start), int(stop)+1):
                hlev.SetSzlFrame(frame)
                if tracker.valid:
                    with open(se_out, 'a') as track_data:
                        track_data.write('{} {} {} {}\n'.format(tracker.nm, frame, round(tracker.u,6), round(tracker.v, 6)))

    return se_out


def _get_save_as_action():
    """
    Simple helper for returning a log action dict for saving the session
    """

    engine = sgtk.platform.current_engine()

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
