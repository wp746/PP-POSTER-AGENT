import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'event-kv-poster'


def test_skill_frontmatter_and_refs_exist():
    text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
    assert text.startswith('---\nname: event-kv-poster\n')
    assert 'description: Use when' in text
    for name in ['style-library.md', 'provider-contract.md', 'io-schema.md']:
        assert (SKILL / 'references' / name).exists()


def test_registry_has_exactly_p01_to_p18():
    registry = json.loads((SKILL / 'registry.json').read_text(encoding='utf-8'))
    assert [x['code'] for x in registry['styles']] == [f'P{i:02d}' for i in range(1,19)]
    assert registry['defaults']['count'] == 3
    assert registry['defaults']['aspect_ratio'] == '9:16'
    assert registry['defaults']['final_pixels'] == '2160x3840'


def test_style_library_has_meta_template_for_every_style():
    text = (SKILL / 'references' / 'style-library.md').read_text(encoding='utf-8')
    for i in range(1,19):
        code=f'P{i:02d}'
        assert f'## {code}' in text
        assert f'<!-- {code}-META-START -->' in text
        assert f'<!-- {code}-META-END -->' in text
