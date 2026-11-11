import {request} from "./client";
export const fetchGroups=()=>request("/groups");
export const createGroups=(value:unknown)=>request("/groups","POST",value);
