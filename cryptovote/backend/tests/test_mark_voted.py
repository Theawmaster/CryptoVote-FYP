from types import SimpleNamespace as NS
from datetime import datetime
import routes.cast_vote as cv

def test_mark_voted_creates_or_updates(monkeypatch):
    added = []
    # Stub VES model with a minimal shape
    class _VES:
        def __init__(self, voter_id, election_id):
            self.voter_id = voter_id
            self.election_id = election_id
            self.voted_at = None

    # Stub VES.query.one_or_none() to simulate "no existing row"
    class _Q:
        def filter_by(self, **kw): return self
        def one_or_none(self): return None

    _ves_model = _VES
    _ves_model.query = _Q()
    monkeypatch.setattr(cv, "VES", _ves_model)

    # Stub db.session to capture what gets added/committed
    class _Sess:
        def add(self, obj): added.append(obj)
        def commit(self): pass
    monkeypatch.setattr(cv.db, "session", _Sess())

    # Act
    cv.mark_voted(voter_id=1, election_id="E")

    # Assert: a new VES was created and voted_at set
    assert len(added) == 1
    row = added[0]
    assert row.voter_id == 1
    assert row.election_id == "E"
    assert row.voted_at is not None
    assert isinstance(row.voted_at, datetime)
