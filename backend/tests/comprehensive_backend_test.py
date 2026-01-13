#!/usr/bin/env python3
"""
后端系统综合测试脚本
用于全面验证县域房产平台后端API的健康程度、功能完备性和安全性

执行: python comprehensive_backend_test.py
结果: 控制台输出详细的测试报告
"""

import requests
import json
import time
import random
import concurrent.futures
from datetime import datetime
import traceback

# 测试配置
BASE_URL = "http://localhost:8000"
API_V1_BASE = f"{BASE_URL}/api/v1"

# 测试报告
TEST_REPORT = {
    "summary": {
        "test_start_time": datetime.now().isoformat(),
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "high_severity_bugs": [],
        "medium_severity_bugs": [],
        "low_severity_bugs": []
    },
    "test_details": []
}

# 测试用户数据
TEST_USERS = [
    {"phone": f"138{str(i).zfill(8)}", "password": f"StrongPass{i}", "nickname": f"TestUser{i}"}
    for i in range(100, 105)  # 13810000000 到 13810400000
]

# 印章和状态代码
PASS_STAMP = "[PASS]"
FAIL_STAMP = "[FAIL]"
WARNING_STAMP = "[WARN]"
INFO_STAMP = "[INFO]"

class TestCase:
    """测试用例基类"""
    def __init__(self, name: str, description: str, severity: str = "high"):
        self.name = name
        self.description = description
        self.severity = severity
        self.test_step = []
        self.passed = False
        self.duration = 0.0
        self.error_message = ""

    def execute(self):
        """子类需要重写这个方法"""
        raise NotImplementedError

    def __enter__(self):
        self.start_time = time.time()
        print(f"\n{INFO_STAMP} 开始测试: {self.name}")
        print(f"{INFO_STAMP} 描述: {self.description}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = time.time() - self.start_time
        TEST_REPORT["summary"]["total_tests"] += 1

        if self.passed:
            TEST_REPORT["summary"]["passed"] += 1
            print(f"{PASS_STAMP} 测试通过 ({self.duration:.2f}s)")
        else:
            TEST_REPORT["summary"]["failed"] += 1
            print(f"{FAIL_STAMP} 测试失败 ({self.duration:.2f}s)")
            print(f"{FAIL_STAMP} 错误: {self.error_message}")

            # 记录到报告
            if self.severity == "high":
                TEST_REPORT["summary"]["high_severity_bugs"].append({
                    "test": self.name,
                    "error": self.error_message,
                    "duration": self.duration
                })
            elif self.severity == "medium":
                TEST_REPORT["summary"]["medium_severity_bugs"].append({
                    "test": self.name,
                    "error": self.error_message,
                    "duration": self.duration
                })
            else:
                TEST_REPORT["summary"]["low_severity_bugs"].append({
                    "test": self.name,
                    "error": self.error_message,
                    "duration": self.duration
                })

        # 记录详细的测试结果
        TEST_REPORT["test_details"].append({
            "name": self.name,
            "description": self.description,
            "passed": self.passed,
            "duration": self.duration,
            "error_message": self.error_message,
            "severity": self.severity,
            "test_steps": self.test_step
        })

# === 系统健康检查测试 ===
class SystemHealthCheck(TestCase):
    """系统健康检查"""
    def __init__(self):
        super().__init__("系统健康检查", "验证服务基本可用性")

    def execute(self):
        with self:
            try:
                # 测试健康检查接口
                response = requests.get(f"{BASE_URL}/health", timeout=5)
                self.test_step.append(f"健康检查请求: {response.status_code}")

                if response.status_code == 200:
                    resp_data = response.json()
                    if resp_data.get("status") == "healthy":
                        self.passed = True
                        self.test_step.append("系统状态: 正常")
                    else:
                        self.error_message = "系统状态异常"
                        self.test_step.append(f"系统响应: {resp_data}")
                else:
                    self.error_message = f"健康检查返回错误码: {response.status_code}"

            except Exception as e:
                self.error_message = f"健康检查异常: {str(e)}"
                self.test_step.append(traceback.format_exc())

# === 认证授权测试 ===
class AuthenticationTest(TestCase):
    """认证测试套件"""
    def __init__(self):
        super().__init__("用户认证测试", "验证注册,登录和权限认证流程")
        self.test_user = TEST_USERS[0]
        self.token = None

    def execute(self):
        with self:
            try:
                # 1. 测试注册流程
                register_data = {
                    "phone": self.test_user["phone"],
                    "password": self.test_user["password"],
                    "nickname": self.test_user["nickname"]
                }

                self.test_step.append("开始注册流程")
                response = requests.post(f"{API_V1_BASE}/auth/register", json=register_data, timeout=10)

                if response.status_code in [200, 201]:
                    self.test_step.append("注册成功")
                    register_result = response.json()
                    self.token = register_result.get("access_token")
                elif response.status_code == 400:
                    # 可能是用户已存在，尝试登录
                    self.test_step.append("用户可能已存在，尝试登录")
                    self._test_login()
                else:
                    self.error_message = f"注册失败: {response.status_code} - {response.text}"
                    return

                if self.token:
                    # 测试认证保护API
                    self._test_protected_api()
                    # 测试错误密码
                    self._test_invalid_login()
                    self.passed = True

            except Exception as e:
                self.error_message = f"认证测试异常: {str(e)}"
                self.test_step.append(traceback.format_exc())

    def _test_login(self):
        """内部登录测试"""
        login_data = {
            "phone": self.test_user["phone"],
            "password": self.test_user["password"]
        }

        response = requests.post(f"{API_V1_BASE}/auth/login", json=login_data, timeout=10)

        if response.status_code == 200:
            login_result = response.json()
            self.token = login_result.get("access_token")
            self.test_step.append("登录成功")
        else:
            self.error_message = f"登录失败: {response.status_code}"

    def _test_protected_api(self):
        """测试需要认证的API"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{API_V1_BASE}/users/me", headers=headers, timeout=5)

        if response.status_code == 200:
            user_data = response.json()
            if user_data.get("phone") == self.test_user["phone"]:
                self.test_step.append("认证API访问成功")
            else:
                self.test_step.append(f"警告: 返回用户数据不一致: {user_data}")
        else:
            self.test_step.append(f"认证API失败: {response.status_code}")

    def _test_invalid_login(self):
        """测试错误密码场景"""
        invalid_login = {
            "phone": self.test_user["phone"],
            "password": "wrong_password"
        }

        response = requests.post(f"{API_V1_BASE}/auth/login", json=invalid_login, timeout=5)

        if response.status_code == 401:
            self.test_step.append("错误密码验证成功")
        else:
            self.test_step.append(f"警告: 错误密码应该返回401, 但实际返回: {response.status_code}")

# === 工具功能测试 ===
class ToolsFunctionalityTest(TestCase):
    """工具功能测试"""
    def __init__(self):
        super().__init__("工具功能测试", "验证房贷计算器等工具功能")

    def execute(self):
        with self:
            try:
                # 测试房贷计算器 - 等额本息
                mortgage_data = {
                    "principal": 1000000,  # 100万
                    "annual_rate": 4.9,     # 4.9% 年利率
                    "years": 30,
                    "payment_type": "equal_principal_interest"
                }

                self.test_step.append("测试房贷计算器-等额本息")
                response = requests.post(f"{API_V1_BASE}/tools/mortgage-calculator", json=mortgage_data, timeout=10)

                if response.status_code == 200:
                    result = response.json()
                    expected_monthly = 8000  # 期望月供范围

                    if "monthly_payment" in result and "total_interest" in result:
                        monthly_payment = result["monthly_payment"]
                        if monthly_payment > 0:
                            self.test_step.append(f"计算成功: 月供 {monthly_payment}元")
                        else:
                            self.error_message = "计算结果无效"
                            return
                    else:
                        self.error_message = "返回数据格式不正确"
                        return
                else:
                    self.error_message = f"房贷计算器错误: {response.status_code}"
                    return

                # 测试等额本金
                self.test_step.append("测试房贷计算器-等额本金")
                mortgage_data["payment_type"] = "equal_principal"
                response = requests.post(f"{API_V1_BASE}/tools/mortgage-calculator", json=mortgage_data, timeout=10)

                if response.status_code == 200:
                    self.test_step.append("等额本金计算成功")
                else:
                    self.error_message = f"等额本金计算错误: {response.status_code}"
                    return

                self.passed = True

            except Exception as e:
                self.error_message = f"工具功能测试异常: {str(e)}"
                self.test_step.append(traceback.format_exc())

# === 性能压力测试 ===
class PerformanceTest(TestCase):
    """性能测试"""
    def __init__(self):
        super().__init__("性能压力测试", "验证系统在高并发下的表现")
        self.response_times = []
        self.error_count = 0

    def execute(self):
        with self:
            try:
                # 并发测试房贷计算器
                urls_to_test = [
                    f"{BASE_URL}/health",
                    f"{API_V1_BASE}/tools/mortgage-calculator"
                ]

                self.test_step.append("开始并发测试")

                # 健康检查并发
                self._concurrent_test(f"{BASE_URL}/health", concurrent=5, requests_per_connection=2)

                # 房贷计算器并发
                data = {
                    "principal": 500000,
                    "annual_rate": 4.9,
                    "years": 30,
                    "payment_type": "equal_principal_interest"
                }
                self._concurrent_post_test(f"{API_V1_BASE}/tools/mortgage-calculator", data, concurrent=3, requests=6)

                # 分析结果
                if self.response_times:
                    avg_time = sum(self.response_times) / len(self.response_times)
                    max_time = max(self.response_times)
                    self.test_step.append(f"平均响应时间: {avg_time:.3f}s")
                    self.test_step.append(f"最大响应时间: {max_time:.3f}s")
                    self.test_step.append(f"错误数: {self.error_count}")

                    # 性能阈值判断
                    if avg_time < 0.5 and self.error_count == 0:  # 平均响应时间<500ms 并且无错误
                        self.passed = True
                    else:
                        self.error_message = f"性能测试结果不理想: 平均{avg_time:.2f}s, 错误{self.error_count}"
                else:
                    self.error_message = "未能收集到响应时间数据"

            except Exception as e:
                self.error_message = f"性能测试异常: {str(e)}"
                self.test_step.append(traceback.format_exc())

    def _concurrent_test(self, url, concurrent=5, requests_per_connection=2):
        """并发GET测试"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = []

            for _ in range(concurrent):
                for _ in range(requests_per_connection):
                    future = executor.submit(self._request_with_timing, url, "GET", None)
                    futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                cost_time, status, error = future.result()
                if error:
                    self.error_count += 1
                    self.test_step.append(f"请求失败: {error}")

    def _concurrent_post_test(self, url, data, concurrent=3, requests=6):
        """并发POST测试"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = []

            for i in range(requests):
                future = executor.submit(self._request_with_timing, url, "POST", data)
                futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                cost_time, status, error = future.result()
                if error:
                    self.error_count += 1

    def _request_with_timing(self, url, method, data):
        """带计时的请求"""
        start_time = time.time()
        try:
            if method == "GET":
                response = requests.get(url, timeout=10)
            else:
                response = requests.post(url, json=data, timeout=10)

            cost_time = time.time() - start_time

            if response.status_code == 200:
                self.response_times.append(cost_time)
                return cost_time, response.status_code, None
            else:
                return cost_time, response.status_code, f"HTTP {response.status_code}"

        except Exception as e:
            cost_time = time.time() - start_time
            return cost_time, 0, str(e)

# === 数据库事务完整性测试 ===
class DatabaseIntegrityTest(TestCase):
    """数据库事务完整性测试"""
    def __init__(self):
        super().__init__("数据库完整性测试", "测试用户数据一致性")

    def execute(self):
        with self:
            try:
                # 测试创建用户后数据是否一致
                test_phone = f"199{random.randint(10000000, 99999999)}"
                test_user = {
                    "phone": test_phone,
                    "password": "ValidPass123",
                    "nickname": f"DBTestUser{random.randint(1000, 9999)}"
                }

                self.test_step.append(f"测试用户数据一致性: {test_phone}")

                # 注册新用户
                response = requests.post(f"{API_V1_BASE}/auth/register", json=test_user, timeout=10)

                if response.status_code == 200:
                    register_result = response.json()
                    new_token = register_result.get("access_token")

                    if new_token:
                        # 查询用户详情验证数据一致性
                        headers = {"Authorization": f"Bearer {new_token}"}
                        user_response = requests.get(f"{API_V1_BASE}/users/me", headers=headers, timeout=5)

                        if user_response.status_code == 200:
                            user_data = user_response.json()
                            if user_data.get("phone") == test_phone and user_data.get("nickname") == test_user["nickname"]:
                                self.test_step.append("用户数据一致性验证成功")
                                self.passed = True
                            else:
                                self.error_message = "用户数据不一致"
                                self.test_step.append(f"期望: {test_phone} 实际: {user_data}")
                        else:
                            self.error_message = f"查询用户失败: {user_response.status_code}"
                    else:
                        self.error_message = "注册未返回令牌"
                else:
                    self.error_message = f"注册失败: {response.status_code}"

            except Exception as e:
                self.error_message = f"数据库完整性测试异常: {str(e)}"
                self.test_step.append(traceback.format_exc())

# === 输入验证测试 ===
class InputValidationTest(TestCase):
    """输入验证测试"""
    def __init__(self):
        super().__init__("输入验证测试",  "测试输入过滤和验证机制")

    def execute(self):
        with self:
            try:
                test_cases = [
                    {"data": {"phone": "111", "password": "a"}, "description": "手机号格式错误"},
                    {"data": {"phone": "13800000000", "password": "123"}, "description": "密码太短"},
                    {"data": {"phone": "13888888888", "password": "valid_pass_but_no_nickname"}, "description": "缺少昵称"}
                ]

                valid_count = 0

                login_test = {"phone": "111", "password": "weak"}
                response = requests.post(f"{API_V1_BASE}/auth/login", json=login_test, timeout=5)

                if response.status_code == 422 or response.status_code == 400:
                    self.test_step.append("无效登录请求被正确拒绝")
                    valid_count += 1
                else:
                    self.test_step.append(f"警告: 无效登录未被拒绝 ({response.status_code})")

                # 测试弱密码注册
                weak_pass_data = {
                    "phone": "13500000000",  "password": "1234",
                    "nickname": "weakuser"
                }
                response = requests.post(f"{API_V1_BASE}/auth/register", json=weak_pass_data, timeout=5)

                if response.status_code == 422:
                    self.test_step.append("弱密码被正确拒绝 ✅")
                    valid_count += 1
                else:
                    self.test_step.append(f"严重问题: 弱密码未被拒绝 {response.status_code}")
                    self.error_message = "密码强度验证不足"
                    return

                self.test_step.append(f"输入验证通过测试: {valid_count}/2")

                if valid_count >= 1:  # 通过至少1个测试
                    self.passed = True

            except Exception as e:
                self.error_message = f"输入验证测试异常: {str(e)}"
                self.test_step.append(traceback.format_exc())

# === 主要测试执行器 ===
def run_all_tests():
    """运行所有测试并生成报告"""
    print("="*60)
    print("==> 县域房产平台后端系统综合测试")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试服务器: {BASE_URL}")
    print("")

    # 测试套件
    test_suite = [
        SystemHealthCheck(),         # 系统健康检查
        AuthenticationTest(),        # 认证测试
        ToolsFunctionalityTest(),    # 工具功能测试
        InputValidationTest(),       # 输入验证测试
        DatabaseIntegrityTest(),     # 数据库完整性测试
        PerformanceTest(),           # 性能压力测试
    ]

    # 运行所有测试
    for test in test_suite:
        try:
            test.execute()
        except Exception as e:
            print(f"{FAIL_STAMP} 测试执行异常: {e}")

    # 生成最终测试报告
    generate_final_report()

def generate_final_report():
    """生成最终测试报告"""
    print("\n" + "="*60)
    print("📊 综合测试报告")
    print("="*60)

    summary = TEST_REPORT["summary"]

    # 统计信息
    print(f"总测试用例: {summary['total_tests']}")
    print(f"{PASS_STAMP} 通过: {summary['passed']}")
    print(f"{FAIL_STAMP} 失败: {summary['failed']}")

    total_tests = summary['total_tests'] or 1  # 避免除0
    pass_rate = (summary['passed'] / total_tests) * 100
    print(f"通过率: {pass_rate:.1f}%")

    # 严重级别统计
    high_bugs = len(summary['high_severity_bugs'])
    medium_bugs = len(summary['medium_severity_bugs'])
    low_bugs = len(summary['low_severity_bugs'])

    print(f"\n🐛 Bug 统计:")
    print(f"🔴 高严重性: {high_bugs}")
    print(f"🟡 中严重性: {medium_bugs}")
    print(f"🟢 低严重性: {low_bugs}")

    # 详细错误信息
    if high_bugs > 0:
        print(f"\n🔴 严重Bug详情:")
        for bug in summary['high_severity_bugs']:
            print(f"  - {bug['test']}: {bug['error']}")

    if medium_bugs > 0:
        print(f"\n🟡 中等Bug详情:")
        for bug in summary['medium_severity_bugs']:
            print(f"  - {bug['test']}: {bug['error']}")

    # 建议摘要
    generate_recommendations(high_bugs, medium_bugs, low_bugs)

    # 性能数据摘要
    print_next_steps()

def generate_recommendations(high, medium, low):
    """生成改进建议"""
    print(f"\n" + "="*60)
    print("🎯 质量改进建议")
    print("="*60)

    if high > 0:
        print("🚨 优先修复严重的功能性Bug，特别是影响业务流程的问题")
        print("🔓 检查认证授权逻辑，防止安全漏洞")
        print("💾 验证数据库事务完整性和并发处理")

    if medium > 0:
        print("⚡ 优化API响应时间，确保在500ms以内")
        print("📊 完善输入参数验证和错误消息返回")
        print("🔍 加强异常处理机制")

    if (high + medium) == 0 and low > 0:
        print(f"✅ 系统质量良好，仅有 {low} 个低优先级优化建议")
        print("🎉 当前版本已达到基本可用标准")

    if (high + medium + low) == 0:
        print("🎊 恭喜! 没有发现明显问题")
        print("📈 可以考虑功能扩展和性能深度优化")

def print_next_steps():
    """打印下一步建议"""
    print(f"\n🚀 下一步建议:")
    print("-" * 40)
    print("1. 修复发现的严重Bug")
    print("2. 运行单元测试和质量检查")
    print("3. 部署到测试环境进行业务验证")
    print("4. 制定性能基准和监控指标")
    print("5. 准备生产环境部署方案")

# === 测试脚本入口 ===
if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print(f"\n{WARNING_STAMP} 测试被用户中断")
    except Exception as e:
        print(f"\n{FAIL_STAMP} 测试执行失败: {e}")
        print(traceback.format_exc())

    print(f"\n{INFO_STAMP} 测试报告生成完成")
    print(f"{INFO_STAMP} 如需详情，查看全局变量 TEST_REPORT")