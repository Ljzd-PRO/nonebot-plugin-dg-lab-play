"""插件加载测试

测试代码修改自 <https://github.com/Lancercmd/nonebot2-store-test>，谢谢 [Lan 佬](https://github.com/Lancercmd)。

在 GitHub Actions 中运行，通过 GitHub Event 文件获取所需信息。并将测试结果保存至 GitHub Action 的输出文件中。

当前会输出 RESULT, OUTPUT, METADATA 三个数据，分别对应测试结果、测试输出、插件元数据。

经测试可以直接在 Python 3.10+ 环境下运行，无需额外依赖。
"""
# ruff: noqa: T201, ASYNC101

import asyncio
import os
import re
from asyncio import create_subprocess_shell, run, subprocess
from pathlib import Path
from typing import Optional, List, Dict

FAKE_SCRIPT = """from typing import Optional, Union

from nonebot import logger
from nonebot.drivers import (
    ASGIMixin,
    HTTPClientMixin,
    HTTPClientSession,
    HTTPVersion,
    Request,
    Response,
    WebSocketClientMixin,
)
from nonebot.drivers import Driver as BaseDriver
from nonebot.internal.driver.model import (
    CookieTypes,
    HeaderTypes,
    QueryTypes,
)
from typing_extensions import override


class Driver(BaseDriver, ASGIMixin, HTTPClientMixin, WebSocketClientMixin):
    @property
    @override
    def type(self) -> str:
        return "fake"

    @property
    @override
    def logger(self):
        return logger

    @override
    def run(self, *args, **kwargs):
        super().run(*args, **kwargs)

    @property
    @override
    def server_app(self):
        return None

    @property
    @override
    def asgi(self):
        raise NotImplementedError

    @override
    def setup_http_server(self, setup):
        raise NotImplementedError

    @override
    def setup_websocket_server(self, setup):
        raise NotImplementedError

    @override
    async def request(self, setup: Request) -> Response:
        raise NotImplementedError

    @override
    async def websocket(self, setup: Request) -> Response:
        raise NotImplementedError

    @override
    def get_session(
        self,
        params: QueryTypes = None,
        headers: HeaderTypes = None,
        cookies: CookieTypes = None,
        version: Union[str, HTTPVersion] = HTTPVersion.H11,
        timeout: Optional[float] = None,
        proxy: Optional[str] = None,
    ) -> HTTPClientSession:
        raise NotImplementedError
"""

RUNNER_SCRIPT = """import json
import os

from nonebot import init, load_plugin, logger, require
from pydantic import BaseModel


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)


init()
plugin = load_plugin("{}")

if not plugin:
    exit(1)
else:
    if plugin.metadata:
        metadata = {{
            "name": plugin.metadata.name,
            "description": plugin.metadata.description,
            "usage": plugin.metadata.usage,
            "type": plugin.metadata.type,
            "homepage": plugin.metadata.homepage,
            "supported_adapters": plugin.metadata.supported_adapters,
        }}
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf8") as f:
            f.write(f"METADATA<<EOF\\n{{json.dumps(metadata, cls=SetEncoder)}}\\nEOF\\n")

        if plugin.metadata.config and not issubclass(plugin.metadata.config, BaseModel):
            logger.error("插件配置项不是 Pydantic BaseModel 的子类")
            exit(1)

{}
"""


def strip_ansi(text: Optional[str]) -> str:
    """去除 ANSI 转义字符"""
    if not text:
        return ""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


class PluginTest:
    def __init__(
            self, module_name: str, config: str = None, python: str = ">=3.9,<4.0"
    ) -> None:
        self.module_name = module_name
        self.config = config
        self.python = python
        self._plugin_list = None

        self._create = False
        self._run = False
        self._deps = []

        # 输出信息
        self._output_lines: List[str] = []

        # 插件测试目录
        self.test_dir = Path("plugin_test")
        # 通过环境变量获取 GITHUB 输出文件位置
        self.github_output_file = Path(os.environ.get("GITHUB_OUTPUT", ""))
        self.github_step_summary_file = Path(os.environ.get("GITHUB_STEP_SUMMARY", ""))

    @property
    def path(self) -> Path:
        """插件测试目录"""
        return self.test_dir / f"{self.module_name}-test"

    async def run(self):
        # 运行前创建测试目录
        if not self.test_dir.exists():
            self.test_dir.mkdir()

        await self.create_poetry_project()
        if self._create:
            await self.run_poetry_project()

        # 输出测试结果
        with open(self.github_output_file, "a", encoding="utf8") as f:
            f.write(f"RESULT={self._run}\n")
        # 输出测试输出
        output = "\n".join(self._output_lines)
        # GitHub 不支持 ANSI 转义字符所以去掉
        ansiless_output = strip_ansi(output)
        # 限制输出长度，防止评论过长，评论最大长度为 65536
        ansiless_output = ansiless_output[:50000]
        with open(self.github_output_file, "a", encoding="utf8") as f:
            f.write(f"OUTPUT<<EOF\n{ansiless_output}\nEOF\n")
        # 输出至作业摘要
        with open(self.github_step_summary_file, "a", encoding="utf8") as f:
            summary = f"插件 {self.module_name} 加载测试结果：{'通过' if self._run else '未通过'}\n"
            summary += f"<details><summary>测试输出</summary><pre><code>{ansiless_output}</code></pre></details>"
            f.write(f"{summary}")
        return self._run, output

    @staticmethod
    def get_env() -> Dict[str, str]:
        """获取环境变量"""
        env = os.environ.copy()
        # 启用 LOGURU 的颜色输出
        env["LOGURU_COLORIZE"] = "true"
        return env

    async def create_poetry_project(self) -> None:
        if not self.path.exists():
            self.path.mkdir(parents=True)
            proc = await create_subprocess_shell(
                f'poetry init --name=plugin-test --python="{self.python}" -n',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.path,
                env=self.get_env(),
            )
            stdout, stderr = await proc.communicate()
            code = proc.returncode

            self._create = not code
            if self._create:
                print(f"项目 {self.module_name} 创建成功。")
                for i in stdout.decode().strip().splitlines():
                    print(f"    {i}")
            else:
                self._log_output(f"项目 {self.module_name} 创建失败：")
                for i in stderr.decode().strip().splitlines():
                    self._log_output(f"    {i}")
        else:
            self._log_output(f"项目 {self.module_name} 已存在，跳过创建。")
            self._create = True

    async def run_poetry_project(self) -> None:
        if self.path.exists():
            # 默认使用 fake 驱动
            with open(self.path / ".env", "w", encoding="utf8") as f:
                f.write("DRIVER=fake")
            # 如果提供了插件配置项，则写入配置文件
            if self.config is not None:
                with open(self.path / ".env.prod", "w", encoding="utf8") as f:
                    f.write(self.config)

            with open(self.path / "fake.py", "w", encoding="utf8") as f:
                f.write(FAKE_SCRIPT)

            with open(self.path / "runner.py", "w", encoding="utf8") as f:
                f.write(
                    RUNNER_SCRIPT.format(
                        self.module_name,
                        "\n".join([f"require('{i}')" for i in self._deps]),
                    )
                )

            proc = None
            try:
                proc = await create_subprocess_shell(
                    "poetry run python runner.py",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=self.path,
                    env=self.get_env(),
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=600)
                code = proc.returncode
            except asyncio.TimeoutError:
                if proc:
                    proc.terminate()
                stdout = b""
                stderr = "测试超时".encode()
                code = 1

            self._run = not code

            status = "正常" if self._run else "出错"
            self._log_output(f"插件 {self.module_name} 加载{status}：")

            _out = stdout.decode().strip().splitlines()
            _err = stderr.decode().strip().splitlines()
            for i in _out:
                self._log_output(f"    {i}")
            for i in _err:
                self._log_output(f"    {i}")

    def _log_output(self, output: str) -> None:
        """记录输出，同时打印到控制台"""
        print(output)
        self._output_lines.append(output)


async def main():
    # 测试插件
    test = PluginTest(
        "nonebot_plugin_dg_lab_play"
    )
    return await test.run()


if __name__ == "__main__":
    is_success, _ = run(main())
    exit(not is_success)
