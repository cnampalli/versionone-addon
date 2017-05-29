/*global window URL*/
require([
    'jquery',
    "splunkjs/mvc/utils",
    "splunkjs/mvc/simplexml/ready!"
], function (
    $,
    SplunkUtil
) {
    'use strict';
    String.prototype.capitalizeFirstLetter = function () {
        return this.charAt(0).toUpperCase() + this.slice(1);
    };
    var appname = SplunkUtil.getCurrentApp();
    var toolName = appname.split('-')[2];
    console.info('appName: ' + appname);
    var document_url = new URL(document.URL);
    var document_path = document_url.pathname;
    var document_domain = document_path.slice(0, document_path.indexOf("/app/"));
    var setup_url = document_domain + '/splunkd/__raw/servicesNS/-/' + appname + '/' + toolName + '/setup';
    var checkpoint_url = document_domain + '/splunkd/__raw/servicesNS/-/' + appname + '/' + toolName + '/checkpoint';


    var authenticationParameters = {
        none: [],
        basic: ['auth_user', 'auth_password'],
        digest: ['auth_user', 'auth_password'],
        oauth1: ['oauth1_client_key', 'oauth1_client_secret', 'oauth1_access_token', 'oauth1_access_token_secret'],
        oauth2: ['oauth2_token_type', 'oauth2_access_token', 'oauth2_refresh_token', 'oauth2_refresh_url', 'oauth2_refresh_props', 'oauth2_client_id', 'oauth2_client_secret'],
        custom: ['access_token']
    };

    function inputVariables() {
        return [
            {
                id: 'host',
                description: toolName.capitalizeFirstLetter() + ' hostname',
                value: ''
            },
            {
                id: 'protocol',
                description: toolName.capitalizeFirstLetter() + ' protocol (http or https)',
                value: 'https',
                authorised_values: ['http', 'https']
            },
            {
                id: 'auth_type',
                description: 'Authentication type',
                value: 'custom',
                authorised_values: ['custom'],
                hidden: true
            },
            {
                id: 'access_token',
                description: 'Access token used to access ' + toolName.capitalizeFirstLetter(),
                value: ''
            },
            {
                id: 'project',
                description: 'Project name',
                value: ''
            },
            {
                id: 'response_handler',
                description: 'API you want to use',
                authorised_values: ['VersionOneQuery', 'VersionOneData'],
                value: 'VersionOneQuery'
            },
            {
                id: 'interval',
                description: 'Interval at which the repository is polled',
                value: '300'
            },
            {
                id: 'index',
                description: 'Splunk index to send the data to',
                value: 'aaam_devops_' + toolName + '_idx'
            },
            {
                id: 'sourcetype',
                description: 'Splunk source type to send the data to',
                value: toolName + '_api'
            }
        ];
    }

    function return_status_banner() {
        return '<div id="info_banner" class="info">Successfully updated configuration for add-on. </div>' +
                '<div id="save_err_banner" class="error">Fail to update configuration for add-on. </div>' +
                '<div id="load_err_banner" class="error">Fail to load configuration for add-on. </div>';
    }

    function input(variable, itemNumber) {
        var result = '';
        var id = variable.id + '-' + itemNumber;

        if (variable !== null && variable.hidden) {
            result += '<input type="hidden" name="' + id + '" id="input-' + id + '" value="' + variable.value + '" class="' + variable.id + '"/>';
        } else if ($.isArray(variable.authorised_values)) {
            result +=
                    '<div id="item-' + id + '" class="widget">' +
                    '  <label>' + variable.description + '</label>';
            result +=
                    '  <select id="input-' + id + '" name="' + id + '" class="' + variable.id + '">';
            $.each(variable.authorised_values, function () {
                if (variable.value === this) {
                    result +=
                            '    <option value="' + this + '" selected="selected">' + this + '</option>';

                } else {
                    result +=
                            '    <option value="' + this + '">' + this + '</option>';
                }

            });
            result +=
                    '  </select>';
            result +=
                    '</div>';
        } else {
            result +=
                    '<div id="item-' + id + '" class="widget">' +
                    '  <label>' + variable.description + '</label>';
            result +=
                    '  <input type="text" name="' + id + '" id="input-' + id + '" value="' + variable.value + '" class="' + variable.id + '"/>';
            result +=
                    '</div>';
        }
        return result;
    }


    function input_block(inputVariables) {
        var itemNumber = $('.inputs').length > 0
            ? (parseInt($('.inputs')[$('.inputs').length - 1].id.split('-')[2]) + 1)
            : 0;

        var result = '<div class="fieldsetWrapper inputs" id="item-blockFieldset-' + itemNumber + '"">' +
                '<fieldset>' +
                '<legend>Inputs</legend>';
        result += (itemNumber !== 0)
            ? '<button class="my-btn-delete deleteInput"  id="button-deleteInput-' + itemNumber + '" type="button"><span>Delete this input</span></button>'
            : '';

        var i = 0;
        for (i = 0; i < inputVariables.length; i += 1) {
            result += input(inputVariables[i], itemNumber);
        }
        result += '</fieldset></div>';
        return result;
    }

    function return_page() {
        var result = '<div class="entityEditForm"><div class="formWrapper" id="inputVariablesList">';
        result +=
                '<div class="jmFormActions" id="inputVariablesActions" style="">' +
                '<button class="my-btn-secondary" id="cancel" type="button"><span>Cancel</span></button>' +
                '<button class="my-btn-secondary" id="addInput" type="button"><span>Add new input</span></button>' +
                '<button class="my-btn-secondary" id="deleteCheckpoint" type="button" title="Remove checkpoint to re-index data from scratch"><span>Delete checkpoint</span></button>' +
                '<button type="submit" class="my-btn-primary" id="save"><span>Save</span></button>' +
                '</div>' +
                '</div></div>';

        return result;
    }

    function load_css() {
        var cssLinks = [
            '/en-US/static/css/view.css',
            '/en-US/static/css/skins/default/default.css',
            '/en-US/static/css/print.css',
            '/en-US/static/css/tipTip.css',
            '/en-US/static/build/css/splunk-components-enterprise.css',
            '/en-US/static/css/admin.css'
        ];

        var i;
        for (i = 0; i < cssLinks.length; i += 1) {
            $("<link>").attr({
                rel: "stylesheet",
                type: "text/css",
                href: cssLinks[i]
            }).appendTo("head");
        }
    }

    function get_all_inputs() {
        var result = {};
        var iVariables = inputVariables();
        $('.inputs').each(function () {
            var itemNumber = this.id.split('-')[2];
            result['inputs-' + itemNumber] = {};
            var key, value, i;
            for (i = 0; i < iVariables.length; i += 1) {
                key = iVariables[i].id;
                value = $('#input-' + key + '-' + itemNumber).val();
                result['inputs-' + itemNumber][key] = value;
            }
        });
        return result;
    }

    function appConfigured() {
        $.ajax({
            url: '/en-US/splunkd/__raw/services/apps/local/' + appname,
            type: 'POST',
            data: {
                configured: true
            }
        }).done(function () {
            console.log('set configured as true!');
        }).fail(function () {
            console.log('fail to set configured as true!');
        });
    }

    /**
     * hide/show fields when authentication scheme changes
     */
    function configure_authentication() {
        console.info('Authentication scheme changed on ' + this.id);
        var itemNumber = this.id.split('-')[2];
        var newAuthenticationScheme = this.value;

        //Hide authentication elements
        $.each(authenticationParameters, function (key) {
            var authenticationType = key;
            $.each(authenticationParameters[key], function () {
                var elementId = '#item-' + this + '-' + itemNumber;
                if ($(elementId).length && authenticationType !== newAuthenticationScheme) {
                    //console.info('hide: ' + elementId);
                    $(elementId).hide();
                }
            });
        });

        //Then show required ones (done in 2 passes to )
        $.each(authenticationParameters[newAuthenticationScheme], function () {
            var elementId = '#item-' + this + '-' + itemNumber;
            if ($(elementId).length) {
                //console.info('show: ' + elementId);
                $(elementId).show();
            }
        });
    }

    var saving = false;
    function save_settings() {
        $.ajax({
            url: setup_url,
            type: "POST",
            data: JSON.stringify(get_all_inputs())
        }).done(function () {
            $('#load_err_banner').hide();
            $('#save_err_banner').hide();
            $('#info_banner').show();
            appConfigured();
        }).fail(function () {
            $('#load_err_banner').hide();
            $('#save_err_banner').show();
            $('#info_banner').hide();
        }).always(function () {
            saving = false;
            $(".my-btn-primary span").html("Save");
        });
    }

    load_css();
    // generate the html
    $("body").prepend(return_status_banner());
    $('#setup_page_container').html(return_page());
    $('#info_banner').hide();
    $('#save_err_banner').hide();
    $('#load_err_banner').hide();

    $(".my-btn-primary span").html("Save");
    //Deletes elements when user clicks on of the delete buttons
    $('#inputVariablesList').on('click', '.deleteInput', function () {
        var itemNumber = $(this).attr('id').split('-')[2];
        console.info('Delete input: ' + itemNumber);
        $('#item-blockFieldset-' + itemNumber).remove();
    });

    //Adds a new block of inputs
    $('#addInput').click(function (e) {
        console.info('Add input: ' + e);
        $("#inputVariablesActions").before(input_block(inputVariables()));
    });

    // Sends results
    $('#save').click(function (e) {
        e.preventDefault();
        if (saving) {
            return;
        }
        saving = true;
        $(".my-btn-primary span").html("Saving");
        save_settings();
    });

    $('#cancel').click(function () {
        window.location = "../../manager/launcher/apps/local";
    });
    //checkpoint_url
    $('#deleteCheckpoint').click(function () {
        $.ajax({
            url: checkpoint_url,
            type: "DELETE"
        });
    });

    //Hide authentication fields if required
    $('#inputVariablesList').on('change', '.auth_type', configure_authentication);


    //Load settings
    $.ajax({
        url: setup_url,
        data: {
            output_mode: "json"
        },
        type: "GET",
        dataType: "json"
    }).done(function (response) {
        $.each(response, function () {
            var settings = this;
            var iVariables = inputVariables();
            Object.keys(settings).forEach(function (key) {
                $.each(iVariables, function () {
                    if (this.id === key) {
                        this.value = settings[key];
                    }
                });
            });
            $("#inputVariablesActions").before(input_block(iVariables));
            $('.auth_type').each(configure_authentication);
        });
    }).fail(function (xhr, status, response) {
        $('#load_err_banner').show();
        $('#save_err_banner').hide();
        $('#info_banner').hide();
        console.log(status, response);
    });

}); // the end of require
