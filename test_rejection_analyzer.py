import os
import rejection_analyzer as m
import pathlib

def test_lookup():
    r = m.lookup('hemolyzed sample')
    assert 'top_hit' in r and 'score' in r
    assert r['top_hit'] == 'Hemolyzed Sample'
    assert r['score'] > 0

def test_process_csv():
    pdir = pathlib.Path(__file__).parent
    out_path = pdir / 'tmp_test_out.csv'
    try:
        rows = m.process_csv(str(pdir / 'sample.csv'), str(out_path))
        assert len(rows) >= 1
        assert 'top_hit' in rows[0]
    finally:
        if out_path.exists():
            os.unlink(out_path)
