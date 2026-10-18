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


    def referenced(self, target):
        t=self.spec({'parameters':[{'$ref':'#/components/parameters/id'}]})
        t['components']={'parameters':{'id':target}}
        return t
    def test_required_parameter_reference_is_compared(self):
        new=self.referenced({'name':'id','in':'query','required':True})
        self.assertEqual(compare(self.spec({}),new)[0]['name'],'id')
    def test_reference_chains_and_escaped_names(self):
        t=self.referenced({'$ref':'#/components/parameters/a~1b~0c%20d'})
        t['components']['parameters']['a/b~c d']={'name':'id','in':'query','required':True}
        self.assertEqual(compare(self.spec({}),t)[0]['name'],'id')
    def test_reference_cycles_missing_and_external_targets_rejected(self):
        for target in [{'$ref':'#/components/parameters/id'}, {'$ref':'#/missing'}, {'$ref':'https://example.com/schema.json#/id'}, {'$ref':'#/bad~2escape'}]:
            with self.assertRaises(ValueError):compare(self.spec({}),self.referenced(target))
    def test_non_object_reference_target_rejected(self):
        with self.assertRaises(ValueError):compare(self.spec({}),self.referenced([]))
    def test_referenced_path_parameter_can_be_overridden(self):
        t=self.spec({'parameters':[{'name':'id','in':'query','required':False}]})
        t['paths']['/pets']['parameters']=[{'$ref':'#/components/parameters/id'}]
        t['components']={'parameters':{'id':{'name':'id','in':'query','required':True}}}
        self.assertEqual(compare(self.spec({}),t),[])
