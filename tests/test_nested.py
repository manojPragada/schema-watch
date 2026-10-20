import unittest
from contracts import compare_schema


class NestedTests(unittest.TestCase):
    def compare(self, old, new, direction='request'):
        return compare_schema(old, new, {'operation': 'POST /demo', 'direction': direction, 'status': 'body'})

    def test_nested_request_narrowing_and_widening(self):
        def obj(kind):
            return {'type': 'object', 'properties': {'count': {'type': kind}}}
        self.assertEqual(self.compare(obj('integer'), obj('number'))[0], [])
        changes, _ = self.compare(obj('number'), obj('integer'))
        self.assertEqual(changes[0]['schema_path'], '$["count"]')
        self.assertEqual(changes[0]['kind'], 'request_type_incompatible')

    def test_response_array_item_widening(self):
        old = {'type': 'array', 'items': {'type': 'integer'}}
        new = {'type': 'array', 'items': {'type': 'number'}}
        changes, _ = self.compare(old, new, 'response')
        self.assertEqual(changes[0]['schema_path'], '$[*]')
        self.assertEqual(changes[0]['kind'], 'response_type_incompatible')

    def test_nested_requiredness(self):
        old = {'type': 'object', 'properties': {'profile': {'type': 'object'}}}
        new = {'type': 'object', 'properties': {'profile': {'type': 'object', 'required': ['id']}}}
        self.assertEqual(self.compare(old, new)[0][0]['schema_path'], '$["profile"]')
        self.assertEqual(self.compare(new, old, 'response')[0][0]['kind'], 'response_required_guarantee_removed')

    def test_nested_refs_warn_while_siblings_are_compared(self):
        old = {'type': 'object', 'properties': {'a': {'$ref': '#/x'}, 'b': {'type': 'string'}}}
        new = {'type': 'object', 'properties': {'a': {}, 'b': {'type': 'integer'}}}
        changes, warnings = self.compare(old, new)
        self.assertEqual(changes[0]['schema_path'], '$["b"]')
        self.assertEqual(warnings[0]['schema_path'], '$["a"]')

    def test_constraints_and_missing_properties_warn(self):
        old = {'type': 'object', 'properties': {'old': {'type': 'string'}}}
        new = {'type': 'object', 'additionalProperties': False, 'properties': {'new': {'type': 'string'}}}
        changes, warnings = self.compare(old, new)
        self.assertEqual(changes, [])
        self.assertEqual(len(warnings), 3)

    def test_depth_limit_does_not_claim_coverage(self):
        old, new = {'type': 'string'}, {'type': 'integer'}
        for _ in range(34):
            old, new = {'type': 'array', 'items': old}, {'type': 'array', 'items': new}
        changes, warnings = self.compare(old, new)
        self.assertEqual(changes, [])
        self.assertIn('32 levels', warnings[0]['reason'])

    def test_boolean_item_schema_and_readonly_warn(self):
        self.assertTrue(self.compare({'type': 'array', 'items': False}, {'type': 'array', 'items': {}})[1])
        obj = {'type': 'object', 'properties': {'a': {'readOnly': True}}}
        self.assertTrue(self.compare(obj, obj)[1])
