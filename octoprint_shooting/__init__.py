# coding=utf-8
from __future__ import absolute_import

import flask

import octoprint.plugin


# from octoprint.events import eventManager, Events
# from octoprint.util import RepeatedTimer
# from subprocess import Popen, PIPE
# import RPi.GPIO as GPIO
# import flask
# import time
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


class ShootingPlugin(octoprint.plugin.SettingsPlugin,  # self._settings (instance of PluginSettingsManager)
                     octoprint.plugin.AssetPlugin,
                     octoprint.plugin.TemplatePlugin,
                     octoprint.plugin.StartupPlugin,
                     octoprint.plugin.BlueprintPlugin,
                     octoprint.plugin.EventHandlerPlugin):

    # ~~ SettingsPlugin mixin

    def get_settings_defaults(self):
        return dict(
            # put your plugin's default settings here
            url="https://en.wikipedia.org/wiki/Hello_world"

            # rpi_outputs=[],
            # rpi_inputs=[],
            # filament_sensor_gcode="G91  ;Set Relative Mode \n" +
            # "G1 E-5.000000 F500 ;Retract 5mm\n" +
            # "G1 Z15 F300         ;move Z up 15mm\n" +
            # "G90            ;Set Absolute Mode\n " +
            # "G1 X20 Y20 F9000      ;Move to hold position\n" +
            # "G91            ;Set Relative Mode\n" +
            # "G1 E-40 F500      ;Retract 40mm\n" +
            # "M0            ;Idle Hold\n" +
            # "G90            ;Set Absolute Mode\n" +
            # "G1 F5000         ;Set speed limits\n" +
            # "G28 X0 Y0         ;Home X Y\n" +
            # "M82            ;Set extruder to Absolute Mode\n" +
            # "G92 E0         ;Set Extruder to 0",
            # use_sudo=True,
            # neopixel_dma=10,
            # debug=False,
            # gcode_control=False,
            # debug_temperature_log=False,
            # use_board_pin_number=False,
            # notification_provider="disabled",
            # notification_api_key="",
            # notification_event_name="printer_event",
            # notifications=[{'printFinish': True, 'filamentChange': True,
            #                 'printer_action': True, 'temperatureAction': True, 'gpioAction': True}]
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

    # ~~ Softwareupdate hook

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

        # ~~ octoprint.comm.protocol.atcommand.<phase> hook; @ commands (https://goo.gl/wXmgvt)
        # ~~ octoprint.comm.protocol.gcode.<phase> hook; read from file and sent gcode do printer (https://goo.gl/at8fEo)
        # ~~ octoprint.comm.protocol.gcode.received hook; read responses from printer (https://goo.gl/hTFcHY)
        # ~~ octoprint.comm.protocol.gcode.error hook; read error messages from printer (https://goo.gl/49XcDd)


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Shooting Plugin"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = ShootingPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
