# -*- coding: utf-8 -*-


class Discovery(object):
    def register_service(self, name, ip, port, ttl):
        raise NotImplementedError()

    def refresh_service(self, name, ttl):
        raise NotImplementedError()

    def unregister_service(self, name):
        raise NotImplementedError()

    def get_service_address(self, name):
        raise NotImplementedError()

    def watch_service_address(self, name):
        raise NotImplementedError()

    def put(self, name, key, value):
        raise NotImplementedError()

    def get(self, name, key):
        raise NotImplementedError()

    def delete(self, name, key):
        raise NotImplementedError()

    def watch(self, name, key):
        raise NotImplementedError()
