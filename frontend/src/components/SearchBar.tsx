import { TextField } from "@mui/material";

export default function SearchBar({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <TextField 
        label="Search by name, address, unit, rent..." 
        fullWidth value={value} 
        onChange={(e) => onChange(e.target.value)} />
  );
}
