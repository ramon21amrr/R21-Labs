export function CanonicalValue({ value }: { value: unknown }) {
  if (value === null) return <span>—</span>;
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return <code>{String(value)}</code>;
  if (Array.isArray(value)) return <ol className="canonical-list">{value.map((item, index) => <li key={index}><CanonicalValue value={item} /></li>)}</ol>;
  if (typeof value === "object") return <div className="canonical-object">{Object.entries(value as Record<string, unknown>).map(([key, child]) => <div className="canonical-field" key={key}><span>{key}</span><CanonicalValue value={child} /></div>)}</div>;
  return <span>—</span>;
}
