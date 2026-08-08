# Qilive (Vestel) Vidaa + Apple TV — Volume Control Failure

## Setup
- TV: Qilive Q43US251B (Auchan, OEM = Vestel, OS = Hisense Vidaa U)
- Streaming: Apple TV 4K
- Goal: Apple TV remote volume buttons control TV speakers

## What was tried and failed

| Attempt | Result | Why |
|---------|--------|-----|
| Enable HDMI-CEC on TV (Réglages > Connexion > HDMI & CEC) | ❌ | CEC enabled on TV, but Apple TV volume still didn't work |
| Apple TV Volume Control → Auto | ❌ | Defaulted to wrong method |
| Apple TV Volume Control → TV via IR | ❌ | TV may not have an IR receiver, or codes don't match |
| Apple TV Volume Control → Learn New Device | ❌ | Bundled TV remote is Bluetooth — no IR codes to learn |

## Root cause

The Qilive Q43US251B has a **Bluetooth-only remote** (voice control enabled). This means:

1. The TV may not respond to IR volume commands (no IR receiver, or firmware ignores IR for volume)
2. The "Learn New Device" Apple TV feature requires IR emissions from the TV remote — impossible with Bluetooth
3. HDMI-CEC volume control may be broken or unsupported in Vestel's Vidaa firmware

## Recommended resolution

**Option A** (easiest): Accept using the Qilive remote for volume, Apple TV remote for everything else.

**Option B**: Add an **external IR blaster** (e.g. SwitchBot Hub Mini) that bridges Apple TV → IR → TV.

**Option C**: Add a **soundbar via HDMI ARC** — soundbar handles audio, Apple TV remote controls soundbar via CEC (soundbars generally have better CEC compliance than entry-level TVs).

## Sources consulted

- Apple Support (108769): Volume button troubleshooting
- Apple Support (atvbbe2477c9): tvOS remote control guide
- Hisense Vidaa manual (manuelsys.pdf): CEC activation path
- Apple Community thread 251720875: Hisense volume + Learn New Device
- ComputerBase forum: Apple TV → TV = IR only for volume, not CEC
- Frandroid: Vidaa OS settings overview
- Dealabs confirmation: Qilive Q50US251B = Vestel OEM with Vidaa OS
