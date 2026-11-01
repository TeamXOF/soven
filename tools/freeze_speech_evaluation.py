"""Freeze a cached baseline or preregister private speech data. Never runs STT."""
import argparse
from importlib.metadata import PackageNotFoundError
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from core.speech_evaluation import (load_profile, freeze_baseline, verify_freeze,
                                    register_evaluation, write_new_receipt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    commands.add_parser('check')
    freeze = commands.add_parser('freeze')
    freeze.add_argument('--model-dir', type=Path, required=True)
    freeze.add_argument('--out', type=Path, required=True)
    verify = commands.add_parser('verify')
    verify.add_argument('--freeze', type=Path, required=True)
    register = commands.add_parser('register')
    register.add_argument('--freeze', type=Path, required=True)
    register.add_argument('--development', type=Path, required=True)
    register.add_argument('--holdout', type=Path, required=True)
    register.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        profile = load_profile()
        if args.action == 'check':
            print(json.dumps({'profile_id': profile['profile_id'], 'languages': list(profile['language_criteria']),
                              'inference_performed': False, 'quality_validated': False}))
            return 0
        if hasattr(args, 'out') and not args.out.resolve().is_relative_to((ROOT / '.qa').resolve()):
            raise ValueError('Private receipts must be written inside this checkout .qa directory')
        if args.action == 'freeze':
            result = freeze_baseline(args.model_dir, profile)
        else:
            frozen = json.loads(args.freeze.read_text(encoding='utf-8'))
            verify_freeze(frozen)
            if args.action == 'verify':
                print(json.dumps({'freeze_verified': True, 'inference_performed': False}))
                return 0
            result = register_evaluation(args.development, args.holdout, frozen)
        write_new_receipt(args.out, result)
        print(json.dumps({'written': True, 'kind': result['kind'], 'receipt_sha256': result['receipt_sha256'],
                          'inference_performed': False, 'quality_validated': False}))
        return 0
    except (ValueError, OSError, KeyError, TypeError, PackageNotFoundError) as error:
        # Private paths, reference text and identifiers must not leak to shell logs.
        print(json.dumps({'success': False, 'error_type': type(error).__name__,
                          'message': str(error) if isinstance(error, ValueError) else 'Invalid or inaccessible private evaluation input'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
