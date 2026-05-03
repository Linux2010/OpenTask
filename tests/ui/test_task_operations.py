"""
任务详情和操作测试
"""

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8090"


@pytest.mark.ui
class TestTaskDetail:
    """任务详情测试类"""

    def test_task_detail_loads(self, page: Page, test_server):
        """T001: 任务详情页面加载"""
        # 先创建一个任务
        page.goto(f"{BASE_URL}/web/tasks/new")
        page.fill("input[name=task_name]", f"详情测试_{int(page.evaluate('Date.now()'))}")
        page.select_option("select[name=assigned_to]", "anna")
        page.click("button:text('创建任务')")
        page.wait_for_timeout(1000)

        # 点击查看详情
        page.click("text=查看任务详情")
        page.wait_for_timeout(500)

        # 检查详情页元素
        expect(page.locator("text=基本信息")).to_be_visible()
        expect(page.locator("text=时间信息")).to_be_visible()
        expect(page.locator("text=执行结果")).to_be_visible()
        expect(page.locator("text=操作")).to_be_visible()

    def test_task_info_display(self, page: Page, test_server):
        """T002: 任务信息显示"""
        page.goto(f"{BASE_URL}/web/tasks/new")
        page.fill("input[name=task_name]", "信息显示测试")
        page.fill("textarea[name=task_description]", "这是测试描述")
        page.fill("input[name=param_key_1]", "key1")
        page.fill("input[name=param_value_1]", "val1")
        page.click("button:text('创建任务')")
        page.wait_for_timeout(1000)
        page.click("text=查看任务详情")
        page.wait_for_timeout(500)

        # 检查各字段
        expect(page.locator("text=信息显示测试")).to_be_visible()
        expect(page.locator("text=anna")).to_be_visible()
        expect(page.locator("text=pending")).to_be_visible()

    def test_task_logs_section(self, page: Page, test_server):
        """T003: 操作日志区域"""
        page.goto(f"{BASE_URL}/web/tasks/new")
        page.fill("input[name=task_name]", "日志测试")
        page.click("button:text('创建任务')")
        page.wait_for_timeout(1000)
        page.click("text=查看任务详情")
        page.wait_for_timeout(500)

        # 检查日志区域
        expect(page.locator("text=操作日志")).to_be_visible()

        # 检查日志内容（HTMX 加载）
        page.wait_for_timeout(1000)
        logs_table = page.locator("table")
        if logs_table.is_visible():
            expect(logs_table.locator("text=动作")).to_be_visible()


@pytest.mark.ui
class TestTaskOperations:
    """任务操作测试类"""

    def test_start_task(self, page: Page, test_server):
        """O001: 开始任务"""
        # 创建任务
        page.goto(f"{BASE_URL}/web/tasks/new")
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
        # 创建并开始任务
        page.goto(f"{BASE_URL}/web/tasks/new")
        page.fill("input[name=task_name]", f"完成测试_{int(page.evaluate('Date.now()'))}")
        page.click("button:text('创建任务')")
        page.wait_for_timeout(1000)
        page.click("text=查看任务详情")
        page.wait_for_timeout(500)

        # 开始任务
        page.click("button:text('开始执行')")
        page.wait_for_timeout(500)

        # 点击标记完成
        page.click("button:text('标记完成')")
        page.wait_for_timeout(300)

        # 检查弹窗
        modal = page.locator("#modal")
        expect(modal).to_be_visible()

        # 输入结果
        page.fill("textarea[name=result]", "执行成功，测试通过")
        page.click("button:text('确认完成')")
        page.wait_for_timeout(500)

        # 检查成功消息
        expect(page.locator("text=已完成")).to_be_visible()

    def test_fail_task_modal(self, page: Page, test_server):
        """O004/O005: 标记失败"""
        # 创建并开始任务
        page.goto(f"{BASE_URL}/web/tasks/new")
        page.fill("input[name=task_name]", f"失败测试_{int(page.evaluate('Date.now()'))}")
        page.click("button:text('创建任务')")
        page.wait_for_timeout(1000)
        page.click("text=查看任务详情")
        page.wait_for_timeout(500)

        # 开始任务
        page.click("button:text('开始执行')")
        page.wait_for_timeout(500)

        # 点击标记失败
        page.click("button:text('标记失败')")
        page.wait_for_timeout(300)

        expect(page.locator("#modal")).to_be_visible()

        # 输入错误信息
        page.fill("textarea[name=error_message]", "测试模拟失败")
        page.click("button:text('确认失败')")
        page.wait_for_timeout(500)

        expect(page.locator("text=已标记失败")).to_be_visible()

    def test_cancel_task(self, page: Page, test_server):
        """O007: 取消任务"""
        # 创建任务
        page.goto(f"{BASE_URL}/web/tasks/new")
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
        # 先找到一个失败的任务
        page.goto(f"{BASE_URL}/web/tasks")
        page.select_option("select[name=status]", "failed")
        page.click("button:text('筛选')")
        page.wait_for_timeout(500)

        rows = page.locator("tbody tr")
        if rows.count() > 0:
            # 进入详情
            rows.first.click("text=详情")
            page.wait_for_timeout(500)

            # 点击重试
            retry_btn = page.locator("button:text('重试任务')")
            if retry_btn.is_visible():
                retry_btn.click()
                page.wait_for_timeout(500)

                expect(page.locator("text=已重新排队")).to_be_visible()