// src/pages/Explore.tsx
import { useMemo, useState } from "react";
import SearchBar from "../components/SearchBar";
import PropertyTable from "../components/PropertyTable";
import UnitTable from "../components/UnitTable";
import UploadPanel from "../components/UploadPanel";
import { useProperties, useUnits } from "../api/hooks";
import { useSearch } from "../api/hooks";

export default function Explore() {
  const [query, setQuery] = useState("");

  
  const { data: search } = useSearch(query);

  const { data: propsList } = useProperties(
    query.trim() ? undefined : undefined 
  );
  const first = propsList?.results?.[0];
  const { data: unitsList } = useUnits(
    query.trim() ? undefined : first ? { property_id: first.id } : undefined
  );

  const propertyRows = useMemo(
    () => (query.trim() ? search?.properties ?? [] : propsList?.results ?? []),
    [query, search, propsList]
  );
  const unitRows = useMemo(
    () => (query.trim() ? search?.units ?? [] : unitsList?.results ?? []),
    [query, search, unitsList]
  );

  return (
    <div className="p-4 flex flex-col gap-4">
      <UploadPanel onUploaded={() => window.location.reload()} />
      <SearchBar value={query} onChange={setQuery} />
      {propertyRows && <PropertyTable rows={propertyRows} onSelect={() => {}} />}
      {unitRows && <UnitTable rows={unitRows} />}
    </div>
  );
}
