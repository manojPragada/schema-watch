import unittest
from app import compare
class Tests(unittest.TestCase):
    def spec(self,operation):return {'openapi':'3.1.0','paths':{'/pets':{'get':operation}}}
    def test_remove(self):self.assertEqual(compare(self.spec({}),{'openapi':'3.1.0','paths':{}})[0]['kind'],'removed_operation')
    def test_required(self):
        new=self.spec({'parameters':[{'name':'id','in':'query','required':True}]})
        self.assertEqual(compare(self.spec({}),new)[0]['name'],'id')
    def test_optional(self):self.assertEqual(compare(self.spec({}),self.spec({'parameters':[{'name':'id','in':'query'}]})),[])
    def test_operation_override(self):
        old=self.spec({});old['paths']['/pets']['parameters']=[{'name':'id','in':'query','required':True}]
        new=self.spec({'parameters':[{'name':'id','in':'query','required':True}]})
        self.assertEqual(compare(old,new),[])
    def test_ref_rejected(self):
        with self.assertRaises(ValueError):compare(self.spec({'parameters':[{'$ref':'#/x'}]}),self.spec({}))
