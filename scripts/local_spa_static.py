"""本地 SPA 静态文件服务。

用于本地调试前端打包产物，支持前端路由回退到 index.html。
"""

from __future__ import annotations

import argparse
import http.server
import socketserver
from functools import partial
from pathlib import Path
from urllib import request as urlrequest
from urllib.error import HTTPError


class SpaStaticHandler(http.server.SimpleHTTPRequestHandler):
    """支持 SPA 路由回退的静态文件处理器。

    :param args: 父类位置参数
    :param kwargs: 父类关键字参数
    :return: 静态文件处理器实例
    """

    backend_target = "http://127.0.0.1:8001"

    def _proxy_to_backend(self) -> None:
        """转发本地 API 与上传资源请求到本地后端。

        :return: None
        """
        target_url = f"{self.backend_target}{self.path}"
        content_length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(content_length) if content_length else None
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in {"host", "origin", "referer", "content-length"}
        }
        req = urlrequest.Request(target_url, data=body, headers=headers, method=self.command)
        try:
            with urlrequest.urlopen(req, timeout=60) as resp:
                self.send_response(resp.status)
                self._copy_proxy_headers(resp.headers.items())
                self.end_headers()
                self.wfile.write(resp.read())
        except HTTPError as err:
            self.send_response(err.code)
            self._copy_proxy_headers(err.headers.items())
            self.end_headers()
            self.wfile.write(err.read())

    def _copy_proxy_headers(self, headers) -> None:
        """复制后端响应头，排除不适合本地代理转发的字段。

        :param headers: 后端响应头迭代器
        :return: None
        """
        skip_headers = {"connection", "transfer-encoding", "content-encoding", "content-length"}
        for key, value in headers:
            if key.lower() not in skip_headers:
                self.send_header(key, value)

    def do_GET(self) -> None:
        """处理 GET 请求，本地 API 走代理，其他请求走静态资源。

        :return: None
        """
        if self.path.startswith(("/api/", "/uploads/")):
            self._proxy_to_backend()
            return
        super().do_GET()

    def do_POST(self) -> None:
        """处理 POST 请求，本地 API 走代理。

        :return: None
        """
        self._proxy_to_backend()

    def do_PATCH(self) -> None:
        """处理 PATCH 请求，本地 API 走代理。

        :return: None
        """
        self._proxy_to_backend()

    def do_DELETE(self) -> None:
        """处理 DELETE 请求，本地 API 走代理。

        :return: None
        """
        self._proxy_to_backend()

    def send_head(self):
        """返回静态资源响应头，不存在的前端路由回退到首页。

        :return: 响应文件对象或 None
        """
        path = self.translate_path(self.path)
        request_path = Path(path)
        if request_path.exists() or "." in Path(self.path.split("?", 1)[0]).name:
            return super().send_head()
        # 本地调试生产构建产物时，前端路由需要交给 index.html 接管。
        self.path = "/"
        return super().send_head()


def main() -> None:
    """启动本地 SPA 静态文件服务。

    :return: None
    """
    parser = argparse.ArgumentParser(description="Serve SPA static files locally.")
    parser.add_argument("--directory", required=True, help="静态文件目录")
    parser.add_argument("--port", type=int, required=True, help="监听端口")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    args = parser.parse_args()

    handler = partial(SpaStaticHandler, directory=args.directory)
    with socketserver.TCPServer((args.host, args.port), handler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()
