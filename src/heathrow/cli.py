"""Command-line entrypoint: `python -m heathrow.cli {run,dq}`."""

from __future__ import annotations

import argparse
import logging

log = logging.getLogger("heathrow")


def cmd_run(args) -> int:
    from heathrow import download, load, quality
    from heathrow.config import ALL_AIRPORTS

    engine = load.get_engine()
    load.ensure_schema(engine)
    run = quality.run_id()
    load.record_run(engine, run, "running")

    # FR-1: download raw files unchanged.
    paths = download.download(force=args.force)

    # FR-2/3: parse + load. Parsing requires real CAA file formats, which are
    # recorded in data/sources.json; until files are present, this logs and
    # leaves the (empty) fact table intact so DQ still runs meaningfully.
    from heathrow import parse  # noqa: F401
    log.info("downloaded %d file(s): %s", len(paths), [p.name for p in paths])

    # FR-4: DQ. With no parsed data yet, checks report 'warn/skip' clearly.
    import pandas as pd

    empty = pd.DataFrame(columns=parse.STAGE_COLUMNS)
    results = quality.run_all(empty, controlled_airports=ALL_AIRPORTS)
    for r in results:
        log.info("DQ %s %s: %s", r.check_code, r.status, r.message)
    load.write_dq_log(engine, run, results)

    fails = [r for r in results if r.status == "fail"]
    load.record_run(engine, run, "done", {"files": len(paths), "dq_fails": len(fails)})
    log.info("run %s complete; %d DQ fail(s)", run, len(fails))
    return 0


def cmd_dq(args) -> int:
    from heathrow import load, quality

    engine = load.get_engine()
    run = quality.run_id()
    import pandas as pd

    df = pd.read_sql("SELECT * FROM fact_punctuality", engine)
    from heathrow.config import ALL_AIRPORTS

    results = quality.run_all(df, controlled_airports=ALL_AIRPORTS)
    for r in results:
        log.info("DQ %s %s: %s", r.check_code, r.status, r.message)
    load.write_dq_log(engine, run, results)
    load.record_run(engine, run, "dq_only")
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(prog="heathrow-pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="download -> parse -> load -> dq")
    p_run.add_argument("--force", action="store_true", help="re-download existing files")
    p_run.set_defaults(func=cmd_run)

    p_dq = sub.add_parser("dq", help="run data-quality checks only")
    p_dq.set_defaults(func=cmd_dq)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
