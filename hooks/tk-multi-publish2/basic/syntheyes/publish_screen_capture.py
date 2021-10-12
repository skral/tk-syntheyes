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



import screen_grab
from syntheyes import get_existing_connection
HookBaseClass = sgtk.get_hook_baseclass()


class SyntheyesScreenCapturePublishPlugin(HookBaseClass):
    """
    plugin for capture the syntheyes scene capture and sending that .mov file
    to shotgrid for review

    """

    # NOTE: The plugin icon and name are defined by the base file plugin.

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does. This can
        contain simple html for formatting.
        """
        publisher = self.parent

        shotgun_url = publisher.sgtk.shotgun_url

        media_page_url = "%s/page/media_center" % (shotgun_url,)
        review_url = "https://www.shotgunsoftware.com/features/#review"

        return """
        capture the syntheyes session in .avi format and Upload the file to ShotGrid for review.<br><br>

        A <b>Version</b> entry will be created in ShotGrid and a transcoded
        copy of the file will be attached to it. The file can then be reviewed
        via the project's <a href='%s'>Media</a> page, <a href='%s'>RV</a>, or
        the <a href='%s'>ShotGrid Review</a> mobile app.
        """ % (
            media_page_url,
            review_url,
            review_url,
        )


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
        base_settings = super(SyntheyesScreenCapturePublishPlugin, self).settings or {}

        # settings specific to this class
        syntheyes_screen_publish_settings = {
            "Publish Template": {
                "type": "template",
                "default": None,
                "description": "Template path for published work files. Should"
                "correspond to a template defined in "
                "templates.yml.",
            },

            "File Extensions": {
                "type": "str",
                "default": "jpeg, jpg, png, mov, mp4, pdf",
                "description": "File Extensions of files to include",
            },
            "Upload": {
                "type": "bool",
                "default": True,
                "description": "Upload content to ShotGrid?",
            },
            "Link Local File": {
                "type": "bool",
                "default": True,
                "description": "Should the local file be referenced by ShotGrid",
            },

        }

        # update the base settings
        base_settings.update(syntheyes_screen_publish_settings)

        return base_settings

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["maya.*", "file.maya"]
        """

        return ["syntheyes.session.screen_grab"]

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
                "publish session capture."
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


        if not path:
            # the session still requires saving. provide a save button.
            # validation fails.
            error_msg = "The syntheyes session has not been saved."
            self.logger.error(error_msg)
            raise Exception(error_msg)

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
                "pass_type": item.properties["publish_type"],
                "publish_type": item.properties["publish_type"]
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

        
        self.logger.info(item.properties["publish_path"])
        # use the work file's version number when publishing
        if "version" in work_fields:
            item.properties["publish_version"] = work_fields["version"]


        # run the base class validation

        return super(SyntheyesScreenCapturePublishPlugin, self).validate(settings, item)

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
        publish_name = item.properties.get("publish_name")
        publish_path = item.properties["publish_path"]
        hlev = item.properties["hlev"]
        if not publish_name:
            self.logger.debug("Using path info hook to determine publish name.")

            # use the path's filename as the publish name
            path_components = publisher.util.get_file_path_components(path)
            publish_name = path_components["filename"]



        self.logger.debug("Publish name: %s" % (publish_name,))

        self.logger.info("Creating Version...")

        version_data = {
            "project": item.context.project,
            "code": publish_name,
            "description": item.description,
            "entity": self._get_version_entity(item),
            "sg_task": item.context.task,
        }

        # get the path to create and publish
        self.parent.ensure_folder_exists(os.path.dirname(publish_path))

        result = screen_grab.play_back(publish_path,hlev)
        self.logger.info("result")
        self.logger.info(result)
        if result:
            version = publisher.shotgun.create("Version", version_data)
            self.logger.info("Version created!")

            # stash the version info in the item just in case
            item.properties["sg_version_data"] = version

            thumb = item.get_thumbnail_as_path()

            if settings["Upload"].value:
                self.logger.info("Uploading content...")

                # on windows, ensure the path is utf-8 encoded to avoid issues with
                # the shotgun api
                if sgtk.util.is_windows():
                    upload_path = six.ensure_text(path)
                else:
                    upload_path = path

                self.parent.shotgun.upload(
                    "Version", version["id"], upload_path, "sg_uploaded_movie"
                )
            elif thumb:
                # only upload thumb if we are not uploading the content. with
                # uploaded content, the thumb is automatically extracted.
                self.logger.info("Uploading thumbnail...")
                self.parent.shotgun.upload_thumbnail("Version", version["id"], thumb)

            self.logger.info("Upload complete!")

        else:
            hlev.Stop()

        self.logger.info("Registering publish...")
        item.properties["publish_fields"] = {
                "upstream_published_files": [{"type": "PublishedFile", "id": item.properties["plate_id"]}]

            }

        # Now that the path has been generated, hand it off to the
        super(SyntheyesScreenCapturePublishPlugin, self).publish(settings, item)

    def _get_version_entity(self, item):
        """
        Returns the best entity to link the version to.
        """

        if item.context.entity:
            return item.context.entity
        elif item.context.project:
            return item.context.project
        else:
            return None





def _session_path():
    """
    Return the path to the current session
    :return:
    """
    hlev = get_existing_connection()
    return hlev.SNIFileName()



