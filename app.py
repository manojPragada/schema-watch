"""Conservative OpenAPI JSON operation-removal and required-parameter checker."""
import argparse
import json
import sys
import re
from urllib.parse import unquote
from contracts import compare_contracts
METHODS={'get','put','post','delete','options','head','patch','trace'}
def resolve_parameter(spec, parameter):
    seen = set()
    while isinstance(parameter, dict) and '$ref' in parameter:
        ref = parameter['$ref']
        if not isinstance(ref, str) or not ref.startswith('#/'):
            raise ValueError('Only same-document JSON Pointer parameter references are supported')
        pointer = unquote(ref[1:])
        if pointer in seen:
            raise ValueError('Parameter reference cycle detected')
        seen.add(pointer)
        if len(seen) > 100:
            raise ValueError('Parameter reference chain exceeds 100 links')
        target = spec
        for token in pointer[1:].split('/'):
            if re.search(r'~(?![01])', token):
                raise ValueError('Invalid JSON Pointer escape')
            key = token.replace('~1', '/').replace('~0', '~')
            if not isinstance(target, dict) or key not in target:
                raise ValueError('Parameter reference does not resolve: ' + ref)
            target = target[key]
        parameter = target
    if not isinstance(parameter, dict):
        raise ValueError('Parameter reference must resolve to an object')
    return parameter

def operations(spec):
    if not isinstance(spec,dict) or not str(spec.get('openapi','')).startswith('3.') or not isinstance(spec.get('paths'),dict):raise ValueError('Expected OpenAPI 3.x JSON with a paths object')
    result={}
    for path,item in spec['paths'].items():
        if not isinstance(item,dict):raise ValueError('Path items must be objects')
        if '$ref' in item:raise ValueError('Path item references are not supported yet')
        for method,op in item.items():
            if method not in METHODS:continue
            if not isinstance(op,dict):raise ValueError('Operations must be objects')
            params={}
            for param in item.get('parameters',[])+op.get('parameters',[]):
                param = resolve_parameter(spec, param)
                if not isinstance(param.get('name'),str) or param.get('in') not in ('query','path','header','cookie'):raise ValueError('Parameters require a name and location')
                params[(param['in'],param['name'])]=param.get('required',False) is True
            result[(method,path)]=params
    return result

def compare(before,after):
    old=operations(before);new=operations(after);changes=[]
    for method,path in sorted(old):
        if (method,path) not in new:changes.append({'kind':'removed_operation','operation':f'{method.upper()} {path}'})
        else:
            for param,required in sorted(new[(method,path)].items()):
                if required and not old[(method,path)].get(param,False):
                    changes.append({'kind':'new_required_parameter','operation':f'{method.upper()} {path}','location':param[0],'name':param[1]})
    return changes + compare_contracts(before, after, old.keys() & new.keys())[0]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('before');p.add_argument('after');a=p.parse_args()
    try:
        with open(a.before,encoding='utf-8') as f:before=json.load(f)
        with open(a.after,encoding='utf-8') as f:after=json.load(f)
        changes=compare(before,after)
        _, warnings=compare_contracts(before,after,operations(before).keys() & operations(after).keys())
        print(json.dumps({'scope':'operation/parameter checks plus bounded nested inline application/json type and required-property checks','breaking_changes':changes,'coverage_warnings':warnings},indent=2));return int(bool(changes))
    except (OSError,ValueError,TypeError,AttributeError) as exc:print(str(exc),file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())



