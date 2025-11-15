import type { GridColDef } from "@mui/x-data-grid";
import { DataGrid } from "@mui/x-data-grid";
import type { Unit } from "../api/types";

export default function UnitTable({ rows }: { rows: Unit[] }) {
  const cols: GridColDef[] = [
    { field: "unit_number", headerName: "Unit", width: 100 },
    { field: "beds", headerName: "Beds", width: 80 },
    { field: "baths", headerName: "Baths", width: 80 },
    { field: "sqft", headerName: "SqFt", width: 100 },
    { field: "rent", headerName: "Rent", width: 100 },
    { field: "status", headerName: "Status", width: 120 },
  ];
  return (
    <div style={{ height: 420 }}>
      <DataGrid rows={rows} columns={cols} getRowId={(r) => r.id} />
    </div>
  );
}
