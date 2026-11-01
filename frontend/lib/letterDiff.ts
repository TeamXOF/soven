// Character-level diff between the printed word and what the child actually
// said (per Whisper). Powers the letter-by-letter inspector in Story Mode.

export type LetterDiffOp = {
  type: "match" | "replace" | "delete" | "insert";
  expected: string;
  heard: string;
};

const clean = (s: string) => (s || "").replace(/[.,!?;:"'()\u060C\u061B\u061F]/g, "").toLowerCase().trim();

/** LCS-based char alignment. "jumped" vs "jump" → one op {type:"delete", expected:"ed"}. */
export function letterDiff(expected: string, heard: string): LetterDiffOp[] {
  const a = clean(expected);
  const b = clean(heard);
  if (!a && !b) return [];
  if (a === b) return [{ type: "match", expected: a, heard: b }];

  const n = a.length, m = b.length;
  // LCS table
  const dp: number[][] = Array.from({ length: n + 1 }, () => new Array(m + 1).fill(0));
  for (let i = 1; i <= n; i++)
    for (let j = 1; j <= m; j++)
      dp[i][j] = a[i - 1] === b[j - 1] ? dp[i - 1][j - 1] + 1 : Math.max(dp[i - 1][j], dp[i][j - 1]);

  // Walk back, grouping consecutive same-type ops
  const ops: LetterDiffOp[] = [];
  let i = n, j = m;
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && a[i - 1] === b[j - 1]) {
      pushOp(ops, "match", a[i - 1], b[j - 1]);
      i--; j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      pushOp(ops, "insert", "", b[j - 1]);
      j--;
    } else {
      pushOp(ops, "delete", a[i - 1], "");
      i--;
    }
  }
  return ops.reverse();

  function pushOp(list: LetterDiffOp[], type: LetterDiffOp["type"], e: string, h: string) {
    const last = list[list.length - 1];
    if (last && last.type === type) {
      if (type === "match") { last.expected = e + last.expected; last.heard = h + last.heard; }
      else if (type === "delete") { last.expected = e + last.expected; }
      else if (type === "insert") { last.heard = h + last.heard; }
      else { last.expected = e + last.expected; last.heard = h + last.heard; }
    } else {
      list.push({ type, expected: e, heard: h });
    }
  }
}
