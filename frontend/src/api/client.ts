export class ApiError extends Error{
 status:number;detail:unknown;
 constructor(message:string,status:number,detail:unknown){super(message);this.status=status;this.detail=detail}
}
export async function request<T=any>(path:string,method="GET",body?:unknown):Promise<T>{
 const token=localStorage.getItem("delay-token");const response=await fetch("/api"+path,{method,headers:{"Content-Type":"application/json",...(token?{Authorization:"Bearer "+token}:{})},body:body===undefined?undefined:JSON.stringify(body)});
 if(!response.ok){let message="请求失败";let detail:unknown;try{const error=await response.json();detail=error.detail;message=typeof detail==="string"?detail:detail&&typeof detail==="object"&&"message" in (detail as Record<string,unknown>)?String((detail as Record<string,unknown>).message):JSON.stringify(detail)}catch{};throw new ApiError(message,response.status,detail)}
 return response.json();
}
export async function downloadCsv(id:string){const r=await fetch("/api/reports/"+id+"/csv",{headers:{Authorization:"Bearer "+localStorage.getItem("delay-token")}});if(!r.ok)throw new Error("下载失败");const a=document.createElement("a");a.href=URL.createObjectURL(await r.blob());a.download="delay-report.csv";a.click();URL.revokeObjectURL(a.href)}
