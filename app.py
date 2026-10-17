"""Conservative OpenAPI JSON operation-removal and required-parameter checker."""
import argparse
import json
import sys
METHODS={'get','put','post','delete','options','head','patch','trace'}
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
                if not isinstance(param,dict) or '$ref' in param:raise ValueError('Inline parameters required; references not supported yet')
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
    return changes

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('before');p.add_argument('after');a=p.parse_args()
    try:
        with open(a.before,encoding='utf-8') as f:before=json.load(f)
        with open(a.after,encoding='utf-8') as f:after=json.load(f)
        changes=compare(before,after);print(json.dumps({'scope':'operation removals and newly required inline parameters only','breaking_changes':changes},indent=2));return int(bool(changes))
    except (OSError,ValueError,TypeError,AttributeError) as exc:print(str(exc),file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
