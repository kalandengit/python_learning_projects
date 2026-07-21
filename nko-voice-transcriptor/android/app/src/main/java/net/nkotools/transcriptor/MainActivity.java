package net.nkotools.transcriptor;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
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
    private static final int MENU_SET_URL = 1;
    private static final int MENU_OFFLINE = 2;
    private static final int MENU_ONLINE = 3;

    /** Bundled offline toolkit: transliterator, dictionary, keyboard, alphabet. */
    private static final String OFFLINE_URL = "file:///android_asset/offline/index.html";

    private WebView web;
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
                runOnUiThread(() -> request.grant(request.getResources()));
            }
        });

        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, REQ_MIC);
        }

        // First launch (no saved URL) → ask for the server. Otherwise load it;
        // if the server is unreachable, onReceivedError re-opens the prompt.
        loadSavedOrPrompt();
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

    /** Shown when the configured server can't be reached: retry, change URL,
     *  or fall back to the bundled offline toolkit. */
    private void showConnectionError(String detail) {
        String url = prefs().getString(KEY_URL, DEFAULT_URL);
        new AlertDialog.Builder(this)
                .setTitle(R.string.conn_error_title)
                .setMessage(getString(R.string.conn_error_message, url, detail))
                .setCancelable(false)
                .setPositiveButton(R.string.retry, (d, w) -> loadSavedOrPrompt())
                .setNegativeButton(R.string.change_url, (d, w) -> promptForUrl())
                .setNeutralButton(R.string.offline_tools, (d, w) -> web.loadUrl(OFFLINE_URL))
                .show();
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        menu.add(0, MENU_SET_URL, 0, R.string.set_url);
        menu.add(0, MENU_OFFLINE, 1, R.string.offline_tools);
        menu.add(0, MENU_ONLINE, 2, R.string.online_app);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        switch (item.getItemId()) {
            case MENU_SET_URL:
                promptForUrl();
                return true;
            case MENU_OFFLINE:
                web.loadUrl(OFFLINE_URL);
                return true;
            case MENU_ONLINE:
                loadSavedOrPrompt();
                return true;
            default:
                return super.onOptionsItemSelected(item);
        }
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
