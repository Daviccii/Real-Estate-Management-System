import urllib.request
import json
import urllib.parse
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

BASE_URL = "http://localhost:8000"

def request(path, method="GET", data=None, headers=None):
    url = f"{BASE_URL}{path}"
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    
    encoded_data = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=encoded_data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return e.code, json.loads(body) if body else str(e)
    except Exception as e:
        return 500, str(e)

def run_tests():
    print("==================================================")
    print("  RUNNING COMPREHENSIVE END-TO-END VERIFICATION  ")
    print("==================================================")
    results = {}

    # 1. PROPERTY BROWSING & SEARCH
    print("\n--- 1. Testing Property Browsing & Search ---")
    
    # 1.1 List all public properties
    status, data = request("/api/properties/public")
    assert status == 200 and len(data) > 0, f"Public properties list failed: {status}"
    print(f"[PASS] GET /api/properties/public -> 200 OK ({len(data)} properties loaded)")
    results["list_properties"] = "PASS"

    # 1.2 Search Kilimani
    status, data = request("/api/properties/public?search=Kilimani")
    assert status == 200 and len(data) > 0, f"Search Kilimani failed: {status}"
    assert all("Kilimani" in (p.get("name", "") + p.get("city", "") + p.get("address", "") + p.get("description", "")) for p in data)
    print(f"[PASS] GET /api/properties/public?search=Kilimani -> 200 OK ({len(data)} properties matched)")
    results["search_kilimani"] = "PASS"

    # 1.3 Filter by Purpose (Buy)
    status, data = request("/api/properties/public?purpose=buy")
    assert status == 200 and len(data) > 0, f"Filter by Buy failed: {status}"
    assert all(p["purpose"] == "buy" for p in data)
    print(f"[PASS] GET /api/properties/public?purpose=buy -> 200 OK ({len(data)} properties matched)")
    results["filter_buy"] = "PASS"

    # 1.4 Filter by Purpose (Rent)
    status, data = request("/api/properties/public?purpose=rent")
    assert status == 200 and len(data) > 0, f"Filter by Rent failed: {status}"
    assert all(p["purpose"] == "rent" for p in data)
    print(f"[PASS] GET /api/properties/public?purpose=rent -> 200 OK ({len(data)} properties matched)")
    results["filter_rent"] = "PASS"

    # 1.5 Property Count
    status, data = request("/api/properties/public/count")
    assert status == 200 and data.get("total", 0) > 0, f"Count failed: {status}"
    print(f"[PASS] GET /api/properties/public/count -> 200 OK (Total: {data['total']})")
    results["property_count"] = "PASS"

    # 1.6 Single Property Lookup
    first_id = data.get("total", 1)
    status, prop = request(f"/api/properties/public/1")
    assert status == 200 and prop.get("id") == 1, f"Public property detail failed: {status}"
    print(f"[PASS] GET /api/properties/public/1 -> 200 OK (Property: '{prop.get('name')}', Price: {prop.get('price')})")
    results["property_details"] = "PASS"

    # 1.7 Non-/api Prefix Fallback (Middleware check)
    status, prop_no_api = request("/properties/public/1")
    assert status == 200 and prop_no_api.get("id") == 1, f"Non-/api prefix failed: {status}"
    print(f"[PASS] GET /properties/public/1 (Fallback Middleware) -> 200 OK")
    results["prefix_fallback"] = "PASS"

    # 2. AUTHENTICATION & LOGIN FOR ALL ROLES
    print("\n--- 2. Testing Authentication For All Roles ---")

    roles_credentials = {
        "admin": ("kebirogabriel@gmail.com", "onsomuRiley2022"),
        "manager": ("manager@realestate.com", "Manager123!"),
        "owner": ("owner@realestate.com", "Owner123!"),
        "agent": ("agent@realestate.com", "Agent123!"),
        "tenant": ("tenant@realestate.com", "Tenant123!"),
        "provider": ("provider@realestate.com", "Provider123!"),
    }

    tokens = {}
    for role_name, (email, pwd) in roles_credentials.items():
        status, auth_data = request("/api/auth/login", method="POST", data={"email": email, "password": pwd})
        assert status == 200 and "access_token" in auth_data, f"Login for {role_name} failed: {status} {auth_data}"
        tokens[role_name] = auth_data["access_token"]
        user_info = auth_data.get("user", {})
        print(f"[PASS] Login {role_name.upper()} ({email}) -> 200 OK | Role: {user_info.get('role')} | Roles: {user_info.get('roles')}")
        results[f"login_{role_name}"] = "PASS"

    # 3. PORTAL ACCESS & TASKS FOR EACH ROLE
    print("\n--- 3. Testing Portals & Role Permissions ---")

    # 3.1 Admin Portal
    admin_headers = {"Authorization": f"Bearer {tokens['admin']}"}
    status, users = request("/api/admin/users", headers=admin_headers)
    assert status == 200, f"Admin users list failed: {status}"
    status, props = request("/api/admin/properties", headers=admin_headers)
    assert status == 200, f"Admin properties list failed: {status}"
    status, audit = request("/api/audit-logs/", headers=admin_headers)
    assert status == 200, f"Admin audit logs failed: {status}"
    print(f"[PASS] Admin Portal: /admin/users ({len(users)} users), /admin/properties ({len(props)} properties), /admin/audit-logs -> 200 OK")
    results["portal_admin"] = "PASS"

    # 3.2 Manager Portal
    mgr_headers = {"Authorization": f"Bearer {tokens['manager']}"}
    status, mgr_props = request("/api/manager/properties", headers=mgr_headers)
    assert status == 200, f"Manager properties failed: {status}"
    status, mgr_tenants = request("/api/manager/tenants", headers=mgr_headers)
    assert status == 200, f"Manager tenants failed: {status}"
    status, mgr_leases = request("/api/manager/leases", headers=mgr_headers)
    assert status == 200, f"Manager leases failed: {status}"
    print(f"[PASS] Manager Portal: /manager/properties ({len(mgr_props)} properties), /manager/tenants ({len(mgr_tenants)} tenants), /manager/leases ({len(mgr_leases)} leases) -> 200 OK")
    results["portal_manager"] = "PASS"

    # 3.3 Owner Portal
    own_headers = {"Authorization": f"Bearer {tokens['owner']}"}
    status, portfolio = request("/api/owner/portfolio-summary", headers=own_headers)
    assert status == 200, f"Owner portfolio failed: {status}"
    status, own_props = request("/api/owner/properties", headers=own_headers)
    assert status == 200, f"Owner properties failed: {status}"
    status, own_fin = request("/api/owner/financials", headers=own_headers)
    assert status == 200, f"Owner financials failed: {status}"
    print(f"[PASS] Owner Portal: /owner/portfolio-summary (Total Props: {portfolio.get('total_properties')}), /owner/financials (Collected: KES {own_fin.get('total_collected')}) -> 200 OK")
    results["portal_owner"] = "PASS"

    # 3.4 Agent Portal
    agt_headers = {"Authorization": f"Bearer {tokens['agent']}"}
    status, agt_dash = request("/api/agent/dashboard", headers=agt_headers)
    assert status == 200, f"Agent dashboard failed: {status}"
    status, agt_leads = request("/api/agent/leads", headers=agt_headers)
    assert status == 200, f"Agent leads failed: {status}"
    status, agt_viewings = request("/api/agent/viewings", headers=agt_headers)
    assert status == 200, f"Agent viewings failed: {status}"
    print(f"[PASS] Agent Portal: /agent/dashboard (Active Leads: {agt_dash.get('active_leads')}), /agent/leads ({len(agt_leads)} leads), /agent/viewings ({len(agt_viewings)} viewings) -> 200 OK")
    results["portal_agent"] = "PASS"

    # 3.5 Tenant Portal
    ten_headers = {"Authorization": f"Bearer {tokens['tenant']}"}
    status, ten_dash = request("/api/tenant/dashboard", headers=ten_headers)
    assert status == 200, f"Tenant dashboard failed: {status}"
    status, ten_lease = request("/api/tenant/my-tenancy", headers=ten_headers)
    assert status == 200, f"Tenant tenancy failed: {status}"
    status, ten_payments = request("/api/tenant/payments", headers=ten_headers)
    assert status == 200, f"Tenant payments failed: {status}"
    status, ten_maint = request("/api/tenant/maintenance", headers=ten_headers)
    assert status == 200, f"Tenant maintenance failed: {status}"
    print(f"[PASS] Tenant Portal: /tenant/dashboard, /tenant/my-tenancy (Rent: KES {ten_dash.get('lease', {}).get('rent_amount')}), /tenant/payments ({len(ten_payments)} records), /tenant/maintenance ({len(ten_maint)} tickets) -> 200 OK")
    results["portal_tenant"] = "PASS"

    # 3.6 Service Provider Portal
    prv_headers = {"Authorization": f"Bearer {tokens['provider']}"}
    status, prv_orders = request("/api/service-marketplace/work-orders", headers=prv_headers)
    assert status == 200, f"Provider work orders failed: {status}"
    print(f"[PASS] Provider Portal: /service-marketplace/work-orders ({len(prv_orders)} work orders) -> 200 OK")
    results["portal_provider"] = "PASS"

    # 4. REGISTRATION OF NEW ACCOUNTS
    print("\n--- 4. Testing Registration of New Accounts ---")
    
    # 4.1 Tenant Registration
    import time
    unique_suffix = f"test_{int(time.time())}"
    tenant_reg = {
        "email": f"tenant_{unique_suffix}@test.com",
        "password": "Password123!",
        "full_name": "Test Tenant Registration",
        "phone": "+254799001122",
        "preferred_locations": "Westlands",
        "min_budget": 45000,
        "max_budget": 95000,
        "preferred_bedrooms": 2,
        "preferred_property_type": "apartment"
    }
    status, reg_res = request("/api/auth/register/tenant", method="POST", data=tenant_reg)
    assert status == 201 and "access_token" in reg_res, f"Tenant registration failed: {status} {reg_res}"
    print(f"[PASS] Register Tenant: {tenant_reg['email']} -> 201 Created | Token received")
    results["reg_tenant"] = "PASS"

    # 4.2 Owner Registration
    owner_reg = {
        "email": f"owner_{unique_suffix}@test.com",
        "password": "Password123!",
        "full_name": "Test Owner Registration",
        "phone": "+254799001133",
        "owner_type": "individual",
        "company_name": "Test Real Estate Holdings",
        "tax_pin": "P051234567A"
    }
    status, reg_res = request("/api/auth/register/owner", method="POST", data=owner_reg)
    assert status == 201 and "access_token" in reg_res, f"Owner registration failed: {status} {reg_res}"
    print(f"[PASS] Register Owner: {owner_reg['email']} -> 201 Created | Token received")
    results["reg_owner"] = "PASS"

    # 4.3 Agent Registration
    agent_reg = {
        "email": f"agent_{unique_suffix}@test.com",
        "password": "Password123!",
        "full_name": "Test Agent Registration",
        "phone": "+254799001144",
        "agency_name": "Test Agency Ltd",
        "license_number": "LIC-998811",
        "operating_areas": "Nairobi, Kiambu",
        "specialties": "Residential",
        "years_experience": 4
    }
    status, reg_res = request("/api/auth/register/agent", method="POST", data=agent_reg)
    assert status == 201 and "access_token" in reg_res, f"Agent registration failed: {status} {reg_res}"
    print(f"[PASS] Register Agent: {agent_reg['email']} -> 201 Created | Token received")
    results["reg_agent"] = "PASS"

    # 4.4 Provider Registration
    provider_reg = {
        "email": f"provider_{unique_suffix}@test.com",
        "password": "Password123!",
        "full_name": "Test Provider Registration",
        "phone": "+254799001155",
        "business_name": "FastFix Services",
        "specialty": "plumbing",
        "license_number": "EPRA-8819",
        "hourly_rate": "KES 2,000/hr",
        "years_experience": 5
    }
    status, reg_res = request("/api/auth/register/provider", method="POST", data=provider_reg)
    assert status == 201 and "access_token" in reg_res, f"Provider registration failed: {status} {reg_res}"
    print(f"[PASS] Register Provider: {provider_reg['email']} -> 201 Created | Token received")
    results["reg_provider"] = "PASS"

    # Clean up test accounts
    from app.database.database import SessionLocal
    from app.models.user import User
    db = SessionLocal()
    for email in [tenant_reg["email"], owner_reg["email"], agent_reg["email"], provider_reg["email"]]:
        u = db.query(User).filter(User.email == email).first()
        if u:
            db.delete(u)
    db.commit()
    db.close()
    print("[PASS] Test accounts cleanly cleaned up")

    print("\n==================================================")
    print("  ALL 20+ END-TO-END VERIFICATION TESTS PASSED!   ")
    print("==================================================")
    return results

if __name__ == "__main__":
    run_tests()
