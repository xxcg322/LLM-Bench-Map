import unittest
from run import field_counts, select, equal


class AnalysisTests(unittest.TestCase):
    def test_missing_is_not_negative(self):
        r=field_counts([{'tags':{'x':['a']}},{'tags':{'x':None}},{'tags':{'x':['unclear']}}],'x','a')
        self.assertEqual((r['n'],r['valid_n'],r['missing_n'],r['known_n']),(1,2,1,1))
        self.assertEqual(r['known_share'],1)

    def test_multilabel_denominator(self):
        rows=[{'tags':{'x':['a','b']}},{'tags':{'x':['b']}}]
        self.assertEqual(field_counts(rows,'x','a')['share']+field_counts(rows,'x','b')['share'],1.5)

    def test_empty(self):
        self.assertIsNone(field_counts([],'x','a')['share'])

    def test_date_boundaries(self):
        r=[{'month':'2024-08','year':'2024'},{'month':'2024-09','year':'2024'},{'month':'2025-01','year':'2025'}]
        self.assertEqual(len(select(r,'jan_aug','2024')),1)
        self.assertEqual(len(select(r,'observed','2024')),2)
        self.assertEqual(len(select(r,'jan_aug','all')),2)

    def test_comparison_detects_difference(self):
        with self.assertRaises(AssertionError):equal({'n':1},{'n':2})


if __name__=='__main__':unittest.main()
