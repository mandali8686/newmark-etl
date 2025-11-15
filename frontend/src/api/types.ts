export type Property = { 
    id: number; 
    name?: string; 
    address?: string; 
    city?: string; 
    state?: string; 
    zipcode?: string; 
    unit_count?: number; 
    cap_rate?: number; 
    sqft?: number; 
    source_document?: number };

export type Unit = { 
    id: number; 
    property: number; 
    unit_number?: string; 
    beds?: string; 
    baths?: string; 
    sqft?: number; 
    rent?: number; 
    status?: string; 
    lease_start?: string; 
    lease_end?: string };

export type Citation = { 
    id: number; 
    model_name: string; 
    record_id: number; 
    field_name: string; 
    page: number; 
    x0: number; 
    y0: number; 
    x1: number; 
    y1: number; 
    snippet?: string };

export type Section = {
    id: number;
    page: number | null;
    title: string;
    text: string;
    bbox_x0: number | null;
    bbox_y0: number | null;
    bbox_x1: number | null;
    bbox_y1: number | null;
};