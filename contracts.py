"""Partial, directional checks for inline application/json body contracts."""
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
                left_types, left_required = inline_schema(left_media.get('schema', {}))
                right_types, right_required = inline_schema(right_media.get('schema', {}))
            except ValueError as error:
                warnings.append(dict(context, reason=str(error)))
                continue
            incompatible = left_types - right_types if direction == 'request' else right_types - left_types
            if incompatible:
                changes.append(dict(context, kind=direction + '_type_incompatible'))
            # Required applies only to objects; no property-level type inference is attempted.
            if 'object' in left_types and 'object' in right_types:
                lost = right_required - left_required if direction == 'request' else left_required - right_required
                for name in sorted(lost):
                    changes.append(dict(context, kind='new_required_request_property' if direction == 'request' else 'response_required_guarantee_removed', name=name))
    return changes, warnings
