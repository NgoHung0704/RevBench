import duckdb
import pytest

from data_pipeline.publish import publish_read_replica, read_replica_path


def make_store(path, rows: int) -> None:
    con = duckdb.connect(str(path))
    con.execute("CREATE TABLE IF NOT EXISTS t (i INTEGER)")
    con.execute("DELETE FROM t")
    con.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(rows)])
    con.close()


def count(path) -> int:
    con = duckdb.connect(str(path), read_only=True)
    try:
        return con.execute("SELECT count(*) FROM t").fetchone()[0]
    finally:
        con.close()


def test_replica_path_naming(tmp_path):
    assert read_replica_path(tmp_path / "revbench.duckdb").name == "revbench-read.duckdb"


def test_publish_copies_current_contents(tmp_path):
    src = tmp_path / "revbench.duckdb"
    make_store(src, 3)

    dst = publish_read_replica(src)

    assert dst == read_replica_path(src)
    assert count(dst) == 3


def test_publish_overwrites_previous_snapshot(tmp_path):
    src = tmp_path / "revbench.duckdb"
    make_store(src, 1)
    publish_read_replica(src)

    make_store(src, 5)
    dst = publish_read_replica(src)

    assert count(dst) == 5
    # no temp file left behind — the swap is a rename, not a partial copy
    assert not list(tmp_path.glob(".*.tmp"))


def test_replica_is_readable_while_writer_holds_the_lock(tmp_path):
    """The whole point of R11: a reader must survive an open writer."""
    src = tmp_path / "revbench.duckdb"
    make_store(src, 2)
    dst = publish_read_replica(src)

    writer = duckdb.connect(str(src))  # holds the single-writer lock
    try:
        # Opening the live store read-only is refused while the writer holds it
        # (IOException across processes, ConnectionException within one).
        with pytest.raises((duckdb.IOException, duckdb.ConnectionException)):
            duckdb.connect(str(src), read_only=True)
        assert count(dst) == 2  # ...but the published snapshot still reads fine
    finally:
        writer.close()


def test_publish_missing_store_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        publish_read_replica(tmp_path / "nope.duckdb")
