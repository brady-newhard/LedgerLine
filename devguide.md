
# LedgerLine Beige Edition – ModeUnlock Developer Guide

## ✳️ You Own: The ModeUnlock System
As the ModeUnlock owner, you're responsible for the logic and UX behind unlocking behavioral "modes" such as:

- **Lockdown Mode**: triggered when expenses exceed income
- **Vacay Mode**: triggered by sustained savings
- **Survival Mode**: triggered by intense early-month spending

---

## 🔩 Your Responsibilities

### 1. Model
- `ModeUnlock` model: user, name, description, is_unlocked, triggered_on

### 2. Fixture
- Create and load starter modes via fixture (JSON)

### 3. Logic
- Write `check_and_unlock_modes(user)` helper in `utils.py`
- Implement auto-check via `signals.py` on `Transaction` save

### 4. Dashboard Integration
- Inject active/unlocked modes into dashboard context
- Display current modes with clean, monospace badges
- (Optional) Show celebratory message when a mode is newly unlocked

### 5. Style Consistency
All interface elements must follow the LedgerLine Beige style:

```css
--bg-beige: #f4f1ea;
--accent-beige: #cfc6b8;
--text-primary: #1a1a1a;
--text-muted: #5e5e5e;
--income: #296442;
--expense: #8b2e2e;
--border-gray: #d3d3d3;
font-family: "IBM Plex Mono", monospace;
```

---

##  Expected Folder Structure (mode-related)

```
main_app/
├── templates/
│   └── main_app/
│       ├── dashboard.html
│       └── modeunlock_list.html
├── fixtures/
│   └── modeunlock_fixture.json
├── models.py
├── views.py
├── signals.py
├── utils.py
└── urls.py
```

---

## Example UI Section (dashboard.html)

```html
<div class="mode-badges" style="border:1px solid var(--border-gray); background:var(--bg-beige); padding:10px;">
  <h4 style="margin-bottom:0.5rem;">Unlocked Modes</h4>
  <ul style="margin:0; padding-left:1rem;">
    {% for mode in modes %}
      <li style="color:var(--text-muted); font-family:monospace;">✔ {{ mode.name }}</li>
    {% endfor %}
  </ul>
</div>
```

---

## ✅ Final Tip
Always test mode logic with real transactions. Use Django admin or create simple test cases. Feel free to expand the logic, but all triggers must remain intuitive and delightfully beige.