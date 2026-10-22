import unittest
from annotations import annotation,render_annotations
class AnnotationTests(unittest.TestCase):
    def test_breaks_and_warnings_have_stable_levels(self):
        text=render_annotations([{'kind':'removed_operation','operation':'GET /pets'}],[{'reason':'Constraints not checked: enum','operation':'GET /pets'}],'after.json')
        self.assertEqual(text.count('\n'),1);self.assertTrue(text.startswith('::error '));self.assertIn('\n::warning ',text)
    def test_workflow_control_characters_are_escaped(self):
        text=annotation('warning',{'reason':'line\nvalue: 50%,','operation':'GET /x'},'spec:after,json')
        self.assertIn('file=spec%3Aafter%2Cjson',text);self.assertIn('line%0Avalue: 50%25,',text)
