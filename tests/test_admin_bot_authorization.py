import unittest
from types import SimpleNamespace
from unittest.mock import patch
from admin import bot

class AuthorizationTests(unittest.TestCase):
    def test_empty_denied(self):
        with patch.object(bot, 'ALLOWED_IDS', set()):
            self.assertFalse(bot._is_allowed(SimpleNamespace(effective_user=SimpleNamespace(id=12), effective_chat=SimpleNamespace(id=34))))

    def test_user_allowed(self):
        with patch.object(bot, 'ALLOWED_IDS', {12}):
            self.assertTrue(bot._is_allowed(SimpleNamespace(effective_user=SimpleNamespace(id=12), effective_chat=SimpleNamespace(id=-34))))

    def test_group_only_denied(self):
        with patch.object(bot, 'ALLOWED_IDS', {-34}):
            self.assertFalse(bot._is_allowed(SimpleNamespace(effective_user=SimpleNamespace(id=56), effective_chat=SimpleNamespace(id=-34))))

    def test_unknown_user_denied(self):
        with patch.object(bot, 'ALLOWED_IDS', {12}):
            self.assertFalse(bot._is_allowed(SimpleNamespace(effective_user=SimpleNamespace(id=56), effective_chat=SimpleNamespace(id=34))))

    def test_absent_user_denied(self):
        with patch.object(bot, 'ALLOWED_IDS', {12}):
            self.assertFalse(bot._is_allowed(SimpleNamespace(effective_user=None, effective_chat=SimpleNamespace(id=12))))
