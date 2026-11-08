"""Local operator maintenance. These functions are not HTTP or MCP endpoints."""
from pathlib import Path
from contextlib import closing
import os
import sqlite3


def backup_database(source: Path, destination: Path):
    """Take a consistent online SQLite snapshot; never overwrite another backup."""
    source, destination = Path(source), Path(destination)
    if not source.is_file():
        raise ValueError('Arena database does not exist')
    # Reserve a private file before opening SQLite; O_EXCL also rejects symlinks.
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)
    try:
        with closing(sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True)) as origin:
            with closing(sqlite3.connect(destination)) as target:
                origin.backup(target)
                if target.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                    raise RuntimeError('Backup integrity verification failed')
    except BaseException:
        destination.unlink(missing_ok=True)
        raise


def reset_password(arena, handle, password):
    """Operator recovery after identity verification; revoke all owner access."""
    if not 12 <= len(password) <= 128:
        raise ValueError('Password must contain 12–128 characters')
    password_hash = arena.passwords.hash(password)
    with arena.db.connect(write=True) as db:
        row = db.execute('SELECT id FROM users WHERE handle=?', (handle,)).fetchone()
        if not row:
            raise ValueError('Account not found')
        db.execute('UPDATE users SET password_hash=? WHERE id=?', (password_hash, row['id']))
        db.execute('UPDATE credentials SET revoked=1 WHERE owner_id=?', (row['id'],))
        arena.audit(db, 'operator-cli', 'account.password_reset', row['id'])
