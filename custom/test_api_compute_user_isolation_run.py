# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os.path
import json
import six
import sys
import time

from oslo_log import log as logging
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import test

CONF = config.CONF
file_path='/tmp/tempest_temp_info_wXBQq8Vn'
LOG = logging.getLogger(__name__)


class IsolationTestRun(base.BaseV2ComputeTest):

    credentials = ['primary']

    @classmethod
    def skip_checks(cls):
        super(IsolationTestRun, cls).skip_checks()
        if not CONF.service_available.glance:
            raise cls.skipException('Glance is not available.')

    @classmethod
    def setup_credentials(cls):
        # No network resources required for this test
        cls.set_network_resources()
        super(IsolationTestRun, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(IsolationTestRun, cls).setup_clients()
        cls.client = cls.os.servers_client
        cls.compute_images_client = cls.os.compute_images_client
        cls.glance_client = cls.os.image_client
        cls.keypairs_client = cls.os.keypairs_client
        cls.security_client = cls.os.compute_security_groups_client
        cls.rule_client = cls.os.compute_security_group_rules_client

    @classmethod
    def resource_setup(cls):
        super(IsolationTestRun, cls).resource_setup()

        print "waiting..."
        while not os.path.exists(file_path):
            time.sleep(3)
        f = open(file_path)
        fileinfo = json.load(f)
        f.close()

        cls.server=fileinfo['server']
        cls.image=fileinfo['image']
        cls.keypairname=fileinfo['keypairname']
        cls.security_group=fileinfo['security_group']
        cls.rule=fileinfo['rule']


    @classmethod
    def resource_cleanup(cls):
        #os.remove(file_path)
        super(IsolationTestRun, cls).resource_cleanup()

###############################################################################

    def test_get_server_for_alt_account(self):
        self.assertTrue(self.client.show_server, self.server['id'])

    @test.attr(type=['negative'])
    def test_delete_server_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden, self.client.delete_server,
                          self.server['id'])

    @test.attr(type=['negative'])
    def test_update_server_for_alt_account_fails(self):
        # An update server request for another user's server should fail
        self.assertRaises(lib_exc.Forbidden, self.client.update_server,
                          self.server['id'], name='test')

    def test_list_server_addresses_for_alt_account(self):
        self.assertTrue(self.client.list_addresses, self.server['id'])

    def test_list_server_addresses_by_network_for_alt_account(self):
        server_id = self.server['id']
        self.assertTrue(self.client.list_addresses_by_network, self.server['id'])

    @test.attr(type=['negative'])
    def test_change_password_for_alt_account_fails(self):
        # A change password request for another user's server should fail
        self.assertRaises(lib_exc.Forbidden, self.client.change_password,
                          self.server['id'], adminPass='newpass')

    @test.attr(type=['negative'])
    def test_reboot_server_for_alt_account_fails(self):
        # A reboot request for another user's server should fail
        self.assertRaises(lib_exc.Forbidden, self.client.reboot_server,
                          self.server['id'], type='HARD')

    @test.attr(type=['negative'])
    def test_rebuild_server_for_alt_account_fails(self):
        # A rebuild request for another user's server should fail
        self.assertRaises(lib_exc.Forbidden, self.client.rebuild_server,
                          self.server['id'], self.image_ref_alt)

    @test.attr(type=['negative'])
    def test_resize_server_for_alt_account_fails(self):
        # A resize request for another user's server should fail
        self.assertRaises(lib_exc.Forbidden, self.client.resize_server,
                          self.server['id'], self.flavor_ref_alt)

    @test.attr(type=['negative'])
    def test_create_image_for_alt_account_fails(self):
        # A create image request for another user's server should fail
        self.assertRaises(lib_exc.Forbidden,
                          self.compute_images_client.create_image,
                          self.server['id'], name='testImage')

    @test.attr(type=['negative'])
    def test_create_server_with_unauthorized_image_fails(self):
        # Server creation with another user's image should fail
        self.assertRaises(lib_exc.BadRequest, self.client.create_server,
                          name='test', imageRef=self.image['id'],
                          flavorRef=self.flavor_ref)

    @test.attr(type=['negative'])
    def test_get_keypair_of_alt_account_fails(self):
        # A GET request for another user's keypair should fail
        self.assertRaises(lib_exc.NotFound,
                          self.keypairs_client.show_keypair,
                          self.keypairname)

    @test.attr(type=['negative'])
    def test_delete_keypair_of_alt_account_fails(self):
        # A DELETE request for another user's keypair should fail
        self.assertRaises(lib_exc.NotFound,
                          self.keypairs_client.delete_keypair,
                          self.keypairname)

    def test_get_image_for_alt_account(self):
        self.assertTrue(self.compute_images_client.show_image,
                        self.image['id'])

#    @test.attr(type=['negative'])
#    def test_delete_image_for_alt_account_fails(self):
#        # A DELETE request for another user's image should fail
#        self.assertRaises(lib_exc.NotFound,
#                          self.compute_images_client.delete_image,
#                          self.image['id'])

    def test_get_security_group_of_alt_account(self):
        self.assertTrue(self.security_client.show_security_group,
                        self.security_group['id'])

#    def test_delete_security_group_of_alt_account_fails(self):
#        # A DELETE request for another user's security group should fail
#        self.assertRaises(lib_exc.NotFound,
#                          self.security_client.delete_security_group,
#                          self.security_group['id'])

#    def test_delete_security_group_rule_of_alt_account_fails(self):
#        # A DELETE request for another user's security group rule
#        # should fail
#        self.assertRaises(lib_exc.NotFound,
#                          self.rule_client.delete_security_group_rule,
#                          self.rule['id'])

    def test_set_metadata_of_alt_account_server_fails(self):
        # A set metadata for another user's server should fail
        req_metadata = {'meta1': 'tempest-server-data1', 'meta2': 'tempest-server-data2'}
        self.assertRaises(lib_exc.Forbidden,
                          self.client.set_server_metadata,
                          self.server['id'],
                          req_metadata)

#    def test_set_metadata_of_alt_account_image_fails(self):
#        # A set metadata for another user's image should fail
#        req_metadata = {'meta1': 'tempest-image-value1', 'meta2': 'tempest-image-value2'}
#        self.assertRaises(lib_exc.Forbidden,
#                          self.compute_images_client.set_image_metadata,
#                          self.image['id'], req_metadata)

    def test_get_metadata_of_alt_account_server_fails(self):
        # A get metadata for another user's server should fail
        self.assertRaises(lib_exc.Forbidden,
                          self.client.show_server_metadata_item,
                          self.server['id'], 'meta1')

    def test_get_metadata_of_alt_account_image_fails(self):
        # A get metadata for another user's image should fail
        self.assertRaises(
            lib_exc.NotFound,
            self.compute_images_client.show_image_metadata_item,
            self.image['id'], 'meta1')

    def test_delete_metadata_of_alt_account_server_fails(self):
        # A delete metadata for another user's server should fail
        self.assertRaises(lib_exc.Forbidden,
                          self.client.delete_server_metadata_item,
                          self.server['id'], 'meta1')

#    def test_delete_metadata_of_alt_account_image_fails(self):
#        # A delete metadata for another user's image should fail
#        self.assertRaises(
#            lib_exc.NotFound,
#            self.compute_images_client.delete_image_metadata_item,
#            self.image['id'], 'meta1')

    def test_get_console_output_of_alt_account_server_fails(self):
        # A Get Console Output for another user's server should fail
        self.assertRaises(lib_exc.Forbidden,
                          self.client.get_console_output,
                          self.server['id'], length=10)

##EOF
