#!/usr/bin/env python3

import unittest

import mistune

from fuzz_mistune import find_unescaped_quote_issues


class MistuneQuoteHarnessTest(unittest.TestCase):
    """Regression tests for the exercise3 quote detector."""

    def test_escaped_quote_entity_is_not_flagged(self):
        html = mistune.Markdown()('[](")')
        self.assertEqual(find_unescaped_quote_issues(html), [])

    def test_single_quoted_attribute_with_double_quote_is_not_flagged(self):
        html = "<p><a href='\"'></a></p>"
        self.assertEqual(find_unescaped_quote_issues(html), [])


if __name__ == "__main__":
    unittest.main()
