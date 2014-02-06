import os

from saltmc import fetchers
from saltmc import link


def fetch_all(formulas, cache_dir):
    """
    Sync all the formulas and their wanted versions.
    """
    for name, data in formulas.items():
        # TODO(ekarlso): Limk creation should maybe happen in get_settings() ?
        l = link.Link(data)

        fetcher = fetchers.get_by_scheme(l.scheme)(l.url)

        source_top = os.path.join(cache_dir, name)
        # This should download / clone or whatever and unpack if a file
        # to the source_top directory within the cache directory
        fetcher.fetch(source_top)
