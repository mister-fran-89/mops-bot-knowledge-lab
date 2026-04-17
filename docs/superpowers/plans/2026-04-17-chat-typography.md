# Chat Typography & Code Block Improvements — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix chat message readability — add code blocks with copy, fix text proportions, fix inline style bugs, widen tables, install Tailwind Typography.

**Architecture:** Five surgical changes to the existing MarkdownRenderer system. One new dependency (`@tailwindcss/typography`), one new component (`CodeBlock`), and targeted fixes to three existing files. No new files created — all changes are in-place.

**Tech Stack:** Next.js 15, Tailwind CSS, `@tailwindcss/typography`, `react-markdown`, `lucide-react` (already installed), `framer-motion` (already installed)

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `ui/package.json` | Modify | Add `@tailwindcss/typography` dependency |
| `ui/tailwind.config.ts` | Modify | Add typography plugin + prose theme customization |
| `ui/src/components/ui/typography/MarkdownRenderer/MarkdownRenderer.tsx` | Modify | Update prose classes |
| `ui/src/components/ui/typography/MarkdownRenderer/styles.tsx` | Modify | Add CodeBlock, fix headings, widen tables |
| `ui/src/components/ui/typography/MarkdownRenderer/inlineStyles.tsx` | Modify | Fix literal string bugs |

---

### Task 1: Install `@tailwindcss/typography` and configure plugin

**Files:**
- Modify: `ui/package.json`
- Modify: `ui/tailwind.config.ts`

- [ ] **Step 1: Install the dependency**

Run from the `ui/` directory:
```bash
cd ui && npm install @tailwindcss/typography
```

Expected: package.json updated, `@tailwindcss/typography` appears in dependencies.

- [ ] **Step 2: Add plugin and prose theme to tailwind config**

In `ui/tailwind.config.ts`, add the import and plugin registration, plus a custom prose theme that matches the dark UI:

```ts
import type { Config } from 'tailwindcss'
import tailwindcssAnimate from 'tailwindcss-animate'
import typography from '@tailwindcss/typography'

export default {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}'
  ],
  theme: {
    extend: {
      colors: {
        primary: '#FAFAFA',
        primaryAccent: '#18181B',
        brand: '#FF4017',
        background: {
          DEFAULT: '#111113',
          secondary: '#27272A'
        },
        secondary: '#f5f5f5',
        border: 'rgba(var(--color-border-default))',
        accent: '#27272A',
        muted: '#A1A1AA',
        destructive: '#E53935',
        positive: '#22C55E'
      },
      fontFamily: {
        geist: 'var(--font-geist-sans)',
        dmmono: 'var(--font-dm-mono)'
      },
      borderRadius: {
        xl: '10px'
      },
      typography: {
        DEFAULT: {
          css: {
            '--tw-prose-body': '#FAFAFA',
            '--tw-prose-headings': '#FAFAFA',
            '--tw-prose-bold': '#FAFAFA',
            '--tw-prose-links': '#FAFAFA',
            '--tw-prose-code': '#FAFAFA',
            '--tw-prose-counters': '#A1A1AA',
            '--tw-prose-bullets': '#A1A1AA',
            '--tw-prose-hr': 'rgba(255, 255, 255, 0.2)',
            '--tw-prose-th-borders': 'rgba(255, 255, 255, 0.2)',
            '--tw-prose-td-borders': 'rgba(255, 255, 255, 0.2)',
            '--tw-prose-pre-bg': '#27272A',
            '--tw-prose-pre-code': '#FAFAFA',
            '--tw-prose-quotes': '#A1A1AA',
            '--tw-prose-quote-borders': 'rgba(255, 255, 255, 0.2)',
          }
        }
      }
    }
  },
  plugins: [tailwindcssAnimate, typography]
} satisfies Config
```

- [ ] **Step 3: Update MarkdownRenderer prose classes**

In `ui/src/components/ui/typography/MarkdownRenderer/MarkdownRenderer.tsx`, change the className:

Replace:
```
'prose prose-h1:text-xl dark:prose-invert flex w-full flex-col gap-y-5 rounded-lg'
```

With:
```
'prose prose-sm dark:prose-invert flex w-full flex-col gap-y-5 rounded-lg'
```

- [ ] **Step 4: Verify the build compiles**

```bash
cd ui && npx tsc --noEmit 2>&1 | grep -E "tailwind|typography|MarkdownRenderer" | head -10
```

Expected: No errors related to these files.

- [ ] **Step 5: Commit**

```bash
git add ui/package.json ui/package-lock.json ui/tailwind.config.ts ui/src/components/ui/typography/MarkdownRenderer/MarkdownRenderer.tsx
git commit -m "feat(ui): install @tailwindcss/typography and configure dark prose theme"
```

---

### Task 2: Add CodeBlock component with copy button

**Files:**
- Modify: `ui/src/components/ui/typography/MarkdownRenderer/styles.tsx`

- [ ] **Step 1: Add imports for useState and lucide icons**

At the top of `styles.tsx`, update the import from `react`:

Replace:
```ts
import { FC, useState } from 'react'
```

With:
```ts
import { FC, useState, ReactElement, isValidElement } from 'react'
```

Add lucide import after the existing imports:
```ts
import { Clipboard, Check } from 'lucide-react'
```

- [ ] **Step 2: Add the CodeBlock component**

Add this component after the `InlineCode` component (after line 130) and before the `Blockquote` component:

```tsx
const CodeBlock: FC<PreparedTextProps> = ({ children }) => {
  const [copied, setCopied] = useState(false)

  let language = ''
  let codeText = ''

  if (isValidElement(children)) {
    const child = children as ReactElement<{ className?: string; children?: string }>
    const className = child.props?.className || ''
    const match = className.match(/language-(\w+)/)
    if (match) language = match[1]
    codeText = String(child.props?.children || '')
  } else {
    codeText = String(children || '')
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(codeText.replace(/\n$/, ''))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="group relative rounded-lg border border-border bg-background-secondary">
      <div className="flex items-center justify-between px-4 py-2">
        <span className="font-dmmono text-xs uppercase text-muted">
          {language || 'code'}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 text-xs text-muted transition-colors hover:text-primary"
        >
          {copied ? (
            <>
              <Check size={14} />
              <span>Copied</span>
            </>
          ) : (
            <>
              <Clipboard size={14} />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="overflow-x-auto px-4 pb-4">
        <code className="font-dmmono text-xs leading-relaxed">{codeText}</code>
      </pre>
    </div>
  )
}
```

- [ ] **Step 3: Add `pre: CodeBlock` to the components export**

In the `components` export object at the bottom of the file, add `pre: CodeBlock` before the existing `code: InlineCode` line:

Replace:
```ts
  code: InlineCode,
```

With:
```ts
  pre: CodeBlock,
  code: InlineCode,
```

- [ ] **Step 4: Verify the build compiles**

```bash
cd ui && npx tsc --noEmit 2>&1 | grep -E "styles|CodeBlock" | head -10
```

Expected: No errors.

- [ ] **Step 5: Commit**

```bash
git add ui/src/components/ui/typography/MarkdownRenderer/styles.tsx
git commit -m "feat(ui): add CodeBlock component with copy button and language label"
```

---

### Task 3: Fix heading proportions

**Files:**
- Modify: `ui/src/components/ui/typography/MarkdownRenderer/styles.tsx`

- [ ] **Step 1: Update heading components**

In `styles.tsx`, replace the six heading components:

Replace:
```tsx
const Heading1 = ({ className, ...props }: HeadingProps) => (
  <h1 className={cn(className, HEADING_SIZES[3])} {...filterProps(props)} />
)

const Heading2 = ({ className, ...props }: HeadingProps) => (
  <h2 className={cn(className, HEADING_SIZES[3])} {...filterProps(props)} />
)

const Heading3 = ({ className, ...props }: HeadingProps) => (
  <h3 className={cn(className, PARAGRAPH_SIZES.lead)} {...filterProps(props)} />
)

const Heading4 = ({ className, ...props }: HeadingProps) => (
  <h4 className={cn(className, PARAGRAPH_SIZES.lead)} {...filterProps(props)} />
)

const Heading5 = ({ className, ...props }: HeadingProps) => (
  <h5
    className={cn(className, PARAGRAPH_SIZES.title)}
    {...filterProps(props)}
  />
)

const Heading6 = ({ className, ...props }: HeadingProps) => (
  <h6
    className={cn(className, PARAGRAPH_SIZES.title)}
    {...filterProps(props)}
  />
)
```

With:
```tsx
const Heading1 = ({ className, ...props }: HeadingProps) => (
  <h1 className={cn(className, 'text-lg font-semibold font-inter')} {...filterProps(props)} />
)

const Heading2 = ({ className, ...props }: HeadingProps) => (
  <h2 className={cn(className, 'text-base font-semibold font-inter')} {...filterProps(props)} />
)

const Heading3 = ({ className, ...props }: HeadingProps) => (
  <h3 className={cn(className, 'text-sm font-semibold font-inter')} {...filterProps(props)} />
)

const Heading4 = ({ className, ...props }: HeadingProps) => (
  <h4 className={cn(className, 'text-sm font-semibold font-inter')} {...filterProps(props)} />
)

const Heading5 = ({ className, ...props }: HeadingProps) => (
  <h5 className={cn(className, 'text-sm font-medium font-inter')} {...filterProps(props)} />
)

const Heading6 = ({ className, ...props }: HeadingProps) => (
  <h6 className={cn(className, 'text-sm font-medium font-inter')} {...filterProps(props)} />
)
```

- [ ] **Step 2: Remove unused HEADING_SIZES import if no longer used**

Check if `HEADING_SIZES` is still used anywhere in the file. After the heading changes, it is no longer referenced. Remove the import:

Replace:
```ts
import { HEADING_SIZES } from '../Heading/constants'
import { PARAGRAPH_SIZES } from '../Paragraph/constants'
```

With:
```ts
import { PARAGRAPH_SIZES } from '../Paragraph/constants'
```

- [ ] **Step 3: Commit**

```bash
git add ui/src/components/ui/typography/MarkdownRenderer/styles.tsx
git commit -m "fix(ui): tighten heading sizes for chat context"
```

---

### Task 4: Widen table max-width

**Files:**
- Modify: `ui/src/components/ui/typography/MarkdownRenderer/styles.tsx`

- [ ] **Step 1: Change table wrapper max-width**

In `styles.tsx`, in the `Table` component:

Replace:
```tsx
  <div className="w-full max-w-[560px] overflow-hidden rounded-md border border-border">
```

With:
```tsx
  <div className="w-full max-w-full overflow-hidden rounded-md border border-border">
```

- [ ] **Step 2: Commit**

```bash
git add ui/src/components/ui/typography/MarkdownRenderer/styles.tsx
git commit -m "fix(ui): widen table max-width to use full chat container"
```

---

### Task 5: Fix inline style literal string bugs

**Files:**
- Modify: `ui/src/components/ui/typography/MarkdownRenderer/inlineStyles.tsx`

- [ ] **Step 1: Fix EmphasizedText (line 67)**

Replace:
```tsx
const EmphasizedText = ({ className, ...props }: EmphasizedTextProps) => (
  <em
    className={cn(className, 'PARAGRAPH_SIZES.lead')}
    {...filterProps(props)}
  />
)
```

With:
```tsx
const EmphasizedText = ({ className, ...props }: EmphasizedTextProps) => (
  <em
    className={cn(className, PARAGRAPH_SIZES.lead)}
    {...filterProps(props)}
  />
)
```

- [ ] **Step 2: Fix StrongText (line 78)**

Replace:
```tsx
const StrongText = ({ className, ...props }: StrongTextProps) => (
  <strong
    className={cn(className, 'PARAGRAPH_SIZES.lead')}
    {...filterProps(props)}
  />
)
```

With:
```tsx
const StrongText = ({ className, ...props }: StrongTextProps) => (
  <strong
    className={cn(className, PARAGRAPH_SIZES.lead)}
    {...filterProps(props)}
  />
)
```

- [ ] **Step 3: Fix BoldText (line 85)**

Replace:
```tsx
const BoldText = ({ className, ...props }: BoldTextProps) => (
  <b
    className={cn(className, 'PARAGRAPH_SIZES.lead')}
    {...filterProps(props)}
  />
)
```

With:
```tsx
const BoldText = ({ className, ...props }: BoldTextProps) => (
  <b
    className={cn(className, PARAGRAPH_SIZES.lead)}
    {...filterProps(props)}
  />
)
```

- [ ] **Step 4: Commit**

```bash
git add ui/src/components/ui/typography/MarkdownRenderer/inlineStyles.tsx
git commit -m "fix(ui): fix literal string bugs in inline markdown styles"
```

---

### Task 6: Final verification

- [ ] **Step 1: Run TypeScript check**

```bash
cd ui && npx tsc --noEmit
```

Expected: No new errors (pre-existing `inlineStyles.tsx:162` type error in `Img` component is unrelated and acceptable).

- [ ] **Step 2: Start dev server and visually verify**

```bash
cd ui && npm run dev
```

Open `http://localhost:3000`. Select an agent. Send a message that triggers a response with:
- Headings (should be proportionate, not oversized)
- A code block with SQL (should have dark background, language label, copy button)
- A table (should use full width, not clipped)
- Bold/italic text (should render correctly, not unstyled)

- [ ] **Step 3: Test copy button**

Click the copy button on a code block. Paste into a text editor. Verify the code text is copied correctly without the language label or button text.

- [ ] **Step 4: Final commit if any adjustments needed**

If visual testing reveals spacing or color tweaks needed, make them and commit:
```bash
git add -u
git commit -m "fix(ui): adjust typography after visual review"
```
