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
import logging
import shutil
import os

from saltmc.cli import BaseCommand
from saltmc import sync
from saltmc import utils


LOG = logging.getLogger(__name__)


class Sync(BaseCommand):
    """
    Sync a deployment using a specification or add / install a specific
    formula
    """
    def take_action(self, parsed_args):
        settings = self.get_settings(parsed_args)

        formulas = settings.get('formulas', {})

        sync.fetch_all(formulas, self.app_args.cache_dir)

        for name, data in formulas.items():
            source_top = os.path.join(self.app_args.cache_dir, name)

            formula_dirs = utils.get_installed_formulas(
                settings['directory'])

            # It exists - wipe it out before copying.
            destination = os.path.join(settings['directory'], name)

            if name in formula_dirs or os.path.exists(destination):
                LOG.debug("Deleting existing formula dir %s" % destination)
                utils.rmtree(destination)

            # The stuff we're copying in is located typically in a subdirectory
            # of the cache source directory.
            source = os.path.join(source_top, name)
            LOG.debug("Copying new formula from %s to %s" %
                      (source, destination))
            shutil.copytree(source, destination)
