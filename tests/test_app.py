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
    def test_referenced_path_item_is_compared(self):
        old=self.spec({});new={'openapi':'3.1.0','paths':{'/pets':{'$ref':'#/components/pathItems/Pets'}},'components':{'pathItems':{'Pets':{'get':{'parameters':[{'name':'id','in':'query','required':True}]}}}}}
        self.assertEqual(compare(old,new)[0]['kind'],'new_required_parameter')
    def test_bad_path_item_references_are_rejected(self):
        for item in [{'$ref':'#/missing'},{'$ref':'#/components/pathItems/Pets','get':{} }]:
            spec={'openapi':'3.1.0','paths':{'/pets':item},'components':{'pathItems':{'Pets':{'get':{}}}}}
            with self.assertRaises(ValueError):compare(self.spec({}),spec)


    def body(self, schema, direction='request'):
        media={'content':{'application/json':{'schema':schema}}}
        return self.spec({'requestBody':media} if direction=='request' else {'responses':{'200':media}})
    def test_new_required_request_property(self):
        old=self.body({'type':'object','required':[]})
        new=self.body({'type':'object','required':['id']})
        self.assertEqual(compare(old,new)[0]['kind'],'new_required_request_property')
    def test_response_required_guarantee_removal(self):
        old=self.body({'type':'object','required':['id']},'response')
        new=self.body({'type':'object'},'response')
        self.assertEqual(compare(old,new)[0]['kind'],'response_required_guarantee_removed')
    def test_directional_integer_number_compatibility(self):
        self.assertEqual(compare(self.body({'type':'integer'}),self.body({'type':'number'})),[])
        self.assertEqual(compare(self.body({'type':'number'}),self.body({'type':'integer'}))[0]['kind'],'request_type_incompatible')
        self.assertEqual(compare(self.body({'type':'integer'},'response'),self.body({'type':'number'},'response'))[0]['kind'],'response_type_incompatible')
    def test_schema_references_are_resolved_and_compared(self):
        from contracts import compare_contracts
        old=self.body({'$ref':'#/components/schemas/Pet'});new=self.body({'$ref':'#/components/schemas/Pet'})
        old['components']={'schemas':{'Pet':{'type':'object','properties':{'id':{'type':'number'}}}}}
        new['components']={'schemas':{'Pet':{'type':'object','properties':{'id':{'type':'integer'}}}}}
        changes,warnings=compare_contracts(old,new,[('get','/pets')])
        self.assertEqual(changes[0]['schema_path'],'$["id"]');self.assertEqual(warnings,[])
    def test_bad_schema_references_warn_without_network_access(self):
        from contracts import compare_contracts
        for ref in ['https://example.com/schema.json#/Pet','#/missing']:
            old=self.body({'$ref':ref});new=self.body({'type':'object'});changes,warnings=compare_contracts(old,new,[('get','/pets')]);self.assertEqual(changes,[]);self.assertTrue(warnings)
    def test_new_required_body_detected(self):
        old=self.spec({});new=self.body({'type':'object'});new['paths']['/pets']['get']['requestBody']['required']=True
        self.assertEqual(compare(old,new)[0]['kind'],'new_required_request_body')
    def test_removed_response_status_is_breaking(self):
        old=self.spec({'responses':{'200':{'description':'ok'},'404':{'description':'missing'}}})
        new=self.spec({'responses':{'200':{'description':'ok'}}})
        finding=compare(old,new)[0]
        self.assertEqual((finding['kind'],finding['status']),('response_status_removed','404'))
    def test_removed_json_media_types_are_breaking(self):
        for direction in ('request','response'):
            old=self.body({'type':'object'},direction)
            new=self.body({'type':'object'},direction)
            target=new['paths']['/pets']['get']['requestBody'] if direction=='request' else new['paths']['/pets']['get']['responses']['200']
            target['content']={'text/plain':{'schema':{'type':'string'}}}
            self.assertEqual(compare(old,new)[0]['kind'],direction+'_json_media_type_removed')

    def test_removed_response_header_is_breaking_case_insensitively(self):
        old=self.spec({'responses':{'200':{'headers':{'X-Rate-Limit':{'schema':{'type':'integer'}}}}}})
        renamed=self.spec({'responses':{'200':{'headers':{'x-rate-limit':{'schema':{'type':'integer'}}}}}})
        removed=self.spec({'responses':{'200':{}}})
        self.assertEqual(compare(old,renamed),[])
        finding=compare(old,removed)[0]
        self.assertEqual((finding['kind'],finding['name'],finding['status']),('response_header_removed','X-Rate-Limit','200'))

    def test_malformed_response_headers_remain_coverage_warnings(self):
        from contracts import compare_contracts
        old=self.spec({'responses':{'200':{'headers':['bad']}}})
        new=self.spec({'responses':{'200':{}}})
        changes,warnings=compare_contracts(old,new,[('get','/pets')])
        self.assertEqual(changes,[]);self.assertTrue(any('headers' in item['reason'] for item in warnings))

    def test_response_header_schema_weakening_is_breaking_case_insensitively(self):
        old=self.spec({'responses':{'200':{'headers':{'X-Rate-Limit':{'schema':{'type':'integer','minimum':0}}}}}})
        new=self.spec({'responses':{'200':{'headers':{'x-rate-limit':{'schema':{'type':'number','minimum':-1}}}}}})
        findings=compare(old,new)
        self.assertEqual({item['kind'] for item in findings},{'response_type_incompatible','response_minimum_incompatible'})
        self.assertTrue(all(item['header']=='X-Rate-Limit' and item['schema_path']=='$header["X-Rate-Limit"]' for item in findings))

    def test_referenced_response_header_remains_a_warning(self):
        from contracts import compare_contracts
        old=self.spec({'responses':{'200':{'headers':{'X-Trace':{'$ref':'#/components/headers/Trace'}}}}})
        new=self.spec({'responses':{'200':{'headers':{'x-trace':{'schema':{'type':'string'}}}}}})
        changes,warnings=compare_contracts(old,new,[('get','/pets')])
        self.assertEqual(changes,[]);self.assertTrue(any(item.get('header')=='X-Trace' for item in warnings))

