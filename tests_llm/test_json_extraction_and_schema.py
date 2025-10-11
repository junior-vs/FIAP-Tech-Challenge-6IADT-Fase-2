import json, pathlib
from jsonschema import validate
from src.llm.utils import extract_json_from_markdown

SCHEMAS = pathlib.Path("schemas/llm_outputs")

def _load_schema(name: str):
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))

def test_extract_json_ok():
    md = "x\n```json\n{\"answer\":\"ok\"}\n```\ny"
    d = extract_json_from_markdown(md)
    assert d["answer"] == "ok"

def test_extract_json_fail():
    try:
        extract_json_from_markdown("sem json")
        assert False
    except ValueError:
        assert True

def test_schemas_exist():
    for f in ["driver_instructions.schema.json","report.schema.json","improvements.schema.json","nlq.schema.json"]:
        assert (SCHEMAS / f).exists()

def test_validate_nlq_schema_example():
    schema = _load_schema("nlq.schema.json")
    data = {"answer":"exemplo","references":["vehicle:V1"]}
    validate(instance=data, schema=schema)
