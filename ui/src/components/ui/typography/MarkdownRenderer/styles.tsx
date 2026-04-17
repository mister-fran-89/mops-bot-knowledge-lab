'use client'

import { FC, useState, ReactElement, isValidElement } from 'react'

import Image from 'next/image'
import Link from 'next/link'
import { Clipboard, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

import type {
  UnorderedListProps,
  OrderedListProps,
  EmphasizedTextProps,
  ItalicTextProps,
  StrongTextProps,
  BoldTextProps,
  DeletedTextProps,
  UnderlinedTextProps,
  HorizontalRuleProps,
  BlockquoteProps,
  AnchorLinkProps,
  HeadingProps,
  ImgProps,
  ParagraphProps,
  TableHeaderCellProps,
  TableProps,
  TableHeaderProps,
  TableBodyProps,
  TableRowProps,
  TableCellProps,
  PreparedTextProps
} from './types'

import { PARAGRAPH_SIZES } from '../Paragraph/constants'

const filterProps = (props: object) => {
  const newProps = { ...props }

  if ('node' in newProps) {
    delete newProps.node
  }

  return newProps
}

const UnorderedList = ({ className, ...props }: UnorderedListProps) => (
  <ul
    className={cn(
      className,
      PARAGRAPH_SIZES.body,
      'flex list-disc flex-col pl-10'
    )}
    {...filterProps(props)}
  />
)

const OrderedList = ({ className, ...props }: OrderedListProps) => (
  <ol
    className={cn(
      className,
      PARAGRAPH_SIZES.body,
      'flex list-decimal flex-col pl-10'
    )}
    {...filterProps(props)}
  />
)

const Paragraph = ({ className, ...props }: ParagraphProps) => (
  <div
    className={cn(className, PARAGRAPH_SIZES.body)}
    {...filterProps(props)}
  />
)

const EmphasizedText = ({ className, ...props }: EmphasizedTextProps) => (
  <em
    className={cn(className, 'text-sm font-semibold')}
    {...filterProps(props)}
  />
)

const ItalicText = ({ className, ...props }: ItalicTextProps) => (
  <i
    className={cn(className, 'italic', PARAGRAPH_SIZES.body)}
    {...filterProps(props)}
  />
)

const StrongText = ({ className, ...props }: StrongTextProps) => (
  <strong
    className={cn(className, 'text-sm font-semibold')}
    {...filterProps(props)}
  />
)

const BoldText = ({ className, ...props }: BoldTextProps) => (
  <b
    className={cn(className, 'text-sm font-semibold')}
    {...filterProps(props)}
  />
)

const UnderlinedText = ({ className, ...props }: UnderlinedTextProps) => (
  <u
    className={cn(className, 'underline', PARAGRAPH_SIZES.body)}
    {...filterProps(props)}
  />
)

const DeletedText = ({ className, ...props }: DeletedTextProps) => (
  <del
    className={cn(className, 'text-muted line-through', PARAGRAPH_SIZES.body)}
    {...filterProps(props)}
  />
)

const HorizontalRule = ({ className, ...props }: HorizontalRuleProps) => (
  <hr
    className={cn(className, 'mx-auto w-48 border-b border-border')}
    {...filterProps(props)}
  />
)

const InlineCode: FC<PreparedTextProps> = ({ children }) => {
  return (
    <code className="relative whitespace-pre-wrap rounded-sm bg-background-secondary/50 p-1">
      {children}
    </code>
  )
}

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

const Blockquote = ({ className, ...props }: BlockquoteProps) => (
  <blockquote
    className={cn(className, 'italic', PARAGRAPH_SIZES.body)}
    {...filterProps(props)}
  />
)

const AnchorLink = ({ className, ...props }: AnchorLinkProps) => (
  <a
    className={cn(className, 'cursor-pointer text-xs underline')}
    target="_blank"
    rel="noopener noreferrer"
    {...filterProps(props)}
  />
)

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

const Img = ({ src, alt }: ImgProps) => {
  const [error, setError] = useState(false)

  if (!src) return null

  return (
    <div className="w-full max-w-xl">
      {error ? (
        <div className="flex h-40 flex-col items-center justify-center gap-2 rounded-md bg-secondary/50 text-muted">
          <Paragraph className="text-primary">Image unavailable</Paragraph>
          <Link
            href={src}
            target="_blank"
            className="max-w-md truncate underline"
          >
            {src}
          </Link>
        </div>
      ) : (
        <Image
          src={src}
          width={1280}
          height={720}
          alt={alt ?? 'Rendered image'}
          className="size-full rounded-md object-cover"
          onError={() => setError(true)}
          unoptimized
        />
      )}
    </div>
  )
}

const Table = ({ className, ...props }: TableProps) => (
  <div className="w-full max-w-full overflow-hidden rounded-md border border-border">
    <div className="w-full overflow-x-auto">
      <table className={cn(className, 'w-full')} {...filterProps(props)} />
    </div>
  </div>
)

const TableHead = ({ className, ...props }: TableHeaderProps) => (
  <thead
    className={cn(
      className,
      'rounded-md border-b border-border bg-transparent p-2 text-left text-sm font-[600]'
    )}
    {...filterProps(props)}
  />
)

const TableHeadCell = ({ className, ...props }: TableHeaderCellProps) => (
  <th
    className={cn(className, 'p-2 text-sm font-[600]')}
    {...filterProps(props)}
  />
)

const TableBody = ({ className, ...props }: TableBodyProps) => (
  <tbody className={cn(className, 'text-xs')} {...filterProps(props)} />
)

const TableRow = ({ className, ...props }: TableRowProps) => (
  <tr
    className={cn(className, 'border-b border-border last:border-b-0')}
    {...filterProps(props)}
  />
)

const TableCell = ({ className, ...props }: TableCellProps) => (
  <td
    className={cn(className, 'whitespace-nowrap p-2 font-[400]')}
    {...filterProps(props)}
  />
)

export const components = {
  h1: Heading1,
  h2: Heading2,
  h3: Heading3,
  h4: Heading4,
  h5: Heading5,
  h6: Heading6,
  ul: UnorderedList,
  ol: OrderedList,
  em: EmphasizedText,
  i: ItalicText,
  strong: StrongText,
  b: BoldText,
  u: UnderlinedText,
  del: DeletedText,
  hr: HorizontalRule,
  blockquote: Blockquote,
  pre: CodeBlock,
  code: InlineCode,
  a: AnchorLink,
  img: Img,
  p: Paragraph,
  table: Table,
  thead: TableHead,
  th: TableHeadCell,
  tbody: TableBody,
  tr: TableRow,
  td: TableCell
}
