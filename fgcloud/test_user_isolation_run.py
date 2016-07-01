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

import json
import os.path
import testtools
import time
from oslo_log import log as logging
from tempest.api.compute import base
from tempest import config
from tempest.common.utils import data_utils
from tempest.lib import exceptions as lib_exc
from tempest import test

CONF = config.CONF
LOG = logging.getLogger(__name__)
file_path = "/tmp/tempest_" + CONF.compute.image_ref

class UserIsolationRun(base.BaseV2ComputeTest):

    credentials = ['primary']

    @classmethod
    def skip_checks(cls):
        super(UserIsolationRun, cls).skip_checks()
        if not CONF.service_available.glance:
            skip_msg = ("%s skipped as Glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)
        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_credentials(cls):
        # No network resources required for this test
        cls.set_network_resources()
        super(UserIsolationRun, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(UserIsolationRun, cls).setup_clients()
        cls.client = cls.os.servers_client
        cls.compute_images_client = cls.os.compute_images_client
        cls.image_client = cls.os.image_client
        cls.keypairs_client = cls.os.keypairs_client
        cls.security_client = cls.os.compute_security_groups_client
        cls.rule_client = cls.os.compute_security_group_rules_client
        cls.snapshots_client = cls.os.snapshots_extensions_client
        if CONF.volume_feature_enabled.api_v1:
            cls.volumes_client = cls.os.volumes_client
        else:
            cls.volumes_client = cls.os.volumes_v2_client

    @classmethod
    def resource_setup(cls):
        super(UserIsolationRun, cls).resource_setup()

        LOG.info("Starting VM_Run")
        name = data_utils.rand_name('VM_Run')
        server = cls.create_test_server(name=name, wait_until='ACTIVE')
        cls.server_run = cls.client.show_server(server['id'])['server']
        LOG.info("VM_Run started and active ")

        LOG.info("Waiting for VM_Setup to get ready...")
        while not os.path.exists(file_path):
            time.sleep(3)

        f = open(file_path)
        fileinfo = json.load(f)
        f.close()

        cls.server = fileinfo['server']
        cls.image = fileinfo['image']
        cls.keypairname = fileinfo['keypairname']
        cls.security_group = fileinfo['security_group']
        cls.rule = fileinfo['rule']
        cls.volume1 = fileinfo['volume1']
        cls.metadata = fileinfo['metadata']
        cls.volume2 = fileinfo['volume2']
        if not CONF.volume_feature_enabled.snapshot:
            LOG.info("Snapshot skipped as volume snapshotting is not enabled")
        else:
            cls.snapshot = fileinfo['snapshot']
        cls.attachment = fileinfo['attachment']

        LOG.info("Running isolation tests from user B...")

    @classmethod
    def resource_cleanup(cls):
        if hasattr(cls, 'server'):
            cls.client.delete_server(cls.server_run['id'])
        os.remove(file_path)
        super(UserIsolationRun, cls).resource_cleanup()

    @test.idempotent_id('1fb19bb3-d40b-49e3-b6f8-04e8ca354067')
    def test_get_server_for_alt_account(self):
        self.assertTrue(self.client.show_server, self.server['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('1e66dee1-1498-4ebb-9304-b952bf4e3ee3')
    def test_update_server_for_alt_account_fails(self):
        # An update server request for another user's server should fail
        self.assertRaises(lib_exc.Forbidden, self.client.update_server,
                          self.server['id'], name='tempest_test_rename')

    @test.idempotent_id('b293feda-861a-4d16-9a0d-6f2341a19abe')
    def test_list_server_addresses_for_alt_account(self):
        self.assertTrue(self.client.list_addresses, self.server['id'])

    @test.idempotent_id('19947773-5c36-49d1-97f1-069308215415')
    def test_list_server_addresses_by_network_for_alt_account(self):
        server_id = self.server['id']
        self.assertTrue(self.client.list_addresses_by_network, server_id)

    @test.attr(type=['negative'])
    @test.idempotent_id('6a990add-e4cc-4c99-99f7-b06c5ab88b5f')
    def test_change_password_for_alt_account_fails(self):
        # A change password request for another user's server should fail
        self.assertRaises(lib_exc.Forbidden, self.client.change_password,
                          self.server['id'], adminPass='newpass')

    @test.attr(type=['negative'])
    @test.idempotent_id('caa72f38-63e4-41ce-bfd8-b134d22e919e')
    def test_show_password_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden, self.client.show_password,
                          self.server['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('088de95a-825c-4773-bf7d-26d9d830f741')
    def test_create_image_for_alt_account_fails(self):
        # A create image request for another user's server should fail
        self.assertRaises(lib_exc.Forbidden,
                          self.compute_images_client.create_image,
                          self.server['id'], name='testImage')

    @test.attr(type=['negative'])
    @test.idempotent_id('ebb37040-ea80-4d73-811f-7cb9a4846a7e')
    def test_get_keypair_of_alt_account_fails(self):
        # A GET request for another user's keypair should fail
        self.assertRaises(lib_exc.NotFound,
                          self.keypairs_client.show_keypair,
                          self.keypairname)

    @test.attr(type=['negative'])
    @test.idempotent_id('35c4d575-423d-4b8c-ab2a-3447b9677422')
    def test_delete_keypair_of_alt_account_fails(self):
        # A DELETE request for another user's keypair should fail
        self.assertRaises(lib_exc.NotFound,
                          self.keypairs_client.delete_keypair,
                          self.keypairname)

    @test.idempotent_id('383c3525-48e9-47b1-9533-1eed490402de')
    def test_get_image_for_alt_account(self):
        self.assertTrue(self.compute_images_client.show_image,
                        self.image['id'])

    @test.idempotent_id('137f2014-79a7-4dcf-8e1c-710893b12d1f')
    def test_get_security_group_of_alt_account(self):
        self.assertTrue(self.security_client.show_security_group,
                        self.security_group['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('c5011b7a-8e11-4f05-86fe-8e1b8b0ab5b1')
    def test_set_metadata_of_alt_account_server_fails(self):
        # A set metadata for another user's server should fail
        req_metadata = {'meta1': 'tempest-server-data1',
                        'meta2': 'tempest-server-data2'}
        self.assertRaises(lib_exc.Forbidden,
                          self.client.set_server_metadata,
                          self.server['id'],
                          req_metadata)

    @test.attr(type=['negative'])
    @test.idempotent_id('36c0b45f-cac3-4aa3-95aa-6722d697de9b')
    def test_get_metadata_of_alt_account_server_fails(self):
        # A get metadata for another user's server should fail
        try:
            self.client.show_server_metadata_item
        except lib_exc.Forbidden:
            self.fail('Forbidden')
        except lib_exc.NotFound:
            self.fail('NotFound')

    @test.attr(type=['negative'])
    @test.idempotent_id('197f8b8e-d41d-4060-9266-f60b2e179a26')
    def test_get_metadata_of_alt_account_image_fails(self):
        # A get metadata for another user's image should fail
        self.assertRaises(
            lib_exc.NotFound,
            self.compute_images_client.show_image_metadata_item,
            self.image['id'], 'meta1')

    @test.attr(type=['negative'])
    @test.idempotent_id('bc8dd9e7-86a4-4bbf-858b-6eb03c9f5655')
    def test_delete_metadata_of_alt_account_server_fails(self):
        # A delete metadata for another user's server should fail
        self.assertRaises(lib_exc.Forbidden,
                          self.client.delete_server_metadata_item,
                          self.server['id'], 'meta1')

    @test.attr(type=['negative'])
    @test.idempotent_id('edb92ce6-b116-472f-9134-335e9195afb6')
    def test_delete_metadata_of_alt_account_image_fails(self):
        # A delete metadata for another user's image should fail
        self.assertRaises(
            lib_exc.NotFound,
            self.compute_images_client.delete_image_metadata_item,
            self.image['id'], 'meta1')

    @test.attr(type=['negative'])
    @test.idempotent_id('0d0f26c4-f69a-4e71-abe8-a342c6975f14')
    def test_get_console_output_of_alt_account_server_fails(self):
        # A Get Console Output for another user's server should fail
        self.assertRaises(lib_exc.Forbidden,
                          self.client.get_console_output,
                          self.server['id'], length=10)

    @test.attr(type=['negative'])
    @test.idempotent_id('7aafc3bd-e664-4f69-b122-6a6e3e551188')
    def test_get_vnc_console_of_alt_account_server_fails(self):
        self.assertRaises(lib_exc.Forbidden, self.client.get_vnc_console,
                          self.server['id'],
                          type='novnc')

    @test.attr(type=['negative'])
    @test.idempotent_id('3080119d-6fa1-489d-9621-f983aff725ed')
    def test_rebuild_server_for_alt_account_fails(self):
        # A rebuild request for another user's server should fail
        self.assertRaises(lib_exc.Forbidden, self.client.rebuild_server,
                          self.server['id'], self.image_ref_alt)

    @test.attr(type=['negative'])
    @test.idempotent_id('827625bb-048d-4cf3-b489-2b36594fb5f8')
    def test_resize_server_for_alt_account_fails(self):
        # A resize request for another user's server should fail
        self.assertRaises(lib_exc.Forbidden, self.client.resize_server,
                          self.server['id'], self.flavor_ref_alt)

    @test.attr(type=['negative'])
    @test.idempotent_id('9df2b0f5-ea2b-41ff-8401-0d1a00dc864a')
    def test_reboot_server_for_alt_account_fails(self):
        # A reboot request for another user's server should fail
        self.assertRaises(lib_exc.Forbidden, self.client.reboot_server,
                          self.server['id'], type='HARD')

    @test.attr(type=['negative'])
    @test.idempotent_id('5c968a59-aeae-4211-b227-adcc9ecd622c')
    def test_delete_server_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden, self.client.delete_server,
                          self.server['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('65e47d5a-8bd4-406b-8d19-52c3eba6f65a')
    def test_start_server_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden, self.client.start_server,
                          self.server['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('56e11972-faac-4487-9420-031ee379319c')
    def test_stop_server_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden, self.client.stop_server,
                          self.server['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('7e921ec4-ecec-4a1b-b673-da2f9dc009cc')
    def test_lock_server_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden, self.client.lock_server,
                          self.server['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('68cfdda6-0475-4734-909d-b2fe21987347')
    def test_unlock_server_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden, self.client.unlock_server,
                          self.server['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('41b5975f-e140-4cc9-83af-a83b8b6cf278')
    def test_pause_server_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden, self.client.pause_server,
                          self.server['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('0a1c4f53-fa8a-4ae9-b5ab-e55e539024d1')
    def test_unpause_server_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden, self.client.unpause_server,
                          self.server['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('5af863a1-f10c-4a3a-a3de-2bf3506247f5')
    def test_suspend_server_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden, self.client.suspend_server,
                          self.server['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('4b93e4b9-b33f-4ff1-8cd0-5f1efe20624b')
    def test_resume_server_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden, self.client.resume_server,
                          self.server['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('1aea9960-897f-4273-ae69-bbd9bc45c359')
    def test_shelve_server_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden, self.client.shelve_server,
                          self.server['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('67e59d60-ccfc-443c-ac9b-9bcaf35044b6')
    def test_unshelve_server_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden, self.client.unshelve_server,
                          self.server['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('0309c7ef-27af-4934-9cc0-66b37085b227')
    def test_shelve_offload_server_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden, self.client.shelve_offload_server,
                          self.server['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('1c48d877-6f4b-480e-ab18-5fe26418bc0a')
    def test_attach_volume_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden, self.client.attach_volume,
                          self.server_run['id'],
                          volumeId=self.volume1['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('46e0198f-52e1-410f-8edc-a287b189d7b7')
    def test_update_volume_attachment_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden, self.client.update_attached_volume,
                          self.server['id'],
                          attachment_id=self.attachment['id'],
                          volumeId=self.volume1['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('2074a6b1-5d08-4724-bfc7-61b6247a017e')
    def test_detach_volume_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden, self.client.detach_volume,
                          self.server['id'],
                          self.volume2['id'])

    @test.attr(type=['negative'])
    @testtools.skipUnless(CONF.volume_feature_enabled.snapshot,
                          'Volume snapshotting is not available.')
    @test.idempotent_id('09cfd067-831a-47fc-ac07-13e05290cf30')
    def test_create_snapshot_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden,
                          self.snapshots_client.create_snapshot,
                          self.volume1['id'])

    @test.attr(type=['negative'])
    @testtools.skipUnless(CONF.volume_feature_enabled.snapshot,
                          'Volume snapshotting is not available.')
    @test.idempotent_id('e4fb10e9-a017-4c02-8299-bc361cf04828')
    def test_delete_snapshot_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden,
                          self.snapshots_client.delete_snapshot,
                          self.snapshot['id'])

    @test.attr(type=['negative'])
    @testtools.skipUnless(CONF.volume_feature_enabled.snapshot,
                          'Volume snapshotting is not available.')
    @test.idempotent_id('2cad9a8f-cc65-429c-a7d4-908bd86358f1')
    def test_get_snapshot_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden,
                          self.snapshots_client.show_snapshot,
                          self.snapshot['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('0bce9bd7-4032-4c81-b277-093bb9058219')
    def test_delete_volume_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden, self.volumes_client.delete_volume,
                          self.volume1['id'])

    @test.attr(type=['negative'])
    @test.idempotent_id('f9be1ab4-0975-4b6b-ae36-da4e7a576b24')
    def test_extend_volume_for_alt_account_fails(self):
        extend_size = int(self.volume1['size']) + 1
        self.assertRaises(lib_exc.Forbidden, self.volumes_client.extend_volume,
                          self.volume1['id'],
                          new_size=extend_size)

    @test.attr(type=['negative'])
    @test.idempotent_id('d279a2c0-f554-4ae9-9a39-2a5caf9fced3')
    def test_update_volume_metadata_for_alt_account_fails(self):
        metadata = {'new_meta': 'tempest-volume-metadata'}
        self.assertRaises(lib_exc.Forbidden,
                          self.volumes_client.update_volume_metadata,
                          self.volume1['id'],
                          metadata)

    @test.attr(type=['negative'])
    @test.idempotent_id('b4a11b21-72c6-4450-985c-6ea9bd0e6d36')
    def test_delete_volume_metadata_for_alt_account_fails(self):
        self.assertRaises(lib_exc.Forbidden,
                          self.volumes_client.delete_volume_metadata_item,
                          self.volume1['id'],
                          'vol_metadata')

# EOF
