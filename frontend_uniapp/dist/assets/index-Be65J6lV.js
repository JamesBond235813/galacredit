import{_ as p,o as f,b as e,c as a,d as i,F as h,r as m,l as r,m as y,t as v}from"./index-Bjf9nslX.js";const g={class:"gc-page authorization-page"},_={class:"gc-card authorization-card"},A={key:0,class:"copy"},b={key:1,class:"authorization-content"},x=`GALACREDIT PERSONAL DATA AUTHORIZATION

Last updated: 5 September 2026

Please read this authorization before submitting identity documents or a credit application.

1. DATA WE MAY COLLECT

GalaCredit may process your identity, phone, application, device, location, emergency contact, MoMo and repayment information for account security, identity verification, credit assessment, servicing and legal obligations.

2. YOUR CHOICES AND RIGHTS

You may request access to or correction of your personal data, raise a complaint through Customer Support and decline optional SMS review. Identity and risk checks required for a credit decision must still be completed.

3. AUTHORIZATION

By submitting your information, you confirm that it is accurate and authorise GalaCredit and approved service providers to process it for the purposes described above, subject to applicable law.`,T={__name:"index",setup(k){const s=r(!0),o=r(""),c=y(()=>String(o.value||"").split(/\n\s*\n/g).map(t=>t.replace(/\n/g," ").trim()).filter(Boolean));async function l(){try{if(typeof fetch=="function"){const t=await fetch("/personal-info-authorization.txt",{cache:"no-cache"});t.ok&&(o.value=await t.text())}}catch{}o.value||(o.value=x),s.value=!1}return f(l),(t,n)=>(e(),a("view",g,[i("view",_,[n[0]||(n[0]=i("text",{class:"authorization-title"},"Personal Data Authorization",-1)),n[1]||(n[1]=i("text",{class:"tip"},"The latest version of the authorization terms is shown below.",-1)),s.value?(e(),a("text",A,"Loading authorization…")):(e(),a("view",b,[(e(!0),a(h,null,m(c.value,(d,u)=>(e(),a("text",{key:u,class:"copy"},v(d),1))),128))]))])]))}},z=p(T,[["__scopeId","data-v-daa5e924"]]);export{z as default};
