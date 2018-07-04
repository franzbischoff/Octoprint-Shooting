/*
* View model for OctoPrint-Shooting
*
* Author: Francisco Bischoff
* License: AGPLv3
*/

$(function () {
    function ShootingViewModel(parameters) {
        var self = this;

        // assign the injected parameters, e.g.:
        // self.loginStateViewModel = parameters[0];
        // self.settingsViewModel = parameters[1];
        self.settingsViewModel = parameters[0];

        self.currentUrl = ko.observable();
        self.plot = null; // plotly graph
        self.defaultColors = {
            background: '#ffffff',
            axises: '#000000'
        }

        self.bindFromSettings = function () {
            self.rpi_outputs(self.settingsViewModel.settings.plugins.enclosure.rpi_outputs());
            self.rpi_inputs(self.settingsViewModel.settings.plugins.enclosure.rpi_inputs());
            self.use_sudo(self.settingsViewModel.settings.plugins.enclosure.use_sudo());
            self.gcode_control(self.settingsViewModel.settings.plugins.enclosure.gcode_control());
            self.neopixel_dma(self.settingsViewModel.settings.plugins.enclosure.neopixel_dma());
            self.debug(self.settingsViewModel.settings.plugins.enclosure.debug());
            self.debug_temperature_log(self.settingsViewModel.settings.plugins.enclosure.debug_temperature_log());
            self.use_board_pin_number(self.settingsViewModel.settings.plugins.enclosure.use_board_pin_number());
            self.filament_sensor_gcode(self.settingsViewModel.settings.plugins.enclosure.filament_sensor_gcode());
            self.notification_provider(self.settingsViewModel.settings.plugins.enclosure.notification_provider());
            self.notification_event_name(self.settingsViewModel.settings.plugins.enclosure.notification_event_name());
            self.notification_api_key(self.settingsViewModel.settings.plugins.enclosure.notification_api_key());
            self.notifications(self.settingsViewModel.settings.plugins.enclosure.notifications());
        };

        // Called when the first initialization has been done. All view models are constructed and hence their
        // dependencies resolved, no bindings have been done yet.
        // self.onStartup = function() {}

        // This will get called before the ShootingViewModel gets bound to the DOM, but after its dependencies have
        // already been initialized. It is especially guaranteed that this method gets called _after_ the settings
        // have been retrieved from the OctoPrint backend and thus the SettingsViewModel been properly populated.
        self.onBeforeBinding = function () {
            self.bindFromSettings();
            self.newUrl(self.settingsViewModel.settings.plugins.shooting.url());
            self.goToUrl();
        }

        // Called per view model after binding it to its binding targets.
        // self.onAfterBinding = function() {}

        // Called after all view models have been bound, with the list of all view models as the single parameter.
        // self.onAllBound(allViewModels) = function() {}

        // Called after the startup of the web app has been completed.
        self.onStartupComplete = function () {
            self.settingsOpen = false;

            self.plot = document.getElementById("plotLy");

            // data [{},{}]
            data = [{
                type: 'scatter',
                x: [1, 2, 3, 4, 5],
                y: [1, 2, 4, 8, 16],
                name: 'data',
                marker: {         // marker is an object, valid marker keys: #scatter-marker
                    color: 'rgb(255, 0, 0)' // more about "marker.color": #scatter-marker-color
                }
            }];

            layout = {
                title: 'Simple Chart',
                xaxis: {
                    title: 'time',
                    type: 'linear',
                    rangemode: 'nonnegative',
                    showgrid: true,
                    zeroline: false,
                    linecolor: 'gray',
                    linewidth: 1,
                    mirror: true,
                    color: self.defaultColors.axises
                },
                yaxis: {
                    title: 'acceleration (m/s' + '2'.sup() + ')',
                    type: 'linear',
                    linecolor: 'gray',
                    linewidth: 1,
                    mirror: true,
                    color: self.defaultColors.axises
                },
                autosize: true,
                height: self.plot.clientHeight,
                width: 588, //self.plot.clientWidth,
                margin: {l: 50, r: 30, b: 50, t: 30},
                showlegend: true,
                hovermode: 'x',
                paper_bgcolor: self.defaultColors.background,
                plot_bgcolor: self.defaultColors.background
            };

            Plotly.plot(self.plot, data, layout);

            // // update plot
            // if (self.plot) {
            //     var tracesToUpdate = []; // [0,1,2,3,...]
            //     for (var i = 0; i < newData.x.length; i++) {
            //         tracesToUpdate.push(i);
            //     }
            //
            //     // update layout
            //     Plotly.extendTraces(self.plot, newData, tracesToUpdate, result.length)
            // }

            // change colors, etc
            // Plotly.relayout(self.plot, relayout);
        }

        // Called if a disconnect from the server is detected.
        // self.onServerDisconnect = function() {}
        // Called when the connection to the server has been reestablished after a disconnect.
        // self.onDataUpdaterReconnect = function() {}
        // Called when history data is received from the server. Usually that happens only after initial connect in
        // order to transmit the temperature and terminal log history to the connecting client. Called with the data as
        // single parameter.
        // self.fromHistoryData = function() {}
        // Called when current printer status data is received from the server with the data as single parameter.
        // self.fromCurrentData = function() {}
        // Called on slicing progress, call rate is once per percentage point of the progress at maximum.
        // self.onSlicingProgress(slicer, modelPath, machineCodePath, progress) = function() {}
        // Called on firing of an event of type EventName, e.g. onEventPrintDone. See the list of available events for the
        // possible events and their payloads.
        // self.onEvent<EventName>(payload) = function() {}
        // Called when timelapse configuration data is received from the server. Usually that happens after initial connect.
        // self.fromTimelapseData(data) = function() {}

        // Called when a plugin message is pushed from the server with the identifier of the calling plugin as first and the
        // actual message as the second parameter. Note that the latter might be a full fledged object, depending on the plugin
        // sending the message. You can use this method to asynchronously push data from your plugin’s server component to its
        // frontend component.
        self.onDataUpdaterPluginMessage = function (plugin, data) {

            if (typeof plugin == 'undefined') {
                return;
            }

            if (plugin != "shooting") {
                return;
            }

            if (self.settingsOpen) {
                return;
            }

            if (data.hasOwnProperty("sensor_data")) {
                data.sensor_data.forEach(function (sensor_data) {
                    var linked_temp_sensor = ko.utils.arrayFilter(self.rpi_inputs_temperature_sensors(), function (temperature_sensor) {
                        return (sensor_data['index_id'] == temperature_sensor.index_id());
                    }).pop();
                    if (linked_temp_sensor) {
                        linked_temp_sensor.temp_sensor_temp(sensor_data['temperature'])
                        linked_temp_sensor.temp_sensor_humidity(sensor_data['humidity'])
                    }
                })
            }

            if (data.hasOwnProperty("set_temperature")) {
                data.set_temperature.forEach(function (set_temperature) {
                    var linked_temp_control = ko.utils.arrayFilter(self.rpi_outputs(), function (temp_control) {
                        return (set_temperature['index_id'] == temp_control.index_id());
                    }).pop();
                    if (linked_temp_control) {
                        linked_temp_control.temp_ctr_set_value(set_temperature['set_temperature'])
                    }
                })
            }

            if (data.hasOwnProperty("rpi_output_regular")) {
                data.rpi_output_regular.forEach(function (output) {
                    var linked_output = ko.utils.arrayFilter(self.rpi_outputs(), function (item) {
                        return (output['index_id'] == item.index_id());
                    }).pop();
                    if (linked_output) {
                        linked_output.gpio_status(output['status'])
                        linked_output.auto_shutdown(output['auto_shutdown'])
                        linked_output.auto_startup(output['auto_startup'])
                    }
                })
            }

            if (data.hasOwnProperty("rpi_output_temp_hum_ctrl")) {
                data.rpi_output_temp_hum_ctrl.forEach(function (output) {
                    var linked_output = ko.utils.arrayFilter(self.rpi_outputs(), function (item) {
                        return (output['index_id'] == item.index_id());
                    }).pop();
                    if (linked_output) {
                        linked_output.gpio_status(output['status'])
                        linked_output.auto_shutdown(output['auto_shutdown'])
                        linked_output.auto_startup(output['auto_startup'])
                    }
                })
            }

            if (data.hasOwnProperty("rpi_output_pwm")) {
                data.rpi_output_pwm.forEach(function (output) {
                    var linked_output = ko.utils.arrayFilter(self.rpi_outputs(), function (item) {
                        return (output['index_id'] == item.index_id());
                    }).pop();
                    if (linked_output) {
                        linked_output.duty_cycle(output['pwm_value'])
                        linked_output.auto_shutdown(output['auto_shutdown'])
                        linked_output.auto_startup(output['auto_startup'])
                    }
                })
            }

            if (data.hasOwnProperty("rpi_output_neopixel")) {
                data.rpi_output_neopixel.forEach(function (output) {
                    var linked_output = ko.utils.arrayFilter(self.rpi_outputs(), function (item) {
                        return (output['index_id'] == item.index_id());
                    }).pop();
                    if (linked_output) {
                        linked_output.neopixel_color(output['color'])
                        linked_output.auto_shutdown(output['auto_shutdown'])
                        linked_output.auto_startup(output['auto_startup'])
                    }
                })
            }

            if (data.hasOwnProperty("filament_sensor_status")) {
                data.filament_sensor_status.forEach(function (filament_sensor) {
                    var linked_filament_sensor = ko.utils.arrayFilter(self.rpi_inputs(), function (item) {
                        return (filament_sensor['index_id'] == item.index_id());
                    }).pop();
                    if (linked_filament_sensor) {
                        linked_filament_sensor.filament_sensor_enabled(filament_sensor['filament_sensor_enabled'])
                    }
                })
            }

            if (data.is_msg) {
                new PNotify({
                    title: "Shooting",
                    text: data.msg,
                    type: data.msg_type
                });
            }
        };

        // Called when a user gets logged into the web app, either passively (upon initial load of the page due to a
        // valid “Remember Me” cookie) or due to an active completion of the login dialog. The user data of the just
        // logged in user will be provided as only parameter.
        // self.onUserLoggedIn(user) = function() {}
        // Called when a user gets logged out of the web app.
        // self.onUserLoggedOut() = function() {}
        // Called before the main tab view switches to a new tab, so before the new tab becomes visible. Called with the
        // next (changed to) and current (still visible) tab’s hash (e.g. #control). Note that current might be
        // undefined on the very first call.
        // self.onTabChange(next, current) = function() {}
        // Called after the main tab view switches to a new tab, so after the new tab becomes visible. Called with the
        // current and previous tab’s hash (e.g. #control).
        // self.onAfterTabChange(current, previous) = function() {}
        // Your view model may return additional custom control definitions for inclusion on the “Control” tab of
        // OctoPrint’s interface. See the custom control feature.
        // self.getAdditionalControls() = function() {}

        // Called when the settings dialog is shown.
        self.onSettingsShown = function () {
            self.settingsOpen = true;
        }

        // Called when the settings dialog is hidden.
        self.onSettingsHidden = function () {
            self.settingsOpen = false;
        }

        // Called just before the settings view model is sent to the server. This is useful, for example, if your plugin
        // needs to compute persisted settings from a custom view model.
        self.onSettingsBeforeSave = function () {
            self.bindFromSettings();
        }

        // Called when the user settings dialog is shown.
        // self.onUserSettingsShown = function() {}
        // Called when the user settings dialog is hidden.
        // self.onUserSettingsHidden = function() {}
        // Called with the response from the wizard detail API call initiated before opening the wizard dialog. Will
        // contain the data from all WizardPlugin implementations returned by their get_wizard_details() method, mapped
        // by the plugin identifier.
        // self.onWizardDetails(response) = function() {}
        // Called before the wizard tab/step is changed, with the ids of the next (changed to) and the current (still
        // visible) tab as parameters. Return false in order to prevent the tab change, e.g. if the wizard step is
        // mandatory and not yet completed by the user. Take a look at the “Core Wizard” plugin bundled with OctoPrint
        // and the ACL wizard step in particular for an example on how to use this.
        // self.onBeforeWizardTabChange(next, current) = function() {}
        // Called after the wizard tab/step is changed, with the id of the current tab as parameter. The id of the
        // previous tab is sadly not available currently.
        // self.onAfterWizardTabChange(current) = function() {}
        // Called before executing the finishing of the wizard. Return false here to stop the actual finish, e.g. if
        // some step is still incomplete.
        // self.onBeforeWizardFinish = function() {}
        // Called after executing the finishing of the wizard and before closing the dialog. Return reload here in order
        // to instruct OctoPrint to reload the UI after the wizard closes.
        // self.onWizardFinish = function() {}
    }

    /* view model class, parameters for constructor, container to bind to
    * Please see http://docs.octoprint.org/en/master/plugins/viewmodels.html#registering-custom-viewmodels for more details
    * and a full list of the available options.
    */
    OCTOPRINT_VIEWMODELS.push({
        construct: ShootingViewModel,
        // ViewModels your plugin depends on, e.g. loginStateViewModel, settingsViewModel, ...
        dependencies: ["settingsViewModel" /* "loginStateViewModel" */],
        // Elements to bind to, e.g. #settings_plugin_shooting, #tab_plugin_shooting, ...
        elements: ["#tab_plugin_shooting", "#navbar_plugin_shooting" /* ... */]
    });
});
