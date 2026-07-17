from pathlib import Path

ROOT = Path(__file__).parents[1]
DASHBOARD = (ROOT / "deploy" / "admin-dashboard.py").read_text(encoding="utf-8")
INSTALLER = (ROOT / "deploy" / "install-admin-dashboard.sh").read_text(encoding="utf-8")
KOLIBRI_INSTALLER = (ROOT / "deploy" / "configure-kolibri-studio.sh").read_text(encoding="utf-8")


def test_dashboard_has_fixed_actions_and_no_shell_execution():
    assert 'ALLOWED_ACTIONS = {"start", "stop", "restart"}' in DASHBOARD
    assert "shell=True" not in DASHBOARD
    assert "os.system" not in DASHBOARD
    assert "eval(" not in DASHBOARD


def test_dashboard_defaults_to_loopback_and_has_csrf_protection():
    assert 'os.getenv("ADMIN_BIND", "127.0.0.1")' in DASHBOARD
    assert 'os.environ["ADMIN_CSRF_TOKEN"]' in DASHBOARD
    assert "X-Frame-Options" in DASHBOARD
    assert "Content-Security-Policy" in DASHBOARD
    assert 'os.environ["ADMIN_SERVICES"]' in DASHBOARD


def test_installer_uses_basic_auth_exact_sudo_rules_and_resource_limit():
    assert 'auth_basic "VPS administration"' in INSTALLER
    assert "NOPASSWD: $SYSTEMCTL start $unit" in INSTALLER
    assert "NOPASSWD: ALL" not in INSTALLER
    assert "MemoryMax=64M" in INSTALLER
    assert "certbot --nginx" in INSTALLER
    assert "admin.saas.kalanfa.org" in INSTALLER
    assert "EXTRA_SERVICES" in INSTALLER


def test_kolibri_proxy_is_loopback_https_and_rolls_back_on_failure():
    assert 'PORT="${PORT:-9090}"' in KOLIBRI_INSTALLER
    assert 'proxy_pass http://127.0.0.1:$PORT' in KOLIBRI_INSTALLER
    assert "certbot --nginx" in KOLIBRI_INSTALLER
    assert "rollback" in KOLIBRI_INSTALLER
    assert 'SERVICE="${SERVICE:-kolibri-studio.service}"' in KOLIBRI_INSTALLER
