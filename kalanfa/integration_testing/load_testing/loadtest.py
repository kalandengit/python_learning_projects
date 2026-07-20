#!/usr/bin/env python
"""
Kalanfa Load Testing Tool

A comprehensive CLI for setting up and running load tests against Kalanfa servers.
Orchestrates device provisioning, user import, content setup, flow capture, and load testing.

Usage:
    # Full automated workflow
    python loadtest.py

    # Step-by-step
    python loadtest.py provision
    python loadtest.py setup-facility
    python loadtest.py import-users
    python loadtest.py import-channel
    python loadtest.py create-lesson
    python loadtest.py capture
    python loadtest.py run --users 50 --duration 5m

"""

import os
import subprocess
import threading
import time
import webbrowser

import click
from kalanfa_client import KalanfaClient
from logger import info
from logger import plain
from logger import section
from logger import step
from logger import success

# Constants
HAR_FILES_DIR = os.path.join(os.path.dirname(__file__), "har_files")
QA_CHANNEL_ID = "95a52b386f2c485cb97dd60901674a98"
FACILITY_NAME = "Load Test Facility"
CLASS_NAME = "Load Test Class"


def _exit_with_error(message):
    exception = click.ClickException(message)
    exception.exit_code = 2
    raise exception


@click.group(invoke_without_command=True)
@click.option("--server", prompt="Kalanfa server URL", help="Kalanfa server URL")
@click.option("--username", prompt="Admin username", help="Admin username")
@click.option(
    "--password", prompt="Admin password", hide_input=True, help="Admin password"
)
@click.option("--har", "-h", help="Specific HAR file to use")
@click.option("--users", "-u", default=50, help="Number of concurrent users")
@click.option("--spawn-rate", "-r", default=50, help="Users spawned per second")
@click.option("--duration", "-t", default="5m", help="Test duration (e.g., 5m, 1h)")
@click.option(
    "--headless", is_flag=True, help="Run without web UI (default: show web UI)"
)
@click.option(
    "--max-retries",
    default=5,
    help="Max retries for 503 errors on trackprogress (default: 5)",
)
@click.option(
    "--retry-delay",
    default=5.0,
    help="Retry delay in seconds for 503 errors (default: 5.0)",
)
@click.pass_context
def cli(
    ctx,
    server,
    username,
    password,
    har,
    users,
    spawn_rate,
    duration,
    headless,
    max_retries,
    retry_delay,
):
    """Kalanfa Load Testing Tool"""
    ctx.ensure_object(dict)
    ctx.obj["server"] = server
    ctx.obj["username"] = username
    ctx.obj["password"] = password
    ctx.obj["har"] = har
    ctx.obj["users"] = users
    ctx.obj["spawn_rate"] = spawn_rate
    ctx.obj["duration"] = duration
    ctx.obj["headless"] = headless
    ctx.obj["max_retries"] = max_retries
    ctx.obj["retry_delay"] = retry_delay

    # If no subcommand provided, run full workflow
    if ctx.invoked_subcommand is None:
        full(ctx)


@cli.command()
@click.pass_context
def provision(ctx):
    """Provision device if not already provisioned"""
    client = KalanfaClient(ctx.obj["server"])

    if not client.is_provisioned():
        info("Provisioning device...")
        client.provision_if_needed(
            ctx.obj["username"], ctx.obj["password"], FACILITY_NAME
        )
        success("Device provisioned successfully")
    else:
        success("Device already provisioned")


@cli.command()
@click.pass_context
def setup_facility(ctx):
    """Setup or get facility"""
    client = KalanfaClient(ctx.obj["server"], ctx.obj["username"], ctx.obj["password"])
    facility_id = client.get_or_create_facility(FACILITY_NAME)
    success(f"Facility: {facility_id}")


@cli.command()
@click.pass_context
def import_users(ctx):
    """Import users from CSV"""
    num_users = ctx.obj["users"]
    client = KalanfaClient(ctx.obj["server"], ctx.obj["username"], ctx.obj["password"])
    facility_id = client.get_or_create_facility(FACILITY_NAME)

    info(f"Importing {num_users} users...")
    classroom_id = client.import_users(facility_id, num_users, CLASS_NAME)
    success(f"Users imported, classroom: {classroom_id}")


@cli.command()
@click.pass_context
def import_channel(ctx):
    """Import channel content"""
    client = KalanfaClient(ctx.obj["server"], ctx.obj["username"], ctx.obj["password"])
    info(f"Importing channel {QA_CHANNEL_ID}...")
    client.import_channel(QA_CHANNEL_ID)
    success(f"Channel imported: {QA_CHANNEL_ID}")


@cli.command()
@click.pass_context
def create_lesson(ctx):
    """Create comprehensive lesson with mixed content"""
    client = KalanfaClient(ctx.obj["server"], ctx.obj["username"], ctx.obj["password"])

    # Get facility and classroom
    facility_id = client.get_or_create_facility(FACILITY_NAME)
    classroom = client.get_classroom(facility_id, CLASS_NAME)

    if not classroom:
        _exit_with_error(
            f"Classroom '{CLASS_NAME}' not found. Run 'import-users' first."
        )

    client.create_lesson(QA_CHANNEL_ID, classroom["id"])


@cli.command()
@click.pass_context
def capture(ctx):
    """Capture HAR file for current Kalanfa version"""
    # Get Kalanfa version for HAR filename
    client = KalanfaClient(ctx.obj["server"], ctx.obj["username"], ctx.obj["password"])
    device_info = client.get_device_info()
    kalanfa_version = device_info.get("kalanfa_version", "unknown")

    # Name HAR file with Kalanfa version
    har_filename = f"lesson_flow_kalanfa_{kalanfa_version}.har"
    har_path = os.path.join(HAR_FILES_DIR, har_filename)

    # Check if HAR already exists
    if os.path.exists(har_path):
        success(f"HAR file already exists for Kalanfa {kalanfa_version}")
        plain(f"  {har_path}")
        plain("\nDelete it to re-capture, or use a different Kalanfa version")
        return

    os.makedirs(HAR_FILES_DIR, exist_ok=True)

    from recorder import capture_manual_flow

    info(f"Manual capture mode for Kalanfa {kalanfa_version}...")
    capture_manual_flow(ctx.obj["server"], har_path)
    success(f"✓ HAR file captured: {har_path}")


@cli.command()
@click.pass_context
def run(ctx):
    """Run Locust load test"""
    client = KalanfaClient(ctx.obj["server"], ctx.obj["username"], ctx.obj["password"])

    # Get Kalanfa version to find the right HAR file
    device_info = client.get_device_info()
    kalanfa_version = device_info.get("kalanfa_version", "unknown")

    if ctx.obj["har"]:
        har_path = ctx.obj["har"]
    else:
        # Find version-specific HAR file
        har_filename = f"lesson_flow_kalanfa_{kalanfa_version}.har"
        har_path = os.path.join(HAR_FILES_DIR, har_filename)

    if not os.path.exists(har_path):
        _exit_with_error(f"Specified HAR file does not exist: {har_path}")

    # Get facility ID
    facility_id = client.get_or_create_facility(FACILITY_NAME)
    classroom = client.get_classroom(facility_id, CLASS_NAME)
    if not classroom:
        _exit_with_error(
            f"Classroom '{CLASS_NAME}' not found. Run 'import-users' first."
        )
    classroom_id = classroom["id"]

    lesson = client.get_lesson(classroom_id)
    if not lesson:
        _exit_with_error("Comprehensive lesson not found. Run 'create-lesson' first.")
    lesson_id = lesson["id"]

    # Path to locustfile.py in the load_testing directory
    locust_path = os.path.join(os.path.dirname(__file__), "locustfile.py")

    users = ctx.obj["users"]
    spawn_rate = ctx.obj["spawn_rate"]
    duration = ctx.obj["duration"]
    headless = ctx.obj["headless"]
    max_retries = ctx.obj["max_retries"]
    retry_delay = ctx.obj["retry_delay"]

    # Set up environment variables for locustfile
    env = os.environ.copy()
    env["KALANFA_HAR_FILE"] = har_path
    env["KALANFA_SERVER_URL"] = ctx.obj["server"]
    env["KALANFA_FACILITY_ID"] = facility_id
    env["KALANFA_CLASSROOM_ID"] = classroom_id
    env["KALANFA_LESSON_ID"] = lesson_id
    env["KALANFA_NUM_USERS"] = str(users)
    env["KALANFA_MAX_RETRIES"] = str(max_retries)
    env["KALANFA_RETRY_DELAY"] = str(retry_delay)
    env["KALANFA_VERSION"] = kalanfa_version

    cmd = [
        "locust",
        "-f",
        locust_path,
        "-u",
        str(users),
        "-r",
        str(spawn_rate),
        "--run-time",
        duration,
        "--processes",
        "-1",
    ]

    # Only add --headless flag if explicitly requested
    if headless:
        cmd.append("--headless")
    else:
        # Auto-start the test when using web UI
        cmd.append("--autostart")

    info(f"Running Locust test (Kalanfa {kalanfa_version})...")
    plain(f"HAR file: {har_path}")
    plain(f"Users: {users}, Spawn rate: {spawn_rate}, Duration: {duration}")
    plain(f"Retry config: max_retries={max_retries}, retry_delay={retry_delay}s")

    if not headless:
        web_ui_url = "http://localhost:8089"
        info(f"Web UI: {web_ui_url}")
        info("Opening web dashboard...")

        # Open browser automatically
        def open_browser():
            # Wait a moment for Locust to start
            time.sleep(2)
            webbrowser.open(web_ui_url)

        # Open browser in background thread
        threading.Thread(target=open_browser, daemon=True).start()

    subprocess.run(cmd, env=env)


@cli.command()
@click.pass_context
def setup(ctx):
    """Provision device, create facility, import users, import channel, and create lesson"""
    step(1, 5, "Checking device provisioning...")
    ctx.invoke(provision)

    step(2, 5, "Setting up facility...")
    ctx.invoke(setup_facility)

    step(3, 5, "Importing users...")
    ctx.invoke(import_users)

    step(4, 5, "Importing QA channel...")
    ctx.invoke(import_channel)

    step(5, 5, "Creating comprehensive lesson...")
    ctx.invoke(create_lesson)

    success("Setup complete")


def full(ctx):
    """Run complete setup → capture → test workflow"""
    section("=" * 70)
    section("KALANFA LOAD TEST - FULL WORKFLOW")
    section("=" * 70)

    total_steps = 6 if ctx.obj["har"] else 7

    # Run each step with step numbering
    step(1, total_steps, "Checking device provisioning...")
    ctx.invoke(provision)

    step(2, total_steps, "Setting up facility...")
    ctx.invoke(setup_facility)

    step(3, total_steps, "Importing users...")
    ctx.invoke(import_users)

    step(4, total_steps, "Importing QA channel...")
    ctx.invoke(import_channel)

    step(5, total_steps, "Creating comprehensive lesson...")
    ctx.invoke(create_lesson)

    if not ctx.obj["har"]:
        step(6, total_steps, "Capturing lesson flow...")
        ctx.invoke(capture)

    step(total_steps, total_steps, "Running load test...")
    ctx.invoke(run)

    section("=" * 70)
    success("WORKFLOW COMPLETE")
    section("=" * 70)


if __name__ == "__main__":
    cli()
