#!/usr/bin/env bash
# coderabbit-ai-generated:v1
# Recreate source-derived data transformations; no Lua is executed.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
bash scratch/dv/reproduce-backtrace.sh
python3 scratch/dv/extract_nested.py --buffer scratch/dv/z240-backtrace.bin --table scratch/dv/z240-backtrace.json --indices 436 --seed 186 > scratch/dv/nested-436.json
python3 - <<'PY'
import json
from pathlib import Path
p=Path('scratch/dv')
record=json.loads((p/'nested-436.json').read_text())['records'][0]
(p/'nested-436-tables.json').write_text(json.dumps(record['tables'],indent=2)+'\n')
PY
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-436-tables.json --pc 318 --seed 0 --mode E201 > scratch/dv/nested-436-e201.json
python3 scratch/dv/extract_records.py --buffer scratch/dv/z240-backtrace.bin --table scratch/dv/z240-backtrace.json --arrays scratch/dv/nested-436-e201.json --output scratch/dv/nested-436-record204.bin --offset 0 --length 171131 --f-seed 0 --b-seed 0 --mode E201 --pcs 159 > scratch/dv/nested-436-record204.json
python3 scratch/dv/extract_nested.py --buffer scratch/dv/nested-436-record204.bin --table scratch/dv/nested-436-record204.json --indices 204 --seed 186 > scratch/dv/nested-204-native.json
python3 scratch/dv/decode_constants.py --buffer scratch/dv/nested-436-record204.bin --table scratch/dv/nested-436-record204.json --indices 705 > scratch/dv/nested-436-captures705.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-436-e201.json --pc 181 --seed 0 --mode Z250 > scratch/dv/nested-436-z250-1.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-436-z250-1.json --pc 192 --seed 0 --mode Z250 > scratch/dv/nested-436-z250-2.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-436-z250-2.json --pc 235 --seed 0 --mode Z250 > scratch/dv/nested-436-z250-3.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-436-z250-3.json --pc 175 --seed 0 --mode Z250 > scratch/dv/nested-436-z250-4.json
python3 scratch/dv/extract_nested.py --buffer scratch/dv/z240-backtrace.bin --table scratch/dv/z240-backtrace.json --indices 589,550,575 --seed 186 > scratch/dv/z240-more-nested.json
python3 scratch/dv/extract_nested.py --buffer scratch/dv/z240-backtrace.bin --table scratch/dv/z240-backtrace.json --indices 539,489 --seed 186 > scratch/dv/nested-539-489.json
python3 - <<'PY'
import json
from pathlib import Path
p=Path('scratch/dv')
for record in json.loads((p/'nested-539-489.json').read_text())['records']:
    (p/f"nested-{record['index']}-tables.json").write_text(json.dumps(record['tables'],indent=2)+'\n')
PY
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-539-tables.json --pc 22 --seed 0 --mode E201 > scratch/dv/nested-539-e201-1.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-539-e201-1.json --pc 5 --seed 0 --mode E201 > scratch/dv/nested-539-e201-2.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-539-e201-2.json --pc 44 --seed 0 --mode Z95 > scratch/dv/nested-539-z95-1.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-539-z95-1.json --pc 27 --seed 0 --mode Z95 > scratch/dv/nested-539-z95-2.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-489-tables.json --pc 1 --seed 0 --mode E201 > scratch/dv/nested-489-e201.json
python3 scratch/dv/extract_records.py --buffer scratch/dv/nested-436-record204.bin --table scratch/dv/nested-436-record204.json --arrays scratch/dv/nested-489-e201.json --output scratch/dv/nested-489-record188.bin --offset 0 --length 171131 --f-seed 0 --b-seed 0 --mode E201 --pcs 2 > scratch/dv/nested-489-record188.json
python3 scratch/dv/extract_nested.py --buffer scratch/dv/nested-489-record188.bin --table scratch/dv/nested-489-record188.json --indices 188 --seed 186 > scratch/dv/nested-188.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-489-e201.json --pc 33 --seed 0 --mode Z250 > scratch/dv/nested-489-z250-1.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-489-z250-1.json --pc 34 --seed 0 --mode Z250 > scratch/dv/nested-489-z250-2.json
python3 scratch/dv/walk_nested188.py --nested scratch/dv/nested-188.json --parent scratch/dv/nested-489-z250-2.json --buffer scratch/dv/nested-489-record188.bin --table scratch/dv/nested-489-record188.json --output-buffer scratch/dv/nested-188-walk.bin --max-steps 75000 --compact > scratch/dv/nested-188-walk.json
python3 scratch/dv/resume_root.py > scratch/dv/z240-return-branches.json
python3 scratch/dv/catalog_constants.py --buffer scratch/dv/z240-backtrace.bin --table scratch/dv/z240-backtrace.json > scratch/dv/z240-constant-candidates.json
python3 scratch/dv/catalog_nested.py --buffer scratch/dv/z240-backtrace.bin --table scratch/dv/z240-backtrace.json > scratch/dv/z240-prototype-candidates.json
python3 scratch/dv/extract_nested.py --buffer scratch/dv/z240-backtrace.bin --table scratch/dv/z240-backtrace.json --indices 670 --seed 186 > scratch/dv/nested-670.json
python3 - <<'PY'
import json
from pathlib import Path
p=Path('scratch/dv')
r=json.loads((p/'nested-670.json').read_text())['records'][0]
(p/'nested-670-tables.json').write_text(json.dumps(r['tables'],indent=2)+'\n')
PY
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-670-tables.json --pc 17 --seed 4199977214 --mode E201 > scratch/dv/nested-670-e201-1.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-670-e201-1.json --pc 18 --seed 4199977214 --mode E201 > scratch/dv/nested-670-e201-2.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-670-e201-2.json --pc 19 --seed 1193198983 --mode E201 > scratch/dv/nested-670-e201-3.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-670-e201-3.json --pc 6 --seed 1193198983 --mode E201 > scratch/dv/nested-670-e201-4.json
python3 scratch/dv/decode_constants.py --buffer scratch/dv/z240-backtrace.bin --table scratch/dv/z240-backtrace.json --indices 659,604,402,434,83,560,499,684,149,429,283 > scratch/dv/nested-factory-constants.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-670-e201-4.json --pc 222 --seed 1193198983 --mode Z250 > scratch/dv/nested-670-z250-1.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-670-z250-1.json --pc 223 --seed 4199977214 --mode Z250 > scratch/dv/nested-670-z250-2.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-670-z250-2.json --pc 60 --seed 1193198983 --mode Z250 > scratch/dv/nested-670-z250-3.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-670-z250-3.json --pc 73 --seed 1193198983 --mode Z95 > scratch/dv/nested-670-z95-1.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-670-z95-1.json --pc 85 --seed 4199977214 --mode Z95 > scratch/dv/nested-670-z95-2.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-670-z95-2.json --pc 94 --seed 285076466 --mode Z95 > scratch/dv/nested-670-z95-3.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-670-z95-3.json --pc 109 --seed 1193198983 --mode Z95 > scratch/dv/nested-670-z95-4.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-670-z95-4.json --pc 199 --seed 1193198983 --mode Z240 > scratch/dv/nested-670-z240-1.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-670-z240-1.json --pc 200 --seed 285076466 --mode Z240 > scratch/dv/nested-670-z240-2.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-670-z240-2.json --pc 154 --seed 1193198983 --mode Z240 > scratch/dv/nested-670-z240-3.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-670-z240-3.json --pc 155 --seed 1193198983 --mode Z240 > scratch/dv/nested-670-z240-4.json
python3 scratch/dv/trace_nested670.py > scratch/dv/nested-670-points.json
python3 scratch/dv/trace_round_indices.py > scratch/dv/z240-round-index-prefix.json
python3 scratch/dv/extract_records.py --buffer scratch/dv/z240-backtrace.bin --table scratch/dv/z240-backtrace.json --arrays scratch/dv/z240-backtrace.json --output scratch/dv/record208-conditional.bin --offset 0 --length 171131 --f-seed 0 --b-seed 0 --mode Z240 --pcs 10616 > scratch/dv/record208-conditional.json
python3 scratch/dv/extract_nested.py --buffer scratch/dv/record208-conditional.bin --table scratch/dv/record208-conditional.json --indices 208 --seed 186 > scratch/dv/nested-208.json
python3 - <<'PY'
import json
from pathlib import Path
p=Path('scratch/dv')
r=json.loads((p/'nested-208.json').read_text())['records'][0]
(p/'nested-208-tables.json').write_text(json.dumps(r['tables'],indent=2)+'\n')
PY
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-208-tables.json --pc 127 --seed 0 --mode Z95 > scratch/dv/nested-208-z95-1.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-208-z95-1.json --pc 128 --seed 0 --mode Z95 > scratch/dv/nested-208-z95-2.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-208-z95-2.json --pc 1169 --seed 0 --mode Z95 > scratch/dv/nested-208-z95-3.json
python3 scratch/dv/decode_constants.py --buffer scratch/dv/record208-conditional.bin --table scratch/dv/record208-conditional.json --indices 408,27,97 > scratch/dv/nested-208-constants.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-208-z95-3.json --pc 1163 --seed 0 --mode Z95 > scratch/dv/nested-208-z95-4.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-208-z95-4.json --pc 1070 --seed 0 --mode Z95 > scratch/dv/nested-208-z95-5.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-208-z95-5.json --pc 878 --seed 0 --mode Z95 > scratch/dv/nested-208-z95-6.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-208-z95-6.json --pc 991 --seed 0 --mode Z95 > scratch/dv/nested-208-z95-7.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-208-z95-7.json --pc 992 --seed 0 --mode Z95 > scratch/dv/nested-208-z95-8.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-208-z95-8.json --pc 947 --seed 0 --mode Z95 > scratch/dv/nested-208-z95-9.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-208-z95-9.json --pc 984 --seed 138650246 --mode Z95 > scratch/dv/nested-208-z95-10.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-208-z95-10.json --pc 964 --seed 138650246 --mode Z95 > scratch/dv/nested-208-z95-11.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-208-z95-11.json --pc 25 --seed 0 --mode Z95 > scratch/dv/nested-208-z95-12.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-208-z95-12.json --pc 26 --seed 0 --mode Z95 > scratch/dv/nested-208-z95-13.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-208-z95-13.json --pc 397 --seed 0 --mode Z95 > scratch/dv/nested-208-z95-14.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-208-z95-14.json --pc 585 --seed 0 --mode Z95 > scratch/dv/nested-208-z95-15.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-208-z95-15.json --pc 586 --seed 0 --mode Z95 > scratch/dv/nested-208-z95-16.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-208-z95-16.json --pc 109 --seed 0 --mode Z95 > scratch/dv/nested-208-z95-17.json
python3 scratch/dv/patch_block.py --arrays scratch/dv/nested-208-z95-17.json --pc 110 --seed 0 --mode Z95 > scratch/dv/nested-208-z95-18.json
