# -*- coding: utf-8 -*-


class Discovery(object):
    def register_service(self, name, ip_port, data='', ttl=None):
        raise NotImplementedError()

    def refresh_service(self, name, ttl):
        raise NotImplementedError()

    def unregister_service(self, name):
        raise NotImplementedError()

    def update_service(self, name, ip_port, data, ttl=None):
        raise NotImplementedError()

    def unregister_service(self, name):
        raise NotImplementedError()

    def get_service(self, name):
        raise NotImplementedError()

    def watch_service(self, name, callback):
        raise NotImplementedError()

    def unwatch_service(self, name):
        raise NotImplementedError()
