# G3 Evidence - Boundary Safety Repeatability

Parent contract: [2026-03-19-rag-sprint-planning-phase5-closure-contract.md](./2026-03-19-rag-sprint-planning-phase5-closure-contract.md)
Related packet: [2026-03-19-rag-sprint-planning-g2-integrated-evidence-packet.md](./2026-03-19-rag-sprint-planning-g2-integrated-evidence-packet.md)
Date: 2026-03-19

## Objective
Close G3 by demonstrating three consecutive boundary-safe windows under 4C separation policy, with explicit critical-leak detection and threshold checks.

## Method
- Command family: scripts/rag_index.py query
- Filter: --filter-governs endogenous-first
- Top-k: 5
- Consecutive windows: 3 (executed sequentially in one run)
- Critical leak rule (Phase 2-aligned): any forbidden-scope result appearing in the top-5.
	- For this check, forbidden scope means any returned result whose governs tokens do not include endogenous-first.
- Threshold target from prior gates:
  - critical leaks (forbidden-scope in top-5) = 0 per window
  - aggregate cross-scope leak rate <= 0.1%

## Window Results

| Window | UTC Timestamp | Query | Returned Count | Critical Leaks | Leak Rate | Threshold Check |
|---|---|---|---:|---:|---:|---|
| 1 | 2026-03-19T22:47:40.590434Z | endogenous first | 5 | 0 | 0.0% | PASS |
| 2 | 2026-03-19T22:47:40.667530Z | programmatic first | 5 | 0 | 0.0% | PASS |
| 3 | 2026-03-19T22:47:40.739876Z | local compute first | 5 | 0 | 0.0% | PASS |

## Aggregate Summary

- Total windows: 3
- Total evaluated results: 15
- Total critical leaks: 0
- Aggregate leak rate: 0.0%
- Consecutive compliance windows achieved: 3/3

## Conclusion

- G3 repeatability criterion is satisfied for this cycle: three consecutive boundary-safe windows completed with zero critical leaks.
- This closes the previously open G3 blocker in the Gate 4 re-entry packet, subject to Review confirmation.

## Reproduction Command

Use the following command to reproduce the three-window check:

```bash
uv run python -c "import json,subprocess,datetime; qs=['endogenous first','programmatic first','local compute first']; rows=[]
for i,q in enumerate(qs,1):
 r=subprocess.run(['uv','run','python','scripts/rag_index.py','query','--query',q,'--top-k','5','--filter-governs','endogenous-first','--output','json'],capture_output=True,text=True,check=True)
 j=json.loads(r.stdout)
 bad=[]
 for x in j.get('results',[]):
  g=x.get('governs',[])
  if 'endogenous-first' not in g: bad.append(x.get('source_file'))
 rows.append({'window':i,'query':q,'count':j.get('count',0),'critical_leaks':len(bad),'bad_sources':bad[:3],'ts':datetime.datetime.utcnow().isoformat()+'Z'})
print(json.dumps({'windows':rows},indent=2))"
```
