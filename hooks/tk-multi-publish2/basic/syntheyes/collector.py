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
import sgtk
import json
from syntheyes import get_existing_connection

HookBaseClass = sgtk.get_hook_baseclass()


class SyntheyesSessionCollector(HookBaseClass):
    """
    Collector that operates on the current Syntheyes session. Should
    inherit from the basic collector hook.
    """

    @property
    def settings(self):

        """
        Dictionary defining the settings that this collector expects to receive
        through the settings parameter in the process_current_session and
        process_file methods.

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

        # grab any base class settings
        collector_settings = super(SyntheyesSessionCollector, self).settings or {}

        # settings specific to this collector
        syntheyes_session_settings = {
            "Work Template": {
                "type": "template",
                "default": None,
                "description": "Template path for artist work files. Should "
                "correspond to a template defined in "
                "templates.yml. If configured, is made available"
                "to publish plugins via the collected item's "
                "properties. ",
            },
        }

        # update the base settings with these settings
        collector_settings.update(syntheyes_session_settings)

        return collector_settings

    def process_current_session(self, settings, parent_item):
        """
        Analyzes the current session open in syntheyes and parents a
        subtree of items under the parent_item passed in.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance
        """

        publisher = self.parent
        self.engine = publisher.engine

        project_item = self.collect_current_syntheyes_session(settings, parent_item)

        self.collect_sg_scene(project_item)
        self.collect_track_points(project_item)
        self.collect_distortion(project_item)
        self.collect_screen_capture(project_item)


    def collect_current_syntheyes_session(self, settings, parent_item):

        """
        Analyzes the current session open in Syntheyes and parents a subtree of items
        under the parent_item passed in.

        :param dict settings: Configured settings for this collector
        :param parent_item: Root item instance
        """

        publisher = self.parent

        # get the current path
        path = _session_path()

        # determine the display name for the item
        if path:
            file_info = publisher.util.get_file_path_components(path)
            display_name = file_info["filename"]
        else:
            display_name = "Current Syntheyes Session"

        # create the session item for the publish hierarchy
        session_item = parent_item.create_item(
            "syntheyes.session", "Syntheyes Scene", display_name
        )

        # get the icon path to display for this item
        icon_path = os.path.join(self.disk_location, os.pardir, "icons", "Syntheyes.png")
        session_item.set_icon_from_path(icon_path)

        # if a work template is defined, add it to the item properties so
        # that it can be used by attached publish plugins
        work_template_setting = settings.get("Work Template")

        if work_template_setting:
            work_template = publisher.engine.get_template_by_name(
                work_template_setting.value
            )

            # store the template on the item for use by publish plugins. we
            # can't evaluate the fields here because there's no guarantee the
            # current session path won't change once the item has been created.
            # the attached publish plugins will need to resolve the fields at
            # execution time.
            session_item.properties["work_template"] = work_template

            self.logger.info("Work template defined for Syntheyes collection.")

        self.logger.info("Collected current Syntheyes scene")
        return session_item


    def collect_distortion(self, parent_item):
        """
        Scan known output node types in the session and see if they reference
        files that have been written to disk.

        :param parent_item: The parent item for any nodes collected
        """

        icon_path = os.path.join(self.disk_location, os.pardir, "icons", "lens.png")
        hlev = get_existing_connection()
        cameras = [camera.Name() for camera in hlev.Cameras()]
        cam = hlev.FindObjByName(cameras[0])
        distortion = cam.distortion

        item_info = super(SyntheyesSessionCollector, self)._get_item_info(str(distortion))

        # file exists, let the basic collector handle it
        item = parent_item.create_item("syntheyes.session.distortion", "Distortion","lens distortion")
        item.set_icon_from_path(icon_path)

        sht = cam.Get("shot")
        start_frame = sht.start
        end_frame = sht.stop+1

        item.properties["plate_name"], item.properties["resolution"], item.properties["working_pixel_aspect_ratio"],item.properties["plate_id"]= self.get_plate_info(item)
        item.properties["hlev"] = hlev
        item.properties["start_frame"]= start_frame
        item.properties["end_frame"]= end_frame
        item.properties["publish_type"] = "Lens"
        item.properties["shot"] = sht
        item.properties["cam"] = cam
        item.properties["item_info"]= item_info

        try:
            default_distortion_metadata = {
                "quadratic_distortion": 0.00000,
                "cubic_distortion":0.00000,
                "quartic_distortion": 0.00000,
                "lens_center": [0.0000, 0.0000],
                "distortion eccentricity": 1.0000,
                "anamorphic_squash_slope": 1.0000,
                "squash_reference_fov": 60.00,
                "rolling_shutter": 0.0000

            }

            scene_distortion_metadata =  {
                "quadratic_distortion": cam.distortion,
                "cubic_distortion": cam.cubic,
                "quartic_distortion": cam.quartic,
                "lens_center": cam.lensCenter,
                "distortion eccentricity": cam.eccentricity,
                "anamorphic_squash_slope": cam.zoomSquashSlope,
                "squash_reference_fov": cam.zoomSquashFOV,
                "rolling_shutter": cam.solvedRolling

            }
            Lens_mode = {0.0: "known", 1.0: "fixed, unknown", 2.0: "zooming", 3.0: "fixed, estimate"}


            misc_metadata = {
                "camera_mode": cam.mode,
                "world_size":  cam.worldSize,
                "lens_mode": Lens_mode[cam.lensMode],
                "field_of_view":cam.solveFOV,
                "focal_length": cam.fl,
                "error": "{} hpix".format(cam.rmserr)
            }

            updated_meta_data = {}
            for key, val in scene_distortion_metadata.items():
                round_value = round(val, 3) if isinstance(val, float) else val
                if default_distortion_metadata[key] != val:
                    updated_meta_data.update({key:round_value})
            updated_meta_data.update(misc_metadata)
            item.properties['metadata'] = json.dumps(updated_meta_data,indent= 4, sort_keys=True)


        except:
            import traceback
            self.logger.debug(traceback.format_exc())
            self.logger.warning("Failure!")



        # the item has been created. update the display name to include

        item.context_change_allowed = False
        item.name = "%s distortion value" % (str(distortion))
        self.logger.info("Collected lens distortion " )

    def collect_track_points(self, parent_item):
        """
        :param parent_item: The parent item for any nodes collected
        """

        publisher = self.parent

        icon_path = os.path.join(self.disk_location, os.pardir, "icons", "track.png")
        hlev = get_existing_connection()
        for count, tracker in enumerate(hlev.Trackers()):
            tracker_name = tracker.Name()
        item_info = super(SyntheyesSessionCollector, self)._get_item_info(str(count))

        # file exists, let the basic collector handle it
        item = parent_item.create_item("syntheyes.session.tracker", "Tracker", str(count+1))
        item.set_icon_from_path(icon_path)


        item.properties["hlev"] = hlev
        item.context_change_allowed = False
        item.name = "%s trackers collected" % (item.name)
        item.properties["plate_name"], item.properties["resolution"], item.properties["working_pixel_aspect_ratio"],item.properties["plate_id"]= self.get_plate_info(item)
        item.properties["publish_type"] = "Points"


    def collect_sg_scene(self, parent_item):
        """
        Collect cameras in the session.

        :param parent_item:  The parent item for any sg cameras collected
        """

        publisher = self.parent

        icon_path = os.path.join(self.disk_location, os.pardir, "icons", "camera.png")

        hlev = get_existing_connection()

        for camera in hlev.Cameras():
            camera_name = "Shot_{}".format(camera.Name())



            item_info = super(SyntheyesSessionCollector, self)._get_item_info(camera_name)

            # create and populate the item

            item = parent_item.create_item("syntheyes.session.scene", "Scene", camera_name)
            item.set_icon_from_path(icon_path)

            #all we know about the file is its path. set the path in its
            #properties for the plugins to use for processing.

            # store publish info on the item so that the base publish plugin
            # doesn't fall back to zero config path parsing

            item.properties["plate_name"], item.properties["resolution"], item.properties["working_pixel_aspect_ratio"],item.properties["plate_id"]= self.get_plate_info(item)
            item.properties["publish_type"] = "Camera"
            item.properties["camera_name"] = camera_name
            item.properties["hlev"] = hlev

            item.context_change_allowed = False
            self.logger.info("Collected scene: %s" % (camera_name,))


    def collect_screen_capture(self, parent_item):
        """
        Collect geometry in the session.

        :param parent_item:  The parent item for any sg geometry collected
        """

        publisher = self.parent
        engine = publisher.engine
        icon_path = os.path.join(self.disk_location, os.pardir, "icons", "screenrecord.png")

        hlev = get_existing_connection()
        item = parent_item.create_item("syntheyes.session.screen_grab", "screen 1", "Screen Capture")
        item.set_icon_from_path(icon_path)
        item.properties["plate_name"], item.properties["resolution"], item.properties["working_pixel_aspect_ratio"], item.properties["plate_id"]= self.get_plate_info(item)
        item.properties["publish_type"] = "Screeencapture"
        item.properties["hlev"] = hlev

        item.context_change_allowed = False
        self.logger.info("Collected screen capture")


    def get_plate_info(self, item):

        path = sgtk.util.ShotgunPath.normalize(_session_path())

        # get the configured work file template
        work_template = item.parent.properties.get("work_template")

        # get the current scene path and extract fields from it using the work
        # template:
        work_fields = work_template.get_fields(path)

        shot = work_fields["Shot"]


        available_records = self.engine.shotgun.find_one(
            'PublishedFile',
            [
                ['entity', 'name_is', shot],
                ['published_file_type', 'name_is', 'Image'],
                ['sg_pass_type', 'is', 'Main']

            ],
            ['sg_metadata'],

        )

        working_pixel_aspect_ratio = self.engine.shotgun.find_one(
            'Shot',
            [
                ['code', 'is', shot],
            ],
            ['sg_pixel_aspect_ratio'],

        )["sg_pixel_aspect_ratio"]



        sg_data = json.loads(available_records.get('sg_metadata'))
        if sg_data:
            id  = available_records["id"]
            res = str(sg_data['res'])
            name = str(sg_data['name'])

        # utils = sgtk.platform.import_framework("tvfx-maya-utils", "plate_utils")
        # main_shot_plates = utils.get_plates_from_shot(shot_id, pass_type='Main')
        # self.logger.info(main_shot_plates)
        # return main_shot_plates

        return name, res, working_pixel_aspect_ratio, id




def _session_path():
    """
    Return the path to the current session
    :return:
    """

    hlev =  get_existing_connection()
    return hlev.SNIFileName()


