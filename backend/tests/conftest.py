# backend/tests/conftest.py
#
# Point the app at a throwaway SQLite DB for the whole test session, BEFORE
# any backend module is imported. This keeps tests off the dev database and
# stops state from accumulating between runs (which was making the ML API
# tests flaky).

import os
import tempfile

_TEST_DB_DIR = tempfile.mkdtemp(prefix="cardoptimizer-tests-")
os.environ["CARDOPTIMIZER_DB"] = os.path.join(_TEST_DB_DIR, "test.db")

from backend.database.connection import init_db  # noqa: E402

init_db()
