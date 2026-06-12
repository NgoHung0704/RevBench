from data_pipeline.universe import HORIZON_DAYS, TICKERS, UNIVERSE


def test_universe_size_and_uniqueness():
    assert len(UNIVERSE) == 15
    assert len(set(TICKERS)) == len(TICKERS)


def test_tickers_are_normalized():
    assert all(t == t.upper() and t.isalpha() for t in TICKERS)


def test_horizon_matches_decision_d9():
    assert HORIZON_DAYS == 5
