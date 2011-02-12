/*jsl:import ipa.js */
/*jsl:import certificate.js */

/*  Authors:
 *    Pavel Zuna <pzuna@redhat.com>
 *    Endi S. Dewata <edewata@redhat.com>
 *
 * Copyright (C) 2010 Red Hat
 * see file 'COPYING' for use and warranty information
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

/* REQUIRES: ipa.js, details.js, search.js, add.js, entity.js */

IPA.entity_factories.host = function () {

    var that = IPA.entity({
        'name': 'host'
    });

    that.init = function() {

        var facet = IPA.host_search_facet({
            'name': 'search',
            'label': 'Search'
        });
        that.add_facet(facet);

        var dialog = IPA.host_add_dialog({
            'name': 'add',
            'title': 'Add New Host'
        });
        facet.dialog(dialog);

        facet = IPA.host_details_facet({
            'name': 'details'
        });
        that.add_facet(facet);

        facet = IPA.host_managedby_host_facet({
            'name': 'managedby_host'
        });
        that.add_facet(facet);

        facet = IPA.association_facet({
            name: 'memberof_hostgroup',
            associator: IPA.serial_associator
        });
        that.add_facet(facet);

        facet = IPA.association_facet({
            name: 'memberof_netgroup',
            associator: IPA.serial_associator
        });
        that.add_facet(facet);

        facet = IPA.association_facet({
            name: 'memberof_role',
            associator: IPA.serial_associator
        });
        that.add_facet(facet);

        that.create_association_facets();

        that.entity_init();
    };

    return that;
};


IPA.host_add_dialog = function (spec) {

    spec = spec || {};

    var that = IPA.add_dialog(spec);

    that.init = function() {

        that.add_field(IPA.text_widget({
            name: 'fqdn',
            size: 40,
            undo: false
        }));

        // TODO: Replace with i18n label
        that.add_field(IPA.checkbox_widget({
            name: 'force',
            label: 'Force',
            tooltip: 'force host name even if not in DNS',
            undo: false
        }));

        that.add_dialog_init();
    };

    return that;
};

/* Take an LDAP format date in UTC and format it */
IPA.utc_date_column_format = function(value){
    if (!value) {
        return "";
    }
    if (value.length  != "20101119025910Z".length){
        return value;
    }
    /* We only handle GMT */
    if (value.charAt(value.length -1) !== 'Z'){
        return value;
    }

    var date = new Date();

    date.setUTCFullYear(
        value.substring(0, 4),
        value.substring(4, 6),
        value.substring(6, 8));
    date.setUTCHours(
        value.substring(8, 10),
        value.substring(10, 12),
        value.substring(12, 14));
    var formated = date.toString();
    return  formated;
};

IPA.host_search_facet = function (spec) {

    spec = spec || {};

    var that = IPA.search_facet(spec);

    that.init = function() {

        that.create_column({name:'fqdn'});
        that.create_column({name:'description'});
        //TODO use the value of this field to set enrollment status
        that.create_column({name:'krblastpwdchange', label:'Enrolled?',
                            format:IPA.utc_date_column_format
                           });
        that.create_column({name:'nshostlocation'});

        that.search_facet_init();
    };

    return that;
};


IPA.host_details_facet = function (spec) {

    spec = spec || {};

    var that = IPA.details_facet(spec);

    that.init = function() {

        var section = IPA.details_list_section({
            'name': 'details',
            'label': 'Host Settings'
        });
        that.add_section(section);

        //TODO: use i18n labels
        section.text({
            name: 'fqdn',
            label: 'Fully Qualified Host Name'
        });

        section.text({'name': 'krbprincipalname'});

        //TODO: add this to the host plugin
        //TODO: use i18n labels
        section.text({
            'name': 'serverhostname',
            'label': 'Host Name'
        });

        section.text({'name': 'description'});

        //TODO: use i18n labels
        section = IPA.details_list_section({
            'name': 'enrollment',
            'label': 'Enrollment'
        });
        that.add_section(section);

        //TODO add label to messages
        section.add_field(host_provisioning_status_widget({
            'name': 'provisioning_status',
            'label': 'Status',
            'facet': that
        }));

        section = IPA.details_list_section({
            'name': 'certificate',
            'label': 'Host Certificate'
        });
        that.add_section(section);

        section.add_field(host_certificate_status_widget({
            'name': 'certificate_status',
            'label': 'Status'
        }));

        that.details_facet_init();
    };

    that.refresh = function() {

        var pkey = $.bbq.getState(that.entity_name + '-pkey', true) || '';

        var command = IPA.command({
            'name': that.entity_name+'_show_'+pkey,
            'method': that.entity_name+'_show',
            'args': [pkey],
            'options': { 'all': true, 'rights': true }
        });

        command.on_success = function(data, text_status, xhr) {
            that.load(data.result.result);
        };

        command.on_error = function(xhr, text_status, error_thrown) {
            var details = $('.details', that.container).empty();
            details.append('<p>Error: '+error_thrown.name+'</p>');
            details.append('<p>'+error_thrown.title+'</p>');
            details.append('<p>'+error_thrown.message+'</p>');
        };

        command.execute();
    };

    return that;
};


function host_provisioning_status_widget(spec) {

    spec = spec || {};

    var that = IPA.widget(spec);

    that.facet = spec.facet;

    that.create = function(container) {

        that.widget_create(container);

        var div = $('<div/>', {
            name: 'kerberos-key-valid',
            style: 'display: none;'
        }).appendTo(container);

        $('<img/>', {
            src: 'check.png',
            style: 'float: left;',
            'class': 'status-icon'
        }).appendTo(div);

        var content_div = $('<div/>', {
            style: 'float: left;'
        }).appendTo(div);

        content_div.append('<b>Kerberos Key Present, Host Provisioned:</b>');

        content_div.append(' ');

        $('<input/>', {
            'type': 'button',
            'name': 'unprovision',
            'value': 'Delete Key, Unprovision'
        }).appendTo(content_div);

        div = $('<div/>', {
            name: 'kerberos-key-missing',
            style: 'display: none;'
        }).appendTo(container);

        $('<img/>', {
            src: 'caution.png',
            style: 'float: left;',
            'class': 'status-icon'
        }).appendTo(div);

        content_div = $('<div/>', {
            style: 'float: left;'
        }).appendTo(div);

        content_div.append('<b>Kerberos Key Not Present</b>');

        content_div.append('<br/>');

        content_div.append('Enroll via One-Time-Password:');

        content_div.append('<br/>');
        content_div.append('<br/>');

        $('<input/>', {
            'type': 'text',
            'name': 'otp',
            'class': 'otp'
        }).appendTo(content_div);

        content_div.append(' ');

        $('<input/>', {
            'type': 'button',
            'name': 'enroll',
            'value': 'Set OTP'
        }).appendTo(content_div);
    };

    that.setup = function(container) {

        that.widget_setup(container);

        that.status_valid = $('div[name=kerberos-key-valid]', that.container);
        that.status_missing = $('div[name=kerberos-key-missing]', that.container);

        var button = $('input[name=unprovision]', that.container);
        that.unprovision_button = IPA.button({
            'label': 'Delete Key, Unprovision',
            'click': that.show_unprovision_dialog
        });
        button.replaceWith(that.unprovision_button);

        that.otp_input = $('input[name=otp]', that.container);

        that.enroll_button = $('input[name=enroll]', that.container);
        button = IPA.button({
            'label': 'Set OTP',
            'click': that.set_otp
        });

        that.enroll_button.replaceWith(button);
        that.enroll_button = button;
    };

    that.show_unprovision_dialog = function() {

        var label = IPA.metadata[that.entity_name].label;
        var dialog = IPA.dialog({
            'title': 'Unprovisioning '+label
        });

        dialog.create = function() {
            dialog.container.append(
                'Are you sure you want to unprovision this host?');
        };

        dialog.add_button('Unprovision', function() {
            that.unprovision(
                function(data, text_status, xhr) {
                    set_status('missing');
                    dialog.close();
                },
                function(xhr, text_status, error_thrown) {
                    dialog.close();
                }
            );
        });

        dialog.init();

        dialog.open(that.container);

        return false;
    };

    that.unprovision = function(on_success, on_error) {

        var pkey = that.facet.get_primary_key();

        var command = IPA.command({
            'name': that.entity_name+'_disable_'+pkey,
            'method': that.entity_name+'_disable',
            'args': [pkey],
            'options': { 'all': true, 'rights': true },
            'on_success': on_success,
            'on_error': on_error
        });

        command.execute();
    };

    that.set_otp = function() {

        var pkey = that.facet.get_primary_key();
        var otp = that.otp_input.val();
        that.otp_input.val('');

        var command = IPA.command({
            'method': that.entity_name+'_mod',
            'args': [pkey],
            'options': {
                'all': true,
                'rights': true,
                'userpassword': otp
            },
            'on_success': function(data, text_status, xhr) {
                alert('One-Time-Password has been set.');
            }
        });

        command.execute();
    };

    that.load = function(result) {
        that.result = result;
        var krblastpwdchange = result['krblastpwdchange'];
        set_status(krblastpwdchange ? 'valid' : 'missing');
    };

    function set_status(status) {
        that.status_valid.css('display', status == 'valid' ? 'inline' : 'none');
        that.status_missing.css('display', status == 'missing' ? 'inline' : 'none');
    }

    return that;
}

function host_certificate_status_widget(spec) {

    spec = spec || {};

    var that = certificate_status_widget(spec);

    that.init = function() {

        that.entity_label = IPA.metadata[that.entity_name].label;

        that.get_entity_pkey = function(result) {
            var values = result['fqdn'];
            return values ? values[0] : null;
        };

        that.get_entity_name = function(result) {
            return that.get_entity_pkey(result);
        };

        that.get_entity_principal = function(result) {
            var values = result['krbprincipalname'];
            return values ? values[0] : null;
        };

        that.get_entity_certificate = function(result) {
            var values = result['usercertificate'];
            return values ? values[0].__base64__ : null;
        };
    };

    return that;
}

IPA.host_managedby_host_facet = function (spec) {

    spec = spec || {};

    var that = IPA.association_facet(spec);

    that.add_method = 'add_managedby';
    that.remove_method = 'remove_managedby';

    that.init = function() {

        var column = that.create_column({
            name: 'fqdn',
            primary_key: true
        });

        column.setup = function(container, record) {
            container.empty();

            var value = record[column.name];
            value = value ? value.toString() : '';

            $('<a/>', {
                'href': '#'+value,
                'html': value,
                'click': function (value) {
                    return function() {
                        var state = IPA.tab_state(that.other_entity);
                        state[that.other_entity + '-facet'] = 'details';
                        state[that.other_entity + '-pkey'] = value;
                        $.bbq.pushState(state);
                        return false;
                    };
                }(value)
            }).appendTo(container);
        };

        that.create_column({name: 'description'});

        that.create_adder_column({
            name: 'fqdn',
            primary_key: true,
            width: '100px'
        });

        that.create_adder_column({
            name: 'description',
            width: '100px'
        });

        that.association_facet_init();
    };

    return that;
};
