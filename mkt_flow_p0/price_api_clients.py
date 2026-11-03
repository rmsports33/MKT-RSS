"""Cliente mínimo Mercado Livre. Sem OAuth interativo ou renovação implícita.

Transporte e relógio injetáveis permitem homologação totalmente offline.
Amazon/Shopee não são implementados neste módulo.
"""
import math
import re
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

import requests


class PriceAPIError(ValueError):
    """Erro sanitizado: nunca inclui token, corpo HTTP ou exceção de transporte."""


class MercadoLivreClient:
    def __init__(self, access_token, *, session=None, sleep=time.sleep,
                 clock=time.monotonic, now=None, max_attempts=3,
                 interval=1.0, max_wait=30.0, timeout=10):
        if not 1 <= max_attempts <= 3 or not 0 < timeout <= 30:
            raise ValueError("limites invalidos")
        if not math.isfinite(interval) or interval < 0 or not 0 <= max_wait <= 30:
            raise ValueError("limites invalidos")
        self._token = str(access_token or '')
        self.session = session if session is not None else requests.Session()
        self.sleep, self.clock = sleep, clock
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.max_attempts, self.interval = max_attempts, interval
        self.max_wait, self.timeout = max_wait, timeout
        self._last = None

    def _retry_wait(self, response, attempt):
        raw = response.headers.get('Retry-After') if response is not None else None
        if raw is None:
            delay = 2 ** attempt
        else:
            try:
                delay = float(raw)
            except (ValueError, TypeError):
                try:
                    delay = (parsedate_to_datetime(raw) - self.now()).total_seconds()
                except (ValueError, TypeError, OverflowError):
                    raise PriceAPIError('Retry-After invalido') from None
        if not math.isfinite(delay) or delay > self.max_wait:
            raise PriceAPIError('aguarde antes de tentar novamente')
        return max(0, delay)

    def get_item(self, item_id):
        if not self._token or '\r' in self._token or '\n' in self._token:
            raise PriceAPIError('credenciais: access token ausente ou invalido')
        if not isinstance(item_id, str) or not re.fullmatch(r'MLB[0-9]+', item_id):
            raise PriceAPIError('identificador MLB invalido')
        response = None
        for attempt in range(self.max_attempts):
            if self._last is not None:
                self.sleep(max(0, self.interval - (self.clock() - self._last)))
            self._last = self.clock()
            try:
                response = self.session.get(
                    'https://api.mercadolibre.com/items/' + item_id,
                    headers={'Authorization': 'Bearer ' + self._token},
                    timeout=self.timeout, allow_redirects=False)
            except requests.RequestException:
                response = None
            if response is not None:
                if response.status_code == 200:
                    break
                if response.status_code not in (429, 500, 502, 503, 504):
                    raise PriceAPIError('HTTP ' + str(response.status_code))
            if attempt + 1 == self.max_attempts:
                raise PriceAPIError('coleta indisponivel apos tentativas limitadas')
            self.sleep(self._retry_wait(response, attempt))
        try:
            data = response.json()
        except (ValueError, TypeError):
            raise PriceAPIError('resposta JSON invalida') from None
        if not isinstance(data, dict):
            raise PriceAPIError('resposta invalida')
        if (data.get('id') != item_id or data.get('site_id') != 'MLB'
                or data.get('currency_id') != 'BRL' or data.get('status') != 'active'):
            raise PriceAPIError('item, moeda ou disponibilidade invalidos')
        value = data.get('price')
        try:
            price = Decimal(str(value))
        except InvalidOperation:
            raise PriceAPIError('preco invalido') from None
        if isinstance(value, bool) or not price.is_finite() or price <= 0 or price > Decimal('1000000000'):
            raise PriceAPIError('preco invalido')
        url = data.get('permalink')
        try:
            parsed = urlsplit(url if isinstance(url, str) else '')
            valid = (parsed.scheme == 'https' and parsed.hostname in
                     {'mercadolivre.com.br', 'www.mercadolivre.com.br', 'produto.mercadolivre.com.br'}
                     and not parsed.username and not parsed.password and parsed.port in (None, 443)
                     and parsed.path not in ('', '/'))
        except ValueError:
            valid = False
        if not valid:
            raise PriceAPIError('URL de oferta invalida')
        return {'preco': str(price), 'data_captura': self.now().strftime('%d/%m/%Y'),
                'url': url, 'item_id': item_id, 'marketplace': 'mercadolivre'}
