---
name: hermes-ios-shell
description: "Modify the Hermes iOS app shell, bridge, and gestures."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [ios, capacitor, wkwebview, mobile, hermes-desktop, renderer, gesture, ipa]
    category: software-development
    related_skills: [hermes-desktop-plugins, github]
---

# Hermes iOS Shell — Development Guide

Modify and extend the Hermes Agent iOS app: a Capacitor/WKWebView shell that
wraps the desktop React renderer in **remote-gateway-only mode**. There is no
local backend — the app connects to a Hermes gateway over REST + WebSocket.

## When to Use

- The user asks to modify the Hermes iOS app (UI, gestures, ergonomics, features)
- You need to understand the iOS branch structure or the bridge layer
- You need to trigger or debug the IPA build workflow
- You want to add mobile-specific UX patterns (swipe, drawers, keyboard awareness)

## Repo Structure

The iOS code lives in the `Jefedi/hermes-agent` fork, on branch
`claude/hermes-gateway-ios-app-r8k0hi`. Key paths:

```
apps/desktop/src/ios/
  ├── bridge.ts       — window.hermesDesktop implementation (REST + WS, 55KB+)
  ├── ios.css         — safe-area insets, touch behaviors, mobile ergonomics
  ├── main.tsx        — iOS entry point (imports bridge + gestures + keyboard before ../main)
  ├── ios-gestures.ts — touch gesture layer (edge swipe, scrim tap, drawer close)
  └── ios-keyboard.ts — visualViewport keyboard tracking, composer offset

apps/ios/
  ├── README.md              — how it works, first run, building, layout
  ├── capacitor.config.json  — app id, webDir, CapacitorHttp
  ├── package.json           — iOS app version
  └── ios/App/               — Xcode project (committed)
      ├── App.xcodeproj/
      ├── App/AppDelegate.swift
      ├── App/SafeAreaViewController.swift  — safe-area confinement + biometric lock
      ├── App/Info.plist
      └── Podfile

apps/desktop/
  ├── ios.html               — Vite entry for the iOS build
  ├── vite.ios.config.ts     — Vite config (separate outDir: dist-ios)
  └── src/store/layout.ts    — $sidebarOpen, $fileBrowserOpen, PANE_TOGGLE_REVEAL_EVENT

.github/workflows/ios-ipa.yml — GitHub Actions IPA build (macos-15, unsigned)
```

## Architecture

### How the iOS shell works

The desktop renderer talks to Electron via `window.hermesDesktop`. On iOS,
`bridge.ts` installs a browser-side implementation of that same interface:

- `api()` → `fetch()` against the gateway base URL with `X-Hermes-Session-Token`
- `getGatewayWsUrl()` → WebSocket URL with `?token=` or single-use `?ticket=`
- `terminal` → PTY-over-WebSocket at `/api/pty` (remote terminal)
- `notify()` → `Capacitor.nativePromise('LocalNotifications', ...)`
- `biometric` → Face ID / Touch ID via `window.__hermesBiometric` (native injection)
- `setKeepAwake()` → Screen Wake Lock API (iOS 16.4+)

The bridge advertises `gatewayOnly: true`, which hides Local and Cloud
connection cards in Settings.

### Pane reveal mechanism

Below 768px viewport, sidebars become overlays. The existing system uses:
- `SIDEBAR_COLLAPSE_MEDIA_QUERY = '(max-width: 768px)'`
- `PANE_TOGGLE_REVEAL_EVENT = 'hermes:pane-toggle-reveal'` (CustomEvent)
- `revealNarrowPane(id, mode)` in `store/layout.ts` dispatches the event
- The layout tree's narrow overlays listen and slide panes over the grid

Gesture layers and CSS can hook into this without modifying React components.

### IPA build workflow

`.github/workflows/ios-ipa.yml`:
- Trigger: `workflow_dispatch` or push to iOS-relevant paths
- Runner: `macos-15`, timeout 45 min
- Builds web bundle (`npm run build:ios`), syncs Capacitor (`npx cap sync ios`)
- Archives unsigned via `xcodebuild` (CODE_SIGNING_ALLOWED=NO)
- Packages `.ipa` manually (zip Payload/)
- Uploads as artifact `hermes-ios-unsigned-ipa` (30-day retention)
- Intended for sideloading via AltStore / Sideloadly / TrollStore

## How to Modify

### 1. Clone the fork and checkout the iOS branch

```bash
git clone --depth 1 https://github.com/Jefedi/hermes-agent.git
cd hermes-agent
git fetch origin --depth 1 claude/hermes-gateway-ios-app-r8k0hi:refs/heads/claude/hermes-gateway-ios-app-r8k0hi
git checkout claude/hermes-gateway-ios-app-r8k0hi
```

### 2. Make changes

Edit files under `apps/desktop/src/ios/` (bridge, CSS, gestures, keyboard) or
`apps/ios/` (Capacitor config, Xcode project, Swift native code).

### 3. Commit and push

```bash
git config user.name "Jefedi"
git config user.email "jefedi@users.noreply.github.com"
git add apps/desktop/src/ios/ apps/ios/
git commit -m "feat(ios): description of change"
git push origin claude/hermes-gateway-ios-app-r8k0hi
```

The push auto-triggers the IPA workflow if iOS-relevant paths changed.

### 4. Monitor the build

Check `https://api.github.com/repos/Jefedi/hermes-agent/actions/runs?branch=claude/hermes-gateway-ios-app-r8k0hi&per_page=5`
or browse to `https://github.com/Jefedi/hermes-agent/actions`.

Download the IPA from the Actions → Artifacts tab once the run completes.

## Mobile UX Patterns (from Apple HIG + industry research)

When adding mobile ergonomics, follow these principles:

### Touch targets
- Minimum 44x44px (Apple HIG), 48px (Material) — use 44px as floor
- Apply via CSS: `min-width` / `min-height` on interactive elements

### Gestures
- **Edge swipe** is the iOS-native pattern for opening drawers (ChatGPT, Mail, Notes)
- Implement via `touchstart`/`touchmove`/`touchend` on `document` (passive listeners)
- Thresholds: 50px min distance, 600ms max duration, 60px max vertical drift
- Velocity shortcut: flick > 0.4px/ms qualifies even under 50px
- Edge zone: 28px from screen edge
- Dispatch existing `PANE_TOGGLE_REVEAL_EVENT` — no React changes needed

### Drawers
- Width: `min(85vw, 320px)` — keeps main content partially visible for context
- Slide transition: `transform 0.28s cubic-bezier(0.32, 0.72, 0, 1)` (iOS curve)
- Scrim backdrop: `rgba(0,0,0,0.4)` with fade-in animation
- Tap on scrim → close drawer

### Composer (message input)
- `font-size: 16px` on textarea — prevents iOS auto-zoom on focus
- Bottom-anchored with safe-area padding
- `max-height: 35dvh` (grows with content)
- Track `visualViewport` API for keyboard height → offset composer via CSS var

### Keyboard awareness
- `window.visualViewport.resize` fires when keyboard opens/closes
- Keyboard height = `window.innerHeight - visualViewport.height`
- Ignore diffs < 100px (browser chrome adjustments)
- Set `--keyboard-height` CSS var on `<body>` for composer offset
- Scroll message list to bottom on keyboard open

## Pitfalls

- **LiveContainer notifications**: iOS rejects notification registration for
  apps hosted inside LiveContainer (UNErrorDomain error 1). Only a real signed
  install (AltStore/Sideloadly) fixes this — it's structural, not a code bug.
- **Keychain stalls**: `capacitor-secure-storage-plugin` can hang inside host
  containers. Wrap every call in a 4s timeout. Never gate boot on Keychain
  migration — run it in the background.
- **WKWebView safe area**: The webview stretches edge-to-edge by default.
  `SafeAreaViewController` must re-parent the webview into a container and pin
  it to `safeAreaLayoutGuide`. CSS `env(safe-area-inset-*)` alone can't save
  fixed-position chrome.
- **Background WebView freeze**: iOS freezes backgrounded WebView (timers stop,
  WS drops). Use Wake Lock API + `visibilitychange` listener to nudge reconnect
  on foreground.
- **OAuth in WebView**: Session cookies can't ride cross-site fetch from
  `capacitor://localhost`. Use the `/app-connect` flow: navigate the app's own
  WebView to the gateway login, redirect back with token in URL fragment.
- **CapacitorHttp**: Enable in `capacitor.config.json` so REST requests go
  through native URLSession — bypasses the gateway's localhost-only CORS.
- **gh CLI not available**: Use the GitHub REST API via `web_extract` against
  `https://api.github.com/repos/Jefedi/hermes-agent/...` (no auth for public repos).

## Verification

- Push triggers the IPA workflow (check Actions tab or API)
- IPA artifact downloads as `hermes-ios-unsigned-ipa`
- Sideload via AltStore/Sideloadly and test on device
- Browser preview: `npm run --prefix apps/desktop build:ios` + serve `dist-ios/`

## References

- `references/mobile-ux-research.md` — condensed Apple HIG findings, competitor
  patterns (ChatGPT iOS, Apple Mail, Claude.ai), and CSS implementation notes
  for touch targets, drawer transitions, safe area, and keyboard tracking.