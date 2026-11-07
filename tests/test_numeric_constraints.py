import unittest
from contracts import compare_schema
class NumericConstraintTests(unittest.TestCase):
 def check(self,left,right,direction):return compare_schema(left,right,{'operation':'POST /x','direction':direction,'status':'body'})
 def test_tighter_request_bounds_break_callers(self):
  changes,warnings=self.check({'type':'number','minimum':0,'maximum':10},{'type':'number','minimum':2,'maximum':8},'request');self.assertEqual(len(changes),2);self.assertEqual(warnings,[])
 def test_weaker_response_guarantees_break_consumers(self):
  changes,warnings=self.check({'type':'number','minimum':2,'maximum':8},{'type':'number','minimum':0,'maximum':10},'response');self.assertEqual(len(changes),2);self.assertEqual(warnings,[])
 def test_multiple_of_is_directional(self):
  changes,warnings=self.check({'type':'number','multipleOf':1},{'type':'number','multipleOf':2},'request');self.assertEqual(changes[0]['kind'],'request_multipleOf_incompatible');self.assertEqual(warnings,[])
  self.assertEqual(self.check({'type':'number','multipleOf':2},{'type':'number','multipleOf':1},'request'),([],[]))
  changes,warnings=self.check({'type':'number','multipleOf':2},{'type':'number','multipleOf':1},'response');self.assertEqual(changes[0]['kind'],'response_multipleOf_incompatible');self.assertEqual(warnings,[])
 def test_multiple_of_add_remove_and_invalid_values(self):
  self.assertEqual(self.check({'type':'number'},{'type':'number','multipleOf':.25},'request')[0][0]['kind'],'request_multipleOf_incompatible')
  self.assertEqual(self.check({'type':'number','multipleOf':.25},{'type':'number'},'response')[0][0]['kind'],'response_multipleOf_incompatible')
  changes,warnings=self.check({'type':'number','multipleOf':1},{'type':'number','multipleOf':0},'request');self.assertEqual(changes,[]);self.assertRegex(warnings[0]['reason'],'finite positive')
