# reverse-engineering

A [Claude Code](https://claude.com/claude-code) Skill that transforms Claude into a
**senior reverse-engineering and binary-analysis expert** covering static and dynamic
analysis, disassembly, decompilation, executable and file formats, malware triage,
firmware and embedded RE, protocol reversing, mobile app analysis, and RE tooling.

It is scoped to **lawful, authorized** work and adapts automatically to your experience
level while keeping analysis rigorous, reproducible, and safe by default.

## Scope and authorization

Reverse engineering is dual-use. This skill assists only with lawful, authorized work:
malware analysis and detection engineering, vulnerability research on software you may
test, CTF challenges, interoperability and legacy maintenance, debugging, and digital
forensics. It will not help with piracy, weaponizing exploits against third parties, or
evading detection for malicious deployment. When intent is unclear, Claude asks.

## What it does

When active, Claude analyzes, explains, documents, and instruments compiled software and
binary artifacts, with dedicated modes for:

- **Static analysis** — triage, file formats (PE/ELF/Mach-O), disassembly, decompilation
  (Ghidra, IDA, Binary Ninja, radare2/rizin), deobfuscation
- **Dynamic analysis** — debugging (GDB/WinDbg/x64dbg), tracing, Frida, emulation (QEMU,
  Unicorn, angr), sandboxing, memory forensics
- **Malware analysis** — triage → classify → unpack → deep-dive → detonate → IOCs →
  detection rules (YARA/Sigma) → report, mapped to MITRE ATT&CK
- **Firmware / embedded** — `binwalk`/`unblob`, bootloaders, SoC/MCU targets, flash dumping
- **Protocol & network reversing** — Wireshark/tshark, custom dissectors, binary protocols
- **Mobile RE** — Android (apktool, jadx, smali) and iOS (Mach-O, Frida/objection)
- **Safe handling** — isolation, hashing, network sinkholing, defanged indicators

## Installation

### Personal skill (available in all your projects)

```bash
mkdir -p ~/.claude/skills/reverse-engineering
curl -fsSL https://raw.githubusercontent.com/kalandengit/python_learning_projects/main/skills/reverse-engineering/SKILL.md \
  -o ~/.claude/skills/reverse-engineering/SKILL.md
```

### Project skill (single project)

Place `SKILL.md` at `.claude/skills/reverse-engineering/SKILL.md` in the project root,
or run the installer:

```bash
COMMIT=1 PUSH=1 ./scripts/install-reverse-engineering.sh
```

## Usage

Invoke explicitly:

```
/reverse-engineering Triage this stripped ELF and identify how it's packed
```

Or just describe an authorized RE task — Claude applies the skill automatically when a
request calls for binary analysis, malware triage, disassembly, or reverse engineering.

## License

MIT
