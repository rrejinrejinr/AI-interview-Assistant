import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';

/**
 * SafeMarkdown.jsx — Safe, dependency-free Markdown renderer for React
 *
 * Renders Markdown into native React JSX nodes without dangerouslySetInnerHTML.
 * Features:
 *   - Code blocks with language badge, monospace font, indentation, & horizontal scroll
 *   - Tables with standard thead / tbody formatting
 *   - Headers (h1 - h4)
 *   - Inline code, bold, italic, lists, and clean paragraph breaks
 */

// Helper to parse inline styles: `code`, **bold**, *italic*
function parseInline(text) {
  if (!text) return text;

  // Tokenize by inline code, bold, and italic
  // Regex matches `inline code`, **bold**, *italic*
  const tokens = [];
  let remaining = text;
  let keyIdx = 0;

  while (remaining.length > 0) {
    // Match inline code: `...`
    const codeMatch = remaining.match(/^(.*?)`([^`]+)`(.*)$/s);
    // Match bold: **...**
    const boldMatch = remaining.match(/^(.*?)\*\*([^*]+)\*\*(.*)$/s);
    // Match italic: *...*
    const italicMatch = remaining.match(/^(.*?)\*([^*]+)\*(.*)$/s);

    // Find earliest match
    let earliest = null;
    let type = null;
    let matchObj = null;

    if (codeMatch) {
      earliest = codeMatch[1].length;
      type = 'code';
      matchObj = codeMatch;
    }
    if (boldMatch && (earliest === null || boldMatch[1].length < earliest)) {
      earliest = boldMatch[1].length;
      type = 'bold';
      matchObj = boldMatch;
    }
    if (italicMatch && (earliest === null || italicMatch[1].length < earliest)) {
      earliest = italicMatch[1].length;
      type = 'italic';
      matchObj = italicMatch;
    }

    if (!matchObj) {
      tokens.push(remaining);
      break;
    }

    // Push preceding plain text
    if (matchObj[1]) {
      tokens.push(matchObj[1]);
    }

    // Push styled element
    if (type === 'code') {
      tokens.push(
        <code
          key={`code-${keyIdx++}`}
          style={{
            background: 'var(--bg-surface-secondary, rgba(255,255,255,0.08))',
            color: 'var(--primary, #38bdf8)',
            padding: '2px 6px',
            borderRadius: '4px',
            fontFamily: "Consolas, Monaco, 'Courier New', monospace",
            fontSize: '0.9em',
            border: '1px solid var(--border-light, rgba(255,255,255,0.1))'
          }}
        >
          {matchObj[2]}
        </code>
      );
    } else if (type === 'bold') {
      tokens.push(
        <strong key={`bold-${keyIdx++}`} style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
          {matchObj[2]}
        </strong>
      );
    } else if (type === 'italic') {
      tokens.push(
        <em key={`italic-${keyIdx++}`} style={{ fontStyle: 'italic', opacity: 0.9 }}>
          {matchObj[2]}
        </em>
      );
    }

    remaining = matchObj[3];
  }

  return tokens.length > 0 ? tokens : text;
}

function CodeBlock({ code, lang }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (typeof navigator !== 'undefined' && navigator.clipboard) {
      navigator.clipboard.writeText(code).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }).catch(() => {});
    }
  };

  return (
    <div
      style={{
        borderRadius: '6px',
        background: '#0f172a',
        border: '1px solid var(--border-light, #334155)',
        overflow: 'hidden',
        margin: '6px 0'
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: '#1e293b',
          padding: '4px 10px',
          fontSize: '11px',
          fontWeight: 600,
          color: '#94a3b8',
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          borderBottom: '1px solid #334155'
        }}
      >
        <span>{lang || 'code'}</span>
        <button
          type="button"
          onClick={handleCopy}
          style={{
            background: 'none',
            border: 'none',
            color: copied ? '#4ade80' : '#94a3b8',
            cursor: 'pointer',
            fontSize: '11px',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            padding: '2px 6px',
            borderRadius: '4px',
            transition: 'color 0.15s'
          }}
          title="Copy code"
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>
      <pre
        style={{
          margin: 0,
          padding: '10px 12px',
          fontFamily: "Consolas, Monaco, 'Courier New', monospace",
          fontSize: '12.5px',
          color: '#f8fafc',
          overflowX: 'auto',
          whiteSpace: 'pre',
          lineHeight: 1.5
        }}
      >
        <code>{code}</code>
      </pre>
    </div>
  );
}

export default function SafeMarkdown({ content = '' }) {
  if (!content) return null;

  // Split into raw blocks (Code blocks vs Text blocks)
  const blocks = [];
  const lines = content.split('\n');
  let inCodeBlock = false;
  let codeLang = '';
  let codeLines = [];
  let currentTextBlock = [];

  const flushTextBlock = () => {
    if (currentTextBlock.length > 0) {
      blocks.push({ type: 'text', lines: [...currentTextBlock] });
      currentTextBlock = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.trim().startsWith('```')) {
      if (inCodeBlock) {
        // End of code block
        blocks.push({
          type: 'code',
          lang: codeLang || 'code',
          code: codeLines.join('\n')
        });
        codeLines = [];
        codeLang = '';
        inCodeBlock = false;
      } else {
        // Start of code block
        flushTextBlock();
        inCodeBlock = true;
        codeLang = line.trim().replace(/^```/, '').trim();
      }
    } else if (inCodeBlock) {
      codeLines.push(line);
    } else {
      currentTextBlock.push(line);
    }
  }

  // Handle trailing blocks
  if (inCodeBlock && codeLines.length > 0) {
    blocks.push({ type: 'code', lang: codeLang || 'code', code: codeLines.join('\n') });
  } else {
    flushTextBlock();
  }

  return (
    <div className="markdown-content" style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13.5px', lineHeight: 1.6 }}>
      {blocks.map((block, bIdx) => {
        if (block.type === 'code') {
          return <CodeBlock key={`block-${bIdx}`} code={block.code} lang={block.lang} />;
        }

        // Parse text lines: Headers, Tables, Lists, Paragraphs
        const textElements = [];
        let tableRows = [];
        let inTable = false;
        let listItems = [];
        let isOrderedList = false;

        const flushList = () => {
          if (listItems.length > 0) {
            if (isOrderedList) {
              textElements.push(
                <ol key={`ol-${textElements.length}`} style={{ margin: '6px 0 10px 20px', padding: 0 }}>
                  {listItems.map((it, idx) => (
                    <li key={idx} style={{ marginBottom: '4px' }}>{parseInline(it)}</li>
                  ))}
                </ol>
              );
            } else {
              textElements.push(
                <ul key={`ul-${textElements.length}`} style={{ margin: '6px 0 10px 20px', padding: 0 }}>
                  {listItems.map((it, idx) => (
                    <li key={idx} style={{ marginBottom: '4px' }}>{parseInline(it)}</li>
                  ))}
                </ul>
              );
            }
            listItems = [];
          }
        };

        const flushTable = () => {
          if (tableRows.length > 0) {
            const headerRow = tableRows[0];
            const bodyRows = tableRows.slice(1).filter(r => !r.every(cell => cell.trim().match(/^:?-+:?$/)));

            textElements.push(
              <div key={`table-${textElements.length}`} style={{ overflowX: 'auto', margin: '10px 0' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12.5px' }}>
                  <thead>
                    <tr style={{ background: 'var(--bg-surface-secondary, rgba(255,255,255,0.06))', borderBottom: '2px solid var(--border-light, #475569)' }}>
                      {headerRow.map((h, idx) => (
                        <th key={idx} style={{ padding: '8px 12px', textAlign: 'left', fontWeight: 700 }}>
                          {parseInline(h)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {bodyRows.map((row, rIdx) => (
                      <tr key={rIdx} style={{ borderBottom: '1px solid var(--border-light, rgba(255,255,255,0.08))' }}>
                        {row.map((cell, cIdx) => (
                          <td key={cIdx} style={{ padding: '7px 12px' }}>
                            {parseInline(cell)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
            tableRows = [];
            inTable = false;
          }
        };

        for (let j = 0; j < block.lines.length; j++) {
          const l = block.lines[j];
          const trimmed = l.trim();

          // Table Line
          if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
            flushList();
            inTable = true;
            const cells = trimmed.split('|').slice(1, -1).map(c => c.trim());
            tableRows.push(cells);
            continue;
          } else if (inTable) {
            flushTable();
          }

          // Unordered List (- or *)
          if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
            if (isOrderedList) flushList();
            isOrderedList = false;
            listItems.push(trimmed.substring(2));
            continue;
          }

          // Ordered List (1. 2.)
          const ordMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
          if (ordMatch) {
            if (!isOrderedList) flushList();
            isOrderedList = true;
            listItems.push(ordMatch[2]);
            continue;
          }

          // Not a list line
          flushList();

          if (!trimmed) {
            continue;
          }

          // Headers
          if (trimmed.startsWith('#### ')) {
            textElements.push(
              <h4 key={`h4-${j}`} style={{ fontSize: '13.5px', fontWeight: 800, margin: '10px 0 4px', color: 'var(--text-primary)' }}>
                {parseInline(trimmed.substring(5))}
              </h4>
            );
          } else if (trimmed.startsWith('### ')) {
            textElements.push(
              <h3 key={`h3-${j}`} style={{ fontSize: '15px', fontWeight: 800, margin: '12px 0 6px', color: 'var(--primary, #38bdf8)' }}>
                {parseInline(trimmed.substring(4))}
              </h3>
            );
          } else if (trimmed.startsWith('## ')) {
            textElements.push(
              <h2 key={`h2-${j}`} style={{ fontSize: '16px', fontWeight: 800, margin: '14px 0 6px', color: 'var(--text-primary)' }}>
                {parseInline(trimmed.substring(3))}
              </h2>
            );
          } else if (trimmed.startsWith('# ')) {
            textElements.push(
              <h1 key={`h1-${j}`} style={{ fontSize: '18px', fontWeight: 800, margin: '16px 0 8px', color: 'var(--text-primary)' }}>
                {parseInline(trimmed.substring(2))}
              </h1>
            );
          } else if (trimmed === '---') {
            textElements.push(<hr key={`hr-${j}`} style={{ border: 'none', borderTop: '1px solid var(--border-light, #334155)', margin: '10px 0' }} />);
          } else {
            textElements.push(
              <p key={`p-${j}`} style={{ margin: '4px 0', color: 'var(--text-primary)' }}>
                {parseInline(trimmed)}
              </p>
            );
          }
        }

        flushList();
        flushTable();

        return <div key={`tb-${bIdx}`} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>{textElements}</div>;
      })}
    </div>
  );
}
