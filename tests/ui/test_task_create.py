"""
创建任务测试
"""

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8090"


@pytest.mark.ui
class TestTaskCreate:
    """创建任务测试类"""

    def test_create_form_loads(self, page: Page, test_server):
        """C001: 表单页面加载"""
        page.goto(f"{BASE_URL}/web/tasks/new")
        expect(page).to_have_title("快速派任务 - OpenTask")

        # 检查表单字段
        expect(page.locator("input[name=task_name]")).to_be_visible()
        expect(page.locator("select[name=assigned_to]")).to_be_visible()
        expect(page.locator("select[name=priority]")).to_be_visible()

    def test_create_task_basic(self, page: Page, test_server):
        """C002: 创建基础任务"""
        page.goto(f"{BASE_URL}/web/tasks/new")

        # 填写表单
        page.fill("input[name=task_name]", f"Playwright测试任务_{int(page.evaluate('Date.now()'))}")
        page.select_option("select[name=assigned_to]", "anna")
        page.select_option("select[name=priority]", "P1")

        # 提交
        page.click("button:text('创建任务')")

        # 等待 HTMX 响应
        page.wait_for_timeout(1000)

        # 检查成功消息
        expect(page.locator("text=操作成功")).to_be_visible()
        expect(page.locator("text=已创建")).to_be_visible()

    def test_create_task_with_params(self, page: Page, test_server):
        """C003: 创建带参数的任务"""
        page.goto(f"{BASE_URL}/web/tasks/new")

        # 填写基本信息
        page.fill("input[name=task_name]", f"带参数测试任务_{int(page.evaluate('Date.now()'))}")
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

    def test_required_field_validation(self, page: Page, test_server):
        """C004: 必填字段校验"""
        page.goto(f"{BASE_URL}/web/tasks/new")

        # 不填名称直接提交
        page.click("button:text('创建任务')")

        # 浏览器原生校验会阻止提交，检查 input 的 required 属性
        task_name_input = page.locator("input[name=task_name]")
        expect(task_name_input).to_have_attribute("required", "")

    def test_default_values(self, page: Page, test_server):
        """C005: 默认值验证"""
        page.goto(f"{BASE_URL}/web/tasks/new")

        # 检查默认选择
        priority_select = page.locator("select[name=priority]")
        expect(priority_select).to_have_value("P2")

        assigned_select = page.locator("select[name=assigned_to]")
        expect(assigned_select).to_have_value("anna")

    def test_param_fields_visible(self, page: Page, test_server):
        """C006: 参数字段显示"""
        page.goto(f"{BASE_URL}/web/tasks/new")

        # 检查任务参数区域
        expect(page.locator("text=任务参数")).to_be_visible()

        # 检查三个参数组
        expect(page.locator("input[name=param_key_1]")).to_be_visible()
        expect(page.locator("input[name=param_value_1]")).to_be_visible()
        expect(page.locator("input[name=param_key_2]")).to_be_visible()
        expect(page.locator("input[name=param_value_2]")).to_be_visible()
        expect(page.locator("input[name=param_key_3]")).to_be_visible()
        expect(page.locator("input[name=param_value_3]")).to_be_visible()

    def test_back_to_list_link(self, page: Page, test_server):
        """C007: 返回列表链接"""
        page.goto(f"{BASE_URL}/web/tasks/new")

        page.click("text=返回任务列表")
        page.wait_for_url(f"{BASE_URL}/web/tasks")

    def test_view_task_after_create(self, page: Page, test_server):
        """C008: 创建后查看详情"""
        page.goto(f"{BASE_URL}/web/tasks/new")

        page.fill("input[name=task_name]", f"测试查看详情_{int(page.evaluate('Date.now()'))}")
        page.select_option("select[name=assigned_to]", "cc")
        page.click("button:text('创建任务')")
        page.wait_for_timeout(1000)

        # 点击查看详情链接
        page.click("text=查看任务详情")
        page.wait_for_timeout(500)

        # 检查任务详情页
        expect(page).to_have_title(regex=r"任务 #\d+ - OpenTask")