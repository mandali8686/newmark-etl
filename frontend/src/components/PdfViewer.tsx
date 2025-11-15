import { useEffect, useRef, useState } from "react";
import { getDocument, GlobalWorkerOptions, type PDFDocumentProxy } from "pdfjs-dist";
import pdfjsWorker from "pdfjs-dist/build/pdf.worker?url";
GlobalWorkerOptions.workerSrc = pdfjsWorker;

export type Highlight = { page: number; bbox: [number, number, number, number] };

export default function PdfViewer({
  url,
  highlights,
}: {
  url: string;
  highlights: Highlight[];
}) {
  const [sizes, setSizes] = useState<{ width: number; height: number }[]>([]);
  const canvasRefs = useRef<(HTMLCanvasElement | null)[]>([]);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      const doc: PDFDocumentProxy = await getDocument(url).promise;

      const pageSizes: { width: number; height: number }[] = [];
      const viewports: any[] = [];

      // compute sizes first
      for (let i = 1; i <= doc.numPages; i++) {
        const page = await doc.getPage(i);
        const viewport = page.getViewport({ scale: 1.2 });
        pageSizes.push({
          width: Math.ceil(viewport.width),
          height: Math.ceil(viewport.height),
        });
        viewports.push(viewport);
      }
      if (cancelled) return;

      setSizes(pageSizes); 

      requestAnimationFrame(async () => {
        for (let i = 1; i <= doc.numPages; i++) {
          const page = await doc.getPage(i);
          const canvas = canvasRefs.current[i - 1];
          if (!canvas) continue;
          const viewport = viewports[i - 1];
          canvas.width = Math.ceil(viewport.width);
          canvas.height = Math.ceil(viewport.height);
          await page.render({ canvas, viewport }).promise;
        }
      });
    })();

    return () => {
      cancelled = true;
    };
  }, [url]);

  // draw highlight overlays
  useEffect(() => {
    sizes.forEach((_, idx) => {
      const canvas = canvasRefs.current[idx];
      const ctx = canvas?.getContext("2d");
      if (!canvas || !ctx) return;

      ctx.save();
      highlights
        .filter((h) => h.page === idx)
        .forEach((h) => {
          const [x0, y0, x1, y1] = h.bbox;
          ctx.globalAlpha = 0.2;
          ctx.fillStyle = "yellow";
          ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
          ctx.globalAlpha = 1.0;
          ctx.lineWidth = 2;
          ctx.strokeStyle = "orange";
          ctx.strokeRect(x0, y0, x1 - x0, y1 - y0);
        });
      ctx.restore();
    });
  }, [sizes, highlights]);

  return (
    <div className="flex flex-col gap-2">
      {sizes.map((s, i) => (
        <canvas
          key={i}
          width={s.width}
          height={s.height}
          ref={(el) => {
            canvasRefs.current[i] = el;
          }}
          style={{ display: "block" }}
        />
      ))}
    </div>
  );
}
