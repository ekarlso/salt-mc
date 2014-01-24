from testtools import TestCase

from saltmc.link import Link


class LinkTest(TestCase):
    def test_schemes(self):
        l = Link('git://i.io/test')
        self.assertEqual('git', l.scheme)

        l = Link('git+http://i.io/test')
        self.assertEqual('git+http', l.scheme)

    def test_no_scheme(self):
        l = Link('git/localhost')
        self.assertEqual('', l.scheme)
