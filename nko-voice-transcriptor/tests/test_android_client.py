"""Static security/permission contract for the dependency-free Android client."""

from pathlib import Path

ANDROID = Path(__file__).parents[1] / "android" / "app"


def test_android_declares_microphone_permission():
    manifest = (ANDROID / "src" / "main" / "AndroidManifest.xml").read_text(encoding="utf-8")
    assert "android.permission.RECORD_AUDIO" in manifest


def test_webview_waits_for_android_permission_and_grants_audio_only():
    activity = (
        ANDROID
        / "src"
        / "main"
        / "java"
        / "net"
        / "nkotools"
        / "transcriptor"
        / "MainActivity.java"
    ).read_text(encoding="utf-8")
    assert "pendingMicRequest" in activity
    assert "onRequestPermissionsResult" in activity
    assert "RESOURCE_AUDIO_CAPTURE" in activity
    assert "request.grant(request.getResources())" not in activity


def test_android_file_upload_uses_document_picker_without_storage_permission():
    activity = (
        ANDROID
        / "src"
        / "main"
        / "java"
        / "net"
        / "nkotools"
        / "transcriptor"
        / "MainActivity.java"
    ).read_text(encoding="utf-8")
    manifest = (ANDROID / "src" / "main" / "AndroidManifest.xml").read_text(encoding="utf-8")
    assert "onShowFileChooser" in activity
    assert 'setType("audio/*")' in activity
    assert "FileChooserParams.parseResult" in activity
    assert "READ_EXTERNAL_STORAGE" not in manifest
