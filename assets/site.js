// Shared header/footer + events rendering. No build step needed.
const PAGES=[["index.html","Home"],["events.html","Events"],["lunch.html","Lunch"],["classes.html","Classes"],["contact.html","Contact"]];
(function(){
  const here=location.pathname.split("/").pop()||"index.html";
  document.getElementById("nav").innerHTML="<ul>"+PAGES.map(([h,t])=>`<li><a href="${h}"${h===here?' aria-current="page"':""}>${t}</a></li>`).join("")+`<li><a class="ext" href="https://www.nhcgov.com/1191/Senior-Resource-Center" target="_blank" rel="noopener">Senior Resource Center ↗</a></li></ul>`;
})();
async function renderEvents(el,limit){
  try{
    const r=await fetch("events.json",{cache:"no-store"});const data=await r.json();
    const today=new Date();today.setHours(0,0,0,0);
    const ev=data.events.filter(e=>new Date((e.end_date||e.date)+"T23:59:59")>=today)
      .sort((a,b)=>(a.date+a.time).localeCompare(b.date+b.time)).slice(0,limit||999);
    if(!ev.length){el.innerHTML='<p>No upcoming events are listed yet. Please call <a href="tel:+19103387246">(910) 338-7246</a>.</p>';return}
    el.innerHTML=ev.map(e=>{
      const d=new Date(e.date+"T12:00:00");
      const long=d.toLocaleDateString("en-US",{weekday:"long",month:"long",day:"numeric"})+(e.end_date?" – "+new Date(e.end_date+"T12:00:00").toLocaleDateString("en-US",{weekday:"long",day:"numeric"}):"");
      return `<article class="event${e.closed?" closed":""}"><div class="datebox" aria-hidden="true"><span class="m">${d.toLocaleDateString("en-US",{month:"short"})}</span><span class="d">${d.getDate()}</span></div>
      <div><h3>${esc(e.title)}</h3><p><strong>${long}</strong>${e.time?" · "+esc(e.time):""}</p></div></article>`}).join("");
    const u=document.getElementById("updated");
    if(u&&data.calendar_pdf)u.innerHTML=`Events come from the New Hanover County <a href="${data.calendar_pdf}">Carolina Beach monthly calendar</a>. Last checked ${new Date(data.updated).toLocaleDateString("en-US",{month:"long",day:"numeric",year:"numeric"})}.`;
  }catch(err){el.innerHTML='<p>Events could not be loaded. Please call <a href="tel:+19103387246">(910) 338-7246</a>.</p>'}
}
function esc(s){return String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]))}
