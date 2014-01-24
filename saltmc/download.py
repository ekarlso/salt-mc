from saltmc.vcs import get_extensions


def get_schemes():
    schemes = ['http', 'https', 'file', 'ftp']
    for ext in get_extensions():
        schemes.extend(ext.plugin.schemes)
    return schemes


def is_url(name):
    """Returns true if the name looks like a URL"""
    if ':' not in name:
        return False
    scheme = name.split(':', 1)[0].lower()
    return scheme in get_schemes()
