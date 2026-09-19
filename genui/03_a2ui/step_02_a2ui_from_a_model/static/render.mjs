// A hand-written painter for part of the Basic Catalog. It reads a Surface
// (surface.mjs) and builds DOM; nothing here parses messages.
//
// Card, Column, Row, Text, TextField, Button, CheckBox are the seven from the
// step brief. Icon, Divider and ChoicePicker are small extras the spec's
// contact form uses. Anything else renders as a labelled box.

function el(tag, className, ...children) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  for (const child of children) if (child != null) node.append(child);
  return node;
}

function text(surface, value) {
  const resolved = surface.resolve(value);
  return resolved == null ? '' : typeof resolved === 'object' ? JSON.stringify(resolved) : String(resolved);
}

// "Supports simple Markdown": the fallback the catalog guide allows is to strip the markers.
function plain(markdown) {
  return markdown.replace(/^#+\s*/, '').replaceAll('**', '');
}

const RENDERERS = {
  Card(ctx, c) {
    return el('div', 'a2ui-card', ctx.paint(c.child));
  },
  Column(ctx, c) {
    const node = el('div', 'a2ui-column', ...ctx.paintAll(c.children));
    node.style.justifyContent = FLEX[c.justify] ?? 'flex-start';
    node.style.alignItems = FLEX[c.align] ?? 'stretch';
    return node;
  },
  Row(ctx, c) {
    const node = el('div', 'a2ui-row', ...ctx.paintAll(c.children));
    node.style.justifyContent = FLEX[c.justify] ?? 'flex-start';
    node.style.alignItems = FLEX[c.align] ?? 'center';
    return node;
  },
  Text(ctx, c) {
    const variant = c.variant ?? 'body';
    const tag = /^h[1-5]$/.test(variant) ? variant : variant === 'caption' ? 'small' : 'p';
    return el(tag, `a2ui-text a2ui-${variant}`, plain(text(ctx.surface, c.text)));
  },
  TextField(ctx, c) {
    const input = el('input', 'a2ui-input');
    input.type = c.variant === 'obscured' ? 'password' : c.variant === 'number' ? 'number' : 'text';
    input.placeholder = text(ctx.surface, c.label);
    input.value = text(ctx.surface, c.value);
    input.dataset.field = c.id;
    if (c.value?.path) input.oninput = () => ctx.write(c.value.path, input.value);
    return el('label', 'a2ui-field', el('span', 'a2ui-label', text(ctx.surface, c.label)), input);
  },
  CheckBox(ctx, c) {
    const input = el('input', 'a2ui-checkbox');
    input.type = 'checkbox';
    input.checked = ctx.surface.resolve(c.value) === true;
    if (c.value?.path) input.onchange = () => ctx.write(c.value.path, input.checked);
    return el('label', 'a2ui-check', input, el('span', null, text(ctx.surface, c.label)));
  },
  Button(ctx, c) {
    const button = el('button', `a2ui-button a2ui-${c.variant ?? 'default'}`, ctx.paint(c.child));
    button.type = 'button';
    if (c.action?.event) button.onclick = () => ctx.act(c.id);
    return button;
  },
  Icon(ctx, c) {
    return el('span', 'a2ui-icon', `[${text(ctx.surface, c.name)}]`);
  },
  Divider(ctx, c) {
    return el('hr', `a2ui-divider a2ui-${c.axis ?? 'horizontal'}`);
  },
  ChoicePicker(ctx, c) {
    const single = c.variant === 'mutuallyExclusive';
    const group = el('div', 'a2ui-choices');
    const resolved = ctx.surface.resolve(c.value);
    const selected = Array.isArray(resolved) ? resolved : resolved == null ? [] : [resolved]; // a single value still selects
    for (const option of c.options ?? []) {
      const input = el('input');
      input.type = single ? 'radio' : 'checkbox';
      input.name = c.id;
      input.checked = selected.includes(option.value);
      input.onchange = () => {
        const next = single ? [option.value] : selected.includes(option.value) ? selected.filter((v) => v !== option.value) : [...selected, option.value];
        if (c.value?.path) ctx.write(c.value.path, next);
      };
      group.append(el('label', 'a2ui-choice', input, el('span', null, text(ctx.surface, option.label))));
    }
    return group;
  },
};

const FLEX = { start: 'flex-start', center: 'center', end: 'flex-end', spaceBetween: 'space-between', spaceAround: 'space-around', spaceEvenly: 'space-evenly', stretch: 'stretch' };

export function paintSurface(surface, { onChange, onAction }) {
  const ctx = {
    surface,
    painting: new Set(), // the ids on the way down: a component inside itself is painted once
    paint(id) {
      if (id == null) return null;
      const component = surface.components.get(id);
      if (!component) return el('span', 'a2ui-placeholder', `waiting for ${id}`);
      if (ctx.painting.has(id)) return el('span', 'a2ui-placeholder', `cycle at ${id}`);
      ctx.painting.add(id);
      try {
        const renderer = Object.hasOwn(RENDERERS, component.component) ? RENDERERS[component.component] : null;
        const node = renderer ? renderer(ctx, component) : el('div', 'a2ui-unknown', `${component.component} is not in this renderer`);
        node.dataset.id = id;
        if (component.weight) node.style.flex = String(component.weight);
        return node;
      } finally {
        ctx.painting.delete(id);
      }
    },
    paintAll(children) {
      if (Array.isArray(children)) return children.map((id) => ctx.paint(id));
      if (children && typeof children === 'object') return [el('span', 'a2ui-placeholder', 'template children are not painted here')];
      return [];
    },
    write(path, value) {
      surface.set(path, value);
      onChange?.(surface);
    },
    act(id) {
      onAction?.(surface.action(id));
    },
  };
  const root = el('section', 'a2ui-surface');
  root.dataset.surface = surface.id;
  if (surface.theme.primaryColor) root.style.setProperty('--a2ui-primary', surface.theme.primaryColor);
  root.append(surface.components.has('root') ? ctx.paint('root') : el('p', 'a2ui-placeholder', 'waiting for root'));
  return root;
}

// Paint every surface into the container, keeping focus and caret on the input being edited.
export function paint(store, container, handlers) {
  const active = document.activeElement?.dataset?.field;
  const caret = document.activeElement?.selectionStart;
  container.replaceChildren(...[...store.surfaces.values()].map((s) => paintSurface(s, handlers)));
  if (active) {
    const again = container.querySelector(`[data-field="${active}"]`);
    if (again) {
      again.focus();
      if (caret != null && again.setSelectionRange) again.setSelectionRange(caret, caret);
    }
  }
}
