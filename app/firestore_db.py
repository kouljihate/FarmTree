import json
import os
import logging
import urllib.request
import urllib.parse
import uuid
from datetime import datetime

logger = logging.getLogger("farmtree")

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "firebase_config.json")
_project_id = None
_api_key = None


def _load_config():
    global _project_id, _api_key
    if _project_id is not None:
        return True
    try:
        with open(_CONFIG_PATH, "r") as f:
            cfg = json.load(f)
        _project_id = cfg["project_id"]
        _api_key = cfg["api_key"]
        return True
    except Exception as ex:
        logger.warning("Firebase config not loaded: %s", ex)
        return False


def _firestore_url(collection: str, doc_id: str = None) -> str:
    base = f"https://firestore.googleapis.com/v1/projects/{_project_id}/databases/(default)/documents"
    if doc_id:
        return f"{base}/{collection}/{doc_id}?key={_api_key}"
    return f"{base}/{collection}?key={_api_key}"


def _firestore_request(method: str, url: str, data: dict = None) -> dict | None:
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as ex:
        error_body = ex.read().decode("utf-8", errors="replace")
        logger.error("Firestore %s failed (%s): %s", method, ex.code, error_body)
        return None
    except Exception as ex:
        logger.error("Firestore request failed: %s", ex)
        return None


def _to_firestore_doc(data: dict) -> dict:
    fields = {}
    for k, v in data.items():
        if v is None:
            continue
        if isinstance(v, str):
            fields[k] = {"stringValue": v}
        elif isinstance(v, (int, float)):
            fields[k] = {"doubleValue": v}
        elif isinstance(v, bool):
            fields[k] = {"booleanValue": v}
        elif isinstance(v, list):
            fields[k] = {"arrayValue": {"values": [_to_firestore_value(item) for item in v]}}
        elif isinstance(v, dict):
            fields[k] = {"mapValue": {"fields": _to_firestore_doc(v)}}
    return {"fields": fields}


def _to_firestore_value(v):
    if v is None:
        return {"nullValue": None}
    if isinstance(v, str):
        return {"stringValue": v}
    if isinstance(v, (int, float)):
        return {"doubleValue": v}
    if isinstance(v, bool):
        return {"booleanValue": v}
    if isinstance(v, list):
        return {"arrayValue": {"values": [_to_firestore_value(item) for item in v]}}
    if isinstance(v, dict):
        return {"mapValue": {"fields": _to_firestore_doc(v)}}
    return {"stringValue": str(v)}


def _from_firestore_doc(doc: dict) -> dict:
    result = {}
    fields = doc.get("fields", {})
    for k, v in fields.items():
        if "stringValue" in v:
            result[k] = v["stringValue"]
        elif "doubleValue" in v:
            result[k] = v["doubleValue"]
        elif "integerValue" in v:
            result[k] = int(v["integerValue"])
        elif "booleanValue" in v:
            result[k] = v["booleanValue"]
        elif "arrayValue" in v:
            result[k] = [_from_firestore_value(item) for item in v["arrayValue"].get("values", [])]
        elif "mapValue" in v:
            result[k] = _from_firestore_doc(v["mapValue"])
        elif "nullValue" in v:
            result[k] = None
    name = doc.get("name", "")
    if "/" in name:
        result["id"] = name.split("/")[-1]
    return result


def _from_firestore_value(v):
    if "stringValue" in v:
        return v["stringValue"]
    if "doubleValue" in v:
        return v["doubleValue"]
    if "integerValue" in v:
        return int(v["integerValue"])
    if "booleanValue" in v:
        return v["booleanValue"]
    if "arrayValue" in v:
        return [_from_firestore_value(item) for item in v["arrayValue"].get("values", [])]
    if "mapValue" in v:
        return _from_firestore_doc(v["mapValue"])
    return None


def is_available() -> bool:
    return _load_config()


def check_tree_code_unique(tree_code: str, exclude_id: str = None) -> bool:
    if not _load_config():
        return True
    encoded = urllib.parse.quote(tree_code)
    url = _firestore_url("trees") + f"&where.fields.tree_code.stringValue={encoded}"
    result = _firestore_request("GET", url)
    if result is None:
        return True
    docs = result.get("documents", [])
    if exclude_id:
        docs = [d for d in docs if d.get("name", "").split("/")[-1] != exclude_id]
    return len(docs) == 0


def insert_tree_firestore(
    tree_code: str,
    kind: str,
    variety: str,
    latitude: str,
    longitude: str,
    status: str,
    notes: str,
    photos: list[str] | None = None,
) -> str | None:
    if not _load_config():
        return None
    if not check_tree_code_unique(tree_code):
        raise ValueError(f"Tree code '{tree_code}' already exists")
    doc_id = uuid.uuid4().hex[:20]
    visit = {
        "visit_dt": datetime.now().strftime("%Y/%m/%d %H:%M"),
        "status": status,
        "notes": notes,
        "photos": photos or [],
    }
    data = {
        "tree_code": tree_code,
        "kind": kind,
        "variety": variety,
        "latitude": latitude,
        "longitude": longitude,
        "visits": [visit],
    }
    url = _firestore_url("trees", doc_id)
    result = _firestore_request("PUT", url, _to_firestore_doc(data))
    if result:
        logger.info("Inserted tree %s to Firestore", doc_id)
        return doc_id
    return None


def get_tree_firestore(doc_id: str) -> dict | None:
    if not _load_config():
        return None
    url = _firestore_url("trees", doc_id)
    result = _firestore_request("GET", url)
    if result:
        return _from_firestore_doc(result)
    return None


def get_all_trees_firestore() -> list[dict]:
    if not _load_config():
        return []
    url = _firestore_url("trees")
    result = _firestore_request("GET", url)
    if not result:
        return []
    docs = result.get("documents", [])
    trees = [_from_firestore_doc(d) for d in docs]
    trees.sort(key=lambda x: x.get("last_visit_dt", ""), reverse=True)
    return trees


def update_tree_firestore(
    doc_id: str,
    tree_code: str | None = None,
    kind: str | None = None,
    variety: str | None = None,
    latitude: str | None = None,
    longitude: str | None = None,
) -> bool:
    if not _load_config():
        return False
    if tree_code and not check_tree_code_unique(tree_code, exclude_id=doc_id):
        raise ValueError(f"Tree code '{tree_code}' already exists")
    existing = get_tree_firestore(doc_id)
    if not existing:
        return False
    updates = {}
    if tree_code is not None:
        updates["tree_code"] = tree_code
    if kind is not None:
        updates["kind"] = kind
    if variety is not None:
        updates["variety"] = variety
    if latitude is not None:
        updates["latitude"] = latitude
    if longitude is not None:
        updates["longitude"] = longitude
    if updates:
        merged = {k: v for k, v in existing.items() if k not in ("id",) and not isinstance(v, (list, dict))}
        merged.update(updates)
        url = _firestore_url("trees", doc_id)
        result = _firestore_request("PATCH", url, _to_firestore_doc(merged))
        return result is not None
    return True


def add_visit_firestore(doc_id: str, status: str, notes: str, photos: list[str] | None = None) -> bool:
    if not _load_config():
        return False
    existing = get_tree_firestore(doc_id)
    if not existing:
        return False
    visits = existing.get("visits", [])
    visits.append({
        "visit_dt": datetime.now().strftime("%Y/%m/%d %H:%M"),
        "status": status,
        "notes": notes,
        "photos": photos or [],
    })
    url = _firestore_url("trees", doc_id)
    data = {k: v for k, v in existing.items() if k != "id"}
    data["visits"] = visits
    result = _firestore_request("PATCH", url, _to_firestore_doc(data))
    return result is not None


def update_tree_status_firestore(doc_id: str, status: str) -> bool:
    return add_visit_firestore(doc_id, status, "", [])


def delete_tree_firestore(doc_id: str) -> bool:
    if not _load_config():
        return False
    url = _firestore_url("trees", doc_id)
    req = urllib.request.Request(url, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return True
    except Exception as ex:
        logger.error("Firestore delete failed: %s", ex)
        return False


def search_trees_firestore(
    query: str = "",
    kind: str | None = None,
    status: str | None = None,
) -> list[dict]:
    all_trees = get_all_trees_firestore()
    terms = []
    for term in query.strip().split("|"):
        t = term.strip()
        if t:
            terms.append(t.lower())
    result = []
    for tree in all_trees:
        if kind and tree.get("kind") != kind:
            continue
        visits = tree.get("visits", [])
        last_status = visits[-1].get("status", "") if visits else ""
        if status and last_status != status:
            continue
        if terms:
            all_found = True
            for term in terms:
                found = (
                    term in (tree.get("kind") or "").lower()
                    or term in (tree.get("variety") or "").lower()
                    or term in (tree.get("tree_code") or "").lower()
                    or any(
                        term in (v.get("notes", "") or "").lower() or term in (v.get("status", "") or "").lower()
                        for v in visits
                    )
                )
                if not found:
                    all_found = False
                    break
            if not all_found:
                continue
        result.append(_enrich_tree_firestore(tree))
    result.sort(key=lambda x: x.get("last_visit_dt", ""), reverse=True)
    return result


def _enrich_tree_firestore(tree: dict) -> dict:
    d = dict(tree)
    visits = d.get("visits", [])
    if visits:
        last = visits[-1]
        d.update(
            last_status=last.get("status", ""),
            last_photo=(last.get("photos") or [""])[0] if last.get("photos") else "",
            last_notes=last.get("notes", ""),
            last_visit_dt=last.get("visit_dt", ""),
        )
    else:
        d.update(last_status="", last_photo="", last_notes="", last_visit_dt="")
    return d
