#!/usr/bin/env python3
"""Verify that a QGIS auth DB master password matches its qgis-auth.db.

This mimics the exact check G3W-Suite runs on startup
(g3w-admin/qdjango/apps.py, init_qgis -> authManager().setMasterPassword(pw, True)),
so a mismatch can be caught before uploading files to the server.

Must be run in an environment with PyQGIS installed (e.g. inside the
g3w-suite docker image via check-qgis-auth-password.sh).

Usage:
    python3 check_qgis_auth_password.py <qgis-auth.db> <password.txt>
"""
import os
import shutil
import sys
import tempfile


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <qgis-auth.db> <password.txt>", file=sys.stderr)
        return 2

    db_path, password_path = sys.argv[1], sys.argv[2]

    if not os.path.isfile(db_path):
        print(f"ERROR: db file not found: {db_path}", file=sys.stderr)
        return 2
    if not os.path.isfile(password_path):
        print(f"ERROR: password file not found: {password_path}", file=sys.stderr)
        return 2

    with open(password_path, "r") as f:
        password = f.read().strip()

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    # Copy to a throwaway dir so we never touch/lock the original db.
    tmp_dir = tempfile.mkdtemp(prefix="qgis_auth_check_")
    shutil.copy(db_path, os.path.join(tmp_dir, "qgis-auth.db"))
    os.environ["QGIS_AUTH_DB_DIR_PATH"] = tmp_dir

    from qgis.core import QgsApplication

    app = QgsApplication([], False)
    app.initQgis()
    auth_manager = app.authManager()

    if auth_manager.isDisabled():
        print("ERROR: QGIS AuthManager is disabled in this environment", file=sys.stderr)
        return 2

    ok = auth_manager.setMasterPassword(password, True)
    app.exitQgis()
    shutil.rmtree(tmp_dir, ignore_errors=True)

    print("MATCH" if ok else "MISMATCH")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
