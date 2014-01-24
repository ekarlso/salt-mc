import os
import logging
import shutil
import stevedore
import urllib
import urlparse


from saltmc import utils


LOG = logging.getLogger(__name__)


def get_extensions():
    return stevedore.ExtensionManager('saltmc.fetchers').extensions


def get_by_name(name):
    dm = stevedore.DriverManager('saltmc.fetchers', name)
    return dm.driver


def get_by_directory(path):
    for e in get_extensions():
        if os.path.exists(path + '/' + e.plugin.dirname):
            return e.plugin
    else:
        raise NotImplementedError


def get_by_scheme(scheme, name=None):
    found = []
    for e in get_extensions():
        if name is not None and e.name == name:
            return e.plugin
        elif scheme in e.plugin.schemes:
            found.append(e)

    length = len(found)
    if length == 0:
        raise ValueError('No provider found')
    elif len(found) > 1:
        msg = 'Multiple providers (%s) found for scheme %s, provide name.'
        names = ", ".join([e.name for e in found])
        raise ValueError(msg % (names, scheme))
    return found[0].plugin


class Fetcher(object):
    """
    Base Fetcher
    """
    def __init__(self, url=None, *args, **kw):
        self.url = url
        self.args = args
        self.kw = kw

    def fetch(self, destionation):
        raise NotImplementedError


class VCSFetcher(Fetcher):
    name = ''
    dirname = ''

    def _is_local_repository(self, repo):
        """
           posix absolute paths start with os.path.sep,
           win32 ones ones start with drive (like c:\\folder)
        """
        drive, tail = os.path.splitdrive(repo)
        return repo.startswith(os.path.sep) or drive

    @property
    def cmd(self):
        if 'cmd' in self.kw:
            return self.kw['cmd']
        command = utils.find_command(self.name)
        LOG.info('Found command %r at %r' % (self.name, command))
        self.kw['cmd'] = command
        return command

    def get_url_rev(self):
        """
        Returns the correct repository URL and revision by parsing the given
        repository URL
        """
        msg = (
            "Sorry, '%s' is a malformed VCS url. "
            "The format is <vcs>+<protocol>://<url>, "
            "e.g. git+http://github.com/user/repo")
        assert '+' in self.url, msg % self.url
        url = self.url.split('+', 1)[1]
        scheme, netloc, path, query, frag = urlparse.urlsplit(url)
        rev = None
        if '@' in path:
            path, rev = path.rsplit('@', 1)
        url = urlparse.urlunsplit((scheme, netloc, path, query, ''))
        return url, rev

    def get_info(self, location):
        """
        Returns (url, revision), where both are strings
        """
        msg = 'Bad directory: %s' % location
        assert not location.rstrip('/').endswith(self.dirname), msg
        return self.get_url(location), self.get_revision(location)

    def normalize_url(self, url):
        """
        Normalize a URL for comparison by unquoting it and removing any
        trailing slash.
        """
        return urllib.unquote(url).rstrip('/')

    def compare_urls(self, url1, url2):
        """
        Compare two repo URLs for identity, ignoring incidental differences.
        """
        return (self.normalize_url(url1) == self.normalize_url(url2))

    def normalize_url(self, url):
        """
        Normalize a URL for comparison by unquoting it and removing any
        trailing slash.
        """
        return urllib.unquote(url).rstrip('/')

    def compare_urls(self, url1, url2):
        """
        Compare two repo URLs for identity, ignoring incidental differences.
        """
        return (self.normalize_url(url1) == self.normalize_url(url2))

    def update(self, dest, rev_options):
        """
        Update an already-existing repo to the given ``rev_options``.
        """
        raise NotImplementedError

    def check_destination(self, dest, url, rev_options, rev_display):
        """
        Prepare a location to receive a checkout/clone.

        Return True if the location is ready for (and requires) a
        checkout/clone, False otherwise.
        """
        checkout = True
        prompt = False
        if os.path.exists(dest):
            checkout = False
            if os.path.exists(os.path.join(dest, self.dirname)):
                existing_url = self.get_url(dest)
                if self.compare_urls(existing_url, url):
                    msg = '%s in %s exists, and has correct URL (%s)'
                    LOG.info(msg % (self.repo_name.title(),
                             utils.display_path(dest), url))
                    LOG.info('Updating %s %s%s' %
                             (utils.display_path(dest), self.repo_name,
                              rev_display))
                    self.update(dest, rev_options)
                else:
                    msg = '%s %s in %s exists with URL %s'
                    LOG.warn(msg % (self.name, self.repo_name,
                                    utils.display_path(dest), existing_url))
                    prompt = ('(s)witch, (i)gnore, (w)ipe, (b)ackup ',
                              ('s', 'i', 'w', 'b'))
            else:
                msg = 'Directory %s already exists, and is not a %s %s.'
                LOG.warn(msg % (dest, self.name, self.repo_name))
                prompt = ('(i)gnore, (w)ipe, (b)ackup ', ('i', 'w', 'b'))
        if prompt:
            msg = 'The plan is to install the %s repository %s'
            LOG.warn(msg % (self.name, url))
            response = utils.ask_path_exists(
                'What to do?  %s' % prompt[0], prompt[1])

            if response == 's':
                msg = 'Switching %s %s to %s%s'
                LOG.info(msg % (self.repo_name, utils.display_path(dest), url,
                         rev_display))
                self.switch(dest, url, rev_options)
            elif response == 'i':
                # do nothing
                pass
            elif response == 'w':
                LOG.warn('Deleting %s' % utils.display_path(dest))
                utils.rmtree(dest)
                checkout = True
            elif response == 'b':
                dest_dir = backup_dir(dest)
                msg = 'Backing up %s to %s'
                LOG.warn(msg % (utils.display_path(dest), dest_dir))
                shutil.move(dest, dest_dir)
                checkout = True
        return checkout

    def unpack(self, location):
        if os.path.exists(location):
            utils.rmtree(location)
        self.fetch(location)
