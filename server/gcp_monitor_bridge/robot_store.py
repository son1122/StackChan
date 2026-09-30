import json
import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("robot_store")

DEFAULT_CONFIG = {
    "name": "StackChan",
    "assigned_project": "ALL FLEET",
    "sound_alerts": True,
    "show_billing": True,
    "poll_interval_sec": 15,
    "display_mode": "standard",  # "standard", "ticker", "avatar_only"
}

class RobotStore:
    def __init__(self, data_path: Optional[str] = None):
        self._lock = threading.Lock()
        
        # Primary path inside container or local workspace
        if data_path:
            self._storage_path = data_path
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            candidate = os.path.join(base_dir, "data", "robot_configs.json")
            if os.path.exists(os.path.dirname(candidate)) or self._try_create_dir(os.path.dirname(candidate)):
                self._storage_path = candidate
            else:
                self._storage_path = "/tmp/stackchan_robot_configs.json"

        # Ephemeral runtime state (IP, battery, last seen)
        self._heartbeats: Dict[str, Dict[str, Any]] = {}
        # Persistent configuration (Name, Assigned Project, Feature Flags)
        self._configs: Dict[str, Dict[str, Any]] = {}
        
        self._load()

    def _try_create_dir(self, path: str) -> bool:
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception:
            return False

    def _normalize_mac(self, mac: str) -> str:
        if not mac:
            return ""
        return mac.strip().upper()

    def _load(self):
        with self._lock:
            if os.path.exists(self._storage_path):
                try:
                    with open(self._storage_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            self._configs = {
                                self._normalize_mac(k): v for k, v in data.items()
                            }
                            logger.info(f"Loaded {len(self._configs)} robot configs from {self._storage_path}")
                except Exception as e:
                    logger.warning(f"Could not load robot configs from {self._storage_path}: {e}")
                    self._configs = {}

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(self._configs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist robot configs to {self._storage_path}: {e}")
            if self._storage_path != "/tmp/stackchan_robot_configs.json":
                try:
                    self._storage_path = "/tmp/stackchan_robot_configs.json"
                    with open(self._storage_path, "w", encoding="utf-8") as f:
                        json.dump(self._configs, f, indent=2)
                    logger.info("Saved robot configs to fallback /tmp/stackchan_robot_configs.json")
                except Exception as inner_e:
                    logger.error(f"Failed to persist to fallback /tmp path: {inner_e}")

    def record_heartbeat(
        self,
        mac: str,
        ip: str,
        requested_project: Optional[str] = None,
        battery: Optional[Any] = None,
        charging: Optional[Any] = None,
        version: Optional[str] = None,
    ) -> Dict[str, Any]:
        norm_mac = self._normalize_mac(mac)
        if not norm_mac:
            return {}

        now = time.time()
        batt_val = None
        if battery is not None and str(battery).isdigit():
            batt_val = max(0, min(100, int(battery)))
        is_charging = charging in ("1", "true", "True", True)

        with self._lock:
            # Update live heartbeat
            self._heartbeats[norm_mac] = {
                "ip": ip,
                "battery": batt_val,
                "charging": is_charging,
                "version": version or "1.0.0",
                "last_seen": now,
            }

            # If robot is new, initialize default persistent configuration
            if norm_mac not in self._configs:
                short_id = norm_mac.replace(":", "")[-4:]
                default_proj = requested_project or "ALL FLEET"
                self._configs[norm_mac] = {
                    "mac": norm_mac,
                    "name": f"StackChan-{short_id}",
                    "assigned_project": default_proj,
                    "sound_alerts": True,
                    "show_billing": True,
                    "poll_interval_sec": 15,
                    "display_mode": "standard",
                    "created_at": int(now),
                    "updated_at": int(now),
                }
                self._save()

            return dict(self._configs[norm_mac])

    def get_effective_project(self, mac: str, explicit_project: Optional[str] = None) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Determines the project telemetry to return for a robot.
        If explicit_project is given in query params, it takes precedence.
        Otherwise, uses the robot's configured assigned_project.
        """
        norm_mac = self._normalize_mac(mac)
        with self._lock:
            config = dict(self._configs.get(norm_mac, DEFAULT_CONFIG))
        
        assigned = config.get("assigned_project", "ALL FLEET")
        effective_project = explicit_project if explicit_project else assigned
        
        # 'ALL FLEET' maps to None for the aggregate collector
        if effective_project in ("ALL FLEET", "ALL", "FLEET", "", None):
            return None, config
        return effective_project, config

    def get_config(self, mac: str) -> Optional[Dict[str, Any]]:
        norm_mac = self._normalize_mac(mac)
        with self._lock:
            if norm_mac in self._configs:
                return dict(self._configs[norm_mac])
            return None

    def update_config(self, mac: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        norm_mac = self._normalize_mac(mac)
        now = int(time.time())
        with self._lock:
            if norm_mac not in self._configs:
                short_id = norm_mac.replace(":", "")[-4:] if len(norm_mac) >= 4 else "0000"
                self._configs[norm_mac] = {
                    "mac": norm_mac,
                    "name": f"StackChan-{short_id}",
                    "assigned_project": "ALL FLEET",
                    "sound_alerts": True,
                    "show_billing": True,
                    "poll_interval_sec": 15,
                    "display_mode": "standard",
                    "created_at": now,
                }
            
            cfg = self._configs[norm_mac]
            if "name" in updates and isinstance(updates["name"], str):
                name = updates["name"].strip()
                if name:
                    cfg["name"] = name[:50]
            
            if "assigned_project" in updates and isinstance(updates["assigned_project"], str):
                proj = updates["assigned_project"].strip()
                if proj:
                    cfg["assigned_project"] = proj
            
            if "sound_alerts" in updates:
                cfg["sound_alerts"] = bool(updates["sound_alerts"])
                
            if "show_billing" in updates:
                cfg["show_billing"] = bool(updates["show_billing"])
                
            if "poll_interval_sec" in updates:
                try:
                    interval = int(updates["poll_interval_sec"])
                    cfg["poll_interval_sec"] = max(5, min(300, interval))
                except (ValueError, TypeError):
                    pass
                    
            if "display_mode" in updates and updates["display_mode"] in ("standard", "ticker", "avatar_only"):
                cfg["display_mode"] = updates["display_mode"]

            cfg["updated_at"] = now
            self._save()
            return dict(cfg)

    def delete_robot(self, mac: str) -> bool:
        norm_mac = self._normalize_mac(mac)
        with self._lock:
            removed = False
            if norm_mac in self._configs:
                del self._configs[norm_mac]
                removed = True
            if norm_mac in self._heartbeats:
                del self._heartbeats[norm_mac]
                removed = True
            if removed:
                self._save()
            return removed

    def get_all_robots(self) -> List[Dict[str, Any]]:
        now = time.time()
        result = []
        with self._lock:
            # Combine all known MACs from configs and heartbeats
            all_macs = set(self._configs.keys()) | set(self._heartbeats.keys())
            
            for mac in all_macs:
                cfg = self._configs.get(mac, {
                    "mac": mac,
                    "name": f"StackChan-{mac.replace(':', '')[-4:]}",
                    "assigned_project": "ALL FLEET",
                    "sound_alerts": True,
                    "show_billing": True,
                    "poll_interval_sec": 15,
                    "display_mode": "standard",
                })
                hb = self._heartbeats.get(mac, {
                    "ip": "offline",
                    "battery": None,
                    "charging": False,
                    "version": "unknown",
                    "last_seen": 0,
                })
                
                sec_ago = int(now - hb["last_seen"]) if hb["last_seen"] > 0 else 999999
                is_online = (sec_ago < 60) and (hb["last_seen"] > 0)
                
                # NEVER expose any keys, credentials, or internal secrets
                result.append({
                    "mac": mac,
                    "name": cfg.get("name", f"StackChan-{mac[-4:]}"),
                    "assigned_project": cfg.get("assigned_project", "ALL FLEET"),
                    "sound_alerts": cfg.get("sound_alerts", True),
                    "show_billing": cfg.get("show_billing", True),
                    "poll_interval_sec": cfg.get("poll_interval_sec", 15),
                    "display_mode": cfg.get("display_mode", "standard"),
                    "ip": hb.get("ip", "offline"),
                    "battery": hb.get("battery"),
                    "charging": hb.get("charging", False),
                    "version": hb.get("version", "1.0.0"),
                    "online": is_online,
                    "last_seen_sec_ago": sec_ago,
                    "last_seen_ts": hb.get("last_seen", 0),
                })

        return sorted(result, key=lambda x: (not x["online"], x["last_seen_sec_ago"]))

# Global singleton
robot_store = RobotStore()
