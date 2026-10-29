"""Partial, directional checks for inline application/json body contracts."""
import json
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
    required = schema.get('required', [])
    properties = schema.get('properties', {})
    if not isinstance(required, list) or not all(isinstance(name, str) for name in required):
        raise ValueError('required must be an array of strings')
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
    def length_constraint(name,lower):
        old,new=left.get(name),right.get(name)
        if old is None and new is None:return
        if type(old) is not int or type(new) is not int or old<0 or new<0:
            warnings.append(dict(location,reason=name+' transition not checked unless both sides contain non-negative integers'));return
        tighter=(new>old if lower else new<old) if context['direction']=='request' else (new<old if lower else new>old)
        if tighter:changes.append(dict(location,kind=context['direction']+'_'+name+'_incompatible'))
    length_constraint('minLength',True);length_constraint('maxLength',False)
    length_constraint('minItems',True);length_constraint('maxItems',False)
    constraints = {'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum',
                   'multipleOf', 'minLength', 'maxLength', 'pattern', 'format', 'minItems',
                   'maxItems', 'uniqueItems', 'contains', 'prefixItems', 'additionalProperties',
                   'patternProperties', 'unevaluatedProperties', 'dependentRequired',
                   'dependentSchemas', 'minProperties', 'maxProperties'}
    checked={'minimum','maximum','exclusiveMinimum','exclusiveMaximum','minLength','maxLength','minItems','maxItems'}
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
            pairs += [('response', str(status), old_responses[status], new_responses[status]) for status in sorted(old_responses.keys() & new_responses.keys())]
        for direction, status, left, right in pairs:
            context = {'operation': label, 'direction': direction, 'status': status}
            if not isinstance(left, dict) or not isinstance(right, dict) or '$ref' in left or '$ref' in right:
                warnings.append(dict(context, reason='Referenced or malformed body/response not checked'))
                continue
            left_content, right_content = left.get('content', {}), right.get('content', {})
            if not isinstance(left_content, dict) or not isinstance(right_content, dict):
                warnings.append(dict(context, reason='Malformed content object not checked'))
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

