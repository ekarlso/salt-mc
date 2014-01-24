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
from cliff.lister import Lister

from saltmc.cli import BaseCommand
from saltmc import utils


class Status(BaseCommand, Lister):
    """
    Shows currently installed versions
    """
    def execute(self, parsed_args):
        settings = self.get_settings(parsed_args)

        # Cached formulas aka downloaded
        cache_items = utils.get_cache_items(self.app_args.cache_dir)

        # Existing formulas
        formula_dirs = utils.get_installed_formulas(
            settings['directory'])

        data = []
        for formula_name in settings.get('formulas', {}):
            cache_dir = cache_items.get(formula_name)
            formula_dir = formula_dirs.get(formula_name)

            if cache_dir and formula_dir:
                comparison = utils.compare_directory(
                    cache_dir + '/' + formula_name, formula_dir)

            data.append([
                formula_name,
                cache_items.get(formula_name),
                formula_dirs.get(formula_name),
                utils.is_identical(comparison)])

        return ('Name', 'Cached', 'Present', 'Up to Date'), data
