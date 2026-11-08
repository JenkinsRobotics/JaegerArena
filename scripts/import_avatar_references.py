#!/usr/bin/env python3
"""Snapshot declared traits and source references, never prompts, code, or earned levels."""
import argparse
import hashlib
import json
from pathlib import Path
import yaml


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('repository',type=Path,help='Path to the JaegerAvatar checkout')
    args=parser.parse_args()
    root=args.repository.resolve()
    profiles=[]
    for path in sorted((root/'avatar-packs').glob('*/avatar.yaml')):
        pack=yaml.safe_load(path.read_text())
        if pack.get('schema')!='avatar/v1':
            raise ValueError(f'Unsupported pack schema: {path}')
        for key,value in pack.get('profiles',{}).items():
            character=value.get('character',{})
            profiles.append({'id':pack['avatar']+':'+key,'avatar':pack['avatar'],'profile':key,'name':pack['name'],
                'version':str(pack.get('version','')),'traits':character.get('traits',{}),
                'provenance':{'repository':'https://github.com/JenkinsRobotics/JaegerAvatar','path':str(path.relative_to(root)),
                'manifest_sha256':hashlib.sha256(path.read_bytes()).hexdigest()},'classification':'declared_character_traits'})
    if not profiles:
        raise ValueError('No avatar/v1 profiles found')
    target=Path(__file__).resolve().parents[1]/'jaeger_arena/data/avatar_profiles.json'
    payload=json.dumps({'schema':'arena.avatar-reference/v1','profiles':profiles},indent=2,allow_nan=False)+'\n'
    target.write_text(payload)
    print(f'Wrote {len(profiles)} character references; no earned progress imported.')


if __name__=='__main__':
    main()
