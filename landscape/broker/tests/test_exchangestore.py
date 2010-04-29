import time

try:
    import sqlite3
except ImportError:
    from pysqlite2 import dbapi2 as sqlite3

from landscape.tests.helpers import LandscapeTest

from landscape.broker.exchangestore import ExchangeStore


class ExchangeStoreTest(LandscapeTest):
    """Unit tests for the C{ExchangeStore}."""

    def setUp(self):
        super(ExchangeStoreTest, self).setUp()

        self.filename = self.makeFile()
        self.store1 = ExchangeStore(self.filename)
        self.store2 = ExchangeStore(self.filename)

    def test_add_message_context(self):
        """Adding a message context works correctly."""
        now = time.time()
        self.store1.add_message_context(123, 'abc', 'change-packages')

        db = sqlite3.connect(self.store2._filename)
        cursor = db.cursor()
        cursor.execute(
            "SELECT operation_id, secure_id, message_type, timestamp "
            "FROM message_context WHERE operation_id=?", (123,))
        results = cursor.fetchall()
        self.assertEquals(1, len(results))
        [row] = results
        self.assertEquals(123, row[0])
        self.assertEquals('abc', row[1])
        self.assertEquals('change-packages', row[2])
        self.assertTrue(row[3] > now)

    def test_add_operationid_is_unique(self):
        """Only one message context with a given operation-id is permitted."""
        self.store1.add_message_context(123, 'abc', 'change-packages')
        self.assertRaises(
            sqlite3.IntegrityError,
            self.store1.add_message_context, 123, 'def', 'change-packages')

    def test_get_message_context_works(self):
        """Accessing a C{MessageContext} with an existing
        C{operation-id} works."""
        now = time.time()
        self.store1.add_message_context(234, 'bcd', 'change-packages')
        context = self.store2.get_message_context(234)
        self.assertEquals(234, context.operation_id)
        self.assertEquals('bcd', context.secure_id)
        self.assertEquals('change-packages', context.message_type)
        self.assertTrue(context.timestamp > now)

    def test_get_message_context_with_nonexistent_operation_id(self):
        """Attempts to access a C{MessageContext} with a non-existent
        C{operation-id} result in C{None}."""
        self.assertIs(None, self.store1.get_message_context(999))

    def test_deleting_message_contexts_works(self):
        """C{MessageContext}s are deleted correctly."""
        context = self.store1.add_message_context(
            345, 'opq', 'change-packages')
        context.remove()
        self.assertIs(None, self.store1.get_message_context(345))
