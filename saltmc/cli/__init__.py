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
from cliff.command import Command
import os

from saltmc import utils


class BaseCommand(Command):
    def post_execute(self, data):
        """
        Format the results locally if needed, by default we just return data

        :param data: Whatever is returned by self.execute()
        """
        return data

    def take_action(self, parsed_args):
        results = self.execute(parsed_args)
        return self.post_execute(results)

    def get_parser(self, prog_name):
        parser = super(BaseCommand, self).get_parser(prog_name)
        parser.add_argument(
            '--formula',
            help="Name of the formula to sync")
        parser.add_argument(
            '--source',
            help="Optional source of the formula")
        parser.add_argument(
            '--branch',
            default="master",
            help="Optional branch of the source")
        return parser

    def get_settings(self, args):
        """
        Fetches the settings from the deployment.read
        """
        settings = utils.read_json(self.app_args.spec)

        spec_dir = os.path.dirname(self.app_args.spec)

        # Handle directory setting
        settings.setdefault('directory', spec_dir + '/salt')
        settings['directory'] = os.path.realpath(settings['directory'])
        return settings
