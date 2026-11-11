import numpy as np
from ..constants.enums import PHASES

def attribute(matrix,replicates=200,seed=42,tail_quantile=.95):
 rng=np.random.default_rng(seed);n,k=matrix.shape
 if n<8 or k!=4 or not np.isfinite(matrix).all() or (matrix<0).any(): raise ValueError("非法阶段时延矩阵")
 medians=np.median(matrix,axis=0);observed=float(np.quantile(matrix.sum(axis=1),tail_quantile))
 # Resample each phase independently; the modeled tail isolates phase dispersion, not route causality.
 samples=[];tails=[]
 for _ in range(replicates):
  synthetic=np.column_stack([rng.choice(matrix[:,j],size=n,replace=True) for j in range(k)])
  baseline=float(np.quantile(synthetic.sum(axis=1),tail_quantile));tails.append(baseline)
  effect=[]
  for j in range(k):
   replaced=synthetic.copy();replaced[:,j]=medians[j]
   effect.append(baseline-float(np.quantile(replaced.sum(axis=1),tail_quantile)))
  samples.append(effect)
 arr=np.array(samples);effects=arr.mean(axis=0);positive=np.maximum(effects,0);den=float(positive.sum())
 return {"observed_tail":observed,"modeled_tail":float(np.mean(tails)),"replicates":replicates,"seed":seed,"quantile":tail_quantile,"contributions":[{"phase":p,"reduction":float(effects[j]),"share":float(positive[j]/den) if den else 0.,"low":float(np.quantile(arr[:,j],.025)),"high":float(np.quantile(arr[:,j],.975)),"median":float(medians[j])} for j,p in enumerate(PHASES)],"assumption":"阶段独立重采样；将某阶段置于其中位数后比较模拟总时延尾部分位。区间表示重采样波动，不是因果效应。"}
