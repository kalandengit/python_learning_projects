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
    assert "ACTION_APPLICATION_DETAILS_SETTINGS" in activity
    assert "openMicrophoneSettings" in activity
    assert "requestMicrophoneAccess" in activity


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
    assert "Intent.EXTRA_MIME_TYPES" in activity
    assert '"video/mp4"' in activity
    assert "FileChooserParams.parseResult" in activity
    assert "READ_EXTERNAL_STORAGE" not in manifest


def test_android_share_bridge_opens_native_share_sheet():
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
    assert 'addJavascriptInterface(new ShareBridge(this), "NkoAndroid")' in activity
    assert "Intent.ACTION_SEND" in activity
    assert "Intent.createChooser" in activity
    assert "@JavascriptInterface" in activity
