#!/usr/bin/env python3
"""
NOCbRAIN API Test Script
Tests the enhanced /analyze-log endpoint with tenant_id and structured NOC Action Plans
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any
import sys

class NOCbRAINAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_check(self) -> bool:
        """Test the health check endpoint"""
        print("🏥 Testing health check...")
        
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data.get('status')}")
                    return True
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_analyze_log_with_tenant(
        self, 
        tenant_id: str, 
        log_content: str,
        expected_category: str = None
    ) -> Dict[str, Any]:
        """Test the enhanced /analyze-log endpoint with tenant isolation"""
        print(f"🔍 Testing log analysis for tenant: {tenant_id}")
        
        payload = {
            "log_content": log_content,
            "tenant_id": tenant_id,
            "include_global_knowledge": True,
            "category_filter": expected_category
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/analyze-log",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Analysis successful for tenant {tenant_id}")
                    return result
                else:
                    error_text = await response.text()
                    print(f"❌ Analysis failed for tenant {tenant_id}: {response.status}")
                    print(f"   Error: {error_text}")
                    return {"error": error_text, "status_code": response.status}
                    
        except Exception as e:
            print(f"❌ Analysis error for tenant {tenant_id}: {e}")
            return {"error": str(e)}
    
    async def test_tenant_isolation(self) -> bool:
        """Test that different tenants get isolated results"""
        print("🔒 Testing tenant isolation...")
        
        # Test logs for different tenants
        test_logs = {
            "tenant-a": {
                "log": "2024-02-14 10:15:30 ERROR: OSPF neighbor 192.168.1.1 stuck in INIT state",
                "expected_category": "networking"
            },
            "tenant-b": {
                "log": "2024-02-14 10:16:45 ERROR: Pod web-server-123 in CrashLoopBackOff state",
                "expected_category": "orchestration"
            },
            "global": {
                "log": "2024-02-14 10:17:22 ERROR: LVM thin pool pve/data is 95% full",
                "expected_category": "virtualization"
            }
        }
        
        results = {}
        
        for tenant_id, test_data in test_logs.items():
            result = await self.test_analyze_log_with_tenant(
                tenant_id=tenant_id,
                log_content=test_data["log"],
                expected_category=test_data["expected_category"]
            )
            results[tenant_id] = result
        
        # Verify tenant isolation
        isolation_passed = True
        
        for tenant_id, result in results.items():
            if "error" in result:
                print(f"❌ Tenant {tenant_id} analysis failed")
                isolation_passed = False
                continue
            
            # Check if tenant_id is properly included in response
            if "tenant_id" not in result or result["tenant_id"] != tenant_id:
                print(f"❌ Tenant isolation failed for {tenant_id}: wrong tenant_id in response")
                isolation_passed = False
            
            # Check if knowledge sources are properly tagged
            if "knowledge_sources" in result:
                for source in result["knowledge_sources"]:
                    if source.get("tenant_id") not in [tenant_id, "global"]:
                        print(f"❌ Tenant isolation breach: {tenant_id} got data from {source.get('tenant_id')}")
                        isolation_passed = False
        
        if isolation_passed:
            print("✅ Tenant isolation test passed")
        else:
            print("❌ Tenant isolation test failed")
        
        return isolation_passed
    
    async def test_structured_action_plan(self) -> bool:
        """Test that the API returns structured NOC Action Plans"""
        print("📋 Testing structured NOC Action Plan...")
        
        # Critical network log
        critical_log = """
        2024-02-14 10:20:15 CRITICAL: Multiple BGP routes flapping
        2024-02-14 10:20:16 BGP: Neighbor 203.0.113.1 went down
        2024-02-14 10:20:17 BGP: Neighbor 203.0.113.2 went down
        2024-02-14 10:20:18 BGP: Neighbor 203.0.113.3 went down
        """
        
        result = await self.test_analyze_log_with_tenant(
            tenant_id="test-tenant",
            log_content=critical_log,
            expected_category="networking"
        )
        
        if "error" in result:
            print("❌ Structured action plan test failed - analysis error")
            return False
        
        # Check for required fields in action plan
        required_fields = [
            "action_plan",
            "priority",
            "estimated_resolution_time",
            "required_tools",
            "safety_checks",
            "verification_steps"
        ]
        
        action_plan = result.get("action_plan", {})
        missing_fields = [field for field in required_fields if field not in action_plan]
        
        if missing_fields:
            print(f"❌ Structured action plan missing fields: {missing_fields}")
            return False
        
        # Check priority levels
        priority = action_plan.get("priority", "").lower()
        if priority not in ["low", "medium", "high", "critical"]:
            print(f"❌ Invalid priority level: {priority}")
            return False
        
        print("✅ Structured NOC Action Plan test passed")
        print(f"   Priority: {action_plan.get('priority')}")
        print(f"   Estimated time: {action_plan.get('estimated_resolution_time')}")
        print(f"   Required tools: {action_plan.get('required_tools', [])}")
        
        return True
    
    async def test_knowledge_seeding_integration(self) -> bool:
        """Test integration with knowledge seeding"""
        print("🌱 Testing knowledge seeding integration...")
        
        # Test with a log that should match seeded knowledge
        seeded_log = "2024-02-14 10:25:30 ERROR: Interface GigabitEthernet0/1 is down, line protocol is down"
        
        result = await self.test_analyze_log_with_tenant(
            tenant_id="demo-tenant",
            log_content=seeded_log,
            expected_category="networking"
        )
        
        if "error" in result:
            print("❌ Knowledge seeding integration test failed")
            return False
        
        # Check if knowledge sources include seeded content
        knowledge_sources = result.get("knowledge_sources", [])
        cisco_sources = [s for s in knowledge_sources if "cisco" in s.get("source", "").lower()]
        
        if not cisco_sources:
            print("❌ No Cisco knowledge sources found - seeding may not be working")
            return False
        
        print("✅ Knowledge seeding integration test passed")
        print(f"   Found {len(cisco_sources)} Cisco knowledge sources")
        
        return True
    
    async def run_comprehensive_test(self) -> Dict[str, bool]:
        """Run all tests and return results"""
        print("🚀 Starting NOCbRAIN API Comprehensive Test")
        print("=" * 60)
        
        test_results = {}
        
        # Test 1: Health Check
        test_results["health_check"] = await self.test_health_check()
        print()
        
        # Test 2: Tenant Isolation
        test_results["tenant_isolation"] = await self.test_tenant_isolation()
        print()
        
        # Test 3: Structured Action Plan
        test_results["structured_action_plan"] = await self.test_structured_action_plan()
        print()
        
        # Test 4: Knowledge Seeding Integration
        test_results["knowledge_seeding"] = await self.test_knowledge_seeding_integration()
        print()
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:.<30} {status}")
            if result:
                passed_tests += 1
        
        print()
        print(f"Overall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL TESTS PASSED - NOCbRAIN is fully operational!")
        else:
            print("⚠️  Some tests failed - check the logs above")
        
        return test_results

async def main():
    """Main function"""
    # Check if server is running
    tester = NOCbRAINAPITester()
    
    try:
        async with tester:
            results = await tester.run_comprehensive_test()
            
            # Exit with appropriate code
            all_passed = all(results.values())
            sys.exit(0 if all_passed else 1)
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
