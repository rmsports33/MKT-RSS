"""Regressions for live provider failures; no real requests or waits."""
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from mkt_flow_p0 import rewriter
from tools.produce_bank_article import minute_quota_delay, ObservedModules
from test_generation_brief_required import brief


@pytest.mark.parametrize('scope,wait,expected', [
    ('tokens_per_minute', 12, 12), ('requests_per_minute', None, 60),
    ('tokens_per_day', 12, None), ('unknown', 12, None),
    ('tokens_per_minute', 66, None), ('tokens_per_minute', True, None),
])
def test_only_proven_minute_quota_allows_one_bounded_recovery(scope, wait, expected):
    assert minute_quota_delay({'error_code': 'PROVIDER_RATE_LIMIT',
        'limit_scope': scope, 'retry_after_seconds': wait}) == expected


def test_actual_writer_exports_safe_quota_code_without_provider_message(monkeypatch):
    error = RuntimeError('429 tokens per day SECRET_PROVIDER_BODY')
    error.response = SimpleNamespace(headers={'retry-after': '150.2'})
    create = Mock(side_effect=error)
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(rewriter, '_get_client', lambda: (client, ''))
    observed = ObservedModules()
    result = observed.call('generation', rewriter.reescrever_materia,
                           'Documento', 'Insumo completo. ' * 120, editorial_brief=brief())
    assert result['limit_scope'] == 'tokens_per_day'
    assert result['retry_after_seconds'] == 151
    assert result['error_code'] == 'PROVIDER_RATE_LIMIT'
    assert create.call_count == 1
    assert minute_quota_delay(result) is None
    assert 'SECRET' not in str(result) + str(observed.events)
    assert observed.events[0]['error_code'] == 'PROVIDER_RATE_LIMIT'
