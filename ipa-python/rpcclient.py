#! /usr/bin/python -E
# Authors: Rob Crittenden <rcritten@redhat.com>
#
# Copyright (C) 2007  Red Hat
# see file 'COPYING' for use and warranty information
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; version 2 or later
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#

#!/usr/bin/python

import xmlrpclib
import socket
import config
from krbtransport import KerbTransport
from kerberos import GSSError
import os
import base64
import user
import ipa
from ipa import ipaerror, ipautil

# Some errors to catch
# http://cvs.fedora.redhat.com/viewcvs/ldapserver/ldap/servers/plugins/pam_passthru/README?root=dirsec&rev=1.6&view=auto

class RPCClient:

    def __init__(self):
        ipa.config.init_config()
    
    def server_url(self):
        """Build the XML-RPC server URL from our configuration"""
        return "http://" + config.config.get_server() + "/ipa"
    
    def setup_server(self):
        """Create our XML-RPC server connection using kerberos
           authentication"""
        return xmlrpclib.ServerProxy(self.server_url(), KerbTransport())
    
    def convert_entry(self,ent):
        # Convert into a dict. We need to handle multi-valued attributes as well
        # so we'll convert those into lists.
        obj={}
        for (k) in ent:
            k = k.lower()
            if obj.get(k) is not None:
                if isinstance(obj[k],list):
                    obj[k].append(ent[k].strip())
                else:
                    first = obj[k]
                    obj[k] = ()
                    obj[k].append(first)
                    obj[k].append(ent[k].strip())
            else:
                 obj[k] = ent[k]
    
        return obj 
        
# User support

    def get_user_by_uid(self,uid,sattrs=None):
        """Get a specific user. If sattrs is not None then only those
           attributes will be returned, otherwise all available
           attributes are returned. The result is a dict."""
        server = self.setup_server()
        if sattrs is None:
            sattrs = "__NONE__"
        try:
            result = server.get_user_by_uid(uid, sattrs)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)
        
    def get_user_by_dn(self,dn,sattrs=None):
        """Get a specific user. If sattrs is not None then only those
           attributes will be returned, otherwise all available
           attributes are returned. The result is a dict."""
        server = self.setup_server()
        if sattrs is None:
            sattrs = "__NONE__"
        try:
            result = server.get_user_by_dn(dn, sattrs)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def add_user(self,user,user_container=None):
        """Add a new user. Takes as input a dict where the key is the
           attribute name and the value is either a string or in the case
           of a multi-valued field a list of values"""
        server = self.setup_server()

        if user_container is None:
            user_container = "__NONE__"
    
        try:
            result = server.add_user(ipautil.wrap_binary_data(user),
                    user_container)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)
        
    def get_add_schema(self):
        """Get the list of attributes we need to ask when adding a new
           user.
        """
        server = self.setup_server()
        
        # FIXME: Hardcoded and designed for the TurboGears GUI. Do we want
        # this for the CLI as well?
        try:
            result = server.get_add_schema()
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)
      
        return ipautil.unwrap_binary_data(result)
    
    def get_all_users (self):
        """Return a list containing a User object for each existing user."""
    
        server = self.setup_server()
        try:
            result = server.get_all_users()
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)
    
        return ipautil.unwrap_binary_data(result)

    def find_users (self, criteria, sattrs=None, searchlimit=0):
        """Return a list: counter followed by a User object for each user that
           matches the criteria. If the results are truncated, counter will
           be set to -1"""
    
        server = self.setup_server()
        try:
            # None values are not allowed in XML-RPC
            if sattrs is None:
                sattrs = "__NONE__"
            result = server.find_users(criteria, sattrs, searchlimit)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)
    
        return ipautil.unwrap_binary_data(result)

    def update_user(self,olduser,newuser):
        """Update an existing user. olduser and newuser are dicts of attributes"""
        server = self.setup_server()
    
        try:
            result = server.update_user(ipautil.wrap_binary_data(olduser),
                    ipautil.wrap_binary_data(newuser))
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def delete_user(self,uid):
        """Delete a user. uid is the uid of the user to delete."""
        server = self.setup_server()
    
        try:
            result = server.delete_user(uid)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return result

    def modifyPassword(self,uid,oldpass,newpass):
        """Modify a user's password"""
        server = self.setup_server()

        if oldpass is None:
            oldpass = "__NONE__"
    
        try:
            result = server.modifyPassword(uid,oldpass,newpass)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return result

    def mark_user_deleted(self,uid):
        """Mark a user as deleted/inactive"""
        server = self.setup_server()
    
        try:
            result = server.mark_user_deleted(uid)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

# Group support
        
    def get_group_by_cn(self,cn,sattrs=None):
        """Get a specific group. If sattrs is not None then only those
           attributes will be returned, otherwise all available
           attributes are returned. The result is a dict."""
        server = self.setup_server()
        if sattrs is None:
            sattrs = "__NONE__"
        try:
            result = server.get_group_by_cn(cn, sattrs)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)
        
    def get_group_by_dn(self,dn,sattrs=None):
        """Get a specific group. If sattrs is not None then only those
           attributes will be returned, otherwise all available
           attributes are returned. The result is a dict."""
        server = self.setup_server()
        if sattrs is None:
            sattrs = "__NONE__"
        try:
            result = server.get_group_by_dn(dn, sattrs)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def get_groups_by_member(self,member_dn,sattrs=None):
        """Gets the groups that member_dn belongs to.
           If sattrs is not None then only those
           attributes will be returned, otherwise all available
           attributes are returned. The result is a list of dicts."""
        server = self.setup_server()
        if sattrs is None:
            sattrs = "__NONE__"
        try:
            result = server.get_groups_by_member(member_dn, sattrs)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def add_group(self,group,group_container=None):
        """Add a new group. Takes as input a dict where the key is the
           attribute name and the value is either a string or in the case
           of a multi-valued field a list of values"""
        server = self.setup_server()

        if group_container is None:
            group_container = "__NONE__"
    
        try:
            result = server.add_group(ipautil.wrap_binary_data(group),
                    group_container)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

    def find_groups (self, criteria, sattrs=None, searchlimit=0):
        """Return a list containing a Group object for each group that matches
           the criteria."""
    
        server = self.setup_server()
        try:
            # None values are not allowed in XML-RPC
            if sattrs is None:
                sattrs = "__NONE__"
            result = server.find_groups(criteria, sattrs, searchlimit)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)
    
        return ipautil.unwrap_binary_data(result)

    def add_user_to_group(self, user, group):
        """Add a user to an existing group.
           user is a uid of the user to add
           group is the cn of the group to be added to
        """
        server = self.setup_server()
        try:
            result = server.add_user_to_group(ipautil.wrap_binary_data(user),
                    ipautil.wrap_binary_data(group))
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)
    
        return ipautil.unwrap_binary_data(result)

    def add_users_to_group(self, users, group):
        """Add several users to an existing group.
           user is a list of the uids of the users to add
           group is the cn of the group to be added to

           Returns a list of the users that were not added.
        """
        server = self.setup_server()
        try:
            result = server.add_users_to_group(ipautil.wrap_binary_data(users),
                    ipautil.wrap_binary_data(group))
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)
    
        return ipautil.unwrap_binary_data(result)

    def remove_user_from_group(self, user, group):
        """Remove a user from an existing group.
           user is a uid of the user to remove
           group is the cn of the group to be removed from
        """
        server = self.setup_server()
        try:
            result = server.remove_user_from_group(ipautil.wrap_binary_data(user),
                    ipautil.wrap_binary_data(group))
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)
    
        return ipautil.unwrap_binary_data(result)

    def remove_users_from_group(self, users, group):
        """Remove several users from an existing group.
           user is a list of the uids of the users to remove
           group is the cn of the group to be removed from

           Returns a list of the users that were not removed.
        """
        server = self.setup_server()
        try:
            result = server.remove_users_from_group(
                    ipautil.wrap_binary_data(users),
                    ipautil.wrap_binary_data(group))
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)
    
        return ipautil.unwrap_binary_data(result)

    def update_group(self,oldgroup,newgroup):
        """Update an existing group. oldgroup and newgroup are dicts of attributes"""
        server = self.setup_server()
    
        try:
            result = server.update_group(ipautil.wrap_binary_data(oldgroup),
                    ipautil.wrap_binary_data(newgroup))
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def delete_group(self,group_cn):
        """Delete a group. group_cn is the cn of the group to be deleted."""
        server = self.setup_server()
    
        try:
            result = server.delete_group(group_cn)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)

        return ipautil.unwrap_binary_data(result)

    def add_group_to_group(self, group_cn, tgroup_cn):
        """Add a group to an existing group.
           group_cn is a cn of the group to add
           tgroup_cn is the cn of the group to be added to
        """
        server = self.setup_server()
        try:
            result = server.add_group_to_group(group_cn, tgroup_cn)
        except xmlrpclib.Fault, fault:
            raise ipaerror.gen_exception(fault.faultCode, fault.faultString)
        except socket.error, (value, msg):
            raise xmlrpclib.Fault(value, msg)
    
        return ipautil.unwrap_binary_data(result)
