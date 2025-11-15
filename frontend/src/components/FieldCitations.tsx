import type { Citation } from "../api/types";

export default function FieldCitations({
  cites,
  onHover,
}: {
  cites: Citation[];
  onHover: (h: { page: number; x0: number; y0: number; x1: number; y1: number } | null) => void;
}) {
  return (
    <div>
      {cites.map((c) => (
        <div
          key={c.id}
          onMouseEnter={() =>
            onHover({ page: c.page, x0: c.x0, y0: c.y0, x1: c.x1, y1: c.y1 })
          }
          onMouseLeave={() => onHover(null)}
          style={{ cursor: "pointer", padding: 4 }}
        >
          p{c.page + 1} • [{c.x0.toFixed(0)},{c.y0.toFixed(0)}]→[{c.x1.toFixed(0)},{c.y1.toFixed(0)}]
        </div>
      ))}
    </div>
  );
}
