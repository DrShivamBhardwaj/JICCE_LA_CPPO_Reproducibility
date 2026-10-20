#!/usr/bin/env python3
"""Read-only publisher registration audit of exactly 25 frozen manuscript references.

Crossref is primary. DataCite is fallback for DOIs (especially arXiv). No guessed
DOI or altered paper identity is accepted. Unregistered technical documentation
is checked against its official citation URL and reviewed separately.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REFS = ROOT / "references" / "array_25_expected.json"
UA = "Manuscript-Reference-Verifier/1.0 (academic bibliography verification)"
TIMEOUT = 18


def fetch_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return json.load(response)


def compact(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", str(value or ""))).strip()


def normalize(s):
    s = compact(s).casefold().replace("–", "-").replace("—", "-")
    return " ".join(re.findall(r"\w+", s, re.UNICODE))


def ratio(a, b):
    return round(difflib.SequenceMatcher(None, normalize(a), normalize(b)).ratio(), 4)


def year_crossref(m):
    for k in ("published", "published-print", "published-online", "issued", "created"):
        d = m.get(k, {}).get("date-parts", [[]])
        if d and d[0]:
            return d[0][0]
    return None


def obtain_doi_metadata(doi):
    q = urllib.parse.quote(doi, safe="")
    errors = []
    try:
        m = fetch_json("https://api.crossref.org/works/" + q)["message"]
        return {
            "registry": "Crossref", "registered_doi": m.get("DOI"),
            "registered_title": compact(m.get("title", [""])[0]),
            "registered_year": year_crossref(m),
            "authors": [
                compact(" ".join((a.get("given", ""), a.get("family", ""))))
                for a in m.get("author", [])],
            "venue": compact(m.get("container-title", [""])[0]) if m.get("container-title") else None,
            "volume": m.get("volume"), "issue": m.get("issue"),
            "page": m.get("page"), "article_number": m.get("article-number"),
            "publisher": m.get("publisher"), "metadata_url": m.get("URL"),
            "registration_errors": []
        }
    except Exception as exc:
        errors.append("Crossref: " + str(exc)[:200])
    try:
        m = fetch_json("https://api.datacite.org/dois/" + q)["data"]["attributes"]
        t = m.get("titles", [{}])[0].get("title")
        people = m.get("creators", [])
        return {
            "registry": "DataCite", "registered_doi": m.get("doi"),
            "registered_title": compact(t), "registered_year": m.get("publicationYear"),
            "authors": [compact(p.get("name")) for p in people],
            "venue": compact(m.get("publisher")), "volume": None, "issue": None,
            "page": None, "article_number": None, "publisher": m.get("publisher"),
            "metadata_url": m.get("url"), "registration_errors": errors
        }
    except Exception as exc:
        errors.append("DataCite: " + str(exc)[:200])
    return {"registry": None, "registration_errors": errors}


def check_official_url(url):
    request = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return {"http_status": response.status, "final_url": response.url}
    except urllib.error.HTTPError as exc:
        # Some documentation hosts forbid HEAD despite being human-browseable.
        if exc.code in (403, 405, 429):
            return {"http_status": exc.code,
                    "notes": "HTTP access restricted to automation; manual source check still required"}
        return {"http_status": exc.code, "notes": "Official link could not be validated"}
    except Exception as exc:
        return {"http_status": None, "notes": str(exc)[:190]}


def verify(ref):
    result = dict(ref)
    checks = []
    doi = ref.get("doi")
    if doi:
        metadata = obtain_doi_metadata(doi)
        result["registry_metadata"] = metadata
        if not metadata["registry"]:
            result["status"] = "DOI_METADATA_UNAVAILABLE"
            result["issues"] = metadata.get("registration_errors", [])
            return result
        score = ratio(ref["title"], metadata["registered_title"])
        result["title_similarity"] = score
        if (metadata.get("registered_doi") or "").casefold() != doi.casefold():
            checks.append("DOI registration mismatch")
        if score < 0.80:
            checks.append("DOI title differs from cited title; verify identity")
        if ref.get("year") and metadata.get("registered_year") and abs(int(metadata["registered_year"])-int(ref["year"])) > 1:
            checks.append("Publication year differs")
        first = normalize(ref["first_author"])
        actual = [normalize(a) for a in metadata.get("authors", [])]
        if actual and not any(first in name for name in actual):
            checks.append("First author not present in registry author list")
        if not actual:
            checks.append("No authors in registry metadata")
        result["issues"] = checks
        result["status"] = "REGISTRY_MATCH" if not checks else "REVIEW_METADATA"
    else:
        result["url_check"] = check_official_url(ref["source_url"])
        status = result["url_check"].get("http_status")
        result["status"] = "OFFICIAL_URL_ACCESSIBLE" if status in (200, 301, 302, 303, 307, 308) else "URL_MANUAL_REVIEW"
        result["issues"] = ([] if result["status"] == "OFFICIAL_URL_ACCESSIBLE"
                            else ["Automated URL check inconclusive; verify official landing page"])
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    rows = json.loads(REFS.read_text())
    assert len(rows)==25 and [x["number"] for x in rows]==list(range(1,26))
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    for x in rows:
        data = verify(x)
        results.append(data)
        print(f'REF {x["number"]:02} {data["status"]} {x["doi"] or x["source_url"]}', flush=True)
        time.sleep(0.35)
    audit = {
        "classification": "publisher_registration_and_official_URL_audit",
        "reference_count": len(results),
        "registered_doi_count": sum(bool(x["doi"]) for x in results),
        "caution": "Automated title/author/DOI validation is not a substitute for manual source-level review of page ranges, editorial corrections and version-specific software citations.",
        "frozen_reference_sha256": hashlib.sha256(REFS.read_bytes()).hexdigest(),
        "records": results,
    }
    (args.output / "reference_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False)+"\n")
    cols = ["number","status","first_author","year","doi","title","registry","registered_title","registered_year","registered_doi","venue","volume","issue","page","article_number","metadata_url","issues","source_url"]
    with (args.output / "reference_audit.csv").open("w", newline="") as f:
        w=csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in results:
            m=row.get("registry_metadata", {})
            w.writerow({**{k:row.get(k) for k in cols},
                       **{k:m.get(k) for k in ("registry","registered_title","registered_year","registered_doi","venue","volume","issue","page","article_number","metadata_url")},
                       "issues":"; ".join(row["issues"])})
    lines = ["# 25-reference bibliographic audit",
             "",
             "Retrieved from Crossref, DataCite or official URLs. A status of REGISTRY_MATCH means the DOI, supplied title, year and first-author name are mutually consistent, not that every page/volume field has been individually matched.",
             "",
             "| # | DOI/official URL | Registry / official-link outcome | Issues |",
             "|---:|---|---|---|"]
    for row in results:
        lines.append(f'| {row["number"]} | {row["doi"] or row["source_url"]} | {row["status"]} | {"; ".join(row["issues"]) or "None detected"} |')
    lines += ["", "## Registry bibliographic fields", ""]
    for row in results:
        m=row.get("registry_metadata", {})
        lines += [f'### [{row["number"]}] {row["title"]}',
                  f'- Cited: {row["first_author"]} ({row["year"] or "no year"}). DOI: {row["doi"] or "not supplied"}.',
                  f'- Registry: {m.get("registry") or "not applicable"}; title: {m.get("registered_title") or "not available"}; authors: {", ".join(m.get("authors", [])[:10]) or "not available"}; year: {m.get("registered_year") or "not available"}.',
                  f'- Venue: {m.get("venue") or "not available"}; volume: {m.get("volume") or "not available"}; issue: {m.get("issue") or "not available"}; pages/article: {m.get("page") or m.get("article_number") or "not available"}.',
                  f'- Source: {m.get("metadata_url") or row["source_url"]}.', ""]
    (args.output / "reference_audit.md").write_text("\n".join(lines)+"\n")
    if any(x["status"]=="DOI_METADATA_UNAVAILABLE" for x in results):
        print("CAUTION: some DOI metadata requests did not return a record",flush=True)
    print(json.dumps({k:v for k,v in audit.items() if k!="records"},indent=2),flush=True)


if __name__=="__main__":
    main()
