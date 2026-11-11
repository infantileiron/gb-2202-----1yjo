export type Role="admin"|"analyst"|"viewer";
export interface Entity {id:string;created_at:string;[key:string]:any}
export interface User {email:string;role:Role}
export interface Phase {phase:string;p50:number;p90:number;p95:number;mean:number}
export interface Contribution {phase:string;reduction:number;share:number;low:number;high:number;median:number}
