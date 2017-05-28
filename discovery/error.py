# -*- coding: utf-8 -*-


class DiscoveryError(Exception):
    pass


class ConnectionError(Exception):
    pass


class NotSupportBackendError(DiscoveryError):
    pass


class ServiceAlreadyExistError(DiscoveryError):
    pass


class ServiceNotExistError(DiscoveryError):
    pass


class ServiceAlreadyWatched(DiscoveryError):
    pass
