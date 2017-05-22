#! /usr/bin/python
# -*- coding: utf-8 -*-

ETCD2 = 0
ETCD3 = 1


class NotSupportBackendError(Exception):
    pass


class DiscoveryFactory:
    def __init__(self):
        pass

    @classmethod
    def create(cls, backend, ip, port):
        if backend == ETCD2:
            pass
        elif backend == ETCD3:
            pass
        else:
            raise NotSupportBackendError('not support backend %s' % backend)
