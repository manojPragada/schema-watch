"""Partial, directional checks for inline application/json body contracts."""
import json
import math
from fractions import Fraction
from urllib.parse import unquote
TYPES = {'null', 'boolean', 'object', 'array', 'string', 'integer', 'non_integer_number'}
UNSUPPORTED = {'$ref', 'allOf', 'anyOf', 'oneOf', 'not', 'if', 'then', 'else', '$dynamicRef'}


def type_set(schema):
    value = schema.get('type')
    if value is None:
        result = set(TYPES)
    elif value == 'number':
        result = {'integer', 'non_integer_number'}
    elif isinstance(value, str) and value in TYPES - {'non_integer_number'}:
        result = {value}
    else:
        raise ValueError('Only single JSON Schema type names are supported')
    if schema.get('nullable') is True:
        result.add('null')
    return result


def inline_schema(schema):
    if not isinstance(schema, dict) or UNSUPPORTED.intersection(schema):
        raise ValueError('Schema references, composition and boolean schemas are not checked')
    if 'nullable' in schema and type(schema['nullable']) is not bool:
        raise ValueError('nullable must be a boolean when supplied')
    required = schema.get('required', [])
    properties = schema.get('properties', {})
    if not isinstance(required, list) or len(required)>100 or not all(isinstance(name,str) and 1<=len(name)<=256 for name in required) or len(required)!=len(set(required)):
        raise ValueError('required must be an array of at most 100 unique, bounded property names')
    if not isinstance(properties, dict):
        raise ValueError('properties must be an object')
    # Directional requiredness needs readOnly/writeOnly-aware handling, still pending.
    if any(isinstance(value, dict) and (value.get('readOnly') or value.get('writeOnly')) for value in properties.values()):
        raise ValueError('readOnly/writeOnly property contracts are not checked')
    return type_set(schema), set(required)


def resolve_local_schema(document,schema,chain=()):
    if not isinstance(schema,dict) or '$ref' not in schema:return schema
    reference=schema['$ref']
    if not isinstance(reference,str) or not reference.startswith('#/') or len(chain)>=100:raise ValueError('Only bounded same-document schema references are checked')
    if reference in chain:raise ValueError('Schema reference cycle not checked')
    target=document
    for raw in reference[2:].split('/'):
        if '~' in raw.replace('~0','').replace('~1',''):raise ValueError('Invalid JSON Pointer escape in schema reference')
        key=unquote(raw).replace('~1','/').replace('~0','~')
        if not isinstance(target,dict) or key not in target:raise ValueError('Schema reference target not found')
        target=target[key]
    if not isinstance(target,dict):raise ValueError('Schema reference target must be an object')
    return resolve_local_schema(document,target,chain+(reference,))

def compare_schema(left, right, context, schema_path='$', depth=0, left_root=None, right_root=None):
    changes, warnings = [], []
    location = dict(context, schema_path=schema_path)
    if depth > 32:
        return [], [dict(location, reason='Schema nesting beyond 32 levels not checked')]
    try:
        if left_root is not None:left=resolve_local_schema(left_root,left)
        if right_root is not None:right=resolve_local_schema(right_root,right)
        left_types, left_required = inline_schema(left)
        right_types, right_required = inline_schema(right)
    except ValueError as error:
        return [], [dict(location, reason=str(error))]
    def literal_values(schema):
        if 'const' in schema:return [schema['const']]
        return schema.get('enum')
    old_literals,new_literals=literal_values(left),literal_values(right)
    if old_literals is not None or new_literals is not None:
        if not all(isinstance(values,list) and values and len(values)<=100 for values in (old_literals,new_literals)):
            warnings.append(dict(location,reason='Enum/const transition not checked unless both sides contain 1–100 values'))
        else:
            old_encoded={json.dumps(value,sort_keys=True,allow_nan=False) for value in old_literals};new_encoded={json.dumps(value,sort_keys=True,allow_nan=False) for value in new_literals}
            incompatible=old_encoded-new_encoded if context['direction']=='request' else new_encoded-old_encoded
            if incompatible:changes.append(dict(location,kind=context['direction']+'_enum_incompatible'))
    def numeric_constraint(name,lower):
        old,new=left.get(name),right.get(name)
        if old is None and new is None:return
        if type(old) not in (int,float) or type(new) not in (int,float):return
        tighter=(new>old if lower else new<old) if context['direction']=='request' else (new<old if lower else new>old)
        if tighter:changes.append(dict(location,kind=context['direction']+'_'+name+'_incompatible'))
    for name in ('minimum','exclusiveMinimum'):numeric_constraint(name,True)
    for name in ('maximum','exclusiveMaximum'):numeric_constraint(name,False)
    def valid_multiple(value):return type(value) in (int,float) and math.isfinite(value) and value>0
    old_multiple,new_multiple=left.get('multipleOf'),right.get('multipleOf')
    if 'multipleOf' in left or 'multipleOf' in right:
        if ('multipleOf' in left and not valid_multiple(old_multiple)) or ('multipleOf' in right and not valid_multiple(new_multiple)):
            warnings.append(dict(location,reason='multipleOf transition not checked unless supplied values are finite positive numbers'))
        else:
            incompatible=False
            if context['direction']=='request':
                incompatible='multipleOf' in right and ('multipleOf' not in left or (Fraction(str(old_multiple))/Fraction(str(new_multiple))).denominator!=1)
            else:
                incompatible='multipleOf' in left and ('multipleOf' not in right or (Fraction(str(new_multiple))/Fraction(str(old_multiple))).denominator!=1)
            if incompatible:changes.append(dict(location,kind=context['direction']+'_multipleOf_incompatible'))
    def length_constraint(name,lower):
        old,new=left.get(name),right.get(name)
        if old is None and new is None:return
        if type(old) is not int or type(new) is not int or old<0 or new<0:
            warnings.append(dict(location,reason=name+' transition not checked unless both sides contain non-negative integers'));return
        tighter=(new>old if lower else new<old) if context['direction']=='request' else (new<old if lower else new>old)
        if tighter:changes.append(dict(location,kind=context['direction']+'_'+name+'_incompatible'))
    length_constraint('minLength',True);length_constraint('maxLength',False)
    length_constraint('minItems',True);length_constraint('maxItems',False)
    length_constraint('minProperties',True);length_constraint('maxProperties',False)
    old_unique,new_unique=left.get('uniqueItems',False),right.get('uniqueItems',False)
    if type(old_unique) is bool and type(new_unique) is bool:
        incompatible=(not old_unique and new_unique) if context['direction']=='request' else (old_unique and not new_unique)
        if incompatible:changes.append(dict(location,kind=context['direction']+'_unique_items_incompatible'))
    elif old_unique!=new_unique:warnings.append(dict(location,reason='uniqueItems transition not checked unless both sides are boolean'))
    for name in ('pattern','format'):
        if left.get(name)!=right.get(name) and (name in left or name in right):
            warnings.append(dict(location,reason=name+' changed; semantic compatibility not checked'))
    if 'object' in left_types and 'object' in right_types:
        old_additional=left.get('additionalProperties',True);new_additional=right.get('additionalProperties',True)
        if type(old_additional) is bool and type(new_additional) is bool:
            incompatible=(old_additional and not new_additional) if context['direction']=='request' else (not old_additional and new_additional)
            if incompatible:changes.append(dict(location,kind=context['direction']+'_additional_properties_incompatible'))
        elif old_additional!=new_additional:
            warnings.append(dict(location,reason='additionalProperties schema transition not checked; only boolean policies are directional'))
        def dependencies(schema):
            value=schema.get('dependentRequired',{})
            if not isinstance(value,dict) or len(value)>100:return None
            if not all(isinstance(name,str) and 1<=len(name)<=256 and isinstance(required,list) and len(required)<=100 and all(isinstance(item,str) and 1<=len(item)<=256 for item in required) and len(required)==len(set(required)) for name,required in value.items()):return None
            return {name:set(required) for name,required in value.items()}
        old_dependencies,new_dependencies=dependencies(left),dependencies(right)
        if old_dependencies is None or new_dependencies is None:
            warnings.append(dict(location,reason='dependentRequired transition not checked unless both sides are bounded string-array maps'))
        else:
            incompatible=any((new_dependencies.get(name,set())-old_dependencies.get(name,set())) if context['direction']=='request' else (old_dependencies.get(name,set())-new_dependencies.get(name,set())) for name in old_dependencies.keys()|new_dependencies.keys())
            if incompatible:changes.append(dict(location,kind=context['direction']+'_dependent_required_incompatible'))
    constraints = {'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum',
                   'multipleOf', 'minLength', 'maxLength', 'pattern', 'format', 'minItems',
                   'maxItems', 'uniqueItems', 'contains', 'prefixItems', 'additionalProperties',
                   'patternProperties', 'unevaluatedProperties', 'dependentRequired',
                   'dependentSchemas', 'minProperties', 'maxProperties'}
    checked={'minimum','maximum','exclusiveMinimum','exclusiveMaximum','multipleOf','minLength','maxLength','minItems','maxItems','minProperties','maxProperties','uniqueItems','pattern','format','additionalProperties','dependentRequired'}
    unchecked = sorted((left.keys() | right.keys()) & (constraints-checked))
    if unchecked:
        warnings.append(dict(location, reason='Constraints not checked: ' + ', '.join(unchecked)))
    direction = context['direction']
    incompatible = left_types - right_types if direction == 'request' else right_types - left_types
    if incompatible:
        changes.append(dict(location, kind=direction + '_type_incompatible'))
    if 'object' in left_types and 'object' in right_types:
        lost = right_required - left_required if direction == 'request' else left_required - right_required
        for name in sorted(lost):
            changes.append(dict(location, kind='new_required_request_property' if direction == 'request' else 'response_required_guarantee_removed', name=name))
        old_props, new_props = left.get('properties', {}), right.get('properties', {})
        for name in sorted(old_props.keys() | new_props.keys()):
            child_path = schema_path + '[' + json.dumps(name) + ']'
            if name not in old_props or name not in new_props:
                warnings.append(dict(context, schema_path=child_path, reason='Property added/removed; interaction with additional properties not checked'))
                continue
            found, skipped = compare_schema(old_props[name], new_props[name], context, child_path, depth + 1, left_root, right_root)
            changes.extend(found); warnings.extend(skipped)
    if 'array' in left_types and 'array' in right_types and ('items' in left or 'items' in right):
        found, skipped = compare_schema(left.get('items', {}), right.get('items', {}), context, schema_path + '[*]', depth + 1, left_root, right_root)
        changes.extend(found); warnings.extend(skipped)
    return changes, warnings


def compare_contracts(before, after, operations):
    changes, warnings = [], []
    for method, path in sorted(operations):
        old = before['paths'][path][method]
        new = after['paths'][path][method]
        label = f'{method.upper()} {path}'
        old_body, new_body = old.get('requestBody', {}), new.get('requestBody', {})
        if isinstance(old_body, dict) and isinstance(new_body, dict) and '$ref' not in old_body and '$ref' not in new_body:
            if new_body.get('required') is True and old_body.get('required') is not True:
                changes.append({'kind': 'new_required_request_body', 'operation': label})
        pairs = [('request', 'body', old_body, new_body)]
        old_responses, new_responses = old.get('responses', {}), new.get('responses', {})
        if isinstance(old_responses, dict) and isinstance(new_responses, dict):
            for status in sorted(old_responses.keys() - new_responses.keys()):
                changes.append({'kind': 'response_status_removed', 'operation': label, 'direction': 'response', 'status': str(status)})
            pairs += [('response', str(status), old_responses[status], new_responses[status]) for status in sorted(old_responses.keys() & new_responses.keys())]
        for direction, status, left, right in pairs:
            context = {'operation': label, 'direction': direction, 'status': status}
            if not isinstance(left, dict) or not isinstance(right, dict) or '$ref' in left or '$ref' in right:
                warnings.append(dict(context, reason='Referenced or malformed body/response not checked'))
                continue
            if direction == 'response':
                left_headers, right_headers = left.get('headers', {}), right.get('headers', {})
                if not isinstance(left_headers, dict) or not isinstance(right_headers, dict):
                    warnings.append(dict(context, reason='Malformed response headers object not checked'))
                else:
                    old_names = {name.lower(): name for name in left_headers if isinstance(name, str)}
                    new_names = {name.lower(): name for name in right_headers if isinstance(name, str)}
                    valid = (len(old_names) == len(left_headers) and len(new_names) == len(right_headers))
                    if not valid:
                        warnings.append(dict(context, reason='Response header names must be unique case-insensitive strings'))
                    else:
                        for normalized in sorted(old_names.keys() - new_names.keys()):
                            changes.append(dict(context, kind='response_header_removed', name=old_names[normalized]))
            left_content, right_content = left.get('content', {}), right.get('content', {})
            if not isinstance(left_content, dict) or not isinstance(right_content, dict):
                warnings.append(dict(context, reason='Malformed content object not checked'))
                continue
            if 'application/json' in left_content and 'application/json' not in right_content:
                changes.append(dict(context, kind=direction + '_json_media_type_removed'))
                continue
            if 'application/json' not in left_content or 'application/json' not in right_content:
                continue
            try:
                left_media, right_media = left_content['application/json'], right_content['application/json']
                if not isinstance(left_media, dict) or not isinstance(right_media, dict):
                    raise ValueError('Malformed media type object')
                found, skipped = compare_schema(left_media.get('schema', {}), right_media.get('schema', {}), context, left_root=before, right_root=after)
            except ValueError as error:
                warnings.append(dict(context, reason=str(error)))
                continue
            changes.extend(found)
            warnings.extend(skipped)
    return changes, warnings

