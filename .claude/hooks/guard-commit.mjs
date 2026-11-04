// The logic behind guard-commit.sh, which carries the why. Reads the PreToolUse
// payload on stdin; exits 2 with the reason on stderr to refuse the command.
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const HOOKS_PATH = ".husky/_";

// Splits a shell command into simple commands, each a list of words with
// quotes removed. Commands inside $( ) and backticks count as their own, and
// heredoc bodies are skipped: a commit message mentioning --no-verify is text,
// not a flag. Not a full shell parser; it errs toward seeing a commit.
export function simpleCommands(src) {
  const commands = [];
  let i = 0;

  function backticks() {
    let end = i;
    while (end < src.length && src[end] !== "`")
      end += src[end] === "\\" ? 2 : 1;
    commands.push(...simpleCommands(src.slice(i, end)));
    i = end + 1;
  }

  function doubleQuoted() {
    let text = "";
    while (i < src.length && src[i] !== '"') {
      if (src[i] === "\\" && '"\\$`\n'.includes(src[i + 1])) {
        text += src[i + 1];
        i += 2;
      } else if (src[i] === "$" && src[i + 1] === "(") {
        i += 2;
        parse(true);
        text += "$()";
      } else if (src[i] === "`") {
        i += 1;
        backticks();
        text += "``";
      } else {
        text += src[i];
        i += 1;
      }
    }
    i += 1;
    return text;
  }

  function parse(inSubstitution) {
    let words = [];
    let word = null;
    let dropNext = false;
    const heredocs = [];
    const endWord = () => {
      if (word !== null && !dropNext) words.push(word);
      if (word !== null) dropNext = false;
      word = null;
    };
    const endCommand = () => {
      endWord();
      if (words.length > 0) commands.push(words);
      words = [];
    };
    const skipHeredocs = () => {
      for (const { delimiter, tabs } of heredocs.splice(0)) {
        while (i < src.length) {
          let end = src.indexOf("\n", i);
          if (end < 0) end = src.length;
          const line = src.slice(i, end);
          i = end + 1;
          if ((tabs ? line.replace(/^\t+/, "") : line) === delimiter) break;
        }
      }
    };
    while (i < src.length) {
      const c = src[i];
      if (c === "\\") {
        if (src[i + 1] !== "\n") word = (word ?? "") + (src[i + 1] ?? "");
        i += 2;
      } else if (c === "'") {
        let end = src.indexOf("'", i + 1);
        if (end < 0) end = src.length;
        word = (word ?? "") + src.slice(i + 1, end);
        i = end + 1;
      } else if (c === '"') {
        i += 1;
        word = (word ?? "") + doubleQuoted();
      } else if (c === "$" && src[i + 1] === "(") {
        i += 2;
        parse(true);
        word = (word ?? "") + "$()";
      } else if (c === "`") {
        i += 1;
        backticks();
        word = (word ?? "") + "``";
      } else if (c === ")" && inSubstitution) {
        i += 1;
        endCommand();
        return;
      } else if (c === "#" && word === null) {
        while (i < src.length && src[i] !== "\n") i += 1;
      } else if (c === "\n") {
        endCommand();
        i += 1;
        skipHeredocs();
      } else if (c === "<" && src[i + 1] === "<" && src[i + 2] !== "<") {
        endWord();
        i += 2;
        const tabs = src[i] === "-";
        if (tabs) i += 1;
        while (src[i] === " " || src[i] === "\t") i += 1;
        let delimiter = "";
        while (i < src.length && !/[\s;&|()<>]/.test(src[i])) {
          if (src[i] === "'" || src[i] === '"') {
            const quote = src[i];
            let end = src.indexOf(quote, i + 1);
            if (end < 0) end = src.length;
            delimiter += src.slice(i + 1, end);
            i = end + 1;
          } else {
            if (src[i] === "\\") i += 1;
            delimiter += src[i] ?? "";
            i += 1;
          }
        }
        heredocs.push({ delimiter, tabs });
      } else if (c === "<" || c === ">") {
        // A redirection target is a file name, never an option.
        endWord();
        while (src[i] === "<" || src[i] === ">") i += 1;
        if (src[i] === "&") i += 1;
        dropNext = true;
      } else if (";&|()".includes(c)) {
        endCommand();
        i += 1;
      } else if (/\s/.test(c)) {
        endWord();
        i += 1;
      } else {
        word = (word ?? "") + c;
        i += 1;
      }
    }
    endCommand();
  }

  parse(false);
  return commands;
}

// git's global options that take the next word as their value.
const GIT_WITH_VALUE = [
  "-C",
  "-c",
  "--git-dir",
  "--work-tree",
  "--namespace",
  "--config-env",
  "--super-prefix",
];
// git commit's options that take the next word as their value, so a message
// that starts with "-n" is not read as the flag.
const SHORT_WITH_VALUE = "mFcCt";
const LONG_WITH_VALUE = [
  "--message",
  "--file",
  "--reedit-message",
  "--reuse-message",
  "--template",
  "--author",
  "--date",
  "--cleanup",
  "--fixup",
  "--squash",
  "--trailer",
  "--pathspec-from-file",
];
const overridesHooks = (setting) => /^core\.hookspath=/i.test(setting);

// { commit, bypasses }: whether the command runs git commit, and every way
// it skips the hooks.
export function inspect(command) {
  const result = { commit: false, bypasses: [] };
  for (const words of simpleCommands(command)) {
    const bypasses = [];
    let k = 0;
    while (k < words.length) {
      if (/^[A-Za-z_][A-Za-z0-9_]*=/.test(words[k])) {
        if (words[k] === "HUSKY=0") bypasses.push("HUSKY=0");
      } else if (words[k] !== "env" && words[k] !== "command") {
        break;
      }
      k += 1;
    }
    if (!/(^|\/)git$/.test(words[k] ?? "")) continue;
    for (k += 1; k < words.length && words[k].startsWith("-"); k += 1) {
      const [name, value] = words[k].split(/=(.*)/s);
      const setting =
        value ?? (GIT_WITH_VALUE.includes(name) ? words[++k] : undefined);
      if (
        (name === "-c" || name === "--config-env") &&
        overridesHooks(setting ?? "")
      ) {
        bypasses.push(`-c ${setting}`);
      }
    }
    if (words[k] !== "commit") continue;
    result.commit = true;
    let noVerify = null;
    for (let j = k + 1; j < words.length; j += 1) {
      const word = words[j];
      if (word === "--") break;
      if (word.startsWith("--")) {
        const name = word.split("=")[0];
        // git accepts any unambiguous prefix; --no-ve could still be --no-verbose.
        if (
          name.length >= "--no-veri".length &&
          "--no-verify".startsWith(name)
        ) {
          noVerify = word;
        } else if (name === "--verify") {
          noVerify = null;
        } else if (!word.includes("=") && LONG_WITH_VALUE.includes(name)) {
          j += 1;
        }
      } else if (word.startsWith("-")) {
        for (let p = 1; p < word.length; p += 1) {
          if (word[p] === "n") noVerify = "-n";
          if (SHORT_WITH_VALUE.includes(word[p])) {
            if (p === word.length - 1) j += 1;
            break;
          }
          // -S and -u take an optional value attached to the flag.
          if (word[p] === "S" || word[p] === "u") break;
        }
      }
    }
    if (noVerify) bypasses.push(noVerify);
    result.bypasses.push(...bypasses);
  }
  return result;
}

function hooksPath(dir) {
  try {
    return execFileSync("git", ["config", "--local", "core.hooksPath"], {
      cwd: dir,
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
  } catch {
    return null;
  }
}

function refuse(message) {
  process.stderr.write(`${message}\n`);
  process.exit(2);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const payload = JSON.parse(readFileSync(0, "utf8"));
  const command = payload?.tool_input?.command;
  if (typeof command !== "string") {
    refuse("guard-commit: no command in the hook input, so it is refused.");
  }
  const { commit, bypasses } = inspect(command);
  if (!commit) process.exit(0);
  if (bypasses.length > 0) {
    refuse(
      `git commit refused: ${bypasses.join(", ")} skips the husky hooks (commitlint and pnpm validate, the checks CI runs). Commit without it and fix what the hooks report. If a hook cannot run, run \`pnpm install\`.`,
    );
  }
  const dir = process.env.CLAUDE_PROJECT_DIR || payload.cwd || ".";
  const current = hooksPath(dir);
  if (current !== HOOKS_PATH) {
    const found = current === null ? "unset or unreadable" : `"${current}"`;
    refuse(
      `git commit refused: core.hooksPath is ${found}, not ${HOOKS_PATH}, so the husky hooks (commitlint and pnpm validate) would not run. Run \`pnpm install\` in ${dir}, then commit again.`,
    );
  }
}
