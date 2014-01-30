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
from filecmp import dircmp
import glob
import json
import logging
import os
import shutil
import sys
import subprocess


from saltmc import exceptions


LOG = logging.getLogger(__name__)


def read_json(path):
    """Simply read a json file and return it."""
    with open(path) as fh:
        contents = fh.read()
        return json.loads(contents)


def is_identical(c):
    if c is None or c.right is None:
        return False
    if c.left_only or c.right_only or c.diff_files:
        return False
    else:
        return True


def compare_directory(a, b):
    return dircmp(a, b)


def get_installed_formulas(directory):
    """
    Get currently installed formulas.
    """
    data = {}

    directories = glob.glob(directory + '/*/init.sls')
    for sls in directories:
        sls_dir = os.path.dirname(sls)
        data[os.path.basename(sls_dir)] = sls_dir
    return data


def get_cache_items(cache_directory):
    # TODO(ekarlso): Fix this to eventually support files as well ?
    directories = glob.glob(cache_directory + '/*')
    return dict([(os.path.basename(d), d) for d in directories])


def call_subprocess(cmd, show_stdout=True,
                    filter_stdout=None, cwd=None,
                    raise_on_returncode=True,
                    command_desc=None,
                    extra_environ=None):
    if command_desc is None:
        cmd_parts = []
        for part in cmd:
            if ' ' in part or '\n' in part or '"' in part or "'" in part:
                part = '"%s"' % part.replace('"', '\\"')
            cmd_parts.append(part)
        command_desc = ' '.join(cmd_parts)
    if show_stdout:
        stdout = None
    else:
        stdout = subprocess.PIPE
    LOG.debug("Running command %s" % command_desc)
    env = os.environ.copy()
    if extra_environ:
        env.update(extra_environ)
    try:
        proc = subprocess.Popen(
            cmd, stderr=subprocess.STDOUT, stdin=None, stdout=stdout,
            cwd=cwd, env=env)
    except Exception:
        e = sys.exc_info()[1]
        LOG.error(
            "Error %s while executing command %s" % (e, command_desc))
        raise
    all_output = []
    if stdout is not None:
        stdout = proc.stdout
        while 1:
            line = str(stdout.readline())
            if not line:
                break
            line = line.rstrip()
            all_output.append(line + '\n')
            if filter_stdout:
                level = filter_stdout(line)
                if isinstance(level, tuple):
                    level, line = level
                LOG.log(level, line)
                if not LOG.stdout_level_matches(level):
                    LOG.show_progress()
            else:
                LOG.info(line)
    else:
        returned_stdout, returned_stderr = proc.communicate()
        all_output = [returned_stdout or '']
    proc.wait()
    if proc.returncode:
        if raise_on_returncode:
            if all_output:
                msg = 'Complete output from command %s:'
                LOG.info(msg % command_desc)
                LOG.info('\n'.join(all_output) +
                         '\n----------------------------------------')
            raise exceptions.InstallationError(
                "Command %s failed with error code %s in %s"
                % (command_desc, proc.returncode, cwd))
        else:
            LOG.warn(
                "Command %s had error code %s in %s"
                % (command_desc, proc.returncode, cwd))
    if stdout is not None:
        return ''.join(all_output)


def get_pathext(default_pathext=None):
    """Returns the path extensions from environment or a default"""
    if default_pathext is None:
        default_pathext = os.pathsep.join(['.COM', '.EXE', '.BAT', '.CMD'])
    pathext = os.environ.get('PATHEXT', default_pathext)
    return pathext


def find_command(cmd, paths=None, pathext=None):
    """Searches the PATH for the given command and returns its path"""
    if paths is None:
        paths = os.environ.get('PATH', '').split(os.pathsep)
    if isinstance(paths, basestring):
        paths = [paths]
    # check if there are funny path extensions for executables, e.g. Windows
    if pathext is None:
        pathext = get_pathext()
    pathext = [ext for ext in pathext.lower().split(os.pathsep) if len(ext)]
    # don't use extensions if the command ends with one of them
    if os.path.splitext(cmd)[1].lower() in pathext:
        pathext = ['']
    # check if we find the command on PATH
    for path in paths:
        # try without extension first
        cmd_path = os.path.join(path, cmd)
        for ext in pathext:
            # then including the extension
            cmd_path_ext = cmd_path + ext
            if os.path.isfile(cmd_path_ext):
                return cmd_path_ext
        if os.path.isfile(cmd_path):
            return cmd_path
    raise BadCommand('Cannot find command %r' % cmd)


def ask_path_exists(message, options):
    for action in os.environ.get('PIP_EXISTS_ACTION', '').split():
        if action in options:
            return action
    return ask(message, options)


def ask(message, options):
    """Ask the message interactively, with the given possible responses"""
    while 1:
        if os.environ.get('SALTMC_NO_INPUT'):
            msg = 'No input was expected ($SALTMC_NO_INPUT set); question: %s'
            raise Exception(msg % message)
        response = raw_input(message)
        response = response.strip().lower()
        if response not in options:
            msg = 'Your response (%r) was not a expected response: %s'
            print(msg % (response, ', '.join(options)))
        else:
            return response


def display_path(path):
    """Gives the display value for a given path, making it relative to cwd
    if possible."""
    path = os.path.normcase(os.path.abspath(path))
    if path.startswith(os.getcwd() + os.path.sep):
        path = '.' + path[len(os.getcwd()):]
    return path


def rmtree(dir, ignore_errors=False):
    shutil.rmtree(dir, ignore_errors=ignore_errors,
                  onerror=rmtree_errorhandler)


def rmtree_errorhandler(func, path, exc_info):
    """On Windows, the files in .svn are read-only, so when rmtree() tries to
    remove them, an exception is thrown.  We catch that here, remove the
    read-only attribute, and hopefully continue without problems."""
    exctype, value = exc_info[:2]
    if not ((exctype is WindowsError and value.args[0] == 5) or  # others
            (exctype is OSError and value.args[0] == 13) or  # python2.4
            (exctype is PermissionError and value.args[3] == 5)  # python3.3
            ):
        raise
    # file type should currently be read only
    if ((os.stat(path).st_mode & stat.S_IREAD) != stat.S_IREAD):
        raise
    # convert to read/write
    os.chmod(path, stat.S_IWRITE)
    # use the original function to repeat the operation
    func(path)
