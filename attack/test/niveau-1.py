

import subprocess
import time

enfant = subprocess.Popen(["sleep", "60"])
with open("/tmp/alpha-test-enfant.pid", "w", encoding="utf-8") as f:
    f.write(str(enfant.pid))
print("[SIMULE] outil enfant lancé (pid %d)" % enfant.pid, flush=True)
time.sleep(60)
