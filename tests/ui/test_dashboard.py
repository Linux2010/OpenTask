"""
仪表盘页面测试
"""

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8090"


@pytest.mark.ui
class TestDashboard:
    """仪表盘测试类"""

    def test_dashboard_loads(self, page: Page, test_server):
        """D001: 页面加载"""
        page.goto(f"{BASE_URL}/web/", wait_until="domcontentloaded")

        # 检查标题
        expect(page).to_have_title("仪表盘 - OpenTask")

        # 检查导航栏
        expect(page.locator("nav")).to_be_visible()
        # 使用更精确的选择器避免 strict mode
        expect(page.get_by_role("link", name="OpenTask").first).to_be_visible()

    def test_stats_cards_visible(self, page: Page, test_server):
        """D002: 统计卡片显示"""
        page.goto(f"{BASE_URL}/web/", wait_until="domcontentloaded")

        # 检查四个统计卡片（使用精确匹配避免 strict mode）
        expect(page.get_by_text("待执行", exact=True)).to_be_visible()
        expect(page.get_by_text("执行中", exact=True)).to_be_visible()
        expect(page.get_by_text("已完成", exact=True)).to_be_visible()
        expect(page.get_by_text("失败", exact=True)).to_be_visible()

    def test_quick_action_create_task(self, page: Page, test_server):
        """D003: 快速派任务链接"""
        page.goto(f"{BASE_URL}/web/", wait_until="domcontentloaded")

        # 点击快速派任务按钮
        page.click("text=快速派任务")

        # 等待跳转
        page.wait_for_url(f"{BASE_URL}/web/tasks/new")
        expect(page).to_have_title("快速派任务 - OpenTask")

    def test_view_all_tasks_link(self, page: Page, test_server):
        """D004: 查看所有任务链接"""
        page.goto(f"{BASE_URL}/web/", wait_until="domcontentloaded")

        page.click("text=查看所有任务")
        page.wait_for_url(f"{BASE_URL}/web/tasks")

    def test_recent_tasks_section(self, page: Page, test_server):
        """D005: 最近任务区域"""
        page.goto(f"{BASE_URL}/web/", wait_until="domcontentloaded")

        # 检查最近任务标题
        expect(page.locator("text=最近任务")).to_be_visible()

        # 检查表格或空提示
        table = page.locator("table")
        if table.is_visible():
            # 有任务时显示表格
            expect(table).to_be_visible()
        else:
            # 无任务时显示提示
            expect(page.locator("text=暂无任务")).to_be_visible()