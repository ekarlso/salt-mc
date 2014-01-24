# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Author: Endre Karlson <endre.karlson@hp.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from cliff.app import App
from cliff.commandmanager import CommandManager
import logging
import os
import sys
#from saltmc import utils


class SaltManager(App):
    log = logging.getLogger(__name__)

    def __init__(self):
        super(SaltManager, self).__init__(
            description='CMD utils to help manage a salt deployment repo.',
            version='0.1',
            command_manager=CommandManager('saltmc.cli'))

        self.log = logging.getLogger(__name__)

    def build_option_parser(self, description, version):
        parser = super(SaltManager, self).build_option_parser(
            description, version)

        default_spec = os.getcwd() + '/deployment.json'
        parser.add_argument(
            '--spec',
            help="Deployment spec file",
            default=default_spec)
        parser.add_argument(
            '--cache-dir',
            help="Cache directory (Where we store modules...)",
            default=os.path.expanduser('~/.cache/saltmc'))
        return parser


def main():
    app = SaltManager()
    sys.exit(app.run(sys.argv[1:]))
