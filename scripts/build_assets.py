import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "technical" / "assets"
OUT.mkdir(parents=True, exist_ok=True)


def box(ax, x, y, w, h, text, color):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.02",facecolor=color,edgecolor="#0F2747",linewidth=1.2))
    ax.text(x+w/2,y+h/2,text,ha="center",va="center",fontsize=9,color="#0F172A",weight="bold")


def architecture():
    fig, ax = plt.subplots(figsize=(11,6)); ax.set_xlim(0,11); ax.set_ylim(0,6); ax.axis("off")
    for x,y,w,h,t,c in [(0.4,4.5,2,0.75,"Streamlit\nAnalyst UI","#DBEAFE"),(3.1,4.5,2,0.75,"FastAPI\nService","#BFDBFE"),(5.8,4.5,2,0.75,"Agent\nWorkflow","#93C5FD"),(8.5,4.5,2,0.75,"Human\nApproval","#FDE68A"),(0.4,2.2,2,0.75,"Synthetic\nAlerts & Logs","#DCFCE7"),(3.1,2.2,2,0.75,"RAG\nKnowledge","#DCFCE7"),(5.8,2.2,2,0.75,"MCP\nTools","#E9D5FF"),(8.5,2.2,2,0.75,"Incident\nJSON & PDF","#FED7AA")]: box(ax,x,y,w,h,t,c)
    arrows=[((2.4,4.88),(3.1,4.88)),((5.1,4.88),(5.8,4.88)),((7.8,4.88),(8.5,4.88)),((1.4,2.95),(1.4,4.5)),((4.1,2.95),(6.4,4.5)),((6.8,2.95),(6.8,4.5)),((9.5,4.5),(9.5,2.95)),((8.5,2.58),(7.8,2.58))]
    for a,b in arrows: ax.annotate("",xy=b,xytext=a,arrowprops={"arrowstyle":"->","color":"#334155","lw":1.7})
    ax.text(5.5,0.9,"Trust rule: retrieved content and logs are data, never instructions. Operational actions remain drafts until analyst approval.",ha="center",fontsize=10,color="#334155")
    fig.tight_layout(); fig.savefig(OUT/"architecture.png",dpi=180,bbox_inches="tight"); plt.close(fig)


def workflow():
    labels=["Alert","Triage","Evidence","Threat Intel\n+ RAG","Investigation","Risk","Defensive\nDrafts","Analyst\nReview","Report"]
    fig,ax=plt.subplots(figsize=(12,3)); ax.set_xlim(0,len(labels)); ax.set_ylim(0,2); ax.axis("off")
    for i,label in enumerate(labels):
        color="#FDE68A" if "Analyst" in label else "#DBEAFE"
        box(ax,i+0.08,0.72,0.78,0.55,label,color)
        if i<len(labels)-1: ax.annotate("",xy=(i+1.08,1),xytext=(i+0.86,1),arrowprops={"arrowstyle":"->","color":"#475569"})
    fig.tight_layout(); fig.savefig(OUT/"workflow.png",dpi=180,bbox_inches="tight"); plt.close(fig)


def dashboard():
    alerts=pd.DataFrame(json.loads((ROOT/"data"/"alerts.json").read_text()))
    fig=plt.figure(figsize=(12,7),facecolor="#F8FAFC"); gs=fig.add_gridspec(3,6,hspace=.65,wspace=.8)
    fig.suptitle("SOC Copilot Dashboard - Synthetic Demo",x=.05,ha="left",fontsize=18,weight="bold",color="#0F2747")
    metrics=[("TOTAL ALERTS",len(alerts)),("HIGH-CRITICAL",3),("AFFECTED USERS",alerts.user.nunique())]
    for i,(label,value) in enumerate(metrics):
        ax=fig.add_subplot(gs[0,i*2:(i+1)*2]); ax.axis("off"); ax.text(.03,.75,label,fontsize=9,color="#64748B"); ax.text(.03,.25,str(value),fontsize=26,weight="bold",color="#0F2747")
    ax1=fig.add_subplot(gs[1:,0:3]); counts=alerts.category.value_counts(); ax1.bar(counts.index,counts.values,color=["#2563EB","#7C3AED","#0F766E"]); ax1.set_title("Alerts by category",loc="left",weight="bold"); ax1.spines[["top","right"]].set_visible(False)
    ax2=fig.add_subplot(gs[1:,3:]); ax2.bar(alerts.alert_id,alerts.asset_criticality,color="#F59E0B"); ax2.set_ylim(0,5.5); ax2.set_title("Asset criticality",loc="left",weight="bold"); ax2.spines[["top","right"]].set_visible(False)
    fig.savefig(OUT/"dashboard_preview.png",dpi=180,bbox_inches="tight"); plt.close(fig)


def evaluation():
    data=json.loads((ROOT/"evaluation"/"results.json").read_text())["metrics"]
    labels=[k.replace("_"," ").title() for k in data]; values=[v*100 for v in data.values()]
    fig,ax=plt.subplots(figsize=(9,4.5)); bars=ax.barh(labels,values,color="#2563EB"); ax.set_xlim(0,105); ax.set_xlabel("Percent"); ax.set_title("MVP labelled-case checks (n=3)",loc="left",weight="bold")
    ax.bar_label(bars,fmt="%.0f%%",padding=3); ax.spines[["top","right"]].set_visible(False); fig.tight_layout(); fig.savefig(OUT/"evaluation.png",dpi=180,bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__": architecture(); workflow(); dashboard(); evaluation(); print(OUT)
