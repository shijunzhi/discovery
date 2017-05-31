# -*- coding: utf-8 -*-
import threading
from string import Template

import etcd

import discovery
from error import *


class Etcd2Discovery(discovery.Discovery):
    prefix = '/services'
    addr_key = 'address'
    data_key = 'data'

    def __init__(self, etcd_ip, etcd_port):
        self._etcd_ip = etcd_ip
        self._etcd_port = etcd_port
        self._client = etcd.Client(host=etcd_ip, port=etcd_port, read_timeout=5,
                                   allow_reconnect=True)

        self._serv_key = Template('{prefix}/$name'.format(prefix=self.prefix))
        self._addr_key = Template(
            '{prefix}/$name/{key}'.format(prefix=self.prefix,
                                          key=self.addr_key))
        self._data_key = Template(
            '{prefix}/$name/{key}'.format(prefix=self.prefix,
                                          key=self.data_key))

        self._watch_table = {}
        self._lock = threading.RLock()

    def register_service(self, name, ip_port, data='', ttl=None):
        try:
            if ttl is not None:
                serv_key = self._serv_key.substitute(name=name)
                self._execute(self._client.write, key=serv_key, value=None,
                              dir=True, ttl=ttl)

            addr_key = self._addr_key.substitute(name=name)
            addr = '{ip}:{port}'.format(ip=ip_port[0], port=ip_port[1])
            self._execute(self._client.write, key=addr_key, value=addr,
                          prevExist=False)

            data_key = self._data_key.substitute(name=name)
            self._execute(self._client.write, key=data_key, value=data,
                          prevExist=False)
        except etcd.EtcdAlreadyExist, etcd.EtcdNotFile:
            msg = 'service {name} already exist'.format(name=name)
            raise ServiceAlreadyExistError(msg)

    def refresh_service(self, name, ttl):
        key = self._serv_key.substitute(name=name)
        try:
            self._execute(self._client.write, key=key, value=None, ttl=ttl,
                          dir=True, prevExist=True)
        except etcd.EtcdKeyNotFound:
            msg = 'service {name} not exist'.format(name=name)
            raise ServiceNotExistError(msg)

    def update_service(self, name, ip_port, data, ttl=None):
        if ip_port is not None:
            addr_key = self._addr_key.substitute(name=name)
            addr = '{ip}:{port}'.format(ip=ip_port[0], port=ip_port[1])
            self._execute(self._client.write, key=addr_key, value=addr)

        if data is not None:
            data_key = self._data_key.substitute(name=name)
            self._execute(self._client.write, key=data_key, value=data)

        if ttl is not None:
            self.refresh_service(name, ttl)

    def unregister_service(self, name):
        key = self._serv_key.substitute(name=name)
        try:
            self._execute(self._client.delete, key=key, recursive=True)
        except etcd.EtcdKeyNotFound:
            return

    def get_service(self, name):
        key = self._serv_key.substitute(name=name)
        try:
            result = self._execute(self._client.read, key=key, recursive=True)
            return self._parse_service(result)
        except etcd.EtcdKeyNotFound:
            msg = 'service {name} not exist'.format(name=name)
            raise ServiceNotExistError(msg)

    def watch_service(self, name, callback):
        def _watch():
            thr = WatchServiceThread(self._etcd_ip, self._etcd_port, name, callback)
            self._watch_table[name] = thr
            thr.start()

        self._lock.acquire()
        try:
            thr = self._watch_table[name]
            if thr.is_alive:
                raise ServiceAlreadyWatched()
            else:
                del self._watch_table[name]
            _watch()
        except KeyError:
            _watch()
        finally:
            self._lock.release()

    def unwatch_service(self, name):
        self._lock.acquire()
        try:
            thr = self._watch_table[name]
            thr.stop = True
            del self._watch_table[name]
        except KeyError:
            pass
        finally:
            self._lock.release()

    def _execute(self, cmd, **kwargs):
        try:
            return cmd(**kwargs)
        except etcd.EtcdConnectionFailed as e:
            raise ConnectionError(
                'connection to etcd break: %s' % e.message)

    def _parse_service(self, etcd_result):
        ip_port = None
        data = None
        for node in etcd_result.leaves:
            key = node.key.encode()
            if key.endswith(self.addr_key):
                ip, port = node.value.encode().split(':')
                ip_port = (ip, int(port))
            elif key.endswith(self.data_key):
                data = node.value.encode()
        return ip_port, data


class WatchServiceThread(threading.Thread):
    def __init__(self, etcd_ip, etcd_port, serv_name, callback):
        super(WatchServiceThread, self).__init__()

        self._etcd_ip = etcd_ip
        self._etcd_port = etcd_port
        self._serv_name = serv_name
        self._key = '{prefix}/{name}'.format(prefix=Etcd2Discovery.prefix,
                                             name=serv_name)
        self._callback = callback

        self.stop = False

    def run(self):
        watch_conn = etcd.Client(host=self._etcd_ip, port=self._etcd_port)
        start_index = None
        callback = self._callback
        key = self._key
        serv_name = self._serv_name

        while not self.stop:
            try:
                result = watch_conn.watch(key=key, index=start_index,
                                          timeout=10, recursive=True)
                if self.stop:
                    return
                start_index = result.modifiedIndex + 1

                if result.action == u'update':
                    pass
                elif result.action == u'expire' or result.action == u'delete':
                    callback(False, serv_name, ('', 0), '')
                else:
                    ip_port, data = self._parse_watch_result(result)
                    callback(False, serv_name, ip_port, data)

            except etcd.EtcdWatcherCleared:
                try:
                    result = watch_conn.get(key=key)
                    start_index = result.etcd_index + 1
                except etcd.EtcdKeyNotFound:
                    callback(False, serv_name, '', '')
                    start_index = None
                except etcd.EtcdError:
                    callback(True, serv_name, None, None)
                    return

            except etcd.EtcdWatchTimedOut:
                pass

            except etcd.EtcdConnectionFailed:
                callback(True, serv_name, None, None)
                return

    def _parse_watch_result(self, etcd_result):
        ip_port = None
        data = None
        for node in etcd_result.leaves:
            key = node.key.encode()
            if key.endswith(Etcd2Discovery.addr_key):
                if node.value == u'':
                    ip_port = ''
                else:
                    ip, port = node.value.encode().split(':')
                    ip_port = (ip, int(port))
            elif key.endswith(Etcd2Discovery.data_key):
                data = node.value.encode()
        return ip_port, data
