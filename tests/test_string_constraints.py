import unittest
from contracts import compare_schema
class StringConstraintTests(unittest.TestCase):
 def test_request_narrowing_and_response_weakening_break(self):
  context={'operation':'POST /x','direction':'request','status':'body'};changes,warnings=compare_schema({'type':'string','minLength':1,'maxLength':20},{'type':'string','minLength':2,'maxLength':10},context);self.assertEqual(len(changes),2);self.assertEqual(warnings,[])
