"use strict";
/* Offline Bambara-Latin → N'Ko transliterator.
 *
 * Faithful JS port of app/nko/transliterator.py, driven by the SAME tables
 * (NKO_DATA, generated from the Python source by build_offline_assets.py).
 * Parity is verified against the Python engine at build time.
 */

const T = NKO_DATA;
const VOWELS = new Set(Object.keys(T.vowels));

function nkoNormalize(text) {
  let s = text.normalize("NFC").toLowerCase();
  for (const [src, dst] of Object.entries(T.normalizations)) {
    s = s.split(src).join(dst);
  }
  return s;
}

function isVowel(ch) { return VOWELS.has(ch); }

function codaNasal(word, i) {
  const ch = word[i];
  if (ch !== "n" && ch !== "ŋ") return false;
  if (i === 0 || !isVowel(word[i - 1])) return false;
  const nxt = i + 1 < word.length ? word[i + 1] : null;
  if (nxt === null) return true;
  if (isVowel(nxt)) return false;
  if (ch === "n" && nxt === "y") return false; // "ny" digraph
  return true;
}

function transliterateWord(word) {
  if (word === "n") return T.nkoNSyllabic;
  const out = [];
  let i = 0;
  while (i < word.length) {
    let matched = false;
    for (const [seq, nko] of Object.entries(T.digraphs)) {
      if (word.startsWith(seq, i)) {
        if (!codaNasal(word, i)) {
          out.push(nko);
          i += seq.length;
          matched = true;
        }
        break;
      }
    }
    if (matched) continue;
    const ch = word[i];
    if (codaNasal(word, i)) out.push(T.nkoNasal);
    else if (ch in T.vowels) out.push(T.vowels[ch]);
    else if (ch in T.consonants) out.push(T.consonants[ch]);
    else if (ch in T.digits) out.push(T.digits[ch]);
    else if (ch in T.punctuation) out.push(T.punctuation[ch]);
    else out.push(ch);
    i += 1;
  }
  return out.join("");
}

function nkoTransliterate(text) {
  if (!text) return "";
  return nkoNormalize(text)
    .split("\n")
    .map((line) => line.split(" ").map(transliterateWord).join(" "))
    .join("\n");
}

/* Offline dictionary search over NKO_LEXICON.
 * lang: "fr" | "bm" | "nko"; ranking exact → prefix → substring. */
function foldFr(s) {
  return s.toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "");
}

function nkoDictSearch(query, lang, limit) {
  const q = lang === "nko" ? query.trim() : foldFr(query.trim());
  if (!q) return [];
  const scored = [];
  for (let i = 0; i < NKO_LEXICON.length; i++) {
    const e = NKO_LEXICON[i];
    const hay = lang === "nko" ? e.nko : lang === "bm" ? e.bm : foldFr(e.fr);
    let rank = null;
    if (hay === q) rank = 0;
    else if (hay.startsWith(q)) rank = 1;
    else if (hay.includes(q)) rank = 2;
    if (rank !== null) scored.push([rank, hay.length, i, e]);
  }
  scored.sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);
  return scored.slice(0, limit).map((s) => s[3]);
}
