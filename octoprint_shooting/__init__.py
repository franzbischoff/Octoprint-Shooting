# @todo: Read gcode from file
# @todo: Parse custom commands from gcode file
# @todo: Start-Stop MPU readings
# @todo: Store readings on file
# @todo: Plot readings on Octoprint Tab

# coding=utf-8
from __future__ import absolute_import

# import sys
# import glob
# import os
# from datetime import datetime
# from datetime import timedelta
# import octoprint.util
# import requests
# import inspect
# import threading
# import json
import io
import time

import octoprint.plugin
from lib.mpu6050 import mpu6050
from octoprint.events import Events
from octoprint.server.util import flask


# from octoprint.events import eventManager, Events
# from octoprint.util import RepeatedTimer
# from subprocess import Popen, PIPE
# import RPi.GPIO as GPIO
# import flask


class ShootingPlugin(octoprint.plugin.SettingsPlugin,
                     octoprint.plugin.AssetPlugin,
                     octoprint.plugin.TemplatePlugin,
                     octoprint.plugin.StartupPlugin,
                     octoprint.plugin.BlueprintPlugin,
                     octoprint.plugin.EventHandlerPlugin):
    capturing_vibration = False
    script_file = "vibration_test_1"
    mpu = None

    # ~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            # put your plugin's default settings here
            script_file="vibration_test_1"
        )

    def get_settings_version(self):
        return 1

    # def on_settings_migrate(self, target, current):
    #     assert target == get_settings_version()

    # ~~ AssetPlugin mixin

    def get_assets(self):
        return dict(
            js=["js/shooting.js", "js/plotly-latest.min.js"],
            css=["css/shooting.css"],
            less=["less/shooting.less"]
        )

    # ~~ TemplatePlugin mixin

    def get_template_configs(self):
        return [
            dict(type="navbar", custom_bindings=True),
            dict(type="tab", name="Shooting", custom_bindings=True),
            dict(type="settings", name="Shooting", custom_bindings=False)
        ]

    # ~~ StartupPlugin mixin

    def on_after_startup(self):
        self._logger.info("Shooting is here!")

    # ~~ BlueprintPlugin mixin

    @octoprint.plugin.BlueprintPlugin.route("/echo", methods=["GET"])
    def myEcho(self):
        if "text" not in flask.request.values:
            return flask.make_response("Expected a text to echo back.", 400)
        return flask.request.values["text"]

    # ~~ EventHandlerPlugin mixin

    def on_event(self, event, payload):
        if event == Events.CONNECTED:
            self.update_ui()

    # ~~ octoprint hooks

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
        # for details.
        return dict(
            shooting=dict(
                displayName="Shooting Plugin",
                displayVersion=self._plugin_version,

                # version check: github repository
                type="github_release",
                user="franzbischoff",
                repo="OctoPrint-Shooting",
                current=self._plugin_version,

                # update method: pip
                pip="https://github.com/franzbischoff/OctoPrint-Shooting/archive/{target_version}.zip"
            )
        )

    def atcommand_handler_hook(self, comm, phase, command, parameters, tags=None, *args, **kwargs):

        command = command.upper()
        parameters = parameters.upper()

        self._logger.info("Command received {command}.".format(command=command))

        if command == "START":
            self.start_gcode(self.script_file + ".gcode")
            return

        if command != "MPU6050":
            return

        if parameters is None:
            parameters = set()

        if "START" in parameters:
            self.start_capture_vibration()
            self._logger.info("Parameter \"{}\" received.".format(parameters))  # todo: implement start mpu6050 method

        if "STOP" in parameters:
            self.stop_capture_vibration()
            self._logger.info("Parameter \"{}\" received.".format(parameters))  # todo: implement stop mpu6050 method

        if tags is None:
            tags = set()

    def printer_message_received_hook(self, comm, line, *args, **kwargs):
        if "FIRMWARE_NAME" not in line:
            return line

        from octoprint.util.comm import parse_firmware_line

        # Create a dict with all the keys/values returned by the M115 request
        printer_data = parse_firmware_line(line)

        self._logger.info("Firmware Name detected: {machine}.".format(machine=printer_data["FIRMWARE_NAME"]))

        return line

    def printer_error_hook(self, comm, error_message, *args, **kwargs):
        _HANDLED_ERRORS = ('fan error', 'bed missing')

        lower_error = error_message.lower()
        if any(map(lambda x: x in lower_error, _HANDLED_ERRORS)):
            self._logger.info("Error \"{}\" is handled by this plugin".format(error_message))
            return True

        # ~~ octoprint.comm.protocol.atcommand.<phase> hook; @ commands (https://goo.gl/wXmgvt)
        # ~~ octoprint.comm.protocol.gcode.<phase> hook; read from file and sent gcode do printer (https://goo.gl/at8fEo)
        # ~~ octoprint.comm.protocol.gcode.received hook; read responses from printer (https://goo.gl/hTFcHY)
        # ~~ octoprint.comm.protocol.gcode.error hook; read error messages from printer (https://goo.gl/49XcDd)

    # ~~ Shooting functions

    def start_gcode(self, filename):

        # @todo: if printer is idle and ready

        # @todo: check if @commands are sync with movement
        path = self._basefolder + "/scripts/" + filename
        self._logger.info("Franz: print file base: \"{}\".".format(path))

        file = io.open(path, 'rt', encoding='utf8')

        for line in file:
            self._printer.commands(line.strip().upper())
            self._logger.info("Sending GCODE command: %s", line.strip().upper())
            time.sleep(0.2)

        file.close()

    def start_capture_vibration(self):
        if self.mpu:
            self._logger.info("Previous instance of MPU6050 exists")
            self.mpu.stop()
            time.sleep(0.1)

        self.mpu = mpu6050(0x68, logger=self._logger, basefolder=self.get_plugin_data_folder())
        self.mpu.start()

    def stop_capture_vibration(self):
        if self.mpu:
            self._logger.info("Stopping instance of MPU6050")
            self.mpu.stop()

        time.sleep(0.2)
        self._logger.info("Deleting MPU6050")
        del self.mpu

    def update_ui(self):
        self.update_ui_current_temperature()

    def update_ui_current_temperature(self):
        self._plugin_manager.send_plugin_message(self._identifier, dict(sensor_data=self.temperature_sensor_data))


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Shooting Plugin"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = ShootingPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
        "octoprint.comm.protocol.atcommand.sending": __plugin_implementation__.atcommand_handler_hook,
        "octoprint.comm.protocol.gcode.received": __plugin_implementation__.printer_message_received_hook,
        "octoprint.comm.protocol.gcode.error": __plugin_implementation__.printer_error_hook
    }
