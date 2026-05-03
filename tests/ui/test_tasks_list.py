"""
任务列表页面测试
"""

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8090"


@pytest.mark.ui
class TestTasksList:
    """任务列表测试类"""

    def test_tasks_list_loads(self, page: Page, test_server):
        """L001: 页面加载"""
        page.goto(f"{BASE_URL}/web/tasks")
        expect(page).to_have_title("任务列表 - OpenTask")

        # 检查筛选区域
        expect(page.locator("text=筛选条件")).to_be_visible()

    def test_filter_by_bot(self, page: Page, test_server):
        """L002: 按 Bot 筛选"""
        page.goto(f"{BASE_URL}/web/tasks")

        # 选择 anna
        page.select_option("select[name=assigned_to]", "anna")

        # 点击筛选按钮
        page.click("button:text('筛选')")

        # 等待 HTMX 加载
        page.wait_for_timeout(500)

        # 检查结果显示 anna
        rows = page.locator("tbody tr")
        count = rows.count()
        if count > 0:
            for i in range(count):
                expect(rows.nth(i).locator("td:nth-child(4)")).to_contain_text("anna")

    def test_filter_by_status(self, page: Page, test_server):
        """L003: 按状态筛选"""
        page.goto(f"{BASE_URL}/web/tasks")

        page.select_option("select[name=status]", "pending")
        page.click("button:text('筛选')")
        page.wait_for_timeout(500)

        rows = page.locator("tbody tr")
        if rows.count() > 0:
            expect(rows.first.locator("text=pending")).to_be_visible()

    def test_filter_by_priority(self, page: Page, test_server):
        """L004: 按优先级筛选"""
        page.goto(f"{BASE_URL}/web/tasks")

        page.select_option("select[name=priority]", "P0")
        page.click("button:text('筛选')")
        page.wait_for_timeout(500)

        rows = page.locator("tbody tr")
        if rows.count() > 0:
            expect(rows.first.locator("text=P0")).to_be_visible()

    def test_clear_filter(self, page: Page, test_server):
        """L005: 清除筛选"""
        page.goto(f"{BASE_URL}/web/tasks")

        # 先设置筛选
        page.select_option("select[name=assigned_to]", "anna")
        page.click("button:text('筛选')")
        page.wait_for_timeout(500)

        # 点击清除
        page.click("a:text('清除')")

        # 等待页面刷新
        page.wait_for_url(f"{BASE_URL}/web/tasks")

    def test_create_task_button(self, page: Page, test_server):
        """L006: 任务列表页的快速派任务按钮"""
        page.goto(f"{BASE_URL}/web/tasks")

        page.click("text=快速派任务")
        page.wait_for_url(f"{BASE_URL}/web/tasks/new")

    def test_task_table_headers(self, page: Page, test_server):
        """L007: 任务表格列头"""
        page.goto(f"{BASE_URL}/web/tasks")

        # 检查列头
        expect(page.locator("text=ID")).to_be_visible()
        expect(page.locator("text=任务名称")).to_be_visible()
        expect(page.locator("text=分配给")).to_be_visible()
        expect(page.locator("text=状态")).to_be_visible()

    def test_task_count_display(self, page: Page, test_server):
        """L008: 任务数量显示"""
        page.goto(f"{BASE_URL}/web/tasks")

        # 检查任务数量提示
        expect(page.locator("text=共")).to_be_visible()