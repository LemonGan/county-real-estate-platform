#!/usr/bin/env python3
"""
Backend System ASCII Test Report
县域房产平台后端API完整检测报告 - ASCII版本编码兼容
"""

import requests
import json
import time
import random
import datetime

# 基础配置
BASE_URL = "http://localhost:8000"
API_V1_BASE = f"{BASE_URL}/api/v1"

# 记录测试数据
test_results = {
    "total_tests": 0,
    "passed": 0,
    "failed": 0,
    "high_severity_bugs": [],
    "medium_severity_bugs": [],
    "low_severity_bugs": [],
    "test_detail": []
}

# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def log_test(name, status, duration=0.0, error="", severity="high"):
    """记录测试结果 - Static ASCII version"""
    test_results["total_tests"] += 1
    test_results["test_detail"].append({
        "test_name": name,
        "status": status,
        "duration": duration,
        "error": error,
        "severity": severity
    })

    if status == "PASS":
        test_results["passed"] += 1
        print(f"[O] {name} OK ({duration:.2f}s)")
    else:
        test_results["failed"] += 1
        print(f"[X] {name} FAILED: {error} ({duration:.2f}s)")

        # 分类Bug严重程度
        if severity == "high":
            test_results["high_severity_bugs"].append({"name": name, "error": error})
        elif severity == "medium":
            test_results["medium_severity_bugs"].append({"name": name, "error": error})
        else:
            test_results["low_severity_bugs"].append({"name": name, "error": error})

# === 系统健康检查测试 ===
def test_system_health():
    """系统健康检查 - 高优先级"""
    name = "系统健康检查"
    print(f"\n[=== {name} ===]")
    start = time.time()

    try:
        print("测试健康检查接口...")
        resp = requests.get(f"{BASE_URL}/health", timeout=5)

        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "healthy":
                log_test(name, "PASS", time.time() - start)
            else:
                log_test(name, "FAIL", time.time() - start, f"系统状态异常: {data}")
        else:
            log_test(name, "FAIL", time.time() - start, f"返回码异常: {resp.status_code}")

    except Exception as e:
        log_test(name, "FAIL", time.time() - start, f"请求异常: {e}")

# === 认证测试 ===
def test_authentication():
    """用户注册与登录完整流程测试"""
    name = "用户认证流程测试"
    print(f"\n[=== {name} ===]")
    start = time.time()

    test_phone = f"13810000{random.randint(100, 999)}"
    test_pass = "ValidPass123456"
    test_nick = f"TestUser{random.randint(1000, 9999)}"

    token = None  # 初始化局部token变量

    try:
        # 1. 注册测试
        register_data = {"phone": test_phone, "password": test_pass, "nickname": test_nick}
        print(f"1. 注册用户: {test_phone}")
        reg_resp = requests.post(f"{API_V1_BASE}/auth/register", json=register_data, timeout=10)

        if reg_resp.status_code in [200, 201]:
            print("   - 注册成功")
            reg_result = reg_resp.json()
            token = reg_result.get("access_token")
            if not token:
                log_test("用户注册", "FAIL", 0, "未返回访问令牌")
                log_test(name, "FAIL", time.time() - start, "注册过程异常")
                return
        else:
            log_test("用户注册", "FAIL", time.time() - start, f"注册失败: {reg_resp.status_code}")
            log_test(name, "FAIL", time.time() - start, "注册未成功")
            return

        # 2. 登录测试 - 验证登录
        print(f"2. 验证登录用户: {test_phone}")
        login_data = {"phone": test_phone, "password": test_pass}
        login_resp = requests.post(f"{API_V1_BASE}/auth/login", json=login_data, timeout=5)

        if login_resp.status_code == 200:
            login_result = login_resp.json()
            token = login_result.get("access_token")
            if token:
                print("   - 登录成功")
            else:
                log_test("用户登录", "FAIL", time.time() - start, "登录未返回令牌")
                return
        else:
            log_test("用户登录", "FAIL", time.time() - start, f"登录失败: {login_resp.status_code}")
            return

        # 3. 访问认证接口 - 验证令牌
        print("3. 验证认证API访问")
        me_resp = requests.get(f"{API_V1_BASE}/users/me", headers={"Authorization": f"Bearer {token}"}, timeout=5)

        if me_resp.status_code == 200:
            user_data = me_resp.json()
            if user_data.get("phone") == test_phone:
                print("   - 令牌和用户信息验证通过")
                log_test(name, "PASS", time.time() - start)
            else:
                print("   - 用户信息不一致")
                log_test(name, "FAIL", time.time() - start, "返回用户信息不匹配")
        else:
            log_test("用户认证API", "FAIL", time.time() - start, f"认证API失败: {me_resp.status_code}")

    except requests.exceptions.ReadTimeout:
        log_test(name, "FAIL", time.time() - start, "请求超时")
    except Exception as e:
        log_test(name, "FAIL", time.time() - start, f"异常: {e}")

# === 工具功能测试 ===
def test_tools_functionality():
    """房贷计算器等工具功能测试"""
    name = "工具功能测试"
    print(f"\n[=== {name} ===]")
    start = time.time()

    test_cases = [
        {
            "name": "等额本息计算器",
            "data": {"principal": 1000000, "annual_rate": 5.0, "years": 30, "payment_type": "equal_principal_interest"}
        },
        {
            "name": "等额本金计算器",
            "data": {"principal": 800000, "annual_rate": 4.5, "years": 20, "payment_type": "equal_principal"}
        }
    ]

    passed = 0
    total_tools = len(test_cases)

    try:
        for i, test in enumerate(test_cases):
            print(f"{i+1}. 测试 {test['name']}...")
            resp = requests.post(f"{API_V1_BASE}/tools/mortgage-calculator", json=test['data'], timeout=5)

            if resp.status_code == 200:
                result = resp.json()
                monthly = result.get('monthly_payment', 0)
                if monthly > 0:
                    print(f"   计算结果: 月供 {monthly:.2f}元")
                    passed += 1
                else:
                    print(f"   警告: 计算结果异常")
            else:
                print(f"   错误: HTTP {resp.status_code}")

        # 总结
        if passed == total_tools:
            log_test(name, "PASS", time.time() - start, f"工具全部通过 ({passed}/{total_tools})")
        else:
            log_test(name, "FAIL", time.time() - start, f"部分工具失败 ({passed}/{total_tools})")

    except requests.exceptions.Timeout:
        log_test(name, "FAIL", time.time() - start, "工具请求超时")
    except Exception as e:
        log_test(name, "FAIL", time.time() - start, f"工具测试异常: {e}")

# === 安全与输入验证测试 ===
def test_security_and_input_validation():
    """安全检测与输入验证"""
    name = "安全与输入验证测试"
    print(f"\n[=== {name} ===]")
    start = time.time()

    fail_count = 0

    print("1. 测试弱密码拒绝...")
    weak_password = {"phone": "13500000000", "password": "1234"}
    resp = requests.post(f"{API_V1_BASE}/auth/register", json=weak_password, timeout=5)

    if resp.status_code == 422:
        print("   弱密码被正确拒绝")
    else:
        print("   错误: 弱密码未被拒绝")
        fail_count += 1

    print("2. 测试无认证访问受保护API...")
    resp = requests.get(f"{API_V1_BASE}/users/me", timeout=5)

    if resp.status_code == 401:
        print("   无认证访问正确被拒绝")
    else:
        print(f"   错误: 应该返回401但实际返回 {resp.status_code}")
        fail_count += 1

    print("3. 测试无效手机号格式...")
    invalid_phone = {"phone": "111", "password": "ValidPass123456"}
    resp = requests.post(f"{API_V1_BASE}/auth/login", json=invalid_phone, timeout=5)

    if resp.status_code == 422:
        print("   无效手机号被正确拒绝")
    else:
        print(f"   错误: 应该拒绝 {resp.status_code}")
        fail_count += 1

    if fail_count == 0:
        log_test(name, "PASS", time.time() - start)
    else:
        log_test(name, "FAIL", time.time() - start, f"发现 {fail_count} 个安全漏洞")

# === 数据库完整性和一致性测试 ===
def test_database_integrity():
    """数据库完整性和数据一致性"""
    name = "数据库完整性测试"
    print(f"\n[=== {name} ===]")
    start = time.time()

    try:
        # 创建新用户验证数据一致性
        new_phone = f"138{random.randint(20000, 99999)}000"
        test_user = {
            "phone": new_phone,
            "password": "TestDBPass123",
            "nickname": "DBTestUser"
        }

        print(f"1. 创建数据库测试用户: {new_phone}")
        reg_resp = requests.post(f"{API_V1_BASE}/auth/register", json=test_user, timeout=8)

        if reg_resp.status_code in [200, 201]:
            result = reg_resp.json()
            access_token = result.get("access_token")

            if access_token:
                print("2. 验证注册后立即查询的用户数据一致性")
                me_resp = requests.get(f"{API_V1_BASE}/users/me",
                                     headers={"Authorization": f"Bearer {access_token}"}, timeout=5)

                if me_resp.status_code == 200:
                    user_data = me_resp.json()
                    if user_data.get("phone") == new_phone and user_data.get("nickname") == test_user["nickname"]:
                        print(f"   - 数据验证成功: {user_data.get('id')} {user_data.get('phone')}")
                        log_test(name, "PASS", time.time() - start, "用户数据一致性验证通过")
                    else:
                        log_test(name, "FAIL", time.time() - start, f"数据不一致: {user_data}")
                else:
                    log_test(name, "FAIL", time.time() - start, f"用户详情查询失败: {me_resp.status_code}")
            else:
                log_test(name, "FAIL", time.time() - start, "注册后未返回访问令牌")
        else:
            log_test(name, "FAIL", time.time() - start, f"数据库测试用户注册失败: {reg_resp.status_code}")

    except requests.exceptions.ReadTimeout:
        log_test(name, "FAIL", time.time() - start, "数据库操作超时")
    except Exception as e:
        log_test(name, "FAIL", time.time() - start, f"数据一致性测试异常: {e}")

# === 性能压力测试 ===
def test_performance_and_stress():
    """性能基准和压力测试"""
    name = "性能压力测试"
    print(f"\n[=== {name} ===]")
    start = time.time()

    response_times = []
    errors = 0
    test_count = 10

    print(f"正在执行 {test_count} 次并发请求...")

    for i in range(test_count):
        start_i = time.time()
        try:
            resp = requests.post(f"{API_V1_BASE}/tools/mortgage-calculator",
                              json={"principal": 1000000, "annual_rate": 5, "years": 30,
                                    "payment_type": "equal_principal_interest"}, timeout=15)
            if resp.status_code == 200:
                response_times.append(time.time() - start_i)
            else:
                errors += 1
        except:
            errors += 1

        if i % 2 == 0:  # 简单的并发模拟
            time.sleep(0.01)

    # 分析结果
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)

        print(f"   成功请求: {len(response_times)}")
        print(f"   错误次数: {errors}")
        print(f"   平均响应: {avg_time:.3f}s")
        print(f"   最大响应: {max_time:.3f}s")

        # 性能等级判断
        if avg_time < 0.5 and errors == 0:
            grade = "优秀" if avg_time < 0.3 else "良好"
            log_test(name, "PASS", time.time() - start, f"性能{rade} - 平均{avg_time:.3f}s, 无错误")
        elif avg_time < 0.8 and errors <= 2:
            log_test(name, "PASS", time.time() - start, f"性能可接受 - 平均{avg_time:.3f}s, 错误{errors}次", "medium")
        else:
            log_test(name, "FAIL", time.time() - start, f"性能不达标 - 平均{avg_time:.3f}s, 错误{errors}次")
    else:
        log_test(name, "FAIL", time.time() - start, "未获取到有效响应时间")

# === 运行所有测试并生成报告 ===
def run_comprehensive_testing():
    """运行完整测试套件"""
    start_time = datetime.datetime.now()
    print(f"\n{'='*60}")
    print(f"=\u003e 县域房产平台后端综合检测报告")
    print(f"{'='*60}")
    print(f"检测时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标服务: {BASE_URL}")
    print(f"检测类型: API健康检测 | 功能验证 | 安全性 | 性能基准")

    # 1. 基础系统
    test_system_health()

    # 2. 身份认证
    test_authentication()

    # 3. 工具功能
    test_tools_functionality()

    # 4. 安全性检查
    test_security_and_input_validation()

    # 5. 数据一致性
    test_database_integrity()

    # 6. 性能基准
    test_performance_and_stress()

    # 生成最终报告
    generate_final_ascii_report(start_time)

def generate_final_ascii_report(start_time):
    """生成ASCII版本的测试报告"""
    total_duration = (datetime.datetime.now() - start_time).total_seconds()

    print(f"\n{'='*70}")
    print("                   综合检测报告汇总")
    print(f"{'='*70}")

    total = test_results["total_tests"]
    passed = test_results["passed"]
    failed = test_results["failed"]

    print(f"检测用例总数: {total}")
    print(f"[O] 通过: {passed}")
    print(f"[X] 失败: {failed}")
    if total > 0:
        print(f"通过率: {(passed/total)*100:.1f}%")
    else:
        print("通过率: N/A (无测试)")

    print(f"总耗时: {total_duration:.2f}秒")

    # BUG统计
    high_bugs = len(test_results["high_severity_bugs"])
    medium_bugs = len(test_results["medium_severity_bugs"])
    low_bugs = len(test_results["low_severity_bugs"])

    print(f"\n质量问题统计:")
    print(f"[*] 关键问题(High): {high_bugs}")
    print(f"[*] 中等问题(Medium): {medium_bugs}")
    print(f"[*] 一般问题(Low): {low_bugs}")

    # 详细错误列表
    if high_bugs > 0:
        print(f"\n关键问题详情:")
        for bug in test_results["high_severity_bugs"]:
            print(f"   - {bug['name']}: {bug['error']}")

    if medium_bugs > 0:
        print(f"\n中等问题详情:")
        for bug in test_results["medium_severity_bugs"]:
            print(f"   - {bug['name']}: {bug['error']}")

    # 评分和建议
    calc_quality_score(high_bugs, medium_bugs, low_bugs, passed, total, total_duration)

def calc_quality_score(high, medium, low, passed, total, duration):
    """计算质量评分并给出建议"""
    print(f"\n{'-'*70}")
    print("                      质量评估与建议")
    print(f"{'-'*70}")

    if total == 0:
        score = 0
        grade = "无法评估"
    else:
        # 评分算法：通过率权重 + BUG负权重 + 性能贡献
        pass_rate = passed / total
        bug_penalty = (high * 0.5 + medium * 0.3 + low * 0.1) * 0.1
        perf_bonus = 1.0 if duration < 60 else 0.8

        score = max(0, min(100, (pass_rate * 100 - bug_penalty * 100) * perf_bonus))

        if score >= 85: grade = "A级 - 优秀"
        elif score >= 70: grade = "B级 - 良好"
        elif score >= 55: grade = "C级 - 可接受"
        elif score >= 40: grade = "D级 - 需要改进"
        else: grade = "F级 - 不宜生产部署"

    print(f"整体质量评分: {score:.1f}/100 ({grade})")

    # 建议摘要
    print(f"\n改进建议:")
    if high > 0:
        print("  1) [!] 高优先级修复严重Bug - 影响核心功能")
        print("  2) [\u003e] 验证数据一致性和安全认证")
    if medium > 0:
        print("  3) [~] 中优先级优化API性能和用户输入验证")
    if high == 0 and medium == 0:
        print("  1) [+++] 系统质量良好，仅少量低优先级建议")
        print("  2) [\u003e] 考虑性能监控和用户体验优化")

    print("\n下一步行动计划:")
    print("  a) 修复发现的高级别问题")
    print("  b) 执行单元测试和代码审查")
    print("  c) 进行集成测试和业务验证")
    print("  d) 准备预生产环境和上线检查")

# 主函数
if __name__ == "__main__":
    print(f"\n BEGIN: {datetime.datetime.now().strftime('%H:%M:%S')}")
    try:
        run_comprehensive_testing()
    except KeyboardInterrupt:
        print("\n[>>] 测试被用户中断")
    except Exception as e:
        print(f"\n[XX] 测试执行失败: {str(e)}")
        import traceback
        traceback.print_exc()

    print(f"\n END: {datetime.datetime.now().strftime('%H:%M:%S')}")
    print("=== 测试报告已生成 ===")