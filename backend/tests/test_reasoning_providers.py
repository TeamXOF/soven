"""Provider contracts use synthetic text and mocked transport only; no live calls."""
import asyncio
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch, AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services import model_client as client
from services import reasoning
from agents import orchestrator


class Response:
    def __init__(self, envelope=None, status=200, raw=None):
        self.status_code = status
        self.raw = raw if raw is not None else json.dumps(envelope).encode()
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True

    def iter_content(self, chunk_size):
        for start in range(0, len(self.raw), chunk_size):
            yield self.raw[start:start + chunk_size]


def chat(data=None, **overrides):
    choice = {'finish_reason': 'stop', 'message': {'content': json.dumps(data or {'tip': 'Read again.', 'syllables': ['read']})}}
    choice.update(overrides)
    return Response({'choices': [choice]})


SCHEMA = reasoning._closed_schema(reasoning.WordCoaching.model_json_schema())


class ProviderContracts(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            'OFFLINE_MODE': '0', 'REASONING_PROVIDER': 'meta',
            'REASONING_ACCESS_CONFIRMED': '1', 'REASONING_API_KEY': 'synthetic-test-key',
            'REASONING_MODEL': 'synthetic-model', 'REASONING_BASE_URL': 'https://example.invalid/v1',
            'GOOGLE_API_KEYS': '', 'GOOGLE_API_KEY': '', 'ENV': 'dev'})
        self.env.start()
        self.transport = patch.object(client.requests, 'post', return_value=chat())
        self.post = self.transport.start()
        self.addCleanup(self.transport.stop)
        self.addCleanup(self.env.stop)

    def generate(self, **kwargs):
        return client.generate_json_sync('Read kindly.', {'word': 'book'}, 'ignored-google-model', schema=SCHEMA, **kwargs)

    def body(self):
        return json.loads(self.post.call_args.kwargs['data'])

    def test_meta_protocol_schema_and_provenance(self):
        result = self.generate()
        self.assertEqual(result.provider, 'meta')
        self.assertEqual(result.model, 'synthetic-model')
        self.assertEqual(client.result_source(result), 'meta')
        self.assertEqual(self.post.call_args.args[0], 'https://api.meta.ai/v1/chat/completions')
        request = self.body()
        self.assertEqual(request['messages'][0]['role'], 'developer')
        self.assertEqual(json.loads(request['messages'][1]['content']), {'word': 'book'})
        self.assertEqual(request['response_format']['json_schema']['schema'], SCHEMA)
        self.assertEqual(request['max_completion_tokens'], 2048)
        self.assertFalse(self.post.call_args.kwargs['allow_redirects'])
        self.assertTrue(self.post.call_args.kwargs['stream'])
        self.assertEqual(self.post.call_args.kwargs['timeout'], (3, 10))
        self.assertTrue(self.post.return_value.closed)

    def test_default_google_keeps_existing_contract(self):
        os.environ.pop('REASONING_PROVIDER')
        os.environ['GOOGLE_API_KEYS'] = ' first-synthetic-key,second-synthetic-key'
        self.post.return_value = Response({'candidates': [{'finishReason': 'STOP', 'content': {'parts': [
            {'text': 'hidden', 'thought': True}, {'text': '{"tip":"Read again."}'}]}}]})
        result = client.generate_json_sync('Prompt', {}, 'gemini-test')
        self.assertEqual(client.result_source(result), 'gemini')
        self.assertEqual(self.post.call_args.kwargs['headers']['x-goog-api-key'], 'first-synthetic-key')
        self.assertEqual(self.body()['generationConfig']['responseMimeType'], 'application/json')
        self.assertNotIn('response_format', self.body())

    def test_per_call_credentials_do_not_leak_between_calls(self):
        self.generate()
        os.environ['REASONING_API_KEY'] = 'second-synthetic-key'
        self.generate()
        headers = [c.kwargs['headers']['Authorization'] for c in self.post.call_args_list]
        self.assertEqual(headers, ['Bearer synthetic-test-key', 'Bearer second-synthetic-key'])

    def test_custom_https_endpoint_and_local_loopback(self):
        os.environ['REASONING_PROVIDER'] = 'chat_completions'
        result = self.generate()
        self.assertEqual(result.provider, 'chat_completions')
        self.assertEqual(self.post.call_args.args[0], 'https://example.invalid/v1/chat/completions')
        self.assertEqual(self.body()['messages'][0]['role'], 'system')
        os.environ.update(REASONING_BASE_URL='http://127.0.0.1:9000/v1', REASONING_API_KEY='')
        self.generate()
        self.assertNotIn('Authorization', self.post.call_args.kwargs['headers'])

    def test_unreviewed_missing_and_offline_configuration_make_no_call(self):
        for key, value in [('REASONING_ACCESS_CONFIRMED', '0'), ('REASONING_API_KEY', ''),
                           ('REASONING_MODEL', ''), ('OFFLINE_MODE', '1'), ('REASONING_PROVIDER', 'unknown')]:
            with self.subTest(key=key), patch.dict(os.environ, {key: value}):
                with self.assertRaises((RuntimeError, ValueError)):
                    self.generate()
        self.post.assert_not_called()

    def test_remote_insecure_credentials_and_redirect_urls_are_rejected(self):
        os.environ['REASONING_PROVIDER'] = 'chat_completions'
        for base in ['http://example.invalid/v1', 'https://user:pass@example.invalid/v1',
                     'https://example.invalid/v1?key=private', 'https://example.invalid/#x',
                     'file:///tmp/server', '', 'https://example.invalid:bad/v1']:
            with self.subTest(base=base), patch.dict(os.environ, REASONING_BASE_URL=base):
                with self.assertRaises(RuntimeError):
                    self.generate()
        self.post.assert_not_called()

    def test_http_errors_and_redirects_do_not_expose_provider_body(self):
        for status in [301, 400, 401, 429, 500]:
            self.post.return_value = Response(status=status, raw=b'private-sentinel')
            with self.assertRaises(RuntimeError) as caught:
                self.generate()
            self.assertNotIn('private-sentinel', str(caught.exception))
            self.assertIn(str(status), str(caught.exception))

    def test_transport_errors_are_redacted(self):
        self.post.side_effect = client.requests.Timeout('private-sentinel-with-url-and-key')
        with self.assertRaises(RuntimeError) as caught:
            self.generate()
        self.assertEqual(str(caught.exception), 'Reasoning provider transport failed')

    def test_bad_json_truncated_refused_and_empty_responses_fail(self):
        variants = [Response(raw=b'private-invalid-json'), Response([]), Response({}),
                    chat(finish_reason='length'), chat(message={'content': '{}', 'refusal': 'private'}),
                    chat(message={'content': '[]'}), chat(message={'content': 'private prose'}),
                    chat(message={'content': '{}', 'tool_calls': [{}]})]
        for response in variants:
            self.post.return_value = response
            with self.subTest(raw=response.raw[:20]), self.assertRaises(RuntimeError) as caught:
                self.generate()
            self.assertNotIn('private', str(caught.exception))

    def test_request_response_and_deadline_bounds(self):
        with self.assertRaisesRegex(RuntimeError, 'request exceeds'):
            client.generate_json_sync('x' * client.MAX_REQUEST_BYTES, {}, 'ignored', schema=SCHEMA)
        self.post.assert_not_called()
        self.post.return_value = Response(raw=b'x' * (client.MAX_RESPONSE_BYTES + 1))
        with self.assertRaisesRegex(RuntimeError, 'response exceeds'):
            self.generate()
        self.post.return_value = chat()
        with patch.object(client.time, 'monotonic', side_effect=[0, 11]):
            with self.assertRaisesRegex(RuntimeError, 'deadline'):
                self.generate()
        for timeout in [0, -1, 31, float('inf'), float('nan')]:
            with self.assertRaises(ValueError):
                self.generate(timeout=timeout)

    def test_provider_cannot_spoof_source_metadata(self):
        self.post.return_value = chat({'provider': 'google', 'model': 'fake', 'tip': 'Read slowly.'})
        result = self.generate()
        self.assertEqual(result['provider'], 'google')
        self.assertEqual(result.provider, 'meta')
        self.assertEqual(client.result_source(result), 'meta')
        self.assertEqual(client.result_source({}), 'model_unknown')

    def test_closed_nullable_schema_and_local_validation(self):
        schema = reasoning._closed_schema(reasoning.CoachingFeedback.model_json_schema())
        self.assertFalse(schema['additionalProperties'])
        self.assertEqual(set(schema['required']), set(schema['properties']))
        self.assertIn({'type': 'null'}, schema['properties']['teacher_note']['anyOf'])
        self.post.return_value = chat({'tip': 42, 'syllables': 'bad'})
        result = asyncio.run(reasoning.generate_word_tip('book'))
        self.assertEqual(result['source'], 'template')
        self.assertNotEqual(result['tip'], 42)

    def test_word_tip_uses_selected_provider_source(self):
        result = asyncio.run(reasoning.generate_word_tip('book'))
        self.assertEqual(result['source'], 'meta')
        self.assertEqual(self.post.call_count, 1)

    def test_feedback_source_and_template_failure_are_explicit(self):
        signal = {'accuracy': 100, 'words': [], 'hesitations': [], 'wpm': 40, 'transcript': 'A book.'}
        self.post.return_value = chat({'feedback_text': 'Read again.', 'comprehension_question': 'What is it?',
                                       'practice_recommendation': None, 'teacher_note': None})
        result = asyncio.run(reasoning.generate_feedback(signal, {'language': 'en'}))
        self.assertEqual(result['feedback_source'], 'meta')
        self.assertIsNone(result['teacher_note'])
        self.assertIsNone(result['practice_recommendation'])
        self.post.return_value = Response(status=429)
        result = asyncio.run(reasoning.generate_feedback(signal, {'language': 'ur'}))
        self.assertEqual(result['feedback_source'], 'template_fallback')
        self.assertTrue(any('ا' <= c <= 'ے' for c in result['feedback_text']))

    def test_no_google_retry_for_selected_provider_failure(self):
        os.environ['GOOGLE_API_KEYS'] = 'synthetic-google-key'
        self.post.return_value = Response(status=429)
        result = asyncio.run(reasoning.generate_word_tip('book'))
        self.assertEqual(result['source'], 'template')
        self.assertEqual(self.post.call_count, 1)
        self.post.reset_mock()
        result = asyncio.run(orchestrator.call_agent(orchestrator.DIFFICULTY_SYSTEM_PROMPT, {}))
        self.assertIn('error', result)
        self.assertEqual(self.post.call_count, 1)

    def test_unknown_provider_reaches_template_not_pipeline_failure(self):
        os.environ['REASONING_PROVIDER'] = 'unknown'
        result = asyncio.run(orchestrator.call_agent(orchestrator.DIFFICULTY_SYSTEM_PROMPT, {}))
        self.assertIn('error', result)
        self.post.assert_not_called()

    def test_async_timeout_does_not_claim_thread_cancellation(self):
        async def slow(*args):
            await asyncio.sleep(2)
        with patch.object(client.asyncio, 'to_thread', side_effect=slow):
            with self.assertRaises(asyncio.TimeoutError):
                asyncio.run(client.generate_json('p', {}, 'm', timeout=.01))
        self.post.assert_not_called()

    def test_inventory_adapters_are_not_live_validation(self):
        from core.provider_capabilities import provider_inventory
        rows = provider_inventory()
        meta = next(row for row in rows if row['id'] == 'meta_reasoning')
        self.assertTrue(meta['adapter_implemented'])
        self.assertEqual(meta['live_validation'], 'not_performed')
        self.assertNotIn('synthetic-test-key', json.dumps(rows))
        voice = next(row for row in rows if row['id'] == 'meta_voice')
        self.assertFalse(voice['adapter_implemented'])
        self.post.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
