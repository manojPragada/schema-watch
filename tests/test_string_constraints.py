import unittest
from contracts import compare_schema
class StringConstraintTests(unittest.TestCase):
 def test_request_narrowing_and_response_weakening_break(self):
  context={'operation':'POST /x','direction':'request','status':'body'};changes,warnings=compare_schema({'type':'string','minLength':1,'maxLength':20},{'type':'string','minLength':2,'maxLength':10},context);self.assertEqual(len(changes),2);self.assertEqual(warnings,[])
 def test_pattern_and_format_changes_are_explicit_warnings(self):
  context={'operation':'POST /x','direction':'request','status':'body'}
  changes,warnings=compare_schema({'type':'string','pattern':'^[a-z]+$','format':'email'},{'type':'string','pattern':'^[A-Z]+$','format':'uuid'},context)
  self.assertEqual(changes,[]);self.assertEqual([item['reason'] for item in warnings],['pattern changed; semantic compatibility not checked','format changed; semantic compatibility not checked'])
 def test_unchanged_pattern_and_format_are_not_warned(self):
  context={'operation':'GET /x','direction':'response','status':'200'};schema={'type':'string','pattern':'^[a-z]+$','format':'email'}
  self.assertEqual(compare_schema(schema,schema,context),([],[]))
