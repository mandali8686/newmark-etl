import PdfViewer from "./PdfViewer";
import { type Property, type Section } from "../api/types";

type Props = {
  docUrl: string;
  property?: Property;
  sections: Section[];
  highlights: {
    page: number;
    bbox: [number, number, number, number];
    label?: string;
    text?: string;
  }[];
};

export default function SideBySide({ docUrl, property, sections, highlights }: Props) {
  const containerStyle: React.CSSProperties = {
    display: "flex",
    flexDirection: "row",
    justifyContent: "space-between",
    width: "100%",
    maxWidth: "1400px",
    margin: "0 auto",
    gap: "24px",
  };

  const pdfContainerStyle: React.CSSProperties = {
    flex: "1 1 auto",
    border: "1px solid #ddd",
    borderRadius: "8px",
    padding: "8px",
    height: "85vh",
    overflow: "auto",
  };

  const sidePanelStyle: React.CSSProperties = {
    width: "420px",
    flex: "0 0 420px",
    border: "1px solid #ddd",
    borderRadius: "8px",
    padding: "16px",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
    maxHeight: "85vh",
    overflowY: "auto",
    position: "sticky",
    top: "16px",
    backgroundColor: "white",
  };

  const sectionItemStyle: React.CSSProperties = {
    fontSize: "0.9rem",
    borderBottom: "1px solid #f0f0f0",
    paddingBottom: "8px",
    marginBottom: "8px",
  };

  return (
    <div style={containerStyle}>
      {/* Left: PDF Viewer */}
      <div style={pdfContainerStyle}>
        <h3 style={{ margin: "8px 0", fontWeight: "bold" }}>PDF View</h3>
        <PdfViewer url={docUrl} highlights={highlights} />
      </div>

      {/* Right: Property + Sections */}
      <div style={sidePanelStyle}>
        {property && (
          <div>
            <h3 style={{ fontWeight: "600", fontSize: "1.1rem" }}>Property</h3>
            <div style={{ fontSize: "0.9rem", color: "#444" }}>
              {property.address}
              {property.city && ` • ${property.city}, ${property.state} ${property.zipcode}`}
              {property.sqft ? ` • ${property.sqft} SF` : ""}
            </div>
          </div>
        )}

        <div>
          <h3 style={{ fontWeight: "600", fontSize: "1.1rem", marginBottom: "8px" }}>Extracted Sections</h3>
          <ul style={{ listStyleType: "none", padding: 0, margin: 0 }}>
            {sections.map((s) => (
              <li key={s.id} style={sectionItemStyle}>
                <div style={{ fontWeight: "500", wordBreak: "break-word" }}>
                  {s.title || "(untitled section)"}
                </div>
                <div style={{ color: "#666" }}>Refer: Page-{(s.page ?? 0) + 1}</div>
                {s.text && (
                  <div style={{ color: "#222", marginTop: "4px", whiteSpace: "pre-wrap" }}>{s.text}</div>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
