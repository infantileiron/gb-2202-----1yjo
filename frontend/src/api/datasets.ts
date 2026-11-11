import {request} from "./client";
export const fetchDatasets=()=>request("/datasets");
export const createDatasets=(value:unknown)=>request("/datasets","POST",value);
export const fetchSupplements=(id:string)=>request(`/datasets/${id}/supplements`);
export const createSupplement=(id:string,value:unknown)=>request(`/datasets/${id}/supplements`,"POST",value);
