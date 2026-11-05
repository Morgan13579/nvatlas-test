import csv, importlib.util, json, random, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('build_data',ROOT/'scripts/build_data.py')
build_data=importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_data)
class CorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'data/corpus.json').read_text())
        with (ROOT/'NVAtlas-AI-Agent.csv').open(encoding='utf-8-sig',newline='') as f: cls.raw=list(csv.DictReader(f))
    def test_original_text_and_ids_preserved(self):
        self.assertEqual(len(self.raw),500)
        for raw,row in zip(self.raw,self.data['records']):
            self.assertEqual(raw['id'],row['id'])
            self.assertEqual(raw['English'].strip(),row['source_text'])
            self.assertEqual(raw['Chinese'].strip(),row['target_text'])
            self.assertTrue(set(['source_text','target_text','source','category','human_checked']).issubset(row))
    def test_reproducible_samples(self):
        rows=[r for r in self.data['records'] if r['duplicate_of'] is None]
        for field,size,seed in [('review_ids',50,20261105),('pilot_ids',25,20261104)]:
            expected=[r['id'] for r in random.Random(seed).sample(rows,size)]
            self.assertEqual(self.data['metadata'][field],expected); self.assertEqual(len(set(expected)),size)
    def test_determiners_do_not_trigger_verb_warning(self):
        by_id={r['id']:r for r in self.raw}
        self.assertEqual(build_data.classify(by_id['2036'])[0],'review')
        self.assertEqual(build_data.classify(by_id['188270'])[0],'other-frame')
        self.assertEqual(build_data.classify(by_id['296458'])[0],'other-frame')
    def test_codebook_examples(self):
        by_id={r['id']:r for r in self.raw}
        for rid,category in [('13113','support-verb'),('5884','prepositional'),('5355','standalone'),('168','other-frame')]: self.assertEqual(build_data.classify(by_id[rid])[0],category)
    def test_no_false_verification_or_provenance(self):
        self.assertTrue(all(r['human_checked']=='no' for r in self.data['records']))
        self.assertIsNone(self.data['provenance']['corpus_name']); self.assertIsNone(self.data['provenance']['original_sampling_seed'])
if __name__=='__main__': unittest.main()
