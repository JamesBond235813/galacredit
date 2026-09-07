import{_ as m,o as d,b as t,c as a,d as o,F as g,r as f,l as c,m as h,t as _}from"./index-DS23BFnx.js";const v={class:"gc-page agreement-page"},x={class:"gc-card agreement-card"},y={key:0,class:"agreement-loading"},E={key:1,class:"agreement-content"},k=`GALACREDIT USER AGREEMENT

Last updated: 5 September 2026

Please read this agreement before using GalaCredit services.

1. ELIGIBILITY AND ACCOUNT

You must provide accurate information and keep your account credentials secure.

2. CREDIT SERVICES

Applications are assessed using the information and checks described in the application flow. Approval, amount and repayment terms are subject to the result of that assessment.

3. CONTACT

You may contact Customer Support for questions, corrections or complaints.`,A={__name:"index",setup(C){const r=c(!0),n=c(""),i=h(()=>String(n.value||"").split(/\n\s*\n/g).map(e=>e.replace(/\n/g," ").trim()).filter(Boolean));async function l(){try{if(typeof fetch=="function"){const e=await fetch("/user-agreement.txt",{cache:"no-cache"});e.ok&&(n.value=await e.text())}}catch{}n.value||(n.value=k),r.value=!1}return d(l),(e,s)=>(t(),a("view",v,[o("view",x,[s[0]||(s[0]=o("text",{class:"agreement-title"},"User Agreement",-1)),s[1]||(s[1]=o("text",{class:"agreement-tip"},"The latest version of the platform agreement is shown below.",-1)),r.value?(t(),a("text",y,"Loading agreement...")):(t(),a("view",E,[(t(!0),a(g,null,f(i.value,(p,u)=>(t(),a("text",{key:u,class:"agreement-paragraph"},_(p),1))),128))]))])]))}},I=m(A,[["__scopeId","data-v-9c871560"]]);export{I as default};
