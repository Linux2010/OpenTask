"""
Playwright 测试配置
"""

import pytest
import subprocess
import time
import os

# 测试服务配置
BASE_URL = "http://localhost:8090"


@pytest.fixture(scope="session")
def test_server():
    """启动测试服务器"""
    # 检查服务是否已运行
    import urllib.request
    try:
        urllib.request.urlopen(f"{BASE_URL}/health", timeout=2)
        yield  # 服务已运行
        return
    except:
        pass

    # 启动服务器
    process = subprocess.Popen(
        ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.getcwd()
    )

    # 等待服务启动
    time.sleep(3)

    yield

    # 清理
    process.terminate()


@pytest.fixture
def page_config(page):
    """页面基础配置"""
    page.set_default_timeout(10000)  # 10秒超时
    yield page


def wait_for_htmx(page, timeout=1000):
    """等待 HTMX 请求完成"""
    # HTMX 加载指示器消失
    page.wait_for_timeout(200)  # 等待请求触发
    page.wait_for_selector(".htmx-request", state="hidden", timeout=timeout)
    page.wait_for_timeout(100)  # 额外等待渲染