import{P as u}from"./PageHeader-DZRguq4P.js";import{_ as d,o as g,b as t,c as a,e as f,d as r,F as h,r as _,l as c,m as v,t as x}from"./index-8iFk1r5n.js";const k={class:"gc-page agreement-page"},y={class:"gc-card agreement-card"},A={key:0,class:"agreement-loading"},E={key:1,class:"agreement-content"},b=`GALACREDIT USER AGREEMENT

Last updated: 5 September 2026

Please read this agreement before using GalaCredit services.

1. ELIGIBILITY AND ACCOUNT

You must provide accurate information and keep your account credentials secure.

2. CREDIT SERVICES

Applications are assessed using the information and checks described in the application flow. Approval, amount and repayment terms are subject to the result of that assessment.

3. CONTACT

You may contact Customer Support for questions, corrections or complaints.`,C={__name:"index",setup(w){const o=c(!0),n=c(""),i=v(()=>String(n.value||"").split(/\n\s*\n/g).map(e=>e.replace(/\n/g," ").trim()).filter(Boolean));async function l(){try{if(typeof fetch=="function"){const e=await fetch("/user-agreement.txt",{cache:"no-cache"});e.ok&&(n.value=await e.text())}}catch{}n.value||(n.value=b),o.value=!1}return g(l),(e,s)=>(t(),a("view",k,[f(u,{title:"User Agreement",back:!0}),r("view",y,[s[0]||(s[0]=r("text",{class:"agreement-title"},"User Agreement",-1)),s[1]||(s[1]=r("text",{class:"agreement-tip"},"The latest version of the platform agreement is shown below.",-1)),o.value?(t(),a("text",A,"Loading agreement...")):(t(),a("view",E,[(t(!0),a(h,null,_(i.value,(p,m)=>(t(),a("text",{key:m,class:"agreement-paragraph"},x(p),1))),128))]))])]))}},S=d(C,[["__scopeId","data-v-7d6b2131"]]);export{S as default};
