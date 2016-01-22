# Copyright 2013 NEC Corporation
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

from oslo_log import log as logging
# from tempest.common import custom_matchers
# from tempest.common import waiters
from tempest import config
# from tempest import exceptions
from tempest.scenario import manager
from tempest import test
import time
CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestBasicValues(manager.ScenarioTest):

    """This is a basic values test.

    This test works:
    * across multiple components
    * as a regular user
    * check command outputs

    Steps:
    1. Check running services activated in the configuration file

    """

    @test.idempotent_id('35e934c6-48e4-43c4-cbfa-b3e7f2c0000a')
    @test.services('compute', 'volume', 'image', 'network')
    def test_basic_values_true(self):
        time.sleep(2)
        LOG.info("info message in OK")
        LOG.warn("warn message in OK")
        LOG.critical("crit message in OK")
        self.assertEqual(4, 2 * 2)

    @test.idempotent_id('35e934c6-48e4-43c4-cbfa-b3e7f2cdad0a')
    @test.services('compute', 'volume', 'image', 'network')
    def test_basic_values_false(self):

        LOG.warn("warn message in FAILED 1")
        self.assertEqual(5, 2 * 2)

    @test.idempotent_id('35e934c6-48e4-43c4-cbfa-b3e7f2bdad0a')
    @test.services('compute', 'volume', 'image', 'network')
    def test_basic_values_false2(self):

        LOG.critical("crit message in FAILED 2")
        self.assertEqual(6, 2 * 2)

