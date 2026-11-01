import unittest
from contracts import compare_schema
class ArrayConstraintTests(unittest.TestCase):
 def test_request_narrowing_and_response_weakening_break(self):
  request={'operation':'POST /x','direction':'request','status':'body'};changes,warnings=compare_schema({'type':'array','minItems':1,'maxItems':20},{'type':'array','minItems':2,'maxItems':10},request);self.assertEqual({item['kind'] for item in changes},{'request_minItems_incompatible','request_maxItems_incompatible'});self.assertEqual(warnings,[])
  response={**request,'direction':'response'};changes,warnings=compare_schema({'type':'array','minItems':2,'maxItems':10},{'type':'array','minItems':1,'maxItems':20},response);self.assertEqual(len(changes),2);self.assertEqual(warnings,[])
 def test_invalid_or_one_sided_bounds_remain_warnings(self):
  context={'operation':'POST /x','direction':'request','status':'body'};changes,warnings=compare_schema({'type':'array','minItems':0},{'type':'array','minItems':True},context);self.assertEqual(changes,[]);self.assertEqual(len(warnings),1)
 def test_unique_items_is_directional(self):
  context={'operation':'POST /x','direction':'request','status':'body'}
  self.assertEqual(compare_schema({'type':'array'},{'type':'array','uniqueItems':True},context)[0][0]['kind'],'request_unique_items_incompatible')
  self.assertEqual(compare_schema({'type':'array','uniqueItems':True},{'type':'array'},dict(context,direction='response'))[0][0]['kind'],'response_unique_items_incompatible')
