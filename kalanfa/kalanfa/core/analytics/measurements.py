import logging
from collections import namedtuple
from datetime import timedelta

from django.db import connection
from django.db.models import Count
from django.db.models import Sum
from django.db.utils import OperationalError
from django.utils import timezone

from kalanfa.core.analytics import SUPPORTED_OS
from kalanfa.core.auth.models import Session
from kalanfa.core.content.models import ChannelMetadata
from kalanfa.core.discovery.utils.network.client import NetworkClient
from kalanfa.core.discovery.utils.network.errors import NetworkLocationResponseFailure
from kalanfa.core.logger.models import ContentSessionLog
from kalanfa.core.logger.models import UserSessionLog
from kalanfa.utils.server import NotRunning
from kalanfa.utils.server import PID_FILE

logger = logging.getLogger(__name__)

try:
    import kalanfa.utils.pskalanfa as psutil
except NotImplementedError:
    # This module can't work on this OS
    psutil = None


def get_db_info():
    """
    Returns information about the sessions and users the current
    Kalanfa server has in use

    """
    # Users information
    active_sessions = "unknown"
    active_users = active_users_minute = None
    try:
        connection.ensure_connection()
        now = timezone.now()
        # Non-expired sessions (includes guest accesses):
        active_sessions = str(Session.objects.filter(expire_date__gte=now).count())
        last_ten_minutes = now - timedelta(minutes=10)
        last_minute = now - timedelta(minutes=1)
        # Active logged users:
        active_users = str(
            UserSessionLog.objects.filter(
                last_interaction_timestamp__gte=last_ten_minutes
            ).count()
        )
        # Logged users with activity in the last minute:
        active_users_minute = str(
            UserSessionLog.objects.filter(
                last_interaction_timestamp__gte=last_minute
            ).count()
        )
    except OperationalError:
        logger.info(
            "Database unavailable, impossible to retrieve users and sessions info"
        )

    return (active_sessions, active_users, active_users_minute)


def get_channels_usage_info():
    """
    Scan the channels Kalanfa has installed, getting information on how many times
    their resources have been accessed and how long they have been used
    :returns: List containing namedtuples, with each channel: id, name, accesses and time spent
    """
    channels_info = []
    ChannelsInfo = namedtuple("ChannelsInfo", "id name accesses time_spent")

    try:
        connection.ensure_connection()
        channels = ChannelMetadata.objects.values("id", "name")
        channel_stats = ContentSessionLog.objects.values("channel_id").annotate(
            time_spent=Sum("time_spent"), total=Count("channel_id")
        )
        for channel in channels:
            stats = channel_stats.filter(channel_id=channel["id"])
            if stats:
                channels_info.append(
                    ChannelsInfo(
                        id=channel["id"],
                        name=channel["name"],
                        accesses=str(stats[0]["total"]),
                        time_spent="{:.2f} s".format(stats[0]["time_spent"]),
                    )
                )
            else:
                channels_info.append(
                    ChannelsInfo(
                        id=channel["id"],
                        name=channel["name"],
                        accesses="0",
                        time_spent="0.00 s",
                    )
                )
    except OperationalError:
        logger.info("Database unavailable, impossible to retrieve channels usage info")
    return channels_info


def get_requests_info():
    """
    Returns timing information on some Kalanfa pages that can be hit without credentials
    :returns: tuple of strings containing time in seconds when requesting
              - Kalanfa homepage
              - Kalanfa recommended channels
              - Kalanfa channels list
    """

    _, port = get_kalanfa_process_info()

    def get_time(url):
        base_url = "http://localhost:{}".format(port)
        client = NetworkClient.build_for_address(base_url)
        try:
            response = client.get(url)
            return response.elapsed.total_seconds()
        except NetworkLocationResponseFailure as e:  # most probably a 404
            return e.response.elapsed.total_seconds()

    if port:
        homepage_time = "{:.2f} s".format(get_time("/"))
        recommended_url = (
            "/api/content/contentnode_slim/popular/?include_coach_content=false"
        )
        recommended_time = "{:.2f} s".format(get_time(recommended_url))
        channels_url = "/api/content/channel/?available=true"
        channels_time = "{:.2f} s".format(get_time(channels_url))
    else:
        homepage_time = recommended_time = channels_time = None

    return (homepage_time, recommended_time, channels_time)


def get_machine_info():
    """
    Gets information on the memory, cpu and processes in the server
    :returns: tuple of strings containing cpu percentage, used memory, free memory and number of active processes
    """
    if not SUPPORTED_OS:
        return (None, None, None, None)
    used_cpu = str(psutil.cpu_percent())
    memory = psutil.virtual_memory()
    used_memory = str(memory.used / pow(10, 6))  # In Megabytes
    total_memory = str(memory.total / pow(10, 6))  # In Megabytes
    total_processes = str(len(psutil.pids()))

    return (used_cpu, used_memory, total_memory, total_processes)


def get_kalanfa_process_info():
    """
    Return information on the Kalanfa process running in the machine
    :returns: tuple of integers containing PID and TCP Port of
              the running (if any) Kalanfa server in this same machine
    """
    kalanfa_pid = None
    kalanfa_port = None
    try:
        with open(PID_FILE, "r") as f:
            kalanfa_pid = int(f.readline())
            kalanfa_port = int(f.readline())
    except OSError:
        pass  # Kalanfa PID file does not exist
    except ValueError:
        pass  # corrupted Kalanfa PID file
    return (kalanfa_pid, kalanfa_port)


def get_kalanfa_process_cmd():
    """
    Retrieve from the OS the command line executed to run Kalanfa server
    :returns: tuple with command line and its arguments
    """
    if not SUPPORTED_OS:
        return None
    kalanfa_pid, _ = get_kalanfa_process_info()
    if kalanfa_pid is None:
        return None
    try:
        kalanfa_proc = psutil.Process(kalanfa_pid)
    except psutil.NoSuchProcess:
        # Kalanfa server is not running
        raise NotRunning(0)
    return kalanfa_proc.cmdline()


def get_kalanfa_use(development=False):
    """
    Gets information on the memory and cpu usage of the current Kalanfa process
    :returns: tuple of strings containing cpu percentage and virtual memory used (in Mb)
    """
    if not SUPPORTED_OS:
        return (None, None)
    kalanfa_mem = kalanfa_cpu = "None"
    kalanfa_pid, _ = get_kalanfa_process_info()

    if kalanfa_pid:
        try:
            kalanfa_proc = psutil.Process(kalanfa_pid)
            kalanfa_mem = str(kalanfa_proc.memory_info().rss / pow(10, 6))
            kalanfa_cpu = str(kalanfa_proc.cpu_percent())
        except psutil.NoSuchProcess:
            # Kalanfa server is not running
            raise NotRunning(0)

    return (kalanfa_cpu, kalanfa_mem)
