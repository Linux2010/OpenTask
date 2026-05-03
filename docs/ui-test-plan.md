# OpenTask 管理端自动化测试方案

> **测试框架：** Playwright (Python)
> **创建日期：** 2026-05-03
> **测试范围：** HTMX + Jinja2 管理端 UI 功能测试

---

## 1. 为什么选择 Playwright

| 特点 | Playwright | Selenium |
|------|------------|----------|
| **自动等待** | ✅ 内置智能等待，无需手动 sleep | ❌ 需手动添加 wait |
| **浏览器驱动** | ✅ 内置 Chromium/Firefox/Safari | ❌ 需单独安装 WebDriver |
| **API 简洁度** | ✅ 现代化 API，代码更短 | 较复杂，链式调用 |
| **稳定性** | ✅ 自动重试，减少 flaky tests | 较多不稳定测试 |
| **调试体验** | ✅ Trace Viewer、Codegen | 仅有截图/日志 |
| **并发执行** | ✅ 内置并行支持 | 需额外配置 |

**结论：Playwright 更适合现代 Web 应用测试，学习成本低，维护简单。**

---

## 2. 安装步骤

### 2.1 安装依赖

```bash
# 安装 Python 包
pip install playwright pytest-playwright

# 安装浏览器（首次使用）
playwright install chromium

# 或安装所有浏览器
playwright install
```

### 2.2 验证安装

```bash
# 测试命令
playwright --version

# 运行简单测试
python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

---

## 3. 测试目录结构

```
tests/
├── __init__.py
├── conftest.py              # Playwright 配置和 fixtures
├── test_dashboard.py        # 仪表盘测试
├── test_tasks_list.py       # 任务列表测试
├── test_task_create.py      # 创建任务测试
├── test_task_detail.py      # 任务详情测试
├── test_task_operations.py  # 任务操作测试（开始/完成/失败）
└── pages/                   # Page Object 模型（可选）
│   ├── __init__.py
│   ├── dashboard_page.py
│   └── tasks_page.py
```

---

## 4. 测试用例设计

### 4.1 仪表盘测试 (`test_dashboard.py`)

| 用例 ID | 用例名称 | 测试步骤 | 预期结果 |
|---------|----------|----------|----------|
| D001 | 页面加载 | 打开 `/web/` | 显示仪表盘标题 |
| D002 | 统计卡片 | 检查四个统计卡片 | 显示待执行/执行中/已完成/失败数量 |
| D003 | 快速操作链接 | 点击"快速派任务" | 跳转到 `/web/tasks/new` |
| D004 | 最近任务表格 | 检查任务表格 | 显示最近 10 个任务 |

### 4.2 任务列表测试 (`test_tasks_list.py`)

| 用例 ID | 用例名称 | 测试步骤 | 预期结果 |
|---------|----------|----------|----------|
| L001 | 页面加载 | 打开 `/web/tasks` | 显示任务列表 |
| L002 | 筛选 - Bot | 选择 `assigned_to=anna` | 只显示 anna 的任务 |
| L003 | 筛选 - 状态 | 选择 `status=pending` | 只显示 pending 任务 |
| L004 | 筛选 - 优先级 | 选择 `priority=P0` | 只显示 P0 任务 |
| L005 | 清除筛选 | 点击清除按钮 | 显示全部任务 |
| L006 | 空列表提示 | 筛选无结果 | 显示"暂无任务" |

### 4.3 创建任务测试 (`test_task_create.py`)

| 用例 ID | 用例名称 | 测试步骤 | 预期结果 |
|---------|----------|----------|----------|
| C001 | 页面加载 | 打开 `/web/tasks/new` | 显示派任务表单 |
| C002 | 创建任务 - 基础 | 填写名称、选择 bot、提交 | 显示成功消息 |
| C003 | 创建任务 - 带参数 | 填写键值对参数 | 参数保存到 task_params |
| C004 | 创建任务 - 必填校验 | 不填名称直接提交 | 显示校验错误 |
| C005 | 默认值验证 | 检查默认值 | priority=P2, assigned_to=anna |

### 4.4 任务详情测试 (`test_task_detail.py`)

| 用例 ID | 用例名称 | 测试步骤 | 预期结果 |
|---------|----------|----------|----------|
| T001 | 页面加载 | 打开 `/web/tasks/{id}` | 显示任务详情 |
| T002 | 信息完整性 | 检查各字段 | 显示名称/描述/参数/状态等 |
| T003 | 时间信息 | 检查时间字段 | 显示创建/开始/完成时间 |
| T004 | 操作日志加载 | 检查日志区域 | 显示操作日志 |

### 4.5 任务操作测试 (`test_task_operations.py`)

| 用例 ID | 用例名称 | 测试步骤 | 预期结果 |
|---------|----------|----------|----------|
| O001 | 开始任务 | 点击"开始执行" | 状态变为 running |
| O002 | 完成任务 - 弹窗 | 点击"标记完成" | 显示输入弹窗 |
| O003 | 完成任务 - 提交 | 输入结果、提交 | 状态变为 completed |
| O004 | 标记失败 - 弹窗 | 点击"标记失败" | 显示输入弹窗 |
| O005 | 标记失败 - 提交 | 输入错误、提交 | 状态变为 failed |
| O006 | 重试任务 | 点击"重试" | 状态变为 pending |
| O007 | 取消任务 | 点击"取消" | 状态变为 cancelled |

---

## 5. 测试脚本示例

### 5.1 配置文件 (`conftest.py`)

```python
"""
Playwright 测试配置
"""

import pytest
from playwright.sync_api import Page, BrowserContext
from app.main import app
import uvicorn
import threading
import time

# 测试服务配置
BASE_URL = "http://localhost:8090"
API_KEY = "hope-bot-apikey-2026-0424"


@pytest.fixture(scope="session")
def test_server():
    """启动测试服务器"""
    # 在后台启动服务器
    thread = threading.Thread(
        target=lambda: uvicorn.run(
            app, host="0.0.0.0", port=8090, log_level="error"
        ),
        daemon=True
    )
    thread.start()
    time.sleep(2)  # 等待服务器启动
    yield
    # 服务器会随主线程退出


@pytest.fixture
def page(page: Page, test_server):
    """设置页面对象"""
    page.set_default_timeout(10000)  # 10秒超时
    yield page


@pytest.fixture
def authenticated_context(browser_context: BrowserContext):
    """带 API Key 的上下文（用于 API 测试）"""
    browser_context.add_init_script(f"""
        window.TEST_API_KEY = "{API_KEY}";
    """)
    yield browser_context
```

### 5.2 仪表盘测试 (`test_dashboard.py`)

```python
"""
仪表盘页面测试
"""

import pytest
from playwright.sync_api import Page, expect


BASE_URL = "http://localhost:8090"


@pytest.mark.ui
class TestDashboard:
    """仪表盘测试类"""

    def test_dashboard_loads(self, page: Page):
        """D001: 页面加载"""
        page.goto(f"{BASE_URL}/web/")
        
        # 检查标题
        expect(page).to_have_title("仪表盘 - OpenTask")
        
        # 检查导航栏
        expect(page.locator("nav")).to_be_visible()
        expect(page.locator("text=OpenTask")).to_be_visible()

    def test_stats_cards_visible(self, page: Page):
        """D002: 统计卡片显示"""
        page.goto(f"{BASE_URL}/web/")
        
        # 检查四个统计卡片
        expect(page.locator("text=待执行")).to_be_visible()
        expect(page.locator("text=执行中")).to_be_visible()
        expect(page.locator("text=已完成")).to_be_visible()
        expect(page.locator("text=失败")).to_be_visible()

    def test_quick_action_create_task(self, page: Page):
        """D003: 快速派任务链接"""
        page.goto(f"{BASE_URL}/web/")
        
        # 点击快速派任务按钮
        page.click("text=快速派任务")
        
        # 等待跳转
        page.wait_for_url(f"{BASE_URL}/web/tasks/new")
        expect(page).to_have_title("快速派任务 - OpenTask")

    def test_recent_tasks_table(self, page: Page):
        """D004: 最近任务表格"""
        page.goto(f"{BASE_URL}/web/")
        
        # 检查任务表格区域
        table_section = page.locator("h2:text('最近任务')")
        expect(table_section).to_be_visible()
```

### 5.3 任务列表测试 (`test_tasks_list.py`)

```python
"""
任务列表页面测试
"""

import pytest
from playwright.sync_api import Page, expect


BASE_URL = "http://localhost:8090"


@pytest.mark.ui
class TestTasksList:
    """任务列表测试类"""

    def test_tasks_list_loads(self, page: Page):
        """L001: 页面加载"""
        page.goto(f"{BASE_URL}/web/tasks")
        expect(page).to_have_title("任务列表 - OpenTask")

    def test_filter_by_bot(self, page: Page):
        """L002: 按 Bot 筛选"""
        page.goto(f"{BASE_URL}/web/tasks")
        
        # 选择 anna
        page.select_option("select[name=assigned_to]", "anna")
        
        # 触发筛选（点击筛选按钮）
        page.click("button:text('筛选')")
        
        # 等待 HTMX 加载
        page.wait_for_timeout(500)
        
        # 检查结果只显示 anna
        tasks = page.locator("tbody tr")
        if tasks.count() > 0:
            for i in range(tasks.count()):
                expect(tasks.nth(i).locator("td:nth-child(4)")).to_have_text("anna")

    def test_filter_by_status(self, page: Page):
        """L003: 按状态筛选"""
        page.goto(f"{BASE_URL}/web/tasks")
        
        page.select_option("select[name=status]", "pending")
        page.click("button:text('筛选')")
        page.wait_for_timeout(500)
        
        tasks = page.locator("tbody tr")
        if tasks.count() > 0:
            for i in range(tasks.count()):
                expect(tasks.nth(i).locator("text=pending")).to_be_visible()

    def test_clear_filter(self, page: Page):
        """L005: 清除筛选"""
        page.goto(f"{BASE_URL}/web/tasks")
        
        # 先设置筛选
        page.select_option("select[name=assigned_to]", "anna")
        page.click("button:text('筛选')")
        page.wait_for_timeout(500)
        
        # 点击清除
        page.click("text=清除")
        
        # 等待加载
        page.wait_for_url(f"{BASE_URL}/web/tasks")

    def test_create_task_button(self, page: Page):
        """任务列表页的快速派任务按钮"""
        page.goto(f"{BASE_URL}/web/tasks")
        
        page.click("text=快速派任务")
        page.wait_for_url(f"{BASE_URL}/web/tasks/new")
```

### 5.4 创建任务测试 (`test_task_create.py`)

```python
"""
创建任务测试
"""

import pytest
from playwright.sync_api import Page, expect


BASE_URL = "http://localhost:8090"


@pytest.mark.ui
class TestTaskCreate:
    """创建任务测试类"""

    def test_create_form_loads(self, page: Page):
        """C001: 表单页面加载"""
        page.goto(f"{BASE_URL}/web/tasks/new")
        expect(page).to_have_title("快速派任务 - OpenTask")
        
        # 检查表单字段
        expect(page.locator("input[name=task_name]")).to_be_visible()
        expect(page.locator("select[name=assigned_to]")).to_be_visible()
        expect(page.locator("select[name=priority]")).to_be_visible()

    def test_create_task_basic(self, page: Page):
        """C002: 创建基础任务"""
        page.goto(f"{BASE_URL}/web/tasks/new")
        
        # 填写表单
        page.fill("input[name=task_name]", "Playwright测试任务")
        page.select_option("select[name=assigned_to]", "anna")
        page.select_option("select[name=priority]", "P1")
        
        # 提交
        page.click("button:text('创建任务')")
        
        # 等待 HTMX 响应
        page.wait_for_timeout(1000)
        
        # 检查成功消息
        expect(page.locator("text=操作成功")).to_be_visible()
        expect(page.locator("text=已创建")).to_be_visible()

    def test_create_task_with_params(self, page: Page):
        """C003: 创建带参数的任务"""
        page.goto(f"{BASE_URL}/web/tasks/new")
        
        # 填写基本信息
        page.fill("input[name=task_name]", "带参数的测试任务")
        page.select_option("select[name=assigned_to]", "trump")
        
        # 填写键值对参数
        page.fill("input[name=param_key_1]", "server")
        page.fill("input[name=param_value_1]", "hope02")
        page.fill("input[name=param_key_2]", "action")
        page.fill("input[name=param_value_2]", "upload")
        
        # 提交
        page.click("button:text('创建任务')")
        page.wait_for_timeout(1000)
        
        # 检查成功
        expect(page.locator("text=操作成功")).to_be_visible()

    def test_required_field_validation(self, page: Page):
        """C004: 必填字段校验"""
        page.goto(f"{BASE_URL}/web/tasks/new")
        
        # 不填名称直接提交
        page.click("button:text('创建任务')")
        
        # 浏览器原生校验会阻止提交
        # 检查 input 是否有 validation 状态
        task_name_input = page.locator("input[name=task_name]")
        expect(task_name_input).to_have_attribute("required", "true")

    def test_default_values(self, page: Page):
        """C005: 默认值验证"""
        page.goto(f"{BASE_URL}/web/tasks/new")
        
        # 检查默认选择
        priority_select = page.locator("select[name=priority]")
        expect(priority_select).to_have_value("P2")
        
        assigned_select = page.locator("select[name=assigned_to]")
        expect(assigned_select).to_have_value("anna")
```

### 5.5 任务操作测试 (`test_task_operations.py`)

```python
"""
任务操作测试（开始/完成/失败等）
"""

import pytest
from playwright.sync_api import Page, expect


BASE_URL = "http://localhost:8090"


@pytest.mark.ui
class TestTaskOperations:
    """任务操作测试类"""

    def get_first_pending_task_id(self, page: Page) -> int:
        """获取第一个 pending 任务的 ID"""
        page.goto(f"{BASE_URL}/web/tasks")
        page.select_option("select[name=status]", "pending")
        page.click("button:text('筛选')")
        page.wait_for_timeout(500)
        
        first_row = page.locator("tbody tr").first
        if first_row.is_visible():
            task_id = first_row.locator("td:first-child").text_content()
            return int(task_id)
        return None

    def test_start_task(self, page: Page):
        """O001: 开始任务"""
        page.goto(f"{BASE_URL}/web/tasks")
        
        # 找一个 pending 任务
        page.select_option("select[name=status]", "pending")
        page.click("button:text('筛选')")
        page.wait_for_timeout(500)
        
        # 如果有 pending 任务，点击开始
        first_row = page.locator("tbody tr").first
        if first_row.is_visible():
            # 点击开始按钮（如果存在）
            start_btn = first_row.locator("text=开始")
            if start_btn.is_visible():
                start_btn.click()
                page.wait_for_timeout(500)
                
                # 检查状态变为 running
                expect(first_row.locator("text=running")).to_be_visible()

    def test_complete_task_modal(self, page: Page):
        """O002/O003: 完成任务弹窗和提交"""
        # 先确保有一个 running 任务
        page.goto(f"{BASE_URL}/web/tasks")
        page.select_option("select[name=status]", "running")
        page.click("button:text('筛选')")
        page.wait_for_timeout(500)
        
        if page.locator("tbody tr").count() > 0:
            task_id = page.locator("tbody tr").first.locator("td:first-child").text_content()
            
            # 进入详情页
            page.goto(f"{BASE_URL}/web/tasks/{task_id}")
            
            # 点击标记完成
            page.click("text=标记完成")
            page.wait_for_timeout(300)
            
            # 检查弹窗显示
            expect(page.locator("#modal")).to_be_visible()
            expect(page.locator("text=标记任务完成")).to_be_visible()
            
            # 输入结果
            page.fill("textarea[name=result]", "测试执行成功")
            page.click("button:text('确认完成')")
            page.wait_for_timeout(500)
            
            # 检查成功消息
            expect(page.locator("text=已完成")).to_be_visible()

    def test_fail_task_modal(self, page: Page):
        """O004/O005: 标记失败弹窗和提交"""
        # 确保有一个 running 任务
        page.goto(f"{BASE_URL}/web/tasks")
        page.select_option("select[name=status]", "running")
        page.click("button:text('筛选')")
        page.wait_for_timeout(500)
        
        if page.locator("tbody tr").count() > 0:
            task_id = page.locator("tbody tr").first.locator("td:first-child").text_content()
            page.goto(f"{BASE_URL}/web/tasks/{task_id}")
            
            # 点击标记失败
            page.click("text=标记失败")
            page.wait_for_timeout(300)
            
            expect(page.locator("#modal")).to_be_visible()
            
            page.fill("textarea[name=error_message]", "测试错误信息")
            page.click("button:text('确认失败')")
            page.wait_for_timeout(500)
            
            expect(page.locator("text=已标记失败")).to_be_visible()

    def test_retry_task(self, page: Page):
        """O006: 重试任务"""
        page.goto(f"{BASE_URL}/web/tasks")
        page.select_option("select[name=status]", "failed")
        page.click("button:text('筛选')")
        page.wait_for_timeout(500)
        
        if page.locator("tbody tr").count() > 0:
            task_id = page.locator("tbody tr").first.locator("td:first-child").text_content()
            page.goto(f"{BASE_URL}/web/tasks/{task_id}")
            
            page.click("text=重试任务")
            page.wait_for_timeout(500)
            
            expect(page.locator("text=已重新排队")).to_be_visible()

    def test_cancel_task(self, page: Page):
        """O007: 取消任务"""
        page.goto(f"{BASE_URL}/web/tasks")
        page.select_option("select[name=status]", "pending")
        page.click("button:text('筛选')")
        page.wait_for_timeout(500)
        
        if page.locator("tbody tr").count() > 0:
            task_id = page.locator("tbody tr").first.locator("td:first-child").text_content()
            page.goto(f"{BASE_URL}/web/tasks/{task_id}")
            
            page.click("text=取消任务")
            page.wait_for_timeout(500)
            
            expect(page.locator("text=已取消")).to_be_visible()
```

---

## 6. 运行测试

### 6.1 命令行运行

```bash
# 运行所有 UI 测试
pytest tests/ -v --headed

# 运行指定测试文件
pytest tests/test_dashboard.py -v

# 运行指定用例
pytest tests/test_dashboard.py::TestDashboard::test_dashboard_loads -v

# 生成 HTML 报告
pytest tests/ --html=report.html --self-contained-html

# 并行执行
pytest tests/ -v -n 4  # 4 个并行进程

# 查看浏览器运行（headed 模式）
pytest tests/ -v --headed --slowmo=500  # 每步延迟 500ms
```

### 6.2 Playwright 特殊命令

```bash
# 代码生成器（录制操作生成测试代码）
playwright codegen http://localhost:8090/web/

# Trace 查看（调试失败测试）
playwright show-trace trace.zip

# 截图
pytest tests/ --screenshot=only-on-failure

# 录制视频
pytest tests/ --video=retain-on-failure
```

---

## 7. 调试技巧

### 7.1 失败调试

```python
# 在测试中使用调试
def test_example(page: Page):
    page.goto("http://localhost:8090/web/")
    
    # 设置断点
    page.pause()  # 打开 Playwright Inspector
    
    # 截图保存
    page.screenshot(path="debug.png")
    
    # 打印页面内容
    print(page.content())
```

### 7.2 HTMX 等待处理

```python
# 等待 HTMX 请求完成
def wait_for_htmx(page: Page):
    """等待 HTMX 请求完成"""
    page.wait_for_selector(".htmx-request", state="hidden")
    page.wait_for_timeout(100)  # 额外等待渲染

# 使用示例
def test_htmx_filter(page: Page):
    page.select_option("select[name=status]", "pending")
    page.click("button:text('筛选')")
    wait_for_htmx(page)
```

---

## 8. CI/CD 集成

### 8.1 GitHub Actions

```yaml
# .github/workflows/ui-tests.yml
name: UI Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      
      - name: Start server
        run: |
          uvicorn app.main:app --host 0.0.0.0 --port 8090 &
          sleep 3
      
      - name: Run tests
        run: pytest tests/ -v
      
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

---

## 9. 预期问题修复

运行测试后可能发现的问题及修复方案：

| 问题 | 可能原因 | 修复方案 |
|------|----------|----------|
| Modal 不显示 | Alpine.js 未加载 | 添加 `page.wait_for_timeout()` |
| HTMX 无响应 | 等待时间不够 | 使用 `wait_for_htmx()` |
| 中文乱码 | 编码问题 | 检查 `<meta charset>` |
| 按钮找不到 | 动态渲染 | 使用 `page.wait_for_selector()` |
| 表单提交失败 | CSRF/校验 | 检查 hidden 字段 |

---

## 10. 执行步骤

```bash
# 1. 安装依赖
pip install playwright pytest-playwright pytest-html
playwright install chromium

# 2. 创建测试文件
mkdir -p tests/pages

# 3. 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8090 &

# 4. 运行测试
pytest tests/ -v --headed

# 5. 查看报告
open report.html
```

---

**文档作者：** Claude Code
**版本：** v1.0