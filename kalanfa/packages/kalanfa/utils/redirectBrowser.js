import urls from 'kalanfa/urls';

export default function redirectBrowser(url, next = false) {
  url = url || urls['kalanfa:core:redirect_user']();
  const urlObject = new URL(url, window.location.origin);
  if (next) {
    urlObject.searchParams.set('next', encodeURIComponent(window.location.href));
  }
  window.location.href = urlObject.href;
}
