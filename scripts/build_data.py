"""Reproducibly normalize the supplied CSV; never invent provenance or verification."""
import csv
import hashlib
import json
import random
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261105
CATEGORIES = ['support-verb', 'prepositional', 'standalone', 'other-frame', 'review']


def classify(row):
    en, zh, term, verb = (row[k].strip() for k in ['English', 'Chinese', 'English_Nominal', 'Chinese_Verb'])
    match = re.search(r'\b' + re.escape(term) + r'(?:s|es)?\b', en, re.I) if term else None
    if not match or not verb or verb not in zh:
        return 'review', 'An annotated term is absent from the corresponding sentence.'
    if re.search(r'\b(?:(?:see|watch|let)\s+(?:(?:her|him|them|us|me)\s+)?|(?:can|could|will|would|to)\s+)' + re.escape(term) + r'\b', en, re.I) and term.lower() in {'dance', 'help', 'look', 'work', 'call', 'talk', 'walk', 'run'}:
        return 'review', 'The English label may be a verb in this context; inspect its word class.'
    prefix = en[:match.start()].lower()
    if not prefix.strip(' -—\"\'♪') and re.match(r'\s*!', en[match.end():]):
        return 'standalone', 'The annotated nominal opens an exclamation without a preceding word.'
    if re.search(r'\b(?:make|makes|made|making|take|takes|took|taking|give|gives|gave|giving|have|has|had|having|pay|pays|paid|paying)\s+(?:[\w\x27-]+\s+){0,3}$', prefix):
        return 'support-verb', 'A listed support-verb form occurs within three intervening words before the nominal.'
    if re.search(r'\b(?:in|on|with|without|for|under|of|after|before|at)\s+(?:[\w\x27-]+\s+){0,2}$', prefix):
        return 'prepositional', 'A listed preposition occurs within two intervening words before the nominal.'
    return 'other-frame', 'The labels are present, but none of the narrower construction rules matches.'


def build():
    raw_path = ROOT / 'NVAtlas-AI-Agent.csv'
    with raw_path.open(encoding='utf-8-sig', newline='') as handle:
        raw = list(csv.DictReader(handle))
    provenance = json.loads((ROOT / 'data/provenance.json').read_text())
    overrides = {}
    annotation_path = ROOT / 'data/annotations.csv'
    if annotation_path.exists():
        with annotation_path.open(encoding='utf-8-sig', newline='') as handle:
            for item in csv.DictReader(handle):
                if item['id'] in overrides:
                    raise ValueError('Duplicate annotation ID: ' + item['id'])
                overrides[item['id']] = item
    rows, seen, ids = [], {}, set()
    for item in raw:
        rid = item['id'].strip()
        if rid in ids:
            raise ValueError('Duplicate record ID: ' + rid)
        ids.add(rid)
        category, reason = classify(item)
        source_text, target_text = item['English'].strip(), item['Chinese'].strip()
        pair = (source_text, target_text)
        duplicate_of = seen.get(pair)
        seen.setdefault(pair, rid)
        source = f'User-supplied NVAtlas-AI-Agent.csv; row id {rid}; original source unconfirmed'
        if provenance['corpus_name']:
            source = f"{provenance['corpus_name']}; version {provenance['version'] or 'unknown'}; row id {rid}; collected {provenance['collection_date'] or 'unknown'}"
        override = overrides.get(rid, {})
        checked = override.get('human_checked', 'no') or 'no'
        if checked not in ('yes', 'no'):
            raise ValueError('human_checked must be yes or no: ' + rid)
        if checked == 'yes' and not (override.get('source') and override.get('checked_date') and override.get('notes')):
            raise ValueError('Verified rows need a source, checked_date and checking notes: ' + rid)
        category = override.get('category') or category
        if category not in CATEGORIES:
            raise ValueError('Unknown category: ' + category)
        rows.append(dict(id=rid, source_text=source_text, target_text=target_text,
                         source=override.get('source') or source,
                         source_url=override.get('source_url') or provenance['source_url'],
                         category=category, human_checked=checked, unit='sentence pair',
                         key_term=item['English_Nominal'].strip(), target_term=item['Chinese_Verb'].strip(),
                         annotation_status='human-reviewed' if checked == 'yes' else 'provisional',
                         category_reason=override.get('notes') or reason,
                         checked_date=override.get('checked_date') or None,
                         duplicate_of=duplicate_of,
                         sensitive=bool(re.search(r'\b(?:fuck\w*|shit\w*|bitch\w*|bastard\w*|damn\w*|asshole\w*|sex\w*|kill\w*|murder\w*|extermination)\b|强奸|強奸|他妈|他媽|混蛋|杀|殺|消灭|消滅', source_text+' '+target_text, re.I)),
                         english_words=len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", source_text)),
                         chinese_characters=len(re.findall(r'[\u3400-\u9fff]', target_text))))
    unknown = set(overrides) - ids
    if unknown:
        raise ValueError('Annotation IDs absent from input: ' + ', '.join(sorted(unknown)))
    unique = [r for r in rows if r['duplicate_of'] is None]
    sample = random.Random(SEED).sample(unique, min(50, len(unique)))
    pilot = random.Random(SEED - 1).sample(unique, min(25, len(unique)))
    stats = dict(records=len(rows), unique_pairs=len(unique), duplicate_records=len(rows)-len(unique),
                 human_checked=sum(r['human_checked']=='yes' for r in rows),
                 categories=dict(Counter(r['category'] for r in rows)),
                 english_terms=len({r['key_term'].lower() for r in rows}),
                 chinese_terms=len({r['target_term'] for r in rows}),
                 sensitive_records=sum(r['sensitive'] for r in rows),
                 input_sha256=hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                 review_seed=SEED, pilot_seed=SEED-1,
                 review_ids=[r['id'] for r in sample], pilot_ids=[r['id'] for r in pilot])
    payload = dict(metadata=stats, provenance=provenance, records=rows)
    (ROOT/'data/corpus.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    with (ROOT/'data/corpus.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)
    for name, selection in [('review-sample', sample), ('pilot-sample', pilot)]:
        # Templates are regenerated separately; completed work belongs in annotations.csv.
        fields = ['id','source_text','target_text','key_term','target_term','category','source','human_checked','checked_date','notes']
        with (ROOT/f'data/{name}.csv').open('w', encoding='utf-8-sig', newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=fields,extrasaction='ignore',lineterminator='\n')
            writer.writeheader(); writer.writerows(selection)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    build()
