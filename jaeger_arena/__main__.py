import argparse
import json
from pathlib import Path
import os


def main():
    parser = argparse.ArgumentParser(description='Jaeger Arena server and operator tools')
    commands = parser.add_subparsers(dest='command')
    serve = commands.add_parser('serve', help='Run the Arena API, app, and authenticated MCP server')
    serve.add_argument('--host', default='127.0.0.1')
    serve.add_argument('--port', type=int, default=8792)
    key = commands.add_parser('evaluator-key', help='Create a scoped evaluator credential in a private file')
    key.add_argument('--label', required=True)
    key.add_argument('--output', type=Path, required=True)
    key.add_argument('--days', type=int, default=7, choices=range(1,31))
    revoke = commands.add_parser('revoke-evaluator', help='Revoke an evaluator key by its ID')
    revoke.add_argument('key_id')
    args = parser.parse_args()
    if args.command in (None, 'serve'):
        import uvicorn
        uvicorn.run('jaeger_arena.app:create_app', factory=True, host=getattr(args,'host','127.0.0.1'), port=getattr(args,'port',8792))
        return
    from .service import Arena
    from .settings import Settings
    arena = Arena(Settings.from_env())
    if args.command == 'evaluator-key':
        # Exclusive creation and restrictive mode: never overwrite an existing credential.
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, 'w') as out:
                result = arena.evaluator_key('skill-practice', args.label, args.days)
                json.dump(result, out)
                out.write('\n')
        except BaseException:
            args.output.unlink(missing_ok=True)
            raise
        print('Evaluator credential saved. Keep this file private; do not commit it.')
    else:
        with arena.db.connect(write=True) as db:
            changed = db.execute("UPDATE credentials SET revoked=1 WHERE id=? AND kind='evaluator'", (args.key_id,)).rowcount
            if not changed:
                parser.error('Evaluator key not found')
            arena.audit(db, 'operator-cli', 'evaluator.revoked', args.key_id)
        print('Evaluator credential revoked.')


if __name__ == '__main__':
    main()
