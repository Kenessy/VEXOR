import time, re
from pathlib import Path
log = Path(r'G:/AI/mirror/VRAXION/logs/current/tournament_phase6.log')
for _ in range(40):
    if log.exists():
        lines = log.read_text().splitlines()[-20:]
        for line in reversed(lines):
            if ' ctrl(' in line:
                m = re.search(r'step\s+(\d+)', line)
                if m and int(m.group(1)) >= 10:
                    print(line)
                    raise SystemExit(0)
    time.sleep(1)
raise SystemExit(1)
