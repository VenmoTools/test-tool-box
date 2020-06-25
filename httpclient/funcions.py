import unittest


def should_none(test: unittest.TestCase, except_value, real_value):
    return test.assertIsNone(real_value)


def should_not_none(test: unittest.TestCase, except_value, real_value):
    return test.assertIsNotNone(real_value)


def should_equal(test: unittest.TestCase, except_value, real_value):
    return test.assertEqual(except_value, real_value)


def should_false(test: unittest.TestCase, except_value, real_value):
    return test.assertFalse(except_value)


def should_true(test: unittest.TestCase, except_value, real_value):
    return test.assertTrue(except_value)


def should_not_equal(test: unittest.TestCase, except_value, real_value):
    return test.assertNotEqual(except_value, real_value)


def should_not_contains(test: unittest.TestCase, except_value, real_value):
    return test.assertNotIn(except_value, real_value)


def should_contains(test: unittest.TestCase, except_value, real_value):
    return test.assertIn(except_value, real_value)
