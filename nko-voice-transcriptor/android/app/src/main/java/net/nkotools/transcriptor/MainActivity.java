package net.nkotools.transcriptor;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.view.Menu;
import android.view.MenuItem;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.ValueCallback;
import android.widget.EditText;

/**
 * Minimal, dependency-free WebView client for the N'Ko Voice Transcriptor.
 *
 * The app itself has no backend; it loads the web UI served by a running
 * N'Ko Voice Transcriptor instance whose URL the tester provides. Microphone
 * permission is forwarded to the WebView so in-page recording works.
 */
public class MainActivity extends Activity {

    private static final String PREFS = "nko";
    private static final String KEY_URL = "server_url";
    private static final String DEFAULT_URL = "http://10.0.2.2:8000";
    private static final int REQ_MIC = 101;
    private static final int REQ_FILE = 102;
    private static final int MENU_SET_URL = 1;

    private WebView web;
    private PermissionRequest pendingMicRequest;
    private ValueCallback<Uri[]> pendingFileCallback;
    private boolean connectionFailed = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        web = new WebView(this);
        setContentView(web);

        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setMediaPlaybackRequiresUserGesture(false);

        web.setWebViewClient(new WebViewClient() {
            @Override
            public void onReceivedError(WebView view, WebResourceRequest request,
                                        WebResourceError error) {
                // Only care about the main page failing to load (not favicons,
                // sub-resources, etc.). Typical causes: server down, wrong URL,
                // no network, DNS failure.
                if (request.isForMainFrame()) {
                    connectionFailed = true;
                    showConnectionError(String.valueOf(error.getDescription()));
                }
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                runOnUiThread(() -> handleWebPermissionRequest(request));
            }

            @Override
            public void onPermissionRequestCanceled(PermissionRequest request) {
                if (request == pendingMicRequest) pendingMicRequest = null;
            }

            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback,
                                             FileChooserParams params) {
                if (pendingFileCallback != null) pendingFileCallback.onReceiveValue(null);
                pendingFileCallback = callback;
                Intent intent = params.createIntent();
                intent.setType("audio/*");
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                try {
                    startActivityForResult(intent, REQ_FILE);
                    return true;
                } catch (RuntimeException error) {
                    pendingFileCallback = null;
                    callback.onReceiveValue(null);
                    return false;
                }
            }
        });

        // First launch (no saved URL) → ask for the server. Otherwise load it;
        // if the server is unreachable, onReceivedError re-opens the prompt.
        loadSavedOrPrompt();
    }

    /** Grant only microphone capture, and only after Android permission succeeds. */
    private void handleWebPermissionRequest(PermissionRequest request) {
        boolean asksForAudio = false;
        for (String resource : request.getResources()) {
            if (PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(resource)) {
                asksForAudio = true;
                break;
            }
        }
        if (!asksForAudio) {
            request.deny();
            return;
        }
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO)
                == PackageManager.PERMISSION_GRANTED) {
            request.grant(new String[]{PermissionRequest.RESOURCE_AUDIO_CAPTURE});
            return;
        }
        if (pendingMicRequest != null) pendingMicRequest.deny();
        pendingMicRequest = request;
        requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, REQ_MIC);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions,
                                           int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode != REQ_MIC || pendingMicRequest == null) return;
        if (grantResults.length > 0
                && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            pendingMicRequest.grant(
                    new String[]{PermissionRequest.RESOURCE_AUDIO_CAPTURE});
        } else {
            pendingMicRequest.deny();
        }
        pendingMicRequest = null;
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQ_FILE || pendingFileCallback == null) return;
        Uri[] result = WebChromeClient.FileChooserParams.parseResult(resultCode, data);
        pendingFileCallback.onReceiveValue(result);
        pendingFileCallback = null;
    }

    private SharedPreferences prefs() {
        return getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    private void loadSavedOrPrompt() {
        String url = prefs().getString(KEY_URL, null);
        if (url == null || url.isEmpty()) {
            promptForUrl();
        } else {
            connectionFailed = false;
            web.loadUrl(url);
        }
    }

    /** Prompt for (or edit) the backend server URL, then load it. */
    private void promptForUrl() {
        final EditText input = new EditText(this);
        input.setHint("https://your-server:8000");
        input.setText(prefs().getString(KEY_URL, DEFAULT_URL));

        new AlertDialog.Builder(this)
                .setTitle(R.string.url_title)
                .setMessage(R.string.url_message)
                .setView(input)
                .setCancelable(false)
                .setPositiveButton(R.string.load, (dialog, which) -> {
                    String url = input.getText().toString().trim();
                    if (!url.startsWith("http://") && !url.startsWith("https://")) {
                        url = "http://" + url;
                    }
                    prefs().edit().putString(KEY_URL, url).apply();
                    connectionFailed = false;
                    web.loadUrl(url);
                })
                .show();
    }

    /** Shown when the configured server can't be reached: retry or change URL. */
    private void showConnectionError(String detail) {
        String url = prefs().getString(KEY_URL, DEFAULT_URL);
        new AlertDialog.Builder(this)
                .setTitle(R.string.conn_error_title)
                .setMessage(getString(R.string.conn_error_message, url, detail))
                .setCancelable(false)
                .setPositiveButton(R.string.retry, (d, w) -> loadSavedOrPrompt())
                .setNegativeButton(R.string.change_url, (d, w) -> promptForUrl())
                .show();
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        menu.add(0, MENU_SET_URL, 0, R.string.set_url);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        if (item.getItemId() == MENU_SET_URL) {
            promptForUrl();
            return true;
        }
        return super.onOptionsItemSelected(item);
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) {
            web.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
