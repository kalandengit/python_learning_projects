"use strict";

// N'Ko on-screen keyboard: letters, digits, tone/length diacritics, punctuation.
const NKO_KEY_ROWS = [
  // Vowels + syllabic N
  ["ߊ", "ߋ", "ߌ", "ߍ", "ߎ", "ߏ", "ߐ", "ߒ"],
  // Consonants
  ["ߓ", "ߔ", "ߕ", "ߖ", "ߗ", "ߘ", "ߙ", "ߚ", "ߛ", "ߜ", "ߝ"],
  ["ߞ", "ߟ", "ߡ", "ߢ", "ߣ", "ߤ", "ߥ", "ߦ", "ߨ", "ߩ", "ߪ"],
  // Digits (RTL order like N'Ko text)
  ["߀", "߁", "߂", "߃", "߄", "߅", "߆", "߇", "߈", "߉"],
  // Tone apostrophes, diacritics, punctuation
  ["߫", "߬", "߭", "߮", "߯", "߰", "߱", "߲", "߳", "ߴ", "ߵ", "ߑ", "߸", "߹", "؟"],
];

const TONE_SET = new Set(["߫", "߬", "߭", "߮", "߯", "߰", "߱", "߲", "߳"]);

function buildKeyboard(container, target) {
  for (const row of NKO_KEY_ROWS) {
    for (const key of row) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = key;
      if (TONE_SET.has(key)) btn.classList.add("tone");
      btn.addEventListener("click", () => {
        const start = target.selectionStart ?? target.value.length;
        const end = target.selectionEnd ?? target.value.length;
        target.value = target.value.slice(0, start) + key + target.value.slice(end);
        target.focus();
        target.selectionStart = target.selectionEnd = start + key.length;
      });
      container.appendChild(btn);
    }
    container.appendChild(document.createElement("br"));
  }
}
