#!/usr/bin/env python3
"""One-off: convert Hugo data/data.yml into EmDash seed/seed.json.

Usage: python3 scripts/data-yml-to-seed.py > seed/seed.json   (needs PyYAML)
"""
import json
import re
import sys

import yaml

d = yaml.safe_load(open("data/data.yml"))


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def f(slug, label, type="string", **kw):
    return {"slug": slug, "label": label, "type": type, **kw}


def repeater(slug, label, subs):
    return f(slug, label, "repeater", validation={"subFields": subs})


def collection(slug, label, singular, title_field, fields, columns=()):
    return {
        "slug": slug,
        "label": label,
        "labelSingular": singular,
        "routable": False,
        "supports": ["revisions"],
        "titleField": title_field,
        "admin": {"listColumns": list(columns)},
        "fields": fields,
    }


def entry(prefix, slug, data):
    # Drop empty values so optional fields stay unset rather than "".
    data = {k: v for k, v in data.items() if v not in (None, "", [])}
    return {"id": f"{prefix}-{slug}", "slug": slug, "status": "published", "data": data}


basic, contact, meta = d["basic"], d["contact"], d["meta"]
contact = {k: v for k, v in contact.items() if v is not None}
SECTIONS = ["profile", "experience", "skill", "organization", "reference"]

collections = [
    collection(
        "resume", "Resume", "Resume", "name",
        [
            f("name", "Name", required=True),
            f("title", "Title"),
            f("avatar_show", "Show avatar", "boolean"),
            f("avatar_path", "Avatar path"),
            *[f(k, k.capitalize()) for k in contact],
            f("direction", "Text direction", "select", validation={"options": ["ltr", "rtl"]}),
            f("language", "Language"),
            f("close", "Hidden-resume message", "text"),
        ],
        ["title"],
    ),
    collection(
        "section", "Sections", "Section", "title",
        [
            f("key", "Key", "select", required=True, validation={"options": SECTIONS}),
            f("title", "Title", required=True),
            f("show", "Show", "boolean"),
            f("order", "Order", "integer"),
            f("description", "Description", "text"),
        ],
        ["key", "order", "show"],
    ),
    collection(
        "experience", "Experience", "Experience", "company",
        [
            f("company", "Company", required=True, searchable=True),
            f("link", "Link"),
            f("tags", "Tags"),
            f("role", "Role", searchable=True),
            f("location", "Location"),
            f("date", "Date"),
            f("description", "Description", "text", searchable=True),
            f("specialties", "Specialties", "text"),
            f("skills", "Skills", "text"),
            f("section", "Projects heading"),
            repeater("items", "Projects", [
                f("client", "Client"),
                f("project", "Project"),
                f("description", "Description", "text"),
            ]),
            f("order", "Order", "integer", required=True),
        ],
        ["role", "date", "order"],
    ),
    collection(
        "skill", "Skills", "Skill group", "name",
        [
            f("name", "Name", required=True),
            repeater("item", "Items", [f("name", "Name", required=True)]),
            f("order", "Order", "integer", required=True),
        ],
        ["order"],
    ),
    collection(
        "organization", "Organizations", "Organization", "organization",
        [
            f("organization", "Organization", required=True),
            f("role", "Role"),
            f("date", "Date"),
            f("url", "URL", "url"),
            f("description", "Description", "text"),
            f("order", "Order", "integer", required=True),
        ],
        ["role", "date", "order"],
    ),
    collection(
        "reference", "References", "Reference", "name",
        [
            f("name", "Name", required=True),
            f("role", "Role"),
            f("company", "Company"),
            f("contact", "Contact"),
            f("description", "Description", "text"),
            f("order", "Order", "integer", required=True),
        ],
        ["company", "order"],
    ),
]

content = {
    "resume": [entry("resume", "main", {
        "name": basic["name"],
        "title": basic["title"],
        "avatar_show": basic["avatar"]["show"],
        "avatar_path": basic["avatar"]["path"],
        **contact,
        "direction": meta["direction"],
        "language": meta["language"],
        "close": d.get("close"),
    })],
    "section": [
        entry("section", k, {
            "key": k,
            "title": d[k]["title"],
            "show": d[k]["show"],
            "order": d[k]["order"],
            "description": d[k].get("description"),
        })
        for k in SECTIONS
    ],
    "experience": [
        entry("experience", slugify(e["company"]), {
            **{k: v for k, v in e.items() if k != "items"},
            "items": [{k: v for k, v in p.items() if v is not None} for p in e.get("items", [])],
            "order": i,
        })
        for i, e in enumerate(d["experience"]["items"], 1)
    ],
    "skill": [
        entry("skill", slugify(g["name"]), {
            "name": g["name"],
            "item": [{"name": s} for s in g["item"]],
            "order": i,
        })
        for i, g in enumerate(d["skill"]["groups"], 1)
    ],
    "organization": [
        entry("organization", slugify(o["organization"]), {**o, "order": i})
        for i, o in enumerate(d["organization"]["items"], 1)
    ],
    "reference": [
        entry("reference", slugify(r["name"]), {**r, "order": i})
        for i, r in enumerate(d["reference"].get("items") or [], 1)
    ],
}

seed = {
    "$schema": "https://emdashcms.com/seed.schema.json",
    "version": "1",
    "meta": {"name": basic["name"], "description": "Online resume", "author": basic["name"]},
    "settings": {"title": basic["name"], "tagline": basic["title"]},
    "collections": collections,
    "content": content,
}
json.dump(seed, sys.stdout, indent="\t", ensure_ascii=False)
sys.stdout.write("\n")
