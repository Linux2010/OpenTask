"""
任务详情和操作测试
"""

import re
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8090"


@pytest.mark.ui
class TestTaskDetail:
    """任务详情测试类"""

    def test_task_detail_loads(self, page: Page, test_server):
        """T001: 任务详情页面加载"""
        # 先创建一个任务
        page.goto(f"{BASE_URL}/web/tasks/new", wait_until="domcontentloaded")
        page.fill("input[name=task_name]", f"详情测试_{int(page.evaluate('Date.now()'))}")
        page.select_option("select[name=assigned_to]", "anna")
        page.click("button:text('创建任务')")
        page.wait_for_timeout(1000)

        # 点击查看详情链接
        page.click("text=查看任务详情")
        page.wait_for_timeout(500)

        # 检查详情页元素（使用更精确的标题匹配）
        expect(page).to_have_title(re.compile(r"任务 #\d+ - OpenTask"))
        expect(page.get_by_role("heading", name="基本信息")).to_be_visible()
        expect(page.get_by_role("heading", name="时间信息")).to_be_visible()
        expect(page.get_by_role("heading", name="执行结果")).to_be_visible()
        # 使用 exact=True 避免 "操作日志" 匹配
        expect(page.get_by_role("heading", name="操作", exact=True)).to_be_visible()

    def test_task_info_display(self, page: Page, test_server):
        """T002: 任务信息显示"""
        page.goto(f"{BASE_URL}/web/tasks/new", wait_until="domcontentloaded")
        page.fill("input[name=task_name]", "信息显示测试")
        page.fill("textarea[name=task_description]", "这是测试描述")
        page.fill("input[name=param_key_1]", "key1")
        page.fill("input[name=param_value_1]", "val1")
        page.click("button:text('创建任务')")
        page.wait_for_timeout(1000)
        page.click("text=查看任务详情")
        page.wait_for_timeout(500)

        # 检查各字段（使用更精确的选择器）
        expect(page.locator("h1")).to_contain_text("任务 #")
        expect(page.get_by_text("anna", exact=True)).to_be_visible()
        expect(page.get_by_text("pending", exact=True)).to_be_visible()

    def test_task_logs_section(self, page: Page, test_server):
        """T003: 操作日志区域"""
        page.goto(f"{BASE_URL}/web/tasks/new", wait_until="domcontentloaded")
        page.fill("input[name=task_name]", "日志测试")
        page.click("button:text('创建任务')")
        page.wait_for_timeout(1000)
        page.click("text=查看任务详情")
        page.wait_for_timeout(500)

        # 检查日志区域标题
        expect(page.get_by_role("heading", name="操作日志")).to_be_visible()

        # 检查日志内容（HTMX 加载）
        page.wait_for_timeout(1000)
        logs_section = page.locator("#logs-section")
        expect(logs_section).to_be_visible()


@pytest.mark.ui
class TestTaskOperations:
    """任务操作测试类"""

    def test_start_task(self, page: Page, test_server):
        """O001: 开始任务"""
        # 创建任务
        page.goto(f"{BASE_URL}/web/tasks/new", wait_until="domcontentloaded")
        page.fill("input[name=task_name]", f"开始测试_{int(page.evaluate('Date.now()'))}")
        page.click("button:text('创建任务')")
        page.wait_for_timeout(1000)
        page.click("text=查看任务详情")
        page.wait_for_timeout(500)

        # 点击开始执行
        start_btn = page.locator("button:text('开始执行')")
        if start_btn.is_visible():
            start_btn.click()
            page.wait_for_timeout(500)

            # 检查状态变为 running
            expect(page.locator("text=running")).to_be_visible()

    def test_complete_task_modal(self, page: Page, test_server):
        """O002/O003: 完成任务"""
        # 创建任务
        page.goto(f"{BASE_URL}/web/tasks/new", wait_until="domcontentloaded")
        page.fill("input[name=task_name]", f"完成测试_{int(page.evaluate('Date.now()'))}")
        page.click("button:text('创建任务')")
        page.wait_for_timeout(1000)
        page.click("text=查看任务详情")
        page.wait_for_timeout(500)

        # 开始任务
        page.click("button:text('开始执行')")
        page.wait_for_timeout(500)

        # 刷新页面以显示新状态和按钮（因为 HTMX start 只更新 action-result）
        page.reload()
        page.wait_for_timeout(500)

        # 确认状态为 running（使用 locator 选择状态徽章）
        status_badge = page.locator("span.bg-blue-100")
        expect(status_badge).to_contain_text("running")

        # 点击标记完成
        page.click("button:text('标记完成')")

        # 等待 modal 显示（hyperscript 需要时间处理）
        modal = page.locator("#modal")
        expect(modal).to_be_visible(timeout=5000)

        # 检查 modal 内容
        modal_content = page.locator("#modal-content")
        expect(modal_content).to_contain_text("标记任务")

        # 输入结果
        page.fill("textarea[name=result]", "执行成功，测试通过")
        page.click("button:text('确认完成')")
        page.wait_for_timeout(500)

        # 刷新页面验证状态
        page.reload()
        page.wait_for_timeout(500)
        # 检查 completed 状态徽章
        status_badge = page.locator("span.bg-green-100")
        expect(status_badge).to_contain_text("completed")

    def test_fail_task_modal(self, page: Page, test_server):
        """O004/O005: 标记失败"""
        # 创建任务
        page.goto(f"{BASE_URL}/web/tasks/new", wait_until="domcontentloaded")
        page.fill("input[name=task_name]", f"失败测试_{int(page.evaluate('Date.now()'))}")
        page.click("button:text('创建任务')")
        page.wait_for_timeout(1000)
        page.click("text=查看任务详情")
        page.wait_for_timeout(500)

        # 开始任务
        page.click("button:text('开始执行')")
        page.wait_for_timeout(500)

        # 刷新页面以显示新状态和按钮
        page.reload()
        page.wait_for_timeout(500)

        # 确认状态为 running（使用 locator 选择状态徽章）
        status_badge = page.locator("span.bg-blue-100")
        expect(status_badge).to_contain_text("running")

        # 点击标记失败
        page.click("button:text('标记失败')")

        # 等待 modal 显示
        modal = page.locator("#modal")
        expect(modal).to_be_visible(timeout=5000)

        # 检查 modal 内容
        modal_content = page.locator("#modal-content")
        expect(modal_content).to_contain_text("标记任务")

        # 输入错误信息
        page.fill("textarea[name=error_message]", "测试模拟失败")
        page.click("button:text('确认失败')")
        page.wait_for_timeout(500)

        # 刷新页面验证状态
        page.reload()
        page.wait_for_timeout(500)
        # 检查 failed 状态徽章
        status_badge = page.locator("span.bg-red-100")
        expect(status_badge).to_contain_text("failed")

    def test_cancel_task(self, page: Page, test_server):
        """O007: 取消任务"""
        # 创建任务
        page.goto(f"{BASE_URL}/web/tasks/new", wait_until="domcontentloaded")
        page.fill("input[name=task_name]", f"取消测试_{int(page.evaluate('Date.now()'))}")
        page.click("button:text('创建任务')")
        page.wait_for_timeout(1000)
        page.click("text=查看任务详情")
        page.wait_for_timeout(500)

        # 点击取消
        page.click("button:text('取消任务')")
        page.wait_for_timeout(500)

        expect(page.locator("text=已取消")).to_be_visible()

    def test_retry_failed_task(self, page: Page, test_server):
        """O006: 重试失败任务"""
        # 创建任务
        page.goto(f"{BASE_URL}/web/tasks/new", wait_until="domcontentloaded")
        page.fill("input[name=task_name]", f"重试测试_{int(page.evaluate('Date.now()'))}")
        page.click("button:text('创建任务')")
        page.wait_for_timeout(1000)
        page.click("text=查看任务详情")
        page.wait_for_timeout(500)

        # 开始任务
        page.click("button:text('开始执行')")
        page.wait_for_timeout(500)

        # 刷新页面以显示新状态和按钮
        page.reload()
        page.wait_for_timeout(500)

        # 确认状态为 running（使用 locator 选择状态徽章）
        status_badge = page.locator("span.bg-blue-100")
        expect(status_badge).to_contain_text("running")

        # 标记失败
        page.click("button:text('标记失败')")

        # 等待 modal 显示
        modal = page.locator("#modal")
        expect(modal).to_be_visible(timeout=5000)

        modal_content = page.locator("#modal-content")
        expect(modal_content).to_contain_text("标记任务")

        page.fill("textarea[name=error_message]", "测试失败")
        page.click("button:text('确认失败')")
        page.wait_for_timeout(500)

        # 刷新页面确认状态为 failed
        page.reload()
        page.wait_for_timeout(500)
        status_badge = page.locator("span.bg-red-100")
        expect(status_badge).to_contain_text("failed")

        # 点击重试
        retry_btn = page.locator("button:text('重试任务')")
        expect(retry_btn).to_be_visible()
        retry_btn.click()
        page.wait_for_timeout(500)

        # 刷新页面验证状态变为 pending
        page.reload()
        page.wait_for_timeout(500)
        status_badge = page.locator("span.bg-yellow-100")
        expect(status_badge).to_contain_text("pending")