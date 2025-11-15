import { useParams } from "react-router-dom";
import SideBySide from "../components/SideBySide";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { type Property, type Section } from "../api/types";

function normalizeDocUrl(fileField: string, apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000/api") {
  try { new URL(fileField); return fileField; } catch {}
  const origin = apiBase.replace(/\/api\/?$/, "");
  return fileField.startsWith("/") ? origin + fileField : `${origin}/${fileField}`;
}

function mapSectionsToHighlights(sections: Section[]) {
  return (sections || [])
    .filter(s => s.page !== null && s.bbox_x0 !== null)
    .map(s => ({
      page: Number(s.page),
      bbox: [s.bbox_x0!, s.bbox_y0!, s.bbox_x1!, s.bbox_y1!] as [number, number, number, number],
      label: s.title || "",
      text: s.text || "",
    }));
}

export default function DocumentView() {
  const { id } = useParams();
  const docId = Number(id);
  const enabledDoc = Number.isFinite(docId) && docId > 0;

  const { data: doc } = useQuery({
    enabled: enabledDoc,
    queryKey: ["doc", docId],
    queryFn: async () => (await api.get(`/documents/${docId}/`)).data,
  });

  const { data: props } = useQuery({
    enabled: !!doc,
    queryKey: ["props-by-doc", docId],
    queryFn: async () =>
      (await api.get<{ results: Property[] }>(`/properties/`, { params: { source_document: docId } })).data,
  });

  const property = props?.results?.[0];
  if (!doc) return null;

  const url = normalizeDocUrl(doc.file);
  const highlights = mapSectionsToHighlights(doc.sections || []);

  return (
    <div className="p-4">
      <SideBySide
        docUrl={url}
        property={property}
        sections={doc.sections}        
        highlights={highlights}        
      />
    </div>
  );
}
