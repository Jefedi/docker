# Dynamic Form Pattern — Conditional Form Sections

When a form needs to show/hide different sections based on a type selector (e.g. "À la boîte" vs "Déplacement"), use this pattern.

## HTML Structure

```html
<!-- Type selector buttons -->
<div class="type-selector">
    <div class="type-btn active" id="btn-typeA" onclick="selectType('typeA')">Type A</div>
    <div class="type-btn" id="btn-typeB" onclick="selectType('typeB')">Type B</div>
</div>
<input type="hidden" name="jour_type" id="jour_type" value="typeA">

<!-- Common fields (always visible) -->
<div class="row">
    <div class="field">
        <label>Heure début</label>
        <input type="time" name="heure_debut">
    </div>
    <div class="field">
        <label>Heure fin</label>
        <input type="time" name="heure_fin">
    </div>
</div>

<!-- Type A fields -->
<div class="typeA-fields" id="typeA-fields">
    <!-- fields specific to type A -->
</div>

<!-- Type B fields -->
<div class="typeB-fields" id="typeB-fields" style="display:none">
    <!-- fields specific to type B -->
</div>
```

## JavaScript

```javascript
function selectType(type) {
    // Set hidden input
    document.getElementById('jour_type').value = type;
    
    // Toggle active state on buttons
    document.getElementById('btn-typeA').classList.toggle('active', type === 'typeA');
    document.getElementById('btn-typeB').classList.toggle('active', type === 'typeB');
    
    // Show/hide field sections
    document.getElementById('typeA-fields').style.display = type === 'typeA' ? 'block' : 'none';
    document.getElementById('typeB-fields').style.display = type === 'typeB' ? 'block' : 'none';
}

// Initialize from server-rendered value
const initialType = document.getElementById('jour_type').value;
selectType(initialType);
```

## CSS

```css
.type-selector { display: flex; gap: 12px; margin-bottom: 20px; }
.type-btn {
    flex: 1; padding: 16px; border-radius: 10px;
    border: 2px solid var(--border); background: var(--bg);
    color: var(--muted); cursor: pointer; text-align: center;
    transition: all .2s;
}
.type-btn.active {
    border-color: var(--accent);
    color: var(--accent);
    background: rgba(79, 158, 255, 0.1);
}
```

## Key Points

- Use a **hidden input** to carry the selected type to the server (buttons are divs, not radio buttons)
- Initialize the form state from the server-rendered value (for edit/modification pages)
- Use `style.display` or class toggling — both work, class toggling allows CSS transitions
- Server-side: only process fields relevant to the selected type (ignore the others)