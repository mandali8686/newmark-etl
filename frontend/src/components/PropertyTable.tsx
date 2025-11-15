import type { GridColDef } from "@mui/x-data-grid";
import { DataGrid } from "@mui/x-data-grid";
import type { Property } from "../api/types";

export default function PropertyTable({ rows, onSelect }: { rows: Property[]; onSelect: (p: Property) => void }) {
  const cols: GridColDef[] = [
    { field: "name", headerName: "Property", flex: 1 },
    { field: "address", headerName: "Address", flex: 1 },
    { field: "city", headerName: "City", width: 120 },
    { field: "state", headerName: "State", width: 80 },
    { field: "unit_count", headerName: "Units", width: 90 },
    { field: "cap_rate", headerName: "Cap %", width: 90 },
  ];
  return (
    <div style={{ height: 420 }}>
      <DataGrid rows={rows} columns={cols} onRowClick={(p) => onSelect(p.row)} getRowId={(r) => r.id} />
    </div>
  );
}
