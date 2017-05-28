#! /usr/bin/python
# -*- coding: utf-8 -*-
from error import *
from etcd2 import Etcd2Discovery

ETCD2 = 0
ETCD3 = 1


class DiscoveryFactory:
    def __init__(self):
        pass

    @classmethod
    def create(cls, backend, ip, port):
        if backend == ETCD2:
            return Etcd2Discovery(ip, port)
        elif backend == ETCD3:
            pass
        else:
            raise NotSupportBackendError('not support backend %s' % backend)


if __name__ == '__main__':
    def watch_callback(err, serv_name, ip_port, data):
        if err:
            print('watch service %s error' % serv_name)
        else:
            if ip_port is not None:
                print('service %s ip port change: ip %s, port %d' %
                      (serv_name, ip_port[0], ip_port[1]))
            if data is not None:
                print('service %s data change: %s' %
                      (serv_name, data))

    import time

    serv = DiscoveryFactory.create(ETCD2, '127.0.0.1', 2379)

    serv.register_service('test', ('127.0.0.1', 8080), 'test', 30)
    ip_port, data = serv.get_service('test')
    print('service ip %s, port %d, data %s' % (ip_port[0], ip_port[1], data))

    serv.update_service('test', ('192.168.1.1', 8080), None)
    ip_port, data = serv.get_service('test')
    print('service ip %s, port %d, data %s' % (ip_port[0], ip_port[1], data))

    serv.update_service('test', None, 'update test')
    ip_port, data = serv.get_service('test')
    print('service ip %s, port %d, data %s' % (ip_port[0], ip_port[1], data))

    serv.watch_service('test', watch_callback)
    serv.refresh_service('test', 5)
    serv.update_service('test', ('10.1.1.1', 8080), 'watch test')
    time.sleep(5)

    serv.unregister_service('test')
