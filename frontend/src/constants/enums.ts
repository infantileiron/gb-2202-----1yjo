export const roles=["admin","analyst","viewer"] as const;
export const runStatuses=["queued","running","completed","failed"] as const;
export const phases:Record<string,string>={collection:"揽收交接",sorting:"分拣出库",linehaul:"干线运输",lastmile:"末端交付"};
export const milestones=["accepted","collected","sorted","arrived","delivered"] as const;
