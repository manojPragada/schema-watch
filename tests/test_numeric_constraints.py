import unittest
from contracts import compare_schema
class NumericConstraintTests(unittest.TestCase):
 def check(self,left,right,direction):return compare_schema(left,right,{'operation':'POST /x','direction':direction,'status':'body'})
 def test_tighter_request_bounds_break_callers(self):
  changes,warnings=self.check({'type':'number','minimum':0,'maximum':10},{'type':'number','minimum':2,'maximum':8},'request');self.assertEqual(len(changes),2);self.assertEqual(warnings,[])
 def test_weaker_response_guarantees_break_consumers(self):
  changes,warnings=self.check({'type':'number','minimum':2,'maximum':8},{'type':'number','minimum':0,'maximum':10},'response');self.assertEqual(len(changes),2);self.assertEqual(warnings,[])
