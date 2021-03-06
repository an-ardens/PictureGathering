# coding: utf-8
import configparser
from contextlib import ExitStack
from datetime import datetime
from datetime import date
from datetime import timedelta
import json
from mock import patch, MagicMock, PropertyMock
import os
import requests
from requests_oauthlib import OAuth1Session
import shutil
import unittest

import freezegun

import DBControlar
import PictureGathering_fav


class TestCrawler(unittest.TestCase):
    def setUp(self):
        self.CONFIG_FILE_NAME = "config.ini"

        self.img_url_s = 'http://www.img.filename.sample.com/media/sample.png'
        self.img_filename_s = os.path.basename(self.img_url_s)
        self.tweet_url_s = 'http://www.tweet.sample.com'
        self.save_file_fullpath_s = os.getcwd()
        self.tweet_s = self.__GetTweetSample(self.img_url_s)
        self.del_tweet_s = self.__GetDelTweetSample()
        self.media_tweet_s = self.__GetMediaTweetSample(self.img_url_s)

        PictureGathering_fav.Crawler.add_cnt = 0
        PictureGathering_fav.Crawler.del_cnt = 0
        PictureGathering_fav.Crawler.add_url_list = []
        PictureGathering_fav.Crawler.del_url_list = []

    def __GetMediaTweetSample(self, img_url_s):
        # ツイートオブジェクトのサンプルを生成する
        tweet_json = f'''{{
            "extended_entities": {{
                "media": [{{
                    "media_url": "{img_url_s}_1"
                }},
                {{
                    "media_url": "{img_url_s}_2"
                }}
                ]
            }},
            "created_at": "Sat Nov 18 17:12:58 +0000 2018",
            "id_str": "12345_id_str_sample",
            "user": {{
                "id_str": "12345_id_str_sample",
                "name": "shift_name_sample",
                "screen_name": "_shift4869_screen_name_sample"
            }},
            "text": "tweet_text_sample"
        }}'''
        tweet_s = json.loads(tweet_json)
        return tweet_s

    def __GetTweetSample(self, img_url_s):
        # ツイートオブジェクトのサンプルを生成する
        tweet_json = f'''{{
            "entities": {{
                "media": {{
                    "expanded_url": "{self.tweet_url_s}"
                }}
            }},
            "created_at": "Sat Nov 18 17:12:58 +0000 2018",
            "id_str": "12345_id_str_sample",
            "user": {{
                "id_str": "12345_id_str_sample",
                "name": "shift_name_sample",
                "screen_name": "_shift4869_screen_name_sample"
            }},
            "text": "tweet_text_sample"
        }}'''
        tweet_s = json.loads(tweet_json)
        return tweet_s

    def __GetDelTweetSample(self):
        # ツイートオブジェクトのサンプルを生成する
        tweet_json = f'''{{
            "created_at": "Sat Nov 18 17:12:58 +0000 2018",
            "id_str": "12345_id_str_sample",
            "text": "@s_shift4869 PictureGathering run.\\n2018/03/09 11:59:38 Process Done !!\\nadd 1 new images. delete 0 old images."
        }}'''
        tweet_s = json.loads(tweet_json)
        return tweet_s

    def test_CrawlerInit(self):
        # Crawlerの初期状態をテストする
        crawler = PictureGathering_fav.Crawler()

        # config
        expect_config = configparser.ConfigParser()
        self.assertTrue(os.path.exists(self.CONFIG_FILE_NAME))
        self.assertFalse(
            expect_config.read("ERROR_PATH" + self.CONFIG_FILE_NAME, encoding="utf8")
        )
        expect_config.read(self.CONFIG_FILE_NAME, encoding="utf8")

        with self.assertRaises(KeyError):
            print(expect_config["ERROR_KEY1"]["ERROR_KEY2"])

        self.assertEqual(expect_config["twitter_token_keys"]["consumer_key"],
                         crawler.TW_CONSUMER_KEY)
        self.assertEqual(expect_config["twitter_token_keys"]["consumer_secret"],
                         crawler.TW_CONSUMER_SECRET)
        self.assertEqual(expect_config["twitter_token_keys"]["access_token"],
                         crawler.TW_ACCESS_TOKEN_KEY)
        self.assertEqual(expect_config["twitter_token_keys"]["access_token_secret"],
                         crawler.TW_ACCESS_TOKEN_SECRET)

        self.assertEqual(expect_config["line_token_keys"]["token_key"],
                         crawler.LN_TOKEN_KEY)

        self.assertEqual(os.path.abspath(expect_config["save_directory"]["save_fav_path"]),
                         crawler.save_fav_path)
        self.assertTrue(os.path.exists(crawler.save_fav_path))
        # self.assertEqual(os.path.abspath(expect_config["save_directory"]["save_retweet_path"]),
        #                  crawler.save_retweet_path)
        # self.assertTrue(os.path.exists(crawler.save_retweet_path))

        self.assertEqual(expect_config["tweet_timeline"]["user_name"],
                         crawler.user_name)
        # self.assertEqual(int(expect_config["tweet_timeline"]["retweet_get_max_loop"]),
        #                  crawler.retweet_get_max_loop)
        self.assertEqual(int(expect_config["tweet_timeline"]["get_pages"]) + 1,
                         crawler.get_pages)
        self.assertEqual(int(expect_config["tweet_timeline"]["count"]),
                         crawler.count)
        self.assertIn(crawler.config["tweet_timeline"]["kind_of_timeline"],
                      ["favorite", "home"])

        self.assertIn(expect_config["timestamp"]["timestamp_created_at"],
                      crawler.config["timestamp"]["timestamp_created_at"])

        self.assertIn(expect_config["notification"]["is_post_fav_done_reply"],
                      crawler.config["notification"]["is_post_fav_done_reply"])
        self.assertIn(expect_config["notification"]["is_post_retweet_done_reply"],
                      crawler.config["notification"]["is_post_retweet_done_reply"])
        self.assertIn(expect_config["notification"]["reply_to_user_name"],
                      crawler.config["notification"]["reply_to_user_name"])
        self.assertIn(expect_config["notification"]["is_post_line_notify"],
                      crawler.config["notification"]["is_post_line_notify"])

        self.assertIn(expect_config["holding"]["holding_file_num"],
                      crawler.config["holding"]["holding_file_num"])

        self.assertIn(expect_config["processes"]["image_magick"],
                      crawler.config["processes"]["image_magick"])
        if crawler.config["processes"]["image_magick"] != "":
            self.assertTrue(os.path.exists(crawler.config["processes"]["image_magick"]))

        self.assertIsInstance(crawler.oath, OAuth1Session)

    def test_TwitterAPIRequest(self):
        # TwitterAPIの応答をチェックする
        crawler = PictureGathering_fav.Crawler()

        for i in range(1, crawler.get_pages):
            url = "https://api.twitter.com/1.1/favorites/list.json"
            params = {
                "screen_name": crawler.user_name,
                "page": i,
                "count": crawler.count,
                "include_entities": 1  # ツイートのメタデータ取得。複数枚の画像取得用。
            }
            self.assertIsNotNone(crawler.TwitterAPIRequest(url, params))

        url = "https://api.twitter.com/1.1/statuses/home_timeline.json"
        params = {
            "count": crawler.count,
            "include_entities": 1
        }
        self.assertIsNotNone(crawler.TwitterAPIRequest(url, params))

        url = "https://api.twitter.com/1.1/users/show.json"
        params = {
            "screen_name": crawler.config["notification"]["reply_to_user_name"],
        }
        self.assertIsNotNone(crawler.TwitterAPIRequest(url, params))

    def test_FavTweetsGet(self):
        # Favツイートの取得をチェックする
        with patch('PictureGathering_fav.Crawler.TwitterAPIRequest') as mocksql:
            mocksql.return_value = self.tweet_s
            crawler = PictureGathering_fav.Crawler()

            for i in range(1, crawler.get_pages):
                res = crawler.FavTweetsGet(i)
                self.assertIsNotNone(res)

    def test_ImageSaver(self):
        # 画像保存をチェックする
        use_file_list = []
        with patch('DBControlar.DBControlar.DBFavUpsert') as mocksql:
            with patch('PictureGathering_fav.urllib.request.urlopen') as mockurllib:
                with patch('PictureGathering_fav.os.system') as mocksystem:
                    mocksql.return_value = 0
                    mocksystem.return_value = 0
                    crawler = PictureGathering_fav.Crawler()
                    crawler.save_fav_path = os.getcwd()

                    def urlopen_side_effect(url_orig):
                        url = url_orig.replace(":orig", "")
                        save_file_path = os.path.join(crawler.save_fav_path, os.path.basename(url))

                        with open(save_file_path, 'wb') as fout:
                            fout.write("test".encode())

                        use_file_list.append(save_file_path)
                        return open(save_file_path, 'rb')

                    mockurllib.side_effect = urlopen_side_effect

                    tweets = []
                    tweets.append(self.media_tweet_s)
                    expect_save_num = len(self.media_tweet_s["extended_entities"]["media"])
                    self.assertEqual(0, crawler.ImageSaver(tweets))

                    self.assertEqual(expect_save_num, crawler.add_cnt)
                    self.assertEqual(expect_save_num, mocksql.call_count)
                    self.assertEqual(expect_save_num, mockurllib.call_count)
                    self.assertEqual(expect_save_num, mocksystem.call_count)

        for path in use_file_list:
            self.assertTrue(os.path.exists(path))

        # テストで使用したファイルを削除する（後始末）
        for path in use_file_list:
            os.remove(path)

        # with freezegun.freeze_time('2018-11-18 17:12:58'):
        #     url_orig_s = self.img_url_s + ":orig"
        #     td_format_s = '%a %b %d %H:%M:%S +0000 %Y'
        #     dts_format_s = '%Y-%m-%d %H:%M:%S'
        #     tca = self.tweet_s["created_at"]
        #     dst = datetime.strptime(tca, td_format_s)
        #     expect = (os.path.basename(self.img_url_s),
        #               url_orig_s,
        #               self.img_url_s + ":large",
        #               self.tweet_s["id_str"],
        #               self.tweet_s["entities"]["media"][0]["expanded_url"],
        #               dst.strftime(dts_format_s),
        #               self.tweet_s["user"]["id_str"],
        #               self.tweet_s["user"]["name"],
        #               self.tweet_s["user"]["screen_name"],
        #               self.tweet_s["text"],
        #               self.save_file_fullpath_s,
        #               datetime.now().strftime(dts_format_s))
        #     actual = controlar._DBControlar__GetUpdateParam(self.img_url_s, self.tweet_s, self.save_file_fullpath_s)
        #     self.assertEqual(expect, actual)

    def test_ShrinkFolder(self):
        # フォルダ内ファイルの数を一定にする機能をチェックする
        crawler = PictureGathering_fav.Crawler()
        holding_file_num = int(crawler.config["holding"]["holding_file_num"])

        xs = []
        for root, dir, files in os.walk(crawler.save_fav_path):
            for f in files:
                path = os.path.join(root, f)
                xs.append((os.path.getmtime(path), path))
        os.walk(crawler.save_fav_path).close()

        file_list = []
        for mtime, path in sorted(xs, reverse=True):
            file_list.append(path)

        expect_del_cnt = 0
        expect_del_url_list = []
        for i, file in enumerate(file_list):
            if i > holding_file_num:
                # os.remove(file)
                expect_del_cnt += 1
                base_url = 'http://pbs.twimg.com/media/{}:orig'
                expect_del_url_list.append(
                    base_url.format(os.path.basename(file)))

        with patch('PictureGathering_fav.os.remove') as mockos:
            mockos.return_value = 0
            self.assertEqual(0, crawler.ShrinkFolder(holding_file_num))

            self.assertEqual(expect_del_cnt, crawler.del_cnt)
            self.assertEqual(expect_del_url_list, crawler.del_url_list)

    def test_EndOfProcess(self):
        # 取得後処理をチェックする
        crawler = PictureGathering_fav.Crawler()
        with ExitStack() as stack:
            # with句にpatchを複数入れる
            mockwhtml = stack.enter_context(patch('WriteHTML.WriteFavHTML'))
            mockcptweet = stack.enter_context(patch('PictureGathering_fav.Crawler.PostTweet'))
            mockcplnotify = stack.enter_context(patch('PictureGathering_fav.Crawler.PostLineNotify'))
            mocksql = stack.enter_context(patch('DBControlar.DBControlar.DBDelSelect'))
            mockoauth = stack.enter_context(patch('requests_oauthlib.OAuth1Session.post'))

            # mock設定
            mockwhtml.return_value = 0
            mockcptweet.return_value = 0
            mockcplnotify.return_value = 0
            mocksql.return_value = []
            mockoauth.return_value = 0

            media_url_list = self.media_tweet_s["extended_entities"]["media"]
            for media_url in media_url_list:
                crawler.add_url_list.append(media_url["media_url"])
                crawler.del_url_list.append(media_url["media_url"])
            crawler.add_cnt = len(crawler.add_url_list)
            crawler.del_cnt = len(crawler.del_url_list)

            self.assertEqual(0, crawler.EndOfProcess())

    def test_PostTweet(self):
        # ツイートポスト機能をチェックする
        crawler = PictureGathering_fav.Crawler()
        with ExitStack() as stack:
            # with句にpatchを複数入れる
            mockctapi = stack.enter_context(patch('PictureGathering_fav.Crawler.TwitterAPIRequest'))
            mockoauth = stack.enter_context(patch('requests_oauthlib.OAuth1Session.post'))
            mocksql = stack.enter_context(patch('DBControlar.DBControlar.DBDelInsert'))

            # mock設定
            mockctapi.return_value = {"id_str": "12345_id_str_sample"}
            responce = MagicMock()
            status_code = PropertyMock()
            status_code.return_value = 200
            type(responce).status_code = status_code
            text = PropertyMock()
            text.return_value = f'{{"text": "sample"}}'
            type(responce).text = text
            mockoauth.return_value = responce
            mocksql.return_value = 0

            self.assertEqual(0, crawler.PostTweet("test"))
            mockctapi.assert_called_once()
            mockoauth.assert_called_once()
            mocksql.assert_called_once()

    def test_PostLineNotify(self):
        # LINE通知ポスト機能をチェックする
        crawler = PictureGathering_fav.Crawler()
        with ExitStack() as stack:
            # with句にpatchを複数入れる
            mockreq = stack.enter_context(patch('PictureGathering_fav.requests.post'))

            # mock設定
            responce = MagicMock()
            status_code = PropertyMock()
            status_code.return_value = 200
            type(responce).status_code = status_code
            mockreq.return_value = responce

            self.assertEqual(0, crawler.PostLineNotify("test"))
            mockreq.assert_called_once()

    def test_Crawl(self):
        # 全体の流れをチェックする
        crawler = PictureGathering_fav.Crawler()
        with ExitStack() as stack:
            # with句にpatchを複数入れる
            mockft = stack.enter_context(patch('PictureGathering_fav.Crawler.FavTweetsGet'))
            mockis = stack.enter_context(patch('PictureGathering_fav.Crawler.ImageSaver'))
            mocksf = stack.enter_context(patch('PictureGathering_fav.Crawler.ShrinkFolder'))
            mockeop = stack.enter_context(patch('PictureGathering_fav.Crawler.EndOfProcess'))

            # mock設定
            rv_list = []
            rv_list.append({"test": "sample"})
            mockft.return_value = rv_list
            mockis.return_value = 0
            mocksf.return_value = 0
            mockeop.return_value = 0

            expect_config = configparser.ConfigParser()
            self.assertTrue(os.path.exists(self.CONFIG_FILE_NAME))
            self.assertFalse(
                expect_config.read("ERROR_PATH" + self.CONFIG_FILE_NAME, encoding="utf8")
            )
            expect_config.read(self.CONFIG_FILE_NAME, encoding="utf8")
            get_pages = int(expect_config["tweet_timeline"]["get_pages"])
            self.assertEqual(0, crawler.Crawl())
            self.assertEqual(get_pages, mockft.call_count)
            self.assertEqual(get_pages, mockis.call_count)
            mocksf.assert_called_once()
            mockeop.assert_called_once()

if __name__ == "__main__":
    unittest.main()
