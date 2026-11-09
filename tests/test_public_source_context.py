import unittest
from mkt_flow_p0.public_source_context import verify_context

URL='https://tecnoblog.net/noticias/iphone-example'
PAGE=('<link rel="canonical" href="'+URL+'"><article><h1>iPhone</h1><p>O teclado.</p></article>').encode()


class PublicSourceContextTests(unittest.TestCase):
    def test_robots_precedes_page_and_context_is_not_factual_approval(self):
        calls=[]
        def transport(url):
            calls.append(url)
            return b'User-agent: *\nAllow: /' if url.endswith('robots.txt') else PAGE
        result=verify_context(URL,['iphone','teclado'],transport=transport)
        self.assertEqual(calls,['https://tecnoblog.net/robots.txt',URL])
        self.assertTrue(result['canonical_matches']);self.assertFalse(result['factuality_verified'])

    def test_blocked_robots_or_wrong_host_prevents_article_fetch(self):
        calls=[]
        def transport(url):calls.append(url);return b'User-agent: *\nDisallow: /'
        with self.assertRaisesRegex(ValueError,'SOURCE_ROBOTS_BLOCKED'):verify_context(URL,['iphone'],transport=transport)
        self.assertEqual(len(calls),1)
        with self.assertRaisesRegex(ValueError,'SOURCE_OUTSIDE_ALLOWLIST'):verify_context('https://other.example/',[],transport=transport)
        self.assertEqual(len(calls),1)

    def test_sidebar_mentions_or_wrong_canonical_do_not_verify_context(self):
        for page in (PAGE.replace(b'<article>',b'<nav>').replace(b'</article>',b'</nav>'),
                     PAGE.replace(URL.encode(),b'https://tecnoblog.net/wrong')):
            with self.assertRaises(ValueError):
                verify_context(URL,['iphone','teclado'],transport=lambda url:b'User-agent: *\nAllow: /' if url.endswith('robots.txt') else page)


if __name__=='__main__':unittest.main()
