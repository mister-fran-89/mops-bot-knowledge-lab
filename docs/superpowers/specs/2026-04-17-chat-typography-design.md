# Chat Typography & Code Block Improvements

Improve chat message readability: fix text proportions, add code blocks with copy, fix bugs, widen tables, and enable Tailwind Typography.

## Problem

Agent responses in chat are hard to read and use:
- Code blocks render as unstyled text — no background, no copy button, no language label
- Heading sizes are disproportionate (h1/h2 jump to 24px while body is 14px)
- `inlineStyles.tsx` has literal string bugs (`'PARAGRAPH_SIZES.lead'` instead of the variable) on lines 67, 78, 85
- Tables are capped at 560px, clipping wider SQL results
- `prose` classes are applied in `MarkdownRenderer.tsx` but `@tailwindcss/typography` is not installed, so they do nothing

## Changes

### 1. Install `@tailwindcss/typography`

**File: `ui/package.json`** — `npm install @tailwindcss/typography`

**File: `ui/tailwind.config.ts`** — Add the plugin:
```ts
plugins: [tailwindcssAnimate, require('@tailwindcss/typography')]
```

Customize prose in `theme.extend.typography` to match the dark UI palette:
- Prose body color: `#FAFAFA` (primary)
- Prose headings color: `#FAFAFA` (primary)
- Prose code color: `#FAFAFA` (primary)
- Prose links color: `#FAFAFA` with underline
- Prose bold: `#FAFAFA`
- Prose counters/bullets: `#A1A1AA` (muted)
- Prose hr/borders: `rgba(255,255,255,0.2)` (border)
- Prose pre background: `#27272A` (background-secondary)
- Font size: `sm` variant (`prose-sm`) to keep text proportionate in chat

**File: `ui/src/components/ui/typography/MarkdownRenderer/MarkdownRenderer.tsx`** — Update className:
```
prose prose-sm dark:prose-invert flex w-full flex-col gap-y-5 rounded-lg
```
(Change `prose-h1:text-xl` to rely on the custom component sizes instead.)

### 2. Code block component

**File: `ui/src/components/ui/typography/MarkdownRenderer/styles.tsx`**

Add a `CodeBlock` component that handles the `pre` element. React-markdown wraps fenced code in `<pre><code>`. The component:

- Extracts the language from the child `<code>` element's `className` (format: `language-sql`)
- Renders a container with:
  - `bg-background-secondary` background, `rounded-lg`, `border border-border`
  - A header bar with the language label (left, `text-xs text-muted uppercase font-dmmono`) and a copy button (right)
  - The code content in `font-dmmono text-xs` with `overflow-x-auto` for horizontal scroll
  - `p-4` padding on the code area
- Copy button uses `navigator.clipboard.writeText(codeText)` and toggles icon from clipboard to check for 2 seconds
- Uses `useState` for copied state — no external dependencies

Update the existing `InlineCode` component to only handle inline code (single backticks). Distinguish by checking: if `code` is inside a `pre`, it's a block; otherwise it's inline. Implement this by:
- Mapping `pre` to `CodeBlock` in the components object
- Keeping `code` mapped to `InlineCode` (react-markdown passes block code through `pre` first, so `InlineCode` only fires for inline usage)

Add to the components export:
```ts
pre: CodeBlock,
code: InlineCode,  // already exists, no change
```

### 3. Heading proportions

**File: `ui/src/components/ui/typography/MarkdownRenderer/styles.tsx`**

Change heading components to use tighter sizes for chat context:

| Element | Current | New |
|---------|---------|-----|
| h1 | `HEADING_SIZES[3]` (24px) | `text-lg font-semibold font-inter` (18px) |
| h2 | `HEADING_SIZES[3]` (24px) | `text-base font-semibold font-inter` (16px) |
| h3 | `PARAGRAPH_SIZES.lead` (18px) | `text-sm font-semibold font-inter` (14px) |
| h4 | `PARAGRAPH_SIZES.lead` (18px) | `text-sm font-semibold font-inter` (14px) |
| h5 | `PARAGRAPH_SIZES.title` (14px) | `text-sm font-medium font-inter` (14px, no change) |
| h6 | `PARAGRAPH_SIZES.title` (14px) | `text-sm font-medium font-inter` (14px, no change) |

### 4. Inline style bugs

**File: `ui/src/components/ui/typography/MarkdownRenderer/inlineStyles.tsx`**

Fix three lines where the variable is quoted as a literal string:

- Line 67: `'PARAGRAPH_SIZES.lead'` → `PARAGRAPH_SIZES.lead`
- Line 78: `'PARAGRAPH_SIZES.lead'` → `PARAGRAPH_SIZES.lead`
- Line 85: `'PARAGRAPH_SIZES.lead'` → `PARAGRAPH_SIZES.lead`

### 5. Table width

**File: `ui/src/components/ui/typography/MarkdownRenderer/styles.tsx`**

Change table wrapper:
```
max-w-[560px]  →  max-w-full
```

This lets tables use the full chat container width (max-w-2xl = 672px from the parent).

## Risk Mitigation

- **Typography plugin conflicts:** Custom components in the `components` object fully replace their HTML elements in react-markdown, so prose only provides baseline rhythm and spacing for elements we don't override. Using `prose-sm` keeps the base size at 14px, matching existing body text.
- **Code block edge cases:** The `pre`/`code` split is react-markdown's standard pattern. Block code always wraps in `<pre><code>`, inline code renders `<code>` alone. No ambiguity.
- **Heading size reduction:** Going from 24px to 18px for h1 is significant. But in a chat context where body text is 14px, 18px headings provide clear hierarchy without dominating.

## Out of Scope

- Syntax highlighting (no shiki/prism — plain monospace is sufficient for now)
- Mobile-specific adjustments
- Message spacing or chat container width changes
- Changes to inline mode styles beyond the bug fixes
