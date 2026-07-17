package net.nkotools.transcriptor;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.hardware.biometrics.BiometricPrompt;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.os.Build;
import android.os.CancellationSignal;
import android.provider.Settings;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.webkit.PermissionRequest;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.ValueCallback;
import android.widget.EditText;
import android.util.Base64;

import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;

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
    private static final int MENU_BIOMETRIC = 2;
    private static final String KEY_BIOMETRIC = "biometric_lock";

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
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setAllowFileAccessFromFileURLs(false);
        settings.setAllowUniversalAccessFromFileURLs(false);
        web.addJavascriptInterface(new ShareBridge(this), "NkoAndroid");
        web.addJavascriptInterface(new SecureStore(this), "NkoSecureStore");

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri target = request.getUrl();
                Uri trusted = Uri.parse(prefs().getString(KEY_URL, DEFAULT_URL));
                boolean sameOrigin = target.getScheme() != null
                        && target.getScheme().equalsIgnoreCase(trusted.getScheme())
                        && target.getHost() != null
                        && target.getHost().equalsIgnoreCase(trusted.getHost())
                        && target.getPort() == trusted.getPort();
                if (sameOrigin) return false;
                if ("https".equals(target.getScheme()) || "http".equals(target.getScheme())) {
                    startActivity(new Intent(Intent.ACTION_VIEW, target));
                }
                return true;
            }
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
                intent.setType("*/*");
                intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{
                        "audio/*", "video/mp4", "video/webm", "video/quicktime"
                });
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
        unlockThenLoad();
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
        if (requestCode != REQ_MIC) return;
        boolean granted = grantResults.length > 0
                && grantResults[0] == PackageManager.PERMISSION_GRANTED;
        if (pendingMicRequest != null) {
            if (granted) {
                pendingMicRequest.grant(
                        new String[]{PermissionRequest.RESOURCE_AUDIO_CAPTURE});
            } else {
                pendingMicRequest.deny();
                showMicrophoneHelp();
            }
            pendingMicRequest = null;
        } else if (granted) {
            new AlertDialog.Builder(this).setMessage("Microphone access granted.")
                    .setPositiveButton("OK", null).show();
        } else {
            showMicrophoneHelp();
        }
    }

    private void showMicrophoneHelp() {
        new AlertDialog.Builder(this)
                .setTitle("Microphone access")
                .setMessage("Allow Microphone for N'Ko Transcriptor in Android settings. "
                        + "The backend address must also use HTTPS for recording.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Open settings", (dialog, which) -> {
                    Intent intent = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
                    intent.setData(Uri.parse("package:" + getPackageName()));
                    startActivity(intent);
                })
                .show();
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

    /** Minimal native bridge used only to open Android's standard share sheet. */
    private static final class ShareBridge {
        private final Activity activity;

        ShareBridge(Activity activity) {
            this.activity = activity;
        }

        @JavascriptInterface
        public void share(String text) {
            if (text == null || text.isBlank()) return;
            String safeText = text.length() > 20_000 ? text.substring(0, 20_000) : text;
            activity.runOnUiThread(() -> {
                Intent send = new Intent(Intent.ACTION_SEND);
                send.setType("text/plain");
                send.putExtra(Intent.EXTRA_TEXT, safeText);
                activity.startActivity(Intent.createChooser(send, "Share N'Ko transcript"));
            });
        }

        @JavascriptInterface
        public void openMicrophoneSettings() {
            activity.runOnUiThread(() -> ((MainActivity) activity).showMicrophoneHelp());
        }

        @JavascriptInterface
        public void requestMicrophoneAccess() {
            activity.runOnUiThread(() -> {
                if (activity.checkSelfPermission(Manifest.permission.RECORD_AUDIO)
                        == PackageManager.PERMISSION_GRANTED) {
                    new AlertDialog.Builder(activity).setMessage("Microphone access is already granted.")
                            .setPositiveButton("OK", null).show();
                } else {
                    activity.requestPermissions(
                            new String[]{Manifest.permission.RECORD_AUDIO}, REQ_MIC);
                }
            });
        }
    }

    /** Access tokens at rest are encrypted by an Android Keystore AES key. */
    private static final class SecureStore {
        private static final String ALIAS = "nko-session-key";
        private static final String VALUE = "secure_token";
        private final Context context;

        SecureStore(Context context) { this.context = context; }

        private SecretKey key() throws Exception {
            KeyStore store = KeyStore.getInstance("AndroidKeyStore");
            store.load(null);
            if (!store.containsAlias(ALIAS)) {
                KeyGenerator generator = KeyGenerator.getInstance(
                        KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
                generator.init(new KeyGenParameterSpec.Builder(
                        ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                        .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                        .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                        .build());
                return generator.generateKey();
            }
            return ((KeyStore.SecretKeyEntry) store.getEntry(ALIAS, null)).getSecretKey();
        }

        @JavascriptInterface
        public void setToken(String token) {
            try {
                Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
                cipher.init(Cipher.ENCRYPT_MODE, key());
                String value = Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP) + "."
                        + Base64.encodeToString(
                                cipher.doFinal(token.getBytes(StandardCharsets.UTF_8)),
                                Base64.NO_WRAP);
                context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                        .edit().putString(VALUE, value).apply();
            } catch (Exception ignored) { }
        }

        @JavascriptInterface
        public String getToken() {
            try {
                String value = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                        .getString(VALUE, "");
                if (value.isEmpty()) return "";
                String[] pieces = value.split("\\.", 2);
                Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
                cipher.init(Cipher.DECRYPT_MODE, key(), new GCMParameterSpec(
                        128, Base64.decode(pieces[0], Base64.NO_WRAP)));
                return new String(cipher.doFinal(
                        Base64.decode(pieces[1], Base64.NO_WRAP)), StandardCharsets.UTF_8);
            } catch (Exception ignored) { return ""; }
        }

        @JavascriptInterface
        public void clear() {
            context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                    .edit().remove(VALUE).apply();
        }
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
        MenuItem lock = menu.add(0, MENU_BIOMETRIC, 1, "Biometric lock");
        lock.setCheckable(true).setChecked(prefs().getBoolean(KEY_BIOMETRIC, false));
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        if (item.getItemId() == MENU_SET_URL) {
            promptForUrl();
            return true;
        }
        if (item.getItemId() == MENU_BIOMETRIC) {
            boolean enabled = !item.isChecked();
            prefs().edit().putBoolean(KEY_BIOMETRIC, enabled).apply();
            item.setChecked(enabled);
            return true;
        }
        return super.onOptionsItemSelected(item);
    }

    private void unlockThenLoad() {
        if (!prefs().getBoolean(KEY_BIOMETRIC, false) || Build.VERSION.SDK_INT < 28) {
            loadSavedOrPrompt();
            return;
        }
        web.setVisibility(View.INVISIBLE);
        BiometricPrompt prompt = new BiometricPrompt.Builder(this)
                .setTitle("Unlock N'Ko Voice")
                .setSubtitle("Protect your transcripts")
                .setDeviceCredentialAllowed(true)
                .build();
        prompt.authenticate(new CancellationSignal(), getMainExecutor(),
                new BiometricPrompt.AuthenticationCallback() {
                    @Override
                    public void onAuthenticationSucceeded(
                            BiometricPrompt.AuthenticationResult result) {
                        web.setVisibility(View.VISIBLE);
                        loadSavedOrPrompt();
                    }

                    @Override
                    public void onAuthenticationError(int code, CharSequence message) {
                        showConnectionError(String.valueOf(message));
                    }
                });
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
