import{P as p}from"./PageHeader-DZRguq4P.js";import{_ as f,o as m,b as e,c as a,e as h,d as i,F as y,r as g,l as r,m as v,t as _}from"./index-8iFk1r5n.js";const A={class:"gc-page authorization-page"},b={class:"gc-card authorization-card"},x={key:0,class:"copy"},k={key:1,class:"authorization-content"},z=`GALACREDIT PERSONAL DATA AUTHORIZATION

Last updated: 5 September 2026

Please read this authorization before submitting identity documents or a credit application.

1. DATA WE MAY COLLECT

GalaCredit may process your identity, phone, application, device, location, emergency contact, MoMo and repayment information for account security, identity verification, credit assessment, servicing and legal obligations.

2. YOUR CHOICES AND RIGHTS

You may request access to or correction of your personal data, raise a complaint through Customer Support and decline optional SMS review. Identity and risk checks required for a credit decision must still be completed.

3. AUTHORIZATION

By submitting your information, you confirm that it is accurate and authorise GalaCredit and approved service providers to process it for the purposes described above, subject to applicable law.`,T={__name:"index",setup(w){const s=r(!0),o=r(""),c=v(()=>String(o.value||"").split(/\n\s*\n/g).map(t=>t.replace(/\n/g," ").trim()).filter(Boolean));async function l(){try{if(typeof fetch=="function"){const t=await fetch("/personal-info-authorization.txt",{cache:"no-cache"});t.ok&&(o.value=await t.text())}}catch{}o.value||(o.value=z),s.value=!1}return m(l),(t,n)=>(e(),a("view",A,[h(p,{title:"Personal Data Authorization",back:!0}),i("view",b,[n[0]||(n[0]=i("text",{class:"authorization-title"},"Personal Data Authorization",-1)),n[1]||(n[1]=i("text",{class:"tip"},"The latest version of the authorization terms is shown below.",-1)),s.value?(e(),a("text",x,"Loading authorization…")):(e(),a("view",k,[(e(!0),a(y,null,g(c.value,(d,u)=>(e(),a("text",{key:u,class:"copy"},_(d),1))),128))]))])]))}},C=f(T,[["__scopeId","data-v-393ed8af"]]);export{C as default};
