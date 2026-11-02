import unittest
from contracts import compare_schema
class ObjectConstraintTests(unittest.TestCase):
 def test_request_narrowing_and_response_weakening_break(self):
  request={'operation':'POST /x','direction':'request','status':'body'}
  changes,warnings=compare_schema({'type':'object','minProperties':1,'maxProperties':10},{'type':'object','minProperties':2,'maxProperties':8},request);self.assertEqual({item['kind'] for item in changes},{'request_minProperties_incompatible','request_maxProperties_incompatible'});self.assertEqual(warnings,[])
  changes,warnings=compare_schema({'type':'object','minProperties':2,'maxProperties':8},{'type':'object','minProperties':1,'maxProperties':10},dict(request,direction='response'));self.assertEqual(len(changes),2);self.assertEqual(warnings,[])
