<!-- docs/improvement_suggestions.md -->
# Dreamcatcher Improvement Suggestions

The table below pairs each observed issue with a concrete path forward so you can weigh effort versus impact at a glance.

| Current Behaviour & Concern | Improvement Proposal |
| --- | --- |
| `AgentMeta` relies on hard-coded `/home/mark/...` paths for agent code, backups, and logs, which breaks portability and complicates deployments outside the author’s workstation. 【F:backend/agents/agent_meta.py†L62-L69】 | Introduce a config-driven path resolver (for example, a `config.py` module backed by environment variables) and build paths with `pathlib.Path`. A sketch of the improved initialisation would be: <br><br>```python
# config.py
from pathlib import Path
from pydantic import BaseSettings

class AppSettings(BaseSettings):
    base_dir: Path = Path(__file__).resolve().parents[1]
    agent_dir: Path = base_dir / "backend" / "agents"
    backup_dir: Path = base_dir / "backups" / "agents"
    evolution_log: Path = base_dir / "logs" / "evolution.log"

settings = AppSettings()
```
```python
# backend/agents/agent_meta.py
from config import settings
...
self.agent_dir = settings.agent_dir
self.backup_dir = settings.backup_dir
self.evolution_log = settings.evolution_log
self.backup_dir.mkdir(parents=True, exist_ok=True)
self.evolution_log.parent.mkdir(parents=True, exist_ok=True)
```
This keeps file operations environment-agnostic and makes overrides trivial via env vars. |
| Async methods such as `_analyze_system_state` open synchronous SQLAlchemy sessions and iterate over ORM objects in the event loop, which risks blocking cooperative multitasking under load. 【F:backend/agents/agent_meta.py†L124-L203】 | Offload blocking DB and file-system work to a thread pool with `asyncio.to_thread`, or migrate the repository layer to SQLAlchemy’s async engine. For a minimal change: <br><br>```python
async def _load_agent_logs(self) -> list[AgentLog]:
    return await asyncio.to_thread(
        AgentLogCRUD.get_logs_since,
        self._db_factory(),
        datetime.now() - timedelta(days=7),
    )
```
Wrap the session factory so each call opens/closes inside the worker thread, and mirror this pattern for error log retrieval, backups, and file writes. This keeps latency predictable for other coroutines. |
| `start_evolution_cycle` continues into improvement and validation even when `_analyze_system` reports that no evolution is needed, wasting compute and potentially rewriting code unnecessarily. 【F:backend/services/evolution_service.py†L55-L112】 | Short-circuit the cycle when `evolution_needed` is false unless `force=True`. Example: <br><br>```python
analysis_result = await self._analyze_system()
if not analysis_result["success"]:
    ...
if not force and not analysis_result.get("evolution_needed", False):
    self.current_state = "idle"
    return {
        "success": True,
        "evolution_complete": False,
        "message": "Evolution skipped; health metrics above thresholds.",
        "analysis": analysis_result["data"],
    }
```
This preserves the agent-driven recommendations while preventing unnecessary self-modification cycles. |

Each recommendation is intentionally modular so you can adopt them incrementally without destabilising the running system.
