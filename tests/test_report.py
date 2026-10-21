import unittest
from report import render_report

class ReportTests(unittest.TestCase):
    def test_report_counts_filters_and_escapes_findings(self):
        result={'scope':'partial <check>','breaking_changes':[{'kind':'removed_operation','operation':'GET /pets?<x>'}],'coverage_warnings':[{'kind':'unsupported','path':'$["x"]'}]}
        html=render_report(result)
        self.assertIn('Breaking only',html);self.assertIn('data-kind="breaking"',html);self.assertIn('data-kind="warning"',html)
        self.assertIn('GET /pets?&lt;x&gt;',html);self.assertNotIn('partial <check>',html)
