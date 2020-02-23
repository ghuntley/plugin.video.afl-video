from __future__ import absolute_import, unicode_literals

import io
import json
import os
import re
import sys

try:
    import mock
except ImportError:
    import unittest.mock as mock

import responses

import testtools

import drmhelper

import resources.lib.config as config
from resources.tests.fakes import fakes


def escape_regex(s):
    escaped = re.escape(s)
    return escaped.replace('\\{', '{').replace('\\}', '}')


class PlayTests(testtools.TestCase):
    @classmethod
    def setUpClass(self):
        cwd = os.path.join(os.getcwd(), 'resources/tests')
        with open(os.path.join(cwd, 'fakes/json/AUTH.json'), 'rb') as f:
            self.AUTH_JSON = io.BytesIO(f.read()).read()
        with open(os.path.join(cwd, 'fakes/json/BC_EDGE.json'), 'rb') as f:
            self.BC_EDGE_JSON = io.BytesIO(f.read()).read()
            with open(os.path.join(cwd, 'fakes/json/CONFIG.json'), 'rb') as f:
                self.CONFIG_JSON = io.BytesIO(f.read()).read()
        with open(os.path.join(cwd, 'fakes/json/EMBED_TOKEN.json'),
                  'rb') as f:
            self.EMBED_TOKEN_JSON = io.BytesIO(f.read()).read()

    @responses.activate
    @mock.patch('resources.lib.stream_auth.addon.getSetting')
    @mock.patch.object(drmhelper.helper.DRMHelper, 'check_inputstream')
    @mock.patch('resources.lib.stream_auth.cache.get')
    @mock.patch('xbmcgui.ListItem')
    @mock.patch('sys.argv',
                ['plugin://plugin.video.afl-video/',
                 '2',
                 '?&genre=Sport&live=True&rating=PG&thumbnail=https%3A%2F'
                 '%2Fresources.afl.com.au%2Fafl%2Fphoto%2F2020%2F02%2F11'
                 '%2F20758dde-9b43-41c1-a087-695442a7f1a1%2FAFLLIVEPASS_x2-2'
                 '-.jpg&title=%5BCOLOR+green%5D%5BLIVE+NOW%5D%5B%2FCOLOR%5D'
                 '+Western+Bulldogs+v+North+Melbourne&type=B&video_id'
                 '=bar'])
    def test_play_video_live(self, mock_listitem, mock_ticket, mock_drm,
                             mock_sub_type):
        escaped_auth_url = re.escape(
            config.AUTH_URL).replace('\\{', '{').replace('\\}', '}')
        auth_url = re.compile(escaped_auth_url.format('.*', '.*', '.*'))
        responses.add(responses.GET, auth_url,
                      body=self.AUTH_JSON, status=200)

        escaped_embed_url = re.escape(
            config.EMBED_TOKEN_URL).replace('\\{', '{').replace('\\}', '}')
        embed_url = re.compile(escaped_embed_url.format('.*', '.*'))
        responses.add(responses.GET, embed_url,
                      body=self.EMBED_TOKEN_JSON, status=200)
        responses.add(responses.POST, config.TOKEN_URL,
                      body=json.dumps({'token': 'abcdef'}), status=200)
        responses.add(responses.GET, config.CONFIG_URL, body=self.CONFIG_JSON,
                      status=200)
        edge_url = config.BC_EDGE_URL.format(account_id='foo', video_id='bar')
        responses.add(responses.GET, edge_url, body=self.BC_EDGE_JSON,
                      status=200)
        mock_ticket.return_value = 'foobar123456'
        mock_listitem.side_effect = fakes.FakeListItem
        mock_drm.return_value = True
        mock_sub_type.return_value = '0'
        mock_plugin = fakes.FakePlugin()
        with mock.patch.dict('sys.modules', xbmcplugin=mock_plugin):
            import resources.lib.play as play
            play.play(sys.argv[2][1:])
            self.assertEqual(fakes.M3U8_URL_BC.get('stream_url'),
                             mock_plugin.resolved[2].getPath())

    @responses.activate
    @mock.patch.object(drmhelper.helper.DRMHelper, 'check_inputstream')
    @mock.patch('xbmcgui.ListItem')
    @mock.patch('sys.argv',
                ['plugin://plugin.video.afl-video/',
                 '2',
                 '?title=foo&genre=Sport&account_id=foo&video_id=bar'
                 '&thumbnail=https://image&type=B'])
    def test_play_video_bc(self, mock_listitem, mock_drm):
        mock_drm.return_value = True
        responses.add(responses.POST, config.TOKEN_URL,
                      body=json.dumps({'token': 'abcdef'}), status=200)
        edge_url = config.BC_EDGE_URL.format(account_id='foo', video_id='bar')
        responses.add(responses.GET, edge_url, body=self.BC_EDGE_JSON,
                      status=200)
        responses.add(responses.GET, config.CONFIG_URL, body=self.CONFIG_JSON,
                      status=200)
        mock_listitem.side_effect = fakes.FakeListItem
        mock_plugin = fakes.FakePlugin()
        with mock.patch.dict('sys.modules', xbmcplugin=mock_plugin):
            import resources.lib.play as play
            play.play(sys.argv[2][1:])
            self.assertEqual(fakes.M3U8_URL_BC.get('stream_url'),
                             mock_plugin.resolved[2].getPath())

    @responses.activate
    @mock.patch('resources.lib.stream_auth.addon.getSetting')
    @mock.patch('drmhelper.check_inputstream')
    @mock.patch('resources.lib.stream_auth.cache.get')
    @mock.patch('xbmcgui.ListItem')
    @mock.patch('sys.argv',
                ['plugin://plugin.video.afl-video/',
                 '2',
                 '?&date=2019-09-28&description=Watch+the+full+replay+of+the'
                 '+final+quarter&genre=Sport&video_id'
                 '=1yNGE5dDoyTdUKykqSeTysvmgup-rvS1&rating=PG'
                 '&subscription_required=True&thumbnail=http%3A%2F'
                 '%2Fbpvideos.telstra.insnw.net%2Fweb%2Fimages'
                 '%2F20190928170147a_1024x576.jpg&title=GF%3A+Tigers+v'
                 '+Giants+Q4&type=O'])
    def test_play_video_replay_ooyala(self, mock_listitem, mock_ticket,
                                      mock_drm, mock_sub_type):
        edge_url = config.BC_EDGE_URL.format(account_id='foo', video_id='bar')
        responses.add(responses.GET, edge_url, body=self.BC_EDGE_JSON,
                      status=200)
        responses.add(responses.POST, config.TOKEN_URL,
                      body=json.dumps({'token': 'abcdef'}), status=200)
        responses.add(responses.GET, config.CONFIG_URL, body=self.CONFIG_JSON,
                      status=200)
        escaped_auth_url = re.escape(
            config.AUTH_URL).replace('\\{', '{').replace('\\}', '}')
        auth_url = re.compile(escaped_auth_url.format('.*', '.*', '.*'))
        responses.add(responses.GET, auth_url,
                      body=self.AUTH_JSON, status=200)

        escaped_embed_url = re.escape(
            config.EMBED_TOKEN_URL).replace('\\{', '{').replace('\\}', '}')
        embed_url = re.compile(escaped_embed_url.format('.*', '.*'))
        responses.add(responses.GET, embed_url,
                      body=self.EMBED_TOKEN_JSON, status=200)
        mock_ticket.return_value = 'foobar123456'
        mock_listitem.side_effect = fakes.FakeListItem
        mock_drm.return_value = True
        mock_sub_type.return_value = '0'
        mock_plugin = fakes.FakePlugin()
        with mock.patch.dict('sys.modules', xbmcplugin=mock_plugin):
            import resources.lib.play as play
            play.play(sys.argv[2][1:])
            self.assertEqual(fakes.M3U8_URL_OOYALA.get('stream_url'),
                             mock_plugin.resolved[2].getPath())
