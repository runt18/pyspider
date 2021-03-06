#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.com>
#         http://binux.me
# Created on 2012-08-30 17:43:49

from __future__ import unicode_literals, division, absolute_import

import logging
logger = logging.getLogger('database.basedb')

from six import itervalues


class BaseDB:

    '''
    BaseDB

    dbcur should be overwirte
    '''
    __tablename__ = None
    placeholder = '%s'

    @staticmethod
    def escape(string):
        return '`{0!s}`'.format(string)

    @property
    def dbcur(self):
        raise NotImplementedError

    def _execute(self, sql_query, values=None):
        if values is None:
            values = []
        dbcur = self.dbcur
        dbcur.execute(sql_query, values)
        return dbcur

    def _select(self, tablename=None, what="*", where="", where_values=None, offset=0, limit=None):
        if where_values is None:
            where_values = []
        tablename = self.escape(tablename or self.__tablename__)
        if isinstance(what, list) or isinstance(what, tuple) or what is None:
            what = ','.join(self.escape(f) for f in what) if what else '*'

        sql_query = "SELECT {0!s} FROM {1!s}".format(what, tablename)
        if where:
            sql_query += " WHERE {0!s}".format(where)
        if limit:
            sql_query += " LIMIT {0:d}, {1:d}".format(offset, limit)
        logger.debug("<sql: %s>", sql_query)

        for row in self._execute(sql_query, where_values):
            yield row

    def _select2dic(self, tablename=None, what="*", where="", where_values=None,
                    order=None, offset=0, limit=None):
        if where_values is None:
            where_values = []
        tablename = self.escape(tablename or self.__tablename__)
        if isinstance(what, list) or isinstance(what, tuple) or what is None:
            what = ','.join(self.escape(f) for f in what) if what else '*'

        sql_query = "SELECT {0!s} FROM {1!s}".format(what, tablename)
        if where:
            sql_query += " WHERE {0!s}".format(where)
        if order:
            sql_query += ' ORDER BY {0!s}'.format(order)
        if limit:
            sql_query += " LIMIT {0:d}, {1:d}".format(offset, limit)
        logger.debug("<sql: %s>", sql_query)

        dbcur = self._execute(sql_query, where_values)
        fields = [f[0] for f in dbcur.description]

        for row in dbcur:
            yield dict(zip(fields, row))

    def _replace(self, tablename=None, **values):
        tablename = self.escape(tablename or self.__tablename__)
        if values:
            _keys = ", ".join(self.escape(k) for k in values)
            _values = ", ".join([self.placeholder, ] * len(values))
            sql_query = "REPLACE INTO {0!s} ({1!s}) VALUES ({2!s})".format(tablename, _keys, _values)
        else:
            sql_query = "REPLACE INTO {0!s} DEFAULT VALUES".format(tablename)
        logger.debug("<sql: %s>", sql_query)

        if values:
            dbcur = self._execute(sql_query, list(itervalues(values)))
        else:
            dbcur = self._execute(sql_query)
        return dbcur.lastrowid

    def _insert(self, tablename=None, **values):
        tablename = self.escape(tablename or self.__tablename__)
        if values:
            _keys = ", ".join((self.escape(k) for k in values))
            _values = ", ".join([self.placeholder, ] * len(values))
            sql_query = "INSERT INTO {0!s} ({1!s}) VALUES ({2!s})".format(tablename, _keys, _values)
        else:
            sql_query = "INSERT INTO {0!s} DEFAULT VALUES".format(tablename)
        logger.debug("<sql: %s>", sql_query)

        if values:
            dbcur = self._execute(sql_query, list(itervalues(values)))
        else:
            dbcur = self._execute(sql_query)
        return dbcur.lastrowid

    def _update(self, tablename=None, where="1=0", where_values=None, **values):
        if where_values is None:
            where_values = []
        tablename = self.escape(tablename or self.__tablename__)
        _key_values = ", ".join([
            "{0!s} = {1!s}".format(self.escape(k), self.placeholder) for k in values
        ])
        sql_query = "UPDATE {0!s} SET {1!s} WHERE {2!s}".format(tablename, _key_values, where)
        logger.debug("<sql: %s>", sql_query)

        return self._execute(sql_query, list(itervalues(values)) + list(where_values))

    def _delete(self, tablename=None, where="1=0", where_values=None):
        if where_values is None:
            where_values = []
        tablename = self.escape(tablename or self.__tablename__)
        sql_query = "DELETE FROM {0!s}".format(tablename)
        if where:
            sql_query += " WHERE {0!s}".format(where)
        logger.debug("<sql: %s>", sql_query)

        return self._execute(sql_query, where_values)

if __name__ == "__main__":
    import sqlite3

    class DB(BaseDB):
        __tablename__ = "test"

        def __init__(self):
            self.conn = sqlite3.connect(":memory:")
            cursor = self.conn.cursor()
            cursor.execute(
                '''CREATE TABLE `{0!s}` (id INTEGER PRIMARY KEY AUTOINCREMENT, name, age)'''.format(self.__tablename__)
            )

        @property
        def dbcur(self):
            return self.conn.cursor()

    db = DB()
    assert db._insert(db.__tablename__, name="binux", age=23) == 1
    assert db._select(db.__tablename__, "name, age").fetchone() == ("binux", 23)
    assert db._select2dic(db.__tablename__, "name, age")[0]["name"] == "binux"
    assert db._select2dic(db.__tablename__, "name, age")[0]["age"] == 23
    db._replace(db.__tablename__, id=1, age=24)
    assert db._select(db.__tablename__, "name, age").fetchone() == (None, 24)
    db._update(db.__tablename__, "id = 1", age=16)
    assert db._select(db.__tablename__, "name, age").fetchone() == (None, 16)
    db._delete(db.__tablename__, "id = 1")
    assert db._select(db.__tablename__).fetchall() == []
