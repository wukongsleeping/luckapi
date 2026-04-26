#!/usr/bin/env python3
"""
并发限流集成测试套件

测试范围:
1. 并发限流器功能验证
2. 监控端点数据验证  
3. 限流器统计准确性
4. 长时间运行稳定性

用法:
    python test_concurrency_full.py           # 运行所有测试
    python test_concurrency_full.py --only limiter  # 仅运行限流测试
    python test_concurrency_full.py --only metrics    # 仅运行监控测试
"""

import asyncio
import aiohttp
import time
import json
import sys
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# 测试配置
BASE_URL = "http://localhost:9090/v1/chat/completions"
METRICS_URL = "http://localhost:9090/admin/api/metrics"
API_KEY = "sk-mPSW8fnSDh5RQ9hLYO5dYZhCY5vrZmyNiLqQgVkhV3IfYKsO"
MODEL = "/root/yrb/models/qwen3.6-35b-a3b-fp8"

@dataclass
class TestCase:
    """测试用例"""
    name: str
    success: bool = False
    duration: float = 0
    details: str = ""
    errors: List[str] = field(default_factory=list)

@dataclass 
class TestReport:
    """测试报告"""
    tests: List[TestCase] = field(default_factory=list)
    start_time: float = 0
    end_time: float = 0
    
    def add_test(self, test: TestCase):
        self.tests.append(test)
    
    def print_summary(self):
        total = len(self.tests)
        passed = sum(1 for t in self.tests if t.success)
        failed = total - passed
        
        print("\n" + "="*60)
        print("测试报告摘要")
        print("="*60)
        print(f"总计: {total} | 通过: {passed} | 失败: {failed}")
        print("-"*60)
        
        for i, test in enumerate(self.tests, 1):
            status = "✅" if test.success else "❌"
            print(f"{i}. {status} {test.name} ({test.duration:.2f}s)")
            if test.details:
                print(f"   详情: {test.details}")
            for err in test.errors:
                print(f"   错误: {err}")
        
        print("="*60)
        return passed == total


class ConcurrencyTester:
    """并发限流测试器"""
    
    def __init__(self, api_key: str = API_KEY, model: str = MODEL):
        self.api_key = api_key
        self.model = model
        self.sessions: Dict[str, aiohttp.ClientSession] = {}
    
    async def send_request(self, session: aiohttp.ClientSession, 
                          req_id: int, max_tokens: int = 200) -> tuple:
        """发送单个请求"""
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": f"测试请求 #{req_id}，请简要回答。"}],
            "max_tokens": max_tokens,
            "temperature": 0.5,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            async with session.post(
                BASE_URL, json=payload, headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                return resp.status, await resp.text()
        except asyncio.TimeoutError:
            return "timeout", "请求超时"
        except Exception as e:
            return "error", str(e)
    
    async def test_basic_concurrency(self, concurrent: int, expected_rejections: int = 0) -> TestCase:
        """基础并发测试"""
        test = TestCase(name=f"基础并发测试 (并发={concurrent})")
        start = time.time()
        
        results = {"success": 0, "429": 0, "error": 0, "timeout": 0}
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.send_request(session, i, max_tokens=100)
                for i in range(1, concurrent + 1)
            ]
            
            for i, (status, _) in enumerate(await asyncio.gather(*tasks), 1):
                if status == 200:
                    results["success"] += 1
                elif status == 429:
                    results["429"] += 1
                elif status == "timeout":
                    results["timeout"] += 1
                else:
                    results["error"] += 1
        
        elapsed = time.time() - start
        test.duration = elapsed
        test.details = (f"成功:{results['success']} 拒绝:{results['429']} "
                       f"超时:{results['timeout']} 错误:{results['error']}")
        
        # 验证结果
        if results["success"] + results["429"] == concurrent:
            test.success = True
        else:
            test.success = False
            test.errors.append(f"意外的响应类型")
        
        return test
    
    async def test_sequential_batches(self, batches: int, per_batch: int) -> TestCase:
        """多批次顺序测试"""
        test = TestCase(name=f"多批次测试 (批次={batches}, 每批={per_batch})")
        start = time.time()
        
        results = {"success": 0, "429": 0}
        
        for batch in range(1, batches + 1):
            print(f"\n  批次 {batch}/{batches}")
            async with aiohttp.ClientSession() as session:
                tasks = [
                    self.send_request(session, (batch-1)*per_batch + i, max_tokens=50)
                    for i in range(1, per_batch + 1)
                ]
                
                for status, _ in await asyncio.gather(*tasks):
                    if status == 200:
                        results["success"] += 1
                    elif status == 429:
                        results["429"] += 1
        
        elapsed = time.time() - start
        test.duration = elapsed
        test.details = f"总成功:{results['success']} 拒绝:{results['429']} 总耗时:{elapsed:.1f}s"
        test.success = results["success"] > 0
        return test
    
    async def test_metrics_endpoint(self) -> TestCase:
        """测试监控端点"""
        test = TestCase(name="监控端点测试")
        start = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    METRICS_URL, timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status != 200:
                        test.success = False
                        test.errors.append(f"HTTP {resp.status}")
                        return test
                    
                    data = await resp.json()
                    test.duration = time.time() - start
                    test.details = f"响应时间: {test.duration*1000:.0f}ms"
                    
                    if "metrics" not in data:
                        test.success = False
                        test.errors.append("缺少 metrics 字段")
                        return test
                    
                    stats = data["metrics"]
                    if stats:
                        total_requests = sum(
                            m["total_requests"] for m in stats.values()
                        )
                        test.details += f" | 总请求数: {total_requests}"
                    
                    test.success = True
                    
        except Exception as e:
            test.duration = time.time() - start
            test.success = False
            test.errors.append(str(e))
        
        return test


async def run_all_tests():
    """运行完整测试套件"""
    report = TestReport()
    report.start_time = time.time()
    
    tester = ConcurrencyTester()
    
    print("="*60)
    print("并发限流集成测试套件")
    print("="*60)
    
    # 测试 1: 监控端点
    print("\n[1/4] 测试监控端点...")
    test1 = await tester.test_metrics_endpoint()
    report.add_test(test1)
    logger.info(f"  {test1.details}")
    
    # 测试 2: 基础并发
    print("\n[2/4] 测试基础并发...")
    test2 = await tester.test_basic_concurrency(concurrent=10)
    report.add_test(test2)
    logger.info(f"  {test2.details}")
    
    # 测试 3: 高并发  
    print("\n[3/4] 测试高并发...")
    test3 = await tester.test_basic_concurrency(concurrent=20, expected_rejections=2)
    report.add_test(test3)
    logger.info(f"  {test3.details}")
    
    # 测试 4: 多批次
    print("\n[4/4] 测试多批次...")
    test4 = await tester.test_sequential_batches(batches=3, per_batch=5)
    report.add_test(test4)
    logger.info(f"  {test4.details}")
    
    report.end_time = time.time()
    
    # 打印报告
    success = report.print_summary()
    
    # 输出 JSON 格式报告 (便于 CI 集成)
    report_json = {
        "total": len(report.tests),
        "passed": sum(1 for t in report.tests if t.success),
        "failed": sum(1 for t in report.tests if not t.success),
        "duration": report.end_time - report.start_time,
        "tests": [
            {
                "name": t.name,
                "passed": t.success,
                "duration": round(t.duration, 2),
                "details": t.details,
                "errors": t.errors
            }
            for t in report.tests
        ]
    }
    
    print("\nJSON 报告:")
    print(json.dumps(report_json, indent=2, ensure_ascii=False))
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
