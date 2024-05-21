"""插件加载测试

测试代码修改自 <https://github.com/Lancercmd/nonebot2-store-test>，谢谢 [Lan 佬](https://github.com/Lancercmd)。

在 GitHub Actions 中运行，通过 GitHub Event 文件获取所需信息。并将测试结果保存至 GitHub Action 的输出文件中。

当前会输出 RESULT, OUTPUT, METADATA 三个数据，分别对应测试结果、测试输出、插件元数据。

经测试可以直接在 Python 3.10+ 环境下运行，无需额外依赖。
"""
# ruff: noqa: T201, ASYNC101

import asyncio
import json
import os
import re
from asyncio import create_subprocess_shell, run, subprocess
from pathlib import Path
from urllib.request import urlopen

# NoneBot Store
STORE_PLUGINS_URL = (
    "https://raw.githubusercontent.com/nonebot/nonebot2/master/assets/plugins.json"
)
# 匹配信息的正则表达式
ISSUE_PATTERN = r"### {}\s+([^\s#].*?)(?=(?:\s+###|$))"
# 插件信息
PROJECT_LINK_PATTERN = re.compile(ISSUE_PATTERN.format("PyPI 项目名"))
MODULE_NAME_PATTERN = re.compile(ISSUE_PATTERN.format("插件 import 包名"))
CONFIG_PATTERN = re.compile(r"### 插件配置项\s+```(?:\w+)?\s?([\s\S]*?)```")

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


def strip_ansi(text: str | None) -> str:
    """去除 ANSI 转义字符"""
    if not text:
        return ""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def get_plugin_list() -> dict[str, str]:
    """获取插件列表

    通过 package_name 获取 module_name
    """
    with urlopen(STORE_PLUGINS_URL) as response:
        plugins = json.loads(response.read())

    return {plugin["project_link"]: plugin["module_name"] for plugin in plugins}


class PluginTest:
    def __init__(
        self, project_link: str, module_name: str, config: str | None = None
    ) -> None:
        self.project_link = project_link
        self.module_name = module_name
        self.config = config
        self._plugin_list = None

        self._create = False
        self._run = False
        self._deps = []

        # 输出信息
        self._output_lines: list[str] = []

        # 插件测试目录
        self.test_dir = Path("plugin_test")
        # 通过环境变量获取 GITHUB 输出文件位置
        self.github_output_file = Path(os.environ.get("GITHUB_OUTPUT", ""))
        self.github_step_summary_file = Path(os.environ.get("GITHUB_STEP_SUMMARY", ""))

    @property
    def key(self) -> str:
        """插件的标识符

        project_link:module_name
        例：nonebot-plugin-test:nonebot_plugin_test
        """
        return f"{self.project_link}:{self.module_name}"

    @property
    def path(self) -> Path:
        """插件测试目录"""
        # 替换 : 为 -，防止文件名不合法
        key = self.key.replace(":", "-")
        return self.test_dir / f"{key}-test"

    async def run(self):
        # 运行前创建测试目录
        if not self.test_dir.exists():
            self.test_dir.mkdir()

        await self.create_poetry_project()
        if self._create:
            await self.show_plugin_dependencies()
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
            summary = f"插件 {self.project_link} 加载测试结果：{'通过' if self._run else '未通过'}\n"
            summary += f"<details><summary>测试输出</summary><pre><code>{ansiless_output}</code></pre></details>"
            f.write(f"{summary}")
        return self._run, output

    def get_env(self) -> dict[str, str]:
        """获取环境变量"""
        env = os.environ.copy()
        # 删除虚拟环境变量，防止 poetry 使用运行当前脚本的虚拟环境
        env.pop("VIRTUAL_ENV", None)
        # 启用 LOGURU 的颜色输出
        env["LOGURU_COLORIZE"] = "true"
        # Poetry 配置
        # https://python-poetry.org/docs/configuration/#virtualenvsin-project
        env["POETRY_VIRTUALENVS_IN_PROJECT"] = "true"
        # https://python-poetry.org/docs/configuration/#virtualenvsprefer-active-python-experimental
        env["POETRY_VIRTUALENVS_PREFER_ACTIVE_PYTHON"] = "true"
        return env

    async def create_poetry_project(self) -> None:
        if not self.path.exists():
            self.path.mkdir(parents=True)
            proc = await create_subprocess_shell(
                f"""poetry init -n && sed -i "s/\\^/~/g" pyproject.toml && poetry env info --ansi && poetry add {self.project_link}""",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.path,
                env=self.get_env(),
            )
            stdout, stderr = await proc.communicate()
            code = proc.returncode

            self._create = not code
            if self._create:
                print(f"项目 {self.project_link} 创建成功。")
                for i in stdout.decode().strip().splitlines():
                    print(f"    {i}")
            else:
                self._log_output(f"项目 {self.project_link} 创建失败：")
                for i in stderr.decode().strip().splitlines():
                    self._log_output(f"    {i}")
        else:
            self._log_output(f"项目 {self.project_link} 已存在，跳过创建。")
            self._create = True

    async def show_package_info(self) -> None:
        if self.path.exists():
            proc = await create_subprocess_shell(
                f"poetry show {self.project_link} --ansi",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.path,
                env=self.get_env(),
            )
            stdout, _ = await proc.communicate()
            code = proc.returncode
            if not code:
                self._log_output(f"插件 {self.project_link} 的信息如下：")
                for i in stdout.decode().splitlines():
                    self._log_output(f"    {i}")
            else:
                self._log_output(f"插件 {self.project_link} 信息获取失败。")

    async def show_plugin_dependencies(self) -> None:
        if self.path.exists():
            proc = await create_subprocess_shell(
                "poetry export --without-hashes",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.path,
                env=self.get_env(),
            )
            stdout, _ = await proc.communicate()
            code = proc.returncode
            if not code:
                self._log_output(f"插件 {self.project_link} 依赖的插件如下：")
                for i in stdout.decode().strip().splitlines():
                    module_name = self._get_plugin_module_name(i)
                    if module_name:
                        self._deps.append(module_name)
                self._log_output(f"    {', '.join(self._deps)}")
            else:
                self._log_output(f"插件 {self.project_link} 依赖获取失败。")

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

    @property
    def plugin_list(self) -> dict[str, str]:
        """获取插件列表"""
        if self._plugin_list is None:
            self._plugin_list = get_plugin_list()
        return self._plugin_list

    def _get_plugin_module_name(self, require: str) -> str | None:
        # anyio==3.6.2 ; python_version >= "3.11" and python_version < "4.0"
        # pydantic[dotenv]==1.10.6 ; python_version >= "3.10" and python_version < "4.0"
        match = re.match(r"^(.+?)(?:\[.+\])?==", require.strip())
        if match:
            package_name = match.group(1)
            # 不用包括自己
            if package_name in self.plugin_list and package_name != self.project_link:
                return self.plugin_list[package_name]


async def main():
    # 测试插件
    test = PluginTest(
        "nonebot-plugin-dg-lab-play",
        "nonebot_plugin_dg_lab_play",
        "",
    )
    await test.run()


if __name__ == "__main__":
    run(main())
