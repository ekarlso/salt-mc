import logging
import requests


LOG = logging.getLogger(__name__)


class RequestsFetcher(object):
    schemes = ('http', 'https')

    def __init__(self, url=None):
        self.url = url

    def fetch(self, dest):
        LOG.debug("Fetching %s to %s" % (self.url, dest))
