try:
    import pkg_resources
    __version__ = pkg_resources.get_distribution('smartgadget').version
except (pkg_resources.DistributionNotFound, ImportError):
    __version__ = 'dev'