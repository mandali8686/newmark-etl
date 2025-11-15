import { useState } from "react";
import { Button, ToggleButton, ToggleButtonGroup } from "@mui/material";
import { useUpload } from "../api/hooks";

export default function UploadPanel({ onUploaded }: { onUploaded: (docId: number) => void }) {
  const [type, setType] = useState<"flyer" | "rent_roll">("flyer");
  const [file, setFile] = useState<File | null>(null);
  const upload = useUpload();
  return (
    <div className="p-4 flex gap-3 items-center border rounded">
      <ToggleButtonGroup value={type} exclusive onChange={(_, v) => v && setType(v)}>
        <ToggleButton value="flyer">Flyer</ToggleButton>
        <ToggleButton value="rent_roll">Rent Roll</ToggleButton>
      </ToggleButtonGroup>
      <input type="file" accept="application/pdf" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      <Button variant="contained" disabled={!file || upload.isPending} onClick={async () => {
        if (!file) return;
        const res = await upload.mutateAsync({ file, doc_type: type });
        onUploaded(res.document_id);
      }}>Upload & Extract</Button>
    </div>
  );
}