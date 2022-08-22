"Database cache backend."

from django.core.cache.backends.db import CacheClass as DjangoCacheClass
from django.db import connection, transaction, DatabaseError
import base64, time
from datetime import datetime
try:
    import pickle as pickle
except ImportError:
    import pickle

class CacheClass(DjangoCacheClass):
    def _base_set(self, mode, key, value, timeout=None):
        if timeout is None:
            timeout = self.default_timeout
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM %s" % self._table)
        num = cursor.fetchone()[0]
        now = datetime.now().replace(microsecond=0)
        exp = datetime.fromtimestamp(time.time() + timeout).replace(microsecond=0)
        if num > self._max_entries:
            self._cull(cursor, now)
        encoded = base64.encodestring(pickle.dumps(value, 2)).strip()
        cursor.execute("SELECT cache_key, expires FROM %s WHERE cache_key = %%s" % self._table, [key])
        try:
            result = cursor.fetchone()
            if result and (mode == 'set' or
                    (mode == 'add' and result[1] < now)):
                cursor.execute("UPDATE %s SET value = %%s, expires = %%s WHERE cache_key = %%s" % self._table, [encoded, str(exp), key])
            else:
                cursor.execute("INSERT INTO %s (cache_key, value, expires) VALUES (%%s, %%s, %%s)" % self._table, [key, encoded, str(exp)])
        except DatabaseError:
            # To be threadsafe, updates/inserts are allowed to fail silently

            # This is a bad call here - the rest of the calls use the rollback_unless_managed
            # method - but this one doesn't.  Stupid.  Django bug: http://code.djangoproject.com/ticket/12189
            transaction.rollback_unless_managed()
            return False
        else:
            transaction.commit_unless_managed()
            return True
