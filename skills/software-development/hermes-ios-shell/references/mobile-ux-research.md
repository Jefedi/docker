# Mobile UX Reference — iOS Shell Ergonomics

Condensed findings from Apple HIG, industry research, and competitor analysis
(ChatGPT iOS, Apple Mail, Notes) used to design the Hermes iOS shell ergonomics.

## Apple HIG — Designing for iOS

Source: developer.apple.com/design/human-interface-guidelines/designing-for-ios

- **Ergonomics**: People hold iPhone in one or both hands. Place frequently
  used controls in the middle or bottom of the display. Let people swipe to
  navigate back or initiate actions in list rows.
- **Gestures**: Multi-Touch gestures are the primary interaction. Support
  interactions that accommodate how people hold the device.
- **Focus**: Limit onscreen controls. Make secondary details discoverable with
  minimal interaction.
- **Adaptability**: Adapt to Dark Mode, Dynamic Type, orientation changes.

## Gesture-Based Navigation (2025 trends)

- Swipe gestures, edge gestures, and invisible transitions now dominate over
  button-based layouts (LinkedIn, Fora Soft, Medium 2025).
- Home indicators replaced the home button; swipe-back, swipe-up, and edge
  gestures are the default on both iOS and Android.
- Apps that place back buttons where system gestures collide generate mis-taps.
- Gestures must be **discoverable** — provide visual cues (edge hints,
  partial reveals) so users learn the interaction.

## Competitor Patterns

### ChatGPT iOS
- Swipe from left edge opens conversation list sidebar
- Sidebar slides in as a drawer with scrim backdrop
- Haptic feedback on open/close
- Composer docked at bottom, full-width
- Send button large, high-contrast, thumb-reachable

### Apple Mail / Notes
- Drawer pattern: 85% width, main content partially visible behind scrim
- Smooth slide transition with deceleration curve
- Tap scrim to dismiss
- Swipe left/right on list rows for actions

### Claude.ai mobile
- Full-width messages, subtle background shading for user vs assistant
- Composer docked, bottom padding = composer + safe area
- Keyboard pushes layout without jumping
- Send/stop buttons at least 44px tall

## AI Chat Interface Best Practices

Source: setproduct.com/blog/ai-chat-interface-ui-design

- **Mobile layout**: single column, full bleed. Conversation list = slide-in
  drawer behind hamburger or top-left avatar.
- **Composer**: dock at bottom, give message stream bottom padding equal to
  composer + safe area. Let keyboard animation push layout without jumping.
- **Send/stop**: at least 44px tall for thumb reach. High contrast.
- **Messages**: full-width is current best practice. Use subtle background
  shading or alignment to separate user/assistant.
- **Context**: show a clear marker when earlier messages get summarized/dropped.
  Offer "Start new conversation" before degraded replies.
- **Anti-patterns**: floating action buttons that overlap streaming content;
  hiding the composer during generation; no stop button.

## Navigation Pattern Comparison

| Pattern | Pros | Cons | Best for |
|--------|------|------|----------|
| Hamburger menu | Saves screen space | Hidden options, easy to forget | Occasional navigation |
| Tab bar | Always visible, low cognitive load | Limited items (3-5) | Frequent switching |
| Gesture-based | Minimal UI, immersive | Learning curve, accessibility | Content-first apps |
| Drawer + scrim | Spatial context, familiar | Requires discoverability | Chat apps (ChatGPT, Mail) |

**Chosen pattern for Hermes iOS**: Drawer + scrim (sidebar/file-browser as
slide-in overlays) + edge-swipe gestures. Matches ChatGPT iOS and Apple Mail.

## CSS Implementation Notes

### Safe area
```css
--ios-safe-top: env(safe-area-inset-top, 0px);
--ios-safe-bottom: env(safe-area-inset-bottom, 0px);
body { padding: var(--ios-safe-top) var(--ios-safe-right) var(--ios-safe-bottom) var(--ios-safe-left); }
```

### Drawer transition
```css
/* iOS native curve */
transition: transform 0.28s cubic-bezier(0.32, 0.72, 0, 1);
```

### Touch target floor
```css
@media (max-width: 768px) {
  button { min-width: 44px; min-height: 44px; }
}
```

### Anti-zoom on input focus
```css
textarea { font-size: 16px; } /* iOS won't auto-zoom if >= 16px */
```

### Keyboard tracking
```js
window.visualViewport.addEventListener('resize', () => {
  const kbHeight = Math.max(0, window.innerHeight - visualViewport.height)
  document.body.style.setProperty('--keyboard-height', kbHeight + 'px')
})
```