import csv, pathlib, runpy, tempfile, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT = runpy.run_path(str(ROOT / 'scripts/data_audit.py'))['audit']

class RegressionR32(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)

    def write(self, fields, rows):
        with (self.root / 'data.csv').open('w', encoding='utf8', newline='') as f:
            writer = csv.writer(f); writer.writerow(fields); writer.writerows(rows)

    def scan(self, **kwargs):
        result = AUDIT(self.root, dict(files=['data.csv'], period='month', **kwargs))
        self.assertEqual(result['status'], 'RECORDED', result.get('errors'))
        return result['files'][0]

    def test_01_late_columns_all_checks(self):
        fields = ['date', 'source'] + ['value_%03d' % i for i in range(200)]
        def rows():
            for i in range(20000):
                month = i % 6 + 1; source = 'ABCD'[(i // 6) % 4]
                values = ['100.5'] * 200
                if month >= 4: values[149] = '10.05'
                if month >= 3 and source == 'A': values[189] = '10.05'
                yield ['2032-%02d-01' % month, source] + values
        self.write(fields, rows()); result = self.scan()
        self.assertTrue(result['complete_rows'])
        signals = result['tables'][0]['scale_suspects']
        self.assertTrue(any(x['column']=='value_149' and x['kind']=='PERIOD' and x['after_period']=='2032-04' for x in signals))
        self.assertTrue(any(x['column']=='value_189' and x['kind']=='SOURCE_PERIOD' and x['source_value']=='A' and x['after_period']=='2032-03' for x in signals))

    def test_02_explicit_scale_columns(self):
        self.write(['date','left','right'], (['2032-%02d-01'%m, '100.5' if m<4 else '10.05', '200.5' if m<4 else '20.05'] for m in range(1,7) for _ in range(20)))
        table = self.scan(scale_columns=['right'])['tables'][0]
        self.assertTrue(any(x['column']=='right' for x in table['scale_suspects']))
        self.assertFalse(any(x['column']=='left' for x in table['scale_suspects']))

    def test_03_integer_codes_excluded_measurement_kept(self):
        self.write(['date','source','code','measurement'], (['2032-%02d-01'%m, 'ABCD'[i%4], (0 if i%4 else 2+i%29), '100.5' if m<4 else '10.05'] for m in range(1,7) for i in range(120)))
        table = self.scan()['tables'][0]
        self.assertTrue(table['numeric_ranges']['code']['treated_as_code'])
        self.assertFalse(any(x['column']=='code' for x in table['scale_suspects']))
        self.assertTrue(any(x['column']=='measurement' and x['kind']=='PERIOD' for x in table['scale_suspects']))

    def test_04_only_over_512_skipped(self):
        fields=['date']+['m%03d'%i for i in range(520)]
        self.write(fields, (['2032-%02d-01'%m]+['100.5' if m<4 else '10.05']*520 for m in range(1,7) for _ in range(2)))
        result=self.scan(); table=result['tables'][0]
        self.assertEqual(len(table['scale_sampling']['columns']),512)
        omitted={x['column'] for x in result['analysis_limits'] if x['reason']=='numeric column budget exceeded'}
        self.assertEqual(omitted, set(fields[-8:]))
        self.assertEqual(sum(x['reason']=='numeric column budget exceeded' for x in result['analysis_limits']),8)
        self.assertTrue(any(x['column']=='m511' for x in table['scale_suspects']))

    def test_integer_measurement_above_100_not_code(self):
        self.write(['date','thickness'], (['2032-%02d-01'%m, (495+i%11 if m<4 else 45+i%11)] for m in range(1,7) for i in range(110)))
        table=self.scan()['tables'][0]
        self.assertFalse(table['numeric_ranges']['thickness']['treated_as_code'])
        self.assertTrue(any(x['column']=='thickness' and x['kind']=='PERIOD' for x in table['scale_suspects']))

    def test_large_named_code_and_late_fraction(self):
        self.write(['date','item_number','measurement'], (['2032-%02d-01'%m, 500 if m<4 else 50, 100 if m<4 else (10.5 if i==0 else 10)] for m in range(1,7) for i in range(30)))
        table=self.scan(max_rows=10)['tables'][0]
        self.assertTrue(table['numeric_ranges']['item_number']['treated_as_code'])
        self.assertFalse(table['numeric_ranges']['measurement']['treated_as_code'])
        self.assertTrue(any(x['column']=='measurement' for x in table['scale_suspects']))
        self.assertFalse(any(x['column']=='item_number' for x in table['scale_suspects']))

    def test_explicit_last_column_beyond_512(self):
        fields=['date']+['m%03d'%i for i in range(520)]
        self.write(fields, (['2032-%02d-01'%m]+['100.5' if m<4 else '10.05']*520 for m in range(1,7) for _ in range(2)))
        table=self.scan(scale_columns=['m519'])['tables'][0]
        self.assertEqual(table['scale_sampling']['columns'], ['m519'])
        self.assertTrue(any(x['column']=='m519' for x in table['scale_suspects']))

    def test_nonnumeric_value_disqualifies_integer_code(self):
        self.write(['date','measurement'], (['2032-%02d-01'%m, ('unknown' if m==2 and i==0 else (100 if m<4 else 10))] for m in range(1,7) for i in range(30)))
        table=self.scan()['tables'][0]
        self.assertFalse(table['numeric_ranges']['measurement']['treated_as_code'])
        self.assertTrue(any(x['column']=='measurement' for x in table['scale_suspects']))

    def test_batched_source_sampling_and_high_cardinality_removal(self):
        self.write(['record','source','measurement'], (['key%d'%i, 'AB'[i%2], '10.05' if i%2==0 else '100.5'] for i in range(10000)))
        result=self.scan(); table=result['tables'][0]
        self.assertTrue(result['complete_rows'])
        self.assertTrue(any(x['kind']=='SOURCE' and x['column']=='measurement' and x['source_value']=='A' for x in table['scale_suspects']))
        self.assertFalse(any(x.get('source_column')=='record' for x in table['scale_suspects']))

    def test_batched_source_sampling_with_many_distinct_values(self):
        self.write(['source','measurement'], (['AB'[i%2], (10.05+i%151/10000 if i%2==0 else 100.5+i%151/1000)] for i in range(5000)))
        table=self.scan()['tables'][0]
        self.assertTrue(any(x['kind']=='SOURCE' and x['column']=='measurement' for x in table['scale_suspects']))

if __name__ == '__main__': unittest.main()
