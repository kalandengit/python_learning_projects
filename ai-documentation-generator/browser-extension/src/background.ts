import { dataUrlToBlob } from "./shared";
type Request={type:"CAPTURE_VISIBLE"|"CAPTURE_REGION"|"CAPTURE_FULL_PAGE"};
chrome.runtime.onMessage.addListener((message:Request,_sender,sendResponse)=>{void handle(message).then(sendResponse).catch(e=>sendResponse({ok:false,error:e instanceof Error?e.message:"Capture failed"}));return true;});
async function activeTab(){const [tab]=await chrome.tabs.query({active:true,currentWindow:true});if(!tab?.id)throw new Error("No active browser tab.");return tab;}
async function visible(){const tab=await activeTab();const dataUrl=await chrome.tabs.captureVisibleTab(tab.windowId,{format:"png"});return{ok:true,dataUrl,title:tab.title||"Browser capture",url:tab.url||""};}
async function handle(message:Request){if(message.type==="CAPTURE_VISIBLE")return visible();const tab=await activeTab();if(message.type==="CAPTURE_REGION"){
 await chrome.scripting.executeScript({target:{tabId:tab.id!},files:["content.js"]});const result=await chrome.tabs.sendMessage(tab.id!,{type:"SELECT_REGION"});if(!result?.rect)throw new Error("Region selection was cancelled.");const capture=await visible();return{...capture,crop:result.rect,devicePixelRatio:result.devicePixelRatio};}
 if(message.type==="CAPTURE_FULL_PAGE"){
  await chrome.scripting.executeScript({target:{tabId:tab.id!},files:["content.js"]});const metrics=await chrome.tabs.sendMessage(tab.id!,{type:"PAGE_METRICS"});const shots:string[]=[];for(let y=0;y<metrics.scrollHeight;y+=metrics.viewportHeight){await chrome.tabs.sendMessage(tab.id!,{type:"SCROLL_TO",y});await new Promise(r=>setTimeout(r,180));shots.push(await chrome.tabs.captureVisibleTab(tab.windowId,{format:"png"}));}await chrome.tabs.sendMessage(tab.id!,{type:"SCROLL_TO",y:metrics.originalY});return{ok:true,segments:shots,metrics,title:tab.title||"Full page capture",url:tab.url||""};}
 throw new Error("Unknown capture request");}
