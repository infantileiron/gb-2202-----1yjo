<script setup lang="ts">
import {ref,onMounted} from 'vue';
import {datasets} from '../stores/datasets';
import {fetchSupplements,createSupplement} from '../api/datasets';
import {canWrite} from '../stores/auth';
import {useTask} from '../hooks/useTask';
import {ApiError} from '../api/client';
import PageHeading from '../components/common/PageHeading.vue';
import Notice from '../components/common/Notice.vue';
import EmptyState from '../components/common/EmptyState.vue';

interface Decision{decision:string;shipment_id:string;milestone:string;revision:number;reason:string;line?:number;detail?:any}
interface Supplement{id:string;seq:number;status:string;note:string;row_count:number;accepted_count:number;ignored_count:number;conflict_count:number;decisions:Decision[];created_at:string}
interface Conflict{shipment_id:string;milestone:string;revision:number;reason:string;lines?:number[];detail:unknown}

const name=ref(''),text=ref(''),description=ref(''),selected=ref('');
const suppText=ref(''),suppNote=ref(''),supplements=ref<Supplement[]>([]),conflicts=ref<Conflict[]>([]),suppLoading=ref(false),suppInfo=ref('');
const {error,busy,act}=useTask();
onMounted(datasets.load);
const decisionLabels:Record<string,string>={adopted:'采纳',ignored_stale:'忽略·迟到旧记录',ignored_duplicate:'忽略·重复投递',conflict:'冲突'};
const milestoneLabels:Record<string,string>={accepted:'揽收',collected:'收件',sorted:'分拣',arrived:'到达',delivered:'交付'};

async function file(e:Event){const f=(e.target as HTMLInputElement).files?.[0];if(f)text.value=await f.text()}
async function suppFile(e:Event){const f=(e.target as HTMLInputElement).files?.[0];if(f)suppText.value=await f.text()}
function submit(){act(async()=>{await datasets.create({name:name.value,csv_text:text.value,description:description.value});name.value='';text.value=''})}
async function openSupplements(row:{id:string}){
 selected.value=row.id;conflicts.value=[];suppInfo.value='';supplements.value=[];suppLoading.value=true;
 try{supplements.value=await fetchSupplements(row.id)}catch(e){suppInfo.value=(e as Error).message}finally{suppLoading.value=false}
}
async function submitSupplement(){
 conflicts.value=[];suppInfo.value='';
 const id=selected.value;
 try{
  await createSupplement(id,{csv_text:suppText.value,note:suppNote.value});
  suppText.value='';suppNote.value='';suppInfo.value='补报已受理：同票同里程碑按较新修订采纳，详见逐行决策。';
 }catch(e){
  if(e instanceof ApiError && e.status===409 && e.detail&&typeof e.detail==='object'&&'conflicts' in (e.detail as Record<string,unknown>)){
   conflicts.value=(e.detail as {conflicts:Conflict[]}).conflicts;
  }else throw e;
 }
 await datasets.load();
 if(id)await openSupplements({id});
}
function fmtTime(s:string){return s?new Date(s).toLocaleString('zh-CN',{hour12:false}):''}
</script>

<template>
 <PageHeading eyebrow="OBSERVATIONS / 01" title="里程碑观测台账" note="原始CSV字段：shipment_id,station,milestone,timestamp，时间必须携带时区。补报CSV增加 revision 列（修订号≥1），原批次事件视为修订零。"/>
 <div class="two-col">
  <section>
   <h2>已入库批次</h2>
   <Notice :message="datasets.error.value"/>
   <EmptyState v-if="!datasets.items.value.length"/>
   <button v-for="row in datasets.items.value" class="record-row" :key="row.id" @click="openSupplements(row)">
    <div><h3>{{row.name}} <small class="version-tag">v{{row.version||0}}</small></h3><p>{{row.events.length}}条事件 · 已接收{{(row.revisions||[]).length}}批补报 · {{row.description}}</p></div>
    <span>{{selected===row.id?'收起/预览':'查看事件与补报 ↗'}}</span>
   </button>

   <div v-for="row in datasets.items.value.filter(r=>r.id===selected)" :key="row.id" class="table-wrap">
    <h3>当前生效事件（预览前15条 / 共{{row.events.length}}条）</h3>
    <table>
     <thead><tr><th>票号</th><th>站点</th><th>里程碑</th><th>带时区时间</th><th>修订</th></tr></thead>
     <tbody><tr v-for="(e,i) in row.events.slice(0,15)" :key="i"><td>{{e.shipment_id}}</td><td>{{e.station}}</td><td>{{e.milestone}}</td><td>{{e.timestamp}}</td><td>v{{e.revision||0}}</td></tr></tbody>
    </table>

    <h3 style="margin-top:1.2rem">补报批次决策台账</h3>
    <p v-if="suppLoading" class="muted">加载中…</p>
    <p v-else-if="!supplements.length" class="muted">暂无补报；原始入库事件均为修订零。</p>
    <div v-for="s in supplements" :key="s.id" class="supp-card" :class="s.status">
     <div class="supp-head">
      <strong>第{{s.seq}}批 · {{s.status==='accepted'?'已受理':'整批拒收'}}</strong>
      <span class="muted">{{fmtTime(s.created_at)}} · {{s.note||'无备注'}}</span>
     </div>
     <p class="supp-counts">
      投递{{s.row_count}}条 · <b class="ok">采纳{{s.accepted_count}}</b> · <b class="warn">忽略{{s.ignored_count}}</b> · <b class="bad">冲突{{s.conflict_count}}</b>
     </p>
     <details>
      <summary>逐行核对（{{s.decisions.length}}条决策与原因）</summary>
      <table>
       <thead><tr><th>行</th><th>票号</th><th>里程碑</th><th>修订</th><th>结论</th><th>原因</th></tr></thead>
       <tbody>
        <tr v-for="(d,i) in s.decisions" :key="i" :class="d.decision">
         <td>{{d.line||'—'}}</td><td>{{d.shipment_id}}</td><td>{{milestoneLabels[d.milestone]||d.milestone}}</td><td>v{{d.revision}}</td>
         <td><span class="decision-pill" :class="d.decision">{{decisionLabels[d.decision]||d.decision}}</span></td>
         <td class="reason-cell">{{d.reason}}</td>
        </tr>
       </tbody>
      </table>
     </details>
    </div>
   </div>
  </section>

  <form v-if="canWrite()" @submit.prevent="submit" class="editor-panel">
   <h2>上传原始观测</h2>
   <label>批次名称<input v-model="name" required minlength="2" placeholder="如：城配里程碑 11月10日"></label>
   <label>CSV 文件<input type="file" accept=".csv" @change="file"></label>
   <label>或粘贴CSV<textarea v-model="text" rows="6" required placeholder="shipment_id,station,milestone,timestamp"></textarea></label>
   <label>口径说明<input v-model="description" placeholder="记录来源和时区"></label>
   <Notice :message="error"/>
   <button :disabled="busy">校验并入库</button>

   <div v-if="selected" class="supplement-panel">
    <h2>向该批次补报（带修订号）</h2>
    <p class="muted small">规则：同票同里程碑取较新修订；迟到旧修订不覆盖；完全重复不新增事件；同修订号内容冲突整批拒收。补报可补齐缺里程碑票，已排队运行与已归档报告保留原口径。</p>
    <label>补报CSV 文件<input type="file" accept=".csv" @change="suppFile"></label>
    <label>或粘贴补报CSV<textarea v-model="suppText" rows="6" required placeholder="shipment_id,station,milestone,timestamp,revision"></textarea></label>
    <label>补报说明<input v-model="suppNote" maxlength="300" placeholder="如：站点11日更正交付时间"></label>
    <Notice :message="error"/>
    <p v-if="suppInfo" class="success">{{suppInfo}}</p>
    <div v-if="conflicts.length" class="conflict-box" role="alert">
     <strong>整批拒收：发现{{conflicts.length}}处同修订号内容冲突，原批次事件未做任何改动。</strong>
     <ul>
      <li v-for="(c,i) in conflicts" :key="i">票号 {{c.shipment_id}} · {{milestoneLabels[c.milestone]||c.milestone}} · 修订v{{c.revision}}：{{c.reason}}<ul v-if="c.lines"><li>冲突行：{{c.lines.join('、')}}</li></ul></li>
     </ul>
    </div>
    <button type="button" :disabled="busy||!suppText.trim()" @click="act(submitSupplement)">校验并合并补报</button>
   </div>
  </form>
  <aside v-else class="field-note">当前是只读账号，可浏览原始事件与补报决策；上传需要分析师权限。</aside>
 </div>
</template>
