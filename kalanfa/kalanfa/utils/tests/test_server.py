"""
Tests for `kalanfa.utils.server` module.
"""

import os
from unittest import TestCase

import mock
import pytest

from kalanfa.core.tasks.job import Job
from kalanfa.core.tasks.storage import Storage
from kalanfa.utils import server
from kalanfa.utils.conf import OPTIONS
from kalanfa.utils.constants import installation_types


class TestServerInstallation:
    @mock.patch("sys.argv", ["kalanfa-0.9.3.pex", "start"])
    def test_pex(self):
        install_type = server.installation_type()
        assert install_type == installation_types.PEX

    def test_dev(self):
        with mock.patch("os.environ", {"KALANFA_DEVELOPER_MODE": "True"}):
            install_type = server.installation_type()
            assert install_type == "devserver"

    @mock.patch("sys.argv", ["/usr/bin/kalanfa", "start"])
    @mock.patch("os.environ", {"KALANFA_INSTALLER_VERSION": "1.0"})
    def test_dpkg(self):
        with mock.patch("kalanfa.utils.server.check_output", return_value=""):
            install_type = server.installation_type()
            assert install_type == installation_types.install_type_map[
                installation_types.DEB
            ].format("1.0")

    @mock.patch("sys.argv", ["/usr/bin/kalanfa", "start"])
    def test_dpkg_version(self):
        DPKG_OUTPUT = """
        Package: kalanfa
        Status: install ok installed
        Priority: optional
        Section: education
        Architecture: all
        Source: kalanfa-source
        Version: 0.15.0~beta2-0ubuntu1
        Depends: python3 (>= 3.4), python3-pkg-resources, adduser
        Recommends: python3-cryptography (>= 1.2.3)
        """
        with mock.patch("kalanfa.utils.server.check_output", return_value=DPKG_OUTPUT):
            install_type = server.installation_type()
            assert install_type == installation_types.install_type_map[
                installation_types.DEB
            ].format("0.15.0~beta2-0ubuntu1")

    @mock.patch("sys.argv", ["/usr/bin/kalanfa", "start"])
    @mock.patch("os.environ", {"KALANFA_INSTALLER_VERSION": "1.0"})
    def test_apt(apt):
        with mock.patch("kalanfa.utils.server.check_output", return_value="any repo"):
            install_type = server.installation_type()
            assert install_type == installation_types.install_type_map[
                installation_types.DEB
            ].format("1.0")

    @mock.patch("sys.argv", ["C:\\Python34\\Scripts\\kalanfa", "start"])
    @mock.patch("sys.path", ["", "C:\\Program Files\\Kalanfa\\kalanfa.exe"])
    @mock.patch("os.environ", {"KALANFA_INSTALLER_VERSION": "1.0"})
    def test_windows(self):
        install_type = server.installation_type()
        assert install_type == installation_types.install_type_map[
            installation_types.WINDOWS
        ].format("1.0")

    @mock.patch("sys.argv", ["/usr/local/bin/kalanfa", "start"])
    def test_whl(self):
        install_type = server.installation_type()
        assert (
            install_type == installation_types.install_type_map[installation_types.WHL]
        )


@pytest.fixture
def job_storage():
    s = Storage()
    s.clear()
    yield s
    s.clear()


class TestServerServices:
    @mock.patch("kalanfa.core.deviceadmin.tasks.schedule_vacuum")
    @mock.patch("kalanfa.core.analytics.tasks.schedule_ping")
    @mock.patch("kalanfa.core.tasks.main.initialize_workers")
    @mock.patch("kalanfa.core.discovery.utils.network.broadcast.KalanfaBroadcast")
    def test_required_services_initiate_on_start(
        self,
        mock_kalanfa_broadcast,
        initialize_workers,
        schedule_ping,
        schedule_vacuum,
    ):
        # Start server services
        services_plugin = server.ServicesPlugin(mock.MagicMock(name="bus"))
        services_plugin.START()

        # Do we initialize workers when services start?
        initialize_workers.assert_called_once()

        mock_kalanfa_broadcast.assert_not_called()

    def test_services_shutdown_on_stop(self):
        # Initialize and ready services plugin for testing
        services_plugin = server.ServicesPlugin(mock.MagicMock(name="bus"))

        from kalanfa.core.tasks.worker import WorkerSupervisor

        services_plugin.worker = mock.MagicMock(
            name="worker", spec_set=WorkerSupervisor
        )

        # Now, let us stop services plugin
        services_plugin.STOP()

        # Do we shutdown workers correctly?
        assert services_plugin.worker.shutdown.call_count == 1
        assert services_plugin.worker.mock_calls == [
            mock.call.shutdown(wait=True),
        ]


@pytest.mark.django_db(databases="__all__", transaction=True)
class TestServerDefaultScheduledTasks:
    @mock.patch("kalanfa.core.discovery.utils.network.broadcast.KalanfaBroadcast")
    def test_scheduled_jobs_persist_on_restart(
        self,
        mock_kalanfa_broadcast,
        job_storage,
    ):
        with mock.patch("kalanfa.core.tasks.registry.job_storage", wraps=job_storage):
            # Schedule two userdefined jobs
            from datetime import timedelta

            from kalanfa.utils.time_utils import local_now

            schedule_time = local_now() + timedelta(hours=1)
            test1 = job_storage.schedule(schedule_time, Job(id))
            test2 = job_storage.schedule(schedule_time, Job(id))

            # Now, start services plugin
            default_scheduled_tasks_plugin = server.DefaultScheduledTasksPlugin(
                mock.MagicMock(name="bus")
            )
            default_scheduled_tasks_plugin.START()

            # We must have exactly six scheduled jobs: the two user-defined
            # jobs above plus four server-defined jobs (pingback, local
            # notifications, vacuum, and streamed cache cleanup).
            from kalanfa.core.analytics.tasks import DEFAULT_PING_JOB_ID
            from kalanfa.core.analytics.tasks import LOCAL_NOTIFICATION_JOB_ID
            from kalanfa.core.deviceadmin.tasks import SCH_VACUUM_JOB_ID
            from kalanfa.core.deviceadmin.tasks import STREAMED_CACHE_CLEANUP_JOB_ID

            assert len(job_storage) == 6
            assert job_storage.get_job(test1) is not None
            assert job_storage.get_job(test2) is not None
            assert job_storage.get_job(DEFAULT_PING_JOB_ID) is not None
            assert job_storage.get_job(LOCAL_NOTIFICATION_JOB_ID) is not None
            assert job_storage.get_job(SCH_VACUUM_JOB_ID) is not None
            assert job_storage.get_job(STREAMED_CACHE_CLEANUP_JOB_ID) is not None

            # Restart services
            default_scheduled_tasks_plugin.START()

            # Make sure all scheduled jobs persist after restart
            assert len(job_storage) == 6
            assert job_storage.get_job(test1) is not None
            assert job_storage.get_job(test2) is not None
            assert job_storage.get_job(DEFAULT_PING_JOB_ID) is not None
            assert job_storage.get_job(LOCAL_NOTIFICATION_JOB_ID) is not None
            assert job_storage.get_job(SCH_VACUUM_JOB_ID) is not None
            assert job_storage.get_job(STREAMED_CACHE_CLEANUP_JOB_ID) is not None


class TestZeroConfPlugin:
    @mock.patch("kalanfa.core.discovery.utils.network.search.NetworkLocationListener")
    @mock.patch(
        "kalanfa.core.discovery.utils.network.broadcast.build_broadcast_instance"
    )
    @mock.patch("kalanfa.core.discovery.utils.network.broadcast.KalanfaBroadcast")
    def test_required_services_initiate_on_start(
        self, mock_kalanfa_broadcast, mock_build_instance, *args
    ):
        # Start zeroconf services
        zeroconf_plugin = server.ZeroConfPlugin(mock.MagicMock(name="bus"), 1234)
        zeroconf_plugin.START()

        mock_kalanfa_broadcast.assert_not_called()

        zeroconf_plugin.SERVING(1234)
        zeroconf_plugin.RUN()

        # Do we register ourselves on zeroconf?
        mock_kalanfa_broadcast.assert_called()
        mock_kalanfa_broadcast().start_broadcast.assert_called_once_with()
        mock_build_instance.assert_called_once_with(1234)

        zeroconf_plugin.STOP()

    @mock.patch("kalanfa.core.discovery.utils.network.broadcast.KalanfaBroadcast")
    def test_services_shutdown_on_stop(self, mock_kalanfa_broadcast):
        zeroconf_plugin = server.ZeroConfPlugin(mock.MagicMock(name="bus"), 1234)
        broadcast = mock_kalanfa_broadcast()
        zeroconf_plugin.broadcast = broadcast
        # Now, let us stop services plugin
        zeroconf_plugin.STOP()

        # Do we unregister ourselves from zeroconf network?
        broadcast.stop_broadcast.assert_called_once()


@pytest.mark.django_db(databases="__all__", transaction=True)
class TestGetLocalHostnames:
    def test_no_hostnames_stored(self):
        assert server.get_local_hostnames() == []

    def test_returns_stored_hostnames(self):
        from kalanfa.core.discovery.models import LocalHostname

        LocalHostname.objects.create(hostname="kalanfa.local")
        LocalHostname.objects.create(hostname="tonyslaptop.local")
        assert set(server.get_local_hostnames()) == {
            "kalanfa.local",
            "tonyslaptop.local",
        }


class GetUrlsTestCase(TestCase):
    @mock.patch.object(server, "get_local_hostnames")
    @mock.patch.object(server, "_get_local_ips")
    def test_get_urls__includes_local_hostnames(self, mock_ips, mock_hostnames):
        mock_ips.return_value = ["10.0.0.5"]
        mock_hostnames.return_value = ["kalanfa.local", "tonyslaptop.local"]
        with mock.patch.dict(OPTIONS["Deployment"], {"LISTEN_ADDRESS": "0.0.0.0"}):
            status, urls = server.get_urls(listen_port=1234)
        self.assertEqual(server.STATUS_RUNNING, status)
        self.assertIn("http://10.0.0.5:1234/", urls)
        self.assertIn("http://kalanfa.local:1234/", urls)
        self.assertIn("http://tonyslaptop.local:1234/", urls)

    @mock.patch.object(server, "get_local_hostnames")
    def test_get_urls__no_local_hostnames(self, mock_hostnames):
        mock_hostnames.return_value = []
        with mock.patch.dict(OPTIONS["Deployment"], {"LISTEN_ADDRESS": "127.0.0.1"}):
            status, urls = server.get_urls(listen_port=1234)
        self.assertEqual(["http://127.0.0.1:1234/"], urls)

    @mock.patch.object(server, "get_local_hostnames")
    @mock.patch.object(server, "_get_local_ips")
    def test_get_urls__local_hostnames_survive_ip_enumeration_failure(
        self, mock_ips, mock_hostnames
    ):
        mock_ips.side_effect = RuntimeError()
        mock_hostnames.return_value = ["kalanfa.local"]
        with mock.patch.dict(OPTIONS["Deployment"], {"LISTEN_ADDRESS": "0.0.0.0"}):
            status, urls = server.get_urls(listen_port=1234)
        self.assertEqual(server.STATUS_RUNNING, status)
        self.assertEqual(["http://kalanfa.local:1234/"], urls)


@mock.patch(
    "kalanfa.utils.server._read_pid_file", return_value=((None, None, None, None))
)
class ServerInitializationTestCase(TestCase):
    @mock.patch("kalanfa.utils.server.logger.error")
    @mock.patch("kalanfa.utils.server.wait_for_free_port")
    def test_port_occupied(self, wait_for_port_mock, logging_mock, read_pid_file_mock):
        wait_for_port_mock.side_effect = OSError
        with self.assertRaises(server.PortOccupied):
            server._port_check("8080")
        logging_mock.assert_called()

    @mock.patch("kalanfa.utils.server.logger.error")
    @mock.patch("kalanfa.utils.server.wait_for_free_port")
    def test_port_occupied_socket_activation(
        self, wait_for_port_mock, logging_mock, read_pid_file_mock
    ):
        wait_for_port_mock.side_effect = OSError
        # LISTEN_PID environment variable would be set if using socket activation
        with mock.patch.dict(os.environ, {"LISTEN_PID": "1234"}):
            server._port_check("8080")
            logging_mock.assert_not_called()

    @mock.patch("kalanfa.utils.server.logger.error")
    @mock.patch("kalanfa.utils.server.wait_for_free_port")
    def test_port_zero_zip_port_zero(
        self, wait_for_port_mock, logging_mock, read_pid_file_mock
    ):
        wait_for_port_mock.side_effect = OSError
        server._port_check(0)
        logging_mock.assert_not_called()

    @mock.patch("kalanfa.utils.server.pid_exists")
    def test_unclean_shutdown(self, pid_exists_mock, read_pid_file_mock):
        pid_exists_mock.return_value = False
        read_pid_file_mock.return_value = (1000, 8000, 8001, server.STATUS_RUNNING)
        with mock.patch.object(server.KalanfaProcessBus, "run") as run_mock:
            server.start()
            run_mock.assert_called()

    @mock.patch("kalanfa.utils.server.pid_exists")
    @mock.patch("kalanfa.utils.server.wait_for_free_port")
    def test_server_running(
        self, wait_for_port_mock, pid_exists_mock, read_pid_file_mock
    ):
        wait_for_port_mock.side_effect = OSError
        pid_exists_mock.return_value = True
        read_pid_file_mock.return_value = (1000, 8000, 8001, server.STATUS_RUNNING)
        with self.assertRaises(server.PortOccupied):
            server.start(port=8000)


class ServerSignalHandlerTestCase(TestCase):
    @mock.patch("kalanfa.utils.server.os.getpid")
    @mock.patch("kalanfa.utils.server.BaseSignalHandler._handle_signal")
    def test_signal_different_pid(self, handle_signal_mock, getpid_mock):
        getpid_mock.return_value = 1235
        signal_handler = server.SignalHandler(mock.MagicMock())
        signal_handler.process_pid = 1234
        signal_handler._handle_signal()
        handle_signal_mock.assert_not_called()

    @mock.patch("kalanfa.utils.server.os.getpid")
    @mock.patch("kalanfa.utils.server.BaseSignalHandler._handle_signal")
    def test_signal_same_pid(self, handle_signal_mock, getpid_mock):
        pid = 1234
        getpid_mock.return_value = pid
        signal_handler = server.SignalHandler(mock.MagicMock())
        signal_handler.process_pid = pid
        signal_handler._handle_signal()
        handle_signal_mock.assert_called()

    def test_signal_subscribe(self):
        bus_mock = mock.MagicMock()
        signal_handler = server.SignalHandler(bus_mock)
        signal_handler.subscribe()
        bus_mock.subscribe.assert_called_with("ENTER", signal_handler.ENTER)
