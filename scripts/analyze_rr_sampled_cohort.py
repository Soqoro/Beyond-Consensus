"""Read-only sampled-organization status/analysis; missing branches stay unknown."""
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from reporecourse.common import load,write_new
from reporecourse.sampled_cohort import analyze


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--proposal',type=Path,required=True)
    p.add_argument('--records',type=Path,help='Optional object mapping configuration IDs to saved results.')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    write_new(args.output,analyze(load(args.proposal),load(args.records) if args.records else {}))
    print('Read-only analysis:',args.output)

if __name__=='__main__':main()
