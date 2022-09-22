#!/usr/bin/env python3
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import asyncio
import bcrypt
import markdown
import os.path
import re
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.locks
import tornado.options
import tornado.web
import unicodedata
import logging
from blind_watermark import WaterMark
from PIL import Image, ImageDraw, ImageFont
import sys
from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)

class NoResultError(Exception):
    pass

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/dewatermark", DewatermarkHandler),
        ]


        settings = dict(
            blog_title="盲水印测试",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
        )
        super().__init__(handlers, **settings)




# 加水印页面
class HomeHandler(tornado.web.RequestHandler):
    
    async def get(self):
        self.render("home.html")

    def post(self):
        text = self.get_argument("text")
        logging.info("text",text)
        for field_name, files in self.request.files.items():
            for info in files:

                fnt = ImageFont.truetype("font.TTF", 30)

                filename, content_type = info["filename"], info["content_type"]
                body = info["body"]
                logging.info(
                    'POST "%s" "%s" %d bytes', filename, content_type, len(body)
                )
                # 保存原始图片文件
                watermark_origin = open("static/watermark/origin.png", 'wb')
                watermark_origin.write(info['body'])
                watermark_origin.close()
                
                watermark_im = Image.new(mode='RGB',size=(200,60))

                draw = ImageDraw.Draw(watermark_im)
                draw.text((10, 10), text,font=fnt, fill=(255, 255, 255, 128))
                
                # 生成水印图片文件
                # write to stdout
                watermark_im.save("static/watermark/watermark.png", "PNG")
                watermark_im.close()


                # 嵌入图片水印
                bwm1 = WaterMark(password_wm=1, password_img=1)
                # read original image
                bwm1.read_img('static/watermark/origin.png')
                # read watermark
                bwm1.read_wm('static/watermark/watermark.png')
                # embed
                bwm1.embed('static/watermark/watermarked.png')

        self.render("home.html")

# 解水印页面
class DewatermarkHandler(tornado.web.RequestHandler):
    async def get(self):
        self.render("dewatermark.html")
    
    def post(self):
        for field_name, files in self.request.files.items():
            for info in files:
                filename, content_type = info["filename"], info["content_type"]
                body = info["body"]
                logging.info(
                    'POST "%s" "%s" %d bytes', filename, content_type, len(body)
                )
                dewatermak_origin = open("static/dewatermark/origin.png", 'wb')
                dewatermak_origin.write(info['body'])


                bwm1 = WaterMark(password_wm=1, password_img=1)
                # notice that wm_shape is necessary
                bwm1.extract(filename="static/dewatermark/origin.png", wm_shape=(60, 200), out_wm_name='static/dewatermark/result.png') 

        self.render("dewatermark.html")

async def main():
    tornado.options.parse_command_line()

    # Create the global connection pool.
   
    app = Application()
    app.listen(options.port)

    # In this demo the server will simply run until interrupted
    # with Ctrl-C, but if you want to shut down more gracefully,
    # call shutdown_event.set().
    shutdown_event = tornado.locks.Event()
    await shutdown_event.wait()


if __name__ == "__main__":
    asyncio.run(main())
