"""Run a frozen offline speech evaluation; all detailed output stays private."""
import argparse
from importlib.metadata import PackageNotFoundError
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'backend'))
from core.speech_runner import run_evaluation
from core.speech_evaluation import load_profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['development','holdout','controls','historical'], required=True)
    parser.add_argument('--freeze', type=Path, required=True)
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--profile', type=Path, help='Explicit candidate configuration matching the freeze')
    parser.add_argument('--registration', type=Path)
    parser.add_argument('--development', type=Path)
    args = parser.parse_args()
    try:
        if not args.out.resolve().is_relative_to((ROOT/'.qa').resolve()):
            raise ValueError('Detailed reports must stay inside this checkout .qa directory')
        frozen = json.loads(args.freeze.read_text(encoding='utf-8'))
        registration = json.loads(args.registration.read_text(encoding='utf-8')) if args.registration else None
        report = run_evaluation(args.dataset, args.mode, frozen, args.model_dir, args.out,
            ROOT/'.qa/speech-evaluation/exposure.sqlite3', registration=registration, development_path=args.development,
            candidate_profile=load_profile(args.profile) if args.profile else None)
        print(json.dumps({'run_id':report['run_id'],'status':report['status'],'clips':len(report['clips']),
            'mode':args.mode,'quality_validated':False,'release_review_eligible':report['summary']['release_review_eligible']}))
        return 0 if report['status']=='completed' else 1
    except (ValueError, OSError, KeyError, TypeError, PackageNotFoundError) as error:
        print(json.dumps({'success':False,'error_type':type(error).__name__,
                         'message':'Evaluation input, exposure or environment check failed; no private details logged'}))
        return 2


if __name__=='__main__':
    raise SystemExit(main())
